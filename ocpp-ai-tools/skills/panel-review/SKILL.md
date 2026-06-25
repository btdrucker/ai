---
name: panel-review
description: Adversarial expert panel review for AI-generated artifacts. Role-plays antagonistic expert personas who assume output is AI slop, then iterates critique-and-fix rounds until two consecutive clean passes. Runs autonomously by default—no pause for panel approval or between rounds. Invoke only when explicitly requested by the user. Use when the user asks for a panel review, adversarial review, quality gauntlet, red-team review, or wants to stress-test the quality of technical output.
---

# Panel Review

On-demand adversarial review process. Role-played expert personas critique artifacts through structured rounds until quality converges.

## Process Overview

1. Scope -- identify artifact(s), domain, sensitivity
2. Assemble Panel -- select personas (or use user-specified count/roles), present roster, proceed autonomously
3. Critique -- each persona independently produces structured criticisms
4. Deliberate -- panel converges on legitimate criticisms (unanimity required)
5. Remediate -- address all agreed criticisms, summarize changes
6. Iterate -- repeat 3-5 with fresh eyes until two consecutive clean rounds
7. Close Out -- emit summary in chat

## Phase 1: Scope

Identify the artifact(s) under review and their domain. Assess sensitivity to calibrate panel size:

| Sensitivity | Panel Size | When |
|---|---|---|
| Routine | 3 | Low-stakes, informal, internal drafts |
| Important | 4-5 | Shared deliverables, presentations, production code |
| Critical | 5+ | Public-facing, security-sensitive, architectural decisions |

If the user provides job titles or persona descriptions, use those instead of selecting autonomously.

## Phase 2: Assemble Panel

Create expert personas. Each gets:

- **Name** (invented)
- **Title and domain of expertise**
- **Skepticism framing** -- one line explaining why they doubt AI output in this domain

All personas share this premise: they are anti-AI, assume the artifact is AI slop, and are eager to prove it. They are open to being proven wrong but start antagonistic.

**Phase-specific behavior:** During Phase 3 (critique), personas are fully antagonistic -- they look for every possible flaw. During Phase 4 (deliberation), personas switch to fair-arbiter mode -- they evaluate each criticism on its merits and are willing to discard criticisms they find unfounded, including their own.

### Persona Selection Heuristics

Always include at minimum:

- A **domain/subject-matter expert** for the artifact's field
- A **clarity/readability reviewer** (technical writing lens)
- A **structural/process thinker** (architecture, flow, completeness)

Add specialists as the domain demands (e.g., security reviewer for auth code, accessibility expert for UI work).

### Prompt Engineer Guidance

The person invoking the panel review should specify **number of reviewers** and/or **specific personas** when that matters to them. If they do not specify, the agent selects autonomously from the heuristics above.

### Panel Assembly Checkpoint

Present the panel roster as a table before starting Round 1. **Proceed autonomously** to Round 1 without pausing for approval. Only pause if the user explicitly asks to approve, adjust, or confirm the roster before continuing.

## Phase 3: Individual Critique (Round N)

Each persona independently reviews the artifact and produces criticisms. Present each persona's criticisms under their name as a heading.

Every criticism must include:

| Field | Required Content |
|---|---|
| **Category** | correctness, clarity, completeness, style, or domain-specific |
| **Severity** | critical, moderate, or minor |
| **Location** | section heading, line number, slide number, passage quote, or equivalent positional reference |
| **Description** | explicit explanation of the issue and why it matters |

No vague feedback. "Could be better" is not a criticism. Cite what is wrong and why.

## Phase 4: Panel Deliberation (Round N)

Simulate a structured group discussion. For each criticism from Phase 3:

1. Each persona states **agree** or **disagree** with a one-sentence rationale
2. If all panelists agree the criticism is legitimate, it survives
3. If even one panelist disagrees, the criticism is discarded -- note the dissent reasoning briefly

Output: a numbered list of agreed-upon criticisms with category, severity, and location.

## Phase 5: Remediation (Round N)

Address every agreed-upon criticism, regardless of severity. For each criticism:

- Apply the fix to the artifact in place
- Record a one-line summary mapping the criticism number to what changed

### Round Transition

After remediation, briefly note round number, criticisms addressed, and artifact state. **Proceed autonomously** to the next round without asking. Do not pause for user approval between rounds. Continue until termination (two consecutive clean rounds) or the safety cap. Only pause if the user explicitly asks to stop, redirect focus, or approve before continuing.

## Phase 6: Iterate

A **round** is one complete cycle of Phase 3 (critique) + Phase 4 (deliberation) + Phase 5 (remediation).

Repeat from Phase 3 with fresh-eyes discipline:

- If the artifact is a file, re-read the current version from disk
- Base critique solely on the current artifact text
- Do **not** reference or re-litigate criticisms, fixes, or discussions from prior rounds

### Termination

Two consecutive rounds where Phase 4 deliberation produces **zero agreed-upon criticisms**.

### Safety Cap

Maximum **5 rounds** by default. The user may override this cap at any time.

If the cap is hit before termination:

1. Summarize all remaining open concerns
2. Present them to the user for disposition
3. Proceed to Close Out

## Phase 7: Close Out

Emit a summary **in chat only**. Do not create any files for this summary.

Template:

    ## Panel Review Complete

    - **Rounds:** N
    - **Criticisms per round:** [R1: X, R2: Y, ...]
    - **Total criticisms addressed:** N
    - **Final verdict:** [Clean / Capped with N remaining concerns]
    - **Remaining concerns (if capped):** [list]

## Constraints

**No new files.** The panel reviews and remediates existing artifacts in place. All deliberation, critique, and summary output lives in the chat. Create new files only if the user explicitly requests them.

**Context management.** After each round, compress that round's critique, deliberation, and remediation into a compact log -- one line per criticism with its number, category, and disposition. When referencing the artifact, always re-read the current version from disk rather than relying on versions quoted earlier in the conversation.

**Concise critiques.** The structured fields (category, severity, location, description) enforce brevity. Personas produce focused criticisms, not essays.
