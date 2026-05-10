import asyncio
import json
import logging
from datetime import datetime, timezone

import anthropic

import app.config as _cfg
from app.agents.specialists.errors import create_errors_agent
from app.agents.specialists.latency import create_latency_agent
from app.agents.specialists.saturation import create_saturation_agent
from app.agents.specialists.traffic import create_traffic_agent
from app.models.report import IncidentReport, Severity, SpecialistFinding

logger = logging.getLogger(__name__)

_SEVERITY_RANK = {Severity.OK: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}

_SYSTEM_PROMPT = """You are an Incident Response Orchestrator for an SRE team. \
You receive structured findings from four specialist agents (Latency, Errors, Saturation, Traffic) \
and synthesize them into a final incident report.

Your task:
1. Determine the overall severity (ok / warning / critical) — use the highest severity across all findings.
2. Write a concise incident title (or "System Healthy" when all is ok).
3. Write a diagnosis explaining the current state or root cause in 2–3 sentences.
4. List 1–5 prioritized, actionable recommendations for the on-call engineer.

Respond ONLY with a valid JSON object — no prose, no markdown:
{
  "overall_severity": "ok"|"warning"|"critical",
  "title": "<title>",
  "diagnosis": "<diagnosis>",
  "recommendations": ["<action 1>", "<action 2>"]
}"""


async def run_analysis() -> IncidentReport:
    agents = [
        create_latency_agent(),
        create_errors_agent(),
        create_saturation_agent(),
        create_traffic_agent(),
    ]

    logger.info("Starting parallel analysis with %d specialist agents", len(agents))
    findings: tuple[SpecialistFinding, ...] = await asyncio.gather(
        *[agent.analyze() for agent in agents]
    )
    logger.info("All specialists completed — synthesizing findings")

    return await _synthesize(list(findings))


async def _synthesize(findings: list[SpecialistFinding]) -> IncidentReport:
    findings_text = "\n\n".join(
        f"**{f.specialist} Specialist** (severity: {f.severity.value})\n"
        f"Summary: {f.summary}\n"
        f"Details: {f.details}"
        for f in findings
    )

    client = anthropic.AsyncAnthropic(api_key=_cfg.settings.anthropic_api_key)
    response = await client.messages.create(
        model=_cfg.settings.model,
        max_tokens=_cfg.settings.max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here are the findings from the specialist agents:\n\n{findings_text}\n\n"
                    "Provide the final incident assessment."
                ),
            }
        ],
    )

    text = next((b.text for b in response.content if hasattr(b, "text")), "")

    try:
        body = text
        if "```json" in body:
            start = body.index("```json") + 7
            end = body.index("```", start)
            body = body[start:end].strip()
        data = json.loads(body)
        return IncidentReport(
            timestamp=datetime.now(timezone.utc),
            overall_severity=Severity(data.get("overall_severity", "ok")),
            title=data.get("title", "Analysis Complete"),
            diagnosis=data.get("diagnosis", ""),
            recommendations=data.get("recommendations", []),
            findings=findings,
        )
    except Exception:
        logger.warning("Could not parse orchestrator JSON response; deriving severity from findings")
        overall = max(findings, key=lambda f: _SEVERITY_RANK[f.severity]).severity
        return IncidentReport(
            timestamp=datetime.now(timezone.utc),
            overall_severity=overall,
            title="Analysis Complete",
            diagnosis=text,
            recommendations=[],
            findings=findings,
        )
