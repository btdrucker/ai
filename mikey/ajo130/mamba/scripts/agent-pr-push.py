#!/usr/bin/env python3
"""Agent-friendly Mamba PR push orchestration.

This script owns the repeatable pre-push workflow so agents do not have to
choose Gradle tasks, parse brittle shell output, or decide when it is safe to
push. It prints a single JSON document to stdout and writes logs/results under
_pra-results/.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from agent_pr_common import (
    CHINA_LINT_EXCLUDES,
    AgentPrError,
    CommandResult,
    category_from_gradle_task,
    ensure_mamba_repo,
    eprint,
    iso_now,
    now_id,
    output_dir,
    repo_lock,
    repo_root,
    run_capture,
    run_logged,
)


GRADLE_OPTS = ["--parallel", "--build-cache", "--continue"]
FAILED_TASK_PATTERNS = [
    re.compile(r"^> Task (?P<task>\S+) FAILED"),
    re.compile(r"Execution failed for task '(?P<task>[^']+)'"),
]


@dataclass(frozen=True)
class Stage:
    name: str
    description: str
    tasks: list[str]


DEFAULT_STAGES = [
    Stage(
        name="push_safety",
        description="Push safety checks",
        tasks=[
            "spotlessCheck",
            "detekt",
            "apiCheck",
            "checkSortDependencies",
            "lint",
            *CHINA_LINT_EXCLUDES,
        ],
    )
]

FULL_PRA_STAGES = [
    Stage(
        name="static",
        description="Static checks",
        tasks=[
            "spotlessCheck",
            "checkSortDependencies",
            "apiCheck",
            "detekt",
            ":nike-gradle-plugin:spotlessCheck",
            "buildHealth",
        ],
    ),
    Stage(
        name="lint",
        description="Android lint",
        tasks=["lint", *CHINA_LINT_EXCLUDES],
    ),
    Stage(
        name="unit_tests",
        description="Unit tests and coverage",
        tasks=[
            "test",
            "jacocoCoverage",
            "-x",
            ":app:testChinaDebugUnitTest",
            "-x",
            ":app:testChinaReleaseUnitTest",
        ],
    ),
    Stage(
        name="assemble",
        description="Assemble APKs",
        tasks=["assembleWorld"],
    ),
]


def current_branch(root: Path) -> str:
    result = run_capture(["git", "branch", "--show-current"], root, check=True)
    branch = result.stdout.strip()
    if not branch:
        raise AgentPrError("Current checkout is detached; refusing to push.")
    return branch


def run_gradle_stage(
    stage: Stage,
    root: Path,
    out_dir: Path,
    stamp: str,
    dry_run: bool,
    test_mode: bool,
    simulated_failure: str | None,
) -> CommandResult:
    command = ["./gradlew", *GRADLE_OPTS, *stage.tasks]
    log_file = out_dir / f"agent-pr-push-{stamp}-{stage.name}.log"
    if dry_run or test_mode:
        label = "TEST MODE" if test_mode else "DRY RUN"
        lines = [f"{label}: {shlex.join(command)}"]
        exit_code = 0
        if simulated_failure:
            lines.extend(
                [
                    "",
                    f"> Task {simulated_failure} FAILED",
                    f"Execution failed for task '{simulated_failure}'.",
                    f"{label}: simulated failure for agent workflow testing.",
                ]
            )
            exit_code = 1
        log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return CommandResult(command=command, exit_code=exit_code, log_file=str(log_file))
    eprint(f"\n== {stage.description} ==")
    return run_logged(command, root, log_file)


def report_hint(category: str) -> str | None:
    return {
        "detekt": "build/reports/detekt/detekt.xml",
        "lint": "build/reports/lint-results-*.html",
        "build_health": "build/reports/dependency-analysis/build-health-report.txt",
        "unit_tests": "build/reports/tests/",
    }.get(category)


def error_excerpt(log_file: Path, max_lines: int = 40) -> list[str]:
    if not log_file.exists():
        return []
    interesting = re.compile(r"(FAILED|FAILURE|ERROR|error:|Exception|Execution failed)")
    lines: list[str] = []
    with log_file.open(encoding="utf-8", errors="replace") as log:
        for line in log:
            stripped = line.rstrip("\n")
            if interesting.search(stripped):
                lines.append(stripped)
            if len(lines) >= max_lines:
                break
    return lines


def parse_failed_tasks(results: list[tuple[Stage, CommandResult]]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    seen: set[tuple[str, str | None, str]] = set()

    for stage, result in results:
        log_path = Path(result.log_file)
        found_tasks: list[str | None] = []
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                for pattern in FAILED_TASK_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        found_tasks.append(match.group("task"))

        if result.exit_code != 0 and not found_tasks:
            found_tasks.append(None)

        for task in found_tasks:
            category = category_from_gradle_task(task)
            key = (stage.name, task, category)
            if key in seen:
                continue
            seen.add(key)
            rerun_arg = task or category
            failures.append(
                {
                    "id": category,
                    "task": task,
                    "stage": stage.name,
                    "log_file": str(log_path),
                    "rerun_command": f"python3 scripts/agent-rerun-failed-task.py {shlex.quote(rerun_arg)}",
                    "report_hint": report_hint(category),
                    "error_excerpt": error_excerpt(log_path),
                }
            )

    return failures


def git_dirty(root: Path) -> list[str]:
    result = run_capture(["git", "status", "--porcelain"], root, check=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def git_push(root: Path, out_dir: Path, stamp: str, remote: str, no_verify: bool) -> CommandResult:
    command = ["git", "push", "-u", remote, "HEAD"]
    if no_verify:
        command.append("--no-verify")
    return run_logged(command, root, out_dir / f"agent-pr-push-{stamp}-git-push.log")


def create_or_view_pr(
    root: Path,
    out_dir: Path,
    stamp: str,
    base: str,
    title: str | None,
    body: str | None,
) -> tuple[str | None, CommandResult]:
    view = run_capture(["gh", "pr", "view", "--json", "url", "--jq", ".url"], root)
    if view.returncode == 0 and view.stdout.strip():
        return view.stdout.strip(), CommandResult(
            command=["gh", "pr", "view", "--json", "url", "--jq", ".url"],
            exit_code=0,
            log_file="",
        )

    command = ["gh", "pr", "create", "--base", base]
    if title is not None:
        command.extend(["--title", title])
    if body is not None:
        command.extend(["--body", body])
    elif title is not None:
        command.extend(["--body", ""])
    if title is None:
        command.append("--fill")

    result = run_logged(command, root, out_dir / f"agent-pr-push-{stamp}-gh-pr-create.log")
    pr_url: str | None = None
    if result.exit_code == 0:
        log_text = Path(result.log_file).read_text(encoding="utf-8", errors="replace")
        urls = re.findall(r"https://\S+", log_text)
        pr_url = urls[-1] if urls else None
    return pr_url, result


def write_result(out_dir: Path, stamp: str, payload: dict[str, object]) -> Path:
    result_file = out_dir / f"agent-pr-push-result-{stamp}.json"
    payload["result_file"] = str(result_file)
    result_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Mamba Android agent-owned pre-push checks, then push/open a PR when green."
    )
    parser.add_argument("--check-only", action="store_true", help="Run checks and emit JSON without pushing.")
    parser.add_argument("--dry-run", action="store_true", help="Emit the planned commands without running them.")
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Exercise the workflow without running Gradle, git push, or gh. Implies --check-only.",
    )
    parser.add_argument(
        "--simulate-failure",
        help="With --test-mode, simulate a failed Gradle task such as ':discover:impl:apiCheck'.",
    )
    parser.add_argument("--full-pra", action="store_true", help="Run the slower CI-like PRA lane.")
    parser.add_argument("--create-pr", action="store_true", help="Create or show a GitHub PR after a successful push.")
    parser.add_argument("--base", default="main", help="Base branch for PR creation. Default: main.")
    parser.add_argument("--remote", default="origin", help="Git remote to push to. Default: origin.")
    parser.add_argument("--pr-title", help="PR title. If omitted with --create-pr, gh --fill is used.")
    parser.add_argument("--pr-body", help="PR body. If omitted with --create-pr, gh --fill is used.")
    parser.add_argument("--no-verify", action="store_true", help="Pass --no-verify to git push. Use only when explicit.")
    parser.add_argument("--allow-main", action="store_true", help="Allow pushing from main/master.")
    parser.add_argument("--no-lock", action="store_true", help="Skip the repo-local lock.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ensure_mamba_repo(root)
    out_dir = output_dir(root)
    stamp = now_id()
    branch = current_branch(root)
    stages = FULL_PRA_STAGES if args.full_pra else DEFAULT_STAGES
    check_only = args.check_only or args.test_mode

    if args.simulate_failure and not args.test_mode:
        raise AgentPrError("--simulate-failure can only be used with --test-mode.")

    if branch in {"main", "master"} and not args.allow_main and not check_only:
        raise AgentPrError("Refusing to push main/master. Pass --allow-main only if this is intentional.")

    with repo_lock(
        out_dir,
        lock_rel="agent-pr-push.lock",
        blocked_message="Another agent PR push/check run is already active.",
        disabled=args.no_lock or args.dry_run or args.test_mode,
    ):
        stage_results: list[tuple[Stage, CommandResult]] = []
        for index, stage in enumerate(stages):
            simulated_failure = args.simulate_failure if args.test_mode and index == 0 else None
            result = run_gradle_stage(
                stage=stage,
                root=root,
                out_dir=out_dir,
                stamp=stamp,
                dry_run=args.dry_run,
                test_mode=args.test_mode,
                simulated_failure=simulated_failure,
            )
            stage_results.append((stage, result))

        failed_tasks = parse_failed_tasks(stage_results)
        checks_passed = all(result.exit_code == 0 for _, result in stage_results)
        dirty_files: list[str] = []
        push_result: CommandResult | None = None
        pr_result: CommandResult | None = None
        pr_url: str | None = None
        pushed = False

        if checks_passed and not check_only and not args.dry_run and not args.test_mode:
            dirty_files = git_dirty(root)
            if not dirty_files:
                push_result = git_push(root, out_dir, stamp, args.remote, args.no_verify)
                pushed = push_result.exit_code == 0
                if pushed and args.create_pr:
                    pr_url, pr_result = create_or_view_pr(
                        root=root,
                        out_dir=out_dir,
                        stamp=stamp,
                        base=args.base,
                        title=args.pr_title,
                        body=args.pr_body,
                    )

        overall_success = checks_passed and (
            check_only
            or args.dry_run
            or args.test_mode
            or (pushed and (not args.create_pr or (pr_result is None or pr_result.exit_code == 0)))
        )
        if dirty_files:
            overall_success = False

        payload: dict[str, object] = {
            "schema_version": 1,
            "timestamp": iso_now(),
            "repo_root": str(root),
            "branch": branch,
            "mode": "full_pra" if args.full_pra else "push_safety",
            "check_only": check_only,
            "dry_run": args.dry_run,
            "test_mode": args.test_mode,
            "simulated_failure": args.simulate_failure,
            "overall_success": overall_success,
            "checks_passed": checks_passed,
            "pushed": pushed,
            "pr_url": pr_url,
            "stages": [
                {
                    "name": stage.name,
                    "description": stage.description,
                    "command": shlex.join(result.command),
                    "exit_code": result.exit_code,
                    "log_file": result.log_file,
                }
                for stage, result in stage_results
            ],
            "failed_tasks": failed_tasks,
            "dirty_files": dirty_files,
            "push": None
            if push_result is None
            else {
                "command": shlex.join(push_result.command),
                "exit_code": push_result.exit_code,
                "log_file": push_result.log_file,
            },
            "next_action": "done",
        }

        if failed_tasks:
            payload["next_action"] = "Run the rerun_command for the first failed task, fix code if needed, then rerun this script."
        elif dirty_files:
            payload["next_action"] = "Commit or discard dirty files before pushing, then rerun this script."
        elif checks_passed and args.test_mode:
            payload["next_action"] = "Test mode passed. Rerun without --test-mode to execute checks and push."
        elif checks_passed and check_only:
            payload["next_action"] = "Checks passed. Rerun without --check-only to push."
        elif push_result and push_result.exit_code != 0:
            payload["next_action"] = "Read the git push log and fix the push failure."
            payload["overall_success"] = False
        elif pr_result and pr_result.exit_code != 0:
            payload["next_action"] = "Read the gh pr create log and fix the PR creation failure."
            payload["overall_success"] = False

        result_file = write_result(out_dir, stamp, payload)
        print(result_file.read_text(encoding="utf-8"), end="")
        return 0 if payload["overall_success"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AgentPrError as error:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "timestamp": iso_now(),
                    "overall_success": False,
                    "error": str(error),
                    "next_action": "Resolve the script error and rerun.",
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(1)
