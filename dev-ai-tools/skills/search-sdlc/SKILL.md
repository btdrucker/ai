---
name: search-sdlc
description: >
  Search Engineering SDLC process guide -- branching strategy, PR workflow,
  CI/CD pipeline, environments, Jira lifecycle, and development guardrails.
  Use when the user is planning work on a project, asking about the team's
  development process, creating branches, preparing for deployment, or needs
  guidance on the SDLC workflow.
---

# Search Engineering SDLC

## Related skills

- **`github`** -- PR creation, code review, and branching patterns via `gh` CLI
- **`jira`** -- Jira ticket transitions and story lookups
- **`confluence`** -- Confluence page lookups

## Spec-driven development (optional)

For non-trivial stories, the team can use the `openspec` skill to plan before
coding. OpenSpec guides the developer through:

1. **Explore** -- research the problem space and gather context
2. **Propose** -- create a lightweight proposal outlining the approach
3. **Design / Spec** -- generate detailed design and specification artifacts
4. **Tasks** -- break the spec into implementable tasks

When a story uses OpenSpec, the SDLC flow becomes:

```
In Definition (+ OpenSpec explore/propose/design) -> Dev (+ OpenSpec apply) -> Pull Request (+ OpenSpec archive) -> QA -> Deploy Ready -> Done
```

Spec-driven development is optional. It tends to be most useful for complex
changes, multi-service work, or stories with significant design decisions, but
the developer can choose to use it for any story.

**Avoiding spec drift:** If OpenSpec artifacts exist for a story but
implementation proceeds without consulting them, the spec and code can diverge.
When this happens, update the spec to reflect reality before archiving:

1. Review the delta between the spec and what was actually implemented.
2. Update the spec's delta markers (ADDED/MODIFIED/REMOVED) to match the
   final implementation.
3. Archive the change only after the spec accurately reflects what shipped.

Changes should go through the spec first whenever possible -- update the spec,
then implement. If the implementation diverged out of necessity, reconcile the
spec before the story is considered done.

## Branching strategy

**Model:** Trunk-based development. Short-lived feature branches are created from
the default branch and merged back quickly via pull request.

**Default branch:** `main` for newer repos, `master` for some legacy repos. Always
check the repo's default branch before creating a feature branch -- never assume.

**Branch naming:** `<type>/JIRA-ID-short-description`

| Prefix | Use for |
|--------|---------|
| `feature/` | New features and enhancements |
| `bugfix/` | Bug fixes |

Examples: `feature/SRPLT-1234-add-typeahead-cache`, `bugfix/SRPLT-5678-fix-null-response`

**Branch protection** (default branch):

- Direct push is blocked -- all changes go through a PR.
- Minimum 2 approvals required before merge.
- CI checks must pass before merge.

**Merge strategy:** Squash and merge. This keeps the default branch history clean
with one commit per PR.

**Cleanup:** Branches are auto-deleted after merge.

## PR and code review process

**PR size:** Keep PRs small and focused on a single concern. Large changes
should be split into a stack of incremental PRs when possible.

**PR description:** Use the `pr-create` skill, which auto-generates a structured
description (Summary + Changes) from the commits and diff. Do not freestyle PR
creation -- always defer to the skill for consistent formatting.

**Reviews:** PRs require 2 approvals and passing CI before merge. Reviews are
thorough -- reviewers check logic, tests, style, and documentation.

**Merge:** Squash and merge (see Branching strategy). After merge, the branch
is auto-deleted.

**Re-review:** Request re-review after addressing feedback rather than merging
with unresolved threads.

**OpenSpec completion:** If the story used spec-driven development (OpenSpec),
verify that any associated artifacts (proposals, specs, designs) are in a
completed state before creating the final PR. For incremental PRs that are part
of a larger story, spec documents can be in any state.

**Slack notification (manual):** After creating a PR, post to
`#search-platform-squad` with a link to the PR, the Jira ticket, and a brief
summary highlighting any caveats, risks, or areas that need extra review
attention. The agent cannot post to Slack directly -- remind the user to do this
after PR creation.

**Agent skills for PR workflow:**

- `pr-create` -- generates the PR with a structured description from commits and
  diff. Always use this instead of hand-crafting `gh pr create` commands.
- `pr-review` -- performs structured code review on a PR. Supports two modes:
  *PR mode* (posts comments to GitHub) and *pre-review mode* (analyzes a local
  diff before the PR is created). Findings are presented for user approval
  before anything is posted.
