from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_DOIS = {
    "SIMULTANEOUS_CP_DRHODT_1969": "10.1016/0038-1098(69)90464-5",
    "SPECIFIC_HEAT_STRAIN_ANNEAL_1979": "10.1088/0305-4608/9/3/007",
    "THERMAL_EXPANSION_SINGLE_CRYSTAL_1969": "10.1143/JPSJ.27.786",
    "THERMAL_EXPANSION_CR_CRV_1986": "10.1088/0305-4608/16/4/009",
    "RESISTIVITY_PRB_1978": "10.1103/PhysRevB.18.3665",
    "LATENT_HEAT_1971": "10.1016/0375-9601(71)90719-5",
    "FIRST_ORDER_PRL_1971": "10.1103/PhysRevLett.27.1523",
    "CALORIMETRIC_CR_ALLOYS_1975": "10.1088/0305-4608/5/10/019",
    "ELASTIC_EXPANSION_1963": "10.1103/PhysRev.129.1063",
    "THERMAL_HYSTERESIS_1980": "10.1088/0305-4608/10/11/026",
}

EXPECTED_DECISIONS = {
    "SIMULTANEOUS_CP_DRHODT_1969": "PRIMARY_SAME_SPECIMEN_PAIR",
    "SPECIFIC_HEAT_STRAIN_ANNEAL_1979": "PRIMARY_HEAT_CAPACITY_VALIDATION",
    "THERMAL_EXPANSION_SINGLE_CRYSTAL_1969": "PRIMARY_THERMAL_EXPANSION_TARGET",
    "THERMAL_EXPANSION_CR_CRV_1986": "SECONDARY_EXPANSION_REFERENCE",
    "RESISTIVITY_PRB_1978": "PRIMARY_RESISTIVITY_VALIDATION",
    "LATENT_HEAT_1971": "FIRST_ORDER_THERMODYNAMIC_WITNESS",
    "FIRST_ORDER_PRL_1971": "FIRST_ORDER_MAGNETIC_WITNESS",
    "CALORIMETRIC_CR_ALLOYS_1975": "TRANSITION_ORDER_COMPARATIVE_CONTROL",
    "ELASTIC_EXPANSION_1963": "SECONDARY_MAGNETOELASTIC_TARGET",
    "THERMAL_HYSTERESIS_1980": "PRIMARY_BRANCH_SEMANTICS_TARGET",
}

EXPECTED_COORDINATES = [
    "equilibrium_sample_temperature_K",
    "thermal_branch",
    "sample_state_id",
]

REQUIRED_QUALIFICATION_GATES = [
    "source_reported_transition_temperature_required",
    "heating_cooling_or_modulation_branch_required",
    "sample_purity_and_treatment_required",
    "crystal_orientation_or_polycrystal_state_required",
    "strain_pressure_and_interstitial_state_required",
    "same_specimen_flag_required",
    "no_universal_311K_substitution",
    "no_cross_specimen_covariance_invention",
    "no_digitized_uncertainty_invention",
    "no_curvature_before_machine_readable_arrays",
    "no_magnetic_order_proxy_substitution_without_type_label",
]


def audit(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    target = contract.get("target", {})
    if target.get("material") != "elemental_bcc_chromium":
        errors.append("target material must remain elemental bcc chromium")
    if target.get("nominal_temperature_window_K") != [293.0, 323.0]:
        errors.append("nominal source-search window changed")
    if target.get("nominal_reference_temperature_K") != 311.0:
        errors.append("nominal reference temperature changed")
    if target.get("nominal_reference_is_not_universal") is not True:
        errors.append("311 K must remain a non-universal reference")
    if target.get("state_coordinates") != EXPECTED_COORDINATES:
        errors.append("typed state coordinates changed")

    qualification = contract.get("qualification_contract", {})
    for gate in REQUIRED_QUALIFICATION_GATES:
        if qualification.get(gate) is not True:
            errors.append(f"qualification gate {gate} must remain true")

    sources = {
        source.get("source_id"): source
        for source in contract.get("source_registry", [])
        if isinstance(source, dict)
    }
    missing = sorted(set(EXPECTED_SOURCE_DOIS) - set(sources))
    extra = sorted(set(sources) - set(EXPECTED_SOURCE_DOIS))
    if missing:
        errors.append(f"missing source pins: {missing}")
    if extra:
        errors.append(f"unexpected source pins: {extra}")

    for source_id, expected_doi in EXPECTED_SOURCE_DOIS.items():
        source = sources.get(source_id, {})
        if source.get("doi") != expected_doi:
            errors.append(f"DOI changed for {source_id}")
        if source.get("decision") != EXPECTED_DECISIONS[source_id]:
            errors.append(f"decision changed for {source_id}")
        if source.get("curve_machine_readable_verified") is not False:
            errors.append(f"machine-readable curve gate must remain false for {source_id}")

    simultaneous = sources.get("SIMULTANEOUS_CP_DRHODT_1969", {})
    if simultaneous.get("same_specimen_multichannel") is not True:
        errors.append("simultaneous heat-capacity/resistivity source must remain same-specimen")
    if simultaneous.get("channels") != [
        "heat_capacity_Cp",
        "resistivity_temperature_coefficient_drho_dT",
    ]:
        errors.append("simultaneous primary channel pair changed")

    heat_capacity = sources.get("SPECIFIC_HEAT_STRAIN_ANNEAL_1979", {})
    if heat_capacity.get("reported_transition_temperature_K") != 311.4:
        errors.append("high-purity heat-capacity transition temperature changed")
    if heat_capacity.get("reported_latent_heat_J_per_mol") != 1.4:
        errors.append("high-purity heat-capacity latent heat changed")
    if heat_capacity.get("strain_and_anneal_dependence_reported") is not True:
        errors.append("strain and anneal dependence must remain explicit")

    expansion = sources.get("THERMAL_EXPANSION_CR_CRV_1986", {})
    if expansion.get("temperature_range_K") != [2.0, 700.0]:
        errors.append("Cr/CrV expansion range changed")
    if expansion.get("paramagnetic_reference") != "Cr95V5":
        errors.append("paramagnetic expansion reference changed")

    latent = sources.get("LATENT_HEAT_1971", {})
    if latent.get("reported_latent_heat_cal_per_mol") != 0.47:
        errors.append("direct latent-heat value changed")
    if latent.get("reported_latent_heat_uncertainty_cal_per_mol") != 0.1:
        errors.append("direct latent-heat uncertainty changed")
    if latent.get("scalar_uncertainty_verified") is not True:
        errors.append("direct latent-heat scalar uncertainty must remain verified")

    calorimetric_control = sources.get("CALORIMETRIC_CR_ALLOYS_1975", {})
    if calorimetric_control.get("pure_incommensurate_transition_reported_first_order") is not True:
        errors.append("pure chromium first-order calorimetric control changed")
    if calorimetric_control.get("commensurate_alloy_transition_reported_second_order") is not True:
        errors.append("commensurate alloy second-order control changed")

    hysteresis = sources.get("THERMAL_HYSTERESIS_1980", {})
    if hysteresis.get("heating_and_cooling_branches_required") is not True:
        errors.append("heating/cooling branch requirement changed")

    admission = contract.get("admission_decision", {})
    if admission.get("primary_same_specimen_source_id") != "SIMULTANEOUS_CP_DRHODT_1969":
        errors.append("primary same-specimen source changed")
    if admission.get("four_channel_common_specimen_ready") is not False:
        errors.append("four-channel common specimen must remain unready")
    if admission.get("machine_readable_curve_source_count") != 0:
        errors.append("machine-readable curve count must remain zero")
    if admission.get("cross_paper_curvature_allowed") is not False:
        errors.append("cross-paper curvature must remain forbidden")
    if admission.get("anomaly_significance_computed") is not False:
        errors.append("C02 must not compute anomaly significance")

    source_list = list(sources.values())
    same_specimen_count = sum(
        source.get("same_specimen_multichannel") is True for source in source_list
    )
    machine_readable_count = sum(
        source.get("curve_machine_readable_verified") is True for source in source_list
    )
    transition_temperatures = sorted(
        {
            float(source[key])
            for source in source_list
            for key in (
                "reported_transition_temperature_K",
                "pure_chromium_transition_temperature_K",
                "neel_anomaly_temperature_K",
            )
            if source.get(key) is not None
        }
    )
    first_order_witness_count = sum(
        source.get("decision")
        in {
            "FIRST_ORDER_THERMODYNAMIC_WITNESS",
            "FIRST_ORDER_MAGNETIC_WITNESS",
            "TRANSITION_ORDER_COMPARATIVE_CONTROL",
        }
        for source in source_list
    )

    status = (
        "PASS_CHROMIUM_NEEL_SOURCE_PINNING_DATA_ACQUISITION_REQUIRED"
        if not errors
        else "FAIL_CHROMIUM_NEEL_SOURCE_PINNING"
    )
    return {
        "campaign": contract.get("campaign"),
        "status": status,
        "errors": errors,
        "target_material": target.get("material"),
        "target_transition": target.get("transition"),
        "nominal_temperature_window_K": target.get("nominal_temperature_window_K"),
        "nominal_reference_temperature_K": target.get("nominal_reference_temperature_K"),
        "nominal_reference_is_not_universal": target.get("nominal_reference_is_not_universal"),
        "state_coordinates": target.get("state_coordinates"),
        "source_count": len(source_list),
        "source_ids": sorted(sources),
        "same_specimen_multichannel_source_count": same_specimen_count,
        "machine_readable_curve_source_count": machine_readable_count,
        "source_reported_transition_temperatures_K": transition_temperatures,
        "first_order_witness_count": first_order_witness_count,
        "primary_same_specimen_source_id": admission.get("primary_same_specimen_source_id"),
        "primary_same_specimen_channels": simultaneous.get("channels", []),
        "direct_latent_heat_scalar": {
            "value_cal_per_mol": latent.get("reported_latent_heat_cal_per_mol"),
            "uncertainty_cal_per_mol": latent.get(
                "reported_latent_heat_uncertainty_cal_per_mol"
            ),
        },
        "four_channel_common_specimen_ready": False,
        "cross_paper_curvature_allowed": False,
        "curvature_computed": False,
        "anomaly_significance_computed": False,
        "decisive_reasons": [
            "The strongest primary source measures heat capacity and resistivity response simultaneously on one specimen.",
            "Thermal expansion, latent heat, elastic, hysteresis and transition-order sources use different specimens and protocols.",
            "Reported transition temperatures differ across sample state, strain, alloying and measurement protocol, so 311 K is not a universal alignment coordinate.",
            "No pinned source currently provides a verified public machine-readable curve with pointwise uncertainty and shared covariance.",
            "Cross-paper curvature and significance remain forbidden until source arrays and branch metadata are acquired.",
        ],
        "required_next_data": admission.get("required_next_data", []),
        "next_stage": contract.get("next_stage"),
        "claim_boundary": contract.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path("protocols/C02_CHROMIUM_NEEL_SOURCE_PINNING.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "releases/chromium-neel-c02/chromium_neel_source_certificate.json"
        ),
    )
    args = parser.parse_args()
    result = audit(json.loads(args.contract.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
