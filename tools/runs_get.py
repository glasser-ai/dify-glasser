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
    opt_bool,
    opt_int,
    req_str,
    summarize_run,
)


class RunsGetTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            run_id = req_str(tool_parameters.get("run_id"), "run_id")
            wait = opt_bool(tool_parameters.get("wait"), False)
            wait_timeout = opt_int(tool_parameters.get("wait_timeout"), "wait_timeout", 1, 200) or 180
            client = client_for(self)
            run = client.get_run(run_id)
            if wait and run.get("status") not in TERMINAL_STATUSES:
                run = client.wait_run(run, budget_s=float(wait_timeout))
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(run)
        yield self.create_text_message(summarize_run(run))
