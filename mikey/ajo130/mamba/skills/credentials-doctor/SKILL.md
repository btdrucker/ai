---
name: credentials-doctor
description: >-
  Live Artifactory, Jenkins, gh, and git SSH credential checks for Mamba publish
  and Nike App integration flows. Report-only — invoked internally by
  test-in-nikeapp and release-mamba before publish or Jenkins. Use when the user
  explicitly asks to verify credentials or keychain setup.
---

# Credentials doctor

Internal preflight for `test-in-nikeapp` and `release-mamba`. **Report-only** — never stores secrets or runs interactive `read -s`.

## Run

From the Mamba Android repo root:

```bash
./scripts/lib/check-creds.sh
```

Always pass `required_permissions: ["all"]` when invoking via Shell — the Jenkins probe targets `mobile-ci.nike.com:8443`, which is not in the sandbox allowlist. The script connect-times out at 5s per probe so it stays fast on success.

Use `--keychain-only` to skip live HTTP and stay sandboxed (Keychain / `gh` presence only).

## Interpret

- Exit **0** → all checks passed; parent skill may proceed.
- Exit **1** → print the script's markdown report to the user and **stop**. Do not create worktrees, commit, publish, or trigger Jenkins.

For a one-line gate in scripts:

```bash
./scripts/lib/check-creds.sh --quiet
```

## Fix guidance

Point the user at the **Fix instructions** section in the report and `docs/CREDENTIALS.md`. The user must run the `security add-generic-password` commands locally — the agent cannot enter passwords.
