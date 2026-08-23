import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/IMPLEMENTATION_SPEC.md"
REPORT = ROOT / "docs/P146C_FORMAL_RQ_AND_SPEC_REVISION_REPORT.md"
PREREG = ROOT / "data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json"
LOG = ROOT / "docs/RESEARCH_DECISION_LOG.md"

REVISED_PRIMARY_RQ = (
    "Conditional on an empirically admissible current battery capacity–resistance state, "
    "under what combinations of remaining vehicle service, replacement-battery embodied emissions, "
    "and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement "
    "robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths "
    "are unidentified?"
)

HISTORICAL_PRIMARY_RQ = (
    "Under what combinations of battery degradation, replacement-battery embodied emissions, "
    "remaining vehicle service life, and temporal decarbonization of charging electricity and battery "
    "manufacturing does the life-cycle-GHG-minimizing first-life battery decision in a battery electric "
    "vehicle favor early replacement, an interior retirement/replacement point, or continued use to "
    "the technical mobility boundary?"
)

EXPECTED_REPORT_SECTIONS = [
    "Governing Files Read", "Change-Control Approval", "Historical Failure Preservation",
    "Option B Formal Adoption", "Original RQ Supersession", "Revised Primary RQ",
    "Revised Sub-RQs", "Scientific Estimand", "Identified-Set Definition",
    "Carbon Classification Rules", "Technical Classification Rules", "Current-State Admissibility",
    "Θ_C Definition", "Θ_R Definition", "Policy Symmetry", "Joint Θ(z) Compatibility Rules",
    "Shared Exogenous Context", "Operational-Energy Bound Architecture",
    "Replacement Manufacturing Accounting", "Grid Treatment", "Survival / Residual Service",
    "Resistance Evidence Tiers", "R10 / R1s Treatment", "Pack-Loss-Share Treatment",
    "Mobility / Technical-Service Treatment", "Uncertainty / Scenario Hierarchy",
    "Revised Non-Robustness Gate", "Prohibited Scientific Claims", "P12 Compatibility",
    "P13 Compatibility", "P14 Compatibility", "P14.5 / P14.5I Failure Role",
    "IMPLEMENTATION_SPEC Amendment", "Machine-Readable Preregistration", "Revised P15R Definition",
    "Revised P16R Definition", "Files Created", "Files Modified", "Tests / Integrity Checks",
    "Lifecycle GHG Calculated", "Decision Bounds Calculated", "Replacement Optimization Performed",
    "Hard Blockers", "Final Status",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_original_rq_is_preserved_and_revised_rq_is_locked_exactly():
    text = SPEC.read_text(encoding="utf-8")
    assert HISTORICAL_PRIMARY_RQ in text
    assert REVISED_PRIMARY_RQ in text
    assert text.index(HISTORICAL_PRIMARY_RQ) < text.index("# P14.6C") < text.index(REVISED_PRIMARY_RQ)
    assert "SUPERSEDED BY APPROVED METHODOLOGICAL REVISION" in text
    assert "REVISED PRIMARY RQ — LOCKED" in text


def test_spec_amendment_is_append_only_and_records_pre_amendment_identity():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    recorded = prereg["pre_amendment_implementation_spec"]
    raw = SPEC.read_bytes()
    assert recorded == {
        "path": "docs/IMPLEMENTATION_SPEC.md",
        "sha256": "f8e29917daa0a4f999088005e0c85dffd6cc3cf3f828b1198dce4b6c1c1d3a80",
        "bytes": 32002,
        "line_count": 844,
    }
    assert sha256_bytes(raw[:recorded["bytes"]]) == recorded["sha256"]
    assert b"P14.6C" in raw[recorded["bytes"]:]


def test_s2_is_primary_s1_is_bound_layer_and_trajectory_outputs_are_superseded():
    text = SPEC.read_text(encoding="utf-8")
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert "S2 = PRIMARY" in text
    assert "S1 = SUPPORTING ONLY" in text
    assert prereg["architecture_roles"]["primary"] == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
    assert prereg["architecture_roles"]["supporting"] == "S1_SYMMETRIC_POLICY_ACCOUNTING_AND_ENDPOINT_BOUND_CONSTRUCTION_ONLY"
    prohibited = set(prereg["prohibited_outputs"])
    assert {"OPTIMAL_RETIREMENT_YEAR", "TIME_TO_STATE", "MILEAGE_TO_STATE"} <= prohibited
    assert {"EARLY_REPLACEMENT_CARBON_REGIME", "INTERIOR_REPLACEMENT_CARBON_REGIME",
            "USE_UNTIL_TECHNICAL_BOUNDARY_CARBON_REGIME"} <= prohibited


def test_estimand_sign_convention_and_exact_primary_labels():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["estimand"]["symbolic_definition"] == (
        "DeltaG(z, theta_R, theta_C) = G_R(z, theta_R) - G_C(z, theta_C)"
    )
    assert prereg["estimand"]["identification_type"] == "MECHANISTIC SET IDENTIFICATION"
    assert prereg["estimand"]["probability_interpretation"] == "NONE"
    assert prereg["sign_convention"]["positive"].startswith("IMMEDIATE_REPLACEMENT_HAS_HIGHER")
    assert prereg["sign_convention"]["negative"].startswith("IMMEDIATE_REPLACEMENT_HAS_LOWER")
    assert prereg["primary_carbon_classifications"] == [
        {"condition": "lower_DeltaG > 0", "label": "ROBUST CONTINUE"},
        {"condition": "upper_DeltaG < 0", "label": "ROBUST REPLACE"},
        {"condition": "lower_DeltaG <= 0 <= upper_DeltaG", "label": "CARBON DECISION INDETERMINATE"},
    ]


def test_theta_sets_symmetry_and_joint_compatibility_are_preregistered():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert [x["id"] for x in prereg["theta_C"]["endpoint_treatments"]] == ["C_LOW", "C_HIGH"]
    assert [x["id"] for x in prereg["theta_R"]["endpoint_treatments"]] == ["R_LOW", "R_HIGH"]
    assert all(x["predicted_trajectory"] is False for x in prereg["theta_C"]["endpoint_treatments"])
    assert all(x["predicted_trajectory"] is False for x in prereg["theta_R"]["endpoint_treatments"])
    assert prereg["symmetry_rules"]["status"] == "HARD_GATE"
    rules = set(prereg["joint_theta"]["rules"])
    assert "PRESERVE_SHARED_EXOGENOUS_CONTEXT_ACROSS_POLICIES" in rules
    assert "DO_NOT_CROSS_MATCH_EXOGENOUS_CORNERS_TO_MAXIMIZE_INTERVAL_WIDTH" in rules
    assert "FAIL_CLOSED_WHEN_COMPATIBILITY_CANNOT_BE_ESTABLISHED" in rules


def test_state_admissibility_resistance_and_technical_axes_are_separate():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["current_state_admissibility"]["time_to_state_used"] is False
    assert prereg["current_state_admissibility"]["experimental_elapsed_day_as_vehicle_age"] is False
    assert prereg["r10_r1s_rules"]["primary"] == "R10"
    assert prereg["r10_r1s_rules"]["alternative_physical_robustness"] == "R1s"
    assert prereg["r10_r1s_rules"]["merge_intervals"] is False
    assert prereg["r10_r1s_rules"]["timescale_switching"] is False
    assert prereg["technical_carbon_separation"] == "TECHNICALLY_REQUIRED_REPLACEMENT_DOES_NOT_IMPLY_ROBUST_REPLACE"
    assert prereg["technical_feasibility"]["universal_soh_threshold"] is False


def test_scenario_tiers_and_no_population_prevalence_claim_are_locked():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    tiers = prereg["scenario_hierarchy"]
    assert set(tiers) >= {"primary_identified_set", "structural_robustness_set", "extreme_stress_set"}
    assert tiers["pool_into_undifferentiated_mega_envelope"] is False
    assert tiers["extreme_stress_set"]["headline_eligible"] is False
    assert prereg["result_hierarchy"] == [
        "PRIMARY CLASSIFICATION", "STRUCTURAL ROBUSTNESS", "EXTREME/STRESS RESULT", "TECHNICAL FEASIBILITY"
    ]
    prohibited = set(prereg["prohibited_outputs"])
    assert "POPULATION_PROBABILITY_OF_ROBUST_REPLACE" in prohibited
    assert "FLEET_PREVALENCE_OF_A_DEGRADATION_STATE" in prohibited


def test_p15r_p16r_names_and_stage_gates_are_frozen_without_starting_them():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["next_stages"]["P15R"]["name"] == "P15R — STATE-CONDITIONED LIFECYCLE-GHG ACCOUNTING ENGINE"
    assert prereg["next_stages"]["P16R"]["name"] == "P16R — IDENTIFIED-SET DECISION BOUNDS & ROBUSTNESS CLASSIFICATION"
    assert prereg["next_stages"]["P15R"]["authorized_now"] is False
    assert prereg["next_stages"]["P16R"]["authorized_now"] is False
    assert prereg["next_stages"]["P16R"]["entry_gate"] == "P15R_PASS_AND_EXPLICIT_INSTRUCTION"
    assert prereg["next_stages"]["P15R"]["optimization_search"] is False
    assert prereg["next_stages"]["P16R"]["trajectory_optimization"] is False


def test_historical_failures_and_p12_p13_p14_outputs_remain_unchanged():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    log = LOG.read_text(encoding="utf-8")
    assert "Decision: REAL-WORLD DEGRADATION BRIDGE FAIL" in log
    assert "Decision: R3 REAL-WORLD DEGRADATION BRIDGE FAIL" in log
    assert prereg["historical_failure_invariants"]["failure_records_removed"] is False
    assert prereg["historical_failure_invariants"]["zero_admissible_r3_joint_rows"] is True
    for stage_paths in prereg["frozen_scientific_output_integrity"].values():
        for relative_path, expected_hash in stage_paths.items():
            assert sha256_bytes((ROOT / relative_path).read_bytes()) == expected_hash


def test_no_numerical_lifecycle_or_decision_artifact_is_declared():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["identified_interval"]["calculated_in_p146c"] is False
    assert prereg["disclosures"] == {
        "lifecycle_ghg_calculated": "NONE",
        "decision_bounds_calculated": "NONE",
        "replacement_optimization_performed": "NONE",
        "original_p145_p145i_failure_records_removed": "NO",
        "p12_p13_p14_scientific_outputs_modified": "NONE",
    }
    forbidden_patterns = ("*p146c*ghg*.parquet", "*p146c*delta*.parquet", "*p146c*decision*.parquet")
    assert not any(path for pattern in forbidden_patterns for path in ROOT.rglob(pattern))


def test_report_has_exact_44_sections_and_required_disclosures():
    text = REPORT.read_text(encoding="utf-8")
    found = re.findall(r"^## (\d+)\. (.+)$", text, flags=re.MULTILINE)
    assert [int(number) for number, _ in found] == list(range(1, 45))
    assert [title for _, title in found] == EXPECTED_REPORT_SECTIONS
    for phrase in (
        "Lifecycle GHG Calculated: `NONE`",
        "Decision Bounds Calculated: `NONE`",
        "Replacement Optimization Performed: `NONE`",
        "Original P14.5/P14.5I Failure Records Removed: `NO`",
        "P12/P13/P14 Scientific Outputs Modified: `NONE`",
        "TRAJECTORY-FREE METHODOLOGICAL REVISION FORMALLY LOCKED WITH BOUNDS",
    ):
        assert phrase in text
