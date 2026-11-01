"""HTML session report: each finding with the check that confirmed it and its design rule.

Standard library only. Reads a run's session.json and checks.json, so it also works on old runs:
    python3 agent/report_html.py runs/<run> [--level vault]
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from report import describe_step  # noqa: E402

_STOP = set("the a an and or of to in on is it its with when while that this be are not "
            "no any by from at as for only can".split())


def _words(text):
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)  # GemBundle -> Gem Bundle
    # shortcut: crude stem (drop a final s, keep 5 letters); upgrade if docs get longer
    return {w.rstrip("s")[:5] for w in re.findall(r"[a-z]+|\d+", text.lower())
            if w not in _STOP}


def rule_blocks(design_text):
    """The design document's paragraphs and bullets; a bullet keeps its lead-in ("...count:")."""
    blocks, lead = [], ""
    for para in re.split(r"\n\s*\n", design_text):
        if para.lstrip().startswith("#"):
            lead = ""
            continue
        parts = [" ".join(p.split()) for p in re.split(r"(?:^|\n)\s*[-*]\s+", para.strip())]
        if parts[0].endswith(":") and len(parts) == 1:
            lead = parts[0]  # bullets follow in the next paragraph
            continue
        if parts[0].endswith(":"):
            lead, parts = parts[0], parts[1:]
        elif parts[0]:
            lead = ""
        blocks += [f"{lead} {p}".strip() for p in parts if p]
    return blocks


def closest_rule(description, blocks):
    """The block that best matches the check's description, rare words counting more; or None."""
    sets = [_words(b) for b in blocks]
    df = {w: sum(w in s for s in sets) for s in sets for w in s}
    want = _words(description)
    scores = [sum(1 / df[w] for w in want & s) for s in sets]
    if not scores or max(scores) == 0:
        return None
    return blocks[scores.index(max(scores))]


def _status(verdict):
    runs = verdict.get("runs", [])
    hits = sum(1 for r in runs if r)
    if verdict.get("confirmed"):
        return "confirmed", f"Confirmed: {hits}/{len(runs)} replays reproduced it"
    if 0 < hits < len(runs):
        return "flaky", f"Flaky, not confirmed: {hits}/{len(runs)} replays"
    return "rejected", f"Rejected: {verdict.get('reason', '')}"


def _finding(f, checks, rules):
    e = html.escape
    kind, status = _status(f.get("verdict") or {})
    check = checks.get(f.get("invariant"))
    rule = closest_rule(f.get("invariant_description", ""), rules) if rules else None
    out = [f'<section class="finding {kind}">',
           f'<div class="badge">{e(status)}</div>',
           f'<h3>{e(f.get("title", ""))}</h3>']
    if rule:
        out.append(f'<p class="label">Design document</p><blockquote>{e(rule)}</blockquote>')
    out.append(f'<p class="label">Check written by the model</p>'
               f'<p><code>{e(str(f.get("invariant", "")))}</code>: '
               f'{e(f.get("invariant_description", ""))}</p>')
    if check:
        out.append(f'<details><summary>Check JSON</summary><pre>'
                   f'{e(json.dumps(check["violation"], indent=1))}</pre></details>')
    if f.get("hypothesis"):
        out.append(f'<p class="label">What the explorer saw</p><p>{e(f["hypothesis"])}</p>')
    steps = "".join(f"<li>{e(describe_step(s))}</li>" for s in f.get("steps", []))
    out.append(f'<p class="label">Repro, from a fresh level load</p><ol>{steps}</ol>')
    if f.get("video_mp4"):
        out.append(f'<video src="{e(f["video_mp4"])}" controls muted loop></video>')
    shots = [(k, f.get(k)) for k in ("before", "after") if f.get(k)]
    if shots:
        out.append('<div class="shots">' + "".join(
            f'<figure><img src="{e(p)}" alt="{k}"><figcaption>{k}</figcaption></figure>'
            for k, p in shots) + "</div>")
    out.append("</section>")
    return "\n".join(out)


CSS = """
:root{--bg:#0f1115;--card:#181b22;--fg:#e8eaf0;--mute:#9aa1b2;--ok:#e5484d;--no:#5b6170;
--flaky:#f5a524;--accent:#7c9cff}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.5 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 16px}
h1{font-size:30px;margin:0 0 4px}h2{margin:40px 0 12px;font-size:22px}
.meta{color:var(--mute)}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}
.stat{background:var(--card);border-radius:10px;padding:12px 18px}
.stat b{display:block;font-size:26px}
.finding{background:var(--card);border-radius:12px;padding:20px 24px;margin:16px 0;
border-left:6px solid var(--no)}
.finding.confirmed{border-left-color:var(--ok)}.finding.flaky{border-left-color:var(--flaky)}
.badge{font-weight:600;color:var(--mute)}.confirmed .badge{color:var(--ok)}
.flaky .badge{color:var(--flaky)}h3{margin:6px 0 12px;font-size:21px}
.label{margin:14px 0 4px;color:var(--mute);font-size:13px;text-transform:uppercase;
letter-spacing:.06em}
blockquote{margin:0;padding:8px 14px;border-left:3px solid var(--accent);font-style:italic}
code,pre{font-family:ui-monospace,Consolas,monospace}pre{background:#0b0d11;padding:12px;
border-radius:8px;overflow:auto;font-size:13px}summary{cursor:pointer;color:var(--accent)}
video,img{max-width:100%;border-radius:8px;margin-top:12px}
.shots{display:grid;grid-template-columns:1fr 1fr;gap:12px}
figure{margin:0}figcaption{color:var(--mute);font-size:13px}
"""


def write_html(run_dir, level=None):
    """Write run_dir/report.html and return its path."""
    run_dir = Path(run_dir)
    doc = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))
    session, findings = doc.get("session", {}), doc.get("findings", [])
    checks_path = run_dir / "checks.json"
    checks = ({c["id"]: c for c in json.loads(checks_path.read_text(encoding="utf-8"))}
              if checks_path.exists() else {})
    level = level or session.get("level")
    design = HERE / "levels" / f"{level}.md"
    rules = rule_blocks(design.read_text(encoding="utf-8")) if level and design.exists() else []

    confirmed = [f for f in findings if (f.get("verdict") or {}).get("confirmed")]
    rejected = [f for f in findings if f not in confirmed]
    e = html.escape
    stats = [("Confirmed bugs", len(confirmed)), ("Rejected hypotheses", len(rejected)),
             ("Checks written", len(checks) or "–"), ("Actions", session.get("actions", "")),
             ("Minutes", round(float(session.get("duration_s") or 0) / 60, 1)),
             ("Cost", f"${session.get('cost_usd', '')}")]
    body = [f"<h1>Playtest report{': ' + e(level.capitalize()) if level else ''}</h1>",
            f'<p class="meta">{e(session.get("model") or "scripted bot")} · '
            f'{e(str(session.get("started", "")))}</p>',
            '<div class="stats">' + "".join(f'<div class="stat"><b>{e(str(v))}</b>{e(k)}</div>'
                                            for k, v in stats) + "</div>",
            "<h2>Confirmed bugs</h2>"]
    body += [_finding(f, checks, rules) for f in confirmed] or ["<p>None.</p>"]
    body.append("<h2>Rejected hypotheses</h2>")
    body += [_finding(f, checks, rules) for f in rejected] or ["<p>None.</p>"]
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Playtest report</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(body)}</main></body></html>")
    path = run_dir / "report.html"
    path.write_text(page, encoding="utf-8")
    return path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--level", help="design document under agent/levels/ (newer runs record it)")
    a = p.parse_args()
    print(write_html(a.run_dir, a.level))
