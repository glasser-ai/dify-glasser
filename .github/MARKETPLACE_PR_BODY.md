# Plugin Submission

## Plugin information

- **Author**: glasser-ai
- **Plugin name**: glasser
- **Version**: see the package file name
- **Source repository**: https://github.com/glasser-ai/dify-glasser
- **Contact**: support@glasser.ai

## Submission type

- [x] New plugin
- [ ] Version update

## What changed

Release notes: https://github.com/glasser-ai/dify-glasser/releases

Glasser sells runnable third-party API operations (Apollo, People Data Labs, Hunter, BuiltWith, DataForSEO, Semrush, Ahrefs, Serper, Exa, ScrapeCreators and others) under one prepaid Key. This plugin exposes five capability tools: Find Prospects, Company Intelligence, Keywords & SEO, Web Research and Social Media Search. Each takes an `action` and a `provider`; `provider = auto` lets the plugin route to a good source for that action, and naming a provider forces it. Tool output is the Glasser API's own JSON for the run (provider output, exact charge, run URL) plus a `routed` block naming the endpoint that served it; errors are the API's error envelope; every run carries an idempotency key so a retry never charges twice.

## Risk level

- [x] Low risk
- [ ] Medium risk
- [ ] High risk

## Required checks

- [x] I have read and followed the [Marketplace submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md).
- [x] I have read and comply with the Plugin Developer Agreement.
- [x] I tested this plugin on Dify Community Edition and Dify Cloud, or documented any limitation below.
- [x] The package contains only files needed at runtime.
- [x] The package does not contain secrets, local credentials, `.env` files, `.git` directories, virtual environments, caches, logs, or IDE files.
- [x] The package does not contain executables or bundled binaries, or I explained why they are required below.
- [x] The plugin README includes setup steps, usage instructions, required APIs or credentials, connection requirements, and the source repository link.
- [x] The plugin includes `PRIVACY.md` or a hosted privacy policy, and `manifest.yaml` references it.
- [x] All user-facing text is primarily in English, with any localized README files following the [i18n guidance](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/multilingual-readme).

## Security and privacy notes

- **Network**: one fixed HTTPS host, `api.glasser.ai` (declared in `manifest.yaml` `network.domains`). `app.glasser.ai` appears only as a link in messages; `www.reddit.com` appears only as an input value passed to Apify through Glasser. The plugin never connects to either.
- **Personal data**: run inputs are whatever the user asks a provider to process (names, emails, LinkedIn URLs, domains) and are forwarded to that one host; the plugin stores nothing.
- **No payments**: the plugin moves no money. A Glasser workspace is prepaid on glasser.ai; each tool call is one metered API run and the response reports its charge. Words like "charge" and "paid" in the README describe that metering.
- **The `SELECT … FROM person` string** in `utils/routes.py` is the query language of the People Data Labs search API, sent as request input to `api.glasser.ai`; the plugin runs no SQL and opens no database.
- **The one file read** (`utils/glasser_client.py`) is the plugin's own bundled `manifest.yaml`, to put the version in the User-Agent header.
- No command or code execution, no browser automation, no user-controlled URLs.

## Local validation

- `uv run pytest` (25 offline tests, including every routing entry) and `dify plugin package .` pass in CI: https://github.com/glasser-ai/dify-glasser/actions
- Tested on **Dify Cloud** on 2026-09-17: installed the package as a local plugin, configured the Key (validation succeeded), and ran an Agent app (gpt-5) with the five tools attached. Verified live: people_search (apollo), company_intelligence tech_stack (builtwith), seo_research keyword_overview (semrush and serpstat) and domain_rating (ahrefs), web_research search (serper), social_research reddit_subreddit (scrapecreators). Each answer reported the provider, endpoint, charge and run URL; a provider 400 was reported as a $0.00 provider error, not as a tool failure.
- **Limitation**: not tested on Dify Community Edition.

## Reviewer notes

Source and issue tracker: https://github.com/glasser-ai/dify-glasser. The same seven operations are also available to Dify as a remote MCP server at `https://api.glasser.ai/mcp`; the plugin exists so the tools appear in the Marketplace with a Key credential and localized descriptions.
