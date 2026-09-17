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
    req_str,
    summarize_inspect,
)


class InspectTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            provider = req_str(tool_parameters.get("provider"), "provider")
            endpoint = req_str(tool_parameters.get("endpoint"), "endpoint")
            version = opt_int(tool_parameters.get("endpoint_version"), "endpoint_version", 1)
            detail = client_for(self).inspect(provider, endpoint, version)
        except InvalidInput as e:
            yield from invalid_input_messages(self, str(e))
            return
        except GlasserApiError as e:
            yield from error_messages(self, e)
            return
        yield self.create_json_message(detail)
        yield self.create_text_message(summarize_inspect(detail))
