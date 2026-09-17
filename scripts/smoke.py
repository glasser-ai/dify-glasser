"""Live smoke test against api.glasser.ai. Needs GLASSER_API_KEY.

Drives each tool class the way the Dify runtime does, minus the daemon:
a ToolRuntime with the credential, and the messages a tool yields.
The run step spends real money (the cheapest catalog endpoint, printed
with its price before the call). Pass --no-run to skip it.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dify_plugin.entities.tool import ToolInvokeMessage, ToolRuntime  # noqa: E402

from tools.balance import BalanceTool  # noqa: E402
from tools.inspect import InspectTool  # noqa: E402
from tools.run import RunTool  # noqa: E402
from tools.runs_get import RunsGetTool  # noqa: E402
from tools.runs_list import RunsListTool  # noqa: E402
from tools.runs_stop import RunsStopTool  # noqa: E402
from tools.search import SearchTool  # noqa: E402

KEY = os.environ.get("GLASSER_API_KEY", "")
if not KEY:
    sys.exit("GLASSER_API_KEY is not set")


def make(cls):
    tool = cls.__new__(cls)
    tool.runtime = ToolRuntime(credentials={"glasser_api_key": KEY}, user_id=None, session_id=None)
    tool.response_type = ToolInvokeMessage  # set by Tool.__init__ in the real runtime
    return tool


def invoke(cls, params):
    print(f"\n== {cls.__name__} {json.dumps(params)}")
    payload = None
    for message in make(cls)._invoke(params):
        if message.type.value == "json":
            payload = message.message.json_object
            print("json:", json.dumps(payload)[:600])
        else:
            print("text:", message.message.text)
    return payload


invoke(BalanceTool, {})
found = invoke(SearchTool, {"query": "domain rating", "limit": 3})
row = found["data"][0]
detail = invoke(InspectTool, {"provider": row["provider"], "endpoint": row["endpoint"]})
listed = invoke(RunsListTool, {"limit": 2})
if listed and listed["data"]:
    invoke(RunsGetTool, {"run_id": listed["data"][0]["id"]})
    invoke(RunsStopTool, {"run_id": listed["data"][0]["id"]})  # terminal: expect 409 conflict
invoke(RunTool, {"provider": "x", "endpoint": "/y", "input": "{bad"})  # invalid_input, no call
invoke(InspectTool, {"provider": "nope", "endpoint": "/nope"})  # not_found envelope

if "--no-run" not in sys.argv:
    price = detail["price"]["rule"]
    print(f"\nabout to run {row['provider']} {row['endpoint']} at ${price.get('amount_usd')} {price.get('type')}")
    run = invoke(
        RunTool,
        {
            "provider": row["provider"],
            "endpoint": row["endpoint"],
            "endpoint_version": detail["endpoint_version"],
            "input": json.dumps(detail["sample_input"] or {}),
        },
    )
    replay = invoke(
        RunTool,
        {
            "provider": row["provider"],
            "endpoint": row["endpoint"],
            "endpoint_version": detail["endpoint_version"],
            "input": json.dumps(detail["sample_input"] or {}),
            "idempotency_key": run["idempotency_key"],  # same body, same key: a read
        },
    )
    print("\nreplay returned the same run:", replay["id"] == run["id"])
invoke(BalanceTool, {})
