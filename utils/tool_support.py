"""Helpers shared by the seven tools: credentials, input parsing, summaries.

Summaries are the text message next to the JSON message. They repeat the
facts an agent must report — run status, what the provider said, the exact
charge, the run URL — and nothing else. Money stays a decimal string.
"""

import json
from typing import Any, Iterable, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import GlasserApiError, GlasserClient


class InvalidInput(Exception):
    """A tool parameter the plugin cannot turn into a request.

    Raised before any API call, so nothing was created and nothing charged.
    """


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


def opt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def req_str(value: Any, name: str) -> str:
    text = opt_str(value)
    if text is None:
        raise InvalidInput(f"'{name}' is required.")
    return text


def opt_int(value: Any, name: str, minimum: Optional[int] = None, maximum: Optional[int] = None) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        raise InvalidInput(f"'{name}' must be an integer.")
    if minimum is not None and number < minimum:
        raise InvalidInput(f"'{name}' must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise InvalidInput(f"'{name}' must be at most {maximum}.")
    return number


def opt_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def json_object(value: Any, name: str) -> dict[str, Any]:
    """A JSON object from a dict, a JSON string, or nothing (empty object)."""
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as e:
            raise InvalidInput(f"'{name}' is not valid JSON: {e.msg} at position {e.pos}.")
        if not isinstance(parsed, dict):
            raise InvalidInput(f"'{name}' must be a JSON object, not {type(parsed).__name__}.")
        return parsed
    raise InvalidInput(f"'{name}' must be a JSON object.")


# --------------------------------------------------------------- summaries


def price_line(price: Optional[dict[str, Any]]) -> str:
    if not isinstance(price, dict):
        return "price unknown"
    rule = price.get("rule") if isinstance(price.get("rule"), dict) else {}
    rule_type = rule.get("type", "?")
    amount = rule.get("amount_usd")
    parts = [f"{rule_type} ${amount}" if amount is not None else rule_type]
    for key, value in rule.items():
        if key not in {"type", "amount_usd"}:
            parts.append(f"{key}={value}")
    charges = price.get("charges") if isinstance(price.get("charges"), dict) else {}
    if charges:
        parts.append("; ".join(f"{k} ${v}" for k, v in charges.items()))
    return " | ".join(parts)


def summarize_search(result: dict[str, Any]) -> str:
    rows = result.get("data") or []
    lines = [f"{len(rows)} of {result.get('total', '?')} endpoints:"]
    for row in rows:
        rule = (row.get("price") or {}).get("rule") or {}
        amount = rule.get("amount_usd")
        price = f"${amount} {rule.get('type', '')}".strip() if amount is not None else "price: inspect"
        lines.append(
            f"- {row.get('provider')} {row.get('endpoint')} v{row.get('endpoint_version')} "
            f"({row.get('provider_label')}): {row.get('name')} | {price} | {row.get('run_mode')} "
            f"| score {row.get('score')}"
        )
    cursor = result.get("next_cursor")
    if cursor:
        lines.append(f"next_cursor: {cursor}")
    lines.append("Inspect an endpoint before the first run. Low scores do not show that a capability is absent; try other words.")
    return "\n".join(lines)


def summarize_inspect(detail: dict[str, Any]) -> str:
    schema = detail.get("input_schema") if isinstance(detail.get("input_schema"), dict) else {}
    required = schema.get("required") or []
    properties = list((schema.get("properties") or {}).keys())
    lines = [
        f"{detail.get('provider')} {detail.get('endpoint')} v{detail.get('endpoint_version')} "
        f"({detail.get('provider_label')}): {detail.get('name')}",
        f"Price: {price_line(detail.get('price'))}",
        f"Run mode: {detail.get('run_mode')}, timeout_ms {detail.get('timeout_ms')}, method {detail.get('method')}",
        f"Input fields: {', '.join(properties) or 'none'}; required: {', '.join(required) or 'none'}",
    ]
    if detail.get("sample_input") is not None:
        lines.append(f"Sample input: {json.dumps(detail.get('sample_input'))}")
    if detail.get("doc_url"):
        lines.append(f"Provider docs: {detail.get('doc_url')}")
    return "\n".join(lines)


def summarize_run(run: dict[str, Any], idempotency_key: Optional[str] = None) -> str:
    status = run.get("status")
    provider_response = run.get("provider_response") if isinstance(run.get("provider_response"), dict) else None
    basis = run.get("charge_basis") if isinstance(run.get("charge_basis"), dict) else {}
    lines = [f"Run {status}: {run.get('provider')} {run.get('endpoint')} v{run.get('endpoint_version')}"]
    if provider_response:
        lines.append(f"Provider answered HTTP {provider_response.get('http_status')}")
    elif status in {"QUEUED", "RUNNING"}:
        lines.append("Provider has not answered yet; poll runs_get with the run id.")
    failure = run.get("failure")
    if isinstance(failure, dict) and failure:
        lines.append(f"Failure: {failure.get('code') or ''} {failure.get('message') or ''}".strip())
    if run.get("charge_usd") is not None:
        lines.append(f"Charge: ${run.get('charge_usd')} ({basis.get('clause', 'clause unknown')})")
    if run.get("run_url"):
        lines.append(f"Run URL: {run.get('run_url')}")
    if idempotency_key:
        lines.append(f"idempotency_key: {idempotency_key} (reuse it to retry; it never charges twice)")
    return "\n".join(lines)


def summarize_runs_list(result: dict[str, Any]) -> str:
    rows = result.get("data") or []
    lines = [f"{len(rows)} runs (newest first):"]
    for run in rows:
        lines.append(
            f"- {run.get('id')} {run.get('status')} {run.get('provider')} {run.get('endpoint')} "
            f"charge ${run.get('charge_usd')} {run.get('created_at')}"
        )
    if result.get("next_cursor"):
        lines.append(f"next_cursor: {result.get('next_cursor')}")
    return "\n".join(lines)


def summarize_balance(result: dict[str, Any]) -> str:
    return (
        f"Balance ${result.get('balance_usd')}, held ${result.get('held_usd')}, "
        f"available ${result.get('available_usd')} (exact decimal strings; do not use float arithmetic)."
    )
