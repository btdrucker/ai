#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JENKINS_BASE="${JENKINS_BASE_URL:-https://searchscience.jenkins.bmx.nikecloud.com}"
JOB_PATH="job/typeahead/job/search.service.searchtypeahead.searchTermsS3Upload"
JOB_URL="${JENKINS_BASE}/${JOB_PATH}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <test|prod>

Trigger the searchtypeahead S3 publish Jenkins job and poll until completion.

Parameters sent:
  test -> Deploy_Environment=test, deploy flow=RELEASE
  prod -> Deploy_Environment=prod, deploy flow=PRODUCTION

Required environment variables:
  JENKINS_USER       Nike NT username
  JENKINS_API_TOKEN  API token from ${JENKINS_BASE}/user/<user>/configure

Optional:
  JENKINS_BASE_URL   Override Jenkins base URL (default: searchscience BMX)
EOF
}

if [[ "${ENV}" != "test" && "${ENV}" != "prod" ]]; then
  usage >&2
  exit 1
fi

if [[ "${ENV}" == "test" ]]; then
  DEPLOY_FLOW="RELEASE"
else
  DEPLOY_FLOW="PRODUCTION"
fi

if [[ -z "${JENKINS_USER:-}" || -z "${JENKINS_API_TOKEN:-}" ]]; then
  if [[ -f "${HOME}/.netrc" ]]; then
    NETRC_USER=$(awk -v host="searchscience.jenkins.bmx.nikecloud.com" '
      $0 ~ /^machine / { m=$2 }
      m == host && $1 == "login" { print $2 }
    ' "${HOME}/.netrc" | head -1)
    NETRC_PASS=$(awk -v host="searchscience.jenkins.bmx.nikecloud.com" '
      $0 ~ /^machine / { m=$2 }
      m == host && $1 == "password" { print $2 }
    ' "${HOME}/.netrc" | head -1)
    if [[ -n "${NETRC_USER}" && -n "${NETRC_PASS}" ]]; then
      JENKINS_USER="${NETRC_USER}"
      JENKINS_API_TOKEN="${NETRC_PASS}"
    fi
  fi
fi

if [[ -z "${JENKINS_USER:-}" || -z "${JENKINS_API_TOKEN:-}" ]]; then
  echo "error: set JENKINS_USER and JENKINS_API_TOKEN, or add credentials to ~/.netrc" >&2
  exit 1
fi

AUTH=("${JENKINS_USER}:${JENKINS_API_TOKEN}")

echo "Triggering Jenkins job for environment: ${ENV} (deploy flow: ${DEPLOY_FLOW})" >&2

BEFORE=$(curl -sf -u "${AUTH[@]}" "${JOB_URL}/lastBuild/api/json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('number', 0))" 2>/dev/null || echo 0)

CRUMB_JSON=$(curl -sf -u "${AUTH[@]}" "${JENKINS_BASE}/crumbIssuer/api/json" 2>/dev/null || true)
CRUMB_ARGS=()
if [[ -n "${CRUMB_JSON}" ]]; then
  CRUMB=$(echo "${CRUMB_JSON}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('crumb',''))")
  CRUMB_FIELD=$(echo "${CRUMB_JSON}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('crumbRequestField','Jenkins-Crumb'))")
  if [[ -n "${CRUMB}" ]]; then
    CRUMB_ARGS=(-H "${CRUMB_FIELD}:${CRUMB}")
  fi
fi

BUILD_PARAMS="Deploy_Environment=${ENV}&Deploy_Flow=${DEPLOY_FLOW}"
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -u "${AUTH[@]}" "${CRUMB_ARGS[@]}" \
  -X POST "${JOB_URL}/buildWithParameters?${BUILD_PARAMS}" || echo "000")

if [[ "${HTTP_CODE}" != "201" && "${HTTP_CODE}" != "200" && "${HTTP_CODE}" != "302" ]]; then
  echo "error: Jenkins trigger failed with HTTP ${HTTP_CODE}" >&2
  exit 1
fi

echo "Build queued. Waiting for new build number..." >&2
BUILD_NUM=""
for _ in $(seq 1 30); do
  sleep 2
  BUILD_NUM=$(curl -sf -u "${AUTH[@]}" "${JOB_URL}/lastBuild/api/json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('number', 0))")
  if [[ "${BUILD_NUM}" -gt "${BEFORE}" ]]; then
    break
  fi
done

if [[ -z "${BUILD_NUM}" || "${BUILD_NUM}" -le "${BEFORE}" ]]; then
  echo "error: timed out waiting for Jenkins to start a new build" >&2
  exit 1
fi

BUILD_URL="${JOB_URL}/${BUILD_NUM}/"
echo "Build #${BUILD_NUM}: ${BUILD_URL}" >&2

RESULT=""
for _ in $(seq 1 120); do
  BUILD_JSON=$(curl -sf -u "${AUTH[@]}" "${BUILD_URL}api/json")
  BUILDING=$(echo "${BUILD_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('building', True))")
  RESULT=$(echo "${BUILD_JSON}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('result') or '')")
  if [[ "${BUILDING}" == "False" && -n "${RESULT}" ]]; then
    break
  fi
  echo "  still running... (${RESULT:-IN_PROGRESS})" >&2
  sleep 10
done

if [[ "${RESULT}" != "SUCCESS" ]]; then
  echo "error: build finished with result: ${RESULT:-UNKNOWN}" >&2
  echo "Build URL: ${BUILD_URL}" >&2
  exit 1
fi

echo "SUCCESS: ${BUILD_URL}" >&2
echo "${BUILD_URL}"
