#!/usr/bin/env python3
"""PreToolUse hook: block writes containing credential-shaped literals.

Two detectors:
  1. Known prefixes (AWS AKIA, sk-/ghp_/xox tokens, PEM private keys, AIza).
  2. Secret-named assignment to a long high-entropy string literal.

Sanctioned: env-var reads (os.environ, ${...}), test/fixture paths.
Fails open on internal error; the harness self-test proves it fires.
"""
import json
import math
import re
import sys

PREFIXES = re.compile(
    r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}"
    r"|xox[bpars]-[A-Za-z0-9\-]{10,}|AIza[0-9A-Za-z_\-]{20,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
ASSIGN = re.compile(
    r"(secret|token|passw|api_?key|credential)[A-Za-z0-9_]*\s*[:=]\s*[\"']([^\"']{16,})[\"']",
    re.IGNORECASE,
)
SKIP_PATH = re.compile(r"(^|/)(tests?|fixtures?|__snapshots__|examples?)(/|$)")
SANCTIONED = re.compile(r"(os\.environ|getenv|\$\{|process\.env|<[A-Z_]+>|\{\{)")


def entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    return -sum((n / len(s)) * math.log2(n / len(s)) for n in freq.values())


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        fp = ti.get("file_path") or ""
        text = ti.get("content") or ti.get("new_string") or ""
        if not text or SKIP_PATH.search(fp.replace("\\", "/")):
            return 0
        for i, line in enumerate(text.splitlines(), 1):
            if SANCTIONED.search(line):
                continue
            if PREFIXES.search(line):
                print(
                    f"BLOCKED: line {i} contains a credential-shaped literal (known token prefix). "
                    "Read secrets from the environment; never write them into tracked files.",
                    file=sys.stderr,
                )
                return 2
            m = ASSIGN.search(line)
            if m and entropy(m.group(2)) >= 3.0:
                print(
                    f"BLOCKED: line {i} assigns a high-entropy literal to '{m.group(1)}…'. "
                    "If this is a real secret, move it to the environment. If it's a test "
                    "value, put it under a tests/ or fixtures/ path.",
                    file=sys.stderr,
                )
                return 2
        return 0
    except Exception:
        return 0  # fail open


if __name__ == "__main__":
    sys.exit(main())
