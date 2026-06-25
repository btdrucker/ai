#!/usr/bin/env bash
set -euo pipefail

MAMBA_REPO="$(cd "$(dirname "$0")/.." && pwd)"

show_help() {
    cat <<'HELP'
setup-worktree.sh — Create a git worktree for a Jira ticket branch.

Creates an isolated working directory so multiple agents can work on
different tickets in parallel without interfering with each other.

The script will:
  1. Fetch the latest from origin.
  2. Create a new branch named <prefix>/<ticket-id> based on origin/main.
  3. Place the worktree in a sibling directory:
       <repo-dir>--<sanitized-branch>
  4. Print the worktree path on success.

If the worktree or branch already exists it will reuse them.

Usage:
  setup-worktree.sh --ticket <TICKET-ID> [--prefix <prefix>] [--base <ref>]

Options:
  --ticket   Jira ticket id (e.g. MMBA-1234). Used as the branch suffix.
  --prefix   Branch prefix (default: $USER). Branch will be <prefix>/<ticket-id>.
  --base     Base ref to branch from (default: origin/main).
  -h, --help Show this help message and exit.

Examples:
  setup-worktree.sh --ticket MMBA-1234
  setup-worktree.sh --ticket MMBA-5678 --prefix jdoe --base origin/develop
HELP
}

ticket=""
prefix="${USER:-$(whoami)}"
base_ref="origin/main"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ticket)
            [[ $# -lt 2 ]] && { echo "Error: --ticket requires a value"; exit 1; }
            ticket="$2"; shift 2 ;;
        --prefix)
            [[ $# -lt 2 ]] && { echo "Error: --prefix requires a value"; exit 1; }
            prefix="$2"; shift 2 ;;
        --base)
            [[ $# -lt 2 ]] && { echo "Error: --base requires a value"; exit 1; }
            base_ref="$2"; shift 2 ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

if [[ -z "$ticket" ]]; then
    echo "Error: --ticket is required"
    show_help
    exit 1
fi

branch="$prefix/$ticket"
sanitized=$(echo "$branch" | tr '/' '-')
worktree_path="$(dirname "$MAMBA_REPO")/$(basename "$MAMBA_REPO")--${sanitized}"

echo "=== Worktree setup for $ticket ==="
echo "Repo:     $MAMBA_REPO"
echo "Branch:   $branch"
echo "Worktree: $worktree_path"
echo ""

echo "Fetching origin..."
git -C "$MAMBA_REPO" fetch origin --quiet

# Check if worktree path already exists and is valid
if [[ -d "$worktree_path" ]]; then
    if git -C "$worktree_path" rev-parse --is-inside-work-tree &>/dev/null; then
        current=$(git -C "$worktree_path" branch --show-current)
        if [[ "$current" == "$branch" ]]; then
            echo "Worktree already exists on branch $branch — reusing."
            echo "$worktree_path"
            exit 0
        else
            echo "Error: $worktree_path exists but is on branch $current, not $branch"
            exit 1
        fi
    else
        echo "Error: $worktree_path exists but is not a valid git worktree"
        exit 1
    fi
fi

# Check if branch already exists locally
if git -C "$MAMBA_REPO" show-ref --verify --quiet "refs/heads/$branch" 2>/dev/null; then
    echo "Local branch $branch exists — creating worktree..."
    git -C "$MAMBA_REPO" worktree add "$worktree_path" "$branch"
# Check if branch exists on remote
elif git -C "$MAMBA_REPO" show-ref --verify --quiet "refs/remotes/origin/$branch" 2>/dev/null; then
    echo "Remote branch origin/$branch exists — creating tracked worktree..."
    git -C "$MAMBA_REPO" worktree add --track -b "$branch" "$worktree_path" "origin/$branch"
else
    echo "Creating new branch $branch from $base_ref..."
    git -C "$MAMBA_REPO" worktree add -b "$branch" "$worktree_path" "$base_ref"
fi

# Symlink local.properties so Gradle can find the Android SDK
if [[ -f "$MAMBA_REPO/local.properties" && ! -f "$worktree_path/local.properties" ]]; then
    ln -sf "$MAMBA_REPO/local.properties" "$worktree_path/local.properties"
    echo "Symlinked local.properties from main repo."
fi

echo ""
echo "NOTE: If included builds (e.g. mpe.foundation.clickstream/Android) have their"
echo "own local.properties, copy them into the worktree so Gradle composite builds"
echo "can locate the Android SDK."
echo ""
echo "Done. Worktree ready at:"
echo "$worktree_path"
