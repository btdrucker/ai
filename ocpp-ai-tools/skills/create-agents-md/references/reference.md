# AGENTS.md Reference

## Structural Template

Include sections relevant to the repo. Omit what's irrelevant. Add what's needed. This is a menu, not a checklist.

### Repo Identity (2-5 lines)

What the repo is, who owns it, what its primary artifact is.

Do NOT include: project history, motivation, or anything a README already covers.

### Directory Map (table)

One row per top-level directory. Columns: directory, what's here, status/type tag.

Do NOT include: file-level detail, nested directory listings, or anything `tree` would show.

### Domain Glossary (table)

Acronyms and terms an agent needs to not be confused. One-line definitions.

Do NOT include: terms the agent already knows (generic tech terms), terms defined in files the glossary points to, or full explanations (those belong in docs).

### Toolchain Registry (table)

Exact commands for build, test, lint, format, type-check. Command-first -- the command IS the instruction. Include file-scoped variants where the toolchain supports them -- these enable faster feedback loops and reduce inference cost.

| Intent | Command | Notes |
|--------|---------|-------|
| Build | `make build` | Outputs to `./bin` |
| Test (all) | `make test` | Runs with `-race` |
| Test (one) | `go test ./path/to/pkg/...` | Prefer for single-file changes |
| Lint | `golangci-lint run` | See `.golangci.yml` |
| Lint (one) | `golangci-lint run ./path/to/file.go` | |

For non-code repos, adapt the table: a documentation repo might list validation (`markdownlint`), link checking, and publishing commands; an IaC repo might list `terraform validate`, `terraform plan`, and `tflint`.

Do NOT include: descriptions of what the tools enforce (the tool config IS the spec).

### Conventions

Naming patterns, structural patterns, architectural patterns -- whatever the discovery phase found. Document as rules that apply to all new work. Prioritize **persistent judgment**: how to resolve ambiguity between valid approaches, what architectural values to uphold, when one pattern wins over another. These judgment calls are the highest-value content -- institutional knowledge that tooling cannot express.

**Judgment call format:** "When X, prefer Y over Z because [reason]."

Examples:
- "When adding a new endpoint, prefer extending an existing controller over creating a new one -- the route namespace is the organizing principle, not the domain entity."
- "When a test needs external state, prefer Testcontainers over mocks -- integration fidelity is prioritized over speed in this repo."
- "When a module needs shared state, prefer explicit parameter passing over singleton registries -- testability and traceability outweigh convenience in this codebase."

The "because" clause is what makes these lines worth their token cost. Without it, the judgment is an unexplained rule an agent may override; with it, the agent can apply the same reasoning to novel situations.

Do NOT include: descriptions of specific implementations, one-off patterns, or anything a linter already enforces.

### Key Navigation Patterns (table)

"You want to..." → "Start here" routing table. Most important routes first.

Do NOT include: more than ~12 rows (diminishing returns), routes to files the directory map already covers, or specific section names within other documents.

### Gotchas and Constraints

Things an agent will get wrong without warning. Semantic traps, common confusions, data model surprises.

**Coupled files:** call out files that must change together -- schema and entity classes, protobuf definitions and generated stubs, API specs and controllers, infrastructure config and app config. Agents can't discover coupling relationships from reading one file; without explicit guidance they'll modify one side and create silent drift.

**Context anchoring warning:** negative instructions ("don't do X") place X in the agent's attention and may increase the unwanted behavior. Prefer positive framing. If a gotcha requires "don't" phrasing, treat it as a signal that the underlying codebase ambiguity should be fixed structurally (rename, delete legacy code, add a linter rule). Only document the gotcha if the structural fix isn't feasible.

Do NOT include: specific field values, specific bug examples, or system behaviors that could change with a code deploy. State the principle, not the instance.

### Escalation Rules

What to do when blocked. NEVER/ASK/ALWAYS tiers.

```
NEVER: guess on ambiguous specs, add dependencies without discussion, force push
ASK: before deleting files, before running migrations, before changing public APIs
ALWAYS: explain plan before writing code, run tests before reporting done
```

### Closure Definitions

What proves a task is done. Specific commands and exit codes.

```
A task is complete when ALL pass:
1. `make lint` exits 0
2. `make test` exits 0
3. Changed files staged and committed
```

### External Knowledge Sources

