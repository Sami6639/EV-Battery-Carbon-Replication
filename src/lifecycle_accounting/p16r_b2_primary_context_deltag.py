from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

THETA_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a3_theta_endpoint_sets.parquet"
)

B1_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_b1_primary_deltag_audit.parquet"
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

CONFIG_FILE = (
    ROOT
    / "src"
    / "vehicle_energy"
    / "p13_config.yaml"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_b2_primary_context_deltag.parquet"
)


print("=" * 78)
print("P16R-B2 — ALL PRIMARY MATCHED CONTEXTS DELTAG")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

theta = pd.read_parquet(THETA_FILE)
b1 = pd.read_parquet(B1_FILE)

mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)


# ============================================================
# 2. FROZEN PRIMARY CONTEXT
# ============================================================

decision_year = 2025
current_age = 0

grid_scenarios = [
    "MidCase",
    "LowRECost",
    "HighRECost",
]

manufacturing_pathways = [
    "SPS",
    "SDS",
]


# ============================================================
# 3. CENTRAL MILEAGE
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"] == "central_use"
].copy()

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


# ============================================================
# 4. CENTRAL CHARGING
# ============================================================

chg = charging.loc[
    charging["scenario_id"] == "central_efficiency"
].copy()

assert len(chg) == 1

charging_efficiency = float(
    chg.iloc[0]["charging_efficiency_fraction"]
)

charging_multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)

assert abs(
    charging_multiplier
    - (1.0 / charging_efficiency)
) <= 1e-6


# ============================================================
# 5. CENTRAL SURVIVAL / RESIDUAL SERVICE
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
# 6. GRID CARBON-SERVICE FACTORS
# ============================================================

grid_factors = {}

for scenario in grid_scenarios:

    g = grid.loc[
        (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
        & (grid["scenario"] == scenario)
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

    if annual[
        "grid_ci_gco2e_per_kwh"
    ].isna().any():
        raise RuntimeError(
            f"P16R-B2 FAIL — missing grid CI for {scenario}"
        )

    grid_factors[scenario] = float(
        (
            annual["expected_service_km"]
            * annual["grid_ci_gco2e_per_kwh"]
            / 1000.0
        ).sum()
    )


# ============================================================
# 7. REPLACEMENT MANUFACTURING FACTORS
# ============================================================

nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)

mfg_burdens = {}

for pathway in manufacturing_pathways:

    row = mfg.loc[
        (mfg["chemistry"] == "NMC811")
        & (mfg["pathway"] == pathway)
        & (mfg["benchmark_type"] == "PROSPECTIVE")
        & (mfg["calendar_year"] == decision_year)
    ].copy()

    assert len(row) == 1

    factor = float(
        row.iloc[0][
            "pack_ghg_kgco2e_per_kwh"
        ]
    )

    mfg_burdens[pathway] = (
        nominal_pack_kwh
        * factor
    )


# ============================================================
# 8. SPLIT THETA_C / THETA_R
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
        "cell_resistance_share",
        "fresh_usable_window_fraction",
        "topology_id",
    ]
].copy()

C = C.rename(
    columns={
        "theta_id": "theta_C",
        "endpoint_state_id": "C_endpoint_state_id",
        "endpoint_capacity_retention":
            "C_endpoint_capacity_retention",
        "endpoint_relative_resistance":
            "C_endpoint_relative_resistance",
        "endpoint_l2_kwh_per_km":
            "C_endpoint_l2_kwh_per_km",
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
    ]
].copy()

R = R.rename(
    columns={
        "theta_id": "theta_R",
        "endpoint_state_id": "R_endpoint_state_id",
        "endpoint_capacity_retention":
            "R_endpoint_capacity_retention",
        "endpoint_relative_resistance":
            "R_endpoint_relative_resistance",
        "endpoint_l2_kwh_per_km":
            "R_endpoint_l2_kwh_per_km",
    }
)


pairs = C.merge(
    R,
    on="current_state_key",
    how="inner",
    validate="many_to_many",
)

counts = (
    pairs.groupby("current_state_key")
    .size()
)

assert (counts == 4).all()


# ============================================================
# 9. SIX MATCHED PRIMARY CONTEXTS
# ============================================================

outputs = []

