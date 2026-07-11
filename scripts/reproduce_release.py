from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import traceback
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
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def read_json_if_present(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_final(payload: dict) -> None:
    FINAL_CERT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_CERT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    base = {
        "certificate_type": "UAM_V4_FROZEN_REPRODUCTION_CERTIFICATE",
        "created_at_utc": started,
        "archive_path": ZIP_PATH.name,
        "expected_report_hash": EXPECTED_HASH,
    }

    try:
        if not ZIP_PATH.exists():
            raise FileNotFoundError(f"missing archive: {ZIP_PATH}")

        base["archive_sha256"] = sha256_file(ZIP_PATH)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(ZIP_PATH) as archive:
            members = [name for name in archive.namelist() if Path(name).name == CSV_PATH.name]
            base["archive_members_matching_dataset"] = members
            if len(members) != 1:
                raise RuntimeError(f"expected exactly one {CSV_PATH.name} in archive, found {members}")
            with archive.open(members[0]) as source, CSV_PATH.open("wb") as target:
                shutil.copyfileobj(source, target)

        base["dataset_file_sha256"] = sha256_file(CSV_PATH)
        run([sys.executable, "scripts/verify_dataset.py", str(CSV_PATH), "--output", str(DATA_CERT)])
        base["dataset"] = read_json_if_present(DATA_CERT)

        run([
            sys.executable,
            "src/uam_v4_reproducer.py",
            "--input", str(CSV_PATH),
            "--output", str(REPORT_PATH),
            "--source-label", "data/processed/ame_nubase_atomic_native.csv",
            "--expected-hash", EXPECTED_HASH,
        ])

        report = read_json_if_present(REPORT_PATH)
        if report is None:
            raise RuntimeError("reproducer completed without a readable report")

        final = {
            **base,
            "report_path": str(REPORT_PATH.relative_to(ROOT)),
            "report_file_sha256": sha256_file(REPORT_PATH),
            "observed_report_hash": report.get("report_hash"),
            "exact_hash_match": report.get("report_hash") == EXPECTED_HASH,
            "guarded_prediction_count": report.get("guarded_prediction_count"),
            "guarded_abstention_count": report.get("guarded_abstention_count"),
            "status": "REPRODUCED" if report.get("report_hash") == EXPECTED_HASH else "FAILED",
        }
        write_final(final)
        if not final["exact_hash_match"]:
            raise SystemExit(1)

    except BaseException as exc:
        dataset = read_json_if_present(DATA_CERT)
        report = read_json_if_present(REPORT_PATH)
        failure = {
            **base,
            "status": "FAILED",
            "exact_hash_match": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "dataset": dataset,
            "observed_report_hash": report.get("report_hash") if report else None,
            "guarded_prediction_count": report.get("guarded_prediction_count") if report else None,
            "guarded_abstention_count": report.get("guarded_abstention_count") if report else None,
        }
        if ZIP_PATH.exists() and "archive_sha256" not in failure:
            failure["archive_sha256"] = sha256_file(ZIP_PATH)
        if CSV_PATH.exists():
            failure["dataset_file_sha256"] = sha256_file(CSV_PATH)
        if REPORT_PATH.exists():
            failure["report_file_sha256"] = sha256_file(REPORT_PATH)
        write_final(failure)
        raise


if __name__ == "__main__":
    main()
