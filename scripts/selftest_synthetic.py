#!/usr/bin/env python3
"""Synthetic tier-M install test — the CI-run product test for harness_selftest.py.

Builds a complete tier-M harness install in a tempdir, asserts the shipped
`scripts/harness_selftest.py` PASSes it (with every plant firing), then applies
each tamper from README's Verification list — plus the G1 "enabled hook deleted,
its settings line remains" case — and asserts the self-test flips to exit 1.
Finally feeds each hook MultiEdit- and NotebookEdit-shaped payloads directly and
asserts the credential/status/protected-path guards still catch them (the tool
shapes the hooks were previously blind to).

Why this exists apart from `make check`: this repo's own installed harness
(.claude/, CLAUDE.md, docs/, Makefile) is intentionally git-excluded, so a fresh
CI checkout has no dogfood install to test and no `make` target. This
self-contained synthetic install is the CI-appropriate gate. Offline, stdlib
only, runs in seconds.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELFTEST = REPO / "scripts" / "harness_selftest.py"
HOOKS_SRC = REPO / "scripts" / "hooks"
GEN_STATUS = REPO / "scripts" / "gen_status.py"
GEN_DASH = REPO / "scripts" / "gen_dashboard.py"

FAILURES = []

# The template's tier-M-prune marker, assembled so this test file — a component
# of this repo's own tier-S install — does not itself trip the tier-prune check.
PRUNE_MARKER = "Delete on tier " + "S"


def check(ok: bool, msg: str, detail: str = ""):
    print(("ok   " if ok else "FAIL ") + msg + (f"\n      {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(msg)


def run_selftest(root: Path):
    p = subprocess.run(
        [sys.executable, str(SELFTEST), str(root)],
        capture_output=True, text=True, timeout=120,
    )
    return p.returncode, p.stdout + p.stderr


def run_hook(hook: str, payload: dict) -> int:
    env = {k: v for k, v in os.environ.items() if k != "ALLOW_PROTECTED_EDIT"}
    p = subprocess.run(
        [sys.executable, str(HOOKS_SRC / hook)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=15, env=env,
    )
    return p.returncode


def plant_passed(out: str, name: str) -> bool:
    return any(line.startswith("PASS") and name in line for line in out.splitlines())


CORE_RULES = """<!-- harness:core-rules:begin -->
1. Surface assumptions before writing code.
2. State victory conditions before a non-trivial change.
3. Minimum code that solves the problem.
4. Surgical diffs: every changed line traces to the request.
5. Loop until verified: a completion claim requires executed check output.
6. Status is derived from evidence, never hand-authored.
<!-- harness:core-rules:end -->"""

HOOKS = ["protected_paths.py", "secret_scan.py", "status_guard.py"]

SETTINGS = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                "hooks": [
                    {"type": "command", "command": f"sh -c 'test ! -f .claude/hooks/{h} || python3 .claude/hooks/{h}'"}
                    for h in HOOKS
                ],
            }
        ]
    }
}

# A PREFIXES-only replacement hook: catches AKIA but has no entropy-assignment
# detector and ignores MultiEdit edits[] — used to prove those plants bite.
PREFIXES_ONLY_HOOK = '''import json, re, sys
P = re.compile(r"AKIA[0-9A-Z]{16}")
try:
    ti = json.load(sys.stdin).get("tool_input") or {}
    text = ti.get("content") or ti.get("new_string") or ""
    for line in text.splitlines():
        if P.search(line):
            print("blocked", file=sys.stderr)
            sys.exit(2)
    sys.exit(0)
except Exception:
    sys.exit(0)
'''


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build_golden(root: Path):
    """Assemble a complete, valid tier-M install under `root`."""
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(SELFTEST, root / "scripts" / "harness_selftest.py")
    shutil.copy(GEN_STATUS, root / "scripts" / "gen_status.py")
    (root / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    for h in HOOKS:
        shutil.copy(HOOKS_SRC / h, root / ".claude" / "hooks" / h)

    write(
        root / "CLAUDE.md",
        "# synthetic — bootstrap pointer\n## CURRENT FOCUS\n- Objective: exercise the self-test\n\n"
        "## Always-on rules\n" + CORE_RULES + "\n",
    )

    for name, marker in [("HARNESS", "harness-md"), ("ACTIVE", "active")]:
        write(root / "docs" / f"{name}.md", f"# {name}\n<!-- harness:{marker} v1 -->\n\nSynthetic body.\n")

    # Richer docs so the dashboard panels have structured signals to render.
    write(root / "docs" / "PRD.md",
          "# PRD\n<!-- harness:prd v1 -->\n\n"
          "### R1 — Session\n- **R1.c1:** create checkout session\n- **R1.c2:** expire idle session\n\n"
          "### R2 — Webhooks\n- **R2.c1:** split payment intents\n- **R2.c2:** verify signature\n"
          "- **R2.c3:** retry backoff\n\n### R3 — Fraud\n- **R3.c1:** score threshold\n")
    write(root / "docs" / "PLAN.md",
          "# Plan\n<!-- harness:plan v1 -->\n\n## Steps\n"
          "- [x] Session endpoint -> verify: pytest tests/test_session.py\n"
          "- [x] Webhook verify -> verify: make check\n"
          "- [ ] Split intents -> verify: pytest -k split\n")
    write(root / "docs" / "UNKNOWNS.md",
          "# Unknowns\n<!-- harness:unknowns v1 -->\n\n"
          "## Open decisions\n| ID | Decision | Options |\n|---|---|---|\n"
          "| D1 | datastore | A/B |\n| D2 | auth model | session/JWT |\n\n"
          "## Assumptions awaiting confirmation\n| ID | Assumption | Status |\n|---|---|---|\n"
          "| A1 | idempotency 24h | unverified |\n\n"
          "## Blindspot findings\n| ID | Finding | Where |\n|---|---|---|\n"
          "| B1 | coupon table no FK | legacy |\n\n"
          "## Preference gaps\n| ID | Area | Variants |\n|---|---|---|\n")
    write(root / "docs" / "DECISIONS.md",
          "# Decisions\n<!-- harness:decisions v1 -->\n\n"
          "## 2026-07-01 — DEC-1: Tier M\n- **Context:** setup\n- **revisit_when:** vendored code appears\n\n"
          "## 2026-07-02 — DEC-2: Datastore = Postgres\n- **Context:** scale\n"
          "- **revisit_when:** write throughput > 5k/s\n")

    story_data = [
        ("S-1", "done", "R1.c1", "\nartifact: docs/evidence/s1.txt"),
        ("S-2", "done", "R2.c2", "\nartifact: docs/evidence/s2.txt"),
        ("S-3", "in-progress", "R2.c1", ""),
        ("S-4", "in-progress", "R2.c3", "\nverify_cmd: pytest -k fraud"),
        ("S-5", "planned", "R1.c2", ""),
    ]
    for sid, status, ref, extra in story_data:
        write(root / "docs" / "stories" / f"{sid}.md",
              f"---\nid: {sid}\ntitle: {sid} work item\nstatus: {status}\n"
              f"prd_refs: [{ref}]{extra}\n---\n# {sid}\n")
    gen = subprocess.run(
        [sys.executable, str(GEN_STATUS), str(root / "docs" / "stories")],
        capture_output=True, text=True, check=True,
    )
    write(root / "docs" / "STATUS.md", gen.stdout)

    write(root / "docs" / "audits" / "audit-2026-07-06.md",
          "# Phase audit — 2026-07-06\n\n"
          "| # | Check | Result | Evidence |\n|---|-------|--------|----------|\n"
          "| 1 | Presence & wiring | PASS | ok |\n| 2 | Rules unweakened | PASS | ok |\n"
          "| 3 | Guards fire | PASS | ok |\n| 4 | Status honesty | PARTIAL | reviewer offline |\n"
          "| 5 | Drift sweep | PASS | ok |\n| 6 | Retro | n/a | — |\n| 7 | Report | done | — |\n\n"
          "## Findings\n1. S-3 in-progress with no evidence artifact.\n\n"
          "## Verdict\nPROCEED-WITH-FIXES\n")

    write(root / "vendor" / "lib.py", "x = 1\n")
    write(root / ".claude" / "settings.json", json.dumps(SETTINGS, indent=2))

    # Manifest last: hash comes from the shipped --hash-rules over the CLAUDE.md written above.
    h = subprocess.run(
        [sys.executable, str(SELFTEST), "--hash-rules", str(root)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    manifest = {
        "harness_version": 1,
        "tier": "M",
        "installed": "2026-07-09",
        "check_command": "make check",
        "components": [
            "CLAUDE.md", "docs/PRD.md", "docs/HARNESS.md", "docs/UNKNOWNS.md",
            "docs/PLAN.md", "docs/DECISIONS.md", "docs/ACTIVE.md",
            "scripts/harness_selftest.py", "scripts/gen_status.py",
        ],
        "hooks": {
            "enabled": list(HOOKS),
            "protected_paths": ["vendor"],
            "gated_statuses": ["done"],
            "evidence_keys": ["verify_cmd", "result", "artifact"],
            "story_glob": "docs/stories/*.md",
        },
        "generated_docs": {"docs/STATUS.md": "python3 scripts/gen_status.py docs/stories"},
        "core_rules_sha256": h,
    }
    write(root / ".claude" / "harness.json", json.dumps(manifest, indent=2))


def edit(path: Path, fn):
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")


def edit_json(path: Path, fn):
    obj = json.loads(path.read_text(encoding="utf-8"))
    fn(obj)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def tamper(golden: Path, name: str, mutate, expect=None):
    with tempfile.TemporaryDirectory(prefix="ph-tamper-") as d:
        t = Path(d) / "install"
        shutil.copytree(golden, t)
        mutate(t)
        rc, out = run_selftest(t)
        ok = rc == 1 and (expect is None or expect in out)
        check(ok, f"tamper caught: {name} (exit {rc})", out if not ok else "")


def expect_pass(golden: Path, name: str, mutate):
    """A benign mutation must NOT trip the self-test (guards against over-firing)."""
    with tempfile.TemporaryDirectory(prefix="ph-ok-") as d:
        t = Path(d) / "install"
        shutil.copytree(golden, t)
        mutate(t)
        rc, out = run_selftest(t)
        check(rc == 0, f"benign mutation still PASSes: {name} (exit {rc})", out if rc else "")


def _unwire(t: Path):
    def drop(obj):
        hooks = obj["hooks"]["PreToolUse"][0]["hooks"]
        obj["hooks"]["PreToolUse"][0]["hooks"] = [h for h in hooks if "secret_scan.py" not in h["command"]]
    edit_json(t / ".claude" / "settings.json", drop)


def _mask_exit(t: Path):
    """Weaken a hook by masking its exit code in settings.json — the file still
    fires when run directly, but the wired command swallows the block."""
    def mask(obj):
        for h in obj["hooks"]["PreToolUse"][0]["hooks"]:
            if "secret_scan.py" in h["command"]:
                h["command"] += " || exit 0"
    edit_json(t / ".claude" / "settings.json", mask)


def direct_payloads(golden: Path):
    """FIX 3 + FIX 4: hooks must read MultiEdit/NotebookEdit surfaces, and secret_scan
    must catch prefixes on {{ }} lines while freeing benign hyphenated sk- strings."""
    src = str(golden / "src" / "config.py")
    nb = str(golden / "src" / "cells.ipynb")
    story = str(golden / "docs" / "stories" / "S-plant.md")
    vend = str(golden / "vendor" / "x.py")
    vend_nb = str(golden / "vendor" / "cells.ipynb")
    akia = 'aws_key = "AKIA1234567890ABCDEF"'
    evless = '---\nid: S-plant\nstatus: done\nverify_cmd: ""\nresult: ""\n---\n'

    check(run_hook("secret_scan.py", {"tool_name": "MultiEdit", "tool_input": {
        "file_path": src, "edits": [{"old_string": "", "new_string": akia}]}}) == 2,
        "secret_scan catches AKIA in MultiEdit edits[].new_string")
    check(run_hook("secret_scan.py", {"tool_name": "NotebookEdit", "tool_input": {
        "notebook_path": nb, "new_source": akia}}) == 2,
        "secret_scan catches AKIA in NotebookEdit new_source (notebook_path)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'aws_key = "AKIA1234567890ABCDEF"  # {{ template }}'}}) == 2,
        "secret_scan still catches AKIA on a {{ }} line (F2: still-caught)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'css_class = "sk-loading-spinner-container"'}}) == 0,
        "secret_scan frees benign sk-loading-spinner-container (F2: no false positive)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'OPENAI_KEY = "sk-EXAMPLE_not-a-real_key-for-tests_only-0123456789abcd"'}}) == 2,
        "secret_scan catches a modern sk- key with -/_ in the body (F2: no regression on real keys)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'api_key = "{{ vault_openai_api_key }}"'}}) == 0,
        "secret_scan frees a bare {{ }} template placeholder assignment (F2: no new false positive)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'api_key = "aB3xK9mQ2pL7vT4wR8nZ6yH1sD5fG0jC"  # {{ note }}'}}) == 2,
        "secret_scan blocks a high-entropy secret even with a {{ }} comment (value-scoped sanction, not line)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'model = "sk-0123456789abcdef0123456789abcdef"'}}) == 2,
        "secret_scan catches a bare 32-char sk- provider key (floor 32, not 40)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'aws_access_key_id = "ASIA1234567890ABCDEF"'}}) == 2,
        "secret_scan catches an ASIA STS access key (not just AKIA)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'api_key: str = "aB3xK9mQ2pL7vT4wR8nZ6yH1sD5fG0jC"'}}) == 2,
        "secret_scan catches a type-annotated assignment (name: type = value)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'api_key = "aB3xK9mQ2pL7vT4wR8nZ6yH1sD5fG0jC${BYPASS}"'}}) == 2,
        "secret_scan blocks a real secret with a ${...} suffix (residue-judged, not substring-sanctioned)")
    check(run_hook("secret_scan.py", {"tool_name": "Write", "tool_input": {
        "file_path": src, "content": 'private_key = "aB3xK9mQ2pL7vT4wR8nZ6yH1sD5fG0jC"'}}) == 2,
        "secret_scan catches a private_key-named assignment")
    check(run_hook("status_guard.py", {"tool_name": "MultiEdit", "tool_input": {
        "file_path": story, "edits": [{"old_string": "", "new_string": evless}]}}) == 2,
        "status_guard catches evidence-less gated status in MultiEdit edits[].new_string")
    check(run_hook("status_guard.py", {"tool_name": "Write", "tool_input": {
        "file_path": story,
        "content": '---\nid: S-plant\nstatus : done\nverify_cmd: ""\nresult: ""\n---\n'}}) == 2,
        "status_guard catches 'status :' with whitespace before the colon")
    check(run_hook("status_guard.py", {"tool_name": "Write", "tool_input": {
        "file_path": story,
        "content": '---\nid: S-plant\nStatus: done\nverify_cmd: ""\nresult: ""\n---\n'}}) == 2,
        "status_guard catches a capitalized 'Status:' key")
    check(run_hook("status_guard.py", {"tool_name": "Edit", "tool_input": {
        "file_path": story, "old_string": "x",
        "new_string": "status: done means the work is verified in prose."}}) == 0,
        "status_guard ignores prose that merely contains 'status: done ...' (no false positive)")
    check(run_hook("protected_paths.py", {"tool_name": "MultiEdit", "tool_input": {
        "file_path": vend, "edits": [{"old_string": "", "new_string": "x = 1"}]}}) == 2,
        "protected_paths catches a MultiEdit under a protected path")
    check(run_hook("protected_paths.py", {"tool_name": "NotebookEdit", "tool_input": {
        "notebook_path": vend_nb, "new_source": "x = 1"}}) == 2,
        "protected_paths catches a NotebookEdit (notebook_path) under a protected path")


def run_dashboard(root: Path) -> str:
    p = subprocess.run([sys.executable, str(GEN_DASH), str(root)],
                       capture_output=True, text=True, timeout=60)
    check(p.returncode == 0, f"gen_dashboard exits 0 (got {p.returncode})", p.stderr)
    return p.stdout


def dashboard_tests(golden: Path):
    """gen_dashboard: complete standalone doc, self-contained, panels render,
    deterministic, and degrades at tier S."""
    html = run_dashboard(golden)
    check(html.startswith("<!DOCTYPE html>") and "</html>" in html,
          "dashboard is a complete standalone document")
    for bad in ('="http://', '="https://', "@import", "url(http", "<script src", "<link "):
        check(bad not in html, f"self-contained: no {bad!r}")
    check('class="board"' in html and "S-1" in html and "S-3" in html,
          "work-item board renders real stories")
    check("S-plant" not in html, "board shows only real stories, not plant fixtures")
    check('class="clauses"' in html and "R2.c1" in html, "PRD coverage renders clauses")
    check("PROCEED" in html, "latest-audit verdict is shown")
    check("revisit_when" in html and "DUE NOW" not in html,
          "decisions listed for review, no fabricated 'due' verdict")
    check("Open decisions" in html, "unknowns quadrants render")
    check(run_dashboard(golden) == html, "dashboard is byte-deterministic across runs")
    with tempfile.TemporaryDirectory(prefix="ph-dash-s-") as d:
        t = Path(d) / "s"
        shutil.copytree(golden, t)
        shutil.rmtree(t / "docs" / "stories")
        edit_json(t / ".claude" / "harness.json", lambda o: o.__setitem__("tier", "S"))
        h2 = run_dashboard(t)
        check('class="board"' not in h2, "board omitted at tier S (no stories)")
        check(h2.startswith("<!DOCTYPE html>") and "</html>" in h2,
              "tier-S dashboard still renders")
    with tempfile.TemporaryDirectory(prefix="ph-dash-a-") as d:
        t = Path(d) / "a"
        shutil.copytree(golden, t)
        write(t / "docs" / "audits" / "audit-draft.md", "# draft\n## Verdict\nBLOCKED\n")
        h3 = run_dashboard(t)
        check("PROCEED" in h3,
              "latest-audit panel keeps the dated audit, not a non-dated audit-draft.md")


def gen_status_tests():
    """gen_status: a table cell containing '|' must not corrupt the Markdown table."""
    with tempfile.TemporaryDirectory(prefix="ph-gs-") as d:
        sd = Path(d) / "stories"
        write(sd / "S-1.md", "---\nid: S-1\nstatus: done\ntitle: A | B danger\n---\n")
        gs = subprocess.run([sys.executable, str(GEN_STATUS), str(sd)],
                            capture_output=True, text=True)
        check("A \\| B danger" in gs.stdout,
              "gen_status escapes '|' in a title cell (no table corruption)")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ph-golden-") as d:
        golden = Path(d) / "install"
        build_golden(golden)

        rc, out = run_selftest(golden)
        check(rc == 0, f"golden tier-M install passes the self-test (exit {rc})", out if rc else "")
        for name in ["plant: protected paths", "plant: secret scan", "plant: status guard"]:
            check(plant_passed(out, name), f"{name} fired in the golden install", out)

        tamper(golden, "soften a core rule (hash mismatch)",
               lambda t: edit(t / "CLAUDE.md",
                              lambda s: s.replace("3. Minimum code that solves the problem.",
                                                  "3. Maximum code, ship fast.")),
               "core-rules hash")
        tamper(golden, "hollow out a hook (plant violation accepted)",
               lambda t: write(t / ".claude" / "hooks" / "secret_scan.py", "import sys\nsys.exit(0)\n"),
               "HOLLOW GUARD")
        tamper(golden, "unwire a hook from settings.json", _unwire,
               "not in settings.json")
        tamper(golden, "G1: enabled hook deleted, settings line remains",
               lambda t: os.remove(t / ".claude" / "hooks" / "status_guard.py"),
               "not installed on disk")
        tamper(golden, "stale generated STATUS.md",
               lambda t: edit(t / "docs" / "STATUS.md", lambda s: s + "\n| tampered | 9 |\n"),
               "STALE")
        tamper(golden, "unfilled descriptive placeholder in an installed doc",
               lambda t: edit(t / "docs" / "PRD.md", lambda s: s + "\n### R1 — {{requirement title}}\n"),
               "unfilled template placeholder")
        tamper(golden, "unfilled placeholder token in the manifest",
               lambda t: edit_json(t / ".claude" / "harness.json",
                                   lambda o: o.__setitem__("installed", "{{DATE}}")),
               "manifest placeholder")
        tamper(golden, "CLAUDE.md bloat past 40 lines",
               lambda t: edit(t / "CLAUDE.md", lambda s: s + "\n".join(f"line {i}" for i in range(50))),
               "bloat is drift")
        tamper(golden, "core-rules delimiter markers removed",
               lambda t: edit(t / "CLAUDE.md",
                              lambda s: s.replace("<!-- harness:core-rules:begin -->\n", "")
                                         .replace("\n<!-- harness:core-rules:end -->", "")),
               "delimiter markers missing")
        tamper(golden, "tier-M section not pruned on a tier-S install",
               lambda t: (edit_json(t / ".claude" / "harness.json",
                                    lambda o: o.__setitem__("tier", "S")),
                          edit(t / "docs" / "HARNESS.md", lambda s: s + f"\n<!-- {PRUNE_MARKER} -->\n")),
               PRUNE_MARKER)
        tamper(golden, "ASSIGN/MultiEdit detector removed (PREFIXES-only hook)",
               lambda t: write(t / ".claude" / "hooks" / "secret_scan.py", PREFIXES_ONLY_HOOK),
               "entropy assign")
        tamper(golden, "exit-code-masked hook wiring (settings appends || exit 0)",
               _mask_exit, "HOLLOW GUARD")

        # Negative: the narrowed placeholder scan must NOT fire on spaced Jinja.
        expect_pass(golden, "spaced Jinja {{ user.name }} in a doc is not a placeholder",
                    lambda t: edit(t / "docs" / "PRD.md", lambda s: s + "\nExample: {{ user.name }}\n"))

        direct_payloads(golden)
        dashboard_tests(golden)
        gen_status_tests()

    print()
    if FAILURES:
        print(f"SYNTHETIC SELF-TEST: FAIL — {len(FAILURES)} assertion(s) failed:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("SYNTHETIC SELF-TEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
