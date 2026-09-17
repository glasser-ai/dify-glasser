"""Shared executor for the capability tools.

A capability tool resolves (action, provider) to one Glasser endpoint through
utils.routes, builds the provider-native input from its flat parameters,
and runs that endpoint. The result is the run as the API returned it, plus
a `routed` block saying which endpoint served the call, so the agent can
name the source and the user can inspect it in the console.
"""

import uuid
from typing import Any, Iterable

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils import routes
from utils.glasser_client import TERMINAL_STATUSES, GlasserApiError
from utils.tool_support import client_for, error_messages, invalid_input_messages, summarize_run

_CREATE_TIMEOUT_S = 120.0
_WAIT_BUDGET_S = 180.0


def run_capability(tool: Tool, tool_name: str, params: dict[str, Any]) -> Iterable[ToolInvokeMessage]:
    try:
        route, provider = routes.resolve(tool_name, params.get("action"), params.get("provider"), params)
        run_input = route.build(params)
    except routes.InvalidInput as e:
        yield from invalid_input_messages(tool, str(e))
        return

    idempotency_key = str(uuid.uuid4())
    try:
        client = client_for(tool)
        _status, run = client.create_run(
            route.provider, route.endpoint, run_input, route.endpoint_version, idempotency_key, _CREATE_TIMEOUT_S
        )
        if run.get("status") not in TERMINAL_STATUSES:
            run = client.wait_run(run, budget_s=_WAIT_BUDGET_S)
    except GlasserApiError as e:
        payload = e.payload()
        payload["routed"] = _routed(route, provider, params, run_input)
        yield tool.create_json_message(payload)
        yield tool.create_text_message(
            f"Glasser error {e.code} while running {route.provider} {route.endpoint}: {e.message}"
            + (f" [request_id {e.request_id}]" if e.request_id else "")
        )
        return

    yield tool.create_json_message({**run, "idempotency_key": idempotency_key, "routed": _routed(route, provider, params, run_input)})
    header = f"{tool_name}.{params.get('action')} via {provider}" + (" (auto)" if (params.get("provider") or "auto") == "auto" else "")
    yield tool.create_text_message(header + "\n" + summarize_run(run))


def _routed(route: routes.Route, provider: str, params: dict[str, Any], run_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": params.get("action"),
        "provider": provider,
        "auto": (params.get("provider") or "auto") == "auto",
        "endpoint": route.endpoint,
        "endpoint_version": route.endpoint_version,
        "input": run_input,
        "note": route.note or None,
    }
