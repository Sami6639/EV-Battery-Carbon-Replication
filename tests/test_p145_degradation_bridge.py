import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.degradation_bridge.p145_pipeline import generate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "src/degradation_bridge/p145_config.yaml").read_text(encoding="utf-8"))
BRIDGE = pd.read_parquet(ROOT / "data/processed/p145_real_world_degradation_bridge.parquet")
UNCERTAINTY = pd.read_parquet(ROOT / "data/processed/p145_degradation_bridge_uncertainty.parquet")
AUTOMOTIVE = pd.read_parquet(ROOT / "data/processed/p145_automotive_bridge_validation.parquet")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_time_and_mileage_axes_are_real_world_and_not_laboratory_aliases():
    assert BRIDGE.operation_year.min() == 2025 and BRIDGE.operation_year.max() == 2050
    assert np.allclose(BRIDGE.calendar_age_days, BRIDGE.calendar_age_years * 365.25)
    assert set(BRIDGE.annual_km) == {3218.688, 10729.496448, 19312.128}
    assert np.allclose(BRIDGE.cumulative_km, BRIDGE.annual_km * BRIDGE.calendar_age_years)


def test_usage_energy_and_throughput_proxy_are_traceable_and_monotone():
    assert set(BRIDGE.fresh_usable_window_fraction) == {0.85, 0.90, 0.95}
    assert np.allclose(BRIDGE.annual_l2_battery_side_kwh / BRIDGE.annual_km, 0.09324077636479178)
    for _, group in BRIDGE.groupby(["bridge_id", "mileage_scenario", "fresh_usable_window_fraction"]):
        assert group.sort_values("operation_year").pack_energy_equivalent_cycles_proxy.is_monotonic_increasing
    assert "not_source_cell_ah" in CONFIG["real_world_inputs"]["proxy_warning"].lower()


def test_capacity_and_resistance_state_assignment_is_baseline_only():
    baseline = BRIDGE.calendar_age_years.eq(0)
    assert np.allclose(BRIDGE.loc[baseline, ["capacity_retention", "r10_rel", "r1s_rel"]], 1.0)
    assert BRIDGE.loc[~baseline, ["capacity_retention", "r10_rel", "r1s_rel"]].isna().all().all()
    assert BRIDGE.loc[baseline, "state_available"].all() and not BRIDGE.loc[~baseline, "state_available"].any()
    assert set(BRIDGE.loc[baseline, "degradation_state_id"]) == {"FRESH_BASELINE"}
    assert set(BRIDGE.loc[baseline, "capacity_source_field"]) == {"reconstructed_capacity_retention"}
    assert not BRIDGE.capacity_source_field.str.contains("source_capacity_soh_percent").any()


def test_calendar_and_use_are_not_double_counted_or_added():
    rejected = UNCERTAINTY[UNCERTAINTY.bridge_id.eq("B_CALENDAR_PLUS_USE")]
    assert not rejected.calendar_component_supported.any()
    assert not rejected.joint_state_mapping_supported.any()
    assert set(rejected.disposition) == {"REJECTED_NO_SEPARABLE_ADDITIVE_EVIDENCE"}
    assert not rejected.calendar_use_double_counting_avoided.any()


def test_domain_status_prevents_multi_year_extrapolation():
    nonbaseline = BRIDGE.calendar_age_years.gt(0)
    assert set(BRIDGE.loc[nonbaseline, "degradation_domain_status"]) == {"DEGRADATION STATE OUTSIDE VALIDATED DOMAIN"}
    assert not BRIDGE.loc[BRIDGE.calendar_age_years.ge(2), "calendar_exposure_in_observed_luh_domain"].any()
    assert CONFIG["final_gate"] == "REAL-WORLD DEGRADATION BRIDGE FAIL"


def test_source_roles_and_schreiber_alignment_are_preserved():
    assert set(AUTOMOTIVE.primary_fit_role) == {"FORBIDDEN_VALIDATION_ONLY"}
    assert set(AUTOMOTIVE.exposure_alignment_to_luh) == {"NONE"}
    assert "EXTREME / CONDITIONAL ENVELOPE" in set(AUTOMOTIVE.validation_envelope_class)
    assert AUTOMOTIVE.laboratory_elapsed_days_from_selected_cu0.ge(0).all()


def test_no_outcome_leakage_or_prohibited_lifecycle_work():
    source = (ROOT / "src/degradation_bridge/p145_pipeline.py").read_text(encoding="utf-8").lower()
    forbidden = ["import lifecycle_ghg", "replacement_optimizer", "carbon_minimizing", "retirement_regime"]
    assert all(token not in source for token in forbidden)
    assert not BRIDGE.lifecycle_ghg_calculated.any()
    assert not BRIDGE.replacement_optimization_performed.any()
    assert CONFIG["locked_before_lifecycle_results"] is True


def test_deterministic_regeneration():
    targets = [ROOT / "data/processed/p145_real_world_degradation_bridge.parquet",
        ROOT / "data/processed/p145_degradation_bridge_uncertainty.parquet",
        ROOT / "data/processed/p145_automotive_bridge_validation.parquet",
        ROOT / "results/intermediate/p145_bridge_parameters.json"]
    before = [_sha(path) for path in targets]
    generate()
    after = [_sha(path) for path in targets]
    assert before == after

