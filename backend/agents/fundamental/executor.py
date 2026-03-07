"""
Step 3 of Plan-and-Solve: execute each AnalysisTask and produce SubConclusions.
"""
import json
import logging
import re
from typing import Any, TYPE_CHECKING

from backend.models.fundamental import AnalysisTask, SubConclusion
from backend.agents.fundamental.prompts import EXECUTOR_SYSTEM_PROMPT
from backend.agents.fundamental.tools.rag_search import rag_search

if TYPE_CHECKING:
    from backend.rag.retriever import HybridRetriever

logger = logging.getLogger(__name__)

# Optional OpenAI import – exposed at module level so tests can patch it
try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore

def _strip_json_fences(raw: str) -> str:
    """Strip markdown code fences that GPT-4o sometimes wraps around JSON."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    return match.group(1) if match else raw


_MAX_SUPPLEMENTARY_ROUNDS = 2
_CONFIDENCE_THRESHOLD = 0.5


def execute_tasks(
    tasks: list[AnalysisTask],
    ticker: str,
    retriever: "HybridRetriever | None",
    financial_data: dict,
    settings_obj: Any,
) -> list[SubConclusion]:
    """
    Execute each AnalysisTask using RAG retrieval + LLM analysis.

    Args:
        tasks: List of AnalysisTask from the planner.
        ticker: Stock ticker symbol.
        retriever: HybridRetriever (may be None if RAG unavailable).
        financial_data: Dict from get_financial_statements().
        settings_obj: Application settings with OpenAI config.

    Returns:
        List of SubConclusion, one per task.
    """
    conclusions: list[SubConclusion] = []

    for task in tasks:
        conclusion = _execute_single_task(
            task=task,
            ticker=ticker,
            retriever=retriever,
            financial_data=financial_data,
            settings_obj=settings_obj,
        )
        conclusions.append(conclusion)

    return conclusions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _execute_single_task(
    task: AnalysisTask,
    ticker: str,
    retriever: "HybridRetriever | None",
    financial_data: dict,
    settings_obj: Any,
) -> SubConclusion:
    """Execute one task with optional supplementary retrieval rounds."""
    rag_passages: list[str] = []
    if retriever is not None:
        rag_passages = rag_search(task.rag_query, retriever, top_k=5)

    metrics_summary = _format_metrics(financial_data.get("metrics", {}))

    conclusion = _call_llm(
        task=task,
        rag_passages=rag_passages,
        metrics_summary=metrics_summary,
        settings_obj=settings_obj,
    )

    # Supplementary rounds if confidence is low
    rounds = 0
    while conclusion.confidence < _CONFIDENCE_THRESHOLD and rounds < _MAX_SUPPLEMENTARY_ROUNDS:
        rounds += 1
        if retriever is not None:
            extra_passages = rag_search(task.description, retriever, top_k=3)
            rag_passages = list({p for p in rag_passages + extra_passages})

        conclusion = _call_llm(
            task=task,
            rag_passages=rag_passages,
            metrics_summary=metrics_summary,
            settings_obj=settings_obj,
        )

    return conclusion


def _call_llm(
    task: AnalysisTask,
    rag_passages: list[str],
    metrics_summary: str,
    settings_obj: Any,
) -> SubConclusion:
    """Call OpenAI to produce a SubConclusion for one task."""
    try:
        api_key = getattr(settings_obj, "openai_api_key", None)
        model = getattr(settings_obj, "openai_model", "gpt-4o")

        if not api_key:
            return _fallback_conclusion(task.task_id, "No OpenAI API key configured.")

        if OpenAI is None:
            return _fallback_conclusion(task.task_id, "openai library not installed.")

        client = OpenAI(api_key=api_key)

        passages_text = (
            "\n\n".join(f"[{i+1}] {p}" for i, p in enumerate(rag_passages))
            if rag_passages
            else "No passages retrieved."
        )

        user_message = (
            f"Task ID: {task.task_id}\n"
            f"Task: {task.description}\n\n"
            f"Retrieved Passages:\n{passages_text}\n\n"
            f"Financial Metrics:\n{metrics_summary}\n\n"
            "Provide your analysis as a JSON object."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        raw = response.choices[0].message.content or ""
        data = json.loads(_strip_json_fences(raw))

        return SubConclusion(
            task_id=str(data.get("task_id", task.task_id)),
            conclusion=str(data.get("conclusion", "")),
            supporting_evidence=[
                str(e) for e in data.get("supporting_evidence", [])
            ],
            sentiment_score=float(
                max(-1.0, min(1.0, data.get("sentiment_score", 0.0)))
            ),
            confidence=float(
                max(0.0, min(1.0, data.get("confidence", 0.3)))
            ),
        )

    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM response for task '%s': %s", task.task_id, exc)
        return _fallback_conclusion(task.task_id, "LLM response parse error.")
    except Exception as exc:
        logger.warning("LLM execution failed for task '%s': %s", task.task_id, exc)
        return _fallback_conclusion(task.task_id, str(exc))


def _fallback_conclusion(task_id: str, reason: str) -> SubConclusion:
    """Return a low-confidence neutral conclusion when LLM fails."""
    return SubConclusion(
        task_id=task_id,
        conclusion=f"Analysis unavailable: {reason}",
        supporting_evidence=[],
        sentiment_score=0.0,
        confidence=0.3,
    )


def _format_metrics(metrics: dict) -> str:
    """Format financial metrics dict into a readable string."""
    if not metrics:
        return "No financial metrics available."

    lines = []
    label_map = {
        "roe": "Return on Equity (ROE)",
        "current_ratio": "Current Ratio",
        "debt_to_equity": "Debt-to-Equity",
        "revenue_growth_yoy": "Revenue Growth YoY",
    }
    for key, label in label_map.items():
        val = metrics.get(key)
        if val is not None:
            lines.append(f"  {label}: {val:.4f}")
        else:
            lines.append(f"  {label}: N/A")

    return "\n".join(lines)
