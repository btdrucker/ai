---
name: create-agents-md
description: Create a high-quality AGENTS.md (or CLAUDE.md) for any repository through deep discovery, structured drafting, automated self-critique via quiz subagents, metadata purity auditing, and adversarial review. Use when the user asks to create an AGENTS.md, CLAUDE.md, repository context file, agent configuration, write agent instructions for a repo, or set up AI agent context for a project. Do not use for README files, CONTRIBUTING guides, general documentation, or non-agent-context files.
---

# Create AGENTS.md

Generate a minimal, high-signal AGENTS.md for the current repository. The process is thorough so the output can be minimal.

**Core constraint:** Gloaguen et al. (2026) found that context files reduce agent task success when they restate cheaply-discoverable information (+20% inference cost, marginal benefit). But "discoverable" is not "cheap" -- in a 500-file codebase, an architectural pointer costs 20 tokens and saves 3000 tokens of exploration. The standard: every line must save more inference cost than it adds. Highest-value content: cross-repo context, architectural shortcuts, ecosystem relationships, institutional judgment. More discovery -- including beyond the repo boundary -- less output.

## Process

### Phase 1: Deep Discovery

Spawn 4+ parallel explore agents covering:

1. Top-level structure and README
2. Existing AI config (`.cursor/`, `.cursorrules`, `AGENTS.md`, `CLAUDE.md`)
3. Content and conventions (read actual files, not just listings)
4. Git history and contributors

**Early-exit check:** if the repo already has an AGENTS.md, run Phase 4 Round 1 quizzes against the existing file first. If it scores well (no LOW-confidence or NO-starting-point results), propose targeted edits rather than a full rewrite.

Then go deeper. All methods apply regardless of repo type -- adapt to what the repo contains:

- **Trace a complete flow.** Pick one real path through the repo (API request, document reference chain, data pipeline, build target) and follow it end-to-end.
- **Read 3+ instances of every recurring artifact type.** What's conventional (all do it) vs incidental (only one does) IS the architecture. You cannot discover conventions from one instance. Also watch for **critical singletons** -- a unique middleware or historical workaround that appears once but explains a major decision.
- **Find ALL instances of critical files.** For API specs, build configs, database configs, and similar artifacts: glob for all of them, not just the first match. A repo with two OpenAPI specs (e.g., one per bounded context) needs both in the AGENTS.md -- map each to its owning module or context in the directory map or navigation table. Dropping one silently is a correctness failure, not a minimization win.
- **Map boundaries.** Module vs package vs service vs directory. Dependency directions. Read build files and import patterns.
- **Look for implicit rules.** The highest-value content: things invisible in any single file but obvious across 5-10. These are what agents will violate without guidance.
- **Identify the configuration and environment story.** Environments, secrets, feature flags.
- **Read the test structure.** Testing conventions tell agents how to verify their own work.
- **Explore the ecosystem.** The highest-value AGENTS.md content is what can't be discovered from the repo alone. Check sibling directories (`../*`) for related repos -- shared dependencies, upstream/downstream services, consumers, libraries. If cross-repo search tools are available (MCP servers, workspace-level skills, multi-root workspaces), use them. If external knowledge sources exist (Confluence, wikis, design docs, enterprise GitHub, commit history), scan them during discovery, not just list them in the output. The goal: understand the repo's role and boundaries within its larger system.

Do not skim. File listings alone are never enough -- read actual content to recognize patterns.

### Phase 2: User Clarification

Ask 1-2 critical scoping questions (only what you genuinely cannot discover):

- Scope of external tool/skill references
- Gitignored content that may or may not exist
- Domain concepts not documented anywhere in the repo

Do not proceed to drafting until answered. If the user declines to answer or says to proceed without clarification, note the unanswered questions as assumptions in the AGENTS.md draft and flag them for user review in Phase 7.

### Phase 3: Structured Draft

Write AGENTS.md using the structural template in [reference.md](references/reference.md).

**Line budget scales with repo complexity.** Base: 60 lines (covers repo identity, directory map, toolchain commands, navigation, gotchas, escalation/closure). Earn additional budget only through discovery:

