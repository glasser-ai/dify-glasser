# Glasser

**Author:** glasser-ai
**Version:** 0.2.1
**Type:** tool

[简体中文](README_zh_Hans.md)

Paid third-party API endpoints for Dify agents and workflows through **one Glasser Key**: search the data sources, inspect the exact price, run, pay per call. No signup at each vendor.

Glasser is a broker. It sells runnable third-party API operations ("endpoints") under a single Key. Your agent searches the catalog, inspects an endpoint's contract and price, and runs it. The response is the provider's own output, with the exact charge and a link to the run in the Glasser console.

## Tools

Five capability tools cover the common jobs. Each takes an `action` and a `provider`; `provider = auto` (the default) lets the plugin pick a good source for that action, and naming a provider forces it. The agent says what data it wants, not which vendor to call.

| Tool | What the agent can do | Providers behind it |
|---|---|---|
| **Find People** (`people_search`) | Search people by title, seniority, location, employer; enrich one person; find a work email | Apollo, People Data Labs, Hunter, Prospeo, LeadMagic, ZoomInfo |
| **Company Intelligence** (`company_intelligence`) | Profile and firmographics, technology stack, website traffic, competitors, funding rounds, news | Apollo, PDL, Hunter, Prospeo, PredictLeads, LeadMagic, BuiltWith, DataForSEO, Ahrefs, Serpstat, Apify, Serper |
| **SEO Research** (`seo_research`) | Keyword metrics and ideas, domain organic overview, ranking keywords, backlinks, referring domains, domain rating, Google results | Semrush, DataForSEO, Ahrefs, Serpstat, Serper |
| **Web Research** (`web_research`) | Web, news, places, scholar, shopping, image and video search; read a page; neural search, answers, similar pages | Serper, SerpApi, Exa, DataForSEO |
| **Social Research** (`social_research`) | Reddit, X, YouTube, TikTok, Instagram, LinkedIn: search posts, read profiles and channels, find social accounts | ScrapeCreators, Apify, TikHub |

Seven catalog tools reach the rest of the 1,400+ endpoints and are the same verbs as the Glasser MCP server and CLI: `search` the data sources, `inspect` an endpoint's contract and price, `run` it, `runs_get`, `runs_list`, `runs_stop`, `balance`.

### How a capability call works

1. The tool resolves `(action, provider)` to one Glasser endpoint through its routing table (`utils/routes.py`) and turns the flat parameters into that endpoint's provider-native input.
2. It runs the endpoint. The result is the run as the Glasser API returned it (provider output, exact `charge_usd`, `run_url`) plus a `routed` block naming the endpoint that served the call and the input it received.
3. Routing, fallback and pricing decisions are Glasser's; the plugin adds no state and no retry beyond reusing the idempotency key on a dropped connection.

### Routing table

**people_search**

| action | provider=auto | other providers |
|---|---|---|
| `search` | apollo | pdl, leadmagic, zoominfo, hunter |
| `enrich` | apollo | pdl, hunter, prospeo, leadmagic |
| `find_email` | hunter | leadmagic, prospeo, apollo |

**company_intelligence**

| action | provider=auto | other providers |
|---|---|---|
| `enrich` | apollo | pdl, hunter, prospeo, predictleads, leadmagic |
| `tech_stack` | builtwith | predictleads, dataforseo |
| `traffic` | dataforseo | ahrefs, apify |
| `competitors` | dataforseo | ahrefs, serpstat, predictleads |
| `funding` | predictleads | leadmagic |
| `news` | predictleads | serper |

**seo_research**

| action | provider=auto | other providers |
|---|---|---|
| `keyword_overview` | semrush (serpstat for several keywords) | serpstat, dataforseo, ahrefs |
| `keyword_ideas` | dataforseo | serpstat, ahrefs |
| `domain_overview` | dataforseo | serpstat, ahrefs |
| `ranked_keywords` | dataforseo | serpstat, ahrefs |
| `backlinks_overview` | semrush | dataforseo, ahrefs, serpstat |
| `backlinks` | semrush | dataforseo, ahrefs |
| `referring_domains` | semrush | dataforseo, ahrefs |
| `domain_rating` | ahrefs | — |
| `serp` | dataforseo | serper |

**web_research**

| action | provider=auto | other providers |
|---|---|---|
| `search` | serper | serpapi, exa |
| `news` | serper | serpapi |
| `scrape` | serper | exa, dataforseo |
| `places` | serper | serpapi |
| `scholar` | serper | serpapi |
| `shopping` | serper | serpapi |
| `images` | serper | — |
| `videos` | serper | — |
| `answer` | exa | — |
| `similar` | exa | — |

**social_research**

| action | provider=auto | other providers |
|---|---|---|
| `reddit_search` | scrapecreators | — |
| `reddit_subreddit` | scrapecreators | apify |
| `x_user_tweets` | scrapecreators | — |
| `x_tweet` | scrapecreators | — |
| `youtube_search` | scrapecreators | apify |
| `youtube_channel` | scrapecreators | — |
| `tiktok_search` | scrapecreators | — |
| `instagram_profile` | scrapecreators | apify |
| `linkedin_posts` | scrapecreators | apify |
| `linkedin_profile` | scrapecreators | tikhub |
| `linkedin_company` | scrapecreators | — |
| `find_profiles` | scrapecreators | — |

`provider = auto` picks are made on price and coverage. Every endpoint above is in the Glasser catalog; `inspect` shows its current price.

### Example prompts

- "Find CTOs at stripe.com." (people_search, search, apollo: free)
- "What is the work email of Patrick Collison at stripe.com?" (people_search, find_email, hunter)
- "What technologies does shopify.com run?" (company_intelligence, tech_stack, builtwith)
- "Search volume and difficulty for 'espresso machine' in the UK." (seo_research, keyword_overview, semrush)
- "Read https://example.com and summarize it." (web_research, scrape, serper)
- "What are people saying about our brand on Reddit this week?" (social_research, reddit_search, scrapecreators)
- "Use Ahrefs for that" forces `provider = ahrefs`.

## Setup

1. **Create a Glasser Key.** Sign in at https://app.glasser.ai, open **Keys**, create a Key (it starts with `gl_`). The workspace needs a balance: runs are prepaid and charged per call.
2. **Install this plugin** in Dify and paste the Key in the provider settings. Validation calls `GET /v1/balance`, which is free.
3. **Attach the tools** to an Agent app, or add them as nodes in a Workflow. All seven tools share the one credential.

### Connection requirements

The plugin makes outbound HTTPS (port 443) requests to **`api.glasser.ai` only**. No other hosts, no inbound connections, no telemetry. It runs in Dify's standard plugin runtime with default permissions (no storage, model or endpoint permissions).

## Usage notes

- **Capability tools price by their route.** Each call is one paid run at the routed endpoint's published price; the `routed` block in the result names it. For catalog tools, inspect before the first run: the price shown by `inspect` is what a normal COMPLETED call costs. The charge clauses list the exceptions, for example `NO_RESULT $0.00` means an empty answer is free. The charge rule may read volume parameters in the input (`num`, `size`, `limit`, arrays of queries), so start small.
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
