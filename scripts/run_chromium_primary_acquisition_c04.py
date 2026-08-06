from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_DOI = "10.1016/0038-1098(69)90464-5"
EXPECTED_PII = "0038109869904645"
EXPECTED_ROUTES = [
    "AUTHOR_DIRECT",
    "ILLINOIS_ARCHIVES_SD131",
    "ILLINOIS_MRL_LEGACY_RECORDS",
    "LIBRARY_DOCUMENT_DELIVERY",
    "PUBLISHER_ACCESS",
]
EXPECTED_DRAFT_PATHS = [
    "docs/requests/C04_AUTHOR_DATA_REQUEST.md",
    "docs/requests/C04_ARCHIVE_SCAN_REQUEST.md",
    "docs/requests/C04_LIBRARY_REQUEST_METADATA.md",
]


def audit(contract: dict[str, Any], repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    article = contract.get("target_article", {})
    routes = list(contract.get("ranked_routes", []))
    packet = contract.get("request_packet", {})
    intake = contract.get("intake_contract", {})
    state = contract.get("current_state", {})

    if article.get("doi") != EXPECTED_DOI:
        errors.append("target DOI changed")
    if article.get("pii") != EXPECTED_PII:
        errors.append("target PII changed")
    if article.get("pages") != [1035, 1038]:
        errors.append("target page range changed")
    if article.get("funding_note") != "Advanced Research Projects Agency Contract SD-131":
        errors.append("ARPA SD-131 funding note changed")

    route_ids = [route.get("route_id") for route in routes]
    ranks = [route.get("rank") for route in routes]
    if route_ids != EXPECTED_ROUTES:
        errors.append("ranked acquisition route sequence changed")
    if ranks != [1, 2, 3, 4, 5]:
        errors.append("route ranks must remain one through five")
    if len(set(route_ids)) != len(route_ids):
        errors.append("route ids must be unique")

    by_id = {route.get("route_id"): route for route in routes}
    author = by_id.get("AUTHOR_DIRECT", {})
    if author.get("contact") != "salamon@utdallas.edu":
        errors.append("official author contact changed")
    if author.get("route_verified") is not True:
        errors.append("author route must remain verified")

    archive = by_id.get("ILLINOIS_ARCHIVES_SD131", {})
    if archive.get("contact") != "illiarch@illinois.edu":
        errors.append("archive contact changed")
    if archive.get("series_number") != "11/14/818":
        errors.append("archive series number changed")
    if archive.get("collection_physically_held") is not True:
        errors.append("archive physical-holdings gate changed")
    if archive.get("collection_proven_to_contain_article_figures") is not False:
        errors.append("archive collection cannot be claimed to contain article figures")

    mrl = by_id.get("ILLINOIS_MRL_LEGACY_RECORDS", {})
    if mrl.get("contact") != "mrl@illinois.edu":
        errors.append("MRL contact changed")
    if mrl.get("institutional_connection_verified") is not True:
        errors.append("MRL institutional connection must remain verified")

    library = by_id.get("LIBRARY_DOCUMENT_DELIVERY", {})
    if library.get("illinois_reference_contact") != "borrowing@library.illinois.edu":
        errors.append("Illinois ILL reference contact changed")
    if library.get("route_verified") is not True:
        errors.append("library route must remain verified")

    publisher = by_id.get("PUBLISHER_ACCESS", {})
    if publisher.get("metadata_and_abstract_accessible") is not True:
        errors.append("publisher metadata gate changed")
    if publisher.get("full_text_bytes_acquired") is not False:
        errors.append("publisher full-text bytes cannot be marked acquired")

    for route in routes:
        for key in ("request_sent", "response_received", "file_acquired"):
            if key in route and route.get(key) is not False:
                errors.append(f"{route.get('route_id')} {key} must remain false before external action")

    packet_paths = [
        packet.get("author_request_draft_path"),
        packet.get("archive_request_draft_path"),
        packet.get("library_request_metadata_path"),
    ]
    if packet_paths != EXPECTED_DRAFT_PATHS:
        errors.append("request packet paths changed")
    request_drafts_present = all((repository_root / path).is_file() for path in EXPECTED_DRAFT_PATHS)
    if not request_drafts_present:
        errors.append("one or more request packet files are missing")
    if packet.get("external_messages_sent") is not False:
        errors.append("external messages cannot be marked sent")
    if packet.get("user_approval_required_before_sending") is not True:
        errors.append("user approval gate cannot be removed")

    required_true_intake = (
        "original_bytes_sha256_required",
        "source_route_id_required",
        "date_received_required",
        "rights_or_access_note_required",
        "page_and_figure_identity_required_for_scans",
        "lossless_scan_preferred",
        "no_ocr_as_numeric_data",
        "no_secondary_redrawing_as_primary_scan",
        "no_curvature_before_c05_intake_certificate",
    )
    for key in required_true_intake:
        if intake.get(key) is not True:
            errors.append(f"intake gate {key} must remain true")
    if int(intake.get("minimum_scan_resolution_dpi", 0)) < 300:
        errors.append("minimum scan resolution must be at least 300 dpi")

    if int(state.get("verified_acquisition_routes", -1)) != 5:
        errors.append("verified acquisition route count must remain five")
    for key in ("external_requests_sent", "responses_received", "primary_files_acquired"):
        if int(state.get(key, -1)) != 0:
            errors.append(f"current state {key} must remain zero")
    for key in (
        "author_arrays_acquired",
        "primary_scan_acquired",
        "intake_certificate_ready",
        "digitization_allowed",
        "curvature_allowed",
    ):
        if state.get(key) is not False:
            errors.append(f"current state {key} must remain false")

    external_action_pending = (
        int(state.get("external_requests_sent", 0)) == 0
        and int(state.get("responses_received", 0)) == 0
        and int(state.get("primary_files_acquired", 0)) == 0
    )
    acquisition_ready = (
        request_drafts_present
        and len(routes) == 5
        and packet.get("user_approval_required_before_sending") is True
        and external_action_pending
    )

    if errors:
        status = "FAIL_CHROMIUM_C04_ACQUISITION_ROUTE_CONTRACT"
    elif acquisition_ready:
        status = "PASS_CHROMIUM_C04_ACQUISITION_PACKET_READY_EXTERNAL_RESPONSE_REQUIRED"
    else:
        status = "INCONCLUSIVE_CHROMIUM_C04_ACQUISITION_PACKET"

    return {
        "campaign": contract.get("campaign"),
        "status": status,
        "errors": errors,
        "target_doi": article.get("doi"),
        "target_pii": article.get("pii"),
        "funding_note": article.get("funding_note"),
        "route_count": len(routes),
        "route_ids": route_ids,
        "route_contacts": {
            route.get("route_id"): route.get("contact")
            or route.get("illinois_reference_contact")
            or route.get("landing_page")
            for route in routes
        },
        "author_contact_verified": author.get("route_verified") is True,
        "archive_collection_physically_held": archive.get("collection_physically_held") is True,
        "archive_collection_proven_to_contain_article_figures": bool(
            archive.get("collection_proven_to_contain_article_figures")
        ),
        "request_draft_paths": packet_paths,
        "request_drafts_present": request_drafts_present,
        "external_messages_sent": bool(packet.get("external_messages_sent")),
        "user_approval_required_before_sending": bool(
            packet.get("user_approval_required_before_sending")
        ),
        "external_requests_sent": int(state.get("external_requests_sent", 0)),
        "responses_received": int(state.get("responses_received", 0)),
        "primary_files_acquired": int(state.get("primary_files_acquired", 0)),
        "primary_scan_acquired": bool(state.get("primary_scan_acquired")),
        "author_arrays_acquired": bool(state.get("author_arrays_acquired")),
        "intake_certificate_ready": bool(state.get("intake_certificate_ready")),
        "digitization_allowed": bool(state.get("digitization_allowed")),
        "curvature_allowed": bool(state.get("curvature_allowed")),
        "minimum_scan_resolution_dpi": intake.get("minimum_scan_resolution_dpi"),
        "acquisition_packet_ready": acquisition_ready,
        "decisive_reasons": [
            "An official emeritus profile provides a direct author contact route.",
            "The University of Illinois Archives physically holds ARPA SD-131 annual technical reports, but the collection is not yet proven to contain the article figures or raw data.",
            "The Materials Research Laboratory and library document-delivery routes are verified institutional acquisition channels.",
            "Prepared request drafts are present, but no external message has been sent automatically.",
            "No primary bytes or author arrays have been received, so intake certification, digitization and curvature remain blocked."
        ],
        "next_stage": contract.get("next_stage"),
        "claim_boundary": contract.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path("protocols/C04_CHROMIUM_PRIMARY_SCAN_ACQUISITION.json"),
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("releases/chromium-neel-c04/chromium_primary_acquisition_certificate.json"),
    )
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = audit(contract, args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
