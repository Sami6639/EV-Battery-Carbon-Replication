from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

THETA_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a3_theta_endpoint_sets.parquet"
)

LRMER_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cambium_2023_lrmer_co2e_combined.parquet"
)

P14_GRID_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_grid_pathways.parquet"
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
    / "p16r_d4e1c_cambium2023_lrmer_sensitivity.parquet"
)


print("=" * 78)
print("P16R-D4E1C — CAMBIUM-2023 LRMER SENSITIVITY")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED INPUTS
# ============================================================

theta = pd.read_parquet(THETA_FILE)
lrmer = pd.read_parquet(LRMER_FILE)
p14_grid = pd.read_parquet(P14_GRID_FILE)

mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
mfg = pd.read_parquet(MFG_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)


# ============================================================
# 2. SCIENTIFIC ROLE
#
# This is explicitly:
#
# Cambium-2023 LRMER sensitivity
#
# It is NOT:
# - Cambium-2024 marginal
# - national LRMER
# - primary average-CI accounting
# ============================================================

SENSITIVITY_LABEL = (
    "Cambium-2023 LRMER sensitivity"
)

assert (
    lrmer["metric_role"]
    == "MARGINAL_EMISSIONS_SENSITIVITY"
).all()

assert not (
    lrmer["region"]
    == "US_LOAD_WEIGHTED"
).any()

assert not lrmer[
    "gwp_selected_by_project"
].any()

assert not lrmer[
    "regional_average_created"
].any()

assert not lrmer[
    "us_load_weighted_lrmer_invented"
].any()


# ============================================================
# 3. SOURCE PANEL
# ============================================================

assert lrmer["scenario"].nunique() == 8
assert lrmer["region"].nunique() == 18

SOURCE_YEARS = [
    2025,
    2030,
    2035,
    2040,
    2045,
    2050,
]

assert sorted(
    lrmer["calendar_year"]
    .unique()
    .tolist()
) == SOURCE_YEARS


# ============================================================
# 4. INTERPOLATION CONTRACT
#
# Cambium source points are 5-year values.
# Operational accounting is annual.
#
# Use the already established P14 temporal interpolation
# convention. No extrapolation beyond source support.
# ============================================================

methods = (
    p14_grid.loc[
        p14_grid[
            "pathway_role"
        ]
        == "PRIMARY_AVERAGE_CI",
        "interpolation_method",
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

print("\nP14 grid interpolation methods:")
print(methods)

if not methods:
    raise RuntimeError(
        "P16R-D4E1C FAIL — P14 interpolation "
        "method is not machine-readable."
    )

if not any(
    "linear" in x.lower()
    for x in methods
):
    raise RuntimeError(
        "P16R-D4E1C FAIL — frozen P14 grid "
        "interpolation is not linear."
    )

INTERPOLATION_METHOD = (
    "LINEAR_WITHIN_SOURCE_SUPPORT"
)


# ============================================================
# 5. FIXED NON-GRID CONTEXT
#
# Only grid-emissions accounting changes.
# ============================================================

DECISION_YEAR = 2025
CURRENT_AGE = 0

MOBILITY_SCENARIO = "central_use"
SURVIVAL_SCENARIO = "central"
CHARGING_SCENARIO = "central_efficiency"

MFG_PATHWAY = "SPS"
MFG_BENCHMARK = "PROSPECTIVE"


# ============================================================
# 6. CENTRAL MILEAGE
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"]
    == MOBILITY_SCENARIO
].copy()

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


# ============================================================
# 7. CENTRAL CHARGING
# ============================================================

chg = charging.loc[
    charging["scenario_id"]
    == CHARGING_SCENARIO
].copy()

assert len(chg) == 1

multiplier = float(
    chg.iloc[0][
        "l2_to_l3_multiplier"
    ]
)

efficiency = float(
    chg.iloc[0][
        "charging_efficiency_fraction"
    ]
)

assert abs(
    multiplier
    - 1.0 / efficiency
) <= 1e-6


# ============================================================
# 8. CENTRAL SURVIVAL / SERVICE
# ============================================================

surv = survival.loc[
    (
        survival["survival_scenario"]
        == SURVIVAL_SCENARIO
    )
    & (
        survival[
            "current_vehicle_age_years"
        ]
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

assert sorted(
    surv["operation_year"].tolist()
) == list(
    range(2025, 2051)
)


# ============================================================
# 9. PRIMARY REPLACEMENT MANUFACTURING
# ============================================================

mrow = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == MFG_PATHWAY)
    & (
        mfg["benchmark_type"]
        == MFG_BENCHMARK
    )
    & (
        mfg["calendar_year"]
        == DECISION_YEAR
    )
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
# 10. THETA PAIRS
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
            "theta_id":
                "theta_C",

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
            "theta_id":
                "theta_R",

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
# 11. ANNUAL LRMER INTERPOLATION
#
# Each scenario-region is interpolated independently.
#
# No national aggregation.
# No cross-region averaging.
# No extrapolation.
# ============================================================

results = []

scenario_region_count = 0


for (
    scenario,
    region,
), group in lrmer.groupby(
    [
        "scenario",
        "region",
    ],
    sort=True,
):

    g = (
        group[
            [
                "calendar_year",
                "lrmer_gco2e_per_kwh",
            ]
        ]
        .sort_values(
            "calendar_year"
        )
        .drop_duplicates(
            "calendar_year"
        )
    )

    assert g[
        "calendar_year"
    ].tolist() == SOURCE_YEARS


    source_series = (
        g.set_index(
            "calendar_year"
        )[
            "lrmer_gco2e_per_kwh"
        ]
    )

    annual_index = pd.Index(
        range(2025, 2051),
        name="calendar_year",
    )

    annual_lrmer = (
        source_series
        .reindex(
            annual_index
        )
        .interpolate(
            method="linear",
            limit_area="inside",
        )
    )

    if annual_lrmer.isna().any():
        raise RuntimeError(
            "P16R-D4E1C FAIL — interpolation "
            f"missing values for {scenario} / {region}"
        )

    # Source anchor values must be preserved exactly.
    for year in SOURCE_YEARS:

        actual = float(
            annual_lrmer.loc[year]
        )

        expected = float(
            source_series.loc[year]
        )

        if not np.isclose(
            actual,
            expected,
            rtol=0,
            atol=1e-12,
        ):
            raise RuntimeError(
                "P16R-D4E1C FAIL — source anchor "
                "changed during interpolation."
            )


    annual_grid = pd.DataFrame(
        {
            "operation_year":
                annual_lrmer.index.astype(int),

            "lrmer_gco2e_per_kwh":
                annual_lrmer.values,
        }
    )


    accounting = surv[
        [
            "operation_year",
            "expected_service_km",
        ]
    ].merge(
        annual_grid,
        on="operation_year",
        how="left",
        validate="one_to_one",
    )

    if accounting[
        "lrmer_gco2e_per_kwh"
    ].isna().any():
        raise RuntimeError(
            "P16R-D4E1C FAIL — missing annual "
            "LRMER after service merge."
        )


    carbon_factor = float(
        (
            accounting[
                "expected_service_km"
            ]
            * accounting[
                "lrmer_gco2e_per_kwh"
            ]
            / 1000.0
        ).sum()
    )


    # ========================================================
    # 12. DELTAG FOR FOUR ENDPOINT COMBINATIONS
    # ========================================================

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


    # ========================================================
    # 13. IDENTIFIED BOUNDS
    # ========================================================

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

    b["identified_width"] = (
        b["upper_DeltaG"]
        - b["lower_DeltaG"]
    )


    # ========================================================
    # 14. EXACT FROZEN CLASSIFICATION RULE
    # ========================================================

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


    # ========================================================
    # 15. SENSITIVITY IDENTITY
    # ========================================================

    b["sensitivity_label"] = (
        SENSITIVITY_LABEL
    )

    b["lrmer_scenario"] = (
        scenario
    )

    b["gea_region"] = (
        region
    )

    b["grid_metric_role"] = (
        "MARGINAL_EMISSIONS_SENSITIVITY"
    )

    b["lrmer_source_version"] = 2023

    b["lrmer_gwp_convention"] = (
        "WORKBOOK_SAVED_100_YEAR_AR6"
    )

    b["lrmer_delivery_boundary"] = (
        "END_USE"
    )

    b["lrmer_levelization_horizon_years"] = 20

    b["lrmer_interpolation_method"] = (
        INTERPOLATION_METHOD
    )

    b["replacement_manufacturing_kgco2e"] = (
        replacement_mfg
    )

    b["expected_residual_service_km"] = (
        float(
            surv[
                "expected_service_km"
            ].sum()
        )
    )

    b["project_selected_gwp"] = False

    b["national_lrmer_aggregation"] = False

    b["time_to_state_used"] = False

    b["state_age_prevalence_interpretation"] = False

    results.append(b)

    scenario_region_count += 1


# ============================================================
# 16. COMBINE
# ============================================================

out = pd.concat(
    results,
    ignore_index=True,
)

assert scenario_region_count == (
    8 * 18
)

assert len(out) == (
    8
    * 18
    * 567
)


# ============================================================
# 17. HARD SCIENTIFIC CONTRACT
# ============================================================

assert (
    out["lrmer_scenario"]
    .nunique()
    == 8
)

assert (
    out["gea_region"]
    .nunique()
    == 18
)

assert not out[
    "project_selected_gwp"
].any()

assert not out[
    "national_lrmer_aggregation"
].any()

assert not out[
    "time_to_state_used"
].any()

assert not out[
    "state_age_prevalence_interpretation"
].any()


# ============================================================
# 18. CLASSIFICATION REVERSAL
#
# Primary average-CI result is ROBUST CONTINUE for 567/567.
# A sensitivity reversal is therefore any non-ROBUST CONTINUE.
# ============================================================

out["classification_reversal_vs_primary_average"] = (
    out["carbon_classification"]
    != "ROBUST CONTINUE"
)


# ============================================================
# 19. SAVE
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
# 20. SUMMARY
# ============================================================

summary = (
    out.groupby(
        [
            "lrmer_scenario",
            "gea_region",
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

        classification_n=(
            "carbon_classification",
            "nunique",
        ),

        reversals=(
            "classification_reversal_vs_primary_average",
            "sum",
        ),

        n_states=(
            "current_state_key",
            "nunique",
        ),
    )
)


print("\nLRMER sensitivity contexts:")

print(
    out[
        [
            "lrmer_scenario",
            "gea_region",
        ]
    ]
    .drop_duplicates()
    .shape[0]
)


print("\nLRMER sensitivity bound rows:")

print(
    len(out)
)


print("\nGlobal LRMER minimum lower_DeltaG:")

print(
    float(
        out[
            "lower_DeltaG"
        ].min()
    ),
    "kg CO2e",
)


print("\nGlobal LRMER maximum upper_DeltaG:")

print(
    float(
        out[
            "upper_DeltaG"
        ].max()
    ),
    "kg CO2e",
)


print("\nLRMER classifications:")

print(
    out[
        "carbon_classification"
    ]
    .value_counts()
    .to_string()
)


print(
    "\nClassification reversals "
    "vs primary average-CI:"
)

print(
    int(
        out[
            "classification_reversal_vs_primary_average"
        ].sum()
    )
)


print(
    "\nTen most replacement-favourable "
    "LRMER scenario-region contexts:"
)

print(
    summary.sort_values(
        "min_lower_DeltaG"
    )
    .head(10)
    .to_string(
        index=False
    )
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4E1C PASS — CAMBIUM-2023 LRMER SENSITIVITY COMPLETED"
)

print(
    "SOURCE SCENARIOS: 8/8"
)

print(
    "GEA REGIONS: 18/18"
)

print(
    "SENSITIVITY CONTEXTS: 144/144"
)

print(
    "WORKBOOK-NATIVE AR6 CO2E: USED"
)

print(
    "ANNUAL INTERPOLATION: WITHIN SOURCE SUPPORT ONLY"
)

print(
    "US_LOAD_WEIGHTED LRMER: NOT INVENTED"
)

print(
    "PRIMARY LABEL: CAMBIUM-2023 LRMER SENSITIVITY"
)

print("=" * 78)