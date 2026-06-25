"""Shared helpers for agent PR push scripts (agent-pr-push, agent-rerun-failed-task)."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class AgentPrError(RuntimeError):
    """Shared errors for agent PR helper scripts."""


@dataclass
class CommandResult:
    command: list[str]
    exit_code: int
    log_file: str


CHINA_LINT_EXCLUDES = ["-x", ":app:lintChinaDebug", "-x", ":app:lintChinaRelease"]


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_capture(command: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AgentPrError(
            f"{shlex.join(command)} failed with exit {result.returncode}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def repo_root() -> Path:
    result = run_capture(["git", "rev-parse", "--show-toplevel"], Path.cwd(), check=True)
    return Path(result.stdout.strip()).resolve()


def ensure_mamba_repo(root: Path) -> None:
    if not (root / "gradlew").exists() or not (root / "build.gradle.kts").exists():
        raise AgentPrError(f"{root} does not look like the Mamba Android repo root.")


def output_dir(root: Path) -> Path:
    path = root / "_pra-results"
    path.mkdir(exist_ok=True)
    return path


@contextmanager
def repo_lock(out_dir: Path, *, lock_rel: str, blocked_message: str, disabled: bool = False) -> Iterable[None]:
    if disabled:
        yield
        return

    lock_dir = out_dir / lock_rel
    try:
        lock_dir.mkdir()
        (lock_dir / "pid").write_text(str(os.getpid()), encoding="utf-8")
    except FileExistsError as exc:
        pid = ""
        pid_file = lock_dir / "pid"
        if pid_file.exists():
            pid = pid_file.read_text(encoding="utf-8").strip()
        suffix = f" (pid {pid})" if pid else ""
        raise AgentPrError(
            f"{blocked_message}{suffix} Wait for it to finish, or pass --no-lock if you are certain it is stale."
        ) from exc

    try:
        yield
    finally:
        shutil.rmtree(lock_dir, ignore_errors=True)


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GRADLE_USER_HOME"] = str(Path.home() / ".gradle")
    return env


def run_logged(command: list[str], root: Path, log_file: Path, stream: bool = True) -> CommandResult:
    eprint(f"Running: {shlex.join(command)}")
    eprint(f"Log: {log_file}")
    with log_file.open("w", encoding="utf-8") as log:
        log.write(f"$ {shlex.join(command)}\n\n")
        process = subprocess.Popen(
            command,
            cwd=root,
            env=command_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            if stream:
                print(line, end="", file=sys.stderr)
        exit_code = process.wait()
        log.write(f"\nexit_code={exit_code}\n")
    return CommandResult(command=command, exit_code=exit_code, log_file=str(log_file))


def normalized_failure_arg(value: str) -> str:
    return value.strip().strip("'\"")


def task_name(value: str) -> str:
    """Return the Gradle task name without module path segments."""
    return normalized_failure_arg(value).rsplit(":", 1)[-1]


def category_from_gradle_task(task: str | None) -> str:
    """Classify a Gradle task path from log output (e.g. ':detekt-rules:apiCheck').

    Only the final task segment is classified so module names such as
    ':detekt-rules' or ':test-fixtures' do not affect the result.
    """
    if not task:
        return "gradle"
    lowered = task_name(task).lower()
    if "spotless" in lowered:
        return "spotless"
    if "apicheck" in lowered or "kompare" in lowered:
        return "api_check"
    if "checksortdependencies" in lowered:
        return "sort_dependencies"
    if "buildhealth" in lowered:
        return "build_health"
    if "lint" in lowered:
        return "lint"
    if "test" in lowered or "jacoco" in lowered:
        return "unit_tests"
    if "assemble" in lowered:
        return "assemble"
    if "detekt" in lowered:
        return "detekt"
    return "gradle"


def category_from_user_failure_arg(value: str) -> str:
    """Classify user or agent-supplied failure id (matches category_from_gradle_task order)."""
    normalized = normalized_failure_arg(value)
    lower = normalized.lower()
    task = task_name(normalized).lower()
    if lower in {"spotless", "spotless_check"} or "spotless" in task:
        return "spotless"
    if lower in {"api", "api_check"} or "apicheck" in task or "kompare" in task:
        return "api_check"
    if lower in {"sort", "sort_dependencies"} or "checksortdependencies" in task:
        return "sort_dependencies"
    if "buildhealth" in task or lower == "build_health":
        return "build_health"
    if "lint" in task:
        return "lint"
    if lower in {"unit_tests", "tests"} or "test" in task or "jacoco" in task:
        return "unit_tests"
    if "assemble" in task:
        return "assemble"
    if "detekt" in task:
        return "detekt"
    return "gradle"

