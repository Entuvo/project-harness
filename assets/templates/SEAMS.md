# Seams — upstream contact surface
<!-- harness:seams v1 · one row per point where this project depends on upstream internals. Enumerating the surface makes an upgrade a finite checklist instead of an archaeology dig. -->

**Upstream pin:** {{REPO_OR_PACKAGE}} @ `{{FULL_COMMIT_OR_VERSION}}`

<!-- A seam is the single named module that isolates one dependence on upstream internals. Code outside seams imports the seam, never the upstream symbol. -->

| Seam (module) | Depends on upstream symbols (file:line at the pin) | Stability guess | Acceptance check | Retirement condition |
|---|---|---|---|---|
| {{seam_module}} | {{symbol}} ({{path:line}}) | {{stable/volatile}} | {{test that proves the seam still holds}} | {{"retire when upstream exposes X publicly"}} |
