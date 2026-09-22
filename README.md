# Glasser

**Author:** glasser-ai
**Version:** 0.4.3
**Type:** tool

Premium go-to-market data for your Dify agents — people search, company intelligence, keywords & SEO, web research, social media search and US market data — all through **one Glasser Key**, backed by Apollo, People Data Labs, Semrush, Ahrefs, Serper, Exa, ScrapeCreators, RentCast and more.

## Why this plugin

Building GTM automation normally means an account, a contract and a bill at each of Apollo, Semrush, Ahrefs, DataForSEO, Serper, Exa, ScrapeCreators, RentCast and a dozen more. Glasser puts **1,900+ endpoints from 40+ providers behind one Key**: no subscriptions, no signup at each vendor, one prepaid balance, pay per call, and failed calls and empty results cost $0.00. A new workspace starts with a $1 signup grant, no card. This plugin exposes the six most-used capabilities to Dify agents and workflows; the agent says what data it wants and Glasser picks the provider.

## Tools

Six tools, one per capability. Each takes an `action` (Social Media Search takes `platform` + `mode`) and a `provider`. Leave `provider` on `auto` and Glasser picks the source for that action and falls back to the next one on a provider error; name one ("use Ahrefs for that") to force it.

| Tool | Backed by | What your agent can do |
|---|---|---|
| **Find Prospects** | Apollo, People Data Labs + more | Search people by title, seniority, location or employer; enrich one profile; find a work email |
| **Company Intelligence** | Apollo, BuiltWith, PredictLeads + more | Company profile and firmographics, technology stack, website traffic, competitors, funding rounds, news |
| **Keywords & SEO** | Semrush, Ahrefs + more | Keyword volume and difficulty, keyword ideas, Google results, a domain's organic overview and ranking keywords, backlinks, referring domains, domain rating |
| **Web Research** | Serper, Exa + more | Web, news, places, scholar, shopping, image and video search; read a page; answers with sources; similar pages |
| **Social Media Search** | ScrapeCreators + more | Reddit, X, YouTube, TikTok, Instagram, LinkedIn: search posts, read a profile or channel, fetch one post, find an account's other profiles |
| **Market Data** | RentCast, SerpApi | US property value and rent estimates, property records, for-sale and rental listings, ZIP-code market statistics, stock quotes |

The rest of the 1,900+ endpoints in the Glasser catalog are reachable through the Glasser MCP server (`https://api.glasser.ai/mcp`, which Dify can add directly as an MCP tool) and the CLI.

### Example prompts

- "Find CTOs at stripe.com and get a work email for the first three."
- "What does shopify.com run on, how much traffic does it get, and who are its competitors?"
- "Search volume and difficulty for 'espresso machine' in the UK, plus 20 related keywords."
- "What are people saying about our brand on Reddit and X this week?"
- "Read https://example.com/pricing and summarize the plans."
- "Who ranks for 'ai meeting notes' in Germany, and what are their backlink profiles?"
- "What is 5500 Grand Lake Dr, San Antonio worth, and what would it rent for?"

## Setup

1. **Create a Glasser Key** — sign in at [app.glasser.ai](https://app.glasser.ai), open **Keys**, create a Key (it starts with `gl_`). A new workspace starts with a $1 signup grant, no card; after that, top up the balance. Calls are prepaid and billed per call, no subscription.
2. **Install this plugin** in Dify, open its provider settings, and paste the Key. Validation is free — the plugin checks the Key against Glasser's balance endpoint without spending anything.
3. **Attach the tools** to your Agent app or add them as Workflow nodes. All six tools share the one credential.

### Connection requirements

The plugin makes outbound HTTPS (port 443) requests to **`api.glasser.ai` only** — no other hosts, no inbound connections, no telemetry. It runs in Dify's standard plugin runtime with default permissions (no storage, model or endpoint permissions required).

## Usage notes

- **Pay per call, exact charge in every response.** Each call is one run at the routed endpoint's published price; the response carries `charge_usd` and a `run_url` that opens the run in the Glasser console. Failed calls and empty results cost $0.00.
- **Auto-routing and fallback.** Under `provider = auto`, a provider error moves the call to the next source, which is a second run billed on its own; every run is listed in the console. An empty answer is an answer — Glasser never falls back on "no result". Name a provider to force it and skip fallback.
- **"Not found" is a normal outcome.** A person or domain the provider does not know comes back as a completed run carrying the provider's own "not found"; it is not an error.
- **Retries never charge twice.** Every run carries an idempotency key; a dropped connection is retried against the same run, never as a new one.
- **Slow sources** (the Apify-backed routes) are waited for up to 180 seconds. A run still in flight after that is returned with its status and run URL.
- **Large outputs** (a full technology stack, a backlink dump) are trimmed to fit the model's context; the full provider output stays at the run URL.
- **Country targeting**: pass two-letter codes or full names ("de", "Germany"). An unsupported country is refused with the list of supported ones, never silently mapped to US.
- **Rate limits** are handled: the plugin waits the interval the API asks for and retries once.
- **Out of balance**: tools return a clear `insufficient_balance` error; top up in the console and retry.
- All tools are **read-only**: nothing is posted, sent, or contacted on your behalf.

## Privacy

Tool inputs (queries, domains, names, emails, URLs) and the Key are sent to `api.glasser.ai` to fulfil each request. The plugin stores nothing and collects no telemetry. Requests identify the plugin by name and version in the `User-Agent` header. See [PRIVACY.md](PRIVACY.md).

## Support

- Source repository: [github.com/glasser-ai/dify-glasser](https://github.com/glasser-ai/dify-glasser)
- Glasser documentation: [glasser.ai/docs](https://glasser.ai/docs)
- Data sources: [glasser.ai/data-sources](https://glasser.ai/data-sources)
- Console: [app.glasser.ai](https://app.glasser.ai)
- Contact: support@glasser.ai
