#!/usr/bin/env python3
"""Jenkins BMX API client for Nike Search Engineering services.

Usage:
  List jobs on an instance:
    python3 jenkins_api.py --action list --instance productfeed

  Get build status:
    python3 jenkins_api.py --action status --service envoy [--branch main]

  Trigger a build:
    python3 jenkins_api.py --action build --service envoy [--branch main]

  Get console output:
    python3 jenkins_api.py --action console --service envoy [--branch main] [--build 42]

  Get build history:
    python3 jenkins_api.py --action history --service envoy [--branch main] [--count 10]

Auth:
  Username: stored in <SKILL_DIR>/tokens/username.txt
            Auto-discovered from `git config user.email` if missing (agent confirms first).
            Override with JENKINS_USER env var.
  Token: per-instance files in <SKILL_DIR>/tokens/<instance>_token.txt
         (e.g. productfeed_token.txt, searchscience_token.txt)
         Fallback: ~/.cursor/skills/ops-bmx/tokens/<instance>_token.txt
"""

import argparse
import base64
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
PROJECT_TOKENS_DIR = SKILL_DIR / "tokens"
HOME_TOKENS_DIR = Path.home() / ".cursor/skills/ops-bmx/tokens"

REQUEST_TIMEOUT = 30

BMX_INSTANCES = {
    "productfeed": "https://productfeed.jenkins.bmx.nikecloud.com",
    "searchscience": "https://searchscience.jenkins.bmx.nikecloud.com",
    "smartsearch": "https://smartsearch.jenkins.bmx.nikecloud.com",
}


def _encode_branch(branch: str) -> str:
    """Encode branch name for use as a Jenkins multibranch URL path segment.
    Jenkins uses URL-encoded branch names (e.g. feature%2Ffoo for feature/foo)."""
    return urllib.parse.quote(branch, safe="")


def _job_url_path(job_path: str) -> str:
    """Convert a job path like 'folder/subfolder/jobname' to Jenkins URL segments
    like 'job/folder/job/subfolder/job/jobname'."""
    segments = job_path.split("/")
    return "/job/".join(urllib.parse.quote(seg, safe="") for seg in segments)


