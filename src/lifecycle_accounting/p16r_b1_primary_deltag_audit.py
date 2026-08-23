from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

THETA_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a3_theta_endpoint_sets.parquet"
)

MOBILITY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_mobility_use_scenarios.parquet"
)

SURVIVAL_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_vehicle_survival.parquet"
)

CHARGING_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_charging_conversion.parquet"
)

GRID_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_grid_pathways.parquet"
)

MFG_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_battery_manufacturing_pathways.parquet"
)

P13_CONFIG_FILE = (
    ROOT
    / "src"
    / "vehicle_energy"
    / "p13_config.yaml"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_b1_primary_deltag_audit.parquet"
)


print("=" * 78)
print("P16R-B1 — PRIMARY CONTEXT DELTAG ACCOUNTING AUDIT")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

import yaml

theta = pd.read_parquet(THETA_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with P13_CONFIG_FILE.open(encoding="utf-8") as f:
    p13_config = yaml.safe_load(f)


# ============================================================
# 2. PRIMARY MATCHED EXOGENOUS CONTEXT z
#
# This is one accounting audit context only:
#
# decision year: 2025
# current vehicle age: 0
# mileage: central_use
# survival: central
# charging: central_efficiency
# grid: MidCase / US_LOAD_WEIGHTED
# manufacturing: NMC811 / SPS / PROSPECTIVE
#
# No result generalization is allowed from B1.
# ============================================================

decision_year = 2025
current_age = 0


mob = mobility.loc[
    mobility["scenario_id"] == "central_use"
].copy()

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


chg = charging.loc[
    charging["scenario_id"] == "central_efficiency"
].copy()

assert len(chg) == 1

charging_multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)

charging_efficiency = float(
    chg.iloc[0]["charging_efficiency_fraction"]
)

assert abs(
    charging_multiplier
    - (1.0 / charging_efficiency)
) <= 1e-6


# ============================================================
# 3. CENTRAL SURVIVAL + RESIDUAL SERVICE
# ============================================================

surv = survival.loc[
    (survival["survival_scenario"] == "central")
    & (survival["current_vehicle_age_years"] == current_age)
].copy()

assert not surv.empty

surv = surv.sort_values(
    "years_after_conditioning"
)

surv["operation_year"] = (
    decision_year
    + surv["years_after_conditioning"]
)

surv = surv.loc[
    surv["operation_year"] <= 2050
].copy()

surv["expected_service_km"] = (
    annual_km
    * surv["conditional_survival"]
)

expected_residual_service_km = float(
    surv["expected_service_km"].sum()
)


# ============================================================
# 4. MIDCASE US LOAD-WEIGHTED GRID
# ============================================================

g = grid.loc[
    (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
    & (grid["scenario"] == "MidCase")
    & (grid["geography_level"] == "US_LOAD_WEIGHTED")
    & (grid["region"] == "US_LOAD_WEIGHTED")
    & (
        grid["calendar_year"]
        .isin(surv["operation_year"])
    )
][
    [
        "calendar_year",
        "grid_ci_gco2e_per_kwh",
    ]
].copy()

g = g.rename(
    columns={
        "calendar_year": "operation_year"
    }
)

annual = surv[
    [
        "operation_year",
        "expected_service_km",
    ]
].merge(
    g,
    on="operation_year",
    how="left",
    validate="one_to_one",
)

if annual["grid_ci_gco2e_per_kwh"].isna().any():
    raise RuntimeError(
        "P16R-B1 FAIL — missing grid CI."
    )


# ============================================================
# 5. CARBON-SERVICE FACTOR
#
# endpoint L2 kWh/km
# × charging multiplier
# × this factor
# = residual operational kg CO2e
# ============================================================

carbon_service_factor = float(
    (
        annual["expected_service_km"]
        * annual["grid_ci_gco2e_per_kwh"]
        / 1000.0
    ).sum()
)


# ============================================================
# 6. REPLACEMENT MANUFACTURING
# ============================================================

mfg_row = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == "SPS")
    & (mfg["benchmark_type"] == "PROSPECTIVE")
    & (mfg["calendar_year"] == decision_year)
].copy()

