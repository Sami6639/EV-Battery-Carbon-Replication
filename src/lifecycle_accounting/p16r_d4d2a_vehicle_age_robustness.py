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
    / "p16r_d4d2a_vehicle_age_robustness.parquet"
)


print("=" * 78)
print("P16R-D4D2A — CURRENT VEHICLE AGE ROBUSTNESS")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

theta = pd.read_parquet(THETA_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)


# ============================================================
# 2. FIX ALL NON-AGE CONTEXT DIMENSIONS
# ============================================================

DECISION_YEAR = 2025

MOBILITY_SCENARIO = "central_use"
SURVIVAL_SCENARIO = "central"
CHARGING_SCENARIO = "central_efficiency"

GRID_SCENARIO = "MidCase"
GRID_GEOGRAPHY = "US_LOAD_WEIGHTED"
GRID_REGION = "US_LOAD_WEIGHTED"

MFG_PATHWAY = "SPS"


# ============================================================
# 3. USE EVERY SOURCE-SUPPORTED CURRENT VEHICLE AGE
# ============================================================

AGES = sorted(
    int(x)
    for x in survival[
        "current_vehicle_age_years"
    ].unique()
)

assert AGES == list(range(26))


# ============================================================
# 4. CENTRAL MILEAGE
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"] == MOBILITY_SCENARIO
]

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


# ============================================================
# 5. CENTRAL CHARGING
# ============================================================

chg = charging.loc[
    charging["scenario_id"] == CHARGING_SCENARIO
]

assert len(chg) == 1

multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)


# ============================================================
# 6. PRIMARY 2025 REPLACEMENT MANUFACTURING
# ============================================================

mrow = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == MFG_PATHWAY)
    & (mfg["benchmark_type"] == "PROSPECTIVE")
    & (mfg["calendar_year"] == DECISION_YEAR)
]

assert len(mrow) == 1

nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)

replacement_mfg = (
    nominal_pack_kwh
    * float(
        mrow.iloc[0][
            "pack_ghg_kgco2e_per_kwh"
        ]
    )
)


# ============================================================
# 7. PRIMARY GRID PATH
# ============================================================

