from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

STATE_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a2_current_state_admissibility.parquet"
)

SERVICE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_mobility_service_requirements.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d4c_mobility_service_robustness.parquet"
)


print("=" * 78)
print("P16R-D4C — MOBILITY-SERVICE TECHNICAL ROBUSTNESS")
print("=" * 78)


# ============================================================
# 1. LOAD FROZEN / VERIFIED INPUTS
# ============================================================

states = pd.read_parquet(STATE_FILE)
service = pd.read_parquet(SERVICE_FILE)

assert not states.empty
assert not service.empty

assert len(states) == 567

required_state_columns = {
    "degradation_state_id",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
    "technical_range_combined_km",
    "current_state_admissible",
    "dual_state_atlas_eligible",
}

missing_state = (
    required_state_columns
    - set(states.columns)
)

if missing_state:
    raise RuntimeError(
        "P16R-D4C FAIL — missing A2 columns: "
        + str(sorted(missing_state))
    )


# ============================================================
# 2. RECONSTRUCT EXACT A3-COMPATIBLE STATE KEY
#
# A2 predates current_state_key.
# We recreate the same deterministic identity used in A3.
# No scientific parameter is changed.
# ============================================================

states["current_state_key"] = (
    states["degradation_state_id"].astype(str)
    + "|"
    + states["topology_id"].astype(str)
    + "|share="
    + states["cell_resistance_share"].astype(str)
    + "|window="
    + states["fresh_usable_window_fraction"].astype(str)
)

if states["current_state_key"].duplicated().any():
    raise RuntimeError(
        "P16R-D4C FAIL — reconstructed state key is not unique."
    )

assert states["current_state_key"].nunique() == 567


# ============================================================
# 3. FROZEN MOBILITY-SERVICE FAMILY
# ============================================================

EXPECTED = [
    "mobility_lower",
    "mobility_central",
    "mobility_upper",
]

svc = (
    service.loc[
        service["scenario_id"].isin(EXPECTED),
        [
            "scenario_id",
            "quantile",
            "required_single_service_distance_km",
            "selected_rule",
            "universal_soh_cutoff",
        ],
    ]
    .drop_duplicates()
)

assert set(svc["scenario_id"]) == set(EXPECTED)
assert len(svc) == 3

# Universal 70/80% SOH cutoff remains prohibited.
assert not svc["universal_soh_cutoff"].any()

assert (
    svc["required_single_service_distance_km"] > 0
).all()


# ============================================================
# 4. CROSS PHYSICAL STATES WITH SERVICE REQUIREMENTS
# ============================================================

out = states.merge(
    svc,
    how="cross",
)

assert len(out) == 567 * 3


# ============================================================
# 5. STATE-SPECIFIC RANGE FEASIBILITY
# ============================================================

out["range_feasible"] = (
    out["technical_range_combined_km"]
    >= out["required_single_service_distance_km"]
)


# ============================================================
# 6. TECHNICAL EVIDENCE LABEL
#
# Range is state-resolved.
# Aged-state power capability remains NOT STATE-RESOLVED.
# ============================================================

out["technical_evidence_label"] = (
    "RANGE-FEASIBLE; AGED-STATE POWER CAPABILITY NOT STATE-RESOLVED"
)

out.loc[
    ~out["range_feasible"],
    "technical_evidence_label",
] = (
    "CONTINUE TECHNICALLY INFEASIBLE — RANGE"
)

out["aged_power_capability_status"] = (
    "NOT STATE-RESOLVED"
)

out["full_technical_feasibility_confirmed"] = False


# ============================================================
# 7. NO CARBON RECLASSIFICATION
#
# D4C is purely a technical mobility robustness layer.
# ============================================================

out["carbon_reclassification_performed"] = False
out["replacement_optimization_performed"] = False

out["time_to_state_used"] = False
out["fleet_prevalence_interpretation"] = False

out["analysis_stage"] = (
    "P16R-D4C_MOBILITY_SERVICE_TECHNICAL_ROBUSTNESS"
)


# ============================================================
# 8. HARD SCIENTIFIC CHECKS
# ============================================================

assert (
    out["technical_range_combined_km"] > 0
).all()

assert (
    out["required_single_service_distance_km"] > 0
).all()

assert not out[
    "full_technical_feasibility_confirmed"
].any()

assert not out[
    "carbon_reclassification_performed"
].any()

assert not out[
    "replacement_optimization_performed"
].any()

assert not out[
    "time_to_state_used"
].any()

assert not out[
    "fleet_prevalence_interpretation"
].any()


# ============================================================
# 9. SAVE
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
# 10. SUMMARY
# ============================================================

summary = (
    out.groupby(
        [
            "scenario_id",
            "required_single_service_distance_km",
        ],
        as_index=False,
    )
    .agg(
        state_rows=(
            "range_feasible",
            "size",
        ),

        feasible_rows=(
            "range_feasible",
            "sum",
        ),

        unique_states=(
            "current_state_key",
            "nunique",
        ),

        minimum_state_range_km=(
            "technical_range_combined_km",
            "min",
        ),

        maximum_state_range_km=(
            "technical_range_combined_km",
            "max",
        ),
    )
)

summary["infeasible_rows"] = (
    summary["state_rows"]
    - summary["feasible_rows"]
)


# Every mobility scenario must retain 567 state rows.
assert (
    summary["state_rows"] == 567
).all()

assert (
    summary["unique_states"] == 567
).all()


print("\nMobility-service technical robustness:")

print(
    summary.to_string(
        index=False
    )
)


print("\nAny range-infeasible state:")

print(
    bool(
        (~out["range_feasible"]).any()
    )
)


print("\nMinimum technical range:")

print(
    float(
        out["technical_range_combined_km"].min()
    ),
    "km",
)


print("\nMaximum locked mobility requirement:")

print(
    float(
        out[
            "required_single_service_distance_km"
        ].max()
    ),
    "km",
)


print("\nTotal physical state × service rows:")

print(
    len(out)
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4C PASS — MOBILITY-SERVICE TECHNICAL ROBUSTNESS COMPLETED"
)

print(
    "LOWER / CENTRAL / UPPER SERVICE REQUIREMENTS: TESTED"
)

print(
    "567/567 PHYSICAL STATES RETAINED PER SERVICE SCENARIO"
)

print(
    "UNIVERSAL SOH CUTOFF: NOT USED"
)

print(
    "STATE-SPECIFIC RANGE FEASIBILITY: USED"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print(
    "FULL TECHNICAL FEASIBILITY CLAIM: NOT MADE"
)

print(
    "CARBON CLASSIFICATION: NOT RECOMPUTED"
)

print(
    "NO TIME-TO-STATE INTERPRETATION"
)

print("=" * 78)