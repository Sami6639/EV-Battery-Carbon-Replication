from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

P145I_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p145i_conditional_resistance_envelopes.parquet"
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

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d4e4_extreme_physical_stress.parquet"
)


print("=" * 78)
print("P16R-D4E4 — CONDITIONAL / EXTREME PHYSICAL STRESS TEST")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

energy = pd.read_parquet(ENERGY_FILE)
p145i = pd.read_parquet(P145I_FILE)
service = pd.read_parquet(SERVICE_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)

with CONFIG_FILE.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)

import json

with PARAM_FILE.open(encoding="utf-8") as f:
    params = json.load(f)


# ============================================================
# 2. P145I PROVENANCE CHECK
#
# This table establishes conditional-envelope evidence.
# It is NOT used to perform an unsupported direct
# resistance -> vehicle-energy conversion.
# ============================================================

supported_provenance = p145i.loc[
    p145i["resistance_state_status"]
    == "SUPPORTED CONDITIONAL ENVELOPE"
].copy()

print("\nP14.5I conditional-envelope provenance:")

print(
    "supported rows:",
    len(supported_provenance),
)

if not supported_provenance.empty:

    print(
        "resistance endpoints:",
        sorted(
            supported_provenance[
                "resistance_endpoint"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
    )


# ============================================================
# 3. SELECT P13 PHYSICS-TRANSLATED EXTREME STATES
#
# No proportional resistance-to-energy conversion.
# ============================================================

extreme = energy.loc[
    energy["conditional_extreme"]
    & energy["drive_cycle"].isin(
        ["UDDS", "HWFET"]
    )
].copy()


if extreme.empty:
    raise RuntimeError(
        "P16R-D4E4 FAIL — "
        "no P13 conditional-extreme energy states."
    )


print("\nP13 translated extreme rows:")
print(len(extreme))

print("\nExtreme physical-envelope classes:")

print(
    sorted(
        extreme[
            "physical_envelope_class"
        ]
        .dropna()
        .unique()
        .tolist()
    )
)

print("\nExtreme resistance specifications:")

print(
    sorted(
        extreme[
            "resistance_specification"
        ]
        .dropna()
        .unique()
        .tolist()
    )
)


# ============================================================
# 4. CENTRAL MOBILITY REQUIREMENT
# ============================================================

central_service = service.loc[
    service["scenario_id"]
    == "mobility_central"
].copy()

assert len(central_service) == 1

required_range_km = float(
    central_service.iloc[0][
        "required_single_service_distance_km"
    ]
)


# ============================================================
# 5. BUILD COMBINED 55/45 EXTREME STATES
# ============================================================

KEY = [
    "degradation_state_id",
    "source_id",
    "resistance_specification",
    "physical_envelope_class",
    "valid_domain_status",
    "topology_id",
    "nominal_pack_voltage_v",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
]


dup = extreme.duplicated(
    subset=KEY + ["drive_cycle"],
    keep=False,
)

if dup.any():
    raise RuntimeError(
        "P16R-D4E4 FAIL — "
        "duplicate extreme state/cycle rows."
    )


wide = (
    extreme[
        KEY
        + [
            "drive_cycle",
            "aged_battery_side_kwh_per_km",
            "usable_battery_energy_kwh",
            "incremental_battery_side_energy_percent",
        ]
    ]
    .pivot(
        index=KEY,
        columns="drive_cycle",
        values=[
            "aged_battery_side_kwh_per_km",
            "usable_battery_energy_kwh",
            "incremental_battery_side_energy_percent",
        ],
    )
)

wide.columns = [
    f"{a}_{b}"
    for a, b in wide.columns
]

wide = wide.reset_index()


required = [
    "aged_battery_side_kwh_per_km_UDDS",
    "aged_battery_side_kwh_per_km_HWFET",
    "usable_battery_energy_kwh_UDDS",
    "usable_battery_energy_kwh_HWFET",
]

if wide[required].isna().any().any():
    raise RuntimeError(
        "P16R-D4E4 FAIL — "
        "incomplete extreme UDDS/HWFET pair."
    )


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


# ============================================================
# 6. TECHNICAL EVIDENCE
# ============================================================

wide["aged_power_capability_status"] = (
    "NOT STATE-RESOLVED"
)

wide["full_technical_feasibility_confirmed"] = False


print("\nExtreme state count by resistance specification:")

print(
    wide[
        "resistance_specification"
    ]
    .value_counts()
    .to_string()
)


print("\nExtreme range feasibility:")

print(
    wide.groupby(
        "resistance_specification"
    )["range_feasible"]
    .agg(["count", "sum"])
    .to_string()
)


# Carbon stress is evaluated only where continuation
# remains range-feasible.
stress = wide.loc[
    wide["range_feasible"]
].copy()

if stress.empty:
    raise RuntimeError(
        "P16R-D4E4 WITH BOUNDS — "
        "no range-feasible extreme states."
    )


# ============================================================
# 7. FRESH REPLACEMENT REFERENCE
# ============================================================

fresh = [
    row
    for row in params["fresh_baseline"]
    if row.get("drive_cycle")
    == "COMBINED_55_45"
]

assert len(fresh) == 1

fresh_l2 = float(
    fresh[0][
        "fresh_battery_side_kwh_per_km"
    ]
)


# ============================================================
# 8. PRIMARY EXOGENOUS CONTEXT
#
# Extreme physical evidence is the only varied family.
#
# 2025 / MidCase / SPS
# central mileage / survival / charging
# ============================================================

DECISION_YEAR = 2025


mob = mobility.loc[
    mobility["scenario_id"]
    == "central_use"
]

assert len(mob) == 1

annual_km = float(
    mob.iloc[0]["annual_km"]
)


chg = charging.loc[
    charging["scenario_id"]
    == "central_efficiency"
]

assert len(chg) == 1

charging_multiplier = float(
    chg.iloc[0][
        "l2_to_l3_multiplier"
    ]
)


surv = survival.loc[
    (
        survival["survival_scenario"]
        == "central"
    )
    & (
        survival[
            "current_vehicle_age_years"
        ]
        == 0
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


g = grid.loc[
    (
        grid["pathway_role"]
        == "PRIMARY_AVERAGE_CI"
    )
    & (
        grid["scenario"] == "MidCase"
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

assert len(g) == len(surv)


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
        annual["expected_service_km"]
        * annual["grid_ci_gco2e_per_kwh"]
        / 1000.0
    ).sum()
)


# ============================================================
# 9. PRIMARY REPLACEMENT MANUFACTURING
# ============================================================

mrow = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (mfg["pathway"] == "SPS")
    & (
        mfg["benchmark_type"]
        == "PROSPECTIVE"
    )
    & (
        mfg["calendar_year"]
        == DECISION_YEAR
    )
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
# 10. BUILD EXTREME POLICY-SYMMETRIC ENDPOINT SETS
#
# R10 and R1s remain separate.
# Worst endpoint is selected only within same architecture
# AND same resistance timescale.
# ============================================================

ARCH = [
    "resistance_specification",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
]


worst_idx = (
    stress.groupby(
        ARCH,
        sort=False,
    )[
        "combined_aged_l2_kwh_per_km"
    ]
    .idxmax()
)

worst = stress.loc[
    worst_idx,
    ARCH
    + [
        "degradation_state_id",
        "combined_aged_l2_kwh_per_km",
        "capacity_retention",
        "relative_resistance",
    ],
].rename(
    columns={
        "degradation_state_id":
            "worst_state_id",

        "combined_aged_l2_kwh_per_km":
            "worst_l2",

        "capacity_retention":
            "worst_capacity",

        "relative_resistance":
            "worst_resistance",
    }
)


base = stress.merge(
    worst,
    on=ARCH,
    how="left",
    validate="many_to_one",
)


# ============================================================
# 11. DELTAG BOUNDS PER EXTREME STATE
#
# C_LOW  = current extreme state
# C_HIGH = worst supported extreme endpoint
#
# R_LOW  = fresh replacement
# R_HIGH = same worst supported extreme endpoint
#
# Policy symmetry retained.
# ============================================================

rows = []

for row in base.itertuples(index=False):

    C_members = {
        "C_LOW":
            float(
                row.combined_aged_l2_kwh_per_km
            ),

        "C_HIGH":
            float(
                row.worst_l2
            ),
    }

    R_members = {
        "R_LOW":
            fresh_l2,

        "R_HIGH":
            float(
                row.worst_l2
            ),
    }

    deltag_values = []

    for theta_R, r_l2 in R_members.items():

        for theta_C, c_l2 in C_members.items():

            deltag = (
                (
                    r_l2 - c_l2
                )
                * charging_multiplier
                * carbon_factor
                + replacement_mfg
            )

            deltag_values.append(
                {
                    "theta_R":
                        theta_R,

                    "theta_C":
                        theta_C,

                    "DeltaG":
                        deltag,
                }
            )


    vals = pd.DataFrame(
        deltag_values
    )

    lower = float(
        vals["DeltaG"].min()
    )

    upper = float(
        vals["DeltaG"].max()
    )


    if lower > 0:
        classification = (
            "ROBUST CONTINUE"
        )

    elif upper < 0:
        classification = (
            "ROBUST REPLACE"
        )

    else:
        classification = (
            "CARBON DECISION INDETERMINATE"
        )


    rows.append(
        {
            "degradation_state_id":
                row.degradation_state_id,

            "source_id":
                row.source_id,

            "resistance_specification":
                row.resistance_specification,

            "physical_envelope_class":
                row.physical_envelope_class,

            "capacity_retention":
                row.capacity_retention,

            "relative_resistance":
                row.relative_resistance,

            "cell_resistance_share":
                row.cell_resistance_share,

            "topology_id":
                row.topology_id,

            "technical_range_km":
                row.technical_range_km,

            "range_feasible":
                True,

            "aged_power_capability_status":
                "NOT STATE-RESOLVED",

            "lower_DeltaG":
                lower,

            "upper_DeltaG":
                upper,

            "identified_width":
                upper - lower,

            "carbon_classification":
                classification,

            "replacement_manufacturing_kgco2e":
                replacement_mfg,

            "stress_tier":
                "EXTREME_CONDITIONAL_STRESS_ONLY",

            "headline_eligible":
                False,

            "primary_domain_member":
                False,

            "one_family_at_a_time":
                True,

            "time_to_state_used":
                False,

            "state_prevalence_interpretation":
                False,

            "direct_resistance_to_energy_conversion":
                False,
        }
    )


out = pd.DataFrame(rows)


# ============================================================
# 12. HARD CLAIM CONTRACT
# ============================================================

assert not out[
    "headline_eligible"
].any()

assert not out[
    "primary_domain_member"
].any()

assert out[
    "one_family_at_a_time"
].all()

assert not out[
    "time_to_state_used"
].any()

assert not out[
    "state_prevalence_interpretation"
].any()

assert not out[
    "direct_resistance_to_energy_conversion"
].any()


# ============================================================
# 13. SAVE
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
# 14. SUMMARY
# ============================================================

print("\nExtreme carbon-stress rows:")
print(len(out))


print("\nExtreme classifications by resistance specification:")

print(
    out.groupby(
        [
            "resistance_specification",
            "carbon_classification",
        ]
    )
    .size()
    .to_string()
)


print("\nExtreme classification reversals from ROBUST CONTINUE:")

reversal_n = int(
    (
        out[
            "carbon_classification"
        ]
        != "ROBUST CONTINUE"
    ).sum()
)

print(reversal_n)


print("\nGlobal extreme minimum lower_DeltaG:")

print(
    float(
        out[
            "lower_DeltaG"
        ].min()
    ),
    "kg CO2e",
)


print("\nGlobal extreme maximum upper_DeltaG:")

print(
    float(
        out[
            "upper_DeltaG"
        ].max()
    ),
    "kg CO2e",
)


print("\nExtreme energy-penalty percent range:")

penalty_cols = [
    c
    for c in wide.columns
    if c.startswith(
        "incremental_battery_side_energy_percent_"
    )
]

if penalty_cols:

    values = pd.concat(
        [
            wide[c]
            for c in penalty_cols
        ],
        ignore_index=True,
    ).dropna()

    print(
        float(values.min()),
        "to",
        float(values.max()),
        "%",
    )

else:

    print(
        "NOT MACHINE-READABLE IN COMBINED TABLE"
    )


print("\nRange-infeasible extreme states:")

print(
    int(
        (
            ~wide[
                "range_feasible"
            ]
        ).sum()
    )
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4E4 PASS — CONDITIONAL / EXTREME "
    "PHYSICAL STRESS TEST COMPLETED"
)

print(
    "P13 PHYSICS-TRANSLATED EXTREME STATES: USED"
)

print(
    "P145I CONDITIONAL ENVELOPE: PROVENANCE ONLY"
)

print(
    "R10 / R1S: KEPT SEPARATE"
)

print(
    "EXTREME STRESS: NOT HEADLINE-ELIGIBLE"
)

print(
    "DIRECT RESISTANCE-TO-ENERGY CONVERSION: NOT USED"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print("=" * 78)