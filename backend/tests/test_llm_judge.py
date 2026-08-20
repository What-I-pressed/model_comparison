from __future__ import annotations

import pytest

from src.metrics.llm_judge import parse_judge_response
from src.openrouter_client import OpenRouterClient, OpenRouterError


def test_parse_judge_response_accepts_double_wrapped_json():
    score, comment = parse_judge_response('{{"score": 7.5, "comment": "Гарна пісня"}}')
    assert score == 7.5
    assert comment == "Гарна пісня"


def test_openrouter_client_rejects_empty_message_content(monkeypatch):
    client = OpenRouterClient(api_key="test")

    class DummyResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {"content": None},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {},
            }

    monkeypatch.setattr("src.openrouter_client.requests.post", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(OpenRouterError, match="порожній або не-текстовий контент"):
        client.complete("cohere/north-mini-code", [{"role": "user", "content": "hi"}])
