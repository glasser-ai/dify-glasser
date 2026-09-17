# Glasser

**Author:** glasser-ai
**Version:** 0.4.0
**Type:** tool

Premium data for Dify agents and workflows through **one Glasser Key**: find people, company intelligence, SEO research, web research, social research and market data, backed by Apollo, People Data Labs, Hunter, BuiltWith, DataForSEO, Semrush, Ahrefs, Serper, Exa, ScrapeCreators, RentCast and more. The agent says what data it wants; Glasser decides which provider serves it. Pay per call, no signup at each vendor.

Glasser is a broker. It sells runnable third-party API operations under a single Key. Each tool call becomes one Glasser run; the response is the provider's own output, with the exact charge and a link to the run in the Glasser console.

## Tools

Six tools, one per Glasser capability. Each takes an `action` (social research takes `platform` + `mode`), a few flat fields, and a `provider`; `provider = auto` (the default) lets Glasser pick the source for that action and fall back to the next one on a provider error, and naming a provider forces it. The agent says what data it wants, not which vendor to call.

| Tool | What the agent can do | Providers behind it |
|---|---|---|
| **Find Prospects** (`people_search`) | Search people by title, seniority, location, employer; enrich one person; find a work email | Apollo, People Data Labs, LeadMagic, ZoomInfo, Hunter, Prospeo |
| **Company Intelligence** (`company_intelligence`) | Profile and firmographics, technology stack, website traffic, competitors, funding rounds, news | Apollo, PDL, Hunter, Prospeo, PredictLeads, LeadMagic, BuiltWith, DataForSEO, Ahrefs, Apify, Serpstat, Serper |
| **Keywords & SEO** (`seo_research`) | Keyword metrics and ideas, Google results, domain organic overview, ranking keywords, backlinks, referring domains, domain rating | Semrush, Serpstat, DataForSEO, Ahrefs, Serper |
| **Web Research** (`web_research`) | Web, news, places, scholar, shopping, image and video search; read a page; answers with sources; similar pages | Serper, SerpApi, Exa, DataForSEO |
| **Social Media Search** (`social_research`) | Reddit, X, YouTube, TikTok, Instagram, LinkedIn: search posts, read a profile or channel, fetch one post, find an account's other profiles | ScrapeCreators, Apify, TikHub |
| **Market Data** (`market_data`) | US property value and rent estimates, property records, for-sale and rental listings, ZIP-code market statistics, stock quotes | RentCast, SerpApi |

The rest of the 1,400+ endpoints in the Glasser catalog are reachable through the Glasser MCP server (`https://api.glasser.ai/mcp`, which Dify can add directly as an MCP tool) and the CLI.

### How a call works

1. The tool sends its parameters as they are to `POST /v1/solutions/gtm/<capability>` with a fresh idempotency key. Comma-separated fields become arrays; nothing else is changed.
2. Glasser resolves `(action, provider)` to one endpoint, translates the fields into that endpoint's native input, runs it, and on a provider error under `provider = auto` moves to the next source. It never falls back on an empty answer: "no result" is an answer.
3. The result is the run exactly as `POST /v1/runs` returns it: `provider` and `endpoint` say who served the call, `input` is what was sent, `output` is the provider's own payload, `charge_usd` is the exact charge, `run_url` opens it in the console.

The plugin holds no routing table and no state. The parameters of each tool are generated from the Glasser OpenAPI document (`scripts/gen_tools.py`), so they cannot drift from the API.

### Example prompts

- "Find CTOs at stripe.com." (people_search, search, apollo: free)
- "What is the work email of Patrick Collison at stripe.com?" (people_search, find_email, hunter)
- "What technologies does shopify.com run?" (company_intelligence, tech_stack, builtwith)
- "Search volume and difficulty for 'espresso machine' in the UK." (seo_research, keyword_overview, semrush)
- "Read https://example.com and summarize it." (web_research, scrape, serper)
- "What are people saying about our brand on Reddit this week?" (social_research, platform reddit, mode search, scrapecreators)
- "What is 5500 Grand Lake Dr, San Antonio worth?" (market_data, property_value, rentcast)
- "Use Ahrefs for that" forces `provider = ahrefs`.

