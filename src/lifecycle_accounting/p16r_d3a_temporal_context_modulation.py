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

TEMPORAL_LOCK_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b0t_temporal_context_audit.parquet"
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

DELTA_OUT = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3a_temporal_deltag.parquet"
)

BOUNDS_OUT = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3a_temporal_identified_bounds.parquet"
)


print("=" * 78)
print("P16R-D3A — TEMPORAL CARBON CONTEXT MODULATION")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

theta = pd.read_parquet(THETA_FILE)
temporal = pd.read_parquet(TEMPORAL_LOCK_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)


# ============================================================
# 2. LOCKED TEMPORAL CONTEXTS
# ============================================================

decision_years = (
    temporal.loc[
        temporal["temporal_context_supported"],
        "decision_calendar_year",
    ]
    .astype(int)
    .tolist()
)

assert decision_years == [
    2025,
    2030,
    2035,
    2040,
    2045,
]

grid_scenarios = [
    "MidCase",
    "LowRECost",
    "HighRECost",
]

mfg_pathways = [
    "SPS",
    "SDS",
]


# ============================================================
# 3. FIXED PRIMARY NON-TEMPORAL CONTEXT
#
# Age=0 is held fixed here to isolate the calendar-context layer.
#
# This does NOT mean an observed degradation state is typical
# at vehicle age zero.
#
# No state-age prevalence claim is permitted.
# ============================================================

current_vehicle_age = 0
mobility_scenario = "central_use"
survival_scenario = "central"
charging_scenario = "central_efficiency"


# ============================================================
# 4. CENTRAL MOBILITY
# ============================================================

mob = mobility.loc[
    mobility["scenario_id"] == mobility_scenario
].copy()

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


# ============================================================
# 5. CENTRAL CHARGING
# ============================================================

chg = charging.loc[
    charging["scenario_id"] == charging_scenario
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
    - 1.0 / charging_efficiency
) <= 1e-6


# ============================================================
# 6. PACK CAPACITY
# ============================================================

nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)


# ============================================================
# 7. SPLIT THETA C / R
# ============================================================

C = theta.loc[
    theta["policy"] == "C"
][
    [
        "current_state_key",
        "current_degradation_state_id",
        "theta_id",
        "endpoint_state_id",
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
        "endpoint_l2_kwh_per_km",
    ]
].copy()

