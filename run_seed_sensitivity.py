"""Re-run the v11 notebook with seeds 1-10 and summarize the headline results.

Run from the project root (the folder that contains TrafficLabelling/ and the v11
notebook). Each run takes about one minute and writes to seed_runs/seed_<n>/.

    python run_seed_sensitivity.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "soc_alert_fatigue_simulation.ipynb"
RUNNER = ROOT / "run_notebook_inprocess.py"
SEEDS = range(1, 11)


def run_seed(seed):
    run_dir = ROOT / "seed_runs" / f"seed_{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    data_link = run_dir / "TrafficLabelling"
    if not data_link.exists():
        try:
            os.symlink(ROOT / "TrafficLabelling", data_link, target_is_directory=True)
        except OSError:  # Windows without symlink rights: point the loader at the shared folder.
            pass
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    replaced = 0
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        cell["outputs"], cell["execution_count"] = [], None
        source = "".join(cell["source"])
        if "SEED = 42\n" in source:
            source = source.replace("SEED = 42\n", f"SEED = {seed}\n")
            replaced += 1
        if not data_link.exists():
            source = source.replace('Path("TrafficLabelling")', repr(str(ROOT / "TrafficLabelling")).join(["Path(", ")"]))
        cell["source"] = source.splitlines(keepends=True)
    if replaced != 1:
        raise RuntimeError("Could not locate the SEED assignment.")
    seed_nb = run_dir / "notebook.ipynb"
    seed_nb.write_text(json.dumps(nb), encoding="utf-8")
    subprocess.run([sys.executable, str(RUNNER), str(seed_nb), str(run_dir)], check=True)
    return run_dir / "exported_results" / "paper_numbers.json"


def summarize(paths):
    def model(rows, name):
        return next(r for r in rows if r["model"] == name)

    records = []
    for seed, path in sorted(paths.items()):
        d = json.loads(Path(path).read_text())
        burst = {r["alert_load_level"]: r for r in d["critical_windows"]}["Burst"]
        records.append({
            "seed": seed,
            "display_reduction": d["overall"]["Overall alert reduction"],
            "burst_critical_windows": burst["critical_windows"],
            "burst_missed_baseline": burst["baseline_missed_rate"],
            "burst_missed_adaptive_group": burst["adaptive_group_budget_missed_rate"],
            "burst_missed_adaptive_alert": burst["adaptive_alert_budget_missed_rate"],
            "overload_bacc_rf": model(d["overload_results"], "Random Forest")["balanced_accuracy"],
            "overload_bacc_persistence": model(d["overload_results"], "Persistence Baseline")["balanced_accuracy"],
            "load_macro_f1_rf": model(d["workload_results"], "Random Forest")["macro_f1"],
            "load_macro_f1_persistence": model(d["workload_results"], "Persistence Baseline")["macro_f1"],
            "missed_risk_auc_rf": model(d["missed_risk_results"], "Random Forest")["roc_auc"],
            "missed_risk_auc_persistence": model(d["missed_risk_results"], "Persistence Baseline")["roc_auc"],
        })
    table = pd.DataFrame(records).set_index("seed")
    table.to_csv(ROOT / "seed_summary.csv")
    print(table.round(3).to_string())
    print(table.agg(["mean", "std", "min", "max"]).T.round(3).to_string())


if __name__ == "__main__":
    paths = {42: ROOT / "exported_results" / "paper_numbers.json"}
    for seed in SEEDS:
        paths[seed] = run_seed(seed)
    summarize(paths)
