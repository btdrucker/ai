---
name: vscode-java-extensions
description: >
  Install recommended VS Code/Cursor extensions for Java, Spring Boot, Gradle,
  YAML, and Docker development. Use when the user wants to set up their IDE for
  Java, install extensions, configure Java plugins, or asks about recommended
  extensions for the Search Engineering workspace.
---

# Java Extensions

> This skill works in both VS Code and Cursor.

## Related skills

- **`vscode-workspace`** -- workspace management (ensures repo is in the active workspace)

Installs recommended VS Code/Cursor extensions for Java/Spring Boot/Gradle development. Prompts the user for each extension before installing.

## Important: IDE CLI detection

Detect the correct CLI for the current IDE. Try in this order:

```bash
if command -v cursor &>/dev/null; then
  IDE_CLI="cursor"
elif [ -x "/Applications/Cursor.app/Contents/Resources/app/bin/cursor" ]; then
  IDE_CLI="/Applications/Cursor.app/Contents/Resources/app/bin/cursor"
elif command -v code &>/dev/null; then
  IDE_CLI="code"
else
  echo "Neither cursor nor code CLI found" && exit 1
fi
```

Use `$IDE_CLI` for all extension commands. Do not hardcode a specific CLI.

## Dependency Order

Extensions MUST be installed sequentially, one at a time. Wait for each install
to complete before starting the next. The install order matters:

1. `redhat.java` first -- most other Java extensions depend on it.
2. `vscjava.vscode-java-pack` second -- this is an extension pack that bundles
   `redhat.java`, `vscode-java-debug`, `vscode-java-test`, `vscode-maven`,
   `vscode-java-dependency`, and `vscode-gradle`. If `redhat.java` is already
   installed, the pack will skip it.
3. Everything else after the pack is installed.

Do NOT install extensions in parallel. Dependent extensions that activate before
their dependencies are present will show errors and require a reload.

## Marketplace Differences

Extension availability varies by IDE. If an install fails with "Extension not
found", note it to the user and move on. Known unavailable in Cursor:
`vscjava.vscode-lombok`.

## Large Workspace Warning

The Red Hat Java extension (`redhat.java`) auto-discovers and imports every
`build.gradle` / `pom.xml` in the workspace. The Search Engineering workspace
uses a **lean model** where only actively worked-on repos are in the
`.code-workspace` file (typically 1-3 repos). Before installing, check how
many project repos are currently active:

- If only 1-3 repos are active, import is fast -- proceed normally.
- If many repos are active, warn the user and suggest running `focus` (via the
  `vscode-workspace` skill) to reduce the active set before installing.
- First import per repo can take a minute while dependencies download.
  Subsequent loads use a cache and are much faster.

## Workflow

### Step 1: Resolve the IDE CLI

Use the detection logic from the "IDE CLI detection" section above to set
`$IDE_CLI`. Verify it works:

```bash
"$IDE_CLI" --version
```

If neither `cursor` nor `code` is found, stop and ask the user.

### Step 2: Check what's already installed

```bash
"$IDE_CLI" --list-extensions
```

Store the output as `INSTALLED`. This determines which extensions to skip.

### Step 3: Present extensions and prompt

Present the extensions below grouped by tier. For each extension, show:
- Name and publisher
- One-line description of what it does
- Whether it's already installed (check against `INSTALLED`)

Skip any extension that is already installed -- just note it as "already installed" and move on.

**Essential -- core Java/Spring Boot development:**

| Extension ID | Name | Purpose |
|-------------|------|---------|
| `vscjava.vscode-java-pack` | Extension Pack for Java | Language support, debugger, test runner, Maven, Gradle, project manager (bundles 6 extensions including `redhat.java` and `vscjava.vscode-gradle`) |
| `vmware.vscode-boot-dev-pack` | Spring Boot Extension Pack | Spring-aware navigation, Boot Dashboard, Actuator, Initializr |
| `eamodio.gitlens` | GitLens | Inline blame, commit graph, file history, PR integration |
| `redhat.vscode-yaml` | YAML | Validation and completion for application.yml, docker-compose, k8s |

**Recommended -- high value add for Search Engineering:**

| Extension ID | Name | Purpose |
|-------------|------|---------|
| `SonarSource.sonarlint-vscode` | SonarQube for IDE | Real-time code quality and security scanning (requires Java 21+ runtime) |
| `AmazonWebServices.aws-toolkit-vscode` | AWS Toolkit | Lambda, S3, CloudWatch Logs, CloudFormation management |
| `ms-azuretools.vscode-docker` | Docker | Dockerfile/Compose IntelliSense, container explorer (works with Podman) |

**Situational -- install as needed:**

| Extension ID | Name | Purpose |
|-------------|------|---------|
| `redhat.vscode-xml` | XML | pom.xml editing, Spring XML config, schema validation |

Ask the user which tiers they want:
- **All** -- install everything not already present
- **Essential only** -- just the core Java stack
- **Pick individually** -- go through each one and ask yes/no

### Step 4: Check active repo count

Check how many project folders (not `workspace` or `dev-ai-tools`) are in the
`.code-workspace` file. If more than 5 are active, warn the user:

> You have N project repos active. Java extensions will import all of them,
> which may take a while. Consider using `focus` to reduce the active set
> first. Proceed anyway?

If 1-5 repos are active, skip the warning and proceed.

### Step 5: Install selected extensions

Install one at a time using the resolved `IDE_CLI`. Always install the
Extension Pack for Java first if selected (it provides the base `redhat.java`
dependency).

```bash
"$IDE_CLI" --install-extension <extension-id>
```

Wait for each install to finish before starting the next. After each install,
confirm success or report any error. If an extension is "not found" in the
marketplace, note it and continue.

### Step 6: Report

Summarize what was done:
- How many extensions were installed
- How many were already present (skipped)
- How many the user declined
- If any installs failed, list them with the error

Remind the user to reload the window (`Cmd+Shift+P` / `Ctrl+Shift+P` -> `Developer: Reload Window`).
