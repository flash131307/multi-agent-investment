"""
Technical Analysis Agent — ReAct loop using OpenAI function calling.
"""
import json
import logging
from typing import Any, Optional

from openai import OpenAI

from backend.agents.base import BaseAgent
from backend.agents.technical.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from backend.agents.technical.tools.market_regime import compute_market_regime
from backend.agents.technical.tools.rsi_analysis import compute_rsi_signal
from backend.agents.technical.tools.macd_analysis import compute_macd_signal
from backend.agents.technical.tools.bollinger_analysis import compute_bollinger_signal
from backend.agents.technical.tools.volume_analysis import compute_volume_signal
from backend.agents.technical.tools.pattern_recognition import compute_pattern_signal
from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.technical import MarketRegime, ToolOutput
from backend.services.yahoo_finance import get_technical_data

logger = logging.getLogger(__name__)

_MAX_STEPS = 5
_FALLBACK_SIGNAL = AgentSignal(
    agent_name="technical",
    direction=Direction.NEUTRAL,
    strength=Strength.WEAK,
    confidence=0.3,
    reasoning="Technical agent fallback: insufficient data or all tools returned NEUTRAL.",
)

# OpenAI tool schemas for function calling
_OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "market_regime",
            "description": TOOL_DESCRIPTIONS["market_regime"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rsi_analysis",
            "description": TOOL_DESCRIPTIONS["rsi_analysis"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "macd_analysis",
            "description": TOOL_DESCRIPTIONS["macd_analysis"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bollinger_analysis",
            "description": TOOL_DESCRIPTIONS["bollinger_analysis"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "volume_analysis",
            "description": TOOL_DESCRIPTIONS["volume_analysis"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pattern_recognition",
            "description": TOOL_DESCRIPTIONS["pattern_recognition"],
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "synthesize_signal",
            "description": (
                "Call this when you have gathered sufficient evidence (at least 2 tool results) "
                "and are ready to produce the final AgentSignal. Pass your conclusions as JSON."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["BUY", "NEUTRAL", "SELL"],
                        "description": "Trading direction based on technical evidence.",
                    },
                    "strength": {
                        "type": "string",
                        "enum": ["STRONG", "MODERATE", "WEAK"],
                        "description": "Signal conviction strength.",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score between 0.0 and 1.0.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Human-readable rationale citing specific indicator values.",
                    },
                },
                "required": ["direction", "strength", "confidence", "reasoning"],
            },
        },
    },
]


