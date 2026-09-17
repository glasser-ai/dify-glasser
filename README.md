# Glasser

**Author:** glasser-ai
**Version:** 0.1.0
**Type:** tool

Paid third-party API endpoints for Dify agents and workflows through **one Glasser Key**: search the data sources, inspect the exact price, run, pay per call. No signup at each vendor.

Glasser is a broker. It sells runnable third-party API operations ("endpoints") under a single Key. Your agent searches the catalog, inspects an endpoint's contract and price, and runs it. The response is the provider's own output, with the exact charge and a link to the run in the Glasser console.

## Tools

The plugin exposes the same seven verbs as the Glasser MCP server and CLI. Endpoints are never tools: the catalog is data, found at runtime with `search`.

| Tool | What it does |
|---|---|
| **search** | Search the data sources by keyword. Returns provider, endpoint, price, run mode and a relevance score per hit, paginated. |
| **inspect** | One endpoint's execution contract: provider-native input schema, exact price with every charge clause, endpoint version, run mode, timeout. |
| **run** | Execute one endpoint. Charges the workspace per the published price. Returns the run with the provider's output, the exact charge and the run URL. Optionally waits for an async endpoint to settle. |
| **runs_get** | One run by id, with an optional wait until it is terminal. |
| **runs_list** | The workspace's runs, newest first, filtered by status, provider or endpoint. |
| **runs_stop** | Request a stop for an in-flight run. |
| **balance** | Balance, held and available, in USD. Also the cheapest check that the Key works. |

### The flow an agent follows

1. `search` with the capability in plain words ("enrich a company by domain", "domain rating").
2. `inspect` the chosen endpoint. Read the price and the charge clauses before running.
3. `run` with an input built against the inspected `input_schema`, passing the `endpoint_version` from inspect.
4. Report the run status, what the provider said, the charge and the run URL.

### Example prompts

- "What is the Ahrefs domain rating of example.com?"
- "Find the LinkedIn profile and current employer for jane@example.com."
- "Get the top 10 Google results for 'best CRM for startups' in Germany."
- "How much would it cost to enrich 50 companies by domain? Inspect first, do not run."

## Setup

1. **Create a Glasser Key.** Sign in at https://app.glasser.ai, open **Keys**, create a Key (it starts with `gl_`). The workspace needs a balance: runs are prepaid and charged per call.
2. **Install this plugin** in Dify and paste the Key in the provider settings. Validation calls `GET /v1/balance`, which is free.
3. **Attach the tools** to an Agent app, or add them as nodes in a Workflow. All seven tools share the one credential.

### Connection requirements

The plugin makes outbound HTTPS (port 443) requests to **`api.glasser.ai` only**. No other hosts, no inbound connections, no telemetry. It runs in Dify's standard plugin runtime with default permissions (no storage, model or endpoint permissions).

## Usage notes

- **Inspect before the first run.** The price shown by `inspect` is what a normal COMPLETED call costs. The charge clauses list the exceptions, for example `NO_RESULT $0.00` means an empty answer is free. The charge rule may read volume parameters in the input (`num`, `size`, `limit`, arrays of queries), so start small.
- **Two indicators, not one.** A run's status and the provider's response are separate. A COMPLETED run whose provider answered 404 ("person not found") is a normal outcome, charged per the endpoint's clauses. A FAILED run can carry a non-zero charge when the clauses say so.
- **Retries never charge twice.** Every run carries an idempotency key. Pass your own UUID, or let the plugin generate one; the result echoes it as `idempotency_key`. Retry with the same key after a timeout and you get the original run back. The plugin also reuses the key when it retries a dropped connection itself.
- **Async endpoints.** `inspect` shows the run mode. A sync endpoint returns the finished run in the same call. For an async endpoint, `run` waits by default (up to the configurable timeout, 180 seconds) and otherwise returns the in-flight run; poll it with `runs_get`.
- **Money is an exact decimal string** (`"0.0005"`), never a float. Do not do float arithmetic on `charge_usd`, `balance_usd` or the price.
- **Rate limits.** A `rate_limited` error carries `retry_after_ms`. The plugin waits that long once and retries the same call; if it is still limited, the error is returned as is.
- **Errors are the API's own envelope**: `{"error": {"code", "message", ...}, "request_id"}`. `insufficient_balance` means the workspace cannot cover the price; top up in the console instead of retrying.

## Run statuses

| Status | Meaning |
|---|---|
| `QUEUED` | Accepted, not yet dispatched to the provider |
| `RUNNING` | Dispatched, provider has not answered yet |
| `COMPLETED` | Terminal. The provider answered (its answer may still be a "not found") |
| `FAILED` | Terminal. No usable provider answer; the `failure` block says why |
| `STOPPED` | Terminal. Stopped before dispatch, charge 0. A run already sent to the provider completes and is charged |

## Privacy

Tool inputs (queries, provider and endpoint names, run inputs, run ids) and the Key are sent to `api.glasser.ai` to fulfil each request. The plugin stores nothing and collects no telemetry. Requests identify the plugin by name and version in the `User-Agent` header. See [PRIVACY.md](PRIVACY.md).

## Development

```sh
uv sync                      # Python 3.12, dify_plugin, pytest
uv run pytest                # offline tests, no network
dify plugin package .        # builds glasser.difypkg
```

Remote debugging against a Dify workspace: copy `.env.example` to `.env`, fill in the debug key from the workspace's plugin page, then `uv run python -m main`.

## Support

- Source repository: https://github.com/glasser-ai/dify-glasser
- Glasser documentation: https://glasser.ai/docs
- Console: https://app.glasser.ai
- Contact: support@glasser.ai
