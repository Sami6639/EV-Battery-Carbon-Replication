from pathlib import Path
import re

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

SERVICE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_mobility_service_requirements.parquet"
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

PARAM_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

TEMPORAL_AUDIT = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b0t_temporal_context_audit.parquet"
)

R10_BOUNDS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3a_temporal_identified_bounds.parquet"
)

OUTPUT_BOUNDS = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d4b_r1s_temporal_bounds.parquet"
)

OUTPUT_COMPARE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d4b_r10_r1s_comparison.parquet"
)


print("=" * 78)
print("P16R-D4B — R1S TEMPORAL STRUCTURAL ROBUSTNESS")
print("=" * 78)


# ============================================================
# 1. HELPERS
# ============================================================

def canonical_state_id(value):

    s = str(value)

    s = re.sub(
        r"_10ms(?=_|$)",
        "",
        s,
        flags=re.IGNORECASE,
    )

    s = re.sub(
        r"_1s(?=_|$)",
        "",
        s,
        flags=re.IGNORECASE,
    )

    return s


ROLE_MAP = {
    "PRIMARY PHYSICAL SPECIFICATION":
        "CORE_PHYSICAL_STATE",

    "ALTERNATIVE 1-S SPECIFICATION":
        "CORE_PHYSICAL_STATE",

    "AUTOMOTIVE-COMPATIBLE ENVELOPE":
        "AUTOMOTIVE_COMPATIBLE_STATE",
}


# ============================================================
# 2. LOAD
# ============================================================

energy = pd.read_parquet(ENERGY_FILE)
service = pd.read_parquet(SERVICE_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)
temporal = pd.read_parquet(TEMPORAL_AUDIT)
r10_bounds = pd.read_parquet(R10_BOUNDS_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)


# ============================================================
# 3. LOCKED TEMPORAL CONTEXTS
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
# 4. CENTRAL TECHNICAL / USE CONTEXT
# ============================================================

central_service = service.loc[
    service["scenario_id"] == "mobility_central"
]

assert len(central_service) == 1

required_range_km = float(
    central_service.iloc[0][
        "required_single_service_distance_km"
    ]
)


mob = mobility.loc[
    mobility["scenario_id"] == "central_use"
]

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


chg = charging.loc[
    charging["scenario_id"] == "central_efficiency"
]

assert len(chg) == 1

charging_multiplier = float(
    chg.iloc[0]["l2_to_l3_multiplier"]
)

charging_efficiency = float(
    chg.iloc[0]["charging_efficiency_fraction"]
)

assert abs(
    charging_multiplier
    - 1.0 / charging_efficiency
) <= 1e-6


nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)


# ============================================================
# 5. SELECT R1S COMMON-SUPPORT STATES
# ============================================================

VALID_STATUS = {
    "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
    "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
}

r1s = energy.loc[
    (energy["resistance_specification"] == "1-s")
    & (~energy["conditional_extreme"])
    & (
        energy["physical_envelope_class"]
        .isin(
            {
                "ALTERNATIVE 1-S SPECIFICATION",
                "AUTOMOTIVE-COMPATIBLE ENVELOPE",
            }
        )
    )
    & (
        energy["valid_domain_status"]
        .isin(VALID_STATUS)
    )
    & (
        energy["drive_cycle"]
        .isin(["UDDS", "HWFET"])
    )
].copy()

assert len(r1s) == 1134


r1s["canonical_physical_state_id"] = (
    r1s["degradation_state_id"]
    .map(canonical_state_id)
)

r1s["canonical_evidence_role"] = (
    r1s["physical_envelope_class"]
    .map(ROLE_MAP)
)

assert not r1s[
    "canonical_evidence_role"
].isna().any()


# ============================================================
# 6. BUILD R1S COMBINED PHYSICAL STATES
# ============================================================

KEY = [
    "canonical_physical_state_id",
    "canonical_evidence_role",
    "source_id",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
]


dup = r1s.duplicated(
    subset=KEY + ["drive_cycle"],
    keep=False,
)

assert not dup.any()


