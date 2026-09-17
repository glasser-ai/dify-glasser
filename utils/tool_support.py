"""Helpers shared by the tools: the client, error messages, the run summary,
and the output size budget.

The summary is the text message next to the JSON message. It repeats the
facts an agent must report — run status, what the provider said, the exact
charge, the run URL — and nothing else. Money stays a decimal string.
"""

import json
from typing import Any, Iterable, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import GlasserApiError, GlasserClient


def client_for(tool: Tool) -> GlasserClient:
    return GlasserClient(tool.runtime.credentials.get("glasser_api_key", ""))


def error_messages(tool: Tool, err: GlasserApiError) -> Iterable[ToolInvokeMessage]:
    yield tool.create_json_message(err.payload())
    line = f"Glasser error {err.code}: {err.message}"
    if err.retry_after_ms:
        line += f" (retry_after_ms {err.retry_after_ms})"
    if err.request_id:
        line += f" [request_id {err.request_id}]"
    yield tool.create_text_message(line)


def invalid_input_messages(tool: Tool, message: str) -> Iterable[ToolInvokeMessage]:
    yield tool.create_json_message(
        {"error": {"code": "invalid_input", "message": message}, "request_id": None}
    )
    yield tool.create_text_message(f"Invalid input: {message} Nothing was run and nothing was charged.")


def summarize_run(run: dict[str, Any], idempotency_key: Optional[str] = None) -> str:
    status = run.get("status")
    truncated = run.get("output_truncated")
    provider_response = run.get("provider_response") if isinstance(run.get("provider_response"), dict) else None
    basis = run.get("charge_basis") if isinstance(run.get("charge_basis"), dict) else {}
    lines = [f"Run {status}: {run.get('provider')} {run.get('endpoint')} v{run.get('endpoint_version')}"]
    if provider_response:
        lines.append(f"Provider answered HTTP {provider_response.get('http_status')}")
    elif status in {"QUEUED", "RUNNING"}:
        lines.append("Provider has not answered yet; the run URL shows its progress.")
    failure = run.get("failure")
    if isinstance(failure, dict) and failure:
        lines.append(f"Failure: {failure.get('code') or ''} {failure.get('message') or ''}".strip())
    if run.get("charge_usd") is not None:
        lines.append(f"Charge: ${run.get('charge_usd')} ({basis.get('clause', 'clause unknown')})")
    if run.get("run_url"):
        lines.append(f"Run URL: {run.get('run_url')}")
    if truncated:
        lines.append("Output was trimmed to fit the context; the full provider output is at the run URL.")
    if idempotency_key:
        lines.append(f"idempotency_key: {idempotency_key} (reuse it to retry; it never charges twice)")
    return "\n".join(lines)


# ------------------------------------------------------------ size budget


def trim_payload(value: Any, max_items: int, max_chars: int) -> Any:
    """Cap every list to max_items and every string to max_chars, recursively.

    Structure is kept: keys are never renamed or dropped, so the agent still
    sees the shape of the provider's answer. A cut list gets a trailing
    marker string saying how many items were left out.
    """
    if isinstance(value, dict):
        return {k: trim_payload(v, max_items, max_chars) for k, v in value.items()}
    if isinstance(value, list):
        head = [trim_payload(v, max_items, max_chars) for v in value[:max_items]]
        if len(value) > max_items:
            head.append(f"... {len(value) - max_items} more items omitted")
        return head
    if isinstance(value, str) and len(value) > max_chars:
        return value[:max_chars] + f"... [{len(value) - max_chars} more characters omitted]"
    return value


def fit_output(run: dict[str, Any], budget_chars: int = 60_000) -> dict[str, Any]:
    """Shrink run.output until the run serialises under budget_chars.

    Provider payloads can run to megabytes (a full technology stack, a
    backlink dump). The agent's context cannot hold that, and Dify feeds
    the whole JSON message to the model. The full output stays in the run
    itself, reachable at run_url.
    """
    if len(json.dumps(run)) <= budget_chars:
        return run
    output = run.get("output")
    for max_items, max_chars in ((50, 4000), (25, 2000), (10, 1000), (5, 500), (3, 200)):
        trimmed = trim_payload(output, max_items, max_chars)
        candidate = {**run, "output": trimmed, "output_truncated": True,
                     "output_note": "Output trimmed to fit the context; the full provider output is at run_url."}
        if len(json.dumps(candidate)) <= budget_chars:
            return candidate
    return {**run, "output": None, "output_truncated": True,
            "output_note": "Output too large for the context; read it at run_url."}