- `pr-address-comments` -- fetches unresolved review comments on a PR, analyzes
  their validity, presents recommendations, implements accepted changes, replies
  to threads, and resolves addressed threads. Use after receiving review feedback.

## CI/CD pipeline

**Tool:** Jenkins. Pipeline configuration lives in a `Jenkinsfile` at the repo
root.

**CI triggers:** Builds run on PR creation and updates. Some pipelines also
trigger automatically on merge to the default branch -- this varies by repo and
pipeline configuration.

**GitHub PR checks** (varies per repo, Envoy shown as representative example):

| Check | Tool | What it does |
|-------|------|-------------|
| `continuous-integration/jenkins/pr-merge` | Jenkins | Full build + test pipeline |
| `QMA Candidate` | QMA | Quality metrics aggregation gate |
| `build - Junit` | JUnit | Unit tests |
| `build - IntegrationTest` | JUnit | Integration tests |
| `build - Checkstyle` | Checkstyle | Code style enforcement |
| `build - FindBugs` | FindBugs | Static bug detection |
| `build - PMD` | PMD | Static analysis |
| `build - Jacoco` | JaCoCo | Code coverage |
| `securecode-static scan` | SecureCode | SAST (static application security) |
| `securecode-secret scan` | SecureCode | Secret detection |
| `securecode-iac scan` | SecureCode | Infrastructure-as-code security |

Not every repo will have all of these. Check `gh pr checks` on a given PR to
see the actual set.

**Deployments:** Triggered via manual Jenkins jobs (build with parameters) or
automatically on merge, depending on the pipeline configuration. Check each
repo's `Jenkinsfile` for its specific deploy behavior.

## Environments and promotion flow

**Environments:** `test` and `prod`. Some services may have additional
environments -- check each repo's `Jenkinsfile` `deploymentEnvironment` block
for the definitive list.

**Promotion:** A mix of automatic and manual gates depending on the pipeline
configuration. Some services auto-deploy to test on merge; others require a
manual Jenkins job. Promotion to prod is typically a manual Jenkins job with
parameters.

**Deployment model:** Blue-green EC2 deployments via the `ec2BlueGreenDeployPipeline`
shared library. Some services use canary referees for automated rollback
decisions.

**Feature flags:** Used sometimes for gating features across environments.

## Release and versioning

**Versioning:** Varies by repo. Check the repo's build config (`build.gradle`,
`gradle.properties`, `pom.xml`, `VERSION`, etc.) for how versions are managed.
Some repos auto-increment versions in CI; others manage them manually.

**Releases:** No single release process across the team. Deploying to prod
effectively constitutes a release. Check each repo for whether it uses Git tags,
GitHub Releases, or treats the Jenkins prod deploy as the release artifact.

## Jira workflow

**Project:** SRPLT

**Sprint cadence:** 2-week sprints.

**Story lifecycle:**

```
In Definition -> Dev -> Pull Request -> QA -> Deploy Ready -> Done
```

Any status can move to **Blocked** and back when an impediment arises.
Stories can also be **Cancelled** from any status.

**Branch-to-ticket linkage:** The Jira ticket ID is embedded in the branch name
(e.g., `feature/SRPLT-1234-add-cache`). The `pr-create` skill auto-detects the
ticket ID from the branch name and includes it in the PR description.

**Jira ticket management:** At each phase of the SDLC, offer to transition the
Jira ticket to the corresponding status and add relevant comments. For example:

| SDLC phase | Jira transition | Comment to add |
|------------|----------------|----------------|
| Start working on a story | -> Dev | |
| Create a PR | -> Pull Request | Link to the PR |
| PR approved / ready for QA | -> QA | |
| Verified in test | -> Deploy Ready | |
| Deployed to prod | -> Done | |
| Impediment encountered | -> Blocked | Description of the blocker |

Always ask before transitioning -- never auto-transition without user
confirmation.

## Development guardrails

- **No force push.** Never force push to any branch.
- **No amending pushed commits.** Never amend commits that have been pushed.
- **Warn before destructive git operations.** Always warn the user before
  running any destructive git operation (e.g., `git reset --hard`,
  `git clean -fd`, rebasing published branches).
- **No silent workspace modifications.** Never modify the IDE workspace
  without explicit user confirmation. When workspace changes may cause the
  IDE to reload, warn the user about potential context loss.
