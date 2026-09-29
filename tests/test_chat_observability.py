from __future__ import annotations

import json
import asyncio
from pathlib import Path

import httpx

from app import logging_config
from app.main import app


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/chat",
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Explain observability",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]
    assert response_event["ttft_ms"] == response.json()["ttft_ms"]
    assert response_event["tool_name"] == "retrieval"
    assert response_event["tool_success"] is True


def test_correlation_id_headers_and_enrichment(monkeypatch, tmp_path: Path) -> None:
    import re
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_requests():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Without x-request-id header (should auto-generate req-<8-hex>)
            r1 = await client.post(
                "/chat",
                json={
                    "user_id": "u01",
                    "session_id": "s01",
                    "feature": "qa",
                    "message": "Contact student@vinuni.edu.vn or 0901234567",
                },
            )
            # 2. With explicit x-request-id header
            r2 = await client.post(
                "/chat",
                headers={"x-request-id": "custom-req-999"},
                json={
                    "user_id": "u02",
                    "session_id": "s02",
                    "feature": "summary",
                    "message": "Normal message without PII",
                },
            )
            return r1, r2

    r1, r2 = asyncio.run(send_requests())

    # Check response headers for r1
    assert "x-request-id" in r1.headers
    assert re.match(r"^req-[a-f0-9]{8}$", r1.headers["x-request-id"])
    assert "x-response-time-ms" in r1.headers
    assert float(r1.headers["x-response-time-ms"]) >= 0

    # Check response headers for r2
    assert r2.headers["x-request-id"] == "custom-req-999"
    assert "x-response-time-ms" in r2.headers

    # Check logs
    lines = log_path.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]

    # Verify r1 logs
    r1_events = [e for e in events if e.get("correlation_id") == r1.headers["x-request-id"]]
    assert len(r1_events) >= 2
    for event in r1_events:
        assert event["session_id"] == "s01"
        assert event["feature"] == "qa"
        assert "user_id_hash" in event
        assert event["model"] == "claude-sonnet-4-5"
        # Check PII scrubbing in log preview
        raw_log = json.dumps(event)
        assert "student@vinuni.edu.vn" not in raw_log
        assert "0901234567" not in raw_log

    # Verify r2 logs
    r2_events = [e for e in events if e.get("correlation_id") == "custom-req-999"]
    assert len(r2_events) >= 2
    for event in r2_events:
        assert event["session_id"] == "s02"
        assert event["feature"] == "summary"
