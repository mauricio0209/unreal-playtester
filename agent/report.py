"""Human-readable session report for the playtester agent.

Standard library only.
"""

from pathlib import Path


def _round_cm(value) -> int:
    return int(round(float(value)))


def describe_step(step: dict) -> str:
    """Return one plain-English imperative line for a repro step."""
    action = step.get("action")
    if action == "move_to":
        return f"Walk to ({_round_cm(step['x'])}, {_round_cm(step['y'])})"
    if action == "look_at":
        return (
            f"Look at ({_round_cm(step['x'])}, "
            f"{_round_cm(step['y'])}, {_round_cm(step['z'])})"
        )
    if action == "jump":
        return "Jump"
    if action == "interact":
        return "Press Interact"
    if action == "step":
        return f"Let the game run for {step['seconds']} s"
    raise ValueError(f"unknown action: {action!r}")


def _escape_md(text) -> str:
    """Escape Markdown-significant characters so explorer text stays literal."""
    return "".join("\\" + ch if ch in _MD_SPECIAL else ch for ch in str(text))


_MD_SPECIAL = set("\\`_*{}[]()#+-.!|>~=")


def _escape_title(title) -> str:
    """Collapse whitespace (single-line heading) then escape Markdown."""
    return _escape_md(" ".join(str(title).split()))


def _finding_section(finding: dict) -> list[str]:
    lines: list[str] = []
    lines.append(f"### {_escape_title(finding.get('title', ''))}")
    lines.append("")
    invariant = finding.get("invariant", "")
    description = finding.get("invariant_description", "")
    lines.append(f"Invariant `{invariant}`: {description}")
    lines.append("")
    verdict = finding.get("verdict") or {}
    runs = verdict.get("runs", [])
    hits = sum(1 for r in runs if r)
    total = len(runs)
    confirmed = verdict.get("confirmed", False)
    status = "Confirmed" if confirmed else "Rejected"
    lines.append(f"Verdict: {status} ({hits}/{total} runs reproduced)")
    lines.append("")
    lines.append(f"Runs: {', '.join(str(bool(r)) for r in runs)}")
    lines.append("")
    reason = verdict.get("reason", "")
    if reason:
        lines.append(f"Reason: {reason}")
        lines.append("")
    hypothesis = finding.get("hypothesis", "")
    lines.append(f"Hypothesis: {_escape_md(hypothesis)}")
    lines.append("")
    lines.append("Repro:")
    lines.append("")
    lines.append("Start from a fresh level load.")
    lines.append("")
    for i, step in enumerate(finding.get("steps", []), start=1):
        lines.append(f"{i}. {describe_step(step)}")
    lines.append("")
    before = finding.get("before")
    after = finding.get("after")
    if before:
        lines.append(f"![Before]({before})")
        lines.append("")
    if after:
        lines.append(f"![After]({after})")
        lines.append("")
    return lines


def write_report(run_dir, session: dict, findings: list[dict]) -> Path:
    """Write run_dir/report.md and return its path."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    confirmed = [f for f in findings
                 if (f.get("verdict") or {}).get("confirmed")]
    rejected = [f for f in findings
                if not (f.get("verdict") or {}).get("confirmed")]
    lines: list[str] = []
    lines.append("# Session report")
    lines.append("")
    lines.append(f"{len(confirmed)} confirmed bugs, "
                 f"{len(rejected)} rejected hypotheses.")
    lines.append("")
    lines.append("## Session")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Model | {session.get('model', '')} |")
    lines.append(f"| Started | {session.get('started', '')} |")
    lines.append(f"| Actions | {session.get('actions', '')} |")
    lines.append(f"| Duration | {session.get('duration_s', '')} s |")
    lines.append(f"| Cost | ${session.get('cost_usd', '')} |")
    lines.append("")
    lines.append("## Confirmed bugs")
    lines.append("")
    if confirmed:
        for finding in confirmed:
            lines.extend(_finding_section(finding))
    else:
        lines.append("None.")
        lines.append("")
    lines.append("## Rejected hypotheses")
    lines.append("")
    if rejected:
        for finding in rejected:
            lines.extend(_finding_section(finding))
    else:
        lines.append("None.")
        lines.append("")
    path = run_dir / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
