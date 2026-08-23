from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

BOUNDS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c1_primary_identified_bounds.parquet"
)

THETA_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a3_theta_endpoint_sets.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c2_primary_carbon_classification.parquet"
)


print("=" * 78)
print("P16R-C2 — PRIMARY CARBON CLASSIFICATION")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED IDENTIFIED BOUNDS
# ============================================================

bounds = pd.read_parquet(BOUNDS_FILE)
theta = pd.read_parquet(THETA_FILE)

assert not bounds.empty

assert (
    bounds["lower_DeltaG_kgco2e"]
    <= bounds["upper_DeltaG_kgco2e"]
).all()


# ============================================================
# 2. EXACT PRE-REGISTERED CARBON CLASSIFICATION
#
# DeltaG = G_R - G_C
#
# lower > 0
# -> replacement has higher GHG for every admissible treatment
# -> ROBUST CONTINUE
#
# upper < 0
# -> replacement has lower GHG for every admissible treatment
# -> ROBUST REPLACE
#
# interval crosses zero
# -> CARBON DECISION INDETERMINATE
#
# NO POST-RESULT THRESHOLD OR EPSILON IS INTRODUCED.
# ============================================================

def classify(row):

    lower = row["lower_DeltaG_kgco2e"]
    upper = row["upper_DeltaG_kgco2e"]

    if lower > 0:
        return "ROBUST CONTINUE"

    if upper < 0:
        return "ROBUST REPLACE"

    return "CARBON DECISION INDETERMINATE"


out = bounds.copy()

out["carbon_classification"] = (
    out.apply(
        classify,
        axis=1,
    )
)


# ============================================================
# 3. OPTIONAL NON-RECOMMENDATION QUALIFIER
# ============================================================

out["potentially_beneficial_qualifier"] = False

out.loc[
    (
        out["carbon_classification"]
        == "CARBON DECISION INDETERMINATE"
    )
    & (
        out["lower_DeltaG_kgco2e"] < 0
    ),
    "potentially_beneficial_qualifier",
] = True


# ============================================================
# 4. TECHNICAL-EVIDENCE AXIS
#
# Technical evidence remains separate from carbon.
# Use C_LOW solely to recover current-state technical evidence.
# ============================================================

technical = (
    theta.loc[
        theta["theta_id"] == "C_LOW",
        [
            "current_state_key",
            "range_feasible_central",
            "aged_power_capability_status",
            "full_technical_feasibility_confirmed",
        ],
    ]
    .drop_duplicates()
)

assert (
    technical["current_state_key"].nunique()
    == 567
)

out = out.merge(
    technical,
    on="current_state_key",
    how="left",
    validate="many_to_one",
)


if out[
    "range_feasible_central"
].isna().any():
    raise RuntimeError(
        "P16R-C2 FAIL — technical evidence missing."
    )


# ============================================================
# 5. TECHNICAL LABEL — SEPARATE FROM CARBON
# ============================================================

out["technical_evidence_label"] = (
    "RANGE-FEASIBLE; AGED-STATE POWER CAPABILITY NOT STATE-RESOLVED"
)

out.loc[
    ~out["range_feasible_central"],
    "technical_evidence_label",
] = "CONTINUE TECHNICALLY INFEASIBLE — RANGE"


# ============================================================
# 6. ENGINEERING-RECOMMENDATION CLAIM LIMIT
# ============================================================

out["full_engineering_recommendation_allowed"] = False

out["carbon_result_is_engineering_recommendation"] = False


# ============================================================
# 7. RESULT TIER
# ============================================================

out["result_tier"] = "PRIMARY CLASSIFICATION"

out["resistance_specification"] = "10-ms"

out["headline_eligible"] = True


# ============================================================
# 8. P15Q ANALYSES NOT YET PERFORMED
# ============================================================

out["identification_leverage_calculated"] = False
out["dual_state_discordance_calculated"] = False
out["context_modulation_completed"] = False
out["structural_robustness_completed"] = False

out["replacement_optimization_performed"] = False

out["analysis_stage"] = (
    "P16R-C2_PRIMARY_CARBON_CLASSIFICATION"
)


# ============================================================
# 9. HARD CLASSIFICATION CONTRACT
# ============================================================

allowed_labels = {
    "ROBUST CONTINUE",
    "ROBUST REPLACE",
    "CARBON DECISION INDETERMINATE",
}

assert (
    set(out["carbon_classification"].unique())
    <= allowed_labels
)


# Recompute classification independently.
expected = []

for row in out.itertuples(index=False):

    if row.lower_DeltaG_kgco2e > 0:
        expected.append(
            "ROBUST CONTINUE"
        )

    elif row.upper_DeltaG_kgco2e < 0:
        expected.append(
            "ROBUST REPLACE"
        )

    else:
        expected.append(
            "CARBON DECISION INDETERMINATE"
        )


assert (
    out["carbon_classification"].tolist()
    == expected
)


# ============================================================
# 10. NO PROHIBITED OLD REGIMES
# ============================================================

old_labels = {
    "EARLY-REPLACEMENT REGIME",
    "ROBUST INTERIOR REGIME",
    "CONDITIONAL INTERIOR REGIME",
    "USE-UNTIL-TECHNICAL-BOUNDARY REGIME",
}

assert not (
    set(out["carbon_classification"])
    & old_labels
)


# ============================================================
# 11. SAVE
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
# 12. SUMMARY
# ============================================================

print(
    f"\nClassification rows: "
    f"{len(out):,}"
)

print(
    f"Matched contexts: "
    f"{out['context_id'].nunique()}"
)

print(
    f"Current states: "
    f"{out['current_state_key'].nunique():,}"
)


print("\nGlobal primary carbon classifications:")

global_counts = (
    out["carbon_classification"]
    .value_counts()
)

print(
    global_counts.to_string()
)


print("\nClassification by matched context:")

context_counts = (
    out.groupby(
        [
            "context_id",
            "carbon_classification",
        ],
        as_index=False,
    )
    .size()
)

print(
    context_counts.to_string(
        index=False
    )
)


print("\nMinimum lower_DeltaG by classification:")

print(
    out.groupby(
        "carbon_classification"
    )[
        "lower_DeltaG_kgco2e"
    ]
    .min()
    .to_string()
)


print("\nMaximum upper_DeltaG by classification:")

print(
    out.groupby(
        "carbon_classification"
    )[
        "upper_DeltaG_kgco2e"
    ]
    .max()
    .to_string()
)


print("\nTechnical evidence:")

print(
    out[
        "technical_evidence_label"
    ]
    .value_counts()
    .to_string()
)


print("\nFull engineering recommendation allowed:")

print(
    out[
        "full_engineering_recommendation_allowed"
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
    "P16R-C2 PASS — PRIMARY CARBON CLASSIFICATION GENERATED"
)

print(
    "EXACT PRE-REGISTERED SIGN RULES APPLIED"
)

print(
    "TECHNICAL AND CARBON CLASSIFICATIONS KEPT SEPARATE"
)

print(
    "NO OLD EARLY/INTERIOR/BOUNDARY REGIME LABELS USED"
)

print(
    "NO IDENTIFICATION LEVERAGE CALCULATED"
)

print(
    "NO DUAL-STATE DISCORDANCE RESULT CALCULATED"
)

print(
    "NO REPLACEMENT OPTIMIZATION PERFORMED"
)

print("=" * 78)