Where domain knowledge lives outside the repo (Confluence spaces, wikis, Slack channels, external APIs). Name the source so agents check it rather than confabulating.

### Guardrails

What agents should not modify without being asked. Protect primary artifacts and verified investigation results.

### Freshness

End the file with a `Last validated:` date line. Not a staleness timer -- a signal to future agents (and humans) that the content was verified against the repo state as of that date. An agent that sees a validation date 6+ months old knows to treat routing pointers with appropriate skepticism.

---

## Pattern Recognition Guide

These methods use code-repo examples but apply to any repo type. For documentation repos, "trace a flow" means following a reference chain across documents. For IaC repos, it means tracing a Terraform dependency graph. For monorepos, run the methods per-package and note cross-package conventions. Adapt the method to the content -- the principle (discover conventions from multiple instances, not one) is universal.

### The "Read 3 Instances" Method

Read 3+ files of the same type (controllers, tests, config files, documentation pages). Note what ALL of them do -- that's convention. Note what ONLY ONE does -- that's incidental or a critical singleton worth investigating.

Convention example: "All controllers validate auth before business logic" -- document this.
Incidental example: "One controller has a retry loop" -- don't document this unless it's a deliberate pattern.
Singleton example: "One middleware handles all rate limiting" -- document this if it's architecturally significant.

### The "Trace a Flow" Method

Pick a real entry point and follow it to completion. Note:
- Layer names (controller → service → repository → database)
- What each layer is responsible for
- Handoff conventions (DTOs at boundaries? Events? Direct calls?)
- Error handling at each layer

The flow reveals the architecture. Document the layer names and responsibilities, not the specific flow.

### The "Boundary Direction" Method

Read import statements across 5-10 files. Map which packages import which. The direction of dependencies reveals:
- Which layers are "inner" (depended on, never depend outward)
- Which layers are "outer" (depend inward, never depended on)
- Whether the repo follows clean architecture, hexagonal, layered, or ad-hoc patterns

Document the rule ("domain never imports infrastructure"), not the observation ("UserService doesn't import DatabaseConfig").

### The "Ecosystem Scan" Method

Look outside the repo. Scan `../*` for sibling repos. For each, read the README and build file -- enough to answer: what is this, and does it depend on or interact with the current repo? Look for:
- Shared dependencies (same libraries, same message queues, same databases)
- API contracts (does a sibling import types from this repo, or call its endpoints?)
- Naming conventions that span repos (if all sibling repos use a pattern, the current repo should too)
- Deployment topology (do these repos deploy together? Share infrastructure?)

The ecosystem context reveals what the repo IS in a way that reading the repo alone cannot. A service that's one of 3 behind an API gateway has different constraints than a standalone service. Document the role, not the inventory.

If cross-repo search skills or MCP servers are available, use them for deeper exploration. If not, `../*` READMEs and build files are a high-signal, low-cost baseline.

### Metadata vs Content

| Metadata (belongs in AGENTS.md) | Content (belongs elsewhere) |
|---|---|
| "We use the repository pattern for all data access" | "UserRepository.findById() calls JPA" |
| "Tests use Testcontainers for integration testing" | "UserServiceIT uses a Postgres Testcontainer on port 5433" |
| "Error responses follow RFC 7807 Problem Details" | "The /users endpoint returns 422 for invalid email" |
| "Environment config uses Spring profiles" | "The prod profile sets pool size to 100" |

**Test:** "Is this a pattern that applies to all new work, or a description of one specific instance?"

---

## Quiz Methodology

### Scoring Matrix

| Confidence | Meaning |
|---|---|
| HIGH | AGENTS.md clearly answers this |
| MEDIUM | Can infer an answer but it's not explicit |
| LOW | AGENTS.md doesn't cover this |

| Starting Point | Meaning |
|---|---|
| YES | AGENTS.md pointed directly to the right file/section |
| PARTIAL | AGENTS.md got me to the neighborhood but I had to search |
| NO | AGENTS.md gave no useful starting point |

### Round 1 Question Design (Foundation)

Navigation: "Where would I look to understand X?", "Which file documents Y?"
Domain: "What is X?", "What's the difference between X and Y?"
Conventions: "How should I name a new X?", "What's the trap when doing Y?"

8 questions per category. All should be answerable from AGENTS.md alone.

### Round 2 Question Design (Self-Stump)

