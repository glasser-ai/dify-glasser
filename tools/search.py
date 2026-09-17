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
    summarize_search,
)


class SearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            query = opt_str(tool_parameters.get("query"))
            limit = opt_int(tool_parameters.get("limit"), "limit", 1, 20)
            cursor = opt_str(tool_parameters.get("cursor"))
            result = client_for(self).search(query, limit, cursor)
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(result)
        yield self.create_text_message(summarize_search(result))
