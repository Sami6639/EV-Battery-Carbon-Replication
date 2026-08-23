from pathlib import Path
import json

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

P13_CONFIG = ROOT / "src/vehicle_energy/p13_config.yaml"
P13_PARAMS = ROOT / "results/intermediate/p13_vehicle_energy_model_parameters.json"

ENERGY_FILE = ROOT / "data/processed/p13_incremental_energy_penalty.parquet"
MOBILITY_FILE = ROOT / "data/processed/p14_mobility_use_scenarios.parquet"
CHARGING_FILE = ROOT / "data/processed/p14_charging_conversion.parquet"
GRID_FILE = ROOT / "data/processed/p14_grid_pathways.parquet"
MFG_FILE = ROOT / "data/processed/p14_battery_manufacturing_pathways.parquet"

OUTPUT_FILE = (
    ROOT
    / "results/intermediate"
    / "p15r_c1_accounting_components_2025.parquet"
)

print("=" * 78)
print("P15R-C1 — REAL PROJECT ACCOUNTING COMPONENT SMOKE TEST")
print("=" * 78)


# ============================================================
# 1. LOAD FROZEN MACHINE-READABLE PARAMETERS
# ============================================================

with P13_CONFIG.open(encoding="utf-8") as f:
    p13_config = yaml.safe_load(f)

nominal_pack_kwh = float(
    p13_config["representative_vehicle"]["nominal_pack_energy_kwh"]
)

with P13_PARAMS.open(encoding="utf-8") as f:
    p13_params = json.load(f)

combined_rows = [
    row
    for row in p13_params["fresh_baseline"]
    if row.get("drive_cycle") == "COMBINED_55_45"
]

assert len(combined_rows) == 1

fresh_combined_l2_kwh_per_km = float(
    combined_rows[0]["fresh_battery_side_kwh_per_km"]
)

print(f"Nominal pack energy: {nominal_pack_kwh:.9f} kWh")
print(
    "Fresh combined L2: "
    f"{fresh_combined_l2_kwh_per_km:.12f} kWh/km"
)


# ============================================================
# 2. LOAD REAL PROJECT INPUTS
# ============================================================

energy = pd.read_parquet(ENERGY_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)


# ============================================================
# 3. LOCK CENTRAL P15R-C1 CONTEXT
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"] == "central_use"
].copy()

assert len(mob) == 1

annual_km = float(mob.iloc[0]["annual_km"])


chg = charging.loc[
    charging["scenario_id"] == "central_efficiency"
].copy()

assert len(chg) == 1

charging_efficiency = float(
    chg.iloc[0]["charging_efficiency_fraction"]
)

l2_to_l3_multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)

assert 0 < charging_efficiency <= 1

assert abs(
    l2_to_l3_multiplier
    - (1.0 / charging_efficiency)
) <= 1e-6


# ============================================================
# 4. PRIMARY GRID CONTEXTS — 2025
# ============================================================

grid_2025 = grid.loc[
    (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
    & (grid["geography_level"] == "US_LOAD_WEIGHTED")
    & (grid["region"] == "US_LOAD_WEIGHTED")
    & (grid["calendar_year"] == 2025)
    & (
        grid["scenario"].isin(
            ["MidCase", "LowRECost", "HighRECost"]
        )
    )
].copy()

assert len(grid_2025) == 3

grid_2025 = grid_2025[
    [
        "scenario",
        "grid_ci_gco2e_per_kwh",
    ]
].rename(
    columns={
        "scenario": "grid_scenario",
    }
)


# ============================================================
# 5. PRIMARY NMC811 MANUFACTURING CONTEXTS — 2025
# ============================================================

mfg_2025 = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["benchmark_type"] == "PROSPECTIVE")
    & (mfg["calendar_year"] == 2025)
    & (mfg["pathway"].isin(["SPS", "SDS"]))
].copy()

assert len(mfg_2025) == 2

mfg_2025 = mfg_2025[
    [
        "pathway",
        "pack_ghg_kgco2e_per_kwh",
    ]
].rename(
    columns={
        "pathway": "manufacturing_pathway",
    }
)


# ============================================================
# 6. MATCHED EXOGENOUS CONTEXTS
# ============================================================

contexts = grid_2025.merge(
    mfg_2025,
    how="cross",
)

assert len(contexts) == 6

