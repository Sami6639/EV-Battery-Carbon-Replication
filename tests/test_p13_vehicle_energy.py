from pathlib import Path

import fastsim
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "src" / "vehicle_energy" / "p13_config.yaml").read_text(encoding="utf-8"))
BASELINE = pd.read_parquet(ROOT / "data" / "processed" / "representative_bev_baseline.parquet")
PACK = pd.read_parquet(ROOT / "data" / "processed" / "p13_pack_electrical_states.parquet")
ENERGY = pd.read_parquet(ROOT / "data" / "processed" / "p13_incremental_energy_penalty.parquet")
TUM = pd.read_parquet(ROOT / "data" / "processed" / "tum_id3_vehicle_energy_validation_summary.parquet")


def test_fastsim_version_is_frozen_and_no_ageing_is_generated():
    assert fastsim.__version__ == "3.0.6"
    assert CONFIG["fastsim_version"] == "3.0.6"
    assert not BASELINE["fastsim_ageing_generated"].any()


def test_energy_boundaries_remain_distinguishable():
    assert set(BASELINE["energy_boundary"]) == {"L2_HV_BATTERY_SIDE"}
    assert CONFIG["energy_boundary"]["l3"] == "grid_side_electricity_not_calculated"
    assert not ENERGY["carbon_calculated"].any()


def test_source_soh_percent_is_forbidden_for_capacity_scaling():
    assert CONFIG["capacity_scaling"]["physical_field"] == "reconstructed_capacity_retention"
    assert CONFIG["capacity_scaling"]["forbidden_field_for_physical_scaling"] == "source_capacity_soh_percent"
    assert "source_capacity_soh_percent" not in ENERGY.columns
    assert ENERGY["capacity_retention"].between(0.0, 1.0).all()


def test_primary_and_alternative_resistance_specs_are_separate():
    primary = ENERGY[ENERGY.physical_envelope_class == "PRIMARY PHYSICAL SPECIFICATION"]
    alternative = ENERGY[ENERGY.physical_envelope_class == "ALTERNATIVE 1-S SPECIFICATION"]
    assert set(primary.resistance_specification) == {"10-ms"}
    assert set(alternative.resistance_specification) == {"1-s"}
    assert set(primary.degradation_state_id).isdisjoint(set(alternative.degradation_state_id))


def test_translation_is_not_direct_r_to_vehicle_energy_proportionality():
    sample = ENERGY[
        (ENERGY.physical_envelope_class == "PRIMARY PHYSICAL SPECIFICATION")
        & (ENERGY.relative_resistance > 1.05)
        & (ENERGY.cell_resistance_share == 1.0)
    ].iloc[0]
    energy_fraction = sample.incremental_battery_side_energy_percent / 100.0
    resistance_fraction = sample.relative_resistance - 1.0
    assert energy_fraction > 0.0
    assert energy_fraction < resistance_fraction / 10.0


def test_noncell_pack_resistance_is_fixed_while_cells_age():
    subset = PACK[
        (PACK.drive_cycle == "UDDS")
        & (PACK.topology_id == "central_voltage_108s")
        & (PACK.cell_resistance_share == 0.5)
        & (PACK.physical_envelope_class == "PRIMARY PHYSICAL SPECIFICATION")
    ].sort_values("relative_resistance")
    assert subset.fixed_noncell_pack_resistance_ohm.nunique() == 1
    assert subset.aged_cell_attributed_pack_resistance_ohm.iloc[-1] > subset.aged_cell_attributed_pack_resistance_ohm.iloc[0]


def test_topology_scaling_identity_is_deterministic():
    row = PACK.iloc[100]
    reconstructed = row.fresh_cell_attributed_pack_resistance_ohm * row.equivalent_parallel_count / row.series_count
    assert np.isclose(reconstructed, row.equivalent_fresh_cell_resistance_ohm, rtol=0.0, atol=1e-15)
    assert set(PACK.series_count) == {96, 108, 120}


def test_source_roles_cannot_leak_into_primary_fit_or_archetype():
    assert CONFIG["source_roles"]["tum_id3"] == "fresh_vehicle_electrical_plausibility_only"
    assert CONFIG["source_roles"]["schreiber"] == "independent_automotive_validation_only"
    primary = ENERGY[ENERGY.physical_envelope_class == "PRIMARY PHYSICAL SPECIFICATION"]
    assert set(primary.source_id) == {"SRC_LUH_2024"}
    assert CONFIG["representative_vehicle"]["role"] == "representative_us_light_duty_midsize_bev_archetype"


def test_no_p12_extrapolation_occurs():
    luh = ENERGY[ENERGY.source_id == "SRC_LUH_2024"]
    assert luh.exposure_days.min() >= CONFIG["p12_domain"]["resistance_min_days"]
    assert luh.exposure_days.max() <= CONFIG["p12_domain"]["resistance_max_days"]
    assert set(luh.valid_domain_status) == {"WITHIN_VALIDATED_DEGRADATION_DOMAIN"}


def test_no_carbon_lifecycle_or_survival_inputs_are_used():
    source = (ROOT / "src" / "vehicle_energy" / "p13_pipeline.py").read_text(encoding="utf-8").lower()
    forbidden_imports = ["cambium", "grid_ci", "manufacturing_ghg", "vehicle_survival", "replacement_timing"]
    assert all(token not in source for token in forbidden_imports)


def test_tum_is_validation_only_and_temperature_order_is_physical():
    assert set(TUM.validation_role) == {"FRESH_VEHICLE_ELECTRICAL_PLAUSIBILITY_ONLY"}
    r10 = TUM[TUM.resistance_specification == "10-ms"].sort_values("test_temperature_c")
    assert r10.tum_pack_resistance_median_ohm.is_monotonic_decreasing
    assert set(TUM.validation_classification) == {"PASS WITH BOUNDS"}


def test_bidirectional_current_proxy_is_present():
    assert BASELINE.hv_terminal_power_w.min() < 0.0
    assert BASELINE.hv_terminal_power_w.max() > 0.0


def test_configuration_was_locked_before_energy_results():
    assert CONFIG["locked_before_degradation_energy_results"] is True
    assert CONFIG["fresh_pack_loss_decomposition"]["outcome_selection_prohibited"] is True
