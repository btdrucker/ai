---
name: enforce-compose-state-callback-contract
description: Enforces Jetpack Compose parameter contracts by separating immutable UI state from stable callback/event groups, reducing threaded params, and preserving recomposition stability. Use when composables have long parameter lists, mixed state and lambdas, hoisted featured-flow controls, or when asked to standardize composable APIs.
---

# Enforce Compose State/Callback Contract

## Purpose

Apply a consistent composable API pattern:
- immutable snapshot state in one object
- callbacks/events in a separate stable object
- optional top-level contract wrapper to reduce parameter threading

Default behavior:
1. Audit first
2. Present findings + proposed split
3. Apply refactor only after approval

## Required Scope Prompt (every run)

Before scanning, ask the user to choose one scope:
- **A**: only explicitly provided files
- **B**: current module + direct call chain
- **C**: whole repo
- **D**: start from current diff and expand outward only if needed

Do not assume scope when not specified.

## Decision Rules

For each parameter in a composable:

1. **Put in UI state object** if it is a snapshot value used for rendering or effect keys:
   - enums, booleans, ints, floats, strings
   - immutable value objects
   - derived flags

2. **Put in callbacks object** if it is behavior/event output:
   - lambdas like `onPageChanged`, `onVisibilityChanged`, `consumeX`, `setX`

3. **Keep separate** (not in state/callback bundle) when it is unrelated domain dependency:
   - providers, routers, navigation handlers, design providers, data lists, card payloads
   - unless user explicitly wants broader grouping

4. **Keep local** if truly internal UI state:
   - `remember`/`mutableStateOf` values not meant to be hoisted

## Stability Rules

1. UI state object:
   - use `@Immutable` data class
   - no mutable collections inside; avoid `MutableList`/`MutableMap`
   - no lambdas inside

2. Callbacks object:
   - use `@Stable` class when it stores lambdas
   - create once with `remember(owner)` at boundary layer to avoid churn

3. Optional wrapper object:
   - use `@Stable` data class combining `state + callbacks`
   - pass wrapper as one param through call chain

4. Effect safety:
   - if callback capture freshness matters in `LaunchedEffect`, use `rememberUpdatedState`

## Refactor Workflow

1. Inventory composables with mixed state + callbacks.
2. Build a parameter table: `name -> usage -> classification`.
3. Propose split and call out edge cases/exceptions.
4. After approval, implement:
   - add contract types
   - update signatures and call sites
   - keep external public API stable unless requested
5. Validate:
   - lint on touched files
   - targeted compile if environment allows
6. Report:
   - findings first
   - what changed
   - assumptions and impact

## Detekt Verification

After applying any refactor, run detekt on the affected modules:

```bash
./gradlew detekt
```

Triage the results:
- **Fix** violations that are directly caused by or related to changes made during this refactor (e.g. new naming issues, complexity increases, missing annotations).
- **Ignore** pre-existing violations unrelated to the refactor.
- If new violations cannot be reasonably fixed without altering intent (e.g. a rule disagrees with the contract pattern itself), **suggest regenerating the detekt baseline** by telling the user to run:
  ```bash
  ./gradlew detektBaseline
  ```
  Explain which violations would be baselined and why.

Do not silently suppress or baseline violations without surfacing them to the user first.

## Output Contract For This Skill

When reporting audit results, use this order:
1. **Findings** (must-fix, should-fix, acceptable)
2. **Proposed split** (state vs callbacks vs keep separate)
3. **Stability risks** (if any)
4. **Refactor plan**
5. **Detekt status** (pass / violations found with triage)
6. **Assumptions + impact**

## Quick Classification Example

Given:
- `autoAdvanceState`, `autoAdvanceProgress`, `autoAdvanceIndex`, `showPlayBar`, `isAutoAdvancing`
- `onVisibilityChanged`, `onPageChanged`, `consumeAutoAdvance`, `setReducedMotion`

Classification:
- state object: first five
- callbacks object: last four
- pass single contract object through intermediate composables

## Additional Resources

- Invocation and output examples: [examples.md](examples.md)
