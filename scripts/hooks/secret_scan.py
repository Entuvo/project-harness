#!/usr/bin/env python3
"""PreToolUse hook: block writes containing credential-shaped literals.

Two detectors:
  1. Known prefixes (AWS AKIA, sk-/ghp_/xox tokens, PEM private keys, AIza) —
     high-confidence, so they fire even on an otherwise-sanctioned line.
  2. Secret-named assignment to a long high-entropy string literal — skipped when
     the value itself is a placeholder ({{ }}, ${...}, <PLACEHOLDER>) or env read,
     or the file is a test/fixture path.

Reads every write surface: Write content, Edit/MultiEdit new_string(s),
NotebookEdit new_source. Fails open on internal error; the self-test proves it fires.
"""
import json
import math
import re
import sys

# Known high-confidence token shapes. sk- uses the real base64url charset (- and _
# included, so modern OpenAI proj/svcacct and provider keys match) with a length
# floor of 32 — the shortest common real sk- key (e.g. 32-hex provider keys) — so a
# short hyphenated identifier like `sk-loading-spinner-container` (25 chars) is not
# a false hit. ponytail: length is the discriminator, not charset; a bare sk- key
# under 32 chars relies on the entropy detector when it is secret-named.
PREFIXES = re.compile(
    r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{32,}|ghp_[A-Za-z0-9]{20,}"
    r"|xox[bpars]-[A-Za-z0-9\-]{10,}|AIza[0-9A-Za-z_\-]{20,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
ASSIGN = re.compile(
    r"(secret|token|passw|api_?key|credential)[A-Za-z0-9_]*\s*[:=]\s*[\"']([^\"']{16,})[\"']",
    re.IGNORECASE,
)
SKIP_PATH = re.compile(r"(^|/)(tests?|fixtures?|__snapshots__|examples?)(/|$)")
# A placeholder / interpolation. Matched against the ENTROPY detector's captured
# VALUE (not the whole line) so a `# {{x}}`/`# ${x}` comment can't shield a real
# secret literal. Prefixes fire regardless of this.
SANCTIONED = re.compile(r"(os\.environ|getenv|\$\{|process\.env|<[A-Z_]+>|\{\{)")


def entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    return -sum((n / len(s)) * math.log2(n / len(s)) for n in freq.values())


def edited_text(ti: dict) -> str:
    """Concatenate every write surface: Write content, Edit/MultiEdit new_string(s),
    NotebookEdit new_source. A hook blind to one of these is a hole."""
    parts = [ti.get("content"), ti.get("new_string"), ti.get("new_source")]
    parts += [e.get("new_string") for e in (ti.get("edits") or []) if isinstance(e, dict)]
    return "\n".join(p for p in parts if p)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        fp = ti.get("file_path") or ti.get("notebook_path") or ""
        text = edited_text(ti)
        if not text or SKIP_PATH.search(fp.replace("\\", "/")):
            return 0
        for i, line in enumerate(text.splitlines(), 1):
            # Known token prefixes are high-confidence — flag even on a line an
            # env-read or template would otherwise sanction (a real key is never a false alarm).
            if PREFIXES.search(line):
                print(
                    f"BLOCKED: line {i} contains a credential-shaped literal (known token prefix). "
                    "Read secrets from the environment; never write them into tracked files.",
                    file=sys.stderr,
                )
                return 2
            # Entropy detector: secret-named assignment to a long literal, unless the
            # VALUE itself is a placeholder/env-read (sanction the value, not the line).
            m = ASSIGN.search(line)
            if m and not SANCTIONED.search(m.group(2)) and entropy(m.group(2)) >= 3.0:
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
