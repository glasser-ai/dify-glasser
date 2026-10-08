# Glasser

**Author:** glasser-ai
**Version:** 0.4.3
**Type:** tool

Glasser is a metered gateway in front of paid data APIs: one Key, one prepaid balance, and every call returns the exact amount it cost. This plugin wires six of those capabilities into Dify, so an agent can look up a person, profile a company, pull keyword and backlink figures, read the live web, watch social platforms, or price US property — without you holding an account at Apollo, Semrush, Ahrefs, Serper, Exa, ScrapeCreators or RentCast.

The catalog behind the Key runs to 1,900+ endpoints across 40+ vendors. No subscription, no signup at each vendor. A new workspace opens with a $1 grant and no card on file; you top it up from there. A call that fails, and a call that comes back empty, both settle at $0.00.

## The six tools

Each tool takes an `action` naming what you want — Social Media Search takes a `platform` and a `mode` instead — plus an optional `provider`.

| Tool | Ask it for | Routed to |
|---|---|---|
| Find Prospects | People by title, seniority, location or employer; one enriched profile; a work email | Apollo, People Data Labs, LeadMagic, ZoomInfo, Hunter, Prospeo |
| Company Intelligence | Firmographics, technology stack, site traffic, competitors, funding rounds, press | Apollo, BuiltWith, PredictLeads, DataForSEO, Ahrefs |
| Keywords & SEO | Volume and difficulty, keyword ideas, SERPs, organic overview, ranking keywords, backlinks, referring domains, domain rating | Semrush, Ahrefs, Serpstat, DataForSEO, Serper |
| Web Research | Web, news, places, scholar, shopping, image and video results; page text; sourced answers; lookalike pages | Serper, SerpApi, Exa, DataForSEO |
| Social Media Search | Posts, profiles, feeds and channels across Reddit, X, YouTube, TikTok, Instagram and LinkedIn | ScrapeCreators, Apify, TikHub |
| Market Data | US property valuations, rent estimates, property records, for-sale and rental listings, ZIP-level statistics, stock quotes | RentCast, SerpApi |

Once the tools are attached, an agent can be asked things like:

- "Pull the engineering leadership at stripe.com and get me a work email for three of them."
- "Profile shopify.com — stack, traffic, funding history, nearest competitors."
- "How hard is 'espresso machine' to rank for in the UK, and give me twenty adjacent terms."
- "Summarise the last week of Reddit threads mentioning Linear."
- "Open https://example.com/pricing and tell me what each tier includes."
- "Estimate the sale value and the monthly rent for 5500 Grand Lake Dr, San Antonio."

## Picking a source

`provider` defaults to `auto`, which lets Glasser choose the vendor it rates best for that specific action. Should that vendor error, the call moves down the list — a second run, billed on its own, and both show up in your ledger. An empty result counts as a real answer, so routing stops there rather than shopping the same question around until something comes back.

Name a vendor outright and the call goes only there, with no fallback attempted.

## What you pay

A run is priced at the published rate of whichever endpoint served it. The response carries `charge_usd` next to a `run_url` that opens that run in the Glasser console, so the cost of any individual agent step stays attributable afterwards.

Every run carries an idempotency key. When a connection drops and the plugin retries, the retry reattaches to the original run — there is no path by which one request bills twice.

## Installing it

1. Sign in at [app.glasser.ai](https://app.glasser.ai), open **Keys**, and generate one. Glasser Keys are prefixed `gl_`.
2. Add the plugin in Dify and paste the Key into its credentials. Dify verifies it by reading your balance, which costs nothing.
3. Pick the tools you want inside an Agent app, or drop them in as Workflow nodes. A single credential covers all six.

## Behaviour worth knowing

- Country arguments take either an ISO two-letter code or the country's name — `de` and `Germany` both work. A country the routed vendor does not serve produces an explicit refusal listing what is available, never a quiet substitution.
- A lookup for someone or something the vendor has no record of comes back as a finished run carrying that vendor's own "no match". Treat it as data, not as a failure.
- A handful of routes run on Apify and are genuinely slow. The plugin waits up to 180 seconds, then hands back the run's status and URL for you to check later.
- Oversized payloads — an exhaustive technology stack, a deep backlink export — get cut down to something a model can hold. The untruncated version stays at the run URL.
- Hitting a vendor's rate limit makes the plugin pause for the interval the API asks for and try once more.
- An exhausted balance surfaces as a named error pointing at the console, rather than as a silent empty response.
- Nothing here writes. These six tools read and return; no message, post or contact is made on your behalf.

## What leaves your Dify instance

`api.glasser.ai` over HTTPS, and nothing else. The plugin opens no other outbound host and listens on no port. In its manifest the `permission` block is empty — it claims nothing optional that Dify can grant a plugin.

What travels: your Key as a bearer token, and whatever you put into a tool — search terms, domains, URLs, and the names or email addresses of people you are looking up. Glasser needs them to run the call. The plugin keeps no copy, writes no logs of its own, and emits no analytics; its name and version ride along in the `User-Agent` header. The longer version is in [PRIVACY.md](PRIVACY.md).

## Beyond the six tools

These six are shortcuts, not the ceiling. The rest of the 1,900+ endpoint catalog is reachable with the same Key two other ways: the Glasser MCP server at `https://api.glasser.ai/mcp`, which Dify can register directly as an MCP tool, and the command-line client.

## Where to go

| | |
|---|---|
| Plugin source | [github.com/glasser-ai/dify-glasser](https://github.com/glasser-ai/dify-glasser) |
| Documentation | [glasser.ai/docs](https://glasser.ai/docs) |
| Catalog of sources | [glasser.ai/data-sources](https://glasser.ai/data-sources) |
| Console | [app.glasser.ai](https://app.glasser.ai) |
| Questions | support@glasser.ai |
