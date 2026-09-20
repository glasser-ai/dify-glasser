"""Glasser API client for the Dify plugin. Standard library only.

One Key, one host (https://api.glasser.ai). A success returns the API's own
JSON body untouched. An error raises GlasserApiError carrying the API's
error envelope ({"error": {"code", "message", ...}, "request_id"}) unchanged,
so a tool can hand the same object to the agent that a direct HTTP caller
would see.

The Key comes from the Dify provider credential ``glasser_api_key``. It is
never read from the environment or from disk: this code runs inside Dify's
plugin sandbox.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

# The host is written into the urlopen call itself, not held in a variable:
# the Marketplace scanner extracts hosts from the call's own arguments and
# counts any call without one as "address built at runtime".
HOST = "api.glasser.ai"
CONSOLE_HINT = "Create one in the Glasser console under Keys."
TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "STOPPED"})

# Rate-limit backoff cap: the API's retry_after_ms is honoured up to this.
_MAX_RATE_LIMIT_WAIT_S = 15.0


# Kept equal to manifest.yaml by tests/test_offline.py; a constant rather than
# a read of the manifest, so the plugin touches no file at runtime.
PLUGIN_VERSION = "0.4.2"

USER_AGENT = f"glasser-dify-plugin/{PLUGIN_VERSION} (+https://github.com/glasser-ai/dify-glasser)"


class GlasserApiError(Exception):
    """An error answer from the API, or a transport failure shaped like one."""

    def __init__(self, status: int, envelope: dict[str, Any]):
        self.status = status
        self.envelope = envelope
        error = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
        self.code: str = str(error.get("code") or status or "error")
        self.message: str = str(error.get("message") or "Request failed.")
        self.retry_after_ms: Optional[int] = error.get("retry_after_ms")
        self.request_id: Optional[str] = envelope.get("request_id")
        super().__init__(f"[{self.code}] {self.message}")

    def payload(self) -> dict[str, Any]:
        """The envelope as the agent should see it: the API's own object."""
        return dict(self.envelope)


def _synthetic(code: str, message: str, status: int = 0) -> GlasserApiError:
    return GlasserApiError(status, {"error": {"code": code, "message": message}, "request_id": None})


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None and v != ""}


class GlasserClient:
    def __init__(self, api_key: str):
        key = (api_key or "").strip()
        if not key:
            raise _synthetic("unauthorized", f"Missing Glasser Key. {CONSOLE_HINT}", 401)
        self.api_key = key

    # ------------------------------------------------------------------ core

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = None,
        query: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        retry_transport: bool = True,
    ) -> tuple[int, Any]:
        """One API call. Returns (http_status, parsed_json_or_None).

        Retries: a 429 is retried once after the API's retry_after_ms; a
        transport failure (connection, timeout) is retried once when
        ``retry_transport`` is set. Callers pass retry_transport=False for
        calls whose second attempt would not be a plain read.
        """
        if query:
            path = f"{path}?{urllib.parse.urlencode(_clean(query), quote_via=urllib.parse.quote)}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        hdrs = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        if headers:
            hdrs.update(headers)

        rate_limit_retried = False
        transport_retried = False
        while True:
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(
                        f"https://api.glasser.ai{path}", data=data, headers=hdrs, method=method
                    ),
                    timeout=timeout,
                ) as response:
                    raw = response.read().decode("utf-8")
                    return response.status, (json.loads(raw) if raw.strip() else None)
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", errors="replace")
                try:
                    envelope = json.loads(raw)
                    if not (isinstance(envelope, dict) and isinstance(envelope.get("error"), dict)):
                        raise ValueError
                except (json.JSONDecodeError, ValueError):
                    envelope = {
                        "error": {"code": str(e.code), "message": raw[:500] or str(e.reason)},
                        "request_id": None,
                    }
                err = GlasserApiError(e.code, envelope)
                if e.code == 429 and not rate_limit_retried:
                    rate_limit_retried = True
                    time.sleep(min((err.retry_after_ms or 1000) / 1000.0, _MAX_RATE_LIMIT_WAIT_S))
                    continue
                raise err
            except urllib.error.URLError as e:
                if retry_transport and not transport_retried:
                    transport_retried = True
                    time.sleep(2)
                    continue
                raise _synthetic("transport_error", f"Could not reach {HOST}: {e.reason}")
            except (TimeoutError, OSError) as e:
                if retry_transport and not transport_retried:
                    transport_retried = True
                    time.sleep(2)
                    continue
                if isinstance(e, TimeoutError):
                    raise _synthetic(
                        "transport_timeout",
                        f"No response within {timeout:.0f}s. The outcome is unknown: for a run, "
                        "retry with the SAME idempotency_key.",
                    )
                raise _synthetic("transport_error", f"{type(e).__name__}: {e}")
            except json.JSONDecodeError:
                raise _synthetic("bad_response", "The API returned a non-JSON body.")

    # ------------------------------------------------------------ operations

    def balance(self) -> dict[str, Any]:
        """GET /v1/balance: the free probe the provider uses to validate a Key."""
        return self.request("GET", "/v1/balance")[1]

    def solution_run(
        self,
        solution: str,
        capability: str,
        body: dict[str, Any],
        idempotency_key: str,
        timeout: float,
    ) -> tuple[int, dict[str, Any]]:
        """POST /v1/solutions/<solution>/<capability>. The answer is a run,
        the same object POST /v1/runs returns: 200 terminal, 202 in flight.

        The API picks the endpoint (or follows ``provider``), translates the
        flat fields and falls back on provider errors. The transport retry
        inside ``request`` reuses the same Idempotency-Key, so a retry after
        a dropped connection is a read of the original run, never a second
        charge.
        """
        path = f"/v1/solutions/{urllib.parse.quote(solution, safe='')}/{urllib.parse.quote(capability, safe='')}"
        return self.request(
            "POST",
            path,
            body=body,
            headers={"Idempotency-Key": idempotency_key},
            timeout=timeout,
        )

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/runs/{urllib.parse.quote(run_id, safe='')}")[1]

    def wait_run(self, run: dict[str, Any], budget_s: float, poll_s: float = 2.0) -> dict[str, Any]:
        """Poll GET /v1/runs/{id} until the run is terminal or the budget is spent."""
        deadline = time.monotonic() + budget_s
        while run.get("status") not in TERMINAL_STATUSES and time.monotonic() < deadline:
            time.sleep(min(poll_s, max(0.0, deadline - time.monotonic())))
            run = self.get_run(run["id"])
        return run