def discover_username() -> str | None:
    """Try to discover username from git config user.email."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_username() -> str:
    """Return Jenkins username from env var, file, or fail with discovery hint."""
    env_user = os.environ.get("JENKINS_USER")
    if env_user:
        return env_user

    username_file = PROJECT_TOKENS_DIR / "username.txt"
    if username_file.is_file():
        value = username_file.read_text().strip()
        if value:
            return value

    home_file = HOME_TOKENS_DIR / "username.txt"
    if home_file.is_file():
        value = home_file.read_text().strip()
        if value:
            return value

    discovered = discover_username()
    hint = ""
    if discovered:
        hint = (
            f"\n  Auto-discovered from git: {discovered}"
            f"\n  If correct, create the file with:"
            f"\n    echo '{discovered}' > {username_file}"
        )

    print(
        f"ERROR: Jenkins username not found.{hint}\n"
        f"  Or set JENKINS_USER env var.\n"
        f"  File locations checked:\n"
        f"    {username_file}\n"
        f"    {home_file}",
        file=sys.stderr,
    )
    sys.exit(1)


def get_token(instance: str) -> str:
    """Return API token for a Jenkins instance from file or env."""
    env_token = os.environ.get("JENKINS_TOKEN")
    if env_token:
        return env_token

    token_file = PROJECT_TOKENS_DIR / f"{instance}_token.txt"
    if token_file.is_file():
        value = token_file.read_text().strip()
        if value:
            return value

    home_file = HOME_TOKENS_DIR / f"{instance}_token.txt"
    if home_file.is_file():
        value = home_file.read_text().strip()
        if value:
            return value

    base_url = BMX_INSTANCES.get(instance, f"https://{instance}.jenkins.bmx.nikecloud.com")
    print(
        f"ERROR: No API token found for instance '{instance}'.\n"
        f"  Options (checked in order):\n"
        f"    1. Set JENKINS_TOKEN environment variable\n"
        f"    2. Save token to: {token_file}\n"
        f"    3. Save token to: {home_file}\n"
        f"  Generate one at: {base_url}/user/<your-username>/configure\n"
        f"    (Profile dropdown -> Security -> API Token -> Add New Token)",
        file=sys.stderr,
    )
    sys.exit(1)


def _ssl_context() -> ssl.SSLContext:
    """Unverified SSL for *.nikecloud.com -- Nike internal CA is not in Python's
    cert bundle and distributing it reliably across dev machines is impractical."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def make_request(url: str, user: str, token: str, method: str = "GET") -> tuple[int, str]:
    """Make an authenticated request to Jenkins. Returns (status_code, body)."""
    auth_string = base64.b64encode(f"{user}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_string}"}

    ctx = _ssl_context()
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body
    except urllib.error.URLError as e:
        print(f"ERROR: Network error connecting to Jenkins: {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_crumb(base_url: str, user: str, token: str) -> dict:
    """Fetch a CSRF crumb for POST requests."""
    url = f"{base_url}/crumbIssuer/api/json"
    status, body = make_request(url, user, token)
    if status == 200:
        try:
            data = json.loads(body)
            return {data["crumbRequestField"]: data["crumb"]}
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def make_post(url: str, user: str, token: str, base_url: str,
              data: bytes = b"", content_type: str | None = None) -> tuple[int, str]:
    """Make an authenticated POST request with CSRF crumb."""
    auth_string = base64.b64encode(f"{user}:{token}".encode()).decode()
    crumb = get_crumb(base_url, user, token)

    headers = {"Authorization": f"Basic {auth_string}"}
    if content_type:
        headers["Content-Type"] = content_type
    headers.update(crumb)

    ctx = _ssl_context()
    req = urllib.request.Request(url, headers=headers, method="POST", data=data)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body
    except urllib.error.URLError as e:
        print(f"ERROR: Network error connecting to Jenkins: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _validate_instance(instance: str | None) -> str:
    """Validate and return instance, or exit with error."""
    if not instance:
        print(f"ERROR: --instance is required."
              f" Available: {', '.join(sorted(BMX_INSTANCES))}", file=sys.stderr)
        sys.exit(1)
    if instance not in BMX_INSTANCES:
        print(f"ERROR: Unknown instance '{instance}'."
              f" Available: {', '.join(sorted(BMX_INSTANCES))}", file=sys.stderr)
        sys.exit(1)
    return instance


def _search_instance_for_job(base_url: str, user: str, token: str, target: str,
                            path_prefix: str = "", max_depth: int = 3) -> str | None:
    """Recursively search a Jenkins instance for a job matching target name.
    Collects all candidates and returns the best match (prefers multibranch pipelines,
    exact name matches, and shorter paths). Returns full job path or None."""
    candidates: list[tuple[tuple, str]] = []  # ((match, type, depth), full_path)
    _collect_candidates(base_url, user, token, target, candidates, path_prefix, max_depth)
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def _collect_candidates(base_url: str, user: str, token: str, target: str,
                        candidates: list, path_prefix: str = "", max_depth: int = 3):
    """Recursively collect job candidates matching target."""
    prefix = f"/job/{_job_url_path(path_prefix)}" if path_prefix else ""
    url = f"{base_url}{prefix}/api/json?tree=jobs[name,_class]"
    status, body = make_request(url, user, token)
    if status != 200:
        return
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return

    target_lower = target.lower()
    for item in data.get("jobs", []):
        name = item.get("name", "")
        cls = item.get("_class", "")
        full_path = f"{path_prefix}/{name}" if path_prefix else name

        if "folder" in cls.lower():
            if max_depth > 0:
                _collect_candidates(base_url, user, token, target,
                                    candidates, full_path, max_depth - 1)
        elif target_lower in name.lower():
            # Score: lower is better
            # Prefer: exact match > ends-with match > contains match
            # Prefer: multibranch pipelines over other job types
            # Prefer: shorter paths (less nesting)
            is_multibranch = "MultiBranch" in cls or "WorkflowMultiBranch" in cls
            name_lower = name.lower()
            if name_lower == target_lower or name_lower == f"search.service.{target_lower}":
                match_score = 0
            elif name_lower.endswith(target_lower) or name_lower.endswith(f"-{target_lower}"):
                match_score = 1
            else:
                match_score = 2
            type_score = 0 if is_multibranch else 1
            depth_score = full_path.count("/")
            score = (match_score, type_score, depth_score)
            candidates.append((score, full_path))


def _get_token_or_none(instance: str) -> str | None:
    """Return API token for an instance, or None if unavailable (non-fatal)."""
    env_token = os.environ.get("JENKINS_TOKEN")
    if env_token:
        return env_token
    token_file = PROJECT_TOKENS_DIR / f"{instance}_token.txt"
    if token_file.is_file():
        value = token_file.read_text().strip()
        if value:
            return value
    home_file = HOME_TOKENS_DIR / f"{instance}_token.txt"
    if home_file.is_file():
        value = home_file.read_text().strip()
        if value:
            return value
    return None


def resolve_service(service: str, instance_hint: str | None = None) -> tuple[str, str, str]:
    """Search Jenkins instances for a job matching the service name.
    If instance_hint is provided, searches that instance first for speed.
    Skips instances where no token is available.
    Returns (base_url, job_path, instance)."""
    search_order = list(BMX_INSTANCES.keys())
    if instance_hint and instance_hint in BMX_INSTANCES:
        search_order.remove(instance_hint)
        search_order.insert(0, instance_hint)

    user = get_username()
    skipped = []
    for instance in search_order:
        token = _get_token_or_none(instance)
        if not token:
            skipped.append(instance)
            continue
        base_url = BMX_INSTANCES[instance]
        found = _search_instance_for_job(base_url, user, token, service)
        if found:
            print(f"Found: {found} on {instance}", file=sys.stderr)
            return base_url, found, instance

    print(f"ERROR: No job matching '{service}' found.", file=sys.stderr)
    print(f"  Searched: {', '.join(i for i in search_order if i not in skipped)}", file=sys.stderr)
    if skipped:
        print(f"  Skipped (no token): {', '.join(skipped)}", file=sys.stderr)
    print(f"  Tip: use --action list --instance <name> to browse available jobs.", file=sys.stderr)
    sys.exit(1)


def action_list(args, user):
    """List all jobs on a Jenkins instance, recursing into folders."""
    instance = _validate_instance(args.instance)

    token = get_token(instance)
    base_url = BMX_INSTANCES[instance]

    def _collect_jobs(prefix: str = "", depth: int = 3) -> list[dict]:
        url_prefix = f"/job/{_job_url_path(prefix)}" if prefix else ""
        url = f"{base_url}{url_prefix}/api/json?tree=jobs[name,url,color,_class]"
        status, body = make_request(url, user, token)
        if status != 200:
            if not prefix:
                snippet = body[:300] if body else "(empty response)"
                print(f"ERROR: HTTP {status} from {url}\n{snippet}", file=sys.stderr)
                sys.exit(1)
            return []
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            if not prefix:
                print(f"ERROR: Expected JSON from Jenkins but got unexpected response:\n{body[:300]}", file=sys.stderr)
                sys.exit(1)
            return []
        results = []
        for item in data.get("jobs", []):
            name = item.get("name", "")
            full_path = f"{prefix}/{name}" if prefix else name
            if "folder" in item.get("_class", "").lower():
                if depth > 0:
                    results.extend(_collect_jobs(full_path, depth - 1))
            else:
                results.append({"name": name, "path": full_path,
                                "url": item.get("url", ""), "color": item.get("color", "")})
        return results

    jobs = _collect_jobs()
    print(json.dumps({"instance": instance, "url": base_url, "job_count": len(jobs), "jobs": jobs}, indent=2))


def action_status(args, user):
    """Get the status of the last build for a service/branch."""
    base_url, job_name, instance = resolve_service(args.service, args.instance)
    token = get_token(instance)
    branch = args.branch or "main"
    encoded_branch = _encode_branch(branch)

    url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/lastBuild/api/json"
    status, body = make_request(url, user, token)

    if status == 404 and branch == "main":
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/lastBuild/api/json"
        status, body = make_request(url, user, token)
        if status == 200:
            branch = "master"

    if status != 200:
        if status in (401, 403):
            print(f"ERROR: HTTP {status} -- authentication failed for {job_name}/{branch}. Check your token.", file=sys.stderr)
        elif status == 404:
            print(f"ERROR: HTTP 404 -- no builds found for {job_name}/{branch}", file=sys.stderr)
        else:
            print(f"ERROR: HTTP {status} from Jenkins for {job_name}/{branch}: {body[:200]}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"ERROR: Expected JSON from Jenkins but got unexpected response:\n{body[:300]}", file=sys.stderr)
        sys.exit(1)
    result = {
        "service": args.service,
        "job": job_name,
        "branch": branch,
        "build_number": data.get("number"),
        "result": data.get("result"),
        "building": data.get("building"),
        "duration_ms": data.get("duration"),
        "timestamp": data.get("timestamp"),
        "url": data.get("url"),
        "display_name": data.get("displayName"),
    }
    print(json.dumps(result, indent=2))


def _build_error(status: int, body: str, job_name: str, branch: str):
    """Print a build-trigger error with context and exit."""
    if status in (401, 403):
        print(f"ERROR: HTTP {status} -- authentication failed for {job_name}/{branch}. Check your token.", file=sys.stderr)
    else:
        print(f"ERROR: HTTP {status} triggering build for {job_name}/{branch}", file=sys.stderr)
        if body:
            print(body[:500], file=sys.stderr)
    sys.exit(1)


def action_build(args, user):
    """Trigger a new build for a service/branch."""
    base_url, job_name, instance = resolve_service(args.service, args.instance)
    token = get_token(instance)
    branch = args.branch or "main"
    encoded_branch = _encode_branch(branch)

    if args.params:
        params_list = [p.strip() for p in args.params.split(",") if "=" in p]
        form_data = urllib.parse.urlencode(
            [tuple(p.split("=", 1)) for p in params_list]
        ).encode("utf-8")
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/buildWithParameters"
        status, body = make_post(url, user, token, base_url,
                                 data=form_data,
                                 content_type="application/x-www-form-urlencoded")
    else:
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/build"
        status, body = make_post(url, user, token, base_url)

    if status in (200, 201, 202):
        print(json.dumps({
            "triggered": True,
            "service": args.service,
            "branch": branch,
            "params": args.params or None,
            "message": f"Build triggered for {job_name}/{branch}",
            "jenkins_url": f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/",
        }, indent=2))
    elif status == 404 and branch == "main":
        if args.params:
            url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/buildWithParameters"
            status, body = make_post(url, user, token, base_url,
                                     data=form_data,
                                     content_type="application/x-www-form-urlencoded")
        else:
            url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/build"
            status, body = make_post(url, user, token, base_url)
        if status in (200, 201, 202):
            print(json.dumps({
                "triggered": True,
                "service": args.service,
                "branch": "master",
                "params": args.params or None,
                "message": f"Build triggered for {job_name}/master (main not found)",
                "jenkins_url": f"{base_url}/job/{_job_url_path(job_name)}/job/master/",
            }, indent=2))
        else:
            _build_error(status, body, job_name, "master")
    else:
        _build_error(status, body, job_name, branch)


def action_console(args, user):
    """Get console output for a build."""
    base_url, job_name, instance = resolve_service(args.service, args.instance)
    token = get_token(instance)
    branch = args.branch or "main"
    encoded_branch = _encode_branch(branch)
    build = args.build or "lastBuild"

    url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/{build}/consoleText"
    status, body = make_request(url, user, token)

    if status == 404 and branch == "main":
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/{build}/consoleText"
        status, body = make_request(url, user, token)
        if status == 200:
            branch = "master"

    if status != 200:
        print(f"ERROR: HTTP {status} fetching console for {job_name}/{branch} build {build}: {body[:200]}", file=sys.stderr)
        sys.exit(1)

    print(body)


def action_history(args, user):
    """Get build history for a service/branch."""
    if args.count < 1 or args.count > 100:
        print("ERROR: --count must be between 1 and 100", file=sys.stderr)
        sys.exit(1)
    base_url, job_name, instance = resolve_service(args.service, args.instance)
    token = get_token(instance)
    branch = args.branch or "main"
    encoded_branch = _encode_branch(branch)
    count = args.count

    tree = urllib.parse.quote(f"builds[number,result,timestamp,duration,url,displayName]{{0,{count}}}")
    url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/api/json?tree={tree}"
    status, body = make_request(url, user, token)

    if status == 404 and branch == "main":
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/api/json?tree={tree}"
        status, body = make_request(url, user, token)
        if status == 200:
            branch = "master"

    if status != 200:
        print(f"ERROR: HTTP {status}", file=sys.stderr)
        print(body[:500], file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"ERROR: Expected JSON from Jenkins but got unexpected response:\n{body[:300]}", file=sys.stderr)
        sys.exit(1)
    builds = data.get("builds", [])
    print(json.dumps({
        "service": args.service,
        "branch": branch,
        "builds": builds,
    }, indent=2))


def action_artifact(args, user):
    """Fetch a build artifact by relative path."""
    base_url, job_name, instance = resolve_service(args.service, args.instance)
    token = get_token(instance)
    branch = args.branch or "main"
    encoded_branch = _encode_branch(branch)
    build = args.build or "lastSuccessfulBuild"
    artifact_path = args.artifact_path

    if not artifact_path:
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/{build}/api/json?tree=artifacts[fileName,relativePath]"
        status, body = make_request(url, user, token)

        if status == 404 and branch == "main":
            url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/{build}/api/json?tree=artifacts[fileName,relativePath]"
            status, body = make_request(url, user, token)

        if status != 200:
            print(f"ERROR: HTTP {status} listing artifacts for {job_name}/{branch} build {build}", file=sys.stderr)
            sys.exit(1)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            print(f"ERROR: Unexpected response:\n{body[:300]}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps({"artifacts": data.get("artifacts", [])}, indent=2))
        return

    url = f"{base_url}/job/{_job_url_path(job_name)}/job/{encoded_branch}/{build}/artifact/{artifact_path}"
    status, body = make_request(url, user, token)

    if status == 404 and branch == "main":
        url = f"{base_url}/job/{_job_url_path(job_name)}/job/master/{build}/artifact/{artifact_path}"
        status, body = make_request(url, user, token)

    if status != 200:
        print(f"ERROR: HTTP {status} fetching artifact '{artifact_path}' for {job_name}/{branch} build {build}", file=sys.stderr)
        sys.exit(1)

    print(body)


def action_get_config(args, user):
    """Get the XML config of an existing job (for use as a template)."""
    if not args.service and not args.job_path:
        print('ERROR: --service or --job-path required for get-config', file=sys.stderr)
        sys.exit(1)

    if args.service and args.job_path:
        print("WARNING: Both --service and --job-path provided; using --service (ignoring --job-path)", file=sys.stderr)

    if args.service:
        base_url, job_name, instance = resolve_service(args.service, args.instance)
    else:
        instance = _validate_instance(args.instance)
        base_url = BMX_INSTANCES[instance]
        job_name = args.job_path

    token = get_token(instance)
    url = f"{base_url}/job/{_job_url_path(job_name)}/config.xml"
    status, body = make_request(url, user, token)

    if status != 200:
        snippet = body[:300] if body else "(empty response)"
        print(f"ERROR: HTTP {status} fetching config from {url}\n{snippet}", file=sys.stderr)
        sys.exit(1)

    print(body)


def action_create_job(args, user):
    """Create a new multibranch pipeline job from XML config (stdin or --config-file)."""
    instance = _validate_instance(args.instance)

    if not args.job_name:
        print('ERROR: --job-name is required for create-job', file=sys.stderr)
        sys.exit(1)

    base_url = BMX_INSTANCES[instance]
    token = get_token(instance)

    if args.config_file:
        config_path = Path(args.config_file)
        try:
            config_xml = config_path.read_text()
        except OSError as e:
            print(f"ERROR: Cannot read config file '{args.config_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        config_xml = sys.stdin.read()

    if not config_xml.strip():
        print('ERROR: No XML config provided (use --config-file or pipe to stdin)', file=sys.stderr)
        sys.exit(1)

    if args.folder:
        folder_path = f"/job/{_job_url_path(args.folder)}"
    else:
        folder_path = ""
    url = f"{base_url}{folder_path}/createItem?name={urllib.parse.quote(args.job_name)}"
    status, body = make_post(url, user, token, base_url,
                             data=config_xml.encode("utf-8"),
                             content_type="application/xml")

    if status in (200, 201):
        job_url_path = f"{folder_path}/job/{urllib.parse.quote(args.job_name)}"
        print(json.dumps({
            "created": True,
            "job_name": args.job_name,
            "folder": args.folder or None,
            "instance": instance,
            "url": f"{base_url}{job_url_path}/",
        }, indent=2))
    else:
        print(f"ERROR: HTTP {status} creating job", file=sys.stderr)
        print(body[:500], file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Jenkins BMX API client for Search Engineering")
    parser.add_argument("--action", required=True,
                        choices=["list", "status", "build", "console", "history", "artifact", "get-config", "create-job"],
                        help="Action to perform")
    parser.add_argument("--service", help="Service name (see REFERENCE.md)")
    parser.add_argument("--instance", help="BMX instance name (required for list, create-job, and get-config with --job-path)")
    parser.add_argument("--branch", default=None, help="Branch name (default: main)")
    parser.add_argument("--build", default=None, help="Build number (for console action; default: lastBuild)")
    parser.add_argument("--count", default=10, type=int, help="Number of builds for history (default: 10, max: 100)")
    parser.add_argument("--job-path", default=None, help="Raw job path for get-config (alternative to --service)")
    parser.add_argument("--job-name", default=None, help="New job name for create-job action")
    parser.add_argument("--config-file", default=None, help="Path to XML config file for create-job")
    parser.add_argument("--folder", default=None, help="Parent folder path for create-job (e.g. 'google' or '.net/lambda')")
    parser.add_argument("--artifact-path", default=None,
                        help="Relative path to artifact (for artifact action; omit to list all artifacts)")
    parser.add_argument("--params", default=None,
                        help="Comma-separated KEY=VALUE build parameters (triggers buildWithParameters)")

    args = parser.parse_args()

    if args.action in ("status", "build", "console", "history", "artifact") and not args.service:
        parser.error(f"--service is required for action '{args.action}'")

    user = get_username()

    actions = {
        "list": action_list,
        "status": action_status,
        "build": action_build,
        "console": action_console,
        "history": action_history,
        "artifact": action_artifact,
        "get-config": action_get_config,
        "create-job": action_create_job,
    }
    actions[args.action](args, user)


if __name__ == "__main__":
    main()
