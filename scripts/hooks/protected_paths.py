#!/usr/bin/env python3
"""PreToolUse hook: block edits under protected paths (vendored/generated code).

Reads the hook JSON from stdin, resolves the target file with realpath (so
worktrees and symlinks can't dodge it), and exits 2 if it falls under any
path listed in .claude/harness.json -> hooks.protected_paths.

Bypass: ALLOW_PROTECTED_EDIT=1 — contractually requires a ledger row
(PATCHES.md or a DECISIONS.md entry) in the same change.

Fails open on any internal error: a broken hook must never brick a session.
The harness self-test proves this hook fires when healthy.
"""
import json
import os
import sys


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        fp = ti.get("file_path") or ti.get("notebook_path") or ""
        if not fp:
            return 0
        root, manifest = find_manifest(os.path.dirname(os.path.abspath(fp)))
        if not manifest:
            return 0  # no harness here — not our business
        with open(manifest) as f:
            cfg = json.load(f)
        protected = (cfg.get("hooks") or {}).get("protected_paths") or []
        if not protected:
            return 0
        real = os.path.realpath(fp)
        for p in protected:
            base = os.path.realpath(os.path.join(root, p))
            if real == base or real.startswith(base + os.sep):
                if os.environ.get("ALLOW_PROTECTED_EDIT") == "1":
                    print(
                        f"protected-paths: bypass used for {fp}. "
                        "Contract: land a PATCHES.md/DECISIONS.md ledger row in the SAME commit.",
                        file=sys.stderr,
                    )
                    return 0
                print(
                    f"BLOCKED: {fp} is under protected path '{p}'. "
                    "This code must not be hand-edited (see docs/HARNESS.md). "
                    "If a patch is truly unavoidable: ALLOW_PROTECTED_EDIT=1 plus a "
                    "ledger row with a machine-evaluable retirement condition, same commit.",
                    file=sys.stderr,
                )
                return 2
        return 0
    except Exception:
        return 0  # fail open


if __name__ == "__main__":
    sys.exit(main())
