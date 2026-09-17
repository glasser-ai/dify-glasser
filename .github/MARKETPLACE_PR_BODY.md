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

See the release notes at https://github.com/glasser-ai/dify-glasser/releases.

## Risk level

- [x] Low risk
- [ ] Medium risk
- [ ] High risk

## Required checks

- [x] I have read and followed the [Marketplace submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md).
- [x] I have read and comply with the Plugin Developer Agreement.
- [ ] I tested this plugin on Dify Community Edition and Dify Cloud, or documented any limitation below (see Local validation).
- [x] The package contains only files needed at runtime.
- [x] The package does not contain secrets, local credentials, `.env` files, `.git` directories, virtual environments, caches, logs, or IDE files.
- [x] The package does not contain executables or bundled binaries, or I explained why they are required below.
- [x] The plugin README includes setup steps, usage instructions, required APIs or credentials, connection requirements, and the source repository link.
- [x] The plugin includes `PRIVACY.md` or a hosted privacy policy, and `manifest.yaml` references it.
- [x] All user-facing text is primarily in English, with any localized README files following the [i18n guidance](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/multilingual-readme).

## Security and privacy notes

The plugin calls one fixed HTTPS host, `api.glasser.ai`, with the user's Glasser Key. Run inputs may contain personal data the user asks a provider to enrich; the plugin stores nothing. Automated release; see PRIVACY.md in the package.

## Local validation

`uv run pytest` and `dify plugin package .` run in CI on every push; the package attached to the release is the one submitted here. Manual testing on Dify Cloud is recorded per release in the release notes, with the Dify version used.
