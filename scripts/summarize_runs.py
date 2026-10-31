"""Summarize a benchmark: python3 scripts/summarize_runs.py . [runs/benchmark.txt]

Each line of the list file is "<provider> <run dir>". door2_opens is the intermittent bug,
so a confirmation of it counts as a false positive."""
import json
import sys
from collections import defaultdict
from pathlib import Path

# Vault seeded bugs: blue door opens without its key, red door ignores the red key, gem adds 1.
# A confirmed check that names none of them (green door, coin, keys) is a false positive.
VAULT_BUGS = [("blue", "vault_blue_door"), ("red", "vault_red_door"), ("gem", "vault_gem_value")]
REAL = {"no_fall_out_of_world", "door_opens", "pickup_counts"} | {b for _, b in VAULT_BUGS}

root = Path(sys.argv[1])
rows = defaultdict(list)
for line in (root / (sys.argv[2] if len(sys.argv) > 2 else "runs/benchmark.txt")).read_text().split("\n"):
    if not line.strip():
        continue
    provider, run = line.split()
    d = json.loads((root / run / "session.json").read_text())
    confirmed = {f["invariant"] for f in d["findings"] if f["verdict"]["confirmed"]}
    if (root / run / "checks.json").exists():  # Vault: ids are model-written, grade by object
        # A check may cover several doors, so the finding's own words say which one broke.
        confirmed = {next((bug for word, bug in VAULT_BUGS
                           if word in f"{f.get('title', '')} {f.get('hypothesis', '')}".lower()),
                          next((bug for word, bug in VAULT_BUGS if word in f["invariant"]),
                               f["invariant"]))
                     for f in d["findings"] if f["verdict"]["confirmed"]}
    flaky = [f["invariant"] for f in d["findings"]
             if not f["verdict"]["confirmed"] and 0 < sum(f["verdict"]["runs"]) < len(f["verdict"]["runs"])]
    rows[provider].append({
        "run": run, "real": len(confirmed & REAL), "fp": len(confirmed - REAL),
        "flaky": len(flaky), "hyp": len(d["findings"]),
        "min": d["session"]["duration_s"] / 60, "cost": d["session"]["cost_usd"],
        "which": sorted(confirmed)})

for provider, rs in rows.items():
    print(f"\n{provider} ({rs[0]['run']} ...)")
    for r in rs:
        print(f"  {r['run']}: real {r['real']}/3 fp {r['fp']} flaky {r['flaky']} hyp {r['hyp']} "
              f"{r['min']:.1f} min ${r['cost']:.3f} {r['which']}")
    n = len(rs)
    print(f"  TOTAL n={n}: all3 {sum(r['real'] == 3 for r in rs)}/{n}, >=2 {sum(r['real'] >= 2 for r in rs)}/{n}, "
          f"mean real {sum(r['real'] for r in rs) / n:.1f}, fp {sum(r['fp'] for r in rs)}, "
          f"flaky caught {sum(r['flaky'] for r in rs)}, mean {sum(r['min'] for r in rs) / n:.1f} min, "
          f"max {max(r['min'] for r in rs):.1f} min, mean ${sum(r['cost'] for r in rs) / n:.3f}")
