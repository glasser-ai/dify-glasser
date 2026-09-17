# Glasser

**Author:** glasser-ai
**Version:** 0.3.3
**Type:** tool

Premium data for Dify agents and workflows through **one Glasser Key**: find people, company intelligence, SEO research, web research and social research, backed by Apollo, People Data Labs, Hunter, BuiltWith, DataForSEO, Semrush, Ahrefs, Serper, Exa, ScrapeCreators and more. The agent says what data it wants; Glasser decides which provider serves it. Pay per call, no signup at each vendor.

Glasser is a broker. It sells runnable third-party API operations under a single Key. Each tool call becomes one Glasser run; the response is the provider's own output, with the exact charge and a link to the run in the Glasser console.

## Tools

Five capability tools cover the common jobs. Each takes an `action` and a `provider`; `provider = auto` (the default) lets the plugin pick a good source for that action, and naming a provider forces it. The agent says what data it wants, not which vendor to call.

| Tool | What the agent can do | Providers behind it |
|---|---|---|
| **Find Prospects** (`people_search`) | Search people by title, seniority, location, employer; enrich one person; find a work email | Apollo, People Data Labs, Hunter, Prospeo, LeadMagic, ZoomInfo |
| **Company Intelligence** (`company_intelligence`) | Profile and firmographics, technology stack, website traffic, competitors, funding rounds, news | Apollo, PDL, Hunter, Prospeo, PredictLeads, LeadMagic, BuiltWith, DataForSEO, Ahrefs, Serpstat, Apify, Serper |
| **Keywords & SEO** (`seo_research`) | Keyword metrics and ideas, domain organic overview, ranking keywords, backlinks, referring domains, domain rating, Google results | Semrush, DataForSEO, Ahrefs, Serpstat, Serper |
| **Web Research** (`web_research`) | Web, news, places, scholar, shopping, image and video search; read a page; neural search, answers, similar pages | Serper, SerpApi, Exa, DataForSEO |
| **Social Media Search** (`social_research`) | Reddit, X, YouTube, TikTok, Instagram, LinkedIn: search posts, read profiles and channels, find social accounts | ScrapeCreators, Apify, TikHub |

The rest of the 1,400+ endpoints in the Glasser catalog are reachable through the Glasser MCP server (`https://api.glasser.ai/mcp`, which Dify can add directly as an MCP tool) and the CLI.

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

`provider = auto` picks are made on price and coverage. Every endpoint above is in the Glasser catalog, where its current price is shown.

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

- **Each call is one paid run** at the routed endpoint's published price; the `routed` block in the result names the endpoint. The routing table below lists which endpoint each action uses. The charge clauses list the exceptions, for example `NO_RESULT $0.00` means an empty answer is free. The charge rule may read volume parameters in the input (`num`, `size`, `limit`, arrays of queries), so start small.
- **Two indicators, not one.** A run's status and the provider's response are separate. A COMPLETED run whose provider answered 404 ("person not found") is a normal outcome, charged per the endpoint's clauses. A FAILED run can carry a non-zero charge when the clauses say so.
- **Retries never charge twice.** Every run carries an idempotency key the plugin generates and echoes as `idempotency_key`; the plugin reuses it when it retries a dropped connection, so a retry reads the original run.
- **Async endpoints** (the Apify routes) are waited for, up to 180 seconds. A run still in flight after that is returned with its status and run URL.
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
uv run pytest                # offline routing tests, no network
dify plugin package .        # builds glasser.difypkg
```

Remote debugging against a Dify workspace: copy `.env.example` to `.env`, fill in the debug key from the workspace's plugin page, then `uv run python -m main`.

## Support

- Source repository: https://github.com/glasser-ai/dify-glasser
- Glasser documentation: https://glasser.ai/docs
- Console: https://app.glasser.ai
- Contact: support@glasser.ai
