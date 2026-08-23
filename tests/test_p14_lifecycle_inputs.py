from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "src/lifecycle_inputs/p14_config.yaml").read_text(encoding="utf-8"))
MILEAGE = pd.read_parquet(ROOT / "data/processed/p14_mobility_use_scenarios.parquet")
MOBILITY = pd.read_parquet(ROOT / "data/processed/p14_mobility_service_requirements.parquet")
SURVIVAL = pd.read_parquet(ROOT / "data/processed/p14_vehicle_survival.parquet")
GRID = pd.read_parquet(ROOT / "data/processed/p14_grid_pathways.parquet")
MFG = pd.read_parquet(ROOT / "data/processed/p14_battery_manufacturing_pathways.parquet")
CHARGING = pd.read_parquet(ROOT / "data/processed/p14_charging_conversion.parquet")
CALENDAR = pd.read_parquet(ROOT / "data/processed/p14_calendar_architecture.parquet")


def test_nhts_missing_codes_are_semantic_and_weights_preserved():
    assert set(MILEAGE.excluded_code_minus9_count) == {213}
    assert set(MILEAGE.weight_field) == {"WTHHFIN"}
    assert MILEAGE.sort_values("quantile").annual_km.is_monotonic_increasing


def test_mileage_and_mobility_rules_are_deterministic_and_no_soh_cutoff():
    assert np.allclose(MILEAGE.sort_values("quantile").annual_km, [3218.688, 10729.496448, 19312.128])
    assert not MOBILITY.universal_soh_cutoff.any()
    assert CONFIG["mobility_rule"]["universal_soh_cutoff"] == "NONE"


def test_survival_is_bounded_nonincreasing_and_conditioned():
    assert SURVIVAL.unconditional_survival.between(0, 1).all()
    assert SURVIVAL.conditional_survival.between(0, 1).all()
    for _, group in SURVIVAL.groupby(["survival_scenario", "current_vehicle_age_years"]):
        assert group.sort_values("attained_vehicle_age_years").conditional_survival.is_monotonic_decreasing
        assert np.isclose(group.conditional_survival.iloc[0], 1.0)
    assert set(SURVIVAL.vehicle_class) == {"passenger_cars"}
    assert not SURVIVAL.mileage_dependence_assumed.any()


def test_grid_is_cambium_2024_average_ci_and_no_extrapolation():
    assert set(GRID.dataset_version) == {2024}
    assert set(GRID.metric_identity) == {"aer_load_co2e"}
    assert set(GRID.pathway_role) == {"PRIMARY_AVERAGE_CI"}
    assert GRID.calendar_year.min() == 2025 and GRID.calendar_year.max() == 2050
    assert set(GRID.scenario) == {"MidCase", "LowRECost", "HighRECost"}
    national = GRID[GRID.geography_level == "US_LOAD_WEIGHTED"]
    assert np.allclose(national.aggregation_weight, 1.0)


def test_lrmer_remains_separate():
    lrmer = pd.read_parquet(ROOT / "data/processed/cambium_lrmer_2023_components.parquet")
    assert set(lrmer.dataset_version) == {2023}
    assert not GRID.source_id.str.contains("LRMER").any()


def test_manufacturing_is_pack_level_same_source_and_not_averaged():
    assert set(MFG.source_id) == {"SRC_LLAMAS_OROZCO_2023"}
    assert MFG.system_boundary.str.contains("pack_level").all()
    assert set(MFG.chemistry) == {"NMC111","NMC532","NMC622","NMC811","NMC955","NCA","LFP"}
    static = MFG[MFG.benchmark_type == "STATIC_SAME_SOURCE_2020"]
    assert static.groupby("chemistry").pack_ghg_kgco2e_per_kwh.nunique().eq(1).all()
    assert MFG.calendar_year.max() == 2050


def test_charging_is_bounded_and_no_atb_double_counting():
    assert CHARGING.charging_efficiency_fraction.between(0, 1, inclusive="neither").all()
    assert not CHARGING.atb_epa_conversion_applied.any()
    assert set(CHARGING.conversion_boundary) == {"L2_HV_BATTERY_SIDE_TO_L3_GRID_SIDE"}


def test_calendar_has_one_cohort_and_no_carbon_or_optimization():
    assert set(CALENDAR.cohort_id) == {"ENTRY_2025"}
    assert CALENDAR.operation_year.min() == 2025 and CALENDAR.operation_year.max() == 2050
    assert not CALENDAR.replacement_optimized.any()
    assert not CALENDAR.lifecycle_ghg_calculated.any()


def test_no_outcome_leakage_or_engine_imports():
    source = (ROOT / "src/lifecycle_inputs/p14_pipeline.py").read_text(encoding="utf-8").lower()
    forbidden = ["import lifecycle_ghg", "replacement_optimizer", "carbon_minimizing", "retirement_regime"]
    assert all(token not in source for token in forbidden)
    assert CONFIG["locked_before_lifecycle_results"] is True
