from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "uam_v4_processed_dataset.zip"
DATA_DIR = ROOT / "data" / "processed"
CSV_PATH = DATA_DIR / "ame_nubase_atomic_native.csv"
DATA_CERT = ROOT / "releases" / "uam-v4" / "dataset_certificate.json"
REPORT_PATH = ROOT / "releases" / "uam-v4" / "universal_atomic_guarded_two_axis_v4.json"
FINAL_CERT = ROOT / "releases" / "uam-v4" / "reproduction_certificate.json"
EXPECTED_HASH = "34efc196e348d58fedf13d7491d20c069345606cd06393b5338a9dc12359edd7"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"missing archive: {ZIP_PATH}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as archive:
        members = [name for name in archive.namelist() if Path(name).name == CSV_PATH.name]
        if len(members) != 1:
            raise RuntimeError(f"expected exactly one {CSV_PATH.name} in archive, found {members}")
        with archive.open(members[0]) as source, CSV_PATH.open("wb") as target:
            shutil.copyfileobj(source, target)

    run([sys.executable, "scripts/verify_dataset.py", str(CSV_PATH), "--output", str(DATA_CERT)])
    run([
        sys.executable,
        "src/uam_v4_reproducer.py",
        "--input", str(CSV_PATH),
        "--output", str(REPORT_PATH),
        "--source-label", "data/processed/ame_nubase_atomic_native.csv",
        "--expected-hash", EXPECTED_HASH,
    ])

    dataset_certificate = json.loads(DATA_CERT.read_text(encoding="utf-8"))
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    final = {
        "certificate_type": "UAM_V4_FROZEN_REPRODUCTION_CERTIFICATE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_path": ZIP_PATH.name,
        "archive_sha256": sha256_file(ZIP_PATH),
        "dataset": dataset_certificate,
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "report_file_sha256": sha256_file(REPORT_PATH),
        "expected_report_hash": EXPECTED_HASH,
        "observed_report_hash": report["report_hash"],
        "exact_hash_match": report["report_hash"] == EXPECTED_HASH,
        "guarded_prediction_count": report["guarded_prediction_count"],
        "guarded_abstention_count": report["guarded_abstention_count"],
        "status": "REPRODUCED" if report["report_hash"] == EXPECTED_HASH else "FAILED",
    }
    FINAL_CERT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_CERT.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(final, indent=2, sort_keys=True))
    if not final["exact_hash_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
