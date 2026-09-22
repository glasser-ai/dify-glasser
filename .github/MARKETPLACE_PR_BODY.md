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

**v0.4.3 is a text-only change to the credential form; behaviour is unchanged.** The API key field's help text is now one line — "Get an API key from the Glasser Console." — in all four locales (en_US, zh_Hans, ja_JP, pt_BR), replacing a three-sentence paragraph that wrapped awkwardly in the credential dialog. The `help.url` still points at the Keys page. Nothing else changed: no Python source was touched apart from the plugin version constant in the User-Agent header, and the network behaviour verified in v0.4.2 stands — one declared host, written into the `urlopen` call, no runtime-constructed call sites, no undeclared domains.

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

- **Network**: one fixed HTTPS host, `api.glasser.ai`, written into the `urlopen` call and declared in `manifest.yaml` `network.domains`. `app.glasser.ai` appears only as the credential form's help link in `provider/glasser.yaml`; the plugin never connects to it.
- **Personal data**: run inputs are whatever the user asks a provider to process (names, emails, LinkedIn URLs, domains) and are forwarded to that one host; the plugin stores nothing.
- **No payments**: the plugin moves no money. A Glasser workspace is prepaid on glasser.ai; each tool call is one metered API run and the response reports its charge. Words like "charge" and "paid" in the README describe that metering.
- **No file reads.** The plugin version in the User-Agent header is a constant, kept equal to `manifest.yaml` by an offline test.
- No command or code execution, no browser automation, no user-controlled URLs.

## Local validation

- `uv run pytest` (15 offline tests) and `dify plugin package .` pass in CI: https://github.com/glasser-ai/dify-glasser/actions
- **Dify Cloud**, 2026-09-17: v0.4.0 installed as a local plugin, Key validated (the free balance call), all six tools attached to an Agent app (gpt-5). Every tool is a pass-through to `POST https://api.glasser.ai/v1/solutions/gtm/<capability>`; those endpoints were exercised with real provider keys for every (action, provider) route before release, including the refusal paths (unsupported country, a filter the named provider cannot apply), which return the API's error envelope with nothing run and nothing charged.
- v0.4.3 changes four strings in `provider/glasser.yaml` and the version constant; no request path was touched. The 15 offline tests pass, including the one that keeps the User-Agent version equal to `manifest.yaml`. **Dify Cloud**, 2026-09-20: v0.4.2 — the same code path — installed as a local plugin over the Marketplace v0.4.1 (credential carried over), Find Prospects run from the Agent app: `POST /v1/solutions/gtm/people_search` → run COMPLETED, provider apollo HTTP 200, charge $0.00, run URL and idempotency key returned. v0.4.3 itself was not re-installed on Cloud; the change is a label in the credential form.
- **Limitation**: not tested on Dify Community Edition.

## Reviewer notes

Source and issue tracker: https://github.com/glasser-ai/dify-glasser. The six capabilities are documented at https://glasser.ai/docs (`POST /v1/solutions/gtm/<capability>`); the plugin exists so the tools appear in the Marketplace with a Key credential and localized descriptions. Tool parameters are generated from the API's OpenAPI document (`scripts/gen_tools.py`, not shipped in the package).
