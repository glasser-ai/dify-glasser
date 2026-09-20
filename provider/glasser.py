from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.glasser_client import CONSOLE_HINT, GlasserApiError, GlasserClient


class GlasserProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """Validate the Key against GET /v1/balance.

        The balance endpoint is the cheapest authentication probe the API
        publishes: a valid Key gets the balance triple, an invalid one gets
        HTTP 401. Nothing is charged either way.
        """
        api_key = (credentials.get("glasser_api_key") or "").strip()
        if not api_key:
            raise ToolProviderCredentialValidationError(
                f"A Glasser Key is required. {CONSOLE_HINT}"
            )
        try:
            GlasserClient(api_key).balance()
        except GlasserApiError as e:
            if e.code == "unauthorized":
                raise ToolProviderCredentialValidationError(
                    f"Invalid or missing API key. {CONSOLE_HINT} Paste it exactly as issued."
                ) from e
            raise ToolProviderCredentialValidationError(
                f"Could not verify the Glasser Key ({e.code}): {e.message}"
            ) from e
        except Exception as e:  # network failures, unexpected payloads
            raise ToolProviderCredentialValidationError(
                f"Could not verify the Glasser Key: {e}"
            ) from e
