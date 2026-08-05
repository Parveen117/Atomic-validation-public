from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rkf_nuclear_prediction import build_experiment_report
from src.rkf_recognition_repair import add_recognition_repair

CSV_PATH = ROOT / "data" / "processed" / "ame_nubase_atomic_native.csv"
FROZEN_UAM_PATH = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
OUTPUT_PATH = ROOT / "releases" / "rkf-nuclear-v5" / "experiment_report.json"


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"missing {CSV_PATH}; run scripts/reproduce_release.py before this experiment"
        )
    if not FROZEN_UAM_PATH.exists():
        raise FileNotFoundError(
            f"missing {FROZEN_UAM_PATH}; run scripts/reproduce_release.py before this experiment"
        )

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    frozen = json.loads(FROZEN_UAM_PATH.read_text(encoding="utf-8"))
    base_report = build_experiment_report(
        rows,
        frozen,
        source="data/processed/ame_nubase_atomic_native.csv",
        level=3,
        ridge=1.0,
    )
    report = add_recognition_repair(base_report, frozen)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": report["status"],
        "base_rkf_status": report["base_rkf_status"],
        "report_hash": report["report_hash"],
        "record_count": report["record_count"],
        "recognition_repair_rule": report["recognition_repair_rule"],
        "recognition_repair_metrics": report["recognition_repair_metrics"],
        "recognition_repair_comparison": report["recognition_repair_comparison"],
        "recognition_repair_sector_audit": report["recognition_repair_sector_audit"],
        "rkf_cross_fitted_metrics": report["rkf_cross_fitted_metrics"],
        "rkf_burden_guarded_metrics": report["rkf_burden_guarded_metrics"],
        "tensor_cubic_metrics": report["tensor_cubic_metrics"],
        "common_support_comparison": report["common_support_comparison"],
        "explainability": report["explainability"],
        "output": str(OUTPUT_PATH.relative_to(ROOT)),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
