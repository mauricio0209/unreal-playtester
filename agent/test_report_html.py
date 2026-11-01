"""Tests for report_html.py. Run: python3 agent/test_report_html.py"""

import json
import tempfile
from pathlib import Path

import report_html

HERE = Path(__file__).resolve().parent
armory = report_html.rule_blocks((HERE / "levels" / "armory.md").read_text())
vault = report_html.rule_blocks((HERE / "levels" / "vault.md").read_text())


def match(description, blocks):
    return report_html.closest_rule(description, blocks) or ""


assert "gold coin is worth 5" in match("The gold coin adds 5 to the inventory.", armory)
assert "side door" in match("Standing next to the side door and interacting opens it.", armory)
assert "exit door" in match("Interacting with the exit door without the gold coin does nothing.", armory)
assert "gem bundle is worth 3" in match("GemBundle is worth 3 inventory.", vault)
assert "same color" in match("Interacting with RedDoor while carrying RedKey opens it.", vault)
assert "collected by walking" in match("The gold coin is collected only by walking over it.", armory)
assert report_html.closest_rule("zzz", vault) is None

with tempfile.TemporaryDirectory() as d:
    finding = {"title": "Gem <adds> 1", "invariant": "gem_worth_three",
               "invariant_description": "The gem bundle adds 3 to the inventory.",
               "steps": [{"action": "move_to", "x": 1, "y": 2}],
               "verdict": {"confirmed": True, "runs": [True, True, True]}}
    Path(d, "session.json").write_text(json.dumps(
        {"session": {"level": "vault", "duration_s": 60}, "findings": [finding]}))
    Path(d, "checks.json").write_text(json.dumps(
        [{"id": "gem_worth_three", "description": "x", "violation": {"var": "InventoryCount"}}]))
    page = report_html.write_html(d).read_text()
    assert "Gem &lt;adds&gt; 1" in page and "Confirmed: 3/3" in page
    assert "gem bundle is worth 3" in page and "InventoryCount" in page and "Walk to (1, 2)" in page
print("ok")
