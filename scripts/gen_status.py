#!/usr/bin/env python3
"""Generate STATUS.md from work-item frontmatter. Deterministic, stdlib only.

    python3 scripts/gen_status.py docs/stories > docs/STATUS.md

STATUS.md is derived, never hand-edited: the harness self-test regenerates it
and diffs against the committed copy (a stale committed copy is a lie in
progress). Output is timestamp-free so identical inputs give identical bytes.
"""
import os
import re
import sys


def frontmatter(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.DOTALL)
    fields = {}
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"^(\w[\w_]*):\s*(.*)$", line)
            if kv:
                fields[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return fields


def cell(v) -> str:
    """A Markdown table cell: escape pipes and flatten newlines so a stray `|` in a
    title/ref can't corrupt the table."""
    return str(v).replace("|", "\\|").replace("\n", " ")


def main() -> int:
    stories_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/stories"
    items = []
    if os.path.isdir(stories_dir):
        for name in sorted(os.listdir(stories_dir)):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(stories_dir, name), encoding="utf-8", errors="replace") as f:
                fm = frontmatter(f.read())
            items.append(
                (fm.get("id", name), fm.get("status", "?"), fm.get("prd_refs", ""), fm.get("title", ""))
            )
    counts = {}
    for _, status, _, _ in items:
        counts[status] = counts.get(status, 0) + 1
    out = [
        "# Status",
        "<!-- harness:status v1 · GENERATED — do not edit. Regenerate: python3 scripts/gen_status.py docs/stories > docs/STATUS.md -->",
        "",
        "## Counts",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    out += [f"| {cell(s)} | {n} |" for s, n in sorted(counts.items())] or ["| (no work items) | 0 |"]
    out += ["", "## Work items", "", "| ID | Status | PRD refs | Title |", "|---|---|---|---|"]
    out += [f"| {cell(i)} | {cell(s)} | {cell(r)} | {cell(t)} |" for i, s, r, t in items]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
