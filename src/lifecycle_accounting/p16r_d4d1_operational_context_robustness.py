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
    / "p16r_d4d1_operational_context_robustness.parquet"
)


print("=" * 78)
print("P16R-D4D1 — OPERATIONAL CONTEXT STRUCTURAL ROBUSTNESS")
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
# 2. FIXED PRIMARY REFERENCE CONTEXT
#
# One dimension changes at a time.
# No Cartesian structural sweep.
# ============================================================

DECISION_YEAR = 2025
CURRENT_AGE = 0

PRIMARY_GRID = "MidCase"
PRIMARY_MFG = "SPS"

PRIMARY_MILEAGE = "central_use"
PRIMARY_SURVIVAL = "central"
PRIMARY_CHARGING = "central_efficiency"


# ============================================================
# 3. STRUCTURAL SCENARIOS
# ============================================================

SCENARIOS = [
    {
        "structural_family": "MILEAGE",
        "structural_member": "lower_use",
        "mobility": "lower_use",
        "survival": PRIMARY_SURVIVAL,
        "charging": PRIMARY_CHARGING,
    },
    {
        "structural_family": "MILEAGE",
        "structural_member": "central_use",
        "mobility": "central_use",
        "survival": PRIMARY_SURVIVAL,
        "charging": PRIMARY_CHARGING,
    },
    {
        "structural_family": "MILEAGE",
        "structural_member": "higher_use",
        "mobility": "higher_use",
        "survival": PRIMARY_SURVIVAL,
        "charging": PRIMARY_CHARGING,
    },

    {
        "structural_family": "SURVIVAL",
        "structural_member": "lower_survival",
        "mobility": PRIMARY_MILEAGE,
        "survival": "lower_survival",
        "charging": PRIMARY_CHARGING,
    },
    {
        "structural_family": "SURVIVAL",
        "structural_member": "central",
        "mobility": PRIMARY_MILEAGE,
        "survival": "central",
        "charging": PRIMARY_CHARGING,
    },
    {
        "structural_family": "SURVIVAL",
        "structural_member": "higher_survival",
        "mobility": PRIMARY_MILEAGE,
        "survival": "higher_survival",
        "charging": PRIMARY_CHARGING,
    },

    {
        "structural_family": "CHARGING",
        "structural_member": "lower_efficiency",
        "mobility": PRIMARY_MILEAGE,
        "survival": PRIMARY_SURVIVAL,
        "charging": "lower_efficiency",
    },
    {
        "structural_family": "CHARGING",
        "structural_member": "central_efficiency",
        "mobility": PRIMARY_MILEAGE,
        "survival": PRIMARY_SURVIVAL,
        "charging": "central_efficiency",
    },
    {
        "structural_family": "CHARGING",
        "structural_member": "higher_efficiency",
        "mobility": PRIMARY_MILEAGE,
        "survival": PRIMARY_SURVIVAL,
        "charging": "higher_efficiency",
    },
]


# ============================================================
# 4. PRIMARY GRID
# ============================================================

g = grid.loc[
    (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
    & (grid["scenario"] == PRIMARY_GRID)
    & (grid["geography_level"] == "US_LOAD_WEIGHTED")
    & (grid["region"] == "US_LOAD_WEIGHTED")
    & (grid["calendar_year"].between(2025, 2050))
][
    [
        "calendar_year",
        "grid_ci_gco2e_per_kwh",
    ]
].copy()

assert len(g) == 26


# ============================================================
# 5. PRIMARY MANUFACTURING
# ============================================================

mrow = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == PRIMARY_MFG)
    & (mfg["benchmark_type"] == "PROSPECTIVE")
    & (mfg["calendar_year"] == DECISION_YEAR)
].copy()

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
# 6. SPLIT THETA
# ============================================================