contexts["decision_calendar_year"] = 2025
contexts["mobility_scenario"] = "central_use"
contexts["annual_km"] = annual_km
contexts["charging_scenario"] = "central_efficiency"
contexts["charging_efficiency_fraction"] = charging_efficiency
contexts["l2_to_l3_multiplier"] = l2_to_l3_multiplier
contexts["replacement_chemistry"] = "NMC811"
contexts["replacement_pack_kwh"] = nominal_pack_kwh


# ============================================================
# 7. PRIMARY R10 MAIN PHYSICAL STATE SET
# ============================================================

allowed_classes = {
    "PRIMARY PHYSICAL SPECIFICATION",
    "AUTOMOTIVE-COMPATIBLE ENVELOPE",
}

allowed_domain_status = {
    "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
    "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
}

states = energy.loc[
    (energy["resistance_specification"] == "10-ms")
    & (~energy["conditional_extreme"])
    & (energy["physical_envelope_class"].isin(allowed_classes))
    & (energy["valid_domain_status"].isin(allowed_domain_status))
    & (energy["drive_cycle"].isin(["UDDS", "HWFET"]))
].copy()

assert not states.empty


# ============================================================
# 8. VERIFY FRESH UDDS/HWFET VALUES
# ============================================================

fresh_by_cycle = (
    states[
        [
            "drive_cycle",
            "fresh_battery_side_kwh_per_km",
        ]
    ]
    .drop_duplicates()
    .sort_values("drive_cycle")
)

counts = (
    fresh_by_cycle
    .groupby("drive_cycle")[
        "fresh_battery_side_kwh_per_km"
    ]
    .nunique()
)

assert counts.get("UDDS", 0) == 1
assert counts.get("HWFET", 0) == 1

fresh_udds = float(
    fresh_by_cycle.loc[
        fresh_by_cycle["drive_cycle"] == "UDDS",
        "fresh_battery_side_kwh_per_km",
    ].iloc[0]
)

fresh_hwfet = float(
    fresh_by_cycle.loc[
        fresh_by_cycle["drive_cycle"] == "HWFET",
        "fresh_battery_side_kwh_per_km",
    ].iloc[0]
)

fresh_reconstructed = (
    0.55 * fresh_udds
    + 0.45 * fresh_hwfet
)

assert abs(
    fresh_reconstructed
    - fresh_combined_l2_kwh_per_km
) <= 1e-10


# ============================================================
# 9. COLLAPSE UDDS/HWFET INTO LOCKED 55/45 COMBINED STATE
# ============================================================

key_cols = [
    "degradation_state_id",
    "source_id",
    "physical_envelope_class",
    "valid_domain_status",
    "topology_id",
    "nominal_pack_voltage_v",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
]

duplicate_mask = states.duplicated(
    subset=key_cols + ["drive_cycle"],
    keep=False,
)

if duplicate_mask.any():
    raise RuntimeError(
        "P15R-C1 FAIL — duplicate state/cycle rows found; "
        "no arbitrary aggregation permitted."
    )

aged_wide = (
    states[
        key_cols
        + [
            "drive_cycle",
            "aged_battery_side_kwh_per_km",
        ]
    ]
    .pivot(
        index=key_cols,
        columns="drive_cycle",
        values="aged_battery_side_kwh_per_km",
    )
    .reset_index()
)

if "UDDS" not in aged_wide.columns or "HWFET" not in aged_wide.columns:
    raise RuntimeError(
        "P15R-C1 FAIL — both UDDS and HWFET required."
    )

if aged_wide[["UDDS", "HWFET"]].isna().any().any():
    raise RuntimeError(
        "P15R-C1 FAIL — incomplete UDDS/HWFET state pair."
    )

aged_wide["continue_l2_kwh_per_km"] = (
    0.55 * aged_wide["UDDS"]
    + 0.45 * aged_wide["HWFET"]
)

aged_wide = aged_wide.drop(
    columns=["UDDS", "HWFET"]
)

aged_wide["replace_l2_kwh_per_km"] = (
    fresh_combined_l2_kwh_per_km
)


# ============================================================
# 10. CROSS SUPPORTED STATES WITH MATCHED 2025 CONTEXTS
# ============================================================

out = aged_wide.merge(
    contexts,
    how="cross",
)


# ============================================================
# 11. L2 -> L3 ACCOUNTING
# ============================================================

out["continue_l3_kwh_per_km"] = (
    out["continue_l2_kwh_per_km"]
    * out["l2_to_l3_multiplier"]
)

out["replace_l3_kwh_per_km"] = (
    out["replace_l2_kwh_per_km"]
    * out["l2_to_l3_multiplier"]
)


# ============================================================
# 12. ANNUAL GRID ELECTRICITY COMPONENTS
# ============================================================

