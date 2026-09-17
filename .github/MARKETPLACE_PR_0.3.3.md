# Plugin Submission

## Plugin information

- **Author**: glasser-ai
- **Plugin name**: glasser
- **Version**: 0.3.3
- **Source repository**: https://github.com/glasser-ai/dify-glasser
- **Contact**: support@glasser.ai

## Submission type

- [x] New plugin
- [ ] Version update

## What changed

Glasser sells runnable third-party API operations (Apollo, People Data Labs, Hunter, BuiltWith, DataForSEO, Semrush, Ahrefs, Serper, Exa, ScrapeCreators and others) under one prepaid Key. This plugin exposes five capability tools: Find Prospects, Company Intelligence, Keywords & SEO, Web Research and Social Media Search. Each takes an `action` and a `provider`; `provider = auto` lets the plugin route to a good source for that action, and naming a provider forces it. Tool output is the Glasser API's own JSON for the run (provider output, exact charge, run URL) plus a `routed` block naming the endpoint that served it; errors are the API's error envelope; every run carries an idempotency key so a retry never charges twice.

## Risk level

- [x] Low risk
- [ ] Medium risk
- [ ] High risk

## Required checks

- [x] I have read and followed the [Marketplace submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md).
- [x] I have read and comply with the Plugin Developer Agreement.
- [ ] I tested this plugin on Dify Community Edition and Dify Cloud, or documented any limitation below.
- [x] The package contains only files needed at runtime.
- [x] The package does not contain secrets, local credentials, `.env` files, `.git` directories, virtual environments, caches, logs, or IDE files.
- [x] The package does not contain executables or bundled binaries, or I explained why they are required below.
- [x] The plugin README includes setup steps, usage instructions, required APIs or credentials, connection requirements, and the source repository link.
- [x] The plugin includes `PRIVACY.md` or a hosted privacy policy, and `manifest.yaml` references it.
- [x] All user-facing text is primarily in English, with any localized README files following the [i18n guidance](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/multilingual-readme).

## Security and privacy notes

The plugin calls one fixed HTTPS host, `api.glasser.ai`, with the user's Glasser Key from Dify's credential store. Run inputs are whatever the user asks a provider to process and may contain personal data (for example an email address to enrich); the plugin forwards them to that one host and stores nothing. No command or code execution, no file access, no user-controlled URLs.

## Local validation

- `uv run pytest` (25 offline tests, including every routing entry) and `dify plugin package .` pass in CI: https://github.com/glasser-ai/dify-glasser/actions
- Tested on **Dify Cloud** on 2026-09-17: installed the package as a local plugin, configured the Key (validation succeeded), and ran an Agent app (gpt-5) with the five tools attached. Verified live: people_search (apollo), company_intelligence tech_stack (builtwith), seo_research keyword_overview (semrush and serpstat) and domain_rating (ahrefs), web_research search (serper), social_research reddit_subreddit (scrapecreators). Each answer reported the provider, endpoint, charge and run URL; a provider 400 was reported as a $0.00 provider error, not as a tool failure.
- **Limitation**: not tested on Dify Community Edition.

## Reviewer notes

Source and issue tracker: https://github.com/glasser-ai/dify-glasser. The same seven operations are also available to Dify as a remote MCP server at `https://api.glasser.ai/mcp`; the plugin exists so the tools appear in the Marketplace with a Key credential and localized descriptions.
