#!/usr/bin/env python3
"""Generate a self-contained HTML status dashboard from a project's harness state.

    python3 scripts/gen_dashboard.py <project-root> > docs/status.html

One standalone HTML file (inline CSS/JS, system fonts — no external deps, no
claude.ai/Artifact, works in any browser and under any agent). Read-only.
Deterministic and timestamp-free so the self-test freshness gate can cover it:
identical harness files → identical bytes. Every panel derives from a structured
signal; a missing/unparseable source omits its panel rather than guessing. Stdlib
only; self-contained (does not import gen_status.py).
"""
import html
import json
import os
import re
import sys

esc = html.escape

# Fixed lane order for the work-item board; unknown statuses append after.
LANE_ORDER = ["backlog", "planned", "in-progress", "done", "verified"]
STATUS_CLASS = {
    "backlog": "st-backlog", "planned": "st-planned",
    "in-progress": "st-progress", "done": "st-done", "verified": "st-done",
}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
    return v.strip("'\"")


def frontmatter(text):
    """Tiny YAML-ish frontmatter parser: top-level scalars/inline-lists plus one
    level of nesting (e.g. an `evidence:` block). Not a general YAML parser."""
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.DOTALL)
    fm = {}
    if not m:
        return fm
    block_key = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        mo = re.match(r"^(\s*)([\w_]+):\s*(.*)$", line)
        if not mo:
            continue
        indent, key, val = mo.group(1), mo.group(2), mo.group(3)
        if not indent:
            if val.strip() == "":
                fm[key] = {}
                block_key = key
            else:
                fm[key] = _scalar(val)
                block_key = None
        elif block_key and isinstance(fm.get(block_key), dict):
            fm[block_key][key] = _scalar(val)
    return fm


def stories(root):
    d = os.path.join(root, "docs", "stories")
    out = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith(".md"):
                out.append(frontmatter(read(os.path.join(d, name))))
    return out


# ---- panel builders (each returns an HTML fragment, or "" to omit) ----

def _evidence_chip(fm):
    ev = fm.get("evidence") if isinstance(fm.get("evidence"), dict) else {}

    def g(k):  # evidence may be nested under evidence: or flat at top level
        return ev.get(k) or fm.get(k)

    status = str(fm.get("status", ""))
    if g("artifact"):
        return '<span class="ev ok">evidence &check;</span>'
    if g("verify_cmd") or g("result"):
        return '<span class="ev test">test committed</span>'
    if status in ("in-progress", "done", "verified"):
        return '<span class="ev no">no evidence</span>'
    return ""


def board(items):
    if not items:
        return ""
    by_status = {}
    for fm in items:
        by_status.setdefault(str(fm.get("status", "?")), []).append(fm)
    lanes = [s for s in LANE_ORDER if s in by_status]
    lanes += sorted(s for s in by_status if s not in LANE_ORDER)
    cols = []
    for st in lanes:
        cards = []
        for fm in by_status[st]:
            sid = esc(str(fm.get("id", "?")))
            title = esc(str(fm.get("title") or fm.get("id", "")))
            refs = fm.get("prd_refs") or []
            if isinstance(refs, str):
                refs = [refs]
            tags = "".join(f'<span class="tag">{esc(str(r))}</span>' for r in refs)
            cards.append(
                f'<article class="card {STATUS_CLASS.get(st, "")}">'
                f'<div class="cid"><span>{sid}</span></div>'
                f'<div class="ct">{title}</div>'
                f'<div class="cf">{tags}{_evidence_chip(fm)}</div></article>'
            )
        cols.append(
            f'<div class="lane"><div class="lh"><span class="name">{esc(st)}</span>'
            f'<span class="ct num">{len(by_status[st])}</span></div>'
            f'<div class="cards">{"".join(cards)}</div></div>'
        )
    return (
        '<section class="panel col-8"><div class="phead"><h2>Work items</h2>'
        '<div class="filter" role="group" aria-label="Filter work items">'
        '<button id="f-all" aria-pressed="true" onclick="filterBoard(true)">All</button>'
        '<button id="f-ev" aria-pressed="false" onclick="filterBoard(false)">Needs evidence</button>'
        f'</div></div><div class="board">{"".join(cols)}</div></section>'
    )


