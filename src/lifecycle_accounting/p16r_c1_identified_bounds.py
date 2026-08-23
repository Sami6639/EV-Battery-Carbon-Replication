from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_b2_primary_context_deltag.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c1_primary_identified_bounds.parquet"
)


print("=" * 78)
print("P16R-C1 — PRIMARY IDENTIFIED BOUNDS CONSTRUCTION")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED DELTAG TABLE
# ============================================================

df = pd.read_parquet(INPUT_FILE)

assert not df.empty
assert df["DeltaG_kgco2e"].notna().all()


# ============================================================
# 2. IDENTIFIED-SET GROUP
# ============================================================

group_cols = [
    "context_id",
    "grid_scenario",
    "manufacturing_pathway",
    "decision_calendar_year",
    "current_vehicle_age_years",
    "mobility_scenario",
    "survival_scenario",
    "charging_scenario",
    "grid_geography",
    "manufacturing_benchmark_type",
    "replacement_chemistry",

    "current_state_key",
    "current_degradation_state_id",

    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "topology_id",
]


# ============================================================
# 3. VERIFY EXACTLY FOUR ENDPOINT COMBINATIONS
# ============================================================

counts = (
    df.groupby(
        group_cols,
        dropna=False,
    )
    .size()
)

if not (counts == 4).all():
    bad = counts.loc[
        counts != 4
    ]

    raise RuntimeError(
        "P16R-C1 FAIL — each identified-set group "
        "must contain exactly four endpoint combinations.\n"
        + bad.head().to_string()
    )


# ============================================================
# 4. LOCATE INFIMUM / SUPREMUM OBSERVATIONS
# ============================================================

groups = df.groupby(
    group_cols,
    dropna=False,
    sort=False,
)

idx_lower = groups[
    "DeltaG_kgco2e"
].idxmin()

idx_upper = groups[
    "DeltaG_kgco2e"
].idxmax()


lower = df.loc[
    idx_lower
].copy()

upper = df.loc[
    idx_upper
].copy()


# ============================================================
# 5. LOWER-BOUND RECORD
# ============================================================

lower_keep = (
    group_cols
    + [
        "DeltaG_kgco2e",
        "theta_R",
        "theta_C",

        "R_endpoint_state_id",
        "C_endpoint_state_id",

        "R_endpoint_capacity_retention",
        "C_endpoint_capacity_retention",

        "R_endpoint_relative_resistance",
        "C_endpoint_relative_resistance",

        "R_endpoint_l2_kwh_per_km",
        "C_endpoint_l2_kwh_per_km",

        "replacement_manufacturing_kgco2e",
        "expected_residual_service_km",
    ]
)

lower = lower[
    lower_keep
].rename(
    columns={
        "DeltaG_kgco2e":
            "lower_DeltaG_kgco2e",

        "theta_R":
            "lower_bound_theta_R",

        "theta_C":
            "lower_bound_theta_C",

        "R_endpoint_state_id":
            "lower_R_endpoint_state_id",

        "C_endpoint_state_id":
            "lower_C_endpoint_state_id",

        "R_endpoint_capacity_retention":
            "lower_R_capacity_retention",

        "C_endpoint_capacity_retention":
            "lower_C_capacity_retention",

        "R_endpoint_relative_resistance":
            "lower_R_relative_resistance",

        "C_endpoint_relative_resistance":
            "lower_C_relative_resistance",

        "R_endpoint_l2_kwh_per_km":
            "lower_R_l2_kwh_per_km",

        "C_endpoint_l2_kwh_per_km":
            "lower_C_l2_kwh_per_km",
    }
)


# ============================================================
# 6. UPPER-BOUND RECORD
# ============================================================

upper_keep = (
    group_cols
    + [
        "DeltaG_kgco2e",
        "theta_R",
        "theta_C",

        "R_endpoint_state_id",
        "C_endpoint_state_id",

        "R_endpoint_capacity_retention",
        "C_endpoint_capacity_retention",

        "R_endpoint_relative_resistance",
        "C_endpoint_relative_resistance",

        "R_endpoint_l2_kwh_per_km",
        "C_endpoint_l2_kwh_per_km",
    ]
)

upper = upper[
    upper_keep
].rename(
    columns={
        "DeltaG_kgco2e":
            "upper_DeltaG_kgco2e",

        "theta_R":
            "upper_bound_theta_R",

        "theta_C":
            "upper_bound_theta_C",

        "R_endpoint_state_id":
            "upper_R_endpoint_state_id",

        "C_endpoint_state_id":
            "upper_C_endpoint_state_id",

        "R_endpoint_capacity_retention":
            "upper_R_capacity_retention",

        "C_endpoint_capacity_retention":
            "upper_C_capacity_retention",

        "R_endpoint_relative_resistance":
            "upper_R_relative_resistance",

        "C_endpoint_relative_resistance":
            "upper_C_relative_resistance",

        "R_endpoint_l2_kwh_per_km":
            "upper_R_l2_kwh_per_km",

        "C_endpoint_l2_kwh_per_km":
            "upper_C_l2_kwh_per_km",
    }
)


