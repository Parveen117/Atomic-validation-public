from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REQUIRED_COLUMNS = {
    "Z",
    "N",
    "A",
    "Symbol",
    "binding_energy_per_A_keV",
    "S_n_keV",
    "S_2n_keV",
    "S_p_keV",
    "S_2p_keV",
    "half_life_raw",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        rows = list(reader)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "columns": sorted(columns),
        "missing_required_columns": missing,
        "expected_row_count": 3558,
        "row_count_matches": len(rows) == 3558,
        "schema_valid": not missing,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify frozen UAM input dataset")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/processed/ame_nubase_atomic_native.csv",
    )
    parser.add_argument("--output", default="releases/uam-v4/dataset_certificate.json")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: {path}")

    certificate = inspect_csv(path)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(certificate, indent=2, sort_keys=True))

    if not certificate["schema_valid"] or not certificate["row_count_matches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
