from pathlib import Path
import json

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

REGISTRY_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d2_context_registry.parquet"
)

PREREG_FILE = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
)

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
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

P13_PARAMS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d3_generic_context_smoke.parquet"
)


print("=" * 78)
print("P15R-D3 — GENERIC CONTEXT ACCOUNTING ENGINE SMOKE TEST")
print("=" * 78)


# ============================================================
# 1. LOAD AUTHORITATIVE INPUTS
# ============================================================

registry = pd.read_parquet(REGISTRY_FILE)
energy = pd.read_parquet(ENERGY_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with PREREG_FILE.open(encoding="utf-8") as f:
    prereg = json.load(f)

with P13_CONFIG_FILE.open(encoding="utf-8") as f:
    p13_config = yaml.safe_load(f)

with P13_PARAMS_FILE.open(encoding="utf-8") as f:
    p13_params = json.load(f)


# ============================================================
# 2. FROZEN P13 MACHINE-READABLE VALUES
# ============================================================

nominal_pack_kwh = float(
    p13_config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)

fresh_combined_rows = [
    row
    for row in p13_params["fresh_baseline"]
    if row.get("drive_cycle") == "COMBINED_55_45"
]

assert len(fresh_combined_rows) == 1

fresh_combined_l2 = float(
    fresh_combined_rows[0][
        "fresh_battery_side_kwh_per_km"
    ]
)


# ============================================================
# 3. REGISTRY VALIDATION HELPER
# ============================================================

def registry_allows(dimension, value):
    rows = registry.loc[
        registry["dimension"] == dimension,
        "value",
    ]

    return str(value) in set(
        rows.astype(str).tolist()
    )


# ============================================================
# 4. ENERGY STATE PREPARATION
# ============================================================

def prepare_energy_states(
    resistance_specification,
):

    if resistance_specification == "10-ms":
        allowed_classes = {
            "PRIMARY PHYSICAL SPECIFICATION",
            "AUTOMOTIVE-COMPATIBLE ENVELOPE",
        }

    elif resistance_specification == "1-s":
        allowed_classes = {
            "ALTERNATIVE 1-S SPECIFICATION",
            "AUTOMOTIVE-COMPATIBLE ENVELOPE",
        }

    else:
        raise ValueError(
            "Unsupported resistance specification."
        )

    allowed_domain = {
        "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
        "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
    }

    states = energy.loc[
        (
            energy["resistance_specification"]
            == resistance_specification
        )
        & (~energy["conditional_extreme"])
        & (
            energy["physical_envelope_class"]
            .isin(allowed_classes)
        )
        & (
            energy["valid_domain_status"]
            .isin(allowed_domain)
        )
        & (
            energy["drive_cycle"]
            .isin(["UDDS", "HWFET"])
        )
    ].copy()

    if states.empty:
        raise RuntimeError(
            "No supported physical states "
            f"for {resistance_specification}."
        )

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
            "Duplicate state/cycle rows found."
        )

    wide = (
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

    if (
        "UDDS" not in wide.columns
        or "HWFET" not in wide.columns
    ):
        raise RuntimeError(
            "UDDS/HWFET pair incomplete."
        )

    if wide[
        ["UDDS", "HWFET"]
    ].isna().any().any():
        raise RuntimeError(
            "Missing cycle value "
            "within a supported state."
        )

    wide[
        "continue_l2_kwh_per_km"
    ] = (
        0.55 * wide["UDDS"]
        + 0.45 * wide["HWFET"]
    )

    wide[
        "replace_l2_kwh_per_km"
    ] = fresh_combined_l2

    wide[
        "resistance_specification"
    ] = resistance_specification

    return wide.drop(
        columns=["UDDS", "HWFET"]
    )


# ============================================================
# 5. GENERIC ACCOUNTING FUNCTION
# ============================================================

def build_components(context):

    required = {
        "context_id",
        "decision_calendar_year",
        "current_vehicle_age_years",
        "mobility_scenario",
        "survival_scenario",
        "charging_scenario",
        "grid_scenario",
        "grid_geography",
        "grid_region",
        "manufacturing_pathway",
        "manufacturing_benchmark_type",
        "resistance_specification",
    }

    missing = (
        required
        - set(context)
    )

    if missing:
        raise RuntimeError(
            f"Context missing fields: {missing}"
        )

    # --------------------------------------------------------
    # Registry-controlled dimensions
    # --------------------------------------------------------

    for dimension in [
        "decision_calendar_year",
        "current_vehicle_age_years",
        "mobility_scenario",
        "survival_scenario",
        "charging_scenario",
        "grid_geography",
        "resistance_specification",
    ]:
        if not registry_allows(
            dimension,
            context[dimension],
        ):
            raise RuntimeError(
                f"Registry rejects "
                f"{dimension}="
                f"{context[dimension]}"
            )

    decision_year = int(
        context["decision_calendar_year"]
    )

    current_age = int(
        context["current_vehicle_age_years"]
    )

    # --------------------------------------------------------
    # Mobility
    # --------------------------------------------------------

    mob = mobility.loc[
        mobility["scenario_id"]
        == context["mobility_scenario"]
    ].copy()

    if len(mob) != 1:
        raise RuntimeError(
            "Mobility scenario did not resolve uniquely."
        )

    annual_km = float(
        mob.iloc[0]["annual_km"]
    )

    # --------------------------------------------------------
    # Charging
    # --------------------------------------------------------

    chg = charging.loc[
        charging["scenario_id"]
        == context["charging_scenario"]
    ].copy()

    if len(chg) != 1:
        raise RuntimeError(
            "Charging scenario did not resolve uniquely."
        )

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

    if abs(
        multiplier
        - 1.0 / efficiency
    ) > 1e-6:
        raise RuntimeError(
            "Charging multiplier identity failed."
        )

    # --------------------------------------------------------
    # Survival / expected residual service
    # --------------------------------------------------------

    surv = survival.loc[
        (
            survival["survival_scenario"]
            == context["survival_scenario"]
        )
        & (
            survival["current_vehicle_age_years"]
            == current_age
        )
    ].copy()

    if surv.empty:
        raise RuntimeError(
            "Survival context not found."
        )

    surv = surv.sort_values(
        "years_after_conditioning"
    )

    surv[
        "operation_year"
    ] = (
        decision_year
        + surv["years_after_conditioning"]
    )

    surv = surv.loc[
        surv["operation_year"] <= 2050
    ].copy()

    surv[
        "expected_service_km"
    ] = (
        annual_km
        * surv["conditional_survival"]
    )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    grid_rows = grid.loc[
        (
            grid["pathway_role"]
            == "PRIMARY_AVERAGE_CI"
        )
        & (
            grid["scenario"]
            == context["grid_scenario"]
        )
        & (
            grid["geography_level"]
            == context["grid_geography"]
        )
        & (
            grid["region"]
            == context["grid_region"]
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

    grid_rows = grid_rows.rename(
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
        grid_rows,
        on="operation_year",
        how="left",
        validate="one_to_one",
    )

    if annual[
        "grid_ci_gco2e_per_kwh"
    ].isna().any():
        raise RuntimeError(
            "Missing grid CI "
            "for residual-service year."
        )

    # This factor converts a constant
    # state-specific kWh/km value into
    # residual operational kg CO2e.
    carbon_service_factor = (
        (
            annual[
                "expected_service_km"
            ]
            * annual[
                "grid_ci_gco2e_per_kwh"
            ]
            / 1000.0
        )
        .sum()
    )

    expected_residual_service_km = float(
        annual[
            "expected_service_km"
        ].sum()
    )

    # --------------------------------------------------------
    # Manufacturing
    # --------------------------------------------------------

    mfg_rows = mfg.loc[
        (
            mfg["chemistry"]
            == "NMC811"
        )
        & (
            mfg["pathway"]
            == context[
                "manufacturing_pathway"
            ]
        )
        & (
            mfg["benchmark_type"]
            == context[
                "manufacturing_benchmark_type"
            ]
        )
        & (
            mfg["calendar_year"]
            == decision_year
        )
    ].copy()

    if len(mfg_rows) != 1:
        raise RuntimeError(
            "Manufacturing context "
            "did not resolve uniquely."
        )

    mfg_factor = float(
        mfg_rows.iloc[0][
            "pack_ghg_kgco2e_per_kwh"
        ]
    )

    replacement_mfg = (
        nominal_pack_kwh
        * mfg_factor
    )

    # --------------------------------------------------------
    # Physical states
    # --------------------------------------------------------

    states = prepare_energy_states(
        context[
            "resistance_specification"
        ]
    )

    out = states.copy()

    out[
        "C_operational_kgco2e"
    ] = (
        out[
            "continue_l2_kwh_per_km"
        ]
        * multiplier
        * carbon_service_factor
    )

    out[
        "R_operational_kgco2e"
    ] = (
        out[
            "replace_l2_kwh_per_km"
        ]
        * multiplier
        * carbon_service_factor
    )

    out[
        "C_replacement_manufacturing_kgco2e"
    ] = 0.0

    out[
        "R_replacement_manufacturing_kgco2e"
    ] = replacement_mfg

    out[
        "C_policy_varying_subtotal_kgco2e"
    ] = out[
        "C_operational_kgco2e"
    ]

    out[
        "R_policy_varying_subtotal_kgco2e"
    ] = (
        out[
            "R_operational_kgco2e"
        ]
        + out[
            "R_replacement_manufacturing_kgco2e"
        ]
    )

    # --------------------------------------------------------
    # Explicit context identity
    # --------------------------------------------------------

    for key, value in context.items():
        out[key] = value

    out[
        "replacement_chemistry"
    ] = "NMC811"

    out[
        "replacement_pack_kwh"
    ] = nominal_pack_kwh

    out[
        "pack_ghg_kgco2e_per_kwh"
    ] = mfg_factor

    out[
        "annual_km"
    ] = annual_km

    out[
        "charging_efficiency_fraction"
    ] = efficiency

    out[
        "l2_to_l3_multiplier"
    ] = multiplier

    out[
        "expected_residual_service_km"
    ] = expected_residual_service_km

    out[
        "common_original_battery_treatment"
    ] = (
        "COMMON_INVARIANT_NOT_A_POLICY_DRIVER"
    )

    out[
        "technical_feasibility_evaluated"
    ] = False

    out[
        "lifecycle_total_calculated"
    ] = False

    out[
        "delta_g_calculated"
    ] = False

    out[
        "decision_bounds_calculated"
    ] = False

    out[
        "carbon_classification_produced"
    ] = False

    out[
        "replacement_optimization_performed"
    ] = False

    return out


# ============================================================
# 6. FOUR PRE-SPECIFIED SMOKE CONTEXTS
#
# These are implementation tests only,
# not publication scenarios/results.
# ============================================================

SMOKE_CONTEXTS = [
    {
        "context_id":
        "PRIMARY_SMOKE",

        "decision_calendar_year":
        2025,

        "current_vehicle_age_years":
        0,

        "mobility_scenario":
        "central_use",

        "survival_scenario":
        "central",

        "charging_scenario":
        "central_efficiency",

        "grid_scenario":
        "MidCase",

        "grid_geography":
        "US_LOAD_WEIGHTED",

        "grid_region":
        "US_LOAD_WEIGHTED",

        "manufacturing_pathway":
        "SPS",

        "manufacturing_benchmark_type":
        "PROSPECTIVE",

        "resistance_specification":
        "10-ms",
    },

    {
        "context_id":
        "R1S_STRUCTURAL_SMOKE",

        "decision_calendar_year":
        2025,

        "current_vehicle_age_years":
        0,

        "mobility_scenario":
        "central_use",

        "survival_scenario":
        "central",

        "charging_scenario":
        "central_efficiency",

        "grid_scenario":
        "LowRECost",

        "grid_geography":
        "US_LOAD_WEIGHTED",

        "grid_region":
        "US_LOAD_WEIGHTED",

        "manufacturing_pathway":
        "SDS",

        "manufacturing_benchmark_type":
        "PROSPECTIVE",

        "resistance_specification":
        "1-s",
    },

    {
        "context_id":
        "AGE_USE_SURVIVAL_SMOKE",

        "decision_calendar_year":
        2025,

        "current_vehicle_age_years":
        10,

        "mobility_scenario":
        "higher_use",

        "survival_scenario":
        "lower_survival",

        "charging_scenario":
        "lower_efficiency",

        "grid_scenario":
        "HighRECost",

        "grid_geography":
        "US_LOAD_WEIGHTED",

        "grid_region":
        "US_LOAD_WEIGHTED",

        "manufacturing_pathway":
        "Current",

        "manufacturing_benchmark_type":
        "STATIC_SAME_SOURCE_2020",

        "resistance_specification":
        "10-ms",
    },

    {
        "context_id":
        "REGIONAL_GRID_SMOKE",

        "decision_calendar_year":
        2025,

        "current_vehicle_age_years":
        5,

        "mobility_scenario":
        "lower_use",

        "survival_scenario":
        "higher_survival",

        "charging_scenario":
        "higher_efficiency",

        "grid_scenario":
        "MidCase",

        "grid_geography":
        "GEA_REGION",

        "grid_region":
        "ERCOT",

        "manufacturing_pathway":
        "SPS",

        "manufacturing_benchmark_type":
        "PROSPECTIVE",

        "resistance_specification":
        "10-ms",
    },
]


# ============================================================
# 7. RUN SMOKE CONTEXTS
# ============================================================

outputs = []

for context in SMOKE_CONTEXTS:

    result = build_components(
        context
    )

    if result.empty:
        raise RuntimeError(
            f"Empty result for "
            f"{context['context_id']}"
        )

    outputs.append(result)

    print(
        "\nContext:",
        context["context_id"],
    )

    print(
        "  rows:",
        len(result),
    )

    print(
        "  residual service km:",
        float(
            result[
                "expected_residual_service_km"
            ].iloc[0]
        ),
    )

    print(
        "  C operational range:",
        float(
            result[
                "C_operational_kgco2e"
            ].min()
        ),
        "to",
        float(
            result[
                "C_operational_kgco2e"
            ].max()
        ),
    )

    print(
        "  R operational:",
        float(
            result[
                "R_operational_kgco2e"
            ].iloc[0]
        ),
    )

    print(
        "  replacement manufacturing:",
        float(
            result[
                "R_replacement_manufacturing_kgco2e"
            ].iloc[0]
        ),
    )


final = pd.concat(
    outputs,
    ignore_index=True,
)


# ============================================================
# 8. FINAL HARD CHECKS
# ============================================================

required_context_columns = {
    "decision_calendar_year",
    "current_vehicle_age_years",
    "mobility_scenario",
    "survival_scenario",
    "charging_scenario",
    "grid_geography",
    "grid_region",
    "resistance_specification",
}

assert required_context_columns <= set(
    final.columns
)

assert (
    set(
        final["context_id"].unique()
    )
    ==
    {
        x["context_id"]
        for x in SMOKE_CONTEXTS
    }
)

assert (
    final[
        "C_replacement_manufacturing_kgco2e"
    ]
    == 0
).all()

assert (
    final[
        "R_replacement_manufacturing_kgco2e"
    ]
    >= 0
).all()

assert not final[
    "lifecycle_total_calculated"
].any()

assert not final[
    "delta_g_calculated"
].any()

assert not final[
    "decision_bounds_calculated"
].any()

assert not final[
    "carbon_classification_produced"
].any()

assert not final[
    "replacement_optimization_performed"
].any()

for forbidden in [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "carbon_classification",
    "decision_classification",
]:
    assert forbidden not in final.columns


# ============================================================
# 9. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

final.to_parquet(
    OUTPUT_FILE,
    index=False,
)


print("\n" + "=" * 78)

print(
    "P15R-D3 PASS — GENERIC ACCOUNTING ENGINE "
    "RESOLVED PRIMARY AND STRUCTURAL SMOKE CONTEXTS"
)

print(
    f"SMOKE CONTEXTS PASSED: "
    f"{len(SMOKE_CONTEXTS)}/{len(SMOKE_CONTEXTS)}"
)

print(
    f"OUTPUT ROWS: {len(final):,}"
)

print(
    "ALL REQUIRED CONTEXT IDENTITIES PRESENT"
)

print(
    "NO LIFECYCLE TOTAL CALCULATED"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO DECISION BOUNDS CALCULATED"
)

print(
    "NO CARBON CLASSIFICATION PRODUCED"
)

print(
    "NO REPLACEMENT OPTIMIZATION PERFORMED"
)

print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)

print("=" * 78)