# ============================================================
# 7. JOIN LOWER + UPPER
# ============================================================

bounds = lower.merge(
    upper,
    on=group_cols,
    how="inner",
    validate="one_to_one",
)


# ============================================================
# 8. IDENTIFIED WIDTH
# ============================================================

bounds["identified_width_kgco2e"] = (
    bounds["upper_DeltaG_kgco2e"]
    - bounds["lower_DeltaG_kgco2e"]
)

if (
    bounds["identified_width_kgco2e"]
    < -1e-12
).any():
    raise RuntimeError(
        "P16R-C1 FAIL — negative identified interval width."
    )


# ============================================================
# 9. CURRENT PHYSICAL STATE
# ============================================================

current_state = (
    df[
        [
            "context_id",
            "current_state_key",
            "C_endpoint_capacity_retention",
            "C_endpoint_relative_resistance",
        ]
    ]
    .loc[
        df["theta_C"] == "C_LOW"
    ]
    .drop_duplicates()
    .rename(
        columns={
            "C_endpoint_capacity_retention":
                "current_capacity_retention",

            "C_endpoint_relative_resistance":
                "current_relative_resistance",
        }
    )
)

bounds = bounds.merge(
    current_state,
    on=[
        "context_id",
        "current_state_key",
    ],
    how="left",
    validate="one_to_one",
)

if bounds[
    [
        "current_capacity_retention",
        "current_relative_resistance",
    ]
].isna().any().any():
    raise RuntimeError(
        "P16R-C1 FAIL — current state identity missing."
    )


# ============================================================
# 10. NO CLASSIFICATION YET
# ============================================================

bounds["identified_bounds_calculated"] = True

bounds["carbon_classification_calculated"] = False
bounds["identification_leverage_calculated"] = False
bounds["dual_state_discordance_calculated"] = False
bounds["replacement_optimization_performed"] = False

bounds["analysis_stage"] = (
    "P16R-C1_PRIMARY_IDENTIFIED_BOUNDS"
)


for forbidden in [
    "carbon_classification",
    "decision_classification",
    "ROBUST CONTINUE",
    "ROBUST REPLACE",
    "CARBON DECISION INDETERMINATE",
]:
    assert forbidden not in bounds.columns


# ============================================================
# 11. HARD CONTRACT
# ============================================================

expected_rows = (
    df["context_id"].nunique()
    * df["current_state_key"].nunique()
)

assert len(bounds) == expected_rows

assert bounds["context_id"].nunique() == 6

assert (
    bounds["current_state_key"].nunique()
    == 567
)

assert (
    bounds["lower_DeltaG_kgco2e"]
    <= bounds["upper_DeltaG_kgco2e"]
).all()


# ============================================================
# 12. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

bounds.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 13. SUMMARY — NO DECISION INTERPRETATION
# ============================================================

summary = (
    bounds.groupby(
        [
            "context_id",
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

        max_lower_DeltaG=(
            "lower_DeltaG_kgco2e",
            "max",
        ),

        min_upper_DeltaG=(
            "upper_DeltaG_kgco2e",
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

        n_states=(
            "current_state_key",
            "nunique",
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
    f"\nIdentified-bound rows: "
    f"{len(bounds):,}"
)

print(
    f"Matched contexts: "
    f"{bounds['context_id'].nunique()}"
)

print(
    f"Current states: "
    f"{bounds['current_state_key'].nunique():,}"
)


print("\nGlobal lower_DeltaG range:")

print(
    float(
        bounds["lower_DeltaG_kgco2e"].min()
    ),
    "to",
    float(
        bounds["lower_DeltaG_kgco2e"].max()
    ),
    "kg CO2e",
)


print("\nGlobal upper_DeltaG range:")

print(
    float(
        bounds["upper_DeltaG_kgco2e"].min()
    ),
    "to",
    float(
        bounds["upper_DeltaG_kgco2e"].max()
    ),
    "kg CO2e",
)


print("\nIdentified-width range:")

print(
    float(
        bounds["identified_width_kgco2e"].min()
    ),
    "to",
    float(
        bounds["identified_width_kgco2e"].max()
    ),
    "kg CO2e",
)


print("\nBound summary by primary matched context:")

print(
    summary.to_string(
        index=False
    )
)


print("\nLower-bound theta combinations:")

print(
    bounds[
        [
            "lower_bound_theta_R",
            "lower_bound_theta_C",
        ]
    ]
    .value_counts()
    .to_string()
)


print("\nUpper-bound theta combinations:")

print(
    bounds[
        [
            "upper_bound_theta_R",
            "upper_bound_theta_C",
        ]
    ]
    .value_counts()
    .to_string()
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-C1 PASS — PRIMARY IDENTIFIED BOUNDS CONSTRUCTED"
)

print(
    "LOWER_DELTAG / UPPER_DELTAG: CALCULATED"
)

print(
    "BOUND-GENERATING THETA COMBINATIONS: PRESERVED"
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