for grid_scenario in grid_scenarios:

    carbon_factor = grid_factors[
        grid_scenario
    ]

    for mfg_pathway in manufacturing_pathways:

        replacement_mfg = mfg_burdens[
            mfg_pathway
        ]

        out = pairs.copy()

        out["G_C_operational_kgco2e"] = (
            out["C_endpoint_l2_kwh_per_km"]
            * charging_multiplier
            * carbon_factor
        )

        out["G_R_operational_kgco2e"] = (
            out["R_endpoint_l2_kwh_per_km"]
            * charging_multiplier
            * carbon_factor
        )

        out[
            "G_R_replacement_manufacturing_kgco2e"
        ] = replacement_mfg

        out[
            "G_C_policy_varying_kgco2e"
        ] = out["G_C_operational_kgco2e"]

        out[
            "G_R_policy_varying_kgco2e"
        ] = (
            out["G_R_operational_kgco2e"]
            + out[
                "G_R_replacement_manufacturing_kgco2e"
            ]
        )

        out["DeltaG_kgco2e"] = (
            out["G_R_policy_varying_kgco2e"]
            - out["G_C_policy_varying_kgco2e"]
        )

        out["decision_calendar_year"] = 2025
        out["current_vehicle_age_years"] = 0

        out["mobility_scenario"] = "central_use"
        out["survival_scenario"] = "central"
        out["charging_scenario"] = "central_efficiency"

        out["grid_scenario"] = grid_scenario
        out["grid_geography"] = "US_LOAD_WEIGHTED"

        out["manufacturing_pathway"] = (
            mfg_pathway
        )

        out[
            "manufacturing_benchmark_type"
        ] = "PROSPECTIVE"

        out["replacement_chemistry"] = "NMC811"

        out[
            "expected_residual_service_km"
        ] = expected_residual_service_km

        out[
            "replacement_manufacturing_kgco2e"
        ] = replacement_mfg

        out["context_id"] = (
            "PRIMARY_2025_"
            + grid_scenario
            + "_"
            + mfg_pathway
        )

        out["identified_bounds_calculated"] = False
        out["carbon_classification_calculated"] = False
        out["identification_leverage_calculated"] = False
        out["dual_state_discordance_calculated"] = False

        outputs.append(out)


final = pd.concat(
    outputs,
    ignore_index=True,
)


# ============================================================
# 10. HARD CONTRACT CHECKS
# ============================================================

expected_context_ids = {
    f"PRIMARY_2025_{g}_{m}"
    for g in grid_scenarios
    for m in manufacturing_pathways
}

assert (
    set(final["context_id"].unique())
    == expected_context_ids
)

assert final["context_id"].nunique() == 6

expected_rows = (
    theta["current_state_key"].nunique()
    * 4
    * 6
)

assert len(final) == expected_rows

per_state_context = (
    final.groupby(
        [
            "context_id",
            "current_state_key",
        ]
    ).size()
)

assert (
    per_state_context == 4
).all()

assert (
    final["DeltaG_kgco2e"]
    .notna()
    .all()
)

assert not final[
    "identified_bounds_calculated"
].any()

assert not final[
    "carbon_classification_calculated"
].any()

assert not final[
    "identification_leverage_calculated"
].any()

assert not final[
    "dual_state_discordance_calculated"
].any()


# ============================================================
# 11. B1 REPRODUCTION CHECK
# ============================================================

b1_key = [
    "current_state_key",
    "theta_R",
    "theta_C",
]

b1_compare = b1[
    b1_key
    + ["DeltaG_kgco2e"]
].rename(
    columns={
        "DeltaG_kgco2e":
            "DeltaG_B1"
    }
)

b2_reference = final.loc[
    (final["grid_scenario"] == "MidCase")
    & (final["manufacturing_pathway"] == "SPS")
][
    b1_key
    + ["DeltaG_kgco2e"]
].rename(
    columns={
        "DeltaG_kgco2e":
            "DeltaG_B2"
    }
)

check = b1_compare.merge(
    b2_reference,
    on=b1_key,
    how="inner",
    validate="one_to_one",
)

assert len(check) == len(b1_compare)

max_diff = (
    check["DeltaG_B1"]
    - check["DeltaG_B2"]
).abs().max()

assert max_diff <= 1e-9


# ============================================================
# 12. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

final.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 13. SUMMARY — NO CLASSIFICATION
# ============================================================

summary = (
    final.groupby(
        [
            "context_id",
            "grid_scenario",
            "manufacturing_pathway",
        ],
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
    .sort_values(
        [
            "grid_scenario",
            "manufacturing_pathway",
        ]
    )
)


print(
    f"\nPrimary matched contexts: "
    f"{final['context_id'].nunique()}"
)

print(
    f"Current states: "
    f"{final['current_state_key'].nunique():,}"
)

print(
    f"Endpoint combinations per context: "
    f"{len(pairs):,}"
)

print(
    f"Total DeltaG rows: "
    f"{len(final):,}"
)

print(
    f"B1 reproduction max absolute difference: "
    f"{max_diff:.15e}"
)


print("\nDeltaG ranges by primary matched context:")

print(
    summary.to_string(
        index=False
    )
)


print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-B2 PASS — ALL PRIMARY MATCHED CONTEXT DELTAG VALUES GENERATED"
)

print(
    "PRIMARY MATCHED CONTEXTS: 6/6"
)

print(
    "B1 REPRODUCTION: PASS"
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