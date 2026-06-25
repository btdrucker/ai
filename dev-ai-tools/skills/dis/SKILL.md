---
name: dis
description: >
  Install, configure, and manage the Dev Integration System (DIS) -- a Rust
  binary providing MCP tools for JIRA, Confluence, Jenkins, Slack, and RAG
  in any MCP-compatible IDE. Use when the user wants to install DIS, configure
  DIS credentials, set up the DIS MCP server, upgrade DIS, troubleshoot DIS,
  or run dis CLI commands.
---

# Dev Integration System (DIS)

Rust binary from GaME Engineering (`nike-internal/uip.dev-integration-system`). MCP tools for JIRA, Confluence, Jenkins, Slack, and RAG. Also works as a standalone CLI.

Docs: <https://didactic-adventure-mw7je6w.pages.github.io/>

## Opening the DIS docs

To open the DIS documentation in Cursor's built-in browser, use the `cursor-ide-browser` MCP server:

```
CallMcpTool: server=cursor-ide-browser, toolName=browser_navigate
arguments: {"url": "https://didactic-adventure-mw7je6w.pages.github.io/", "position": "side"}
```

Use `"position": "side"` to show the page beside the chat. Omit `position` for background access. Use `browser_snapshot` to read page content or `browser_take_screenshot` for visual verification.

## Guardrails

- Never store PATs or secrets in files tracked by git.
- Always append to the user's shell RC with `>>`, never overwrite with `>`.
- Detect the shell RC file (`~/.zshrc`, `~/.bashrc`, etc.) and use it consistently.
- Confirm before running `dis auth logout` (destroys stored Okta tokens).
- Never run `sudo`. If something needs it, show the command and ask the user.

---

## Choosing an install path

Ask the user which path fits, or infer from context:

| Path | When to use |
|------|-------------|
| **Quick Install** | Default for most users -- download pre-built binary |
| **Guided Setup** | New to the project or wants AI-assisted walkthrough |
| **Pre-Release** | Testing a release candidate (e.g. `v0.1.0-rc.3`) |
| **From Source** | Contributors, or unsupported platform (Intel Mac) |

All four paths share the same prerequisites and converge at **Configure Credentials** after the binary is installed.

---

## Prerequisites (all paths)

### 1. GitHub CLI

If not installed: `brew install gh && gh auth login` (or see [REFERENCE.md](REFERENCE.md) for direct download without Homebrew).

```bash
gh --version 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
gh repo view nike-internal/uip.dev-integration-system --json name 2>/dev/null \
  && echo "ACCESS OK" || echo "NO ACCESS -- ask in #github-nike-internal Slack channel"
```

### 2. PATH setup

```bash
echo "$PATH" | tr ':' '\n' | grep -q '.local/bin' && echo "ON PATH" || echo "NOT ON PATH"
```

If not on PATH:

```bash
mkdir -p ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Platform detection

```bash
ARCH=$(uname -m); OS=$(uname -s | tr '[:upper:]' '[:lower:]')
if [ "$ARCH" = "arm64" ] && [ "$OS" = "darwin" ]; then TRIPLE="aarch64-apple-darwin"
elif [ "$ARCH" = "x86_64" ] && [ "$OS" = "linux" ]; then TRIPLE="x86_64-unknown-linux-gnu"
else echo "Unsupported: $OS $ARCH -- use From Source path"; fi
```

---

## Path A: Quick Install (stable release)

```bash
gh release download --repo nike-internal/uip.dev-integration-system \
  --pattern "dis-latest-${TRIPLE}.tar.gz" --dir /tmp --clobber \
  && tar xzf /tmp/dis-latest-${TRIPLE}.tar.gz -C /tmp \
  && install /tmp/dis ~/.local/bin/
```

Verify: `dis --version`

Continue to **Configure Credentials**.

---

## Path B: Guided Setup (AI-assisted)

A setup prompt walks the user through everything: GitHub CLI, SSH keys, DIS install, credentials, and IDE config.

1. Visit <https://didactic-adventure-mw7je6w.pages.github.io/> and click the **Guided Setup** tab.
2. Click **Copy Setup Prompt**.
3. Paste into the IDE's agent chat.
4. Follow the conversation.

---

## Path C: Pre-Release (release candidate)

Same as Quick Install but with a specific version tag. List releases, then install:

```bash
gh release list --repo nike-internal/uip.dev-integration-system --limit 10

VERSION="<tag>"  # replace with chosen tag from the list above
gh release download "$VERSION" --repo nike-internal/uip.dev-integration-system \
  --pattern "dis-${VERSION}-${TRIPLE}.tar.gz" --dir /tmp --clobber \
  && tar xzf /tmp/dis-${VERSION}-${TRIPLE}.tar.gz -C /tmp \
  && install /tmp/dis ~/.local/bin/
