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
    opt_int,
    opt_str,
    summarize_runs_list,
)


class RunsListTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = client_for(self).list_runs(
                limit=opt_int(tool_parameters.get("limit"), "limit", 1),
                cursor=opt_str(tool_parameters.get("cursor")),
                status=opt_str(tool_parameters.get("status")),
                provider=opt_str(tool_parameters.get("provider")),
                endpoint=opt_str(tool_parameters.get("endpoint")),
            )
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(result)
        yield self.create_text_message(summarize_runs_list(result))
