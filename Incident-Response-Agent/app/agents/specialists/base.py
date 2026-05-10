import json
import logging
from typing import Any, Callable, Coroutine

import anthropic

import app.config as _cfg
from app.models.report import Severity, SpecialistFinding

logger = logging.getLogger(__name__)


class SpecialistAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[dict],
        tool_handlers: dict[str, Callable[..., Coroutine[Any, Any, dict]]],
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.tool_handlers = tool_handlers
        self._client = anthropic.AsyncAnthropic(api_key=_cfg.settings.anthropic_api_key)

    async def analyze(self) -> SpecialistFinding:
        messages: list[dict] = [
            {"role": "user", "content": f"Analyze the current {self.name} metrics and report your finding."}
        ]

        while True:
            response = await self._client.messages.create(
                model=_cfg.settings.model,
                max_tokens=_cfg.settings.max_tokens,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        handler = self.tool_handlers.get(block.name)
                        if handler:
                            try:
                                result = await handler(**block.input)
                            except Exception as exc:
                                logger.warning("Tool %s failed: %s", block.name, exc)
                                result = {"error": str(exc)}
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result),
                                }
                            )
                messages = messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results},
                ]
            else:
                text = next(
                    (b.text for b in response.content if hasattr(b, "text")),
                    "",
                )
                return self._parse_finding(text)

    def _parse_finding(self, text: str) -> SpecialistFinding:
        try:
            body = text
            if "```json" in body:
                start = body.index("```json") + 7
                end = body.index("```", start)
                body = body[start:end].strip()
            elif "```" in body:
                start = body.index("```") + 3
                end = body.index("```", start)
                body = body[start:end].strip()

            data = json.loads(body)
            return SpecialistFinding(
                specialist=self.name,
                severity=Severity(data.get("severity", "ok")),
                summary=data.get("summary", ""),
                details=data.get("details", ""),
            )
        except Exception:
            logger.warning("Could not parse JSON finding from %s; falling back to raw text", self.name)
            return SpecialistFinding(
                specialist=self.name,
                severity=Severity.WARNING,
                summary=f"{self.name} analysis completed",
                details=text,
            )
