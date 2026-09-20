"""Offline tests: no network. The API is replaced by a fake urlopen."""

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import glasser_client as gc  # noqa: E402
from utils import gtm_schema  # noqa: E402
from utils.capability import request_body  # noqa: E402
from utils.tool_support import fit_output, summarize_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


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


# ------------------------------------------------------------------ client


def test_missing_key_is_unauthorized_before_any_call():
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("   ")
    assert e.value.code == "unauthorized"


def test_solution_run_posts_the_body_with_an_idempotency_key(fake_api):
    calls, script = fake_api
    script.append(_Response(200, {"id": "run-1", "status": "COMPLETED"}))
    status, run = gc.GlasserClient("gl_test").solution_run(
        "gtm", "people_search", {"action": "search", "job_titles": ["CTO"]}, "key-1", 5
    )
    req = calls[0]
    assert status == 200 and run["id"] == "run-1"
    assert req.full_url == "https://api.glasser.ai/v1/solutions/gtm/people_search"
    assert req.get_method() == "POST"
    assert req.get_header("Authorization") == "Bearer gl_test"
    assert req.get_header("Idempotency-key") == "key-1"
    assert req.get_header("User-agent").startswith("glasser-dify-plugin/")
    assert json.loads(req.data) == {"action": "search", "job_titles": ["CTO"]}


def test_solution_run_retry_reuses_idempotency_key(fake_api):
    calls, script = fake_api
    script.append(urllib.error.URLError("reset"))
    script.append(_Response(200, {"id": "run-1", "status": "COMPLETED"}))
    status, run = gc.GlasserClient("gl_test").solution_run("gtm", "web_research", {"query": "x"}, "key-1", 5)
    assert status == 200 and run["id"] == "run-1"
    assert [c.get_header("Idempotency-key") for c in calls] == ["key-1", "key-1"]


def test_error_envelope_passes_through(fake_api):
    _calls, script = fake_api
    envelope = {
        "error": {
            "code": "validation_failed",
            "message": "provider ahrefs does not serve action enrich",
            "details": {"providers": ["apollo", "pdl"]},
        },
        "request_id": "req-1",
    }
    script.append(_http_error(400, envelope))
    with pytest.raises(gc.GlasserApiError) as e:
        gc.GlasserClient("gl_test").solution_run("gtm", "company_intelligence", {"domain": "x.com"}, "k", 5)
    assert e.value.code == "validation_failed"
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


def test_wait_run_polls_until_terminal(fake_api):
    calls, script = fake_api
    script.append(_Response(200, {"id": "run-1", "status": "RUNNING"}))
    script.append(_Response(200, {"id": "run-1", "status": "COMPLETED"}))
    run = gc.GlasserClient("gl_test").wait_run({"id": "run-1", "status": "QUEUED"}, budget_s=30, poll_s=0)
    assert run["status"] == "COMPLETED"
    assert calls[-1].full_url.endswith("/v1/runs/run-1")


# ------------------------------------------------------------ request body


def test_request_body_splits_lists_and_drops_blanks():
    body = request_body(
        "people_search",
        {"action": "search", "provider": "auto", "job_titles": "CTO, VP Engineering, ", "locations": "", "email": None},
    )
    assert body == {"action": "search", "provider": "auto", "job_titles": ["CTO", "VP Engineering"]}


def test_request_body_passes_platform_and_mode_through():
    body = request_body("social_research", {"platform": "reddit", "mode": "profile", "handle": " javascript "})
    assert body == {"platform": "reddit", "mode": "profile", "handle": "javascript"}


def test_request_body_keeps_people_keywords_as_text_and_seo_keywords_as_a_list():
    assert request_body("people_search", {"keywords": "ai, agents"}) == {"keywords": "ai, agents"}
    assert request_body("seo_research", {"keywords": "ai, agents"}) == {"keywords": ["ai", "agents"]}


def test_request_body_coerces_integer_fields_and_rejects_non_numbers(monkeypatch):
    # No tool shows an integer field today; the mechanism stays generic for when one does.
    monkeypatch.setitem(gtm_schema.INT_FIELDS, "people_search", ["limit"])
    assert request_body("people_search", {"job_titles": "CTO", "limit": "5"})["limit"] == 5
    with pytest.raises(ValueError):
        request_body("people_search", {"job_titles": "CTO", "limit": "many"})


# ------------------------------------------------------- generated files


def test_every_capability_has_a_tool_yaml_and_the_provider_lists_it():
    provider = yaml.safe_load((ROOT / "provider" / "glasser.yaml").read_text(encoding="utf-8"))
    listed = {Path(p).stem for p in provider["tools"]}
    assert listed == set(gtm_schema.CAPABILITIES)
    for capability in gtm_schema.CAPABILITIES:
        doc = yaml.safe_load((ROOT / "tools" / f"{capability}.yaml").read_text(encoding="utf-8"))
        assert doc["identity"]["name"] == capability
        assert doc["extra"]["python"]["source"] == f"tools/{capability}.py"
        assert (ROOT / "tools" / f"{capability}.py").exists()
        names = [p["name"] for p in doc["parameters"]]
        for field in gtm_schema.LIST_FIELDS[capability] + gtm_schema.INT_FIELDS[capability]:
            assert field in names, f"{capability}: {field} is in the schema hints but not in the yaml"


# --------------------------------------------------------------- summaries


def test_money_stays_a_string_in_summaries():
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


def test_fit_output_trims_large_payloads_but_keeps_shape():
    big = {"status": "COMPLETED", "run_url": "u", "output": {"Results": [{"Paths": [{"Technologies": [{"Name": f"t{i}", "Desc": "x" * 500} for i in range(3000)]}]}]}}
    out = fit_output(big, budget_chars=20_000)
    assert out["output_truncated"] is True
    assert len(json.dumps(out)) <= 20_000
    techs = out["output"]["Results"][0]["Paths"][0]["Technologies"]
    assert techs[0]["Name"] == "t0" and techs[-1].endswith("more items omitted")
    small = {"status": "COMPLETED", "output": {"a": 1}}
    assert fit_output(small) is small


def test_plugin_version_matches_manifest():
    declared = yaml.safe_load((Path(__file__).resolve().parents[1] / "manifest.yaml").read_text())["version"]
    assert gc.PLUGIN_VERSION == str(declared)
    assert f"glasser-dify-plugin/{declared} " in gc.USER_AGENT
