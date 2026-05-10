import app.tools.metrics_client as _mc
from app.agents.specialists.base import SpecialistAgent

_SYSTEM_PROMPT = """You are a Traffic Specialist SRE agent. Your role is to analyze request volume \
and detect anomalies such as sudden drops (possible outage) or unexpected spikes.

Use get_rps to fetch requests-per-minute for the last 10 minutes.
Use get_backends to see traffic distribution across HAProxy backends.

Patterns to detect:
- RPS drops to 0 after having traffic → possible outage / upstream failure (CRITICAL)
- All traffic concentrated on a single backend when multiple exist → WARNING
- Sudden RPS spike (> 3× average) → WARNING

After analyzing, respond ONLY with a valid JSON object — no prose, no markdown:
{"severity": "ok"|"warning"|"critical", "summary": "<one-line>", "details": "<explanation>"}"""

_TOOLS = [
    {
        "name": "get_rps",
        "description": "Fetch requests-per-minute buckets for the last N minutes (default 10).",
        "input_schema": {
            "type": "object",
            "properties": {
                "minutes": {
                    "type": "integer",
                    "description": "Number of past minutes to include (1–60).",
                    "default": 10,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_backends",
        "description": "Fetch request count per HAProxy backend.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def create_traffic_agent() -> SpecialistAgent:
    return SpecialistAgent(
        name="Traffic",
        system_prompt=_SYSTEM_PROMPT,
        tools=_TOOLS,
        tool_handlers={
            "get_rps": lambda minutes=10, **_: _mc.fetch_rps(minutes=minutes),
            "get_backends": lambda **_: _mc.fetch_backends(),
        },
    )
