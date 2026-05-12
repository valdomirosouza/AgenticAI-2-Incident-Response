from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.tools.kb_client import search_kb


async def test_search_kb_returns_results():
    fake_results = [
        {
            "id": "abc",
            "content": "Padrão de sintoma — INC-001: P99 > 1800ms + deploy recente",
            "metadata": {"incident_id": "INC-001", "chunk_type": "symptom_fingerprint"},
            "score": 0.85,
        }
    ]
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": fake_results, "total": 1}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_kb("P99 alto após deploy")

    assert results == fake_results
    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["query"] == "P99 alto após deploy"
    assert "symptom_fingerprint" in payload["chunk_types"]
    assert "runbook_step" in payload["chunk_types"]
    assert "lesson_learned" in payload["chunk_types"]


async def test_search_kb_returns_empty_on_http_error():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_kb("redis OOM noeviction")

    assert results == []


async def test_search_kb_returns_empty_on_timeout():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_kb("HAProxy down outage")

    assert results == []


async def test_search_kb_returns_empty_on_non_200():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock()
    )

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_kb("auth 401 checkout")

    assert results == []


async def test_search_kb_respects_custom_limit():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": [], "total": 0}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await search_kb("test query", limit=3)

    payload = mock_client.post.call_args.kwargs.get("json") or mock_client.post.call_args.args[1]
    assert payload["limit"] == 3
