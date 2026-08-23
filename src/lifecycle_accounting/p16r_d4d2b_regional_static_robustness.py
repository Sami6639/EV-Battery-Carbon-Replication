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
    / "p16r_d4d2b_regional_static_robustness.parquet"
)


print("=" * 78)
print("P16R-D4D2B — REGIONAL GRID + STATIC MANUFACTURING ROBUSTNESS")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED INPUTS
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
# ============================================================

DECISION_YEAR = 2025
CURRENT_AGE = 0

MOBILITY_SCENARIO = "central_use"
SURVIVAL_SCENARIO = "central"
CHARGING_SCENARIO = "central_efficiency"

PRIMARY_GRID_SCENARIO = "MidCase"
PRIMARY_GRID_GEOGRAPHY = "US_LOAD_WEIGHTED"
PRIMARY_GRID_REGION = "US_LOAD_WEIGHTED"

PRIMARY_MFG_PATHWAY = "SPS"
PRIMARY_MFG_BENCHMARK = "PROSPECTIVE"


# ============================================================
# 3. CENTRAL MILEAGE
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"] == MOBILITY_SCENARIO
].copy()

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


# ============================================================
# 4. CENTRAL CHARGING
# ============================================================

chg = charging.loc[
    charging["scenario_id"] == CHARGING_SCENARIO
].copy()

assert len(chg) == 1

multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)

efficiency = float(
    chg.iloc[0]["charging_efficiency_fraction"]
)

assert abs(
    multiplier - 1.0 / efficiency
) <= 1e-6


# ============================================================
# 5. CENTRAL SURVIVAL
# ============================================================

surv = survival.loc[
    (
        survival["survival_scenario"]
        == SURVIVAL_SCENARIO
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

residual_service_km = float(
    surv["expected_service_km"].sum()
)


# ============================================================
# 6. THETA PAIRS
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
# 7. PACK CAPACITY
# ============================================================

nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)


# ============================================================
# 8. PRIMARY SPS MANUFACTURING BURDEN
# ============================================================

primary_mfg_row = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == PRIMARY_MFG_PATHWAY)
    & (mfg["benchmark_type"] == PRIMARY_MFG_BENCHMARK)
    & (mfg["calendar_year"] == DECISION_YEAR)
].copy()

assert len(primary_mfg_row) == 1

primary_mfg_factor = float(
    primary_mfg_row.iloc[0][
        "pack_ghg_kgco2e_per_kwh"
    ]
)

primary_replacement_mfg = (
    nominal_pack_kwh
    * primary_mfg_factor
)


# ============================================================
# 9. GENERIC BOUND FUNCTION
# ============================================================