g = grid.loc[
    (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
    & (grid["scenario"] == GRID_SCENARIO)
    & (grid["geography_level"] == GRID_GEOGRAPHY)
    & (grid["region"] == GRID_REGION)
    & (grid["calendar_year"].between(2025, 2050))
][
    [
        "calendar_year",
        "grid_ci_gco2e_per_kwh",
    ]
].copy()

assert len(g) == 26


# ============================================================
# 8. THETA PAIRS
# ============================================================

C = (
    theta.loc[
        theta["policy"] == "C",
        [
            "current_state_key",
            "theta_id",
            "endpoint_l2_kwh_per_km",
        ],
    ]
    .rename(
        columns={
            "theta_id": "theta_C",
            "endpoint_l2_kwh_per_km":
                "C_endpoint_l2",
        }
    )
)

R = (
    theta.loc[
        theta["policy"] == "R",
        [
            "current_state_key",
            "theta_id",
            "endpoint_l2_kwh_per_km",
        ],
    ]
    .rename(
        columns={
            "theta_id": "theta_R",
            "endpoint_l2_kwh_per_km":
                "R_endpoint_l2",
        }
    )
)

pairs = C.merge(
    R,
    on="current_state_key",
    how="inner",
    validate="many_to_many",
)

assert len(pairs) == 567 * 4


# ============================================================
# 9. AGE-CONDITIONED ACCOUNTING
# ============================================================

results = []

for current_age in AGES:

    surv = survival.loc[
        (
            survival["survival_scenario"]
            == SURVIVAL_SCENARIO
        )
        & (
            survival["current_vehicle_age_years"]
            == current_age
        )
    ].copy()

    if surv.empty:
        raise RuntimeError(
            f"No survival data for age {current_age}."
        )

    surv["operation_year"] = (
        DECISION_YEAR
        + surv["years_after_conditioning"]
    )

    surv = surv.loc[
        surv["operation_year"] <= 2050
    ].copy()

    surv["expected_service_km"] = (
        annual_km
        * surv["conditional_survival"]
    )

    annual = surv[
        [
            "operation_year",
            "expected_service_km",
        ]
    ].merge(
        g.rename(
            columns={
                "calendar_year": "operation_year"
            }
        ),
        on="operation_year",
        how="left",
        validate="one_to_one",
    )

    if annual[
        "grid_ci_gco2e_per_kwh"
    ].isna().any():
        raise RuntimeError(
            f"Missing grid CI for age {current_age}."
        )

    carbon_factor = float(
        (
            annual["expected_service_km"]
            * annual["grid_ci_gco2e_per_kwh"]
            / 1000.0
        ).sum()
    )

    residual_service_km = float(
        annual["expected_service_km"].sum()
    )

    x = pairs.copy()

    x["DeltaG"] = (
        (
            x["R_endpoint_l2"]
            - x["C_endpoint_l2"]
        )
        * multiplier
        * carbon_factor
        + replacement_mfg
    )

    b = (
        x.groupby(
            "current_state_key",
            as_index=False,
        )
        .agg(
            lower_DeltaG=(
                "DeltaG",
                "min",
            ),
            upper_DeltaG=(
                "DeltaG",
                "max",
            ),
        )
    )

    b["carbon_classification"] = (
        "CARBON DECISION INDETERMINATE"
    )

    b.loc[
        b["lower_DeltaG"] > 0,
        "carbon_classification",
    ] = "ROBUST CONTINUE"

    b.loc[
        b["upper_DeltaG"] < 0,
        "carbon_classification",
    ] = "ROBUST REPLACE"

    b["current_vehicle_age_years"] = (
        current_age
    )

    b["expected_residual_service_km"] = (
        residual_service_km
    )

    b["state_age_prevalence_interpretation"] = False

    b["degradation_state_assigned_by_age"] = False

    results.append(b)


out = pd.concat(
    results,
    ignore_index=True,
)


# ============================================================
# 10. HARD CONTRACT
# ============================================================

assert len(out) == 26 * 567

assert not out[
    "state_age_prevalence_interpretation"
].any()

assert not out[
    "degradation_state_assigned_by_age"
].any()


# ============================================================
# 11. SAVE
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
# 12. SUMMARY
# ============================================================

summary = (
    out.groupby(
        "current_vehicle_age_years",
        as_index=False,
    )
    .agg(
        min_lower_DeltaG=(
            "lower_DeltaG",
            "min",
        ),

        max_upper_DeltaG=(
            "upper_DeltaG",
            "max",
        ),

        expected_residual_service_km=(
            "expected_residual_service_km",
            "first",
        ),

        classification_n=(
            "carbon_classification",
            "nunique",
        ),

        n_states=(
            "current_state_key",
            "nunique",
        ),
    )
)


class_counts = (
    out.groupby(
        [
            "current_vehicle_age_years",
            "carbon_classification",
        ],
        as_index=False,
    )
    .size()
)


print("\nVehicle-age robustness summary:")

print(
    summary.to_string(
        index=False
    )
)


print("\nVehicle-age classification counts:")

print(
    class_counts.to_string(
        index=False
    )
)


print("\nGlobal age-robustness minimum lower_DeltaG:")

print(
    float(
        out["lower_DeltaG"].min()
    ),
    "kg CO2e",
)


print("\nAny classification reversal:")

print(
    bool(
        (
            out["carbon_classification"]
            != "ROBUST CONTINUE"
        ).any()
    )
)


print("\nResidual-service range across current ages:")

print(
    float(
        out[
            "expected_residual_service_km"
        ].min()
    ),
    "to",
    float(
        out[
            "expected_residual_service_km"
        ].max()
    ),
    "km",
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4D2A PASS — CURRENT VEHICLE AGE ROBUSTNESS COMPLETED"
)

print(
    "ALL SOURCE-SUPPORTED CURRENT AGES: 0–25 TESTED"
)

print(
    "AGE DID NOT ASSIGN BATTERY DEGRADATION STATE"
)

print(
    "STATE-AGE PREVALENCE CLAIM: NONE"
)

print(
    "PRIMARY MILEAGE / SURVIVAL / CHARGING / GRID / "
    "MANUFACTURING HELD FIXED"
)

print("=" * 78)