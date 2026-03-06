"""
Prompts and JSON schemas for the fundamental analysis agent.
"""

PLANNER_SYSTEM_PROMPT = """You are a senior fundamental equity analyst.
Given a company profile, generate 3-5 specific analysis tasks to assess the company's investment value.
Each task should have a clear analytical focus and a targeted RAG query to retrieve supporting evidence.

Respond ONLY with a valid JSON array. Do not include any other text.
Each element must have these fields:
- task_id: unique string identifier (e.g., "task_1")
- description: clear description of what to analyze
- rag_query: specific query to retrieve supporting documents
- weight: importance weight between 0 and 1 (all weights must sum to 1.0)
"""

EXECUTOR_SYSTEM_PROMPT = """You are a senior fundamental equity analyst executing a specific analysis task.
You will be given:
1. A task description
2. Relevant passages retrieved from SEC filings and company documents
3. Key financial metrics

Analyze the evidence and produce a structured conclusion.
Respond ONLY with a valid JSON object. Do not include any other text.
The object must have these fields:
- task_id: string (same as the input task_id)
- conclusion: string (1-3 sentences summarizing your findings)
- supporting_evidence: array of strings (key quotes or data points)
- sentiment_score: float between -1.0 (very bearish) and 1.0 (very bullish)
- confidence: float between 0.0 and 1.0 (how confident you are in this conclusion)
"""

TASK_OUTPUT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["task_id", "description", "rag_query", "weight"],
        "properties": {
            "task_id": {"type": "string"},
            "description": {"type": "string"},
            "rag_query": {"type": "string"},
            "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
    },
}

CONCLUSION_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "task_id",
        "conclusion",
        "supporting_evidence",
        "sentiment_score",
        "confidence",
    ],
    "properties": {
        "task_id": {"type": "string"},
        "conclusion": {"type": "string"},
        "supporting_evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
        "sentiment_score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}
