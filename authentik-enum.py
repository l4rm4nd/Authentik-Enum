#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

GITHUB_API = "https://api.github.com"


def normalize_tag(tag: str) -> str:
    tag = tag.strip()
    tag = re.sub(r"^version/", "", tag)
    tag = re.sub(r"^v", "", tag)
    return tag


def parse_link_header(link: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for part in link.split(","):
        part = part.strip()
        m = re.match(r'^<([^>]+)>;\s*rel="([^"]+)"$', part)
        if m:
            url, rel = m.group(1), m.group(2)
            out[rel] = url
    return out


def github_fetch_release_tags(repo: str, timeout: float, token: Optional[str]) -> List[str]:
    opener = build_opener(HTTPRedirectHandler())
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "authentik-admin-js-md5",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    versions: List[str] = []
    seen = set()

    url = f"{GITHUB_API}/repos/{repo}/releases?per_page=100&page=1"
    while url:
        req = Request(url, headers=headers, method="GET")
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            for rel in data:
                tag = normalize_tag(rel.get("tag_name") or "")
                if not tag or tag in seen:
                    continue
                seen.add(tag)
                versions.append(tag)

            link = resp.headers.get("Link") or ""
            url = parse_link_header(link).get("next", "")

        time.sleep(0.05)

    return versions


def fetch_status_md5_bytes(url: str, timeout: float) -> Tuple[int, str, int]:
    opener = build_opener(HTTPRedirectHandler())
    req = Request(url, headers={"User-Agent": "authentik-admin-js-md5"}, method="GET")

    md5 = hashlib.md5()
    total = 0

    try:
        with opener.open(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", resp.getcode()))
            while True:
                chunk = resp.read(1024 * 128)
                if not chunk:
                    break
                md5.update(chunk)
                total += len(chunk)
            return status, md5.hexdigest(), total

    except HTTPError as e:
        status = int(getattr(e, "code", 0) or 0)
        try:
            while True:
                chunk = e.read(1024 * 128)
                if not chunk:
                    break
                md5.update(chunk)
                total += len(chunk)
            md5_hex = md5.hexdigest() if total > 0 else hashlib.md5(b"").hexdigest()
            return status, md5_hex, total
        except Exception:
            return status, "-", 0

    except (URLError, TimeoutError, Exception):
        return 0, "-", 0


def main() -> int:
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Find (or enumerate) authentik AdminInterface-{version}.js and print HTTP status + MD5.",
    )
    ap.add_argument("--base-url", help="Base URL, e.g. https://sso.example.com")
    ap.add_argument("--repo", default="goauthentik/authentik", help="GitHub repo to query for releases")
    ap.add_argument("--timeout", type=float, default=30.0, help="Network timeout (seconds)")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep between requests (seconds)")
    ap.add_argument("--all", action="store_true", help="Do not stop at first hit; enumerate all versions")
    ap.add_argument("--include-404", action="store_true", help="Print 404 rows (otherwise they are skipped)")
    ap.add_argument("--verbose", action="store_true", help="Print checked versions to STDERR")
    args = ap.parse_args()

    base_url = (args.base_url or "").strip()
    if not base_url:
        base_url = input("Enter base URL (e.g. https://sso.example.com): ").strip()
    base_url = base_url.rstrip("/")
    if not base_url:
        print("No base URL provided.", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN") or None

    try:
        versions = github_fetch_release_tags(args.repo, timeout=args.timeout, token=token)
    except Exception as e:
        print(f"Failed to fetch GitHub releases for {args.repo}: {e}", file=sys.stderr)
        print("Tip: set GITHUB_TOKEN to avoid GitHub rate limits.", file=sys.stderr)
        return 1

    # Print TSV header
    print("version\thttp_status\tmd5\tbytes\turl")

    hits = 0
    for i, ver in enumerate(versions, start=1):
        js_url = f"{base_url}/static/dist/admin/AdminInterface-{ver}.js"

        if args.verbose:
            print(f"checking [{i}/{len(versions)}] {ver}", file=sys.stderr)

        status, md5_hex, nbytes = fetch_status_md5_bytes(js_url, timeout=args.timeout)

        # Skip 404 noise unless user asked for it
        if status == 404 and not args.include_404:
            pass
        else:
            # In default mode, we only really care about hits,
            # but still allow printing non-404 errors for troubleshooting.
            if args.all:
                # enumerate mode: print whatever is allowed by filters
                print(f"{ver}\t{status}\t{md5_hex}\t{nbytes}\t{js_url}")
            else:
                # find-first mode: print only the first HTTP 200 and exit
                if status == 200:
                    print(f"{ver}\t{status}\t{md5_hex}\t{nbytes}\t{js_url}")
                    return 0

        if status == 200:
            hits += 1

        if args.sleep > 0:
            time.sleep(args.sleep)

    # If we get here:
    # - in find-first mode: no 200 found
    # - in --all mode: finished enumeration
    if not args.all:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
