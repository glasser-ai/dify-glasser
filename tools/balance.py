from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.glasser_client import GlasserApiError
from utils.tool_support import client_for, error_messages, summarize_balance


class BalanceTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = client_for(self).balance()
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(result)
        yield self.create_text_message(summarize_balance(result))
