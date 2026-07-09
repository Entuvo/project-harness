#!/usr/bin/env python3
"""Harness self-test: prove the installed harness is present, unweakened, and firing.

    python3 harness_selftest.py <project-root>            full self-test (exit 1 on any FAIL)
    python3 harness_selftest.py --hash-rules <project-root>  print SHA-256 of the CLAUDE.md core-rules block

Why plant tests: a guard that has never been fed a fake violation must be
presumed hollow. Every check here verifies disk reality — never a document's
description of itself. Stdlib only.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

RESULTS = []

# An unfilled template placeholder: {{ immediately followed by a non-space, up to
# }}. Catches the skill's forms — {{TIER}} and {{descriptive prose}} alike — while
# skipping conventionally-spaced Jinja/handlebars ({{ user.name }}) a real doc may
# legitimately contain. Prose describing a placeholder must use the spaced form.
PLACEHOLDER = re.compile(r"\{\{\S[^}]*\}\}")


def record(status: str, name: str, detail: str = ""):
    RESULTS.append((status, name, detail))
    print(f"{status:7s} {name}" + (f" — {detail}" if detail else ""))


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def rules_block(claude_md_text: str):
    m = re.search(
        r"(<!-- harness:core-rules:begin.*?harness:core-rules:end -->)",
        claude_md_text,
        re.DOTALL,
    )
    return m.group(1) if m else None


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_hook(hook_path: str, payload: dict, env_extra=None) -> int:
    env = {k: v for k, v in os.environ.items() if k != "ALLOW_PROTECTED_EDIT"}
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            [sys.executable, hook_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        return proc.returncode
    except Exception:
        return -1


def run_wired(cmd: str, payload: dict, root: str) -> int:
    """Run the ACTUAL settings.json command (shell, cwd=root) with the plant payload.
    This is what Claude Code runs on every edit — so it catches exit-code masking
    (`… || true`) that invoking the hook file directly would sail right past."""
    env = {k: v for k, v in os.environ.items() if k != "ALLOW_PROTECTED_EDIT"}
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=root, input=json.dumps(payload),
            capture_output=True, text=True, timeout=15, env=env,
        )
        return proc.returncode
    except Exception:
        return -1


def wired_cmd(root: str, hook: str):
    """The settings.json command string that invokes `hook`, or None if unwired."""
    sp = os.path.join(root, ".claude", "settings.json")
    if not os.path.isfile(sp):
        return None
    try:
        obj = json.loads(read(sp))
    except Exception:
        return None
    found = []

    def walk(o):
        if isinstance(o, dict):
            for k, val in o.items():
                if k == "command" and isinstance(val, str) and f".claude/hooks/{hook}" in val:
                    found.append(val)
                else:
                    walk(val)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(obj)
    return found[0] if found else None


def plant(name: str, hook: str, violation: dict, clean: dict, root: str):
    """A healthy guard rejects the fake (exit 2) and allows the clean case (exit 0).
    Runs the wired settings command when present (catches exit-code masking), else
    the hook file directly."""
    path = os.path.join(root, ".claude", "hooks", hook)
    if not os.path.isfile(path):
        record("FAIL", name, f"hook not installed at .claude/hooks/{hook}")
        return
    cmd = wired_cmd(root, hook)
    if cmd:
        v = run_wired(cmd, violation, root)
        c = run_wired(cmd, clean, root)
    else:
        v = run_hook(path, violation)
        c = run_hook(path, clean)
    if v == 2 and c == 0:
        record("PASS", name, "rejected the plant, allowed the clean case")
    elif v != 2:
        record("FAIL", name, f"HOLLOW GUARD: plant violation exited {v}, expected 2")
    else:
        record("FAIL", name, f"guard blocks clean input (exit {c}) — miswired or overbroad")


def main() -> int:
    args = sys.argv[1:]
    hash_only = "--hash-rules" in args
    args = [a for a in args if a != "--hash-rules"]
    root = os.path.realpath(args[0] if args else ".")

    claude_md = os.path.join(root, "CLAUDE.md")
    if hash_only:
        block = rules_block(read(claude_md)) if os.path.isfile(claude_md) else None
        if not block:
            print("ERROR: no core-rules block found in CLAUDE.md", file=sys.stderr)
            return 1
        print(sha(block))
        return 0

    # 1. Manifest
    manifest_path = os.path.join(root, ".claude", "harness.json")
    if not os.path.isfile(manifest_path):
        record("FAIL", "manifest", ".claude/harness.json missing — no harness installed?")
        return finish()
    try:
        manifest_raw = read(manifest_path)
        cfg = json.loads(manifest_raw)
        record("PASS", "manifest", f"tier {cfg.get('tier', '?')}")
    except Exception as e:
        record("FAIL", "manifest", f"unparseable: {e}")
        return finish()

    # 1b. The manifest file itself must carry no unfilled template token.
    if PLACEHOLDER.search(manifest_raw):
        record("FAIL", "manifest placeholder",
               "unfilled template token (e.g. {{TIER}}) in .claude/harness.json")
    else:
        record("PASS", "manifest placeholder", "no unfilled tokens")

    # 2. Components exist, non-empty, placeholders filled, markers present, tier-pruned
    tier = cfg.get("tier")
    for comp in cfg.get("components", []):
        p = os.path.join(root, comp)
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            record("FAIL", f"component {comp}", "missing or empty")
            continue
        text = read(p)
        # Placeholder/marker/tier-prune checks apply to installed docs, not copied
        # scripts — a .py legitimately contains template tokens in its own source.
        if not comp.endswith(".py") and PLACEHOLDER.search(text):
            record("FAIL", f"component {comp}", "unfilled template placeholder (e.g. {{TIER}}) remains")
        elif comp.endswith(".md") and "<!-- harness:" not in text:
            record("FAIL", f"component {comp}", "harness marker comment missing")
        elif tier == "S" and not comp.endswith(".py") and "Delete on tier S" in text:
            record("FAIL", f"component {comp}",
                   "tier-M-only section left un-pruned (contains a 'Delete on tier S' marker) — "
                   "an installed doc describing enforcement this tier doesn't have")
        else:
            record("PASS", f"component {comp}")

    # 3. CLAUDE.md: length + rules hash
    if os.path.isfile(claude_md):
        text = read(claude_md)
        n = len(text.rstrip("\n").split("\n"))
        if n <= 40:
            record("PASS", "CLAUDE.md length", f"{n} lines (≤40)")
        else:
            record("FAIL", "CLAUDE.md length", f"{n} lines — bloat is drift; it stops being read")
        block = rules_block(text)
        want = cfg.get("core_rules_sha256", "")
        if not block:
            record("FAIL", "core-rules block", "delimiter markers missing — rules were edited away")
        elif "{{" in want or not want:
            record("FAIL", "core-rules hash", "manifest hash unset — run --hash-rules and record it")
        elif sha(block) == want:
            record("PASS", "core-rules hash", "block matches manifest — rules unweakened")
        else:
            record(
                "FAIL",
                "core-rules hash",
                "MISMATCH: rules changed without re-blessing. Authorized (DECISIONS.md entry)? "
                "→ update manifest hash. Not authorized? → restore the block.",
            )
    else:
        record("FAIL", "CLAUDE.md", "missing")

    # 4. Hook wiring: enabled-but-absent, installed-but-unwired, and wired-but-missing all fail.
    hooks_dir = os.path.join(root, ".claude", "hooks")
    installed_hooks = (
        [h for h in os.listdir(hooks_dir) if h.endswith(".py")] if os.path.isdir(hooks_dir) else []
    )
    settings_path = os.path.join(root, ".claude", "settings.json")
    settings = read(settings_path) if os.path.isfile(settings_path) else ""
    referenced = set(re.findall(r"\.claude/hooks/([\w.\-]+\.py)", settings))
    # hooks.enabled = the explicit contract: these MUST be present, wired, and plant-passing.
    # Absent (tier S / no hooks) → no expected hooks, backward compatible.
    enabled = (cfg.get("hooks") or {}).get("enabled") or []
    if installed_hooks or referenced or enabled:
        unwired = [h for h in installed_hooks if h not in referenced]
        phantom = [
            h for h in referenced
            if not os.path.isfile(os.path.join(hooks_dir, h))
            and f"test ! -f .claude/hooks/{h}" not in settings
        ]
        missing_enabled = [h for h in enabled if h not in installed_hooks]
        if missing_enabled:
            record("FAIL", "hook wiring",
                   f"manifest hooks.enabled lists hook(s) not installed on disk: {', '.join(missing_enabled)} "
                   "— a deleted hook whose 'test ! -f'-guarded settings line lingers would be silent-green. "
                   "Reinstall the hook, or drop it from hooks.enabled if retired.")
        elif unwired:
            record("FAIL", "hook wiring", f"installed but not in settings.json: {', '.join(unwired)}")
        elif phantom:
            record("FAIL", "hook wiring",
                   f"settings.json invokes missing hook(s) without a 'test ! -f' guard "
                   f"(would block every edit): {', '.join(phantom)}")
        else:
            detail = f"{len(installed_hooks)} hook(s) registered"
            if enabled:
                detail += f"; {len(enabled)} enabled and present"
            record("PASS", "hook wiring", detail)

    # 4b. Generated docs freshness: regenerate and diff against committed
    for target, cmd in (cfg.get("generated_docs") or {}).items():
        target_path = os.path.join(root, target)
        if not os.path.isfile(target_path):
            record("FAIL", f"generated {target}", "listed in manifest but missing on disk")
            continue
        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=30
            )
            if proc.returncode != 0:
                record("FAIL", f"generated {target}", f"generator failed (exit {proc.returncode})")
            elif proc.stdout.strip() == read(target_path).strip():
                record("PASS", f"generated {target}", "committed copy matches regeneration")
            else:
                record("FAIL", f"generated {target}",
                       "STALE: committed copy differs from regeneration — a stale generated "
                       f"doc is a lie in progress. Regenerate: {cmd} > {target}")
        except Exception as e:
            record("FAIL", f"generated {target}", f"could not regenerate: {e}")

    # 5. Plant tests — feed each guard a fake violation
    hooks_cfg = cfg.get("hooks") or {}
    protected = hooks_cfg.get("protected_paths") or []
    if "protected_paths.py" in installed_hooks:
        if protected:
            plant(
                "plant: protected paths",
                "protected_paths.py",
                {"tool_name": "Write", "tool_input": {
                    "file_path": os.path.join(root, protected[0], "plant_violation.py"),
                    "content": "x = 1"}},
                {"tool_name": "Write", "tool_input": {
                    "file_path": os.path.join(root, "docs", "plant_clean.md"),
                    "content": "hello"}},
                root,
            )
        else:
            record("SKIP", "plant: protected paths", "no protected_paths configured in manifest")
    if "secret_scan.py" in installed_hooks:
        cfg_py = os.path.join(root, "src", "config.py")
        plant(
            "plant: secret scan",
            "secret_scan.py",
            {"tool_name": "Write", "tool_input": {
                "file_path": cfg_py, "content": 'aws_key = "AKIA1234567890ABCDEF"'}},
            {"tool_name": "Write", "tool_input": {
                "file_path": cfg_py, "content": 'aws_key = os.environ["AWS_KEY"]'}},
            root,
        )
        # Second detector: high-entropy assignment (proves the ASSIGN branch is live).
        plant(
            "plant: secret scan (entropy assign)",
            "secret_scan.py",
            {"tool_name": "Write", "tool_input": {
                "file_path": cfg_py, "content": 'api_key = "aB3xK9mQ2pL7vT4wR8nZ6yH1sD5fG0jC"'}},
            {"tool_name": "Write", "tool_input": {
                "file_path": cfg_py, "content": 'api_key = os.environ["API_KEY"]'}},
            root,
        )
        # MultiEdit shape: the secret must be read from edits[].new_string, not just content.
        plant(
            "plant: secret scan (MultiEdit)",
            "secret_scan.py",
            {"tool_name": "MultiEdit", "tool_input": {
                "file_path": cfg_py,
                "edits": [{"old_string": "", "new_string": 'aws_key = "AKIA1234567890ABCDEF"'}]}},
            {"tool_name": "MultiEdit", "tool_input": {
                "file_path": cfg_py,
                "edits": [{"old_string": "", "new_string": 'aws_key = os.environ["AWS_KEY"]'}]}},
            root,
        )
    if "status_guard.py" in installed_hooks:
        glob = hooks_cfg.get("story_glob", "docs/stories/*.md")
        story = os.path.join(root, glob.replace("*", "S-plant"))
        gated = (hooks_cfg.get("gated_statuses") or ["done"])[0]
        plant(
            "plant: status guard",
            "status_guard.py",
            # Sneaky case: gated status with the template's empty-quoted evidence defaults.
            {"tool_name": "Write", "tool_input": {
                "file_path": story,
                "content": f'---\nid: S-plant\nstatus: {gated}\nverify_cmd: ""\nresult: ""\n---\n'}},
            {"tool_name": "Write", "tool_input": {
                "file_path": story,
                "content": f"---\nid: S-plant\nstatus: {gated}\nverify_cmd: make check\nresult: exit 0\n---\n"}},
            root,
        )
        # MultiEdit shape: the status/evidence must be read from edits[].new_string.
        plant(
            "plant: status guard (MultiEdit)",
            "status_guard.py",
            {"tool_name": "MultiEdit", "tool_input": {
                "file_path": story,
                "edits": [{"old_string": "", "new_string":
                           f'---\nid: S-plant\nstatus: {gated}\nverify_cmd: ""\nresult: ""\n---\n'}]}},
            {"tool_name": "MultiEdit", "tool_input": {
                "file_path": story,
                "edits": [{"old_string": "", "new_string":
                           f"---\nid: S-plant\nstatus: {gated}\nverify_cmd: make check\nresult: exit 0\n---\n"}]}},
            root,
        )

    return finish()


def finish() -> int:
    fails = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"\n{len([r for r in RESULTS if r[0] == 'PASS'])} pass, "
          f"{len(fails)} fail, {len([r for r in RESULTS if r[0] == 'SKIP'])} skip")
    if fails:
        print("HARNESS SELF-TEST: FAIL — a failing guard is a hollow guard; fix before proceeding.")
        return 1
    print("HARNESS SELF-TEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