R = R.rename(
    columns={
        "theta_id": "theta_R",
        "endpoint_state_id": "R_endpoint_state_id",
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

per_state = (
    pairs.groupby("current_state_key")
    .size()
)

assert (per_state == 4).all()


# ============================================================
# 8. GENERATE 30 MATCHED TEMPORAL CONTEXTS
# ============================================================

all_rows = []

context_diagnostics = []

for decision_year in decision_years:

    # --------------------------------------------------------
    # Survival / residual service
    # --------------------------------------------------------

    surv = survival.loc[
        (
            survival["survival_scenario"]
            == survival_scenario
        )
        & (
            survival["current_vehicle_age_years"]
            == current_vehicle_age
        )
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

    residual_service_km = float(
        surv["expected_service_km"].sum()
    )

    # --------------------------------------------------------
    # Grid pathway
    # --------------------------------------------------------

    for grid_scenario in grid_scenarios:

        g = grid.loc[
            (
                grid["pathway_role"]
                == "PRIMARY_AVERAGE_CI"
            )
            & (
                grid["scenario"]
                == grid_scenario
            )
            & (
                grid["geography_level"]
                == "US_LOAD_WEIGHTED"
            )
            & (
                grid["region"]
                == "US_LOAD_WEIGHTED"
            )
            & (
                grid["calendar_year"]
                .isin(
                    surv["operation_year"]
                )
            )
        ][
            [
                "calendar_year",
                "grid_ci_gco2e_per_kwh",
            ]
        ].copy()

        g = g.rename(
            columns={
                "calendar_year":
                    "operation_year"
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
                "P16R-D3A FAIL — missing grid CI."
            )

        carbon_service_factor = float(
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

        # ----------------------------------------------------
        # Manufacturing pathway
        # ----------------------------------------------------

        for pathway in mfg_pathways:

            mrow = mfg.loc[
                (
                    mfg["chemistry"]
                    == "NMC811"
                )
                & (
                    mfg["pathway"]
                    == pathway
                )
                & (
                    mfg["benchmark_type"]
                    == "PROSPECTIVE"
                )
                & (
                    mfg["calendar_year"]
                    == decision_year
                )
            ].copy()

            assert len(mrow) == 1

            mfg_factor = float(
                mrow.iloc[0][
                    "pack_ghg_kgco2e_per_kwh"
                ]
            )

            replacement_mfg = (
                nominal_pack_kwh
                * mfg_factor
            )

            out = pairs.copy()

            out[
                "G_C_operational_kgco2e"
            ] = (
                out[
                    "C_endpoint_l2_kwh_per_km"
                ]
                * charging_multiplier
                * carbon_service_factor
            )

            out[
                "G_R_operational_kgco2e"
            ] = (
                out[
                    "R_endpoint_l2_kwh_per_km"
                ]
                * charging_multiplier
                * carbon_service_factor
            )

            out[
                "G_R_replacement_manufacturing_kgco2e"
            ] = replacement_mfg

            out[
                "DeltaG_kgco2e"
            ] = (
                out[
                    "G_R_operational_kgco2e"
                ]
                + replacement_mfg
                - out[
                    "G_C_operational_kgco2e"
                ]
            )

            out[
                "decision_calendar_year"
            ] = decision_year

            out[
                "current_vehicle_age_years"
            ] = current_vehicle_age

            out[
                "mobility_scenario"
            ] = mobility_scenario

            out[
                "survival_scenario"
            ] = survival_scenario

            out[
                "charging_scenario"
            ] = charging_scenario

            out[
                "grid_scenario"
            ] = grid_scenario

            out[
                "grid_geography"
            ] = "US_LOAD_WEIGHTED"

            out[
                "manufacturing_pathway"
            ] = pathway

            out[
                "manufacturing_benchmark_type"
            ] = "PROSPECTIVE"

            out[
                "replacement_chemistry"
            ] = "NMC811"

            out[
                "expected_residual_service_km"
            ] = residual_service_km

            out[
                "carbon_service_factor"
            ] = carbon_service_factor

            out[
                "replacement_manufacturing_kgco2e"
            ] = replacement_mfg

            out[
                "time_to_state_interpretation"
            ] = False

            out[
                "state_age_prevalence_interpretation"
            ] = False

            out[
                "temporal_analysis_role"
            ] = "CONTEXT MODULATION"

            out["context_id"] = (
                f"TEMP_{decision_year}_"
                f"{grid_scenario}_"
                f"{pathway}"
            )

            all_rows.append(out)

            context_diagnostics.append(
                {
                    "context_id":
                        out[
                            "context_id"
                        ].iloc[0],

                    "decision_calendar_year":
                        decision_year,

                    "grid_scenario":
                        grid_scenario,

                    "manufacturing_pathway":
                        pathway,

                    "expected_residual_service_km":
                        residual_service_km,

                    "carbon_service_factor":
                        carbon_service_factor,

                    "replacement_manufacturing_kgco2e":
                        replacement_mfg,
                }
            )


delta = pd.concat(
    all_rows,
    ignore_index=True,
)

diagnostics = pd.DataFrame(
    context_diagnostics
)


# ============================================================
# 9. CONTRACT
# ============================================================

assert delta["context_id"].nunique() == 30

expected_rows = (
    30
    * theta["current_state_key"].nunique()
    * 4
)

assert len(delta) == expected_rows

assert not delta[
    "time_to_state_interpretation"
].any()

assert not delta[
    "state_age_prevalence_interpretation"
].any()


# ============================================================
# 10. IDENTIFIED BOUNDS
# ============================================================

group_cols = [
    "context_id",
    "decision_calendar_year",
    "grid_scenario",
    "manufacturing_pathway",
    "current_state_key",
    "current_degradation_state_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "topology_id",
]


counts = (
    delta.groupby(
        group_cols,
        dropna=False,
    )
    .size()
)

assert (counts == 4).all()


bounds = (
    delta.groupby(
        group_cols,
        as_index=False,
        dropna=False,
    )
    .agg(
        lower_DeltaG_kgco2e=(
            "DeltaG_kgco2e",
            "min",
        ),
        upper_DeltaG_kgco2e=(
            "DeltaG_kgco2e",
            "max",
        ),
        expected_residual_service_km=(
            "expected_residual_service_km",
            "first",
        ),
        carbon_service_factor=(
            "carbon_service_factor",
            "first",
        ),
        replacement_manufacturing_kgco2e=(
            "replacement_manufacturing_kgco2e",
            "first",
        ),
    )
)


bounds[
    "identified_width_kgco2e"
] = (
    bounds["upper_DeltaG_kgco2e"]
    - bounds["lower_DeltaG_kgco2e"]
)


# ============================================================
# 11. EXACT CLASSIFICATION
# ============================================================

def classify(row):

    if row["lower_DeltaG_kgco2e"] > 0:
        return "ROBUST CONTINUE"

    if row["upper_DeltaG_kgco2e"] < 0:
        return "ROBUST REPLACE"

    return "CARBON DECISION INDETERMINATE"


bounds[
    "carbon_classification"
] = bounds.apply(
    classify,
    axis=1,
)


bounds[
    "temporal_analysis_role"
] = "CONTEXT MODULATION"

bounds[
    "time_to_state_interpretation"
] = False

bounds[
    "state_age_prevalence_interpretation"
] = False


# ============================================================
# 12. SAVE
# ============================================================

DELTA_OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

delta.to_parquet(
    DELTA_OUT,
    index=False,
)

bounds.to_parquet(
    BOUNDS_OUT,
    index=False,
)


# ============================================================
# 13. TEMPORAL SUMMARY
# ============================================================

summary = (
    bounds.groupby(
        [
            "decision_calendar_year",
            "grid_scenario",
            "manufacturing_pathway",
        ],
        as_index=False,
    )
    .agg(
        min_lower_DeltaG=(
            "lower_DeltaG_kgco2e",
            "min",
        ),
        max_upper_DeltaG=(
            "upper_DeltaG_kgco2e",
            "max",
        ),
        min_width=(
            "identified_width_kgco2e",
            "min",
        ),
        max_width=(
            "identified_width_kgco2e",
            "max",
        ),
        replacement_manufacturing_kgco2e=(
            "replacement_manufacturing_kgco2e",
            "first",
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
    .sort_values(
        [
            "decision_calendar_year",
            "grid_scenario",
            "manufacturing_pathway",
        ]
    )
)


# ============================================================
# 14. CLASSIFICATION COUNTS BY YEAR
# ============================================================

year_class = (
    bounds.groupby(
        [
            "decision_calendar_year",
            "carbon_classification",
        ],
        as_index=False,
    )
    .size()
)


# ============================================================
# 15. DISPLAY
# ============================================================

print(
    f"\nTemporal matched contexts: "
    f"{bounds['context_id'].nunique()}"
)

print(
    f"Temporal DeltaG rows: "
    f"{len(delta):,}"
)

print(
    f"Temporal bound rows: "
    f"{len(bounds):,}"
)


print("\nClassification counts by decision year:")

print(
    year_class.to_string(
        index=False
    )
)


print("\nTemporal context summary:")

print(
    summary.to_string(
        index=False
    )
)


print("\nReplacement-manufacturing range by year:")

mfg_summary = (
    summary.groupby(
        "decision_calendar_year"
    )[
        "replacement_manufacturing_kgco2e"
    ]
    .agg(["min", "max"])
)

print(
    mfg_summary.to_string()
)


print("\nResidual-service range by year:")

service_summary = (
    summary.groupby(
        "decision_calendar_year"
    )[
        "expected_residual_service_km"
    ]
    .first()
)

print(
    service_summary.to_string()
)


print("\nGlobal temporal lower_DeltaG:")

print(
    float(
        bounds[
            "lower_DeltaG_kgco2e"
        ].min()
    )
)


print("\nGlobal temporal upper_DeltaG:")

print(
    float(
        bounds[
            "upper_DeltaG_kgco2e"
        ].max()
    )
)


print("\nOutputs:")

print(
    DELTA_OUT.relative_to(ROOT)
)

print(
    BOUNDS_OUT.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D3A PASS — TEMPORAL CONTEXT MODULATION CALCULATED"
)

print(
    "MATCHED TEMPORAL CONTEXTS: 30/30"
)

print(
    "DECISION YEAR USED AS EXOGENOUS CONTEXT ONLY"
)

print(
    "TIME-TO-STATE INTERPRETATION: NONE"
)

print(
    "STATE-AGE PREVALENCE CLAIM: NONE"
)

print(
    "TEMPORAL MANUFACTURING BURDEN: CALENDAR-SPECIFIC"
)

print(
    "GRID CI: CALENDAR-SPECIFIC"
)

print("=" * 78)