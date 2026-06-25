---
name: openspec
description: >
  Spec-driven development with OpenSpec. Guides users through exploring ideas,
  creating proposals, generating design/spec/task artifacts, implementing, and
  archiving. Handles prerequisites (Node.js, CLI install) and auto-bootstraps
  repos. Use when the user mentions openspec, spec-driven development, wants to
  plan a change, or asks to create a proposal, spec, or design for a feature.
---

# OpenSpec

## Related skills

- **`jira`** -- fetch stories, search with JQL, get sprint data
- **`confluence`** -- fetch pages, search documentation

For CLI details, schema management, and troubleshooting see
[REFERENCE.md](REFERENCE.md).

## Interaction Flow

The workflow follows: Prerequisites -> Branch Check -> Jira/Confluence Context (optional) -> Explore or Propose -> Create Artifacts -> Apply -> Verify -> Archive.

**Full sequence diagram:** see [REFERENCE.md](REFERENCE.md#interaction-flow).

---

## Prerequisites

Run in order before any workflow step. Each depends on the previous.

### 1. Node.js (>= 20.19.0)

```bash
node --version 2>/dev/null
```

If missing or below 20.19.0, detect available tools and present options via
**AskQuestion**:

| Condition | Option |
|-----------|--------|
| `command -v nvm` succeeds | `nvm install 20` (recommended) |
| `command -v fnm` succeeds | `fnm install 20` |
| `command -v brew` succeeds | `brew install node@20` |
| None detected | Direct user to https://nodejs.org |

**STOP** until resolved.

### 2. OpenSpec CLI

```bash
which openspec && openspec --version
```

If missing, present install options via **AskQuestion** and offer to run the
selected command:

- `npm install -g @fission-ai/openspec@latest` (recommended)
- `pnpm add -g @fission-ai/openspec@latest`
- `yarn global add @fission-ai/openspec@latest`
- `bun add -g @fission-ai/openspec@latest`

**STOP** until resolved.

### 3. Repo initialization

Check the **active repo** (not `search.tool.dev-ai-tools`):

```bash
ls openspec/ 2>/dev/null
```

If missing, auto-run without prompting:

```bash
openspec init --tools none --force
```

---

## Branch Check

After prerequisites pass, verify the user is on the right branch for this
effort.

1. Get the current branch:
   ```bash
   git branch --show-current
   ```

2. Show the user the current branch and ask via **AskQuestion**: "You are on
   `<branch>`. Is this the right branch for this effort?"
   - **Yes** -- continue
   - **No, create a new branch** -- proceed to step 3

3. Ask via **AskQuestion** for the branch type:
   - `feature` -- new functionality
   - `bugfix` -- fixing a defect
   - `hotfix` -- urgent production fix

4. Ask for the Jira issue key (e.g., `SRPLT-1234`) and a short description.
   If a Jira story was already mentioned or will be fetched in the next step,
   offer to derive these automatically.

5. Detect the default branch and create:
   ```bash
   git fetch origin
   default_branch=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
   git checkout -b <type>/<JIRA-KEY>-<short-description> "origin/$default_branch"
   ```

   Branch name format: `feature|bugfix|hotfix/<JIRA-KEY>-<kebab-case-description>`
   Example: `feature/SRPLT-1234-add-wholesale-price-filter`

---

## Jira/Confluence Context (optional)

After prerequisites pass and before choosing explore or propose, ask via
**AskQuestion** whether the user wants to pull in external context:

- **Jira story/stories** -- provide issue key(s), or search the current sprint
- **Confluence page(s)** -- provide a page title/URL, or search by keyword
- **Skip** -- proceed without external context

If Jira is selected, read and follow the `jira` skill. If Confluence is
selected, read and follow the `confluence` skill. Either way, use the skill to
fetch the data. Keep the fetched content as background context for the
remainder of the workflow -- do not discard it.

---

## Workflow: explore

Read-only thinking partner. You may read files and search code but NEVER write
application code. You MAY create OpenSpec artifacts if the user asks.

**Stance:** curious not prescriptive, surface multiple directions, use ASCII
diagrams, ground discussion in the actual codebase. If Jira/Confluence context
was fetched, reference it -- e.g., acceptance criteria from a story or
architecture from a Confluence page.

At the start, check for existing changes:

```bash
openspec list --json
```

When insights crystallize, offer to transition to **propose**.

---

## Workflow: propose

1. If no change described, ask what they want to build via **AskQuestion**.
   If a Jira story was fetched, pre-populate the description from its
   summary and acceptance criteria.

2. Derive a kebab-case name (e.g., "add user authentication" -> `add-user-auth`).
   If a Jira story was fetched, derive from its summary.

3. Scaffold:
   ```bash
   openspec new change "<name>"
   ```

4. Get artifact build order:
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse `applyRequires`, `artifacts`, `changeRoot`, `artifactPaths`,
   `actionContext`.

5. Ask via **AskQuestion**: create artifacts **one at a time** (continue) or
   **all at once** (ff)?

---

## Workflow: create artifacts

Called from **propose**. Two modes:

- **continue** -- create each artifact, pause for user to review/revise.
- **ff** -- create all artifacts, then pause for review/revise.

### Artifact creation loop

1. Get next ready artifact:
   ```bash
   openspec status --change "<name>" --json
   ```

2. Get its instructions:
   ```bash
   openspec instructions <artifact-id> --change "<name>" --json
   ```
   JSON fields: `template` (output structure), `instruction` (guidance),
   `context` (project background -- constraints for you, do NOT include in
   output), `rules` (artifact rules -- constraints for you, do NOT include in
   output), `resolvedOutputPath` (write target), `dependencies` (read these
   first).

3. Read dependency artifacts, then create the file using `template` as
   structure. Write to `resolvedOutputPath`.

4. **continue mode:** After each artifact, ask the user to review. Apply any
   revisions before creating the next artifact.

   **ff mode:** Continue to next artifact without pausing.

5. Repeat until all `applyRequires` artifacts are `done`.

6. **Review checkpoint:** Show a summary of all artifacts created. Ask the
   user if they want to review or revise any artifacts before proceeding.
   Apply revisions. Then proceed to **apply**.

---

## Workflow: apply

1. Get implementation instructions:
   ```bash
   openspec instructions apply --change "<name>" --json
   ```

2. Read `tasks.md` from the change directory.

3. Use **TodoWrite** to track progress. Work through each task: read existing
   code, implement, mark the checkbox in `tasks.md`, show brief progress.

4. **Review checkpoint:** When all tasks are complete, ask the user if they
   want to revise any planning artifacts based on what was learned during
   implementation (e.g., design assumptions that turned out wrong, new
   requirements discovered). Apply revisions, then proceed to **verify**.

---

## Workflow: verify

1. Read all planning artifacts. Compare against the implementation: are all
   spec requirements addressed? Does the implementation match the design? Are
   all tasks complete?

2. Run structural validation:
   ```bash
   openspec validate "<name>" --json
   ```

3. If issues found, list them and ask the user how to proceed.

4. When clean, present options via **AskQuestion**:
   - **Run tests** -- detect the project's test command (`./gradlew test`,
     `mvn test`, `npm test`, etc.) and run it. If tests fail, help fix before
     proceeding. After pass, ask: review code or archive?
   - **Review code** -- summarize changes by file (what was added, modified,
     removed). Let the user ask questions or request adjustments.
   - **Archive** -- proceed directly.

---

## Workflow: archive

Merges delta specs into `openspec/specs/` and moves the change to
`openspec/changes/archive/`. There is no separate sync CLI command -- spec
merging happens here.

1. Show delta specs:
   ```bash
   openspec show "<name>" --deltas-only --json
   ```

2. Confirm via **AskQuestion**: list the delta specs that will be merged and
   ask the user to confirm.

3. Archive:
   ```bash
   openspec archive "<name>" --yes
   ```

---

## Guardrails

- **Artifact completion is file-based.** There is no `complete`, `done`, or
  `mark` CLI command. Write the artifact file to the expected path and
  `openspec status` will automatically show it as `done`.
- **explore** is read-only. Never write application code during explore.
- Always read dependency artifacts before creating a new one.
- `context` and `rules` from `openspec instructions --json` are constraints
  for you. Never copy `<project-context>` or `<artifact-rules>` blocks into
  artifact files.
- Confirm with the user before archiving.
- Operate on the active repo, not `search.tool.dev-ai-tools`.