C = (
    theta.loc[
        theta["policy"] == "C"
    ][
        [
            "current_state_key",
            "theta_id",
            "endpoint_l2_kwh_per_km",
        ]
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
        theta["policy"] == "R"
    ][
        [
            "current_state_key",
            "theta_id",
            "endpoint_l2_kwh_per_km",
        ]
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
# 7. RUN ONE-FAMILY-AT-A-TIME STRUCTURAL CONTEXTS
# ============================================================

results = []

for scenario in SCENARIOS:

    mob = mobility.loc[
        mobility["scenario_id"]
        == scenario["mobility"]
    ].copy()

    assert len(mob) == 1

    annual_km = float(
        mob.iloc[0]["annual_km"]
    )


    chg = charging.loc[
        charging["scenario_id"]
        == scenario["charging"]
    ].copy()

    assert len(chg) == 1

    multiplier = float(
        chg.iloc[0]["l2_to_l3_multiplier"]
    )


    surv = survival.loc[
        (
            survival["survival_scenario"]
            == scenario["survival"]
        )
        & (
            survival["current_vehicle_age_years"]
            == CURRENT_AGE
        )
    ].copy()

    assert not surv.empty

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
                "calendar_year":
                    "operation_year"
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
            "P16R-D4D1 FAIL — missing grid CI."
        )


    carbon_factor = float(
        (
            annual["expected_service_km"]
            * annual["grid_ci_gco2e_per_kwh"]
            / 1000.0
        ).sum()
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


    bounds = (
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

    bounds["carbon_classification"] = (
        "CARBON DECISION INDETERMINATE"
    )

    bounds.loc[
        bounds["lower_DeltaG"] > 0,
        "carbon_classification",
    ] = "ROBUST CONTINUE"

    bounds.loc[
        bounds["upper_DeltaG"] < 0,
        "carbon_classification",
    ] = "ROBUST REPLACE"


    bounds["structural_family"] = (
        scenario["structural_family"]
    )

    bounds["structural_member"] = (
        scenario["structural_member"]
    )

    bounds["mobility_scenario"] = (
        scenario["mobility"]
    )

    bounds["survival_scenario"] = (
        scenario["survival"]
    )

    bounds["charging_scenario"] = (
        scenario["charging"]
    )

    bounds["annual_km"] = annual_km

    bounds["expected_residual_service_km"] = (
        float(
            surv["expected_service_km"].sum()
        )
    )

    bounds["replacement_manufacturing_kgco2e"] = (
        replacement_mfg
    )

    results.append(bounds)


out = pd.concat(
    results,
    ignore_index=True,
)


# ============================================================
# 8. HARD CHECKS
# ============================================================

assert len(out) == 9 * 567

assert (
    out.groupby(
        [
            "structural_family",
            "structural_member",
        ]
    )[
        "current_state_key"
    ]
    .nunique()
    .eq(567)
    .all()
)


# ============================================================
# 9. SAVE
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
# 10. SUMMARY
# ============================================================

summary = (
    out.groupby(
        [
            "structural_family",
            "structural_member",
        ],
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
            "structural_family",
            "structural_member",
            "carbon_classification",
        ],
        as_index=False,
    )
    .size()
)


print("\nStructural-context bound summary:")

print(
    summary.to_string(
        index=False
    )
)


print("\nStructural-context classification counts:")

print(
    class_counts.to_string(
        index=False
    )
)


print("\nGlobal structural minimum lower_DeltaG:")

print(
    float(
        out["lower_DeltaG"].min()
    ),
    "kg CO2e",
)


print("\nAny classification reversal from ROBUST CONTINUE:")

print(
    bool(
        (
            out["carbon_classification"]
            != "ROBUST CONTINUE"
        ).any()
    )
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4D1 PASS — MILEAGE / SURVIVAL / "
    "CHARGING STRUCTURAL ROBUSTNESS COMPLETED"
)

print(
    "ONE-FAMILY-AT-A-TIME DESIGN: PRESERVED"
)

print(
    "FULL CARTESIAN STRUCTURAL SWEEP: NOT PERFORMED"
)

print(
    "PRIMARY GRID / MANUFACTURING HELD FIXED"
)

print("=" * 78)