```

Verify: `dis --version`. RC builds may contain bugs -- report issues on GitHub.

Continue to **Configure Credentials**.

---

## Path D: From Source

For contributors or unsupported platforms (e.g. Intel Mac).

### Install Rust (skip if `cargo --version` works)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
```

### Clone and build

```bash
mkdir -p ~/NikeDev
gh repo clone nike-internal/uip.dev-integration-system ~/NikeDev/dev-integration-system
cd ~/NikeDev/dev-integration-system
cargo build --release
```

### Install binary

```bash
mkdir -p ~/.local/bin
install ~/NikeDev/dev-integration-system/target/release/dis ~/.local/bin/
```

Verify: `dis --version`

See `CLAUDE.md` in the repo root for development workflow and conventions.

Continue to **Configure Credentials**.

---

## Configure Credentials

### JIRA and Confluence PATs (required)

Check current state:

```bash
[ -n "$JIRA_PAT" ] && echo "JIRA_PAT set" || echo "JIRA_PAT missing"
[ -n "$CONFLUENCE_PAT" ] && echo "CONFLUENCE_PAT set" || echo "CONFLUENCE_PAT missing"
```

If missing, direct the user to generate tokens:
- JIRA PAT: <https://jira.nike.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens>
- Confluence PAT: <https://confluence.nike.com/plugins/personalaccesstokens/usertokens.action>

Ask for the actual token values. Add to shell RC:

```bash
echo 'export JIRA_PAT="<token>"' >> ~/.zshrc
echo 'export CONFLUENCE_PAT="<token>"' >> ~/.zshrc
source ~/.zshrc
```

### Okta authentication (optional -- enables write operations)

Required for creating JIRA tickets, posting Slack messages.

```bash
dis auth login
```

Opens a browser for Nike Okta OAuth PKCE. Tokens are saved locally and auto-refreshed. Check with `dis auth status`. Requires `App.Game.ReadUpdate` access in idlocker.

### Slack (optional)

On macOS, extract browser-session credentials from Chrome (must be logged into `nike.enterprise.slack.com`):

```bash
dis auth slack
```

On other platforms, set env vars manually:

```bash
echo 'export SLACK_TOKEN="xoxc-your-token"' >> ~/.zshrc
echo 'export SLACK_COOKIE="xoxd-your-cookie"' >> ~/.zshrc
source ~/.zshrc
```

6 base tools (including `slack_post`) work with either `dis auth login` (Okta proxy) or `dis auth slack` (browser session). The 4 enhanced tools (`slack_search`, `slack_dm_open`, `slack_draft`, `slack_scan_secrets`) require browser-session auth (`dis auth slack`).

### Jenkins (optional)

Set env vars per instance. The prefix is the instance name uppercased with underscores (e.g. instance `team-builds` becomes `TEAM_BUILDS`):

```bash
echo 'export NIKE_EMAIL="your.name@nike.com"' >> ~/.zshrc
echo 'export MY_INSTANCE_JENKINS_URL="https://your-jenkins.nike.com"' >> ~/.zshrc
echo 'export MY_INSTANCE_JENKINS_PAT="your-jenkins-api-token"' >> ~/.zshrc
source ~/.zshrc
```

Verify: `dis call jenkins_list_instances '{}'`

---

## IDE Setup

### Cursor (Nike-managed)

Nike-managed Cursor can't launch arbitrary binaries via stdio MCP. DIS runs as a local HTTP daemon instead:

```bash
dis setup mcp cursor   # register MCP server entry in ~/.cursor/mcp.json
dis serve              # start the HTTP MCP daemon (detaches to background)
```

Check daemon status: `dis serve status`. Stop: `dis serve stop`.

Optionally install bundled agent files:

```bash
dis setup cursor
```

After registration, reload Cursor's MCP servers (Settings > MCP > Reload). Tool calls will prompt for approval until Nike admin adds `nike-dev-integration-system-mcp:*` to the central `mcpToolAllowlist` -- request in `#ai-developer-tooling-support`.

### Claude Code

```bash
claude mcp add dev-integration-server dis -s user --transport stdio \
  --env JIRA_PAT=$JIRA_PAT --env CONFLUENCE_PAT=$CONFLUENCE_PAT \
  --env SLACK_TOKEN=$SLACK_TOKEN --env SLACK_COOKIE=$SLACK_COOKIE
dis setup claude
```

### Goose

Add to `~/.config/goose/config.yaml` under MCP servers:

