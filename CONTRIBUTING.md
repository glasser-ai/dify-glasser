# Contributing

```sh
uv sync                              # Python 3.12, dify_plugin, pytest
uv run pytest                        # offline tests, no network
uv run python scripts/gen_tools.py   # regenerate tools/*.yaml from https://glasser.ai/docs/openapi.json
dify plugin package .                # builds glasser.difypkg
```

Remote debugging against a Dify workspace: create `.env` with `INSTALL_METHOD=remote`, `REMOTE_INSTALL_URL` and `REMOTE_INSTALL_KEY` from the workspace's plugin page, then `uv run python -m main`.

## How a call works

1. The tool sends its parameters as they are to `POST /v1/solutions/gtm/<capability>` with a fresh idempotency key. Comma-separated fields become arrays; nothing else is changed.
2. Glasser resolves `(action, provider)` to one endpoint, translates the fields into that endpoint's native input, runs it, and on a provider error under `provider = auto` moves to the next source. It never falls back on an empty answer: "no result" is an answer.
3. The result is the run exactly as `POST /v1/runs` returns it: `provider` and `endpoint` say who served the call, `input` is what was sent, `output` is the provider's own payload, `charge_usd` is the exact charge, `run_url` opens it in the console.

The plugin holds no routing table and no state. The parameters of each tool are generated from the Glasser OpenAPI document (`scripts/gen_tools.py`), so they cannot drift from the API.

## Run statuses

| Status | Meaning |
|---|---|
| `QUEUED` | Accepted, not yet dispatched to the provider |
| `RUNNING` | Dispatched, provider has not answered yet |
| `COMPLETED` | Terminal. The provider answered (its answer may still be a "not found") |
| `FAILED` | Terminal. No usable provider answer; the `failure` block says why |
| `STOPPED` | Terminal. Stopped in the Glasser console before dispatch, charge 0 |