assert len(mfg_row) == 1

mfg_factor = float(
    mfg_row.iloc[0][
        "pack_ghg_kgco2e_per_kwh"
    ]
)

nominal_pack_kwh = float(
    p13_config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)

replacement_mfg_kgco2e = (
    nominal_pack_kwh
    * mfg_factor
)


# ============================================================
# 7. POLICY-SPECIFIC ENDPOINT ACCOUNTING
# ============================================================

theta = theta.copy()

theta["operational_kgco2e"] = (
    theta["endpoint_l2_kwh_per_km"]
    * charging_multiplier
    * carbon_service_factor
)

theta["replacement_manufacturing_kgco2e"] = (
    0.0
)

theta.loc[
    theta["policy"] == "R",
    "replacement_manufacturing_kgco2e",
] = replacement_mfg_kgco2e


theta["policy_varying_ghg_kgco2e"] = (
    theta["operational_kgco2e"]
    + theta["replacement_manufacturing_kgco2e"]
)


# ============================================================
# 8. SPLIT R AND C
# ============================================================

C = theta.loc[
    theta["policy"] == "C"
][
    [
        "current_state_key",
        "current_degradation_state_id",
        "theta_id",
        "endpoint_state_id",
        "endpoint_capacity_retention",
        "endpoint_relative_resistance",
        "endpoint_l2_kwh_per_km",
        "policy_varying_ghg_kgco2e",
        "cell_resistance_share",
        "fresh_usable_window_fraction",
        "topology_id",
    ]
].copy()

C = C.rename(
    columns={
        "theta_id":
            "theta_C",

        "endpoint_state_id":
            "C_endpoint_state_id",

        "endpoint_capacity_retention":
            "C_endpoint_capacity_retention",

        "endpoint_relative_resistance":
            "C_endpoint_relative_resistance",

        "endpoint_l2_kwh_per_km":
            "C_endpoint_l2_kwh_per_km",

        "policy_varying_ghg_kgco2e":
            "G_C_policy_varying_kgco2e",
    }
)


R = theta.loc[
    theta["policy"] == "R"
][
    [
        "current_state_key",
        "theta_id",
        "endpoint_state_id",
        "endpoint_capacity_retention",
        "endpoint_relative_resistance",
        "endpoint_l2_kwh_per_km",
        "policy_varying_ghg_kgco2e",
    ]
].copy()

R = R.rename(
    columns={
        "theta_id":
            "theta_R",

        "endpoint_state_id":
            "R_endpoint_state_id",

        "endpoint_capacity_retention":
            "R_endpoint_capacity_retention",

        "endpoint_relative_resistance":
            "R_endpoint_relative_resistance",

        "endpoint_l2_kwh_per_km":
            "R_endpoint_l2_kwh_per_km",

        "policy_varying_ghg_kgco2e":
            "G_R_policy_varying_kgco2e",
    }
)


# ============================================================
# 9. FORM ALL 2 × 2 ADMISSIBLE ENDPOINT COMBINATIONS
# ============================================================

pairs = C.merge(
    R,
    on="current_state_key",
    how="inner",
    validate="many_to_many",
)

assert not pairs.empty


counts = (
    pairs.groupby(
        "current_state_key"
    )
    .size()
)

if not (counts == 4).all():
    raise RuntimeError(
        "P16R-B1 FAIL — every current state "
        "must have exactly 4 endpoint combinations."
    )


# ============================================================
# 10. FIRST DELTAG CALCULATION
#
# DeltaG = G_R - G_C
#
# Positive:
# replacement has higher GHG.
#
# Negative:
# replacement has lower GHG.
# ============================================================

