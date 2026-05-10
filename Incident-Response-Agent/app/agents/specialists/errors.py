import app.tools.metrics_client as _mc
from app.agents.specialists.base import SpecialistAgent

_SYSTEM_PROMPT = """You are an Error Rate Specialist SRE agent. Your role is to analyze HTTP error \
rates and identify abnormal error patterns.

Use get_overview to fetch total requests and error rates (4xx/5xx %).
Use get_status_codes to see the distribution of individual status codes.

Thresholds:
- 5xx rate > 5 %  → WARNING
- 5xx rate > 10 % → CRITICAL
- 4xx rate > 20 % → WARNING

After analyzing, respond ONLY with a valid JSON object — no prose, no markdown:
{"severity": "ok"|"warning"|"critical", "summary": "<one-line>", "details": "<explanation>"}"""

_TOOLS = [
    {
        "name": "get_overview",
        "description": "Fetch total requests, 4xx/5xx counts and error-rate percentages.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_status_codes",
        "description": "Fetch request count broken down by HTTP status code.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def create_errors_agent() -> SpecialistAgent:
    return SpecialistAgent(
        name="Errors",
        system_prompt=_SYSTEM_PROMPT,
        tools=_TOOLS,
        tool_handlers={
            "get_overview": lambda **_: _mc.fetch_overview(),
            "get_status_codes": lambda **_: _mc.fetch_status_codes(),
        },
    )