```yaml
dis:
  enabled: true
  type: stdio
  cmd: dis
  env_keys: [JIRA_PAT, CONFLUENCE_PAT, SLACK_TOKEN, SLACK_COOKIE]
  timeout: 300
```

---

## Verification

Run after completing all setup:

```bash
command -v dis && echo "DIS $(dis --version 2>/dev/null)" || echo "DIS missing"
[ -n "$JIRA_PAT" ] && echo "JIRA_PAT set" || echo "JIRA_PAT missing"
[ -n "$CONFLUENCE_PAT" ] && echo "CONFLUENCE_PAT set" || echo "CONFLUENCE_PAT missing"
[ -f ~/.config/dis/slack-credentials ] && echo "Slack configured" || echo "Slack not configured (optional)"
[ -f ~/.config/dis/okta-credentials.json ] && echo "Okta configured" || echo "Okta not configured (optional)"
```

Smoke test:

```bash
dis call jira_list_projects '{}'
```

---

## Upgrade and Version Management

### Check version and available updates

```bash
dis --version           # current version
dis upgrade --check     # check if a newer version exists (no install)
```

### Self-upgrade (recommended)

```bash
dis upgrade
```

Downloads and replaces the binary in place.

### Manual upgrade / pinned version

If `dis upgrade` fails, re-run the install commands from **Path A** (stable) or **Path C** (specific version). For contributors, pull and rebuild per **Path D**.

### List available releases

```bash
gh release list --repo nike-internal/uip.dev-integration-system --limit 10
```

### After any upgrade

```bash
dis --version
```

If the IDE uses the HTTP daemon (Cursor), also restart it: `dis serve stop && dis serve`

---

## CLI and MCP tool reference

See [REFERENCE.md](REFERENCE.md) for the full CLI command listing and all 56 MCP tools by domain.

---

## Troubleshooting

### `dis: command not found`

Binary is not on PATH. Fix:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify: `which dis`

### `dis upgrade` fails or downloads wrong platform

Check detected platform:

```bash
uname -m && uname -s
```

Expected: `arm64` + `Darwin` (macOS) or `x86_64` + `Linux`. If neither matches, use Path D (From Source).

### JIRA or Confluence authentication errors

Verify PATs are set and not expired:

```bash
[ -n "$JIRA_PAT" ] && echo "JIRA_PAT set" || echo "JIRA_PAT missing"
[ -n "$CONFLUENCE_PAT" ] && echo "CONFLUENCE_PAT set" || echo "CONFLUENCE_PAT missing"
```

If set but requests fail, the token has expired. Generate new ones:
- JIRA: <https://jira.nike.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens>
- Confluence: <https://confluence.nike.com/plugins/personalaccesstokens/usertokens.action>

### Jenkins tools return connection errors

Verify instance config:

```bash
dis call jenkins_list_instances '{}'
```

If no instances appear, the env vars are missing. See **Configure Credentials > Jenkins**.

### `gh: command not found` or GitHub auth issues

```bash
brew install gh && gh auth login
gh repo view nike-internal/uip.dev-integration-system --json name
```

If no Homebrew, see the direct download in [REFERENCE.md](REFERENCE.md).

### Slack tools not available or returning errors

On macOS, extract credentials from Chrome (must be logged into `nike.enterprise.slack.com`):

```bash
dis auth slack
```

If Chrome extraction fails (non-macOS or different browser), set `SLACK_TOKEN` and `SLACK_COOKIE` env vars manually.

### Okta login fails with "access_denied"

Requires `App.Game.ReadUpdate` access in idlocker. Apply for it, then retry `dis auth login`.

For read-only Slack (search, history, channels), skip Okta and use `dis auth slack` instead.

### MCP server not detected by the IDE

Verify standalone first:

```bash
dis --version
```

**Cursor (Nike-managed):** Check HTTP daemon status:

```bash
dis serve status
```

If not running:

```bash
dis setup mcp cursor
dis serve
```

Then reload in Cursor (Settings > MCP > Reload). Tool calls prompt for approval until admin adds `nike-dev-integration-system-mcp:*` to `mcpToolAllowlist` -- request in `#ai-developer-tooling-support`.

**Claude Code / Goose:** Re-run the IDE setup commands from the **IDE Setup** section.

### No access to `nike-internal` org

If `gh repo view nike-internal/uip.dev-integration-system` fails, the user needs org access. Direct them to ask in the `#github-nike-internal` Slack channel.

---

## Sources

- [DIS documentation](https://didactic-adventure-mw7je6w.pages.github.io/)
- [GitHub repo](https://github.com/nike-internal/uip.dev-integration-system)
