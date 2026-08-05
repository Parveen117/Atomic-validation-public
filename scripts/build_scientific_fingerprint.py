from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scientific_fingerprint import (
    SCHEMA,
    canonical_scientific_json,
    scientific_fingerprint,
    scientific_payload,
)

DEFAULT_REPORT = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
DEFAULT_OUTPUT = ROOT / "releases" / "uam-v4" / "scientific_fingerprint.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the versioned scientific fingerprint for the frozen UAM-V4 report."
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report_path = args.report.resolve()
    output_path = args.output.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    payload = {
        "certificate_type": "UAM_V4_SCIENTIFIC_FINGERPRINT_CERTIFICATE",
        "schema": SCHEMA,
        "scientific_payload": scientific_payload(report),
        "canonical_scientific_json": canonical_scientific_json(report),
        "scientific_fingerprint_sha256": scientific_fingerprint(report),
        "report_artifact": {
            "path": str(report_path.relative_to(ROOT)),
            "file_sha256": sha256_file(report_path),
            "embedded_report_hash": report.get("report_hash"),
        },
        "interpretation": (
            "The scientific fingerprint identifies only the declared frozen counts and "
            "headline guarded metrics. Report hashes and file hashes identify serialized "
            "artifacts and may differ when non-scientific metadata or record serialization differs."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