class TechnicalAgent(BaseAgent):
    """
    Technical Analysis Agent using a ReAct loop with OpenAI function calling.

    Workflow:
    1. Fetch OHLCV data via get_technical_data(ticker).
    2. Force call market_regime as first step.
    3. LLM decides which tools to call next (max 5 steps total).
    4. LLM calls synthesize_signal to produce final AgentSignal.
    5. On loop failure: return NEUTRAL/WEAK/0.3 fallback.
    """

    def __init__(self, openai_client: Optional[OpenAI] = None, timeout: float = 30.0) -> None:
        super().__init__(agent_name="technical", timeout=timeout)
        self._client = openai_client or self._build_default_client()

    @staticmethod
    def _build_default_client() -> OpenAI:
        from backend.config.settings import settings
        return OpenAI(api_key=settings.openai_api_key)

    def _dispatch_tool(
        self,
        tool_name: str,
        df: Any,
        regime: Optional[MarketRegime],
    ) -> dict[str, Any]:
        """
        Execute a named tool and return its JSON-serialisable result.
        """
        try:
            if tool_name == "market_regime":
                result = compute_market_regime(df)
                return result.model_dump()
            elif tool_name == "rsi_analysis":
                if regime is None:
                    raise ValueError("market_regime must be called before rsi_analysis")
                result = compute_rsi_signal(df, regime)
                return result.model_dump()
            elif tool_name == "macd_analysis":
                result = compute_macd_signal(df)
                return result.model_dump()
            elif tool_name == "bollinger_analysis":
                result = compute_bollinger_signal(df)
                return result.model_dump()
            elif tool_name == "volume_analysis":
                result = compute_volume_signal(df)
                return result.model_dump()
            elif tool_name == "pattern_recognition":
                result = compute_pattern_signal(df)
                return result.model_dump()
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as exc:
            logger.warning("Tool '%s' raised an error: %s", tool_name, exc)
            return {"error": str(exc)}

    async def _execute(self, ticker: str) -> Optional[AgentSignal]:
        """
        Run the ReAct loop for the given ticker.
        """
        # 1. Fetch data
        try:
            df = get_technical_data(ticker)
        except ValueError as exc:
            logger.error("Failed to fetch technical data for %s: %s", ticker, exc)
            return _FALLBACK_SIGNAL

        # 2. Force first step: market_regime
        regime: Optional[MarketRegime] = None
        try:
            regime_dict = self._dispatch_tool("market_regime", df, None)
            if "error" not in regime_dict:
                regime = MarketRegime(**regime_dict)
        except Exception as exc:
            logger.error("market_regime tool failed for %s: %s", ticker, exc)
            return _FALLBACK_SIGNAL

        # 3. Build initial messages
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze the technical situation for ticker '{ticker}'. "
                    f"The market regime has already been computed and is as follows:\n"
                    f"{json.dumps(regime_dict, indent=2)}\n\n"
                    f"Now select 1-4 additional tools, then call synthesize_signal."
                ),
            },
            # Inject the forced market_regime result as an assistant tool call
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_regime_0",
                        "type": "function",
                        "function": {
                            "name": "market_regime",
                            "arguments": "{}",
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_regime_0",
                "content": json.dumps(regime_dict),
            },
        ]

        # 4. ReAct loop (max _MAX_STEPS - 1 additional steps, since step 1 is done)
        tool_outputs: list[ToolOutput] = []
        called_tools: set[str] = {"market_regime"}
        final_signal: Optional[AgentSignal] = None

        for step in range(_MAX_STEPS - 1):
            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=_OPENAI_TOOLS,
                    tool_choice="required",
                )
            except Exception as exc:
                logger.error("OpenAI API call failed at step %d: %s", step + 2, exc)
                break

            assistant_message = response.choices[0].message
            messages.append(assistant_message.model_dump(exclude_none=True))

            # Check if no tool calls (shouldn't happen with tool_choice=required)
            if not assistant_message.tool_calls:
                logger.warning("LLM produced no tool calls at step %d", step + 2)
                break

            # Process tool calls
            synthesis_requested = False
            for tc in assistant_message.tool_calls:
                tool_name = tc.function.name
                call_args_str = tc.function.arguments or "{}"

                if tool_name == "synthesize_signal":
                    synthesis_requested = True
                    try:
                        args = json.loads(call_args_str)
                        final_signal = self._build_agent_signal(args)
                        tool_result = {"status": "signal_synthesized"}
                    except Exception as exc:
                        logger.warning("synthesize_signal parsing failed: %s", exc)
                        tool_result = {"error": str(exc)}
                else:
                    called_tools.add(tool_name)
                    tool_result = self._dispatch_tool(tool_name, df, regime)
                    # Track ToolOutput objects (not errors)
                    if "error" not in tool_result and tool_name != "market_regime":
                        try:
                            output = ToolOutput(**tool_result)
                            tool_outputs.append(output)
                        except Exception:
                            pass

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result),
                })

            if synthesis_requested and final_signal is not None:
                break

        # 5. Fallback if no signal synthesized
        if final_signal is None:
            logger.warning(
                "TechnicalAgent: no synthesize_signal call completed for %s; using fallback.",
                ticker,
            )
            final_signal = _FALLBACK_SIGNAL

        return final_signal

    def _build_agent_signal(self, args: dict) -> AgentSignal:
        """
        Construct an AgentSignal from synthesize_signal arguments.
        Validates and clamps confidence.
        """
        direction = Direction(args["direction"])
        strength = Strength(args["strength"])
        confidence = max(0.0, min(1.0, float(args["confidence"])))
        reasoning = str(args.get("reasoning", ""))

        # Validate NEUTRAL/STRONG constraint
        if direction == Direction.NEUTRAL and strength == Strength.STRONG:
            strength = Strength.MODERATE

        if not reasoning:
            reasoning = "Technical analysis complete."

        return AgentSignal(
            agent_name="technical",
            direction=direction,
            strength=strength,
            confidence=confidence,
            reasoning=reasoning,
        )
