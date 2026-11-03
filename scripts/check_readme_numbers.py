"""
Fail if a number quoted in the docs does not match the file that produced it.

Every metric in README.md and docs/PRD.md is wrapped in a marker that names its
source, for example

    MAE <!--v:dev.full.mae-->7.8<!--/v-->

(an HTML comment, invisible when rendered). This script resolves each key from
the committed eval outputs and compares the quoted text, rounded to the number of
decimals quoted. A key it cannot resolve, or a mismatch, is an error, so no
number in the docs can drift from the script that generates it.

    python scripts/check_readme_numbers.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = re.compile(r"<!--v:([A-Za-z0-9_.\-]+)-->(.*?)<!--/v-->", re.DOTALL)
DOCS = ["README.md", os.path.join("docs", "PRD.md")]
MIN_MARKERS = 12   # guard against the markers being stripped out wholesale


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def resolve_all() -> dict:
    d = {}
    res = load("eval/results.json")
    d["dev.n"] = len(res["slugs"])
    for name, s in res["systems"].items():
        pre = f"dev.{name}"
        d[f"{pre}.mae"] = s["mae"]
        d[f"{pre}.spearman"] = s["spearman"]
        d[f"{pre}.calls"] = s["calls_per_submission"]
        d[f"{pre}.cost"] = s["cost"]["cost_usd"]
        d[f"{pre}.seconds"] = s["cost"]["seconds"]
        d[f"{pre}.citations"] = s["citations"]
        d[f"{pre}.recall"] = s["detection"]["recall"]
        d[f"{pre}.precision"] = s["detection"]["precision"]
        d[f"{pre}.false_alarm_rate"] = s["detection"]["false_alarm_rate"]
    d["dev.mae_gain"] = round(res["systems"]["baseline"]["mae"] - res["systems"]["full"]["mae"], 1)
    d["dev.cost_ratio"] = round(res["systems"]["full"]["cost"]["cost_usd"] / res["systems"]["baseline"]["cost"]["cost_usd"], 1)
    d["dev.time_ratio"] = round(res["systems"]["full"]["cost"]["seconds"] / res["systems"]["baseline"]["cost"]["seconds"], 1)

    # ablation table rows: "| <stage> | <MAE> | <Spearman> |"
    stage_keys = (("baseline", "baseline"), ("+ evidence ledger", "ledger"),
                  ("+ specialist split", "split"), ("+ verification", "verify"))
    with open(os.path.join(ROOT, "eval", "ABLATIONS.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\| (.+?) \| ([\d.]+) \| ([\d.]+) \|$", line.strip())
            if not m:
                continue
            for prefix, key in stage_keys:
                if m.group(1).startswith(prefix) and f"ablation.{key}.mae" not in d:
                    d[f"ablation.{key}.mae"] = float(m.group(2))
                    d[f"ablation.{key}.spearman"] = float(m.group(3))
    d["ablation.verify_gain"] = round(d["ablation.split.mae"] - d["ablation.verify.mae"], 1)

    rp = load("eval/lean_replay.json")
    for k, name in (("baseline", "baseline"), ("full", "full"), ("lean_replay_estimate", "lean")):
        d[f"replay.{name}.mae"] = rp["mae_vs_human"][k]
        d[f"replay.{name}.spearman"] = rp["spearman_vs_human"][k]
    d["replay.lean.calls"] = rp["llm_calls_per_submission"]["lean_expected"]
    gain_full = rp["mae_vs_human"]["baseline"] - rp["mae_vs_human"]["full"]
    gain_lean = rp["mae_vs_human"]["baseline"] - rp["mae_vs_human"]["lean_replay_estimate"]
    d["replay.lean.share_of_gain_pct"] = round(100 * gain_lean / gain_full)
    d["replay.lean.call_share_pct"] = round(100 * rp["llm_calls_per_submission"]["lean_expected"] / rp["llm_calls_per_submission"]["full"])

    tot = {"n": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for name in ("dev", "held-out"):
        w = load(f"eval/writeup_check_{name}.json")
        d[f"writeup.{name}.n"] = w["n"]
        d[f"writeup.{name}.caught"] = w["true_positive"]
        d[f"writeup.{name}.filler"] = w["true_positive"] + w["false_negative"]
        d[f"writeup.{name}.false_alarms"] = w["false_positive"]
        d[f"writeup.{name}.honest"] = w["false_positive"] + w["true_negative"]
        for k, src in (("n", "n"), ("tp", "true_positive"), ("fp", "false_positive"),
                       ("tn", "true_negative"), ("fn", "false_negative")):
            tot[k] += w[src]
    d["writeup.all.n"] = tot["n"]
    d["writeup.all.caught"] = tot["tp"]
    d["writeup.all.filler"] = tot["tp"] + tot["fn"]
    d["writeup.all.false_alarms"] = tot["fp"]
    d["writeup.all.honest"] = tot["fp"] + tot["tn"]

    d["heldout.n"] = len(load("data/human_scores_heldout.json")["submissions"])
    d["heldout.dirs"] = len(glob.glob(os.path.join(ROOT, "data", "submissions_heldout", "*")))
    d["dev.dirs"] = len(glob.glob(os.path.join(ROOT, "data", "submissions", "*")))
    d["tests.count"] = count_tests()
    return d


def count_tests() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", out)
    if m:
        return int(m.group(1))
    return len([ln for ln in out.splitlines() if "::" in ln])


def matches(text: str, value) -> bool:
    text = text.strip().replace(",", "")
    try:
        quoted = float(text)
    except ValueError:
        return False
    decimals = len(text.split(".")[1]) if "." in text else 0
    return round(float(value), decimals) == quoted


def main() -> int:
    values = resolve_all()
    errors, found = [], 0
    for rel in DOCS:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            text = f.read()
        for m in MARKER.finditer(text):
            key, quoted = m.group(1), m.group(2)
            found += 1
            line = text.count("\n", 0, m.start()) + 1
            if key not in values:
                errors.append(f"{rel}:{line}: unknown key '{key}'")
            elif not matches(quoted, values[key]):
                errors.append(f"{rel}:{line}: '{key}' says {quoted.strip()} but the generated value is {values[key]}")
    if found < MIN_MARKERS:
        errors.append(f"only {found} number markers found in the docs (expected at least {MIN_MARKERS})")
    if errors:
        print("README / PRD numbers do not match the generated files:")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK: {found} quoted numbers match the generated files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
