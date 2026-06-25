#!/bin/bash
# sessionStart hook: silently pull latest dev-ai-tools from origin/main.
# Runs once per session, fire-and-forget. Failures are silent.

input=$(cat)

ai_tools_path=""
while IFS= read -r root; do
  if [[ "$root" == *"dev-ai-tools"* ]] && [ -d "$root/.git" ]; then
    ai_tools_path="$root"
    break
  fi
  candidate="$root/../search.tool.dev-ai-tools"
  if [ -d "$candidate/.git" ]; then
    ai_tools_path=$(cd "$candidate" && pwd)
    break
  fi
done < <(echo "$input" | jq -r '.workspace_roots[]? // empty' 2>/dev/null)

# Fallback: derive from script location
if [ -z "$ai_tools_path" ]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  candidate="$(cd "$script_dir/../.." && pwd)"
  if [ -d "$candidate/.git" ]; then
    ai_tools_path="$candidate"
  fi
fi

if [ -z "$ai_tools_path" ]; then
  echo '{}'
  exit 0
fi

git -C "$ai_tools_path" fetch origin --quiet 2>/dev/null

local_head=$(git -C "$ai_tools_path" rev-parse HEAD 2>/dev/null)
remote_head=$(git -C "$ai_tools_path" rev-parse origin/main 2>/dev/null)

if [ -z "$local_head" ] || [ -z "$remote_head" ]; then
  echo '{}'
  exit 0
fi

if [ "$local_head" != "$remote_head" ]; then
  if git -C "$ai_tools_path" pull --ff-only --quiet 2>/dev/null; then
    changelog=$(git -C "$ai_tools_path" log --oneline "$local_head..$remote_head" 2>/dev/null)
    if [ -n "$changelog" ]; then
      escaped=$(printf '%s' "$changelog" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "%s\\n", $0}' | sed 's/\\n$//')
      echo "{\"additional_context\": \"dev-ai-tools updated to latest origin/main. What's new since your last session:\\n${escaped}\"}"
    else
      echo '{"additional_context": "dev-ai-tools repo updated to latest origin/main."}'
    fi
  else
    echo '{"additional_context": "dev-ai-tools repo is behind origin/main but fast-forward failed. Consider pulling manually."}'
  fi
else
  echo '{}'
fi

exit 0