wide = (
    r1s[
        KEY
        + [
            "drive_cycle",
            "aged_battery_side_kwh_per_km",
            "usable_battery_energy_kwh",
        ]
    ]
    .pivot(
        index=KEY,
        columns="drive_cycle",
        values=[
            "aged_battery_side_kwh_per_km",
            "usable_battery_energy_kwh",
        ],
    )
)

wide.columns = [
    f"{a}_{b}"
    for a, b in wide.columns
]

wide = wide.reset_index()

assert len(wide) == 567


needed = [
    "aged_battery_side_kwh_per_km_UDDS",
    "aged_battery_side_kwh_per_km_HWFET",
    "usable_battery_energy_kwh_UDDS",
    "usable_battery_energy_kwh_HWFET",
]

assert not wide[needed].isna().any().any()


usable_diff = (
    wide["usable_battery_energy_kwh_UDDS"]
    - wide["usable_battery_energy_kwh_HWFET"]
).abs()

assert usable_diff.max() <= 1e-10


wide["usable_battery_energy_kwh"] = (
    wide["usable_battery_energy_kwh_UDDS"]
)

wide["combined_aged_l2_kwh_per_km"] = (
    0.55
    * wide[
        "aged_battery_side_kwh_per_km_UDDS"
    ]
    +
    0.45
    * wide[
        "aged_battery_side_kwh_per_km_HWFET"
    ]
)

wide["technical_range_km"] = (
    wide["usable_battery_energy_kwh"]
    / wide["combined_aged_l2_kwh_per_km"]
)

wide["range_feasible"] = (
    wide["technical_range_km"]
    >= required_range_km
)


print(
    "\nR1s central range-feasible states:",
    int(wide["range_feasible"].sum()),
)

print(
    "R1s central range-infeasible states:",
    int((~wide["range_feasible"]).sum()),
)


# Structural carbon comparison uses common
# range-feasible physical support.
wide = wide.loc[
    wide["range_feasible"]
].copy()

if len(wide) != 567:
    raise RuntimeError(
        "P16R-D4B WITH BOUNDS — "
        "R1s central range support differs from R10."
    )


# ============================================================
# 7. R1S WORST ENDPOINT BY COMPATIBLE ARCHITECTURE
# ============================================================

ARCH = [
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
]

worst_idx = (
    wide.groupby(ARCH)[
        "combined_aged_l2_kwh_per_km"
    ]
    .idxmax()
)

worst = wide.loc[
    worst_idx
][
    ARCH
    + [
        "canonical_physical_state_id",
        "capacity_retention",
        "relative_resistance",
        "combined_aged_l2_kwh_per_km",
    ]
].rename(
    columns={
        "canonical_physical_state_id":
            "worst_state_id",

        "capacity_retention":
            "worst_capacity_retention",

        "relative_resistance":
            "worst_relative_resistance",

        "combined_aged_l2_kwh_per_km":
            "worst_l2_kwh_per_km",
    }
)


base = wide.merge(
    worst,
    on=ARCH,
    how="left",
    validate="many_to_one",
)


# ============================================================
# 8. FRESH REPLACEMENT REFERENCE
# ============================================================

import json

with PARAM_FILE.open(encoding="utf-8") as f:
    params = json.load(f)

fresh = [
    x
    for x in params["fresh_baseline"]
    if x.get("drive_cycle") == "COMBINED_55_45"
]

assert len(fresh) == 1

fresh_l2 = float(
    fresh[0][
        "fresh_battery_side_kwh_per_km"
    ]
)


# ============================================================
# 9. BUILD R1S THETA ENDPOINTS
# ============================================================

theta_rows = []

for row in base.itertuples(index=False):

    physical_key = (
        f"{row.canonical_physical_state_id}"
        f"|{row.topology_id}"
        f"|share={row.cell_resistance_share}"
        f"|window={row.fresh_usable_window_fraction}"
    )

    theta_rows.extend(
        [
            {
                "physical_key":
                    physical_key,

                "policy":
                    "C",

                "theta_id":
                    "C_LOW",

                "endpoint_l2":
                    row.combined_aged_l2_kwh_per_km,
            },

            {
                "physical_key":
                    physical_key,

                "policy":
                    "C",

                "theta_id":
                    "C_HIGH",

                "endpoint_l2":
                    row.worst_l2_kwh_per_km,
            },

            {
                "physical_key":
                    physical_key,

                "policy":
                    "R",

                "theta_id":
                    "R_LOW",

                "endpoint_l2":
                    fresh_l2,
            },

            {
                "physical_key":
                    physical_key,

                "policy":
                    "R",

                "theta_id":
                    "R_HIGH",

                "endpoint_l2":
                    row.worst_l2_kwh_per_km,
            },
        ]
    )


