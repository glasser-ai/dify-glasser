# Plugin Submission

## Plugin information

- **Author**: glasser-ai
- **Plugin name**: glasser
- **Version**: see the package file name
- **Source repository**: https://github.com/glasser-ai/dify-glasser
- **Contact**: support@glasser.ai

## Submission type

- [ ] New plugin
- [x] Version update

## What changed

Release notes: https://github.com/glasser-ai/dify-glasser/releases

**v0.4.1 is a documentation-only release; the code is identical to v0.4.0.** The README is rewritten as a Marketplace listing: a "Why this plugin" section, a shorter tools table, goal-oriented example prompts, a Setup with the pricing model ($1 signup grant, prepaid, per call), and usage notes written for a Dify user. The API-level material (request flow, run statuses, build and remote-debug commands) moved to `CONTRIBUTING.md`, which is excluded from the package.

Glasser sells runnable third-party API operations (Apollo, People Data Labs, Hunter, BuiltWith, DataForSEO, Semrush, Ahrefs, Serper, Exa, ScrapeCreators, RentCast and others) under one prepaid Key. This plugin exposes six capability tools: Find Prospects, Company Intelligence, Keywords & SEO, Web Research, Social Media Search and Market Data. Each tool is one call to `POST /v1/solutions/gtm/<capability>` on the Glasser API with the tool's parameters as they are; routing to a provider, parameter translation and fallback happen in the API, not in the plugin. `provider = auto` (the default) lets Glasser pick the source, and naming a provider forces it. Tool output is the Glasser API's own JSON for the run (provider, endpoint, provider output, exact charge, run URL); errors are the API's error envelope; every run carries an idempotency key so a retry never charges twice.

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

- **Network**: one fixed HTTPS host, `api.glasser.ai` (declared in `manifest.yaml` `network.domains`). `app.glasser.ai` appears only as a link in messages; the plugin never connects to it.
- **Personal data**: run inputs are whatever the user asks a provider to process (names, emails, LinkedIn URLs, domains) and are forwarded to that one host; the plugin stores nothing.
- **No payments**: the plugin moves no money. A Glasser workspace is prepaid on glasser.ai; each tool call is one metered API run and the response reports its charge. Words like "charge" and "paid" in the README describe that metering.
- **The one file read** (`utils/glasser_client.py`) is the plugin's own bundled `manifest.yaml`, to put the version in the User-Agent header.
- No command or code execution, no browser automation, no user-controlled URLs.

## Local validation

- `uv run pytest` (14 offline tests) and `dify plugin package .` pass in CI: https://github.com/glasser-ai/dify-glasser/actions
- **Dify Cloud**, 2026-09-17: v0.4.0 (same code as this release) installed as a local plugin, Key validated (the free balance call), all six tools attached to an Agent app (gpt-5). Every tool is a pass-through to `POST https://api.glasser.ai/v1/solutions/gtm/<capability>`; those endpoints were exercised with real provider keys for every (action, provider) route before release, including the refusal paths (unsupported country, a filter the named provider cannot apply), which return the API's error envelope with nothing run and nothing charged.
- **Limitation**: not tested on Dify Community Edition.

## Reviewer notes

Source and issue tracker: https://github.com/glasser-ai/dify-glasser. The six capabilities are documented at https://glasser.ai/docs (`POST /v1/solutions/gtm/<capability>`); the plugin exists so the tools appear in the Marketplace with a Key credential and localized descriptions. Tool parameters are generated from the API's OpenAPI document (`scripts/gen_tools.py`, not shipped in the package).
