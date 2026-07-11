from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "releases" / "uam-v4"
REPORT_PATH = RELEASE_DIR / "universal_atomic_guarded_two_axis_v4.json"
CERT_PATH = RELEASE_DIR / "reproduction_certificate.json"
BUNDLE_DIR = RELEASE_DIR / "publication_bundle"

PREDICTION_FIELDS = [
    "entity", "z", "n", "a", "mass_region",
    "actual_binding_energy_per_A_keV",
    "guarded_blended_prediction_keV_per_a",
    "signed_residual_keV_per_a",
    "absolute_residual_keV_per_a",
    "n_prediction_keV_per_a", "z_prediction_keV_per_a",
    "directional_disagreement_keV_per_a",
    "directional_disagreement_threshold_keV_per_a",
    "weight_n", "weight_z", "guard_decision", "guard_reasons",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def metrics(records: list[dict]) -> dict:
    residuals = [
        float(record["guarded_blended_prediction_keV_per_a"])
        - float(record["actual_binding_energy_per_A_keV"])
        for record in records
        if record.get("guarded_blended_prediction_keV_per_a") is not None
        and record.get("actual_binding_energy_per_A_keV") is not None
    ]
    absolute = [abs(value) for value in residuals]
    count = len(records)
    if not residuals:
        return {
            "count": count,
            "prediction_count": 0,
            "coverage": 0.0 if count else None,
            "mean_absolute_residual_keV_per_a": None,
            "median_absolute_residual_keV_per_a": None,
            "p95_absolute_residual_keV_per_a": None,
            "p99_absolute_residual_keV_per_a": None,
            "max_absolute_residual_keV_per_a": None,
            "root_mean_square_residual_keV_per_a": None,
            "mean_signed_residual_keV_per_a": None,
        }
    ordered_absolute = sorted(absolute)
    middle = len(ordered_absolute) // 2
    median = (
        ordered_absolute[middle]
        if len(ordered_absolute) % 2
        else (ordered_absolute[middle - 1] + ordered_absolute[middle]) / 2.0
    )
    return {
        "count": count,
        "prediction_count": len(residuals),
        "coverage": len(residuals) / count if count else None,
        "mean_absolute_residual_keV_per_a": sum(absolute) / len(absolute),
        "median_absolute_residual_keV_per_a": median,
        "p95_absolute_residual_keV_per_a": percentile(absolute, 0.95),
        "p99_absolute_residual_keV_per_a": percentile(absolute, 0.99),
        "max_absolute_residual_keV_per_a": max(absolute),
        "root_mean_square_residual_keV_per_a": (
            sum(value * value for value in residuals) / len(residuals)
        ) ** 0.5,
        "mean_signed_residual_keV_per_a": sum(residuals) / len(residuals),
    }


def normalized_row(record: dict) -> dict:
    prediction = record.get("guarded_blended_prediction_keV_per_a")
    actual = record.get("actual_binding_energy_per_A_keV")
    signed = None
    if prediction is not None and actual is not None:
        signed = float(prediction) - float(actual)
    row = {field: record.get(field) for field in PREDICTION_FIELDS}
    row["signed_residual_keV_per_a"] = signed
    row["absolute_residual_keV_per_a"] = abs(signed) if signed is not None else None
    row["guard_reasons"] = ";".join(record.get("guard_reasons") or [])
    return row


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    certificate = json.loads(CERT_PATH.read_text(encoding="utf-8"))
    if certificate.get("status") != "SCIENTIFICALLY_REPRODUCED":
        raise RuntimeError("publication bundle requires SCIENTIFICALLY_REPRODUCED certificate")

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    records = list(report.get("records") or [])
    rows = [normalized_row(record) for record in records]
    predictions = [row for row in rows if row["guard_decision"] == "PREDICT"]
    abstentions = [row for row in rows if row["guard_decision"] == "ABSTAIN"]

    write_csv(BUNDLE_DIR / "predictions.csv", predictions, PREDICTION_FIELDS)
    write_csv(BUNDLE_DIR / "abstentions.csv", abstentions, PREDICTION_FIELDS)

    by_region: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_region[str(record.get("mass_region"))].append(record)
    region_summary = {
        region: metrics(group) for region, group in sorted(by_region.items())
    }
    (BUNDLE_DIR / "mass_region_metrics.json").write_text(
        json.dumps(region_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    region_rows = [{"mass_region": region, **values} for region, values in region_summary.items()]
    region_fields = ["mass_region"] + list(next(iter(region_summary.values())).keys())
    write_csv(BUNDLE_DIR / "mass_region_metrics.csv", region_rows, region_fields)

    configuration = {
        "release_id": "uam-v4-publication-candidate",
        "model": "guarded two-axis V4",
        "disagreement_sigma": report.get("declared_disagreement_sigma"),
        "scientific_status": report.get("scientific_status"),
        "dataset_sha256": certificate.get("dataset_file_sha256"),
        "dataset_rows": certificate.get("dataset", {}).get("row_count"),
        "scientific_reproduction_status": certificate.get("status"),
        "reproducible_report_hash": certificate.get("observed_report_hash"),
        "legacy_report_hash": certificate.get("legacy_report_hash"),
        "legacy_exact_hash_match": certificate.get("legacy_exact_hash_match"),
    }
    (BUNDLE_DIR / "configuration.json").write_text(
        json.dumps(configuration, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "dataset": certificate.get("dataset"),
        "archive_path": certificate.get("archive_path"),
        "archive_sha256": certificate.get("archive_sha256"),
        "source_repository": "Parveen117/Atomic-model",
        "source_snapshot": "5133413a5a88b0a571d7254d547aca9965620c8e",
        "implementation_blob_sha": "c9ac194d7736c16636e69b089940a0a7de4deb4b",
        "record_count": len(records),
        "prediction_count": len(predictions),
        "abstention_count": len(abstentions),
    }
    (BUNDLE_DIR / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    environment = {
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "dependencies": "Python standard library only",
    }
    (BUNDLE_DIR / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (BUNDLE_DIR / "reproduction_command.txt").write_text(
        "python scripts/reproduce_release.py\npython scripts/build_publication_bundle.py\n",
        encoding="utf-8",
    )
    (BUNDLE_DIR / "report_hash.txt").write_text(
        str(certificate.get("observed_report_hash")) + "\n",
        encoding="utf-8",
    )

    generated = sorted(path for path in BUNDLE_DIR.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    checksum_lines = [f"{sha256_file(path)}  {path.name}" for path in generated]
    (BUNDLE_DIR / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    summary = {
        "status": "PUBLICATION_BUNDLE_BUILT",
        "record_count": len(records),
        "prediction_count": len(predictions),
        "abstention_count": len(abstentions),
        "bundle_path": str(BUNDLE_DIR.relative_to(ROOT)),
        "files": [path.name for path in sorted(BUNDLE_DIR.iterdir()) if path.is_file()],
    }
    (BUNDLE_DIR / "bundle_certificate.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
