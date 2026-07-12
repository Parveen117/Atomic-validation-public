from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release" / "uam_halo_v10_1"
MAPPING = RELEASE / "data" / "manifests" / "v4_input_mapping.json"
ANNOTATIONS = RELEASE / "data" / "manifests" / "halo_annotations.json"
ARCHIVE = ROOT / "releases" / "uam-v4" / "uam_v4_processed_dataset.zip"
WORK = RELEASE / "data" / "generated"
REPORT = RELEASE / "reports" / "uam_halo_v10_1_report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    if sha256(ARCHIVE) != mapping["source_archive_sha256"]:
        raise SystemExit("frozen UAM V4 archive hash mismatch")

    WORK.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    member = mapping["archive_member"]
    with zipfile.ZipFile(ARCHIVE) as bundle:
        bundle.extract(member, WORK)
    dataset = WORK / member
    if sha256(dataset) != mapping["dataset_sha256"]:
        raise SystemExit("extracted UAM V4 dataset hash mismatch")

    command = [
        sys.executable,
        "-m",
        "release.uam_halo_v10_1.src.uam_halo_v10_1",
        "--input",
        str(dataset),
        "--output",
        str(REPORT),
        "--annotations",
        str(ANNOTATIONS),
        "--thresholds-keV",
        "500",
        "1000",
        "1500",
        "2000",
        "--controls-per-halo",
        "3",
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report["rows_read"] != mapping["expected_row_count"]:
        raise SystemExit("halo report row count does not match frozen UAM V4 certificate")
    if report["rows_rejected"] != 0:
        raise SystemExit("halo report rejected rows from certified UAM V4 input")

    certificate = {
        "certificate_type": "UAM_HALO_V10_1_REPRODUCTION_CERTIFICATE",
        "source_archive_sha256": mapping["source_archive_sha256"],
        "source_dataset_sha256": mapping["dataset_sha256"],
        "source_row_count": mapping["expected_row_count"],
        "report_path": str(REPORT.relative_to(ROOT)),
        "report_file_sha256": sha256(REPORT),
        "report_hash": report["report_hash"],
        "rows_valid": report["rows_valid"],
        "rows_rejected": report["rows_rejected"],
        "halo_candidates_present": report["halo_candidates_present"],
        "status": "REPRODUCED_FROM_FROZEN_UAM_V4_INPUT",
    }
    certificate_path = RELEASE / "reproduction_certificate.json"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(certificate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
