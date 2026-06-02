#!/usr/bin/env python3
"""Refresh star counts embedded in the profile README files.

Each count lives between markers like:
    (<!--stars:frontend-slides-->19.9k+<!--/stars--> stars)
This script finds every such marker, looks up the repo's current star count
via the GitHub API, formats it (e.g. 19916 -> "19.9k+", 802 -> "802+"), and
rewrites the value in place. Descriptions and layout are left untouched.
"""

import json
import os
import re
import sys
import urllib.request

OWNER = "zarazhangrui"
FILES = ["README.md", "README.zh-CN.md"]
MARKER = re.compile(r"(<!--stars:([\w.\-]+)-->)(.*?)(<!--/stars-->)")
TOKEN = os.environ.get("GITHUB_TOKEN")


def format_count(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k+"
    return f"{n}+"


def fetch_stars(repo: str) -> int:
    url = f"https://api.github.com/repos/{OWNER}/{repo}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["stargazers_count"]


def main() -> None:
    cache: dict[str, str] = {}
    changed = False

    for path in FILES:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        def replace(match: "re.Match[str]") -> str:
            slug = match.group(2)
            if slug not in cache:
                cache[slug] = format_count(fetch_stars(slug))
                print(f"{slug}: {cache[slug]}")
            return match.group(1) + cache[slug] + match.group(4)

        new_text = MARKER.sub(replace, text)
        if new_text != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)
            changed = True
            print(f"updated {path}")

    if not changed:
        print("no changes")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