## Setup

1. **Create a Glasser Key.** Sign in at https://app.glasser.ai, open **Keys**, create a Key (it starts with `gl_`). The workspace needs a balance: runs are prepaid and charged per call.
2. **Install this plugin** in Dify and paste the Key in the provider settings. Validation calls `GET /v1/balance`, which is free.
3. **Attach the tools** to an Agent app, or add them as nodes in a Workflow. All six tools share the one credential.

### Connection requirements

The plugin makes outbound HTTPS (port 443) requests to **`api.glasser.ai` only**. No other hosts, no inbound connections, no telemetry. It runs in Dify's standard plugin runtime with default permissions (no storage, model or endpoint permissions).

## Usage notes

- **Each call is one paid run** at the routed endpoint's published price; the run's `provider` and `endpoint` name it. Under `provider = auto` a provider error can lead to a second run at the next source; each run is billed under its own terms and all of them are visible in the console. The charge clauses list the exceptions, for example `NO_RESULT $0.00` means an empty answer is free. Row counts are fixed by Glasser per endpoint; the plugin exposes no volume knobs.
- **Two indicators, not one.** A run's status and the provider's response are separate. A COMPLETED run whose provider answered 404 ("person not found") is a normal outcome, charged per the endpoint's clauses. A FAILED run can carry a non-zero charge when the clauses say so.
- **Retries never charge twice.** Every run carries an idempotency key the plugin generates and echoes as `idempotency_key`; the plugin reuses it when it retries a dropped connection, so a retry reads the original run.
- **Async endpoints** (the Apify routes) are waited for, up to 180 seconds. A run still in flight after that is returned with its status and run URL.
- **A bad country is refused, not guessed.** `country` takes a two-letter code or a name; an unsupported one is a 400 listing the supported countries, never a silent fallback to US.
- **Money is an exact decimal string** (`"0.0005"`), never a float. Do not do float arithmetic on `charge_usd`.
- **Rate limits.** A `rate_limited` error carries `retry_after_ms`. The plugin waits that long once and retries the same call; if it is still limited, the error is returned as is.
- **Errors are the API's own envelope**: `{"error": {"code", "message", ...}, "request_id"}`. `insufficient_balance` means the workspace cannot cover the price; top up in the console instead of retrying.

## Run statuses

| Status | Meaning |
|---|---|
| `QUEUED` | Accepted, not yet dispatched to the provider |
| `RUNNING` | Dispatched, provider has not answered yet |
| `COMPLETED` | Terminal. The provider answered (its answer may still be a "not found") |
| `FAILED` | Terminal. No usable provider answer; the `failure` block says why |
| `STOPPED` | Terminal. Stopped in the Glasser console before dispatch, charge 0 |

## Privacy

Tool inputs (queries, domains, names, emails, URLs) and the Key are sent to `api.glasser.ai` to fulfil each request. The plugin stores nothing and collects no telemetry. Requests identify the plugin by name and version in the `User-Agent` header. See [PRIVACY.md](PRIVACY.md).

## Development

```sh
uv sync                      # Python 3.12, dify_plugin, pytest
uv run pytest                # offline tests, no network
uv run python scripts/gen_tools.py   # regenerate tools/*.yaml from https://glasser.ai/docs/openapi.json
dify plugin package .        # builds glasser.difypkg
```

Remote debugging against a Dify workspace: copy `.env.example` to `.env`, fill in the debug key from the workspace's plugin page, then `uv run python -m main`.

## Support

- Source repository: https://github.com/glasser-ai/dify-glasser
- Glasser documentation: https://glasser.ai/docs
- Console: https://app.glasser.ai
- Contact: support@glasser.ai
