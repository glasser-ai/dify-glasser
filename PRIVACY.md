# Privacy Policy

This document describes what the Glasser Dify plugin ("the plugin") does with
data. The Glasser service itself is governed by the Glasser Privacy Policy at
https://glasser.ai/privacy-policy and the Terms of Service at
https://glasser.ai/terms-of-service.

## What the plugin is

The plugin is a stateless connector between Dify and the Glasser API at
`https://api.glasser.ai`. It makes outbound HTTPS requests to that one host
and to no other host. It accepts no inbound connections.

## Data the plugin sends

- **Your Glasser Key.** Stored by Dify's credential store, sent as the
  `Authorization: Bearer` header of every request. The plugin never writes it
  to logs, error messages or tool output.
- **Tool inputs.** Queries, domains, keywords, URLs, and the names, emails and
  profile URLs of people you ask to look up. They are sent to the Glasser API
  solely to fulfil the request they belong to. An input may contain personal
  data about third parties (for example an email address you ask to enrich);
  the Glasser Privacy Policy covers how Glasser and the provider handle it.
- **A User-Agent header** naming the plugin and its version, so Glasser can
  support and improve the integration. Nothing else about the Dify
  installation or its users is sent.

## Data the plugin returns

Tool output is the Glasser API's own response: the run record with the
provider's output, the exact charge and a link to the run in the console. Dify stores that output as part of the conversation or workflow
run, under Dify's own data policies.

## Data the plugin stores

None. The plugin keeps no state between invocations, uses no Dify storage
permission, and collects no telemetry or analytics.

## Data retention and deletion

The plugin retains nothing, so there is nothing to delete on the plugin side.
Run records are retained by Glasser as described in the Glasser Privacy
Policy and can be viewed in the Glasser console at https://app.glasser.ai.

## Contact

Privacy questions about the plugin or the Glasser service: support@glasser.ai
