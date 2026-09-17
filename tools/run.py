import uuid
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import TERMINAL_STATUSES, GlasserApiError
from utils.tool_support import (
    InvalidInput,
    client_for,
    error_messages,
    invalid_input_messages,
    json_object,
    opt_bool,
    opt_int,
    opt_str,
    req_str,
    summarize_run,
)

# Above the longest published sync timeout (inspect prints timeout_ms), and
# under the plugin's MAX_REQUEST_TIMEOUT of 240s set in main.py.
_CREATE_TIMEOUT_S = 120.0
_MAX_WAIT_S = 200


class RunTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            provider = req_str(tool_parameters.get("provider"), "provider")
            endpoint = req_str(tool_parameters.get("endpoint"), "endpoint")
            run_input = json_object(tool_parameters.get("input"), "input")
            version = opt_int(tool_parameters.get("endpoint_version"), "endpoint_version", 1)
            # The plugin generates the key only when the caller sent none. A
            # transport retry inside the client reuses it, so a dropped
            # connection reads the original run instead of paying twice.
            idempotency_key = opt_str(tool_parameters.get("idempotency_key")) or str(uuid.uuid4())
            wait = opt_bool(tool_parameters.get("wait"), True)
            wait_timeout = opt_int(tool_parameters.get("wait_timeout"), "wait_timeout", 1, _MAX_WAIT_S) or 180

            client = client_for(self)
            _status, run = client.create_run(
                provider, endpoint, run_input, version, idempotency_key, _CREATE_TIMEOUT_S
            )
            if wait and run.get("status") not in TERMINAL_STATUSES:
                run = client.wait_run(run, budget_s=float(wait_timeout))
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return

        yield self.create_json_message({**run, "idempotency_key": idempotency_key})
        yield self.create_text_message(summarize_run(run, idempotency_key))
