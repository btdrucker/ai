---
name: humanize-text
description: Identify and remove AI-generated writing patterns from text. Use when the user explicitly asks to humanize, de-AI, clean up, or remove AI patterns from text. Do not activate for general editing, proofreading, or review tasks unless the user specifically requests humanization.
---

# Humanize Text

Remove detectable AI writing patterns from text while preserving meaning, accuracy, and the document's existing register.

## When to use

- User explicitly asks to "humanize," "de-AI," or "clean up" text
- User asks to remove AI patterns or make text sound more natural
- Post-drafting cleanup when the user flags content as AI-generated

## When NOT to use

- General editing or proofreading (use standard editing judgment)
- Rewriting text in a specific person's voice (use a voice/style skill if available)
- Content that was human-written and the user just wants reviewed

## Process

1. Read the target text. If no significant AI-pattern clusters are present, report that the text is clean and stop. Do not invent problems.
2. Identify the document type (investigation report, reference doc, architecture overview, wiki page, decision document, etc.). This determines which patterns apply and what register to maintain. See the document-type matrix in [references/patterns.md](references/patterns.md). If the document doesn't match a listed type, pick the closest row and note any deviations in register or formatting expectations.
3. Read [references/patterns.md](references/patterns.md) for severity tiers, the full pattern catalog, and before/after examples.
4. Fix high-severity patterns first (see "Always fix" in patterns.md § Severity and Priority): chatbot artifacts, filler phrases, sycophantic tone, knowledge-cutoff disclaimers, generic conclusions. These are never acceptable in published text.
5. Fix medium-severity patterns (see "Fix when you see them" in the same section): AI vocabulary clusters, inflated significance, -ing padding, vague attributions, copula avoidance, synonym cycling, excessive hedging.
6. Check low-severity patterns by density, not by instance. One em dash or one "robust" is normal English. Three or more distinct patterns co-occurring within a two-paragraph span is a cluster. The signal is concentration, not individual words.
7. Apply structural patterns per document type. Reference docs keep consistent formatting and precise counts. Investigation reports use first person and express genuine uncertainty. Do not apply prose fixes to structured data.
8. Rewrite problematic sections. Preserve meaning. Match the document's register.
9. Never fabricate specifics. When removing vague claims, cut them or describe the evidence honestly. Do not invent sources, people, or statistics.
10. Self-review before returning:
    - Did you over-correct? (Stripped useful structure, made a technical doc casual, rewrote clean prose unnecessarily)
    - Did you introduce new problems? (Fabricated sources, changed meaning, lost precision)
    - Did you match the document type? (First person in a field mapping is wrong; third person in a team analysis is wrong)
    - Is the result clearer than the original, or just different?
11. Return the rewritten text with a brief summary of what changed. Reference pattern numbers from the catalog.

## Diminishing returns

After the first pass removes obvious clusters, subsequent passes yield less. If the second pass finds only isolated low-severity instances, report the text as clean, note any remaining isolated patterns without fixing them, and stop. Chasing every em dash or single "Additionally" past the cluster threshold produces text that reads over-edited -- which is its own tell.

## Scope

This skill removes AI patterns. It does not apply any personal voice or style. The output should read like clean, professional prose in whatever register the document already uses.

## Principles

- Fix by density, not by instance. One pattern is English; a cluster is AI.
- High-severity patterns are always wrong. Low-severity patterns are judgment calls.
- First person is for authored analysis, not reference docs.
- Express uncertainty only where it's genuine, not for flavor.
- In structured references, consistent formatting and precise counts are correct.
- Never manufacture personality. Fake casual is as detectable as fake formal.
- When in doubt, leave it. Clarity beats style.
