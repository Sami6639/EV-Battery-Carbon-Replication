from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DELTA_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3a_temporal_deltag.parquet"
)

BOUNDS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3a_temporal_identified_bounds.parquet"
)

OUTPUT_DETAIL = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3b_temporal_mechanism_decomposition.parquet"
)

OUTPUT_SUMMARY = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3b_temporal_mechanism_summary.parquet"
)


print("=" * 78)
print("P16R-D3B — TEMPORAL DOMINANCE MECHANISM DECOMPOSITION")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED D3A OUTPUTS
# ============================================================

delta = pd.read_parquet(DELTA_FILE)
bounds = pd.read_parquet(BOUNDS_FILE)

assert not delta.empty
assert not bounds.empty

assert delta["context_id"].nunique() == 30


# ============================================================
# 2. OPERATIONAL CARBON SAVING FROM REPLACEMENT
#
# Positive value:
# replacement has lower operational GHG than continuation.
#
# This is NOT total lifecycle benefit.
# ============================================================

delta["operational_saving_kgco2e"] = (
    delta["G_C_operational_kgco2e"]
    - delta["G_R_operational_kgco2e"]
)


# ============================================================
# 3. ACCOUNTING IDENTITY
#
# DeltaG
# =
# replacement manufacturing
# -
# operational saving
# ============================================================

delta["DeltaG_reconstructed_kgco2e"] = (
    delta["replacement_manufacturing_kgco2e"]
    - delta["operational_saving_kgco2e"]
)

identity_error = (
    delta["DeltaG_kgco2e"]
    - delta["DeltaG_reconstructed_kgco2e"]
).abs()

assert identity_error.max() <= 1e-9


# ============================================================
# 4. STATE × CONTEXT MECHANISM ENVELOPE
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