def compute_bounds(
    carbon_service_factor,
    replacement_mfg,
):

    x = pairs.copy()

    x["DeltaG"] = (
        (
            x["R_endpoint_l2"]
            - x["C_endpoint_l2"]
        )
        * multiplier
        * carbon_service_factor
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

    return b


# ============================================================
# 10. REGIONAL GRID ROBUSTNESS
#
# Manufacturing held fixed at primary SPS 2025.
# Grid scenario held MidCase.
# Only geography/region changes.
# ============================================================

regions = sorted(
    grid.loc[
        (
            grid["pathway_role"]
            == "PRIMARY_AVERAGE_CI"
        )
        & (
            grid["scenario"]
            == PRIMARY_GRID_SCENARIO
        )
        & (
            grid["geography_level"]
            == "GEA_REGION"
        ),
        "region",
    ]
    .dropna()
    .unique()
    .tolist()
)

assert len(regions) == 18


regional_results = []

for region in regions:

    g = grid.loc[
        (
            grid["pathway_role"]
            == "PRIMARY_AVERAGE_CI"
        )
        & (
            grid["scenario"]
            == PRIMARY_GRID_SCENARIO
        )
        & (
            grid["geography_level"]
            == "GEA_REGION"
        )
        & (
            grid["region"] == region
        )
        & (
            grid["calendar_year"]
            .isin(surv["operation_year"])
        )
    ][
        [
            "calendar_year",
            "grid_ci_gco2e_per_kwh",
        ]
    ].rename(
        columns={
            "calendar_year":
                "operation_year"
        }
    )

    if len(g) != len(surv):
        raise RuntimeError(
            f"Regional grid support incomplete: {region}"
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
            f"Missing regional grid CI: {region}"
        )

    carbon_factor = float(
        (
            annual[
                "expected_service_km"
            ]
            * annual[
                "grid_ci_gco2e_per_kwh"
            ]
            / 1000.0
        ).sum()
    )

    b = compute_bounds(
        carbon_service_factor=carbon_factor,
        replacement_mfg=primary_replacement_mfg,
    )

    b["structural_family"] = (
        "REGIONAL_GRID"
    )

    b["structural_member"] = region

    b["grid_scenario"] = (
        PRIMARY_GRID_SCENARIO
    )

    b["grid_geography"] = (
        "GEA_REGION"
    )

    b["grid_region"] = region

    b["manufacturing_pathway"] = (
        PRIMARY_MFG_PATHWAY
    )

    b["manufacturing_benchmark_type"] = (
        PRIMARY_MFG_BENCHMARK
    )

    b["replacement_manufacturing_kgco2e"] = (
        primary_replacement_mfg
    )

    b["expected_residual_service_km"] = (
        residual_service_km
    )

    regional_results.append(b)


regional = pd.concat(
    regional_results,
    ignore_index=True,
)

assert len(regional) == 18 * 567


# ============================================================
# 11. STATIC SAME-SOURCE MANUFACTURING BENCHMARK
#
# Grid held at primary US_LOAD_WEIGHTED MidCase.
# Only manufacturing temporal treatment changes.
# ============================================================

g_primary = grid.loc[
    (
        grid["pathway_role"]
        == "PRIMARY_AVERAGE_CI"
    )
    & (
        grid["scenario"]
        == PRIMARY_GRID_SCENARIO
    )
    & (
        grid["geography_level"]
        == PRIMARY_GRID_GEOGRAPHY
    )
    & (
        grid["region"]
        == PRIMARY_GRID_REGION
    )
    & (
        grid["calendar_year"]
        .isin(surv["operation_year"])
    )
][
    [
        "calendar_year",
        "grid_ci_gco2e_per_kwh",
    ]
].rename(
    columns={
        "calendar_year":
            "operation_year"
    }
)

assert len(g_primary) == len(surv)

annual_primary = surv[
    [
        "operation_year",
        "expected_service_km",
    ]
].merge(
    g_primary,
    on="operation_year",
    how="left",
    validate="one_to_one",
)

assert not annual_primary[
    "grid_ci_gco2e_per_kwh"
].isna().any()

primary_carbon_factor = float(
    (
        annual_primary[
            "expected_service_km"
        ]
        * annual_primary[
            "grid_ci_gco2e_per_kwh"
        ]
        / 1000.0
    ).sum()
)


static_row = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == "Current")
    & (
        mfg["benchmark_type"]
        == "STATIC_SAME_SOURCE_2020"
    )
    & (
        mfg["calendar_year"]
        == DECISION_YEAR
    )
].copy()

assert len(static_row) == 1

static_mfg_factor = float(
    static_row.iloc[0][
        "pack_ghg_kgco2e_per_kwh"
    ]
)

static_replacement_mfg = (
    nominal_pack_kwh
    * static_mfg_factor
)


static_bounds = compute_bounds(
    carbon_service_factor=primary_carbon_factor,
    replacement_mfg=static_replacement_mfg,
)

static_bounds["structural_family"] = (
    "STATIC_MANUFACTURING"
)

static_bounds["structural_member"] = (
    "Current_STATIC_SAME_SOURCE_2020"
)

static_bounds["grid_scenario"] = (
    PRIMARY_GRID_SCENARIO
)

static_bounds["grid_geography"] = (
    PRIMARY_GRID_GEOGRAPHY
)

static_bounds["grid_region"] = (
    PRIMARY_GRID_REGION
)

static_bounds["manufacturing_pathway"] = (
    "Current"
)

static_bounds[
    "manufacturing_benchmark_type"
] = "STATIC_SAME_SOURCE_2020"

static_bounds[
    "replacement_manufacturing_kgco2e"
] = static_replacement_mfg

static_bounds[
    "expected_residual_service_km"
] = residual_service_km


# ============================================================
# 12. COMBINE — BUT KEEP FAMILIES DISTINCT
# ============================================================

out = pd.concat(
    [
        regional,
        static_bounds,
    ],
    ignore_index=True,
)


# ============================================================
# 13. CLAIM DISCIPLINE
# ============================================================

out["one_family_at_a_time"] = True

out["full_cartesian_structural_sweep"] = False

out["time_to_state_used"] = False

out["state_age_prevalence_interpretation"] = False

out["aged_power_capability_status"] = (
    "NOT STATE-RESOLVED"
)


# ============================================================
# 14. HARD CHECKS
# ============================================================

assert (
    regional[
        "structural_member"
    ].nunique()
    == 18
)

assert (
    regional[
        "current_state_key"
    ].nunique()
    == 567
)

assert (
    static_bounds[
        "current_state_key"
    ].nunique()
    == 567
)

assert not out[
    "full_cartesian_structural_sweep"
].any()

assert not out[
    "time_to_state_used"
].any()

assert not out[
    "state_age_prevalence_interpretation"
].any()


# ============================================================
# 15. SAVE
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
# 16. REGIONAL SUMMARY
# ============================================================

regional_summary = (
    regional.groupby(
        "structural_member",
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

        classification_n=(
            "carbon_classification",
            "nunique",
        ),

        n_states=(
            "current_state_key",
            "nunique",
        ),
    )
    .sort_values(
        "min_lower_DeltaG"
    )
)


# ============================================================
# 17. STATIC SUMMARY
# ============================================================

static_summary = (
    static_bounds.groupby(
        "structural_member",
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

        replacement_manufacturing_kgco2e=(
            "replacement_manufacturing_kgco2e",
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


# ============================================================
# 18. DISPLAY
# ============================================================

print("\nREGIONAL GRID ROBUSTNESS")

print(
    "Regions tested:",
    regional[
        "structural_member"
    ].nunique()
)

print(
    "Regional global minimum lower_DeltaG:",
    float(
        regional[
            "lower_DeltaG"
        ].min()
    ),
    "kg CO2e",
)

print(
    "Regional global maximum upper_DeltaG:",
    float(
        regional[
            "upper_DeltaG"
        ].max()
    ),
    "kg CO2e",
)

print(
    "Regional classification reversals:",
    int(
        (
            regional[
                "carbon_classification"
            ]
            != "ROBUST CONTINUE"
        ).sum()
    ),
)


print("\nFive most replacement-favourable regions:")

print(
    regional_summary.head(5)
    .to_string(
        index=False
    )
)


print("\nSTATIC MANUFACTURING ROBUSTNESS")

print(
    static_summary.to_string(
        index=False
    )
)

print(
    "Static manufacturing factor:",
    static_mfg_factor,
    "kg CO2e/kWh_pack",
)

print(
    "Static replacement burden:",
    static_replacement_mfg,
    "kg CO2e",
)

print(
    "Static classification reversals:",
    int(
        (
            static_bounds[
                "carbon_classification"
            ]
            != "ROBUST CONTINUE"
        ).sum()
    ),
)


print("\nGlobal D4D2B minimum lower_DeltaG:")

print(
    float(
        out[
            "lower_DeltaG"
        ].min()
    ),
    "kg CO2e",
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4D2B PASS — REGIONAL GRID AND "
    "STATIC MANUFACTURING ROBUSTNESS COMPLETED"
)

print(
    "GEA REGIONS: 18/18"
)

print(
    "STATIC SAME-SOURCE MANUFACTURING BENCHMARK: TESTED"
)

print(
    "ONE-FAMILY-AT-A-TIME DESIGN: PRESERVED"
)

print(
    "FULL CARTESIAN STRUCTURAL SWEEP: NOT PERFORMED"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print("=" * 78)