Multi-hop: questions that in practice require 2+ files, but must be answerable from AGENTS.md alone. "Trace field X from source to API response."
Negative-space: "What endpoints aren't implemented?", "What's missing from the schema?"
Pattern recognition: "Where would I add a new controller?", "What pattern do I follow for error handling?"
Cross-system: "How does service A communicate with service B?"

Generate questions that probe YOUR OWN shallow areas -- where you explored structurally but didn't deeply understand.

### Interpreting Wrong Answers

| Subagent Behavior | Diagnosis | Fix |
|---|---|---|
| Confident + correct | AGENTS.md works | None |
| Confident + wrong | Routing failure -- AGENTS.md pointed to wrong place or agent confabulated | Add or fix navigation entry |
| Low confidence + no answer | Missing coverage -- AGENTS.md doesn't address this area | Add section or navigation entry |
| Correct but required extensive searching | Weak routing -- AGENTS.md is too vague | Sharpen the navigation pointer |
| Correct but cited 3+ sections | Over-routing -- redundant pointers for one topic | Consolidate into a single clear route |

The most dangerous failure is **confident + wrong** (confabulation). This means AGENTS.md gave enough context for the agent to construct a plausible but incorrect answer. Fix by adding more specific routing or by explicitly noting where the knowledge lives.

---

## Metadata Purity Checklist

### The 6-Month Test

For every line: "Will this still be true in 6 months without anyone updating it?"

Stable (keep): repo purpose, directory structure, domain terms, architectural patterns, naming conventions, tool commands
Unstable (remove or relocate): specific field values, package versions, endpoint URLs, section names in other docs, system behaviors tied to code that ships

### The Toolchain-First Test

For every constraint: "Is this already enforced by a tool in the repo?"

If yes: replace the instruction with a pointer to the tool config. Example:
- Bad: "Use 2-space indentation, no trailing whitespace, LF line endings"
- Good: "Format: `prettier --write .` (see `.prettierrc`)"

### The Discoverability Test

For every line: "Could an agent find this in ≤3 tool calls (grep, glob, read a known file)?"

If yes and the result is unambiguous: remove. The line adds inference cost without saving exploration.
If yes but the result is ambiguous (e.g., an acronym that appears in 40 filenames but whose meaning is unclear): keep. The definition resolves ambiguity cheaply.

### The README Test

For every line: "Does this appear (in substance) in README.md or a file the navigation table points to?"

If yes: remove unless the AGENTS.md version adds routing value the original lacks. A directory listing that duplicates the README wastes tokens. A directory listing that adds status tags or "what's here" context the README omits earns its space.

### Common Violations

- Specific field names as examples of gotchas (use the principle, not the instance)
- Package version lists (will go stale)
- Section-name pointers into other documents (will drift if reorganized)
- Endpoint URLs (will change with deploys)
- Restated linter/formatter rules (the tool config is the authority)
- LLM-generated content from `/init` commands (treat as inventory, not output)

### What Belongs Elsewhere

| Content Type | Belongs In |
|---|---|
| System-specific troubleshooting | helpers/ or project docs |
| Architectural principles with specific examples | Design docs or ADRs |
| Tool authentication details | Individual skill files |
| Knowledge only on Confluence/wiki | Note the source in External Knowledge Sources; don't reproduce |
| Anything a linter/formatter/CI gate enforces | Tool config files |

---

## Research Basis

- **Gloaguen et al. (2026):** Context files reduce agent task success while inflating inference cost by 20%+. Developer-written files offer only marginal (+4%) improvement when minimal. [arxiv.org/abs/2602.11988](https://arxiv.org/abs/2602.11988)
- **ASDLC spec:** Treat AGENTS.md as code -- optimized, falsifiable, version controlled. Introduces persistent judgment and context anchoring concepts. [asdlc.io/practices/agents-md-spec](https://asdlc.io/practices/agents-md-spec)
- **Crosley (2026):** Command-first, task-organized, closure-defined. Instructions without verification commands are suggestions, not rules. [blakecrosley.com/blog/agents-md-patterns](https://blakecrosley.com/blog/agents-md-patterns)
- **agentsmd.io (2026):** File-scoped commands, safety boundaries, and granular verification as highest-value patterns. [agentsmd.io/agents-md-best-practices](https://agentsmd.io/agents-md-best-practices)
