import unittest

from src.scientific_fingerprint import (
    canonical_scientific_json,
    scientific_fingerprint,
    scientific_payload,
)


def report() -> dict:
    return {
        "rows_valid": 3558,
        "rows_rejected": 0,
        "guarded_prediction_count": 3514,
        "guarded_abstention_count": 44,
        "guarded_blended_metrics": {
            "coverage": 0.9876335019673974,
            "mean_absolute_residual_keV_per_a": 10.214723170037805,
            "mean_signed_residual_keV_per_a": 2.0481822570706876,
            "median_absolute_residual_keV_per_a": 0.9893949800216433,
            "p95_absolute_residual_keV_per_a": 36.98455875106174,
            "p99_absolute_residual_keV_per_a": 165.2220135494648,
            "max_absolute_residual_keV_per_a": 1282.4164,
            "root_mean_square_residual_keV_per_a": 54.750312355960354,
        },
        "report_hash": "artifact-a",
        "source_label": "first-path",
        "records": [{"z": 1}, {"z": 2}],
    }


class ScientificFingerprintTests(unittest.TestCase):
    def test_frozen_release_fingerprint(self) -> None:
        self.assertEqual(
            scientific_fingerprint(report()),
            "fcf83345a4f18ca82fd5282c1dae6d183f1015e68dceb4719cd6fbbecdcfc25b",
        )

    def test_artifact_metadata_does_not_change_scientific_identity(self) -> None:
        first = report()
        second = report()
        second["report_hash"] = "artifact-b"
        second["source_label"] = "different-path"
        second["records"] = list(reversed(second["records"]))
        second["created_at"] = "tomorrow"
        self.assertEqual(scientific_fingerprint(first), scientific_fingerprint(second))

    def test_scientific_metric_change_changes_fingerprint(self) -> None:
        first = report()
        second = report()
        second["guarded_blended_metrics"]["coverage"] -= 1e-6
        self.assertNotEqual(scientific_fingerprint(first), scientific_fingerprint(second))

    def test_missing_declared_metric_is_rejected(self) -> None:
        broken = report()
        del broken["guarded_blended_metrics"]["p99_absolute_residual_keV_per_a"]
        with self.assertRaises(KeyError):
            scientific_payload(broken)

    def test_canonical_json_is_deterministic(self) -> None:
        self.assertEqual(canonical_scientific_json(report()), canonical_scientific_json(report()))


if __name__ == "__main__":
    unittest.main()
