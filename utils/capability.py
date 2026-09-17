"""One call per tool: POST /v1/solutions/gtm/<capability> and hand back the run.

The plugin adds nothing to the API: no routing, no parameter translation,
no fallback. Those live in Glasser. This module turns Dify's flat string
parameters into the request body the contract expects (comma-separated
strings become arrays, numbers become integers, blanks are dropped), sends
it with an idempotency key, waits for an in-flight run, and trims a large
output to fit the model's context.
"""

import uuid
from typing import Any, Iterable

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import TERMINAL_STATUSES, GlasserApiError
from utils.gtm_schema import INT_FIELDS, LIST_FIELDS, SOLUTION
from utils.tool_support import client_for, error_messages, fit_output, invalid_input_messages, summarize_run

_CREATE_TIMEOUT_S = 120.0
_WAIT_BUDGET_S = 180.0


def request_body(capability: str, params: dict[str, Any]) -> dict[str, Any]:
    """The contract's request body from Dify's parameters.

    Raises ValueError for a number that is not one; everything else is the
    API's to validate, so its own error envelope reaches the agent.
    """
    lists = LIST_FIELDS.get(capability, [])
    integers = INT_FIELDS.get(capability, [])
    body: dict[str, Any] = {}
    for name, value in params.items():
        if value is None or value == "":
            continue
        if name in lists:
            items = [s.strip() for s in str(value).split(",")] if isinstance(value, str) else [str(s).strip() for s in value]
            items = [s for s in items if s]
            if items:
                body[name] = items
        elif name in integers:
            try:
                body[name] = int(float(value))
            except (TypeError, ValueError):
                raise ValueError(f"'{name}' must be a whole number.")
        else:
            body[name] = value.strip() if isinstance(value, str) else value
    return body


def run_capability(tool: Tool, capability: str, params: dict[str, Any]) -> Iterable[ToolInvokeMessage]:
    try:
        body = request_body(capability, params)
    except ValueError as e:
        yield from invalid_input_messages(tool, str(e))
        return

    idempotency_key = str(uuid.uuid4())
    try:
        client = client_for(tool)
        _status, run = client.solution_run(SOLUTION, capability, body, idempotency_key, _CREATE_TIMEOUT_S)
        if run.get("status") not in TERMINAL_STATUSES:
            run = client.wait_run(run, budget_s=_WAIT_BUDGET_S)
    except GlasserApiError as e:
        yield from error_messages(tool, e)
        return

    run = fit_output(run)
    yield tool.create_json_message({**run, "idempotency_key": idempotency_key})
    yield tool.create_text_message(summarize_run(run, idempotency_key))
