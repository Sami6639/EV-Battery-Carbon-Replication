from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SURVIVAL_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_vehicle_survival.parquet"
)

MOBILITY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_mobility_use_scenarios.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_c2_residual_service_weights.parquet"
)


print("=" * 78)
print("P15R-C2 — RESIDUAL SERVICE / SURVIVAL ACCOUNTING")
print("=" * 78)


# ============================================================
# 1. LOAD FROZEN P14 INPUTS
# ============================================================

survival = pd.read_parquet(SURVIVAL_FILE)
mobility = pd.read_parquet(MOBILITY_FILE)


# ============================================================
# 2. CENTRAL ANNUAL MOBILITY
# ============================================================

central_mobility = mobility.loc[
    mobility["scenario_id"] == "central_use"
].copy()

assert len(central_mobility) == 1

annual_km = float(
    central_mobility.iloc[0]["annual_km"]
)

assert annual_km > 0

print(
    f"Central annual mobility: "
    f"{annual_km:.6f} km/year"
)


# ============================================================
# 3. KEEP ALL PREREGISTERED SURVIVAL SCENARIOS
#
# central             -> PRIMARY
# lower_survival      -> STRUCTURAL ROBUSTNESS
# higher_survival     -> STRUCTURAL ROBUSTNESS
# ============================================================

allowed_survival = {
    "central",
    "lower_survival",
    "higher_survival",
}

s = survival.loc[
    survival["survival_scenario"].isin(
        allowed_survival
    )
].copy()

assert not s.empty


# ============================================================
# 4. BASIC SURVIVAL VALIDITY
# ============================================================

assert (
    s["conditional_survival"]
    .between(0.0, 1.0)
    .all()
)

assert (
    s["years_after_conditioning"] >= 0
).all()

assert (
    s["attained_vehicle_age_years"]
    >= s["current_vehicle_age_years"]
).all()


# ============================================================
# 5. VERIFY CONDITIONAL SURVIVAL STARTS AT 1
# ============================================================

start_rows = s.loc[
    s["years_after_conditioning"] == 0
].copy()

if start_rows.empty:
    raise RuntimeError(
        "P15R-C2 FAIL — no conditioning-year "
        "survival rows found."
    )

if not np.allclose(
    start_rows["conditional_survival"],
    1.0,
    rtol=0,
    atol=1e-10,
):
    raise RuntimeError(
        "P15R-C2 FAIL — conditional survival "
        "does not start at 1."
    )


# ============================================================
# 6. VERIFY SURVIVAL IS NON-INCREASING
# ============================================================

for (
    scenario,
    current_age,
), group in s.groupby(
    [
        "survival_scenario",
        "current_vehicle_age_years",
    ],
    sort=True,
):
    g = group.sort_values(
        "years_after_conditioning"
    )

    diffs = (
        g["conditional_survival"]
        .diff()
        .dropna()
    )

    if (diffs > 1e-10).any():
        raise RuntimeError(
            "P15R-C2 FAIL — conditional "
            "survival increases for "
            f"{scenario}, age={current_age}"
        )


# ============================================================
# 7. SCENARIO TIER
# ============================================================

s["survival_tier"] = np.where(
    s["survival_scenario"] == "central",
    "PRIMARY",
    "STRUCTURAL_ROBUSTNESS",
)


# ============================================================
# 8. EXPECTED RESIDUAL SERVICE
#
# Survival is NOT a degradation model.
#
# This quantity is only:
#
# annual mobility × probability vehicle
# remains in service at that future interval.
# ============================================================

s["mobility_scenario"] = "central_use"

s["annual_km_if_in_service"] = annual_km

s["expected_service_km"] = (
    s["annual_km_if_in_service"]
    * s["conditional_survival"]
)


# ============================================================
# 9. CUMULATIVE EXPECTED RESIDUAL SERVICE
# ============================================================

s = s.sort_values(
    [
        "survival_scenario",
        "current_vehicle_age_years",
        "years_after_conditioning",
    ]
).reset_index(drop=True)

s["cumulative_expected_service_km"] = (
    s.groupby(
        [
            "survival_scenario",
            "current_vehicle_age_years",
        ]
    )["expected_service_km"]
    .cumsum()
)


# ============================================================
# 10. ACCOUNTING METADATA
# ============================================================

s["accounting_stage"] = "P15R-C2"

s["survival_role"] = (
    "RESIDUAL_SERVICE_WEIGHT_ONLY"
)

s["degradation_state_assigned_by_survival"] = False

s["lifecycle_ghg_calculated"] = False
s["delta_g_calculated"] = False
s["decision_bounds_calculated"] = False
s["carbon_classification_produced"] = False
s["replacement_optimization_performed"] = False


# ============================================================
# 11. HARD SCIENTIFIC SAFETY CHECKS
# ============================================================

assert not s[
    "degradation_state_assigned_by_survival"
].any()

assert not s[
    "lifecycle_ghg_calculated"
].any()

assert not s[
    "delta_g_calculated"
].any()

assert not s[
    "decision_bounds_calculated"
].any()

assert not s[
    "carbon_classification_produced"
].any()

assert not s[
    "replacement_optimization_performed"
].any()


# ============================================================
# 12. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

s.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 13. SUMMARY TABLE
# ============================================================

summary = (
    s.groupby(
        [
            "survival_scenario",
            "survival_tier",
            "current_vehicle_age_years",
        ],
        as_index=False,
    )
    .agg(
        max_years_after_conditioning=(
            "years_after_conditioning",
            "max",
        ),
        final_conditional_survival=(
            "conditional_survival",
            "last",
        ),
        total_expected_service_km=(
            "expected_service_km",
            "sum",
        ),
    )
)


print(
    f"\nOutput rows: {len(s):,}"
)

print(
    "Current vehicle ages:",
    sorted(
        s["current_vehicle_age_years"]
        .unique()
        .tolist()
    ),
)

print(
    "Survival scenarios:",
    sorted(
        s["survival_scenario"]
        .unique()
        .tolist()
    ),
)


print("\nSelected summary examples:")

examples = summary.loc[
    summary["current_vehicle_age_years"]
    .isin([0, 5, 10, 15, 20])
].copy()

print(
    examples.to_string(
        index=False
    )
)


print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P15R-C2 PASS — RESIDUAL SERVICE "
    "ACCOUNTING VERIFIED"
)

print(
    "SURVIVAL USED ONLY AS SERVICE WEIGHT"
)

print(
    "SURVIVAL DID NOT ASSIGN "
    "BATTERY DEGRADATION STATE"
)

print(
    "NO LIFECYCLE GHG CALCULATED"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO IDENTIFIED DECISION BOUNDS CALCULATED"
)

print(
    "NO CARBON CLASSIFICATION PRODUCED"
)

print(
    "NO REPLACEMENT OPTIMIZATION PERFORMED"
)

print("=" * 78)