out["continue_annual_grid_kwh"] = (
    out["continue_l3_kwh_per_km"]
    * out["annual_km"]
)

out["replace_annual_grid_kwh"] = (
    out["replace_l3_kwh_per_km"]
    * out["annual_km"]
)


# ============================================================
# 13. ANNUAL OPERATIONAL GHG COMPONENTS
# g/kWh -> kg via /1000
# ============================================================

out["continue_operational_kgco2e"] = (
    out["continue_annual_grid_kwh"]
    * out["grid_ci_gco2e_per_kwh"]
    / 1000.0
)

out["replace_operational_kgco2e"] = (
    out["replace_annual_grid_kwh"]
    * out["grid_ci_gco2e_per_kwh"]
    / 1000.0
)


# ============================================================
# 14. REPLACEMENT MANUFACTURING COMPONENT
# kgCO2e/kWh_pack × kWh_pack
# ============================================================

out["replacement_manufacturing_kgco2e"] = (
    out["replacement_pack_kwh"]
    * out["pack_ghg_kgco2e_per_kwh"]
)


# ============================================================
# 15. ACCOUNTING METADATA
# ============================================================

out["accounting_stage"] = "P15R-C1"

out["component_scope"] = (
    "REAL_PROJECT_COMPONENT_ACCOUNTING_2025_SMOKE_TEST"
)

out["original_battery_manufacturing_treatment"] = (
    "COMMON_INVARIANT_NOT_NUMERICALLY_ADDED_IN_C1"
)

out["lifecycle_total_calculated"] = False
out["delta_g_calculated"] = False
out["decision_bounds_calculated"] = False
out["carbon_classification_produced"] = False
out["replacement_optimization_performed"] = False


# ============================================================
# 16. HARD SAFETY CHECKS
# ============================================================

assert (out["continue_l2_kwh_per_km"] > 0).all()
assert (out["replace_l2_kwh_per_km"] > 0).all()

assert (out["continue_l3_kwh_per_km"] > 0).all()
assert (out["replace_l3_kwh_per_km"] > 0).all()

assert (out["grid_ci_gco2e_per_kwh"] >= 0).all()
assert (out["pack_ghg_kgco2e_per_kwh"] >= 0).all()

assert (out["replacement_manufacturing_kgco2e"] >= 0).all()

for forbidden in [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "ROBUST CONTINUE",
    "ROBUST REPLACE",
    "CARBON DECISION INDETERMINATE",
]:
    assert forbidden not in out.columns


# ============================================================
# 17. WRITE INTERMEDIATE ACCOUNTING COMPONENT TABLE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

out.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 18. DISPLAY AUDIT SUMMARY
# ============================================================

print("\nMatched contexts:", len(contexts))
print("Supported R10 state rows:", len(aged_wide))
print("Output rows:", len(out))

print("\nGrid scenarios:")
print(sorted(out["grid_scenario"].unique().tolist()))

print("\nManufacturing pathways:")
print(sorted(out["manufacturing_pathway"].unique().tolist()))

print("\nCell-sensitive loss shares:")
print(
    sorted(
        out["cell_resistance_share"]
        .dropna()
        .unique()
        .tolist()
    )
)

print("\nOperational component ranges:")
print(
    "Continue:",
    float(out["continue_operational_kgco2e"].min()),
    "to",
    float(out["continue_operational_kgco2e"].max()),
    "kg CO2e/year",
)

print(
    "Replace:",
    float(out["replace_operational_kgco2e"].min()),
    "to",
    float(out["replace_operational_kgco2e"].max()),
    "kg CO2e/year",
)

print("\nReplacement manufacturing component range:")
print(
    float(out["replacement_manufacturing_kgco2e"].min()),
    "to",
    float(out["replacement_manufacturing_kgco2e"].max()),
    "kg CO2e",
)

print("\nOutput:")
print(OUTPUT_FILE.relative_to(ROOT))

print("\n" + "=" * 78)
print("P15R-C1 PASS — REAL PROJECT ACCOUNTING COMPONENTS GENERATED")
print("L2 -> L3 -> OPERATIONAL GHG BOUNDARY VERIFIED")
print("REPLACEMENT MANUFACTURING COMPONENT VERIFIED")
print("NO LIFECYCLE TOTAL CALCULATED")
print("NO DELTAG CALCULATED")
print("NO IDENTIFIED DECISION BOUNDS CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")
print("NO REPLACEMENT OPTIMIZATION PERFORMED")
print("=" * 78)