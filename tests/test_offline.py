"""Offline tests: no network. The API is replaced by a fake urlopen."""

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import glasser_client as gc  # noqa: E402
from utils.tool_support import (  # noqa: E402
    InvalidInput,
    json_object,
    opt_int,
    price_line,
    summarize_run,
    summarize_search,
)


class _Response(io.BytesIO):
    def __init__(self, status, body):
        super().__init__(json.dumps(body).encode())
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(status, envelope):
    return urllib.error.HTTPError(
        "https://api.glasser.ai/x", status, "err", {}, io.BytesIO(json.dumps(envelope).encode())
    )


@pytest.fixture
def fake_api(monkeypatch):
    calls = []
    script = []

    def urlopen(req, timeout=None):
        calls.append(req)
        outcome = script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(gc.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(gc.time, "sleep", lambda s: None)
    return calls, script


def test_missing_key_is_unauthorized_before_any_call():
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("   ")
    assert e.value.code == "unauthorized"


def test_headers_and_body(fake_api):
    calls, script = fake_api
    script.append(_Response(200, {"data": [], "total": 0}))
    gc.GlasserClient("gl_test").search("domain rating", 3, None)
    req = calls[0]
    assert req.full_url == "https://api.glasser.ai/v1/endpoints/search"
    assert req.get_header("Authorization") == "Bearer gl_test"
    assert req.get_header("User-agent").startswith("glasser-dify-plugin/")
    assert json.loads(req.data) == {"query": "domain rating", "limit": 3}


def test_error_envelope_passes_through(fake_api):
    _calls, script = fake_api
    envelope = {
        "error": {"code": "insufficient_balance", "message": "Top up", "details": {"required_usd": "0.01"}},
        "request_id": "req-1",
    }
    script.append(_http_error(402, envelope))
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("gl_test").balance()
    assert e.value.code == "insufficient_balance"
    assert e.value.request_id == "req-1"
    assert e.value.payload() == envelope


def test_rate_limit_retries_once(fake_api):
    calls, script = fake_api
    limited = {"error": {"code": "rate_limited", "message": "slow down", "retry_after_ms": 10}, "request_id": "r"}
    script.append(_http_error(429, limited))
    script.append(_Response(200, {"balance_usd": "1.00", "held_usd": "0.00", "available_usd": "1.00"}))
    assert gc.GlasserClient("gl_test").balance()["available_usd"] == "1.00"
    assert len(calls) == 2


def test_rate_limit_second_time_is_returned(fake_api):
    calls, script = fake_api
    limited = {"error": {"code": "rate_limited", "message": "slow down", "retry_after_ms": 10}, "request_id": "r"}
    script.extend([_http_error(429, limited), _http_error(429, limited)])
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("gl_test").balance()
    assert e.value.code == "rate_limited"
    assert len(calls) == 2


def test_run_retry_reuses_idempotency_key(fake_api):
    calls, script = fake_api
    script.append(urllib.error.URLError("reset"))
    script.append(_Response(200, {"id": "run-1", "status": "COMPLETED"}))
    status, run = gc.GlasserClient("gl_test").create_run(
        "ahrefs", "/v3/public/domain-rating-free", {"target": "x.com"}, None, "key-1", 5
    )
    assert status == 200 and run["id"] == "run-1"
    assert [c.get_header("Idempotency-key") for c in calls] == ["key-1", "key-1"]


def test_stop_has_no_transport_retry(fake_api):
    calls, script = fake_api
    script.append(urllib.error.URLError("reset"))
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("gl_test").stop_run("run-1")
    assert e.value.code == "transport_error"
    assert len(calls) == 1


def test_wait_run_polls_until_terminal(fake_api):
    calls, script = fake_api
    script.append(_Response(200, {"id": "run-1", "status": "RUNNING"}))
    script.append(_Response(200, {"id": "run-1", "status": "COMPLETED"}))
    run = gc.GlasserClient("gl_test").wait_run({"id": "run-1", "status": "QUEUED"}, budget_s=30, poll_s=0)
    assert run["status"] == "COMPLETED"
    assert calls[-1].full_url.endswith("/v1/runs/run-1")


def test_json_object_accepts_dict_string_and_empty():
    assert json_object(None, "input") == {}
    assert json_object("", "input") == {}
    assert json_object({"a": 1}, "input") == {"a": 1}
    assert json_object('{"target": "x.com"}', "input") == {"target": "x.com"}
    with pytest.raises(InvalidInput):
        json_object("[1]", "input")
    with pytest.raises(InvalidInput):
        json_object("{not json", "input")


def test_opt_int_bounds():
    assert opt_int("7", "limit", 1, 20) == 7
    assert opt_int(None, "limit") is None
    with pytest.raises(InvalidInput):
        opt_int(21, "limit", 1, 20)
    with pytest.raises(InvalidInput):
        opt_int("x", "limit")


def test_money_stays_a_string_in_summaries():
    price = {"rule": {"type": "flat", "amount_usd": "0.0005"}, "charges": {"NO_RESULT": "0.00"}}
    assert price_line(price) == "flat $0.0005 | NO_RESULT $0.00"
    run = {
        "status": "COMPLETED",
        "provider": "ahrefs",
        "endpoint": "/v3/public/domain-rating-free",
        "endpoint_version": 1,
        "provider_response": {"http_status": 404},
        "charge_usd": "0.0005",
        "charge_basis": {"clause": "rule", "quantity": None},
        "run_url": "https://app.glasser.ai/runs/run-1",
    }
    text = summarize_run(run, "key-1")
    assert "Run COMPLETED" in text
    assert "Provider answered HTTP 404" in text
    assert "Charge: $0.0005 (rule)" in text
    assert "https://app.glasser.ai/runs/run-1" in text
    assert "key-1" in text


def test_search_summary_mentions_cursor_and_caveat():
    text = summarize_search({"data": [], "total": 12, "next_cursor": "abc"})
    assert "next_cursor: abc" in text
    assert "Low scores do not show" in text
