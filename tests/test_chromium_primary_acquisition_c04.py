from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module():
    script = ROOT / "scripts" / "run_chromium_primary_acquisition_c04.py"
    spec = importlib.util.spec_from_file_location("chromium_c04", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict:
    return json.loads(
        (ROOT / "protocols" / "C04_CHROMIUM_PRIMARY_SCAN_ACQUISITION.json").read_text(
            encoding="utf-8"
        )
    )


class ChromiumPrimaryAcquisitionC04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_packet_is_ready_but_external_response_is_required(self) -> None:
        result = self.module.audit(load_contract(), ROOT)
        self.assertEqual(
            result["status"],
            "PASS_CHROMIUM_C04_ACQUISITION_PACKET_READY_EXTERNAL_RESPONSE_REQUIRED",
        )
        self.assertTrue(result["acquisition_packet_ready"])
        self.assertEqual(result["primary_files_acquired"], 0)
        self.assertFalse(result["digitization_allowed"])

    def test_five_ranked_routes_are_frozen(self) -> None:
        result = self.module.audit(load_contract(), ROOT)
        self.assertEqual(result["route_count"], 5)
        self.assertEqual(
            result["route_ids"],
            [
                "AUTHOR_DIRECT",
                "ILLINOIS_ARCHIVES_SD131",
                "ILLINOIS_MRL_LEGACY_RECORDS",
                "LIBRARY_DOCUMENT_DELIVERY",
                "PUBLISHER_ACCESS",
            ],
        )

    def test_author_contact_is_frozen(self) -> None:
        contract = load_contract()
        contract["ranked_routes"][0]["contact"] = "unknown@example.com"
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("author contact" in error for error in result["errors"]))

    def test_archive_collection_cannot_be_claimed_to_contain_figures(self) -> None:
        contract = load_contract()
        contract["ranked_routes"][1]["collection_proven_to_contain_article_figures"] = True
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("cannot be claimed" in error for error in result["errors"]))

    def test_external_messages_cannot_be_marked_sent_automatically(self) -> None:
        contract = load_contract()
        contract["request_packet"]["external_messages_sent"] = True
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("external messages" in error for error in result["errors"]))

    def test_user_approval_gate_cannot_be_removed(self) -> None:
        contract = load_contract()
        contract["request_packet"]["user_approval_required_before_sending"] = False
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("user approval" in error for error in result["errors"]))

    def test_original_byte_hash_gate_is_required(self) -> None:
        contract = load_contract()
        contract["intake_contract"]["original_bytes_sha256_required"] = False
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("original_bytes_sha256_required" in error for error in result["errors"]))

    def test_scan_resolution_cannot_drop_below_300_dpi(self) -> None:
        contract = load_contract()
        contract["intake_contract"]["minimum_scan_resolution_dpi"] = 200
        result = self.module.audit(contract, ROOT)
        self.assertEqual(result["status"], "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT")
        self.assertTrue(any("300 dpi" in error for error in result["errors"]))

    def test_request_drafts_exist(self) -> None:
        result = self.module.audit(load_contract(), ROOT)
        self.assertTrue(result["request_drafts_present"])
        for path in result["request_draft_paths"]:
            self.assertTrue((ROOT / path).is_file())


if __name__ == "__main__":
    unittest.main()