- +up to 30 for domain terminology that's opaque without definitions (enterprise acronyms, project-specific jargon an agent can't resolve from code alone). Roughly 1 line per term; if the glossary exceeds 20 terms, the repo likely needs a separate glossary file with a pointer instead.
- +up to 30 for cross-repo/ecosystem context (upstream/downstream relationships, shared infrastructure, deployment topology). Roughly 1-2 lines per external dependency or relationship.
- +up to 30 for non-obvious architectural conventions found via the "read 3 instances" method (persistent judgment calls, implicit rules). Each convention earns its lines only if it passed the "read 3 instances" bar -- observed across multiple files, not inferred from one.

Hard ceiling: 150 lines. Each section under 50. Most repos should land 60-100. If the draft exceeds budget, cut by:
1. Removing anything already enforced by toolchain (linters, formatters, CI gates)
2. Removing anything discoverable in ≤3 tool calls with unambiguous results (but keep terms that are discoverable yet ambiguous -- see Phase 5 discoverability test)
3. Removing anything duplicating README.md or files the navigation table points to
4. Collapsing verbose tables

**Rules:**
- **Metadata purity:** every line describes shape (what the repo IS, how it's organized, what terms mean, where to look) not state (specific values, specific bugs, behaviors that could change).
- **Describe what exists:** use the repo's actual directory names, paths, and conventions. Do not relabel directories based on assumptions about their purpose -- read the contents to confirm. A `/docs/` directory containing OpenAPI specs is a specs directory, not a documentation directory. If the team uses `/specs` for feature specifications and `/docs/` for documentation, label them accordingly. The AGENTS.md describes what exists, not what a template prescribes.
- **Infrastructure dependencies survive minimization.** Databases (RDS, Aurora, DynamoDB), message queues (SQS, Kafka), caches (Redis, ElastiCache), and other infrastructure a service directly connects to are high-value architectural context. They are not cheaply discoverable -- connection configs may be in environment variables, secret managers, or Spring properties spread across profiles. Do not remove them during the purity audit.
- **Toolchain-first:** if a constraint is enforced by a tool in the repo, point to the tool config instead of restating it.
- **Context anchoring:** negative instructions ("don't do X") place X in the agent's attention and can increase the unwanted behavior (the Pink Elephant Problem). For gotchas and constraints, prefer positive framing. If a gotcha requires "don't" phrasing, treat it as a signal that the underlying codebase ambiguity should be fixed structurally (rename, delete legacy code, add a linter rule). Only document the gotcha if the structural fix isn't feasible.
- **Persistent judgment:** prioritize institutional judgment that tooling cannot express -- how to resolve ambiguity between valid approaches, what architectural values to uphold, when one pattern wins over another. These are the highest-value lines in an AGENTS.md.
- **Gotcha verification:** before including any gotcha or constraint, trace it in the actual code. Naming conventions and file structures can mislead -- a field or header that looks sensitive may be routine. Only include gotchas you have confirmed through code inspection, not ones you inferred from naming alone.
- **Verification completeness:** if the AGENTS.md includes a "task is complete when" checklist, enumerate ALL build and test targets the team actually uses (build, test, integrationTest, check, etc.), not just the most common one. Read the build file to confirm which targets exist. A checklist that omits a target the CI runs will cause agents to declare work complete before it is.
- **Cross-tool compatibility:** after writing, create a symlink: `ln -s AGENTS.md CLAUDE.md`. The symlink ensures both tools read the same content from a single source of truth. If the repo already has a CLAUDE.md with independent content, discuss with the user before replacing it with the symlink. Cursor reads `.cursor/rules/*.mdc` files for glob-scoped rules; AGENTS.md provides the cross-tool baseline context layer.

### Phase 4: Self-Critique via Quiz Subagents

The critical quality gate. Question design and scoring details: see [reference.md](references/reference.md) → Quiz Methodology. Spawn readonly subagents that read ONLY the AGENTS.md file.

**Round 1 -- Foundation (3 subagents in parallel):**

- Agent A: Navigation ("where would I look to...?")
- Agent B: Domain terminology ("what is X?")
- Agent C: Conventions and gotchas ("how do I...?", "what's the trap?")

Each agent scores every answer: confidence (HIGH/MEDIUM/LOW), starting point (YES/PARTIAL/NO). Fix any result that isn't HIGH confidence with YES starting point.

**Round 2 -- Self-Stump (2 subagents in parallel):**

The parent agent generates 10 genuinely hard questions -- ones that in practice require 2+ files to answer -- then passes them to 2 readonly subagents that answer using only AGENTS.md. Instruct subagents to cite which AGENTS.md sections they referenced for each answer. Requirements:

- At least 2 requiring cross-repo or external tooling
- At least 2 "negative space" questions (what ISN'T there, what's missing)
- At least 3 testing pattern recognition ("Where would I add a new X?", "What pattern do I follow for Y?")
- Probe areas where Phase 1 discovery was shallow -- boundaries you explored structurally but didn't deeply understand, cross-cutting concerns you noticed but didn't trace

Score results. NO starting point = gap to fix. Confident but WRONG = routing failure to fix. Correct but citing 3+ AGENTS.md sections to compose the answer = over-routing; consolidate redundant pointers so the agent reaches the answer in fewer hops.

**Verify before promoting -- critical safeguard.** Subagents reading only AGENTS.md may infer constraints that don't exist. Before adding any gotcha, security constraint, or behavioral claim to the AGENTS.md based on subagent feedback:

1. Locate the actual code the subagent's claim refers to
2. Trace its usage -- read callers, consumers, and tests to understand actual behavior, not just existence
3. Promote only if the code confirms the constraint; discard if it doesn't

Example failure: a subagent sees a field named `discoverHeaders` and reports "sensitive header data must not reach the client." A grep confirms the field exists (step 1), but tracing callers (step 2) reveals it's a routine cache tag. Without step 2, a false gotcha enters the AGENTS.md. The parent agent's interpretation of subagent reports is the most error-prone step in this process.

**Round 3 -- User Challenge:**

Present Round 2 results. Ask the user to generate their own challenge questions. Run through subagents. For any completely wrong answer, investigate whether AGENTS.md can help or the knowledge lives elsewhere.

If the user declines, skip -- Round 2 is the minimum quality bar.

### Phase 5: Metadata Purity Audit

Re-read the AGENTS.md. For every line, apply five tests:

- **6-month test:** will this still be true without anyone updating it? If no: remove, generalize, or relocate.
- **Toolchain-first test:** is this enforced by a tool in the repo? If yes: replace with a pointer to the tool config.
- **Discoverability test:** could an agent find this in ≤3 tool calls (grep, glob, read a known file)? If yes and the information is unambiguous in context, the line costs more inference than it saves. Two categories pass this test despite being findable: (1) domain terms whose meaning is opaque -- discoverable but ambiguous, so the definition adds value; (2) infrastructure dependencies (databases, queues, caches) -- individual connection references may be discoverable, but the full dependency graph is scattered across environment configs, secret managers, and profiles, making reconstruction expensive.
- **README test:** does this line appear (in substance) in README.md or another file the navigation table already points to? If yes, remove it unless the AGENTS.md version adds routing value the original lacks.
- **Necessity test:** if this line were removed, would an agent perform measurably worse on real tasks? If the answer isn't clearly yes, the line is a candidate for removal. Phase 4 quizzes test for missing coverage; this test catches excess -- the failure mode Gloaguen identified.

### Phase 6: Inline Adversarial Review

If a panel-review skill is available (repo-level or user-level), invoke it targeting the AGENTS.md file. Otherwise, run a compressed inline review:

- 3 personas: domain expert, technical writer, agent framework engineer
- 2 rounds maximum
- Each criticism requires: category, severity, location, description
- Deliberation: unanimity required to sustain a criticism
- Fix all agreed criticisms in place
- Focus areas: correctness, metadata purity, actionability, context anchoring

### Phase 7: Commit

If in a git repo and user approves, create a single commit with a descriptive message. If a commit-message skill is available (repo-level or user-level), use it.

### Definition of Done

- Within line budget (60 base + earned additions, hard ceiling 150)
- Phase 4 Round 1: all results HIGH confidence with YES starting point
- Phase 4 Round 2: at most 1 NO-starting-point answer
- Phase 6: terminates cleanly or user accepts remaining concerns
- User has reviewed the final artifact -- this is not optional. Present the artifact and explicitly ask the user to verify: (1) gotchas and constraints reflect actual repo behavior, not inferred assumptions; (2) infrastructure dependencies are accurate; (3) conventions match the team's actual practice. Subagent quiz results are filtered through the parent agent's interpretation and can mischaracterize domain-specific behavior -- the parent may promote a subagent's inference as a hard rule when it's actually routine.