theta = pd.DataFrame(theta_rows)

assert len(theta) == 567 * 4


# ============================================================
# 10. SPLIT C / R
# ============================================================

C = (
    theta.loc[
        theta["policy"] == "C"
    ][
        [
            "physical_key",
            "theta_id",
            "endpoint_l2",
        ]
    ]
    .rename(
        columns={
            "theta_id":
                "theta_C",

            "endpoint_l2":
                "C_endpoint_l2",
        }
    )
)

R = (
    theta.loc[
        theta["policy"] == "R"
    ][
        [
            "physical_key",
            "theta_id",
            "endpoint_l2",
        ]
    ]
    .rename(
        columns={
            "theta_id":
                "theta_R",

            "endpoint_l2":
                "R_endpoint_l2",
        }
    )
)


pairs = C.merge(
    R,
    on="physical_key",
    how="inner",
    validate="many_to_many",
)

assert len(pairs) == 567 * 4


# ============================================================
# 11. TEMPORAL R1S ANALYSIS
# ============================================================

all_bounds = []

for decision_year in decision_years:

    surv = survival.loc[
        (survival["survival_scenario"] == "central")
        & (
            survival["current_vehicle_age_years"]
            == 0
        )
    ].copy()

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
        ].rename(
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

        assert not annual[
            "grid_ci_gco2e_per_kwh"
        ].isna().any()

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

        for pathway in mfg_pathways:

            mrow = mfg.loc[
                (mfg["chemistry"] == "NMC811")
                & (mfg["pathway"] == pathway)
                & (
                    mfg["benchmark_type"]
                    == "PROSPECTIVE"
                )
                & (
                    mfg["calendar_year"]
                    == decision_year
                )
            ]

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

            x = pairs.copy()

            x["DeltaG"] = (
                (
                    x["R_endpoint_l2"]
                    - x["C_endpoint_l2"]
                )
                * charging_multiplier
                * carbon_factor
                + replacement_mfg
            )

            x["decision_calendar_year"] = (
                decision_year
            )

            x["grid_scenario"] = (
                grid_scenario
            )

            x["manufacturing_pathway"] = (
                pathway
            )

            x["replacement_manufacturing"] = (
                replacement_mfg
            )

            x["residual_service_km"] = (
                residual_service_km
            )

            context_id = (
                f"TEMP_{decision_year}_"
                f"{grid_scenario}_{pathway}"
            )

            x["context_id"] = context_id

            b = (
                x.groupby(
                    [
                        "context_id",
                        "decision_calendar_year",
                        "grid_scenario",
                        "manufacturing_pathway",
                        "physical_key",
                    ],
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

                    replacement_manufacturing=(
                        "replacement_manufacturing",
                        "first",
                    ),

                    residual_service_km=(
                        "residual_service_km",
                        "first",
                    ),
                )
            )

            b["identified_width"] = (
                b["upper_DeltaG"]
                - b["lower_DeltaG"]
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

            all_bounds.append(b)


r1s_bounds = pd.concat(
    all_bounds,
    ignore_index=True,
)

assert len(r1s_bounds) == 30 * 567


# ============================================================
# 12. CANONICALIZE R10 RESULT FOR SAME PHYSICAL SUPPORT
# ============================================================

r10 = r10_bounds.copy()

r10[
    "canonical_physical_state_id"
] = (
    r10[
        "current_degradation_state_id"
    ]
    .map(canonical_state_id)
)

r10["physical_key"] = (
    r10[
        "canonical_physical_state_id"
    ].astype(str)
    + "|"
    + r10["topology_id"].astype(str)
    + "|share="
    + r10["cell_resistance_share"].astype(str)
    + "|window="
    + r10[
        "fresh_usable_window_fraction"
    ].astype(str)
)


r10_compare = r10[
    [
        "context_id",
        "physical_key",
        "lower_DeltaG_kgco2e",
        "upper_DeltaG_kgco2e",
        "carbon_classification",
    ]
].rename(
    columns={
        "lower_DeltaG_kgco2e":
            "r10_lower_DeltaG",

        "upper_DeltaG_kgco2e":
            "r10_upper_DeltaG",

        "carbon_classification":
            "r10_classification",
    }
)


r1s_compare = r1s_bounds[
    [
        "context_id",
        "physical_key",
        "lower_DeltaG",
        "upper_DeltaG",
        "carbon_classification",
    ]
].rename(
    columns={
        "lower_DeltaG":
            "r1s_lower_DeltaG",

        "upper_DeltaG":
            "r1s_upper_DeltaG",

        "carbon_classification":
            "r1s_classification",
    }
)


compare = r10_compare.merge(
    r1s_compare,
    on=[
        "context_id",
        "physical_key",
    ],
    how="inner",
    validate="one_to_one",
)


assert len(compare) == 30 * 567


# ============================================================
# 13. STRUCTURAL ROBUSTNESS METRICS
# ============================================================

compare["classification_reversal"] = (
    compare["r10_classification"]
    != compare["r1s_classification"]
)

compare["lower_DeltaG_shift_r1s_minus_r10"] = (
    compare["r1s_lower_DeltaG"]
    - compare["r10_lower_DeltaG"]
)

compare["upper_DeltaG_shift_r1s_minus_r10"] = (
    compare["r1s_upper_DeltaG"]
    - compare["r10_upper_DeltaG"]
)


# ============================================================
# 14. SAVE
# ============================================================

OUTPUT_BOUNDS.parent.mkdir(
    parents=True,
    exist_ok=True,
)

r1s_bounds.to_parquet(
    OUTPUT_BOUNDS,
    index=False,
)

compare.to_parquet(
    OUTPUT_COMPARE,
    index=False,
)


# ============================================================
# 15. SUMMARY
# ============================================================

print(
    f"\nR1s temporal bound rows: "
    f"{len(r1s_bounds):,}"
)

print(
    "R1s temporal contexts:",
    r1s_bounds["context_id"].nunique(),
)


print("\nR1s classifications:")

print(
    r1s_bounds[
        "carbon_classification"
    ]
    .value_counts()
    .to_string()
)


print("\nR10/R1s classification reversals:")

print(
    int(
        compare[
            "classification_reversal"
        ].sum()
    )
)


print("\nR1s global minimum lower_DeltaG:")

print(
    float(
        r1s_bounds[
            "lower_DeltaG"
        ].min()
    ),
    "kg CO2e",
)


print("\nR1s global maximum upper_DeltaG:")

print(
    float(
        r1s_bounds[
            "upper_DeltaG"
        ].max()
    ),
    "kg CO2e",
)


print("\nR1s - R10 lower_DeltaG shift range:")

print(
    float(
        compare[
            "lower_DeltaG_shift_r1s_minus_r10"
        ].min()
    ),
    "to",
    float(
        compare[
            "lower_DeltaG_shift_r1s_minus_r10"
        ].max()
    ),
    "kg CO2e",
)


print("\nR1s - R10 upper_DeltaG shift range:")

print(
    float(
        compare[
            "upper_DeltaG_shift_r1s_minus_r10"
        ].min()
    ),
    "to",
    float(
        compare[
            "upper_DeltaG_shift_r1s_minus_r10"
        ].max()
    ),
    "kg CO2e",
)


print("\n" + "=" * 78)

print(
    "P16R-D4B PASS — R1S TEMPORAL STRUCTURAL ROBUSTNESS COMPLETED"
)

print(
    "COMMON PHYSICAL SUPPORT: 567/567"
)

print(
    "MATCHED TEMPORAL CONTEXTS: 30/30"
)

print(
    "R10/R1S TIMESCALES KEPT SEPARATE"
)

print(
    "NO STATE-ID EQUALITY ASSUMED"
)

print("=" * 78)