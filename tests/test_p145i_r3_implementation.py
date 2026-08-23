import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/P145I_R3_CONTROLLED_IMPLEMENTATION_REPORT.md"
SECTIONS = [
    "Governing Files Read", "Controlled Revision Acceptance", "Historical P14.5 Failure Preservation",
    "Frozen R3 Invariants", "Source and Version Verification", "E2 Exposure Implementation",
    "Mileage/Energy Preservation", "Charging and Parked-SOC Architecture", "Cell-Temperature Implementation",
    "BLAST Input-Domain Audit", "DENSO NMC622 Capacity Results", "LG MJ1 NMC811 Capacity Results",
    "Structural Model Comparison", "Conditional Model Sensitivities", "Long-Horizon Projection Treatment",
    "Liu Validation Implementation", "Liu Validation Results", "Deng Compatibility Wrapper",
    "Deng Reproduction Results", "Capacity Validation Metrics", "Capacity Validation Gate",
    "Resistance-Envelope Implementation", "R10 Support and Envelopes", "R1s Support and Envelopes",
    "Schreiber Automotive Outer Envelope", "Unsupported Resistance States", "Joint R3 Bridge Construction",
    "Valid Real-World Bridge Domain", "P13 Compatibility", "False-Optimum Precursor Audit",
    "Files Created", "Files Modified", "Tests Run", "Determinism Verification", "Scientific Fitting Performed",
    "Field Calibration Performed", "Lifecycle GHG Calculated", "Replacement Optimization Performed",
    "Unsupported Extrapolation Performed", "Existing P12/P13/P14 Outputs Modified",
    "P14.5 Failure Record Removed", "IMPLEMENTATION_SPEC Amendment", "Remaining Bounds", "Hard Blockers",
    "Final Status"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_report_exact_45_sections_and_disclosures():
    text = REPORT.read_text(encoding="utf-8")
    found = re.findall(r"^## (\d+)\. (.+)$", text, flags=re.MULTILINE)
    assert [int(n) for n, _ in found] == list(range(1, 46))
    assert [title for _, title in found] == SECTIONS
    for phrase in ["modeled real-world capacity trajectory", "conditional resistance-state envelope",
                   "real-world resistance trajectory unidentified", "R3 REAL-WORLD DEGRADATION BRIDGE FAIL",
                   "Scientific Fitting Performed: NONE", "Field Calibration Performed: NONE",
                   "Lifecycle GHG Calculated: NONE", "Replacement Optimization Performed: NONE",
                   "Unsupported Extrapolation Performed: NONE",
                   "Existing P12/P13/P14 Scientific Outputs Modified: NONE", "P14.5 Failure Record Removed: NO"]:
        assert phrase in text


def test_e2_profiles_exact_design_and_preservation():
    d = pd.read_parquet(ROOT / "data/processed/p145i_e2_exposure_profiles.parquet")
    assert d.profile_id.nunique() == 17
    assert set(d.state) == {"driving", "charging", "parked_not_charging"}
    assert d.groupby("profile_id").size().eq(35064).all()
    params = json.loads((ROOT / "results/intermediate/p145i_r3_parameters.json").read_text(encoding="utf-8"))
    assert max(max(x["distance_relative_error"], x["throughput_relative_error"]) for x in params["profile_summaries"]) <= 0.005
    assert {x["annual_km_target"] for x in params["profile_summaries"]} == {3218.688, 10729.496448, 19312.128}
    assert {x["charger_kw"] for x in params["profile_summaries"]} == {3.7, 11.0, 22.0, 75.0, 150.0}


def test_capacity_models_roles_domains_and_long_horizon():
    d = pd.read_parquet(ROOT / "data/processed/p145i_blast_capacity_trajectories.parquet")
    primary = set(d.loc[d.model_role.eq("PRIMARY_NON_AVERAGED"), "model_name"])
    assert primary == {"Nmc622_Gr_DENSO50Ah_Battery", "Nmc811_GrSi_LGMJ1_4Ah_Battery"}
    assert set(d.loc[d.model_role.eq("STRUCTURAL_SENSITIVITY"), "model_name"]) == {
        "NMC_Gr_75Ah_A", "NMC_Gr_50Ah_B1", "NMC_Gr_50Ah_B2", "Nmc811_GrSi_LGM50_5Ah_Battery"}
    assert d.degradation_scalar.eq(1).all() and d.source_native_parameters.all()
    assert set(d.input_domain_status) <= {"IN_DOMAIN", "CAPACITY MODEL MEMBER OUTSIDE VALIDATED INPUT DOMAIN"}
    assert d.loc[d.input_domain_status.ne("IN_DOMAIN"), "capacity_state_status"].eq("CAPACITY STATE UNSUPPORTED").all()
    assert d.loc[d.age_years.gt(3), "long_horizon_label"].eq("MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION").all()
    assert set(["annual_km", "cumulative_km", "cumulative_battery_throughput_kwh", "mean_cell_temperature_c", "mean_soc"]).issubset(d.columns)


def test_field_validation_is_external_and_preregistered_gate_fails():
    d = pd.read_parquet(ROOT / "data/processed/p145i_capacity_field_validation.parquet")
    assert set(d.source_id) == {"SRC_LIU_2025", "SRC_DENG_2023"}
    assert len(d.loc[d.source_id.eq("SRC_LIU_2025")]) == 2610
    assert "not asserted as 300 independent vehicles" in d.loc[d.source_id.eq("SRC_LIU_2025"), "claim_scope"].iloc[0]
    params = json.loads((ROOT / "results/intermediate/p145i_r3_parameters.json").read_text(encoding="utf-8"))
    assert params["overall_capacity_validation_status"] == "FAIL"
    assert params["scientific_fitting_performed"] == "NONE"
    assert params["field_calibration_performed"] == "NONE"


def test_deng_all_archives_complete():
    audit = json.loads((ROOT / "results/diagnostics/P145I_DENG_ARCHIVE_CHECKPOINT.json").read_text(encoding="utf-8"))
    assert audit["archive_attempted"] == audit["archive_completed"] == 20
    assert audit["status"] == "COMPLETE"
    assert all(item["status"] == "COMPLETE" for item in audit["archives"])


def test_resistance_is_conditional_fail_closed_and_timescales_separate():
    d = pd.read_parquet(ROOT / "data/processed/p145i_conditional_resistance_envelopes.parquet")
    assert set(d.resistance_endpoint) == {"R10", "R1s"}
    assert set(d.stress_class) == {"calendar_dominant", "use_dominant", "mixed_union"}
    assert d.capacity_matching_window.eq(0.025).all()
    supported = d.resistance_state_status.eq("SUPPORTED CONDITIONAL ENVELOPE")
    assert d.loc[supported, "observation_count"].ge(10).all()
    assert d.loc[supported, "cell_count"].ge(3).all()
    assert d.loc[supported, "condition_count"].ge(2).all()
    assert d.loc[~supported, "resistance_state_status"].eq("RESISTANCE STATE UNSUPPORTED").all()
    assert d.extreme_schreiber_excluded_from_outer.dropna().all()


def test_joint_bridge_and_p13_compatibility_fail_closed():
    d = pd.read_parquet(ROOT / "data/processed/p145i_r3_real_world_degradation_bridge.parquet")
    assert not d.joint_bridge_admissible.any()
    assert d.capacity_field_validation_status.eq("FAIL").all()
    assert d.lifecycle_ghg_calculated.eq(False).all()
    assert d.replacement_optimization_performed.eq(False).all()
    assert set(d.capacity_claim) == {"modeled real-world capacity trajectory"}
    assert set(d.resistance_claim) == {"conditional resistance-state envelope"}
    assert set(d.resistance_identifiability) == {"real-world resistance trajectory unidentified"}


def test_historical_integrity_and_no_spec_amendment_on_fail():
    pre = json.loads((ROOT / "data/metadata/P145I_PRE_IMPLEMENTATION_INTEGRITY.json").read_text(encoding="utf-8"))
    spec = pre.get("pre_amendment_implementation_spec") or pre["special_pre_change_records"]["docs/IMPLEMENTATION_SPEC.md"]
    # P14.5I itself made no amendment. A later explicitly approved P14.6C
    # append-only amendment must preserve the exact P14.5I-era byte prefix.
    current_spec = (ROOT / "docs/IMPLEMENTATION_SPEC.md").read_bytes()
    historical_prefix = current_spec[:spec["bytes"]]
    assert hashlib.sha256(historical_prefix).hexdigest() == spec["sha256"]
    if len(current_spec) > spec["bytes"]:
        assert b"P14.6C" in current_spec[spec["bytes"]:]
    manifest_records = pre.get("historical_stage_manifests")
    if manifest_records is None:
        manifest_records = [item for item in pre["frozen_artifacts"] if item["path"].endswith("_artifact_manifest.json")]
    for item in manifest_records:
        if item["path"] == "results/intermediate/p145_artifact_manifest.json":
            continue  # legacy manifest embeds the append-only decision log
        assert sha256(ROOT / item["path"]) == item["sha256"]
    expected_p145_science = {
        "data/processed/p145_automotive_bridge_validation.parquet": "8724eb6c483a437ef0dd97c159ec0602b4c6604b973e992cb12499b62165db50",
        "data/processed/p145_degradation_bridge_uncertainty.parquet": "c2174807a8ec3c4f7d712cab24f3113d5840227ccf4b6685bd410a6058838ab7",
        "data/processed/p145_real_world_degradation_bridge.parquet": "297f8ad11968e47eb477dd9e2718c039f79a72d1d2867d23b2a959fc0616b482",
    }
    for path, expected in expected_p145_science.items():
        assert sha256(ROOT / path) == expected


def test_determinism_two_complete_generations():
    result = json.loads((ROOT / "results/diagnostics/P145I_DETERMINISM_VERIFICATION.json").read_text(encoding="utf-8"))
    assert result["generation_count"] == 2
    assert result["identical_sha256"] is True
    assert result["mismatches"] == []
