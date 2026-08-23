from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

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

SURVIVAL_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_vehicle_survival.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b0t_temporal_context_audit.parquet"
)


print("=" * 78)
print("P16R-D2B0T — TEMPORAL DECISION-YEAR FEASIBILITY AUDIT")
print("=" * 78)


# ============================================================
# 1. LOAD FROZEN P14 INPUTS
# ============================================================

grid = pd.read_parquet(GRID_FILE)
mfg = pd.read_parquet(MFG_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)


# ============================================================
# 2. PRE-RESULT CANDIDATE DECISION YEARS
#
# Five-year source-supported calendar contexts.
#
# 2050 is not used as a decision-year context because it
# provides essentially no prospective operational horizon.
#
# These are exogenous decision contexts.
# They are NOT time-to-state predictions.
# ============================================================

CANDIDATE_YEARS = [
    2025,
    2030,
    2035,
    2040,
    2045,
]

GRID_SCENARIOS = [
    "MidCase",
    "LowRECost",
    "HighRECost",
]

MFG_PATHWAYS = [
    "SPS",
    "SDS",
]


# ============================================================
# 3. CENTRAL SURVIVAL SUPPORT
#
# Calendar year does NOT assign degradation state.
# We only verify that the frozen age-conditioned survival
# representation can support the remaining horizon.
# ============================================================

central_survival = survival.loc[
    (survival["survival_scenario"] == "central")
    & (survival["current_vehicle_age_years"] == 0)
].copy()

assert not central_survival.empty

max_survival_followup = int(
    central_survival[
        "years_after_conditioning"
    ].max()
)


# ============================================================
# 4. AUDIT EACH DECISION YEAR
# ============================================================

rows = []

for decision_year in CANDIDATE_YEARS:

    remaining_years = (
        2050 - decision_year
    )

    # --------------------------------------------------------
    # Grid support:
    # every primary scenario must exist annually from the
    # decision year through 2050.
    # --------------------------------------------------------

    grid_ok_by_scenario = {}

    for scenario in GRID_SCENARIOS:

        g = grid.loc[
            (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
            & (grid["scenario"] == scenario)
            & (grid["geography_level"] == "US_LOAD_WEIGHTED")
            & (grid["region"] == "US_LOAD_WEIGHTED")
            & (
                grid["calendar_year"]
                .between(decision_year, 2050)
            )
        ].copy()

        expected_years = set(
            range(
                decision_year,
                2051,
            )
        )

        observed_years = set(
            int(x)
            for x in g[
                "calendar_year"
            ].unique()
        )

        grid_ok_by_scenario[
            scenario
        ] = (
            observed_years
            == expected_years
        )

    grid_supported = all(
        grid_ok_by_scenario.values()
    )

    # --------------------------------------------------------
    # Manufacturing support:
    # NMC811 prospective SPS and SDS must each have an exact
    # in-domain value for the decision year.
    # --------------------------------------------------------

    m = mfg.loc[
        (mfg["chemistry"] == "NMC811")
        & (mfg["benchmark_type"] == "PROSPECTIVE")
        & (
            mfg["pathway"]
            .isin(MFG_PATHWAYS)
        )
        & (
            mfg["calendar_year"]
            == decision_year
        )
    ].copy()

    mfg_pathways_found = set(
        m["pathway"].tolist()
    )

    manufacturing_supported = (
        mfg_pathways_found
        == set(MFG_PATHWAYS)
    )

    # --------------------------------------------------------
    # Survival support:
    # enough years-after-conditioning must exist to populate
    # the remaining calendar horizon.
    # --------------------------------------------------------

    survival_supported = (
        max_survival_followup
        >= remaining_years
    )

    # --------------------------------------------------------
    # No extrapolation
    # --------------------------------------------------------

    no_grid_extrapolation = (
        2025 <= decision_year <= 2050
    )

    no_mfg_extrapolation = (
        decision_year
        in set(
            int(x)
            for x in mfg.loc[
                (mfg["chemistry"] == "NMC811")
                & (
                    mfg["benchmark_type"]
                    == "PROSPECTIVE"
                ),
                "calendar_year",
            ].unique()
        )
    )

    temporal_context_supported = (
        grid_supported
        and manufacturing_supported
        and survival_supported
        and no_grid_extrapolation
        and no_mfg_extrapolation
    )

    rows.append(
        {
            "decision_calendar_year":
                decision_year,

            "remaining_calendar_years_to_2050":
                remaining_years,

            "grid_supported":
                grid_supported,

            "manufacturing_supported":
                manufacturing_supported,

            "survival_followup_supported":
                survival_supported,

            "no_grid_extrapolation":
                no_grid_extrapolation,

            "no_manufacturing_extrapolation":
                no_mfg_extrapolation,

            "temporal_context_supported":
                temporal_context_supported,

            "time_to_state_interpretation":
                False,

            "degradation_state_assigned_by_year":
                False,

            "carbon_calculated":
                False,
        }
    )


audit = pd.DataFrame(rows)


# ============================================================
# 5. HARD GATE
# ============================================================

if not audit[
    "temporal_context_supported"
].all():

    print("\nUnsupported temporal contexts:")

    print(
        audit.loc[
            ~audit[
                "temporal_context_supported"
            ]
        ].to_string(index=False)
    )

    raise RuntimeError(
        "P16R-D2B0T FAIL — one or more candidate "
        "decision years are not fully source-supported."
    )


assert not audit[
    "time_to_state_interpretation"
].any()

assert not audit[
    "degradation_state_assigned_by_year"
].any()

assert not audit[
    "carbon_calculated"
].any()


# ============================================================
# 6. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

audit.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 7. DISPLAY
# ============================================================

print("\nTemporal decision-year audit:")

print(
    audit.to_string(
        index=False
    )
)

print("\nSupported decision years:")

print(
    audit.loc[
        audit[
            "temporal_context_supported"
        ],
        "decision_calendar_year",
    ].tolist()
)

print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D2B0T PASS — TEMPORAL DECISION-YEAR "
    "CONTEXTS ARE SOURCE-SUPPORTED"
)

print(
    "DECISION YEARS: 2025 / 2030 / 2035 / 2040 / 2045"
)

print(
    "DECISION YEAR IS EXOGENOUS CONTEXT — NOT TIME-TO-STATE"
)

print(
    "GRID AND MANUFACTURING EXTRAPOLATION: NONE"
)

print(
    "DEGRADATION STATE ASSIGNED BY CALENDAR YEAR: NO"
)

print(
    "NO NEW CARBON RESULT CALCULATED"
)

print("=" * 78)