def _clauses(root):
    p = os.path.join(root, "docs", "PRD.md")
    if not os.path.isfile(p):
        return None
    return sorted(set(re.findall(r"\bR\d+\.c\d+\b", read(p))))


def prd_panel(root, items):
    clauses = _clauses(root)
    if not clauses:
        return ""
    referenced = set()
    for fm in items:
        refs = fm.get("prd_refs") or []
        referenced.update([refs] if isinstance(refs, str) else refs)
    covered = [c for c in clauses if c in referenced]
    chips = "".join(
        f'<span class="clause {"cov" if c in referenced else "unc"}">{esc(c)}</span>'
        for c in clauses
    )
    pct = round(100 * len(covered) / len(clauses), 1)
    return (
        '<section class="panel col-7"><div class="phead"><h2>PRD clause coverage</h2>'
        f'<span class="meta"><span class="num">{len(covered)}</span>/'
        f'<span class="num">{len(clauses)}</span> referenced by a story</span></div>'
        f'<div class="clauses">{chips}</div>'
        f'<div class="barmeter"><span style="width:{pct}%"></span></div></section>'
    )


def _plan(root):
    p = os.path.join(root, "docs", "PLAN.md")
    if not os.path.isfile(p):
        return None
    text = read(p)
    steps = re.findall(r"^\s*(?:- \[([ xX])\]|\d+\.)\s+(.*)$", text, re.MULTILINE)
    if not steps:
        return None
    total = len(steps)
    done = sum(1 for mark, _ in steps if mark.lower() == "x")
    with_verify = sum(1 for _, body in steps if "verify:" in body)
    return total, done, with_verify, [b for _, b in steps]


def plan_panel(root):
    info = _plan(root)
    if not info:
        return ""
    total, done, with_verify, bodies = info
    rows = []
    for b in bodies[:6]:
        b = re.sub(r"\s+", " ", b).strip()
        vf = ""
        vm = re.search(r"(?:&rarr;|->|→)?\s*verify:\s*(.+)$", b)
        if vm:
            vf = f'<div class="vf">verify: {esc(vm.group(1)[:70])}</div>'
            b = b[: vm.start()].strip(" —-") or b
        rows.append('<div class="step"><div class="mk"></div>'
                    f'<div class="body"><div class="t">{esc(b[:90])}</div>{vf}</div></div>')
    label = (f"{done}/{total} done" if done else f"{with_verify}/{total} with verify")
    pct = round(100 * (done or with_verify) / total, 1) if total else 0
    return (
        '<section class="panel col-6"><div class="phead"><h2>Plan progress</h2>'
        f'<span class="meta">{label}</span></div>'
        f'<div class="steps">{"".join(rows)}</div>'
        f'<div class="barmeter"><span style="width:{pct}%"></span></div></section>'
    )


QUADS = [
    ("Open decisions", "Open decisions"),
    ("Assumptions", "Assumptions awaiting"),
    ("Blindspots", "Blindspot"),
    ("Preferences", "Preference"),
]


def _quad_rows(section_text):
    ids = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            first = cells[0] if cells else ""
            if first and first.lower() not in ("id", "date", ""):
                ids.append(first)
    return ids


def unknowns_panel(root):
    p = os.path.join(root, "docs", "UNKNOWNS.md")
    if not os.path.isfile(p):
        return ""
    text = read(p)
    # split into (heading, body) sections
    parts = re.split(r"^##\s+(.*)$", text, flags=re.MULTILINE)
    sections = {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    total = 0
    qhtml = []
    for label, needle in QUADS:
        body = ""
        for head, b in sections.items():
            if needle.lower() in head.lower() and "resolution" not in head.lower():
                body = b
                break
        ids = _quad_rows(body)
        total += len(ids)
        lis = "".join(f'<li><span class="qid">{esc(i.split()[0])}</span></li>'
                      for i in ids[:3]) or '<li>&mdash; none open</li>'
        empty = " empty" if not ids else ""
        qhtml.append(
            f'<div class="q{empty}"><div class="qh"><span class="qn">{esc(label)}</span>'
            f'<span class="qc num">{len(ids)}</span></div><ul>{lis}</ul></div>'
        )
    return (
        '<section class="panel col-6"><div class="phead"><h2>Unknowns register</h2>'
        f'<span class="meta"><span class="num">{total}</span> open</span></div>'
        f'<div class="quad">{"".join(qhtml)}</div></section>'
    )


def decisions_panel(root):
    p = os.path.join(root, "docs", "DECISIONS.md")
    if not os.path.isfile(p):
        return ""
    text = read(p)
    blocks = re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]
    rows = []
    for blk in blocks:
        did = re.search(r"(DEC-\d+)", blk)
        rv = re.search(r"revisit_when:?\*{0,2}\s*(.+)", blk)
        if not (did and rv):
            continue
        title = blk.splitlines()[0]
        title = re.sub(r".*DEC-\d+:?\s*", "", title).strip() or did.group(1)
        cond = re.sub(r"\s+", " ", rv.group(1)).strip().rstrip(".")[:120]
        rows.append(
            f'<div class="drow"><div><div class="did">{esc(did.group(1))} &middot; {esc(title[:60])}</div>'
            f'<div class="dw"><span class="mono">revisit_when</span>: {esc(cond)}</div></div>'
            f'<span class="duepill">REVIEW</span></div>'
        )
    if not rows:
        return ""
    return (
        '<section class="panel col-5"><div class="phead"><h2>Decisions to review</h2>'
        f'<span class="meta"><span class="num">{len(rows)}</span> with revisit_when</span></div>'
        f'<div class="rows">{"".join(rows)}</div></section>'
    )


PILL = {"PASS": "pass", "PARTIAL": "partial", "DONE": "pass", "N/A": "na", "NA": "na"}


def _latest_audit(root):
    d = os.path.join(root, "docs", "audits")
    if not os.path.isdir(d):
        return None
    files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    return os.path.join(d, files[-1]) if files else None


def audit_panel(root):
    p = _latest_audit(root)
    if not p:
        return ""
    text = read(p)
    date = re.search(r"audit-(\d{4}-\d{2}-\d{2})", os.path.basename(p))
    verdict = re.search(r"\b(PROCEED-WITH-FIXES|PROCEED|BLOCKED)\b", text)
    checks = []
    for line in text.splitlines():
        m = re.match(r"\|\s*(\d)\s*\|\s*([^|]+?)\s*\|\s*(PASS|PARTIAL|BLOCKED|FAIL|n/a|N/A|done)\b",
                     line, re.IGNORECASE)
        if m:
            res = m.group(3)
            cls = PILL.get(res.upper(), "partial" if res.upper() != "PASS" else "pass")
            checks.append(f'<tr><td class="n">{m.group(1)}</td><td>{esc(m.group(2))}</td>'
                          f'<td class="r"><span class="pill {cls}">{esc(res.upper())}</span></td></tr>')
    finding = re.search(r"^(?:1\.|\-)\s+(.*)$", text[text.find("## Finding"):], re.MULTILINE) \
        if "## Finding" in text else None
    fhtml = ""
    if finding:
        fx = re.sub(r"[*`\[\]]", "", finding.group(1))
        fhtml = f'<div class="finding"><span class="fx">!</span><span>{esc(fx[:140])}</span></div>'
    vcls = {"PROCEED": "good", "PROCEED-WITH-FIXES": "warn", "BLOCKED": "crit"}.get(
        verdict.group(1) if verdict else "", "good")
    vtxt = esc(verdict.group(1)) if verdict else "—"
    meta = esc(date.group(1)) if date else ""
    return (
        '<section class="panel col-4"><div class="phead"><h2>Latest audit</h2>'
        f'<span class="meta mono">{meta}</span></div>'
        f'<div style="margin-bottom:11px"><span class="verdict {vcls}">{vtxt}</span></div>'
        f'<table class="checks">{"".join(checks)}</table>{fhtml}</section>'
    )


def kpis(items, prd, plan):
    tiles = []

    def tile(v, sub_v, label, sub, cls=""):
        tiles.append(f'<div class="kpi {cls}"><div class="v num">{v}{sub_v}</div>'
                     f'<div class="l">{esc(label)}</div><div class="sub">{esc(sub)}</div></div>')

    if items:
        done = sum(1 for f in items if str(f.get("status")) in ("done", "verified"))
        wip = sum(1 for f in items if str(f.get("status")) == "in-progress")
        tile(len(items), "", "Work items", f"{done} done · {wip} wip")
    if prd is not None:
        referenced = set()
        for f in items:
            r = f.get("prd_refs") or []
            referenced.update([r] if isinstance(r, str) else r)
        cov = len([c for c in prd if c in referenced])
        tile(cov, f'<small>/{len(prd)}</small>', "PRD clauses covered",
             f"{len(prd) - cov} uncovered", "" if cov == len(prd) else "s-warn")
    if plan:
        total, d, wv = plan[0], plan[1], plan[2]
        tile(d or wv, f'<small>/{total}</small>', "Plan steps",
             "verified" if d else "with verify")
    return ("<section class=\"kpis\">" + "".join(tiles) + "</section>") if tiles else ""


CSS = r"""
:root{--paper:#EFEBE2;--card:#F8F5EF;--sunk:#EAE5DA;--ink:#1C1A16;--muted:#6B675E;--faint:#918C81;
--line:#DAD5C8;--line-strong:#C9C3B4;--accent:#1F6F6A;--accent-soft:#DCEAE7;
--good:#4F7A3F;--good-soft:#E5EBDD;--warn:#B07A22;--warn-soft:#F0E6D2;--crit:#A23B32;--crit-soft:#F1DDD9;
--info:#3E6690;--info-soft:#DEE6EF;--radius:6px;--radius-sm:4px;
--sans:-apple-system,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--mono:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,monospace;
--shadow:0 1px 2px rgba(28,26,22,.05),0 4px 14px rgba(28,26,22,.05);}
@media (prefers-color-scheme:dark){:root{--paper:#17150F;--card:#201D16;--sunk:#191710;--ink:#ECE7DA;
--muted:#9A958A;--faint:#726D63;--line:#33302A;--line-strong:#403C34;--accent:#4FB3AC;--accent-soft:#183530;
--good:#7FA867;--good-soft:#20291A;--warn:#D19A3C;--warn-soft:#2E2413;--crit:#D06A5F;--crit-soft:#2E1815;
--info:#6E97C4;--info-soft:#141F2B;--shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.28);}}
:root[data-theme="light"]{--paper:#EFEBE2;--card:#F8F5EF;--sunk:#EAE5DA;--ink:#1C1A16;--muted:#6B675E;
--faint:#918C81;--line:#DAD5C8;--line-strong:#C9C3B4;--accent:#1F6F6A;--accent-soft:#DCEAE7;--good:#4F7A3F;
--good-soft:#E5EBDD;--warn:#B07A22;--warn-soft:#F0E6D2;--crit:#A23B32;--crit-soft:#F1DDD9;--info:#3E6690;
--info-soft:#DEE6EF;--shadow:0 1px 2px rgba(28,26,22,.05),0 4px 14px rgba(28,26,22,.05);}
:root[data-theme="dark"]{--paper:#17150F;--card:#201D16;--sunk:#191710;--ink:#ECE7DA;--muted:#9A958A;
--faint:#726D63;--line:#33302A;--line-strong:#403C34;--accent:#4FB3AC;--accent-soft:#183530;--good:#7FA867;
--good-soft:#20291A;--warn:#D19A3C;--warn-soft:#2E2413;--crit:#D06A5F;--crit-soft:#2E1815;--info:#6E97C4;
--info-soft:#141F2B;--shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.28);}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;
line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:26px 22px 60px}
.mono{font-family:var(--mono)}.num{font-variant-numeric:tabular-nums}
h1,h2,h3{margin:0;text-wrap:balance;font-weight:640;letter-spacing:-.01em}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:14px 20px;padding-bottom:18px;
border-bottom:1px solid var(--line);margin-bottom:22px}
.bar .id{display:flex;flex-direction:column;gap:3px;margin-right:auto}
.bar .id h1{font-size:23px;line-height:1.1}
.bar .facts{display:flex;flex-wrap:wrap;align-items:center;gap:10px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border:1px solid var(--line-strong);
border-radius:100px;background:var(--card);font-size:12.5px;white-space:nowrap}
.chip .k{color:var(--muted)}.chip.tier{font-family:var(--mono);font-weight:600}
.dot{width:8px;height:8px;border-radius:50%;flex:none}.dot.good{background:var(--good)}
.verdict{font-weight:600}.verdict.good{color:var(--good)}.verdict.warn{color:var(--warn)}.verdict.crit{color:var(--crit)}
.cmd{font-family:var(--mono);font-size:12px;color:var(--muted);background:var(--sunk);
border:1px solid var(--line);border-radius:var(--radius-sm);padding:3px 8px}
.tt{font:inherit;font-size:12px;cursor:pointer;background:var(--card);border:1px solid var(--line-strong);
border-radius:100px;padding:5px 11px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;margin-bottom:22px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:13px 14px;
box-shadow:var(--shadow);position:relative;overflow:hidden}
.kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent)}
.kpi.s-warn::before{background:var(--warn)}.kpi.s-crit::before{background:var(--crit)}.kpi.s-good::before{background:var(--good)}
.kpi .v{font-size:27px;font-weight:660;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi .v small{font-size:14px;font-weight:500;color:var(--muted)}
.kpi .l{font-size:11.5px;color:var(--muted);margin-top:7px}
.kpi .sub{font-size:11px;color:var(--faint);margin-top:2px;font-family:var(--mono)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
box-shadow:var(--shadow);padding:16px;min-width:0}
.col-8{grid-column:span 8}.col-7{grid-column:span 7}.col-6{grid-column:span 6}.col-5{grid-column:span 5}.col-4{grid-column:span 4}
.phead{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:13px}
.phead h2{font-size:14px}.phead .meta{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.filter{display:flex;gap:6px}
.filter button{font:inherit;font-size:11.5px;padding:3px 9px;border:1px solid var(--line-strong);
background:var(--card);color:var(--muted);border-radius:100px;cursor:pointer}
.filter button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.lane{background:var(--sunk);border:1px solid var(--line);border-radius:var(--radius);padding:9px;min-width:0}
.lane .lh{display:flex;align-items:center;justify-content:space-between;margin:2px 3px 9px}
.lane .lh .name{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.lane .lh .ct{font-size:11px;color:var(--faint);font-variant-numeric:tabular-nums}
.cards{display:flex;flex-direction:column;gap:8px}
.card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--faint);
border-radius:var(--radius-sm);padding:9px 10px}
.card.st-planned{border-left-color:var(--info)}.card.st-progress{border-left-color:var(--warn)}
.card.st-done{border-left-color:var(--good)}
.card .cid{font-family:var(--mono);font-size:11px;color:var(--muted)}
.card .ct{font-size:13px;margin:4px 0 7px;line-height:1.35}
.card .cf{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
.tag{font-family:var(--mono);font-size:10.5px;padding:1.5px 6px;border-radius:3px;background:var(--accent-soft);color:var(--accent)}
.ev{font-size:10.5px;padding:1.5px 6px;border-radius:3px;font-weight:600}
.ev.ok{background:var(--good-soft);color:var(--good)}.ev.no{background:var(--crit-soft);color:var(--crit)}
.ev.test{background:var(--info-soft);color:var(--info)}
.clauses{display:flex;flex-wrap:wrap;gap:6px}
.clause{font-family:var(--mono);font-size:11.5px;padding:3px 8px;border-radius:3px;border:1px solid var(--line-strong)}
.clause.cov{background:var(--accent-soft);color:var(--accent);border-color:transparent}
.clause.unc{color:var(--faint);border-style:dashed}
.barmeter{height:7px;background:var(--sunk);border-radius:100px;overflow:hidden;margin-top:12px;border:1px solid var(--line)}
.barmeter>span{display:block;height:100%;background:var(--accent)}
.steps{display:flex;flex-direction:column}
.step{display:grid;grid-template-columns:18px 1fr;gap:9px;align-items:start;padding:8px 0;border-top:1px solid var(--line)}
.step:first-child{border-top:0}
.step .mk{width:15px;height:15px;border-radius:50%;border:2px solid var(--line-strong);margin-top:2px}
.step.done .mk{background:var(--good);border-color:var(--good)}
.step .body .t{font-size:13px}
.step .body .vf{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:2px;overflow-wrap:anywhere}
.quad{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.q{background:var(--sunk);border:1px solid var(--line);border-radius:var(--radius-sm);padding:11px}
.q .qh{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:7px}
.q .qh .qn{font-size:12px;font-weight:600}.q .qh .qc{font-family:var(--mono);font-size:15px;font-variant-numeric:tabular-nums}
.q ul{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:5px}
.q li{font-size:11.5px;color:var(--muted)}.q li .qid{font-family:var(--mono);color:var(--ink);font-size:11px}
.q.empty .qc{color:var(--faint)}
.rows{display:flex;flex-direction:column;gap:10px}
.drow{display:flex;gap:10px;align-items:flex-start;padding:10px;background:var(--sunk);border:1px solid var(--line);
border-left:3px solid var(--warn);border-radius:var(--radius-sm)}
.drow .did{font-family:var(--mono);font-size:12px;font-weight:600}
.drow .dw{font-size:12px;color:var(--muted);margin-top:2px}
.duepill{margin-left:auto;font-size:10.5px;font-weight:600;color:var(--warn);background:var(--warn-soft);
padding:2px 8px;border-radius:100px;white-space:nowrap}
.checks{width:100%;border-collapse:collapse;font-size:12.5px}
.checks td{padding:6px 4px;border-top:1px solid var(--line)}.checks tr:first-child td{border-top:0}
.checks td.n{font-family:var(--mono);color:var(--faint);width:22px}.checks td.r{text-align:right;width:64px}
.pill{font-size:10.5px;font-weight:600;padding:2px 8px;border-radius:100px}
.pill.pass{background:var(--good-soft);color:var(--good)}.pill.partial{background:var(--warn-soft);color:var(--warn)}
.pill.na{background:var(--sunk);color:var(--faint)}
.finding{margin-top:12px;font-size:12px;color:var(--muted);display:flex;gap:8px;align-items:baseline}
.finding .fx{color:var(--warn);font-family:var(--mono);font-weight:700}
.foot{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);display:flex;flex-wrap:wrap;
gap:6px 16px;font-size:11.5px;color:var(--faint);font-family:var(--mono)}
.foot .g{color:var(--muted)}
a{color:var(--accent)}:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.hidden{display:none!important}
@media (max-width:900px){.col-8,.col-7,.col-6,.col-5,.col-4{grid-column:span 12}.board{grid-template-columns:repeat(2,1fr)}}
@media (max-width:560px){.board,.quad{grid-template-columns:1fr}}
"""

