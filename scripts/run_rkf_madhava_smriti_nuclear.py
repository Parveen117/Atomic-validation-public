from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rkf_madhava_smriti_diagnostics import add_honest_v6_diagnostics
from src.rkf_madhava_smriti_nuclear import build_madhava_smriti_report

CSV_PATH = ROOT / "data" / "processed" / "ame_nubase_atomic_native.csv"
FROZEN_UAM_PATH = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
V5_REPORT_PATH = ROOT / "releases" / "rkf-nuclear-v5" / "experiment_report.json"
OUTPUT_PATH = ROOT / "releases" / "rkf-nuclear-v6" / "madhava_smriti_report.json"


def main() -> None:
    for path in (CSV_PATH, FROZEN_UAM_PATH, V5_REPORT_PATH):
        if not path.exists():
            raise FileNotFoundError(f"missing {path}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    frozen = json.loads(FROZEN_UAM_PATH.read_text(encoding="utf-8"))
    v5 = json.loads(V5_REPORT_PATH.read_text(encoding="utf-8"))

    base_report = build_madhava_smriti_report(
        rows,
        frozen,
        v5,
        source="data/processed/ame_nubase_atomic_native.csv",
        ridge=1.0,
    )
    report = add_honest_v6_diagnostics(base_report)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": report["status"],
        "performance_status": report["performance_status"],
        "promotion_decision": report["promotion_decision"],
        "report_hash": report["report_hash"],
        "record_count": report["record_count"],
        "refinement_classification_counts": report[
            "refinement_classification_counts"
        ],
        "identity_audit": report["identity_audit"],
        "convergence_audit": report["convergence_audit"],
        "metrics": report["metrics"],
        "same_support_audit": report["same_support_audit"],
        "refinement_proxy_audit": report["refinement_proxy_audit"],
        "output": str(OUTPUT_PATH.relative_to(ROOT)),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
