import app.tools.metrics_client as _mc
from app.agents.specialists.base import SpecialistAgent

_SYSTEM_PROMPT = """You are a Latency Specialist SRE agent. Your role is to analyze HTTP response-time \
metrics and detect latency degradation.

Use the get_response_times tool to fetch current P50, P95, and P99 percentiles.

Thresholds:
- P95 > 500 ms  → WARNING
- P99 > 1000 ms → CRITICAL
- count == 0    → OK (no traffic yet)

After analyzing the data, respond ONLY with a valid JSON object — no prose, no markdown:
{"severity": "ok"|"warning"|"critical", "summary": "<one-line>", "details": "<explanation>"}"""

_TOOLS = [
    {
        "name": "get_response_times",
        "description": "Fetch current HTTP latency percentiles (P50, P95, P99) and sample count.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
]


def create_latency_agent() -> SpecialistAgent:
    return SpecialistAgent(
        name="Latency",
        system_prompt=_SYSTEM_PROMPT,
        tools=_TOOLS,
        tool_handlers={"get_response_times": lambda **_: _mc.fetch_response_times()},
    )
