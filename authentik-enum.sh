#!/usr/bin/env bash
set -euo pipefail

# Fetch all authentik GitHub release tags and request:
#   {domain}/static/dist/admin/AdminInterface-{version}.js
# Print HTTP status + MD5 of the returned response body (even for 404, etc).
#
# Usage:
#   ./authentik-admin-js-md5.sh
#
# Optional env:
#   GITHUB_TOKEN="..."                 # higher GitHub API rate limit
#   AUTHENTIK_REPO="goauthentik/authentik"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }; }
need curl
need python3
need md5sum
need wc

read -r -p "Enter base domain (e.g. https://sso.example.com): " BASE
BASE="${BASE%/}"
if [[ -z "$BASE" ]]; then
  echo "No domain provided, exiting." >&2
  exit 1
fi

REPO="${AUTHENTIK_REPO:-goauthentik/authentik}"

# GitHub API headers
GH_HEADERS=(-H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" -H "User-Agent: authentik-admin-js-md5")
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  GH_HEADERS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

versions_file="${tmpdir}/versions.txt"
: > "$versions_file"

page=1
while :; do
  headers="${tmpdir}/gh_headers_${page}.txt"
  body="${tmpdir}/gh_body_${page}.json"
  url="https://api.github.com/repos/${REPO}/releases?per_page=100&page=${page}"

  if ! curl -sS -L "${GH_HEADERS[@]}" -D "$headers" -o "$body" "$url"; then
    echo "Failed to fetch GitHub releases from: $url" >&2
    echo "Tip: set GITHUB_TOKEN to avoid rate limits." >&2
    exit 1
  fi

  python3 - "$body" >> "$versions_file" <<'PY'
import json, sys, re
data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
for r in data:
    tag = (r.get("tag_name") or "").strip()
    if not tag:
        continue
    tag = re.sub(r"^version/", "", tag)
    tag = re.sub(r"^v", "", tag)
    print(tag)
PY

  if ! grep -qi 'rel="next"' "$headers"; then
    break
  fi
  page=$((page + 1))
done

dedup_file="${tmpdir}/versions_dedup.txt"
python3 - "$versions_file" > "$dedup_file" <<'PY'
import sys
seen=set()
for line in open(sys.argv[1], "r", encoding="utf-8"):
    v=line.strip()
    if not v or v in seen:
        continue
    seen.add(v)
    print(v)
PY

total_versions="$(wc -l < "$dedup_file" | tr -d ' ')"
echo "Found ${total_versions} release tag(s) in ${REPO}."
echo

# Output header (TSV)
printf "version\thttp_status\tmd5\tbytes\turl\n"

while IFS= read -r ver; do
  js_url="${BASE}/static/dist/admin/AdminInterface-${ver}.js"
  resp_file="${tmpdir}/resp_${ver//[^a-zA-Z0-9._-]/_}.bin"

  # Fetch full response body to compute MD5.
  # Do NOT use -f, so we still capture body for 404/500 and can hash it.
  http_code="$(
    curl -sS -L \
      --connect-timeout 10 \
      --max-time 60 \
      -o "$resp_file" \
      -w '%{http_code}' \
      "$js_url" \
    || echo "000"
  )"

  bytes="$(wc -c < "$resp_file" 2>/dev/null || echo 0)"

  if [[ "$http_code" == "000" ]]; then
    md5="-"
    bytes="0"
  else
    md5="$(md5sum "$resp_file" | awk '{print $1}')"
  fi

  printf "%s\t%s\t%s\t%s\t%s\n" "$ver" "$http_code" "$md5" "$bytes" "$js_url"
done < "$dedup_file"
