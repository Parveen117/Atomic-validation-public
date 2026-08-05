from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

SCHEMA = "UAM_V4_SCIENTIFIC_FINGERPRINT_V1"

COUNT_FIELDS = (
    "rows_valid",
    "rows_rejected",
    "guarded_prediction_count",
    "guarded_abstention_count",
)

METRIC_FIELDS = (
    "coverage",
    "mean_absolute_residual_keV_per_a",
    "mean_signed_residual_keV_per_a",
    "median_absolute_residual_keV_per_a",
    "p95_absolute_residual_keV_per_a",
    "p99_absolute_residual_keV_per_a",
    "max_absolute_residual_keV_per_a",
    "root_mean_square_residual_keV_per_a",
)


def _required(mapping: Mapping[str, Any], key: str, location: str) -> Any:
    if key not in mapping:
        raise KeyError(f"missing {location}.{key}")
    return mapping[key]


def _normalize_count(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{key} must be an integer count")
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{key} must be an integer count") from exc
    if normalized < 0 or normalized != value:
        raise ValueError(f"{key} must be a non-negative integer")
    return normalized


def _normalize_metric(value: Any, key: str) -> str:
    if isinstance(value, bool):
        raise TypeError(f"{key} must be a finite number")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{key} must be a finite number") from exc
    if not math.isfinite(normalized):
        raise ValueError(f"{key} must be a finite number")
    # Python's repr is the shortest decimal string that round-trips to the
    # same IEEE-754 value. The schema version pins this normalization rule.
    return repr(normalized)


def scientific_payload(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return the versioned scientific identity packet for a UAM-V4 report.

    The packet deliberately excludes record ordering, source labels, timestamps,
    execution metadata, and the full report hash. Those belong to artifact
    provenance, not to the identity of the declared headline result.
    """

    metrics = _required(report, "guarded_blended_metrics", "report")
    if not isinstance(metrics, Mapping):
        raise TypeError("report.guarded_blended_metrics must be a mapping")

    counts = {
        key: _normalize_count(_required(report, key, "report"), key)
        for key in COUNT_FIELDS
    }
    guarded_metrics = {
        key: _normalize_metric(_required(metrics, key, "guarded_blended_metrics"), key)
        for key in METRIC_FIELDS
    }

    return {
        "schema": SCHEMA,
        "counts": counts,
        "guarded_blended_metrics": guarded_metrics,
    }


def canonical_scientific_json(report: Mapping[str, Any]) -> str:
    return json.dumps(
        scientific_payload(report),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def scientific_fingerprint(report: Mapping[str, Any]) -> str:
    canonical = canonical_scientific_json(report).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
