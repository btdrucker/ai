---
name: vscode-workspace
description: >
  Manage the Search Engineering workspace (VS Code and Cursor). Supports
  bootstrap, update, focus, add, remove, list, and reset. Use when the user
  wants to set up their dev environment, switch between repos, or manage
  workspace folders.
---

# Workspace Management

> This skill works in both VS Code and Cursor.

## Related skills

- **`sdkman`** -- JDK version management (called during bootstrap/focus for Java projects)
- **`vscode-java-extensions`** -- recommended IDE extensions for Java development

Manages the Search Engineering multi-root workspace using a **two-tier
model**: a full registry of all repos and a lean active workspace containing
only the repos being worked on.

- **Registry** (`workspace-registry.json`): Full catalog of all repos -- paths,
  GitHub URLs, default branches, types. Source of truth for "what exists."
- **Active workspace** (`search-engineering.code-workspace`): Contains only the
  workspace directory + dev-ai-tools + repos being actively worked on (typically
  1-3 repos).

This prevents Java IDE extensions from importing every Gradle/Maven project at
once, which is catastrophic in a large multi-repo workspace.

## Before you begin: Context-loss warning

Operations that modify the `.code-workspace` file (focus, add, remove, reset,
bootstrap) may cause the IDE to reload, terminating the agent session.

**IMPORTANT**: Before any such operation, warn the user:

> **Warning**: This will modify the workspace file, which may cause the IDE to
> reload and terminate this session. Save any important context first.

Wait for explicit confirmation. Read-only operations (list, update) do not
need this warning.

## Step 0: Check prerequisites

Verify required tools:

```bash
gh auth status
ssh -T git@github.com
```

- `gh auth status` should show an authenticated user. If not, tell the user to
  run `gh auth login` and stop.
- `ssh -T git@github.com` should respond with "successfully authenticated". If
  not, tell the user to set up SSH keys for GitHub and stop.

## Step 1: Determine mode

| Mode | Trigger | Modifies workspace file? |
|------|---------|--------------------------|
| `bootstrap` | No `.code-workspace` file found, or user requests fresh setup | Yes |
| `update` | User asks to refresh/sync repos | No (registry only) |
| `focus <repos>` | User wants to switch to specific repos | Yes |
| `add <repos>` | User wants to add repos without removing current ones | Yes |
| `remove <repos>` | User wants to remove repos from active workspace | Yes |
| `list` | User wants to see available and active repos | No |
| `reset` | User wants to clear workspace back to baseline | Yes |

Detection logic:

1. Search for `*.code-workspace` files in the current workspace
2. If no workspace file found -> `bootstrap`
3. If user mentions specific repos to work on -> `focus` or `add`
4. If user mentions removing repos -> `remove`
5. If user asks to refresh or sync -> `update`
6. If user asks what's available -> `list`
7. If user wants to start fresh -> `reset`

Tell the user which mode was detected and let them override.

## Repo resolution

When a mode accepts `<repos>`, resolve names against `workspace-registry.json`:

1. Read the registry file (same directory as the `.code-workspace` file)
2. Match user input against registry keys:
   - **Exact match**: `kingpin-v1` -> `kingpin-v1`
   - **Substring match**: `kingpin` -> `kingpin-v1`
   - **Prefix match for groups**: `productfeed` -> all `productfeed*` repos
3. If multiple matches and user likely meant one, present the matches and ask
4. If no match, suggest running `update` to refresh the registry

## Layout detection

The workspace file can live in one of two layouts:

- **Layout A -- Dedicated directory**: The `.code-workspace` file is inside a
  subdirectory that is NOT a repo (e.g.
  `search-engineering-workspace/search-engineering.code-workspace`). This
  directory gets added as the first folder entry with name `workspace`.
- **Layout B -- Alongside repos**: The `.code-workspace` file sits in the same
  directory as the cloned repos. Do NOT add this directory as a folder entry.

Detection: Check if the workspace file's containing directory is the common
parent of the repo directories. If yes, Layout B. If the workspace file is in
a subdirectory below the repos' common parent, Layout A.

---

## Mode: bootstrap

Fresh setup. Clones all repos, generates the registry, but creates a lean
workspace with only the baseline folders (no project repos).

### Step B1: Determine target directory

- If the cwd or an open file is inside a `search.service.*` repo, suggest its
  **parent directory** as the default
- Otherwise, ask the user where to clone repos
- Confirm the target directory before proceeding
- Bootstrap always creates Layout A (dedicated directory)

### Step B2: Discover repos

Search GitHub for all search service repos:

```bash
gh search repos "search.service" --owner nike-internal --json name --limit 100
gh search repos "search.lambda" --owner nike-internal --json name --limit 50
gh search repos "search.server" --owner nike-internal --json name --limit 50
gh search repos "search.web" --owner nike-internal --json name --limit 50
gh search repos "gcde.service.pf" --owner nike-internal --json name --limit 50
```

Check which repos are already cloned in the target directory. Present the list
showing status (already cloned / new / not accessible). All repos are selected
by default; user can deselect any.

The AI tools repo (`nike-internal/search.tool.dev-ai-tools`) is always
included.

### Step B3: Clone missing repos

```bash
git clone git@github.com:<org>/<repo-name>.git
```

Run clones in parallel (batches of 5). Handle failures gracefully per-repo.
Skip repos that already exist.

### Step B4: Create workspace file

1. Ask for a workspace directory name. Default: `search-engineering-workspace`.
2. Ask where to create it. Default: the target directory (adjacent to repos).
3. Create the workspace directory (plain folder, no git init).
4. Generate `search-engineering.code-workspace` with **only baseline folders**:

```json
{
  "folders": [
    {
      "name": "workspace",
      "path": "/absolute/path/to/search-engineering-workspace"
    },
    {
      "name": "dev-ai-tools",
      "path": "/absolute/path/to/search.tool.dev-ai-tools"
    }
  ],
  "settings": {},
  "extensions": {
    "recommendations": [
      "vscjava.vscode-java-pack",
      "vmware.vscode-boot-dev-pack",
      "redhat.vscode-yaml",
      "redhat.vscode-xml"
    ]
  }
}
```

No project repos in the workspace file. They are cloned and registered but
not active.

### Step B5: Generate registry

See [Registry generation](#registry-generation) below. Scans ALL cloned repos,
not just active ones.

### Step B6: Report

Summarize: repos cloned, workspace file created, registry generated. Then:

> Workspace is ready with N repos registered. Use **focus** to activate the
> repos you want to work on. Example: "focus kingpin" or "focus productfeed".

---

## Mode: update

Refreshes the registry by discovering new repos from GitHub and cloning any
that are missing. Does NOT modify the `.code-workspace` file.

### Step U1: Determine target directory

Infer from the existing workspace file's folder entries (their common parent).

### Step U2: Discover and clone

Same as bootstrap steps B2-B3. Discover repos from GitHub, clone any that
are new.

### Step U3: Regenerate registry

See [Registry generation](#registry-generation). Scans all cloned repos.

### Step U4: Report

Summarize: new repos discovered, cloned, registry updated. Active workspace
unchanged.

---

## Mode: focus

Replaces the active project set. Keeps workspace dir + dev-ai-tools, removes all
other entries, adds specified repos.

### Step F1: Resolve repos

Use [Repo resolution](#repo-resolution) to match user input to registry entries.
Present the resolved list and confirm.

### Step F2: Update workspace file

1. Read `.code-workspace`
2. Keep only the workspace directory entry (Layout A) and `dev-ai-tools`
3. Add entries for the resolved repos using [Naming rules](#naming-rules) and
   [Folder ordering](#folder-ordering)
4. Write the file

### Step F3: Report

Summarize: which repos are now active, which were removed. Remind user the
window may reload.

---

## Mode: add

Adds repos to the active workspace without removing existing ones.

### Step A1: Resolve repos

Use [Repo resolution](#repo-resolution). Skip any that are already in the
workspace file.

### Step A2: Update workspace file

1. Read `.code-workspace`
2. Append entries for the resolved repos
3. Re-sort all project entries per [Folder ordering](#folder-ordering)
4. Write the file

### Step A3: Report

Summarize: which repos were added, which were already present.

---

## Mode: remove

Removes repos from the active workspace. Repos remain on disk and in registry.

### Step R1: Identify repos to remove

If user specified repos, resolve them. Otherwise, present current active
project repos and ask which to remove. Never allow removing `workspace` or
`dev-ai-tools`.

### Step R2: Update workspace file

1. Read `.code-workspace`
2. Remove the specified entries
3. Write the file

### Step R3: Report

Summarize: which repos were removed. Note they remain on disk.

---

## Mode: list

Read-only. Shows all repos from the registry, highlighting which are currently
active in the workspace.

### Step L1: Load data

1. Read `workspace-registry.json`
2. Read `.code-workspace` to get active folders

### Step L2: Present

Display a table:

| Repo | Type | Active |
|------|------|--------|
| kingpin-v1 | service | * |
| envoy | service | |
| ... | ... | ... |

Mark active repos with `*`. Group or sort alphabetically.

---

## Mode: reset

Clears the workspace back to just workspace dir + dev-ai-tools. Quick way to
start fresh between efforts.

### Step X1: Update workspace file

1. Read `.code-workspace`
2. Keep only the workspace directory entry and `dev-ai-tools`
3. Write the file

### Step X2: Report

Summarize: all project repos removed from active workspace. Registry unchanged.
Prompt: "Use **focus** to activate repos for your next effort."

---

## Naming rules

The display name is derived from the repo namespace:

- **Workspace directory** (Layout A only): always `workspace`
- **AI tools**: always `dev-ai-tools`
- **`search.service.*`**: strip prefix, append ` (service)` -- e.g.
  `search.service.kingpin-v1` -> `kingpin-v1 (service)`
- **`search.lambda.*`**: strip prefix, append ` (lambda)` -- e.g.
  `search.lambda.replicationlistener` -> `replicationlistener (lambda)`
- **`search.server.*`**: strip prefix, append ` (server)` -- e.g.
  `search.server.apolloauthenticationv1` -> `apolloauthenticationv1 (server)`
- **`search.web.*`**: strip prefix, append ` (web)` -- e.g.
  `search.web.collectionsui` -> `collectionsui (web)`
- **`gcde.service.*`**: strip prefix, append ` (gcde)` -- e.g.
  `gcde.service.pfetl` -> `pfetl (gcde)`

Use absolute paths for `path` values.

## Folder ordering

1. **Workspace directory** (Layout A only) -- always first
2. **`dev-ai-tools`** -- always second (Layout A) or first (Layout B)
3. **Project repos** -- sorted alphabetically by base name regardless of prefix

## Registry generation

**Full schema and generation logic:** see [REFERENCE.md](REFERENCE.md#registry-generation).

## Java/Gradle project setup

**Full Java/Gradle setup steps (J0-J5):** see [REFERENCE.md](REFERENCE.md#javagradle-project-setup).

---

## Opening the workspace

After bootstrap, offer to open. Detect the IDE CLI (`cursor` or `code`):

```bash
if command -v cursor &>/dev/null; then
  cursor /path/to/search-engineering.code-workspace
elif command -v code &>/dev/null; then
  code /path/to/search-engineering.code-workspace
fi
```

If the user is already in the workspace, changes take effect when the IDE
reloads (automatic for workspace file modifications).