detail = (
    delta.groupby(
        group_cols,
        as_index=False,
    )
    .agg(
        min_operational_saving_kgco2e=(
            "operational_saving_kgco2e",
            "min",
        ),
        max_operational_saving_kgco2e=(
            "operational_saving_kgco2e",
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
    )
)


# ============================================================
# 5. DOMINANCE MARGIN
#
# Most replacement-favourable operational case uses
# maximum operational saving.
#
# manufacturing burden - max saving
# must equal lower_DeltaG.
# ============================================================

detail["dominance_margin_kgco2e"] = (
    detail["replacement_manufacturing_kgco2e"]
    - detail["max_operational_saving_kgco2e"]
)


# ============================================================
# 6. JOIN IDENTIFIED LOWER BOUND
# ============================================================

bounds_key = group_cols

check_bounds = bounds[
    bounds_key
    + [
        "lower_DeltaG_kgco2e",
        "upper_DeltaG_kgco2e",
        "identified_width_kgco2e",
        "carbon_classification",
    ]
].copy()


detail = detail.merge(
    check_bounds,
    on=bounds_key,
    how="left",
    validate="one_to_one",
)


if detail["lower_DeltaG_kgco2e"].isna().any():
    raise RuntimeError(
        "P16R-D3B FAIL — temporal bounds did not merge."
    )


margin_error = (
    detail["dominance_margin_kgco2e"]
    - detail["lower_DeltaG_kgco2e"]
).abs()

assert margin_error.max() <= 1e-9


# ============================================================
# 7. MANUFACTURING / OPERATIONAL-SAVING RATIOS
# ============================================================

detail[
    "max_operational_saving_fraction_of_manufacturing"
] = (
    detail["max_operational_saving_kgco2e"]
    / detail["replacement_manufacturing_kgco2e"]
)


detail["manufacturing_to_max_saving_ratio"] = np.where(
    detail["max_operational_saving_kgco2e"] > 0,
    (
        detail["replacement_manufacturing_kgco2e"]
        / detail["max_operational_saving_kgco2e"]
    ),
    np.nan,
)


# ============================================================
# 8. CLAIM DISCIPLINE
# ============================================================

detail["break_even_time_calculated"] = False
detail["time_to_state_used"] = False
detail["fleet_prevalence_interpretation"] = False

detail["mechanism_label"] = (
    "REPLACEMENT_MANUFACTURING_VS_OPERATIONAL_SAVING"
)


# ============================================================
# 9. CONTEXT-LEVEL SUMMARY
# ============================================================

summary = (
    detail.groupby(
        [
            "decision_calendar_year",
            "grid_scenario",
            "manufacturing_pathway",
        ],
        as_index=False,
    )
    .agg(
        replacement_manufacturing_kgco2e=(
            "replacement_manufacturing_kgco2e",
            "first",
        ),

        expected_residual_service_km=(
            "expected_residual_service_km",
            "first",
        ),

        min_operational_saving_kgco2e=(
            "min_operational_saving_kgco2e",
            "min",
        ),

        max_operational_saving_kgco2e=(
            "max_operational_saving_kgco2e",
            "max",
        ),

        minimum_dominance_margin_kgco2e=(
            "dominance_margin_kgco2e",
            "min",
        ),

        maximum_saving_fraction_of_manufacturing=(
            "max_operational_saving_fraction_of_manufacturing",
            "max",
        ),

        minimum_manufacturing_to_max_saving_ratio=(
            "manufacturing_to_max_saving_ratio",
            "min",
        ),

        n_states=(
            "current_state_key",
            "nunique",
        ),
    )
)


# ============================================================
# 10. YEAR-LEVEL MECHANISM SUMMARY
# ============================================================

year_summary = (
    summary.groupby(
        "decision_calendar_year",
        as_index=False,
    )
    .agg(
        manufacturing_min=(
            "replacement_manufacturing_kgco2e",
            "min",
        ),

        manufacturing_max=(
            "replacement_manufacturing_kgco2e",
            "max",
        ),

        max_operational_saving=(
            "max_operational_saving_kgco2e",
            "max",
        ),

        minimum_dominance_margin=(
            "minimum_dominance_margin_kgco2e",
            "min",
        ),

        max_saving_fraction_of_manufacturing=(
            "maximum_saving_fraction_of_manufacturing",
            "max",
        ),

        minimum_manufacturing_to_saving_ratio=(
            "minimum_manufacturing_to_max_saving_ratio",
            "min",
        ),

        residual_service_km=(
            "expected_residual_service_km",
            "first",
        ),
    )
)


# ============================================================
# 11. HARD SCIENTIFIC CHECKS
# ============================================================

assert (
    detail["dominance_margin_kgco2e"]
    > 0
).all()

assert (
    detail["carbon_classification"]
    == "ROBUST CONTINUE"
).all()

assert not detail[
    "break_even_time_calculated"
].any()

assert not detail[
    "time_to_state_used"
].any()

assert not detail[
    "fleet_prevalence_interpretation"
].any()


# ============================================================
# 12. SAVE
# ============================================================

OUTPUT_DETAIL.parent.mkdir(
    parents=True,
    exist_ok=True,
)

detail.to_parquet(
    OUTPUT_DETAIL,
    index=False,
)

summary.to_parquet(
    OUTPUT_SUMMARY,
    index=False,
)


# ============================================================
# 13. DISPLAY
# ============================================================

print(
    f"\nMechanism detail rows: "
    f"{len(detail):,}"
)

print(
    f"Matched temporal contexts: "
    f"{detail['context_id'].nunique()}"
)


print("\nMaximum admissible operational saving:")

print(
    float(
        detail[
            "max_operational_saving_kgco2e"
        ].max()
    ),
    "kg CO2e",
)


print("\nMinimum dominance margin:")

print(
    float(
        detail[
            "dominance_margin_kgco2e"
        ].min()
    ),
    "kg CO2e",
)


print(
    "\nMaximum operational-saving fraction "
    "of replacement manufacturing:"
)

print(
    float(
        detail[
            "max_operational_saving_fraction_of_manufacturing"
        ].max()
    )
)


print(
    "\nMinimum manufacturing-to-operational-saving ratio:"
)

ratio_values = detail[
    "manufacturing_to_max_saving_ratio"
].dropna()

if ratio_values.empty:
    print("NO POSITIVE OPERATIONAL SAVING")

else:
    print(
        float(
            ratio_values.min()
        )
    )


print("\nMechanism by decision year:")

print(
    year_summary.to_string(
        index=False
    )
)


print("\nOutputs:")

print(
    OUTPUT_DETAIL.relative_to(ROOT)
)

print(
    OUTPUT_SUMMARY.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D3B PASS — TEMPORAL DOMINANCE MECHANISM DECOMPOSED"
)

print(
    "DELTAG ACCOUNTING IDENTITY: VERIFIED"
)

print(
    "REPLACEMENT MANUFACTURING BURDEN: SEPARATED"
)

print(
    "MAXIMUM ADMISSIBLE OPERATIONAL SAVING: SEPARATED"
)

print(
    "DOMINANCE MARGIN: VERIFIED AGAINST LOWER_DELTAG"
)

print(
    "BREAK-EVEN TIME: NOT CALCULATED"
)

print(
    "TIME-TO-STATE INTERPRETATION: NONE"
)

print("=" * 78)