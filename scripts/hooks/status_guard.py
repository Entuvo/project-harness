#!/usr/bin/env python3
"""PreToolUse hook: block hand-editing a work item into a gated status.

Statuses like 'done'/'verified' are advanced by work that produced evidence,
never by a bare edit. If an edit to a story file sets a gated status and the
written content carries no non-empty evidence key, exit 2.

Heuristic by design (an Edit fragment may omit evidence that already exists
in the file — we check the on-disk file too). Fails open on internal error.
The harness self-test proves it fires when healthy.
"""
import fnmatch
import json
import os
import re
import sys

from pathlib import Path


def find_manifest(start: str):
    d = os.path.realpath(start)
    while True:
        m = os.path.join(d, ".claude", "harness.json")
        if os.path.isfile(m):
            return d, m
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def has_evidence(text: str, keys) -> bool:
    for k in keys:
        m = re.search(rf"^\s*{re.escape(k)}:\s*(.+)$", text, re.MULTILINE)
        if m:
            val = m.group(1).strip().strip("\"'").strip()
            if val:  # empty or empty-quoted ("") template defaults are NOT evidence
                return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        fp = ti.get("file_path") or ""
        new_text = ti.get("content") or ti.get("new_string") or ""
        if not fp or not new_text:
            return 0
        root, manifest = find_manifest(os.path.dirname(os.path.abspath(fp)))
        if not manifest:
            return 0
        with open(manifest) as f:
            cfg = json.load(f)
        hooks = cfg.get("hooks") or {}
        glob = hooks.get("story_glob") or "docs/stories/*.md"
        gated = hooks.get("gated_statuses") or []
        keys = hooks.get("evidence_keys") or ["verify_cmd", "result"]
        rel = os.path.relpath(os.path.abspath(fp), root)
        if not fnmatch.fnmatch(rel, glob):
            return 0
        m = re.search(r"^status:\s*(\S+)", new_text, re.MULTILINE)
        if not m or m.group(1).strip("'\"") not in gated:
            return 0
        # Evidence may be in the written fragment or already on disk.
        on_disk = ""
        p = Path(fp)
        if p.is_file():
            on_disk = p.read_text(errors="replace")
        if has_evidence(new_text, keys) or (
            ti.get("new_string") and has_evidence(on_disk, keys)
        ):
            return 0
        print(
            f"BLOCKED: this edit sets status '{m.group(1)}' on {rel} without evidence "
            f"({'/'.join(keys)}). Status is derived from executed checks, never hand-authored "
            "(docs/HARNESS.md honesty rule). Run the verify command, record its output in the "
            "evidence fields, then advance the status in the same edit.",
            file=sys.stderr,
        )
        return 2
    except Exception:
        return 0  # fail open


if __name__ == "__main__":
    sys.exit(main())
