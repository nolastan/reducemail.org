#!/usr/bin/env python3
"""Regenerate sitemap.xml from the pages themselves.

Every page already declares where it lives in its `<link rel="canonical">` tag,
so that tag — not the file path — is the source of truth here. A page without
one is skipped and reported, which is the signal that the page is missing a
canonical rather than that the sitemap is wrong.

`lastmod` comes from the file's last commit date, so it reflects when the page
actually changed rather than when this script happened to run. A file with
uncommitted changes falls back to today.

There is no build step on this site, so this is not wired into anything —
run it after adding or removing a page:

    python3 tools/build-sitemap.py [--dry-run]
"""

import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "sitemap.xml")

# Directories that hold no published pages: the markdown the articles were
# generated from, the generators themselves, and the design docs.
SKIP_DIRS = {".git", ".claude", "blog", "tools", "docs", "assets", "content"}

CANONICAL = re.compile(
    r"""<link\s+rel=["']canonical["']\s+href=["']([^"']+)["']""", re.IGNORECASE
)


def html_files():
    """Every published .html file, depth-first, in a stable order."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".html"):
                yield os.path.join(dirpath, name)


def canonical_url(path):
    with open(path, encoding="utf-8") as handle:
        match = CANONICAL.search(handle.read())
    return match.group(1) if match else None


def last_modified(path, today):
    """Date of the commit that last touched `path`, or today if it's dirty."""
    rel = os.path.relpath(path, ROOT)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", rel],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if dirty.stdout.strip():
        return today

    logged = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", rel],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return logged.stdout.strip() or today


def main():
    dry_run = "--dry-run" in sys.argv
    today = datetime.date.today().isoformat()

    entries = []
    skipped = []
    for path in html_files():
        rel = os.path.relpath(path, ROOT)
        url = canonical_url(path)
        if url is None:
            skipped.append(rel)
            continue
        entries.append((url, last_modified(path, today)))

    entries.sort()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, lastmod in entries:
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % url)
        lines.append("    <lastmod>%s</lastmod>" % lastmod)
        lines.append("  </url>")
    lines.append("</urlset>")
    document = "\n".join(lines) + "\n"

    for rel in skipped:
        print("no canonical, skipped: %s" % rel, file=sys.stderr)

    if dry_run:
        print(document, end="")
    else:
        with open(OUTPUT, "w", encoding="utf-8") as handle:
            handle.write(document)
        print("wrote %d urls to %s" % (len(entries), os.path.relpath(OUTPUT, ROOT)))


if __name__ == "__main__":
    main()
