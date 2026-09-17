from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import GlasserApiError
from utils.tool_support import (
    InvalidInput,
    client_for,
    error_messages,
    invalid_input_messages,
    req_str,
    summarize_run,
)


class RunsStopTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            run = client_for(self).stop_run(req_str(tool_parameters.get("run_id"), "run_id"))
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(run)
        yield self.create_text_message(summarize_run(run))
