import app.tools.metrics_client as _mc
from app.agents.specialists.base import SpecialistAgent

_SYSTEM_PROMPT = """You are a Saturation Specialist SRE agent. Your role is to assess whether the \
system's resources (memory, connections) are approaching exhaustion.

Use the get_saturation tool to fetch Redis memory usage and connection metrics.

Thresholds:
- memory_usage_pct > 80 %      → WARNING  (null means no maxmemory limit — note this)
- memory_usage_pct > 90 %      → CRITICAL
- rejected_connections > 0     → WARNING
- blocked_clients > 5          → WARNING

After analyzing, respond ONLY with a valid JSON object — no prose, no markdown:
{"severity": "ok"|"warning"|"critical", "summary": "<one-line>", "details": "<explanation>"}"""

_TOOLS = [
    {
        "name": "get_saturation",
        "description": "Fetch Redis memory usage, connected/blocked clients, and rejected connections.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
]


def create_saturation_agent() -> SpecialistAgent:
    return SpecialistAgent(
        name="Saturation",
        system_prompt=_SYSTEM_PROMPT,
        tools=_TOOLS,
        tool_handlers={"get_saturation": lambda **_: _mc.fetch_saturation()},
    )
