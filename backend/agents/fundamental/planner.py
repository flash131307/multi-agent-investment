"""
Step 2 of Plan-and-Solve: LLM-generated analysis task list.
Falls back to default tasks when LLM is unavailable.
"""
import json
import logging
import re
from typing import Any

from backend.models.fundamental import AnalysisTask, CompanyProfile
from backend.agents.fundamental.prompts import PLANNER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Optional OpenAI import – exposed at module level so tests can patch it
try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore

_DEFAULT_TASKS: list[dict[str, Any]] = [
    {
        "task_id": "task_revenue_growth",
        "description": "Analyze revenue growth trends and drivers",
        "rag_query": "revenue growth sales trends market expansion",
        "weight": 0.4,
    },
    {
        "task_id": "task_profitability",
        "description": "Assess profitability margins and return on equity",
        "rag_query": "profit margin operating income return on equity",
        "weight": 0.35,
    },
    {
        "task_id": "task_balance_sheet",
        "description": "Evaluate balance sheet health and debt levels",
        "rag_query": "debt equity ratio balance sheet financial health liquidity",
        "weight": 0.25,
    },
]


def _strip_json_fences(raw: str) -> str:
    """Strip markdown code fences that GPT-4o sometimes wraps around JSON."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    return match.group(1) if match else raw


def generate_tasks(
    profile: CompanyProfile,
    settings_obj: Any,
) -> list[AnalysisTask]:
    """
    Generate analysis tasks for a company profile using an LLM (Plan-and-Solve Step 2).

    Falls back to 3 default tasks if LLM is unavailable or fails.

    Args:
        profile: CompanyProfile from Step 1.
        settings_obj: Application settings (must have openai_api_key, openai_model).

    Returns:
        List of AnalysisTask (normalized weights summing to 1.0).
    """
    tasks = _try_llm_generate(profile, settings_obj)
    if not tasks:
        logger.warning(
            "LLM task generation failed for '%s'; using default tasks.", profile.ticker
        )
        tasks = _DEFAULT_TASKS

    return _build_and_normalize(tasks)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _try_llm_generate(
    profile: CompanyProfile,
    settings_obj: Any,
) -> list[dict] | None:
    """Call OpenAI to generate tasks; return raw dicts or None on failure."""
    try:
        api_key = getattr(settings_obj, "openai_api_key", None)
        model = getattr(settings_obj, "openai_model", "gpt-4o")

        if not api_key:
            logger.warning("No OpenAI API key configured; skipping LLM task generation.")
            return None

        if OpenAI is None:
            logger.warning("openai library not installed; using default tasks.")
            return None

        client = OpenAI(api_key=api_key)

        user_message = (
            f"Company: {profile.name} ({profile.ticker})\n"
            f"Sector: {profile.sector}\n"
            f"Industry: {profile.industry}\n"
            f"Market Cap: {profile.market_cap}\n"
            f"P/E Ratio: {profile.pe_ratio}\n"
            f"Revenue Growth: {profile.revenue_growth}\n"
            f"Description: {profile.description[:500] if profile.description else 'N/A'}\n\n"
            "Generate 3-5 specific analysis tasks as a JSON array."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        raw = response.choices[0].message.content or ""
        tasks = json.loads(_strip_json_fences(raw))

        if not isinstance(tasks, list):
            logger.warning("LLM returned non-list response; using defaults.")
            return None

        return tasks

    except Exception as exc:
        logger.warning("LLM task generation error: %s", exc)
        return None


def _build_and_normalize(raw_tasks: list[dict]) -> list[AnalysisTask]:
    """Parse raw task dicts into AnalysisTask models and normalize weights."""
    parsed: list[AnalysisTask] = []

    for raw in raw_tasks:
        try:
            task = AnalysisTask(
                task_id=str(raw.get("task_id", f"task_{len(parsed)}")),
                description=str(raw.get("description", "")),
                rag_query=str(raw.get("rag_query", "")),
                weight=float(raw.get("weight", 1.0 / len(raw_tasks))),
            )
            parsed.append(task)
        except Exception as exc:
            logger.warning("Could not parse task %r: %s", raw, exc)

    if not parsed:
        parsed = [AnalysisTask(**t) for t in _DEFAULT_TASKS]

    # Normalize weights so they sum to 1.0
    total_weight = sum(t.weight for t in parsed)
    if total_weight <= 0:
        total_weight = 1.0

    normalized: list[AnalysisTask] = []
    for task in parsed:
        new_weight = task.weight / total_weight
        # Clamp to (0, 1] to satisfy field constraints
        new_weight = max(1e-6, min(1.0, new_weight))
        normalized.append(
            AnalysisTask(
                task_id=task.task_id,
                description=task.description,
                rag_query=task.rag_query,
                weight=new_weight,
            )
        )

    return normalized