JS = """
function setTheme(t){document.documentElement.setAttribute('data-theme',t);}
function toggleTheme(){var r=document.documentElement;
var cur=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
setTheme(cur==='dark'?'light':'dark');}
function filterBoard(all){var a=document.getElementById('f-all'),e=document.getElementById('f-ev');
if(a){a.setAttribute('aria-pressed',all);e.setAttribute('aria-pressed',!all);}
document.querySelectorAll('.board .card').forEach(function(c){
c.classList.toggle('hidden',!all && !c.querySelector('.ev.no'));});}
"""


def render(root):
    manifest = os.path.join(root, ".claude", "harness.json")
    project = os.path.basename(os.path.abspath(root)) or "project"
    head = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>Harness Status — {esc(project)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n')
    if not os.path.isfile(manifest):
        return head + ('<div class="wrap"><p>No harness installed here '
                       '(<span class="mono">.claude/harness.json</span> missing).</p></div>\n'
                       '</body>\n</html>\n')
    try:
        cfg = json.loads(read(manifest))
    except Exception:
        cfg = {}
    items = stories(root)
    prd = _clauses(root)
    plan = _plan(root)

    tier = esc(str(cfg.get("tier", "?")))
    check = esc(str(cfg.get("check_command", "")))
    bar = (
        '<header class="bar"><div class="id">'
        '<span class="eyebrow">Project Harness &middot; Status</span>'
        f'<h1>{esc(project)}</h1></div><div class="facts">'
        f'<span class="chip tier"><span class="k">TIER</span> {tier}</span>'
        + (f'<span class="cmd">{check}</span>' if check else '')
        + '<button class="tt" onclick="toggleTheme()">Theme</button></div></header>'
    )
    panels = [board(items), audit_panel(root), prd_panel(root, items),
              decisions_panel(root), plan_panel(root), unknowns_panel(root)]
    grid = '<div class="grid">' + "".join(p for p in panels if p) + '</div>'
    foot = ('<footer class="foot"><span class="g">Generated by</span> scripts/gen_dashboard.py'
            '<span class="g">&middot; deterministic, self-contained &middot; regenerate:</span>'
            ' python3 scripts/gen_dashboard.py . &gt; docs/status.html</footer>')
    return (head + '<div class="wrap">' + bar + kpis(items, prd, plan)
            + grid + foot + '</div>\n<script>' + JS + '</script>\n</body>\n</html>\n')


def main():
    root = os.path.realpath(sys.argv[1] if len(sys.argv) > 1 else ".")
    sys.stdout.write(render(root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
