---
name: commit-message
description: Generates commit messages in a concise, functional-area style with ticket prefixes and structured bodies. Use when the user asks to commit, write a commit message, or when creating commits on the user's behalf. Review the conventions below and adapt to your team's preferences before adopting.
---

# Commit Message Skill

A specific commit discipline developed through daily use on OCPP repositories. The conventions below are opinionated -- review them and adjust to your team's preferences.

## Branch Workflow

This skill assumes a one-commit-per-branch workflow:

1. **One commit per branch.** All work on a feature branch is squashed into a single commit. This is the norm, not the exception.
2. **Rebase from main.** The branch stays rebased on top of main, not merged.
3. **Force push with lease.** After rebasing or amending, push with `git push --force-with-lease`.

Multiple commits on a single branch happen only by explicit exception (e.g., the user asks to keep commits separate, or there is a deliberate reason to preserve intermediate history).

### Amending

When the user asks to commit during ongoing work on a branch that already has a commit, **amend** the existing commit rather than creating a second one. Rewrite the subject and body from scratch based on the full accumulated diff — do not append to the old message.

If the existing commit cannot be safely amended — it wasn't created by the agent in this session, it has already been pushed without the user requesting a force push, or it belongs to another author — ask the user how to proceed rather than silently creating a second commit.

## Subject Line

```
TICKET - Title Case Noun Phrase
```

- **Always** include a ticket prefix. Use `NOJIRA` (one word, no space) when there is no ticket.
- Derive the ticket from the branch name if it follows a ticket pattern (e.g., `SHROCPP-2175_description`). Fall back to context from the user's prompt. Default to `NOJIRA` only when neither source provides one.
- Dash separator between prefix and description.
- Aim for roughly 3–7 words after the prefix. Name the functional area and the action taken.
- Title Case.

## Body

Add a bullet body (`* `) when the commit includes **more than one independent concern**. A concern is any of:

- A **behavioral change** — something that changes what the system does or returns
- An **API surface change** — new/modified endpoints, error codes, response shapes
- An **architectural change** — extracted classes, new modules, restructured layers
- An **infrastructure/tooling change** — build tool versions, Dockerfile changes, CI config

The unit of concern is a **functional area**, not an individual code change. Group related behavioral changes into one bullet when they serve the same user-facing purpose — e.g., a new flag alias and improved error messages for that flag family are one "CLI ergonomics" concern, not two. Mechanical changes supporting a concern (renames, import cleanup, formatting, test additions, config tweaks, bug fixes that make the primary change work correctly) do not need their own bullets.

Each bullet should do significant lifting — covering a coherent group of related changes. Aim for **3–5 bullets** on large commits. More than 5 is a smell that you're atomizing instead of grouping. No bullet should be vague enough to hide a change, but it should summarize at the functional-area level, not the code-change level.

Omit the body entirely when the subject already captures the full scope (single-concern commits, version bumps, config changes).

Tests that accompany production changes do not need their own bullet. Tests committed *alone* (refactors, stability fixes) do.

## Anti-Patterns

- **Never** use catch-all qualifiers like "w/ other bugs", "and misc fixes", "plus cleanup". If it's worth committing, it's worth naming.
  Bad: `SHROCPP-2142 - Snapshot on Drop w/ other bugs`
  Fix: `SHROCPP-2142 - Snapshot on Drop from Orchestration` with body bullets for each additional concern.
- **Never** concatenate unrelated phrases without structure.
  Bad: `Upgrade to SpringBoot Remove AAA`
  Fix: `NOJIRA - Upgrade to SpringBoot 2.5.15` with a body bullet for the AAA removal.
- **Never** omit the ticket prefix. If there's no ticket, write `NOJIRA`.

## Examples

**Single-concern, small change — no body needed:**
```
NOJIRA - SFx Version to 5.5.0.23
```

**Single-concern, larger change — no body needed:**
```
SHROCPP-2175 - Forbid Zero Length Activations
```

**Multi-concern — body names each behavioral concern:**
```
SHROCPP-2142 - Snapshot on Drop from Orchestration

* Add snapshot data when dropping from orchestration
* Migrate legacy methods from ActivationRepository to LegacyRepository
* Return inventoryOverride on all Launch Event responses
* Map APPROVED launch event status to null
* Preserve preheat and status override for new channels
```

**Infrastructure + cleanup — body names each concern:**
```
NOJIRA - Upgrade to SpringBoot 2.5.15

* Upgrade Spring Boot from 2.3.x to 2.5.15
* Remove AAA auth configuration
* Replace DatabaseConfig with JooqConfigurationCustomizer
```

**Build/test stability — body names what changed:**
```
NOJIRA - Improve Build Stability

* Add publish validation calls to all integration tests
* Update default activation IT data creation
* Update CVE threshold in twistlock rules
```
