# Invocation Examples

## Audit only, targeted files

`Use enforce-compose-state-callback-contract on ShopCarousel.kt and LargeCarousel.kt. Scope A. Audit only.`

## Audit then apply for module

`Use enforce-compose-state-callback-contract for the shop-carousel module. Scope B. Show findings first, then apply after my approval.`

## Diff-first expansion

`Use enforce-compose-state-callback-contract. Scope D (start from current diff). Expand only if call chain requires it.`

# Expected Audit Output Example

## Findings
- Must-fix: state and callbacks mixed in composable signature.
- Should-fix: repeated threading of 7+ params across two layers.
- Acceptable: domain providers kept separate from UI contract.

## Proposed split
- `XxxUiState`: immutable snapshot rendering/effect values.
- `XxxCallbacks`: event lambdas and side-effect intents.
- `XxxContract`: top-level wrapper passed through intermediates.

## Stability check
- `XxxUiState` uses `@Immutable`.
- `XxxCallbacks` uses `@Stable` and is created with `remember(controller)`.
- No mutable collections in immutable state objects.

## Detekt check
- `./gradlew detekt` passed with no new violations.
- (or) 2 new violations found — both fixed inline. See refactor report.

# Exceptions (Pragmatic Mode)

Allow exceptions only with explicit rationale:
- Callback intentionally kept separate for readability at public API boundary.
- Value excluded from grouped state because it belongs to unrelated domain dependency.