pairs["DeltaG_kgco2e"] = (
    pairs["G_R_policy_varying_kgco2e"]
    - pairs["G_C_policy_varying_kgco2e"]
)


# ============================================================
# 11. CONTEXT METADATA
# ============================================================

pairs["decision_calendar_year"] = 2025
pairs["current_vehicle_age_years"] = 0

pairs["mobility_scenario"] = "central_use"
pairs["survival_scenario"] = "central"
pairs["charging_scenario"] = "central_efficiency"

pairs["grid_scenario"] = "MidCase"
pairs["grid_geography"] = "US_LOAD_WEIGHTED"

pairs["manufacturing_pathway"] = "SPS"
pairs["manufacturing_benchmark_type"] = "PROSPECTIVE"

pairs["replacement_chemistry"] = "NMC811"

pairs["expected_residual_service_km"] = (
    expected_residual_service_km
)

pairs["replacement_manufacturing_kgco2e"] = (
    replacement_mfg_kgco2e
)


# ============================================================
# 12. IMPORTANT — NO IDENTIFIED BOUNDS YET
# ============================================================

pairs["identified_bounds_calculated"] = False
pairs["carbon_classification_calculated"] = False
pairs["identification_leverage_calculated"] = False
pairs["dual_state_discordance_calculated"] = False

pairs["analysis_stage"] = "P16R-B1_PRIMARY_DELTAG_AUDIT"


# ============================================================
# 13. SAFETY CHECKS
# ============================================================

assert (
    pairs["DeltaG_kgco2e"]
    .notna()
    .all()
)

assert not pairs[
    "identified_bounds_calculated"
].any()

assert not pairs[
    "carbon_classification_calculated"
].any()

assert not pairs[
    "identification_leverage_calculated"
].any()

assert not pairs[
    "dual_state_discordance_calculated"
].any()


for forbidden in [
    "lower_DeltaG",
    "upper_DeltaG",
    "ROBUST CONTINUE",
    "ROBUST REPLACE",
    "CARBON DECISION INDETERMINATE",
]:
    assert forbidden not in pairs.columns


# ============================================================
# 14. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

pairs.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 15. SUMMARY — ACCOUNTING AUDIT ONLY
# ============================================================

print(
    f"\nCurrent states: "
    f"{pairs['current_state_key'].nunique():,}"
)

print(
    f"Endpoint combinations: "
    f"{len(pairs):,}"
)

print(
    f"Expected residual service: "
    f"{expected_residual_service_km:.6f} km"
)

print(
    f"Replacement manufacturing: "
    f"{replacement_mfg_kgco2e:.6f} kg CO2e"
)


print("\nDeltaG range across endpoint combinations:")

print(
    float(pairs["DeltaG_kgco2e"].min()),
    "to",
    float(pairs["DeltaG_kgco2e"].max()),
    "kg CO2e",
)


print("\nDeltaG by endpoint combination:")

combo = (
    pairs.groupby(
        ["theta_R", "theta_C"],
        as_index=False,
    )
    .agg(
        min_DeltaG=(
            "DeltaG_kgco2e",
            "min",
        ),
        max_DeltaG=(
            "DeltaG_kgco2e",
            "max",
        ),
        n=(
            "DeltaG_kgco2e",
            "size",
        ),
    )
)

print(
    combo.to_string(
        index=False
    )
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-B1 PASS — PRIMARY CONTEXT DELTAG ACCOUNTING VERIFIED"
)

print(
    "FOUR ENDPOINT COMBINATIONS PER CURRENT STATE: VERIFIED"
)

print(
    "DELTAG SIGN CONVENTION: G_R - G_C"
)

print(
    "NO IDENTIFIED BOUNDS CALCULATED"
)

print(
    "NO ROBUST CARBON CLASSIFICATION PRODUCED"
)

print(
    "NO IDENTIFICATION LEVERAGE CALCULATED"
)

print(
    "NO DUAL-STATE DISCORDANCE RESULT PRODUCED"
)

print("=" * 78)