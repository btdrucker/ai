#!/usr/bin/env python3
"""Rerun or auto-fix one Mamba PR-push failure.

Agents should pass the failed task id from scripts/agent-pr-push.py directly to
this script. The ordering rules live here, not in the agent prompt.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from agent_pr_common import (
    CHINA_LINT_EXCLUDES,
    AgentPrError,
    CommandResult,
    category_from_user_failure_arg,
    ensure_mamba_repo,
    eprint,
    iso_now,
    normalized_failure_arg,
    now_id,
    output_dir,
    repo_lock,
    repo_root,
    run_logged,
)


GRADLE_OPTS = ["--parallel", "--build-cache"]


@dataclass(frozen=True)
class Step:
    name: str
    description: str
    tasks: list[str]


def gradle_step(step: Step, root: Path, out_dir: Path, stamp: str, dry_run: bool, test_mode: bool) -> CommandResult:
    command = ["./gradlew", *GRADLE_OPTS, *step.tasks]
    log_file = out_dir / f"agent-rerun-{stamp}-{step.name}.log"
    if dry_run or test_mode:
        label = "TEST MODE" if test_mode else "DRY RUN"
        log_file.write_text(f"{label}: {shlex.join(command)}\n", encoding="utf-8")
        return CommandResult(command=command, exit_code=0, log_file=str(log_file))
    eprint(f"\n== {step.description} ==")
    return run_logged(command, root, log_file)


def module_prefix(task: str, task_name: str) -> str:
    suffix = f":{task_name}"
    if task.endswith(suffix):
        return task[: -len(suffix)]
    if task == task_name:
        return ""
    return ""


def scoped_task(prefix: str, task_name: str) -> str:
    return f"{prefix}:{task_name}" if prefix else task_name


def replacement_task(task: str, check_name: str, fix_name: str) -> str:
    prefix = module_prefix(task, check_name)
    return scoped_task(prefix, fix_name)


def task_or_default(value: str, default_task: str) -> str:
    if value.startswith(":") or value.endswith(default_task):
        return value
    return default_task


def build_steps(failure: str) -> tuple[str, list[Step], str | None]:
    value = normalized_failure_arg(failure)
    category = category_from_user_failure_arg(value)

    if category == "spotless":
        check_task = task_or_default(value, "spotlessCheck")
        fix_task = replacement_task(check_task, "spotlessCheck", "spotlessApply")
        return (
            category,
            [
                Step("spotless_apply", "Apply Spotless formatting", [fix_task]),
                Step("spotless_check", "Verify Spotless formatting", [check_task]),
            ],
            None,
        )

    if category == "api_check":
        check_task = value if value.startswith(":") else "apiCheck"
        if check_task.endswith(":kompare"):
            dump_task = replacement_task(check_task, "kompare", "apiDump")
        else:
            dump_task = replacement_task(check_task, "apiCheck", "apiDump")
        return (
            category,
            [
                Step("api_dump", "Update API dumps before checking API", [dump_task]),
                Step("api_check", "Verify API compatibility", [check_task]),
            ],
            None,
        )

    if category == "sort_dependencies":
        check_task = task_or_default(value, "checkSortDependencies")
        fix_task = replacement_task(check_task, "checkSortDependencies", "sortDependencies")
        return (
            category,
            [
                Step("sort_dependencies", "Sort Gradle dependencies", [fix_task]),
                Step("check_sort_dependencies", "Verify sorted Gradle dependencies", [check_task]),
            ],
            None,
        )

    if category == "detekt":
        task = task_or_default(value, "detekt")
        return category, [Step("detekt", "Rerun Detekt", [task])], "build/reports/detekt/detekt.xml"

    if category == "lint":
        task = value if value.startswith(":") else "lint"
        tasks = [task] if task.startswith(":") else [task, *CHINA_LINT_EXCLUDES]
        return category, [Step("lint", "Rerun Android lint", tasks)], "build/reports/lint-results-*.html"

    if category == "build_health":
        task = task_or_default(value, "buildHealth")
        return (
            category,
            [Step("build_health", "Rerun dependency build health", [task])],
            "build/reports/dependency-analysis/build-health-report.txt",
        )

    if category == "unit_tests":
        if value.startswith(":"):
            tasks = [value]
        else:
            tasks = [
                "test",
                "jacocoCoverage",
                "-x",
                ":app:testChinaDebugUnitTest",
                "-x",
                ":app:testChinaReleaseUnitTest",
            ]
        return category, [Step("unit_tests", "Rerun unit tests", tasks)], "build/reports/tests/"

    if category == "assemble":
        task = value if value.startswith(":") else "assembleWorld"
        return category, [Step("assemble", "Rerun assemble", [task])], None

    if category == "gradle" and value == "gradle":
        return (
            category,
            [
                Step(
                    "push_safety",
                    "Rerun push safety checks after fixing the Gradle/environment failure",
                    [
                        "spotlessCheck",
                        "detekt",
                        "apiCheck",
                        "checkSortDependencies",
                        "lint",
                        *CHINA_LINT_EXCLUDES,
                    ],
                )
            ],
            None,
        )

    if value.startswith(":"):
        return category, [Step("gradle_task", "Rerun exact Gradle task", [value])], None

    raise AgentPrError(
        f"Unknown failure id '{failure}'. Pass an exact Gradle task like ':module:detekt' "
        "or one of: spotless, api_check, sort_dependencies, detekt, lint, build_health, unit_tests, assemble, gradle."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the safe rerun or auto-fix sequence for one failed Mamba PR-push task."
    )
    parser.add_argument("failure", help="Failure id or exact Gradle task from agent-pr-push.py JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Emit planned commands without running them.")
    parser.add_argument("--test-mode", action="store_true", help="Exercise rerun mapping without running Gradle.")
    parser.add_argument("--no-lock", action="store_true", help="Skip the repo-local rerun lock.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ensure_mamba_repo(root)
    out_dir = output_dir(root)
    stamp = now_id()
    category, steps, report_hint = build_steps(args.failure)

    with repo_lock(
        out_dir,
        lock_rel="agent-rerun.lock",
        blocked_message="Another agent rerun is already active.",
        disabled=args.no_lock or args.dry_run or args.test_mode,
    ):
        results: list[CommandResult] = []
        for step in steps:
            result = gradle_step(step, root, out_dir, stamp, args.dry_run, args.test_mode)
            results.append(result)
            if result.exit_code != 0:
                break

    overall_success = all(result.exit_code == 0 for result in results)
    payload: dict[str, object] = {
        "schema_version": 1,
        "timestamp": iso_now(),
        "repo_root": str(root),
        "failure": args.failure,
        "category": category,
        "dry_run": args.dry_run,
        "test_mode": args.test_mode,
        "overall_success": overall_success,
        "report_hint": report_hint,
        "steps": [
            {
                "command": shlex.join(result.command),
                "exit_code": result.exit_code,
                "log_file": result.log_file,
            }
            for result in results
        ],
        "next_action": "Rerun scripts/agent-pr-push.py to continue push validation."
        if overall_success
        else "Inspect the failed step log/report, fix the code if needed, then rerun this script.",
    }

    result_file = out_dir / f"agent-rerun-result-{stamp}.json"
    payload["result_file"] = str(result_file)
    result_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result_file.read_text(encoding="utf-8"), end="")
    return 0 if overall_success else 1


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
