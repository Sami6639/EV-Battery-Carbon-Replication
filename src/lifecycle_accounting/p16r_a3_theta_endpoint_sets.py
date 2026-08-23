from pathlib import Path
import json

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

STATE_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a2_current_state_admissibility.parquet"
)

P13_CONFIG = (
    ROOT
    / "src"
    / "vehicle_energy"
    / "p13_config.yaml"
)

P13_PARAMS = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

P146C = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
)

P15Q_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

POWER_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_A1D_POWER_EVIDENCE_LIMITATION_LOCK.json"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a3_theta_endpoint_sets.parquet"
)


print("=" * 78)
print("P16R-A3 — THETA_C / THETA_R ENDPOINT-SET CONSTRUCTION")
print("=" * 78)


# ============================================================
# 1. VERIFY AUTHORITATIVE LOCKS
# ============================================================

with P146C.open(encoding="utf-8") as f:
    prereg = json.load(f)

with P15Q_LOCK.open(encoding="utf-8") as f:
    q1_lock = json.load(f)

with POWER_LOCK.open(encoding="utf-8") as f:
    power_lock = json.load(f)

assert (
    prereg["architecture_roles"]["primary"]
    == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
)

assert (
    q1_lock["final_status"]
    == "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS"
)

assert (
    power_lock["aged_power_evidence"]
    == "AGED_STATE_POWER_CAPABILITY_NOT_STATE_RESOLVED"
)

assert (
    prereg["symmetry_rules"]["status"]
    == "HARD_GATE"
)


# ============================================================
# 2. LOAD ADMISSIBLE CURRENT STATES
# ============================================================

states = pd.read_parquet(STATE_FILE)

assert not states.empty
assert states["current_state_admissible"].all()
assert states["dual_state_atlas_eligible"].all()

# Main P16R-A3 works only with the central range-feasible state set.
states = states.loc[
    states["range_feasible_central"]
].copy()

if states.empty:
    raise RuntimeError(
        "P16R-A3 FAIL — no central range-feasible states."
    )


# ============================================================
# 3. LOAD FRESH MACHINE-READABLE REFERENCE
# ============================================================

with P13_CONFIG.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)

with P13_PARAMS.open(encoding="utf-8") as f:
    params = json.load(f)

nominal_pack_kwh = float(
    config["representative_vehicle"]["nominal_pack_energy_kwh"]
)

combined = [
    row
    for row in params["fresh_baseline"]
    if row.get("drive_cycle") == "COMBINED_55_45"
]

assert len(combined) == 1

fresh_l2_kwh_per_km = float(
    combined[0]["fresh_battery_side_kwh_per_km"]
)

assert fresh_l2_kwh_per_km > 0


# ============================================================
# 4. DEFINE ARCHITECTURE-COMPATIBILITY GROUPS
#
# Worst-state endpoints must remain within the same:
# - topology
# - cell-sensitive pack-loss share
# - usable-window assumption
#
# This prevents cross-architecture endpoint cherry-picking.
# ============================================================

architecture_cols = [
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
]


# ============================================================
# 5. FIND WORST CENTRAL-RANGE-FEASIBLE SUPPORTED ENDPOINT
#
# "Worst" here means highest validated combined aged L2
# energy intensity within the compatible architecture.
#
# This is an endpoint bound, NOT a predicted future state.
# ============================================================

worst_index = (
    states.groupby(
        architecture_cols,
        sort=False,
    )["combined_aged_l2_kwh_per_km"]
    .idxmax()
)

worst = states.loc[
    worst_index
].copy()

worst = worst[
    architecture_cols
    + [
        "degradation_state_id",
        "source_id",
        "physical_envelope_class",
        "capacity_retention",
        "relative_resistance",
        "combined_aged_l2_kwh_per_km",
        "usable_battery_energy_kwh",
        "technical_range_combined_km",
        "technical_evidence_classification",
    ]
].rename(
    columns={
        "degradation_state_id":
            "worst_endpoint_state_id",

        "source_id":
            "worst_endpoint_source_id",

        "physical_envelope_class":
            "worst_endpoint_envelope_class",

        "capacity_retention":
            "worst_endpoint_capacity_retention",

        "relative_resistance":
            "worst_endpoint_relative_resistance",

        "combined_aged_l2_kwh_per_km":
            "worst_endpoint_l2_kwh_per_km",

        "usable_battery_energy_kwh":
            "worst_endpoint_usable_energy_kwh",

        "technical_range_combined_km":
            "worst_endpoint_range_km",

        "technical_evidence_classification":
            "worst_endpoint_technical_evidence",
    }
)


# ============================================================
# 6. ATTACH COMPATIBLE WORST ENDPOINT TO EACH CURRENT STATE
# ============================================================

base = states.merge(
    worst,
    on=architecture_cols,
    how="left",
    validate="many_to_one",
)

if base[
    "worst_endpoint_state_id"
].isna().any():
    raise RuntimeError(
        "P16R-A3 FAIL — compatible worst endpoint missing."
    )

# Worst endpoint must be at least as energy-intensive as
# the current state's endpoint within numerical precision.
if (
    base["worst_endpoint_l2_kwh_per_km"]
    + 1e-12
    <
    base["combined_aged_l2_kwh_per_km"]
).any():
    raise RuntimeError(
        "P16R-A3 FAIL — worst endpoint is not actually worst."
    )


# ============================================================
# 7. CURRENT-STATE UNIQUE ANALYSIS KEY
# ============================================================

base["current_state_key"] = (
    base["degradation_state_id"].astype(str)
    + "|"
    + base["topology_id"].astype(str)
    + "|share="
    + base["cell_resistance_share"].astype(str)
    + "|window="
    + base["fresh_usable_window_fraction"].astype(str)
)


# ============================================================
# 8. BUILD THETA_C — CONTINUE
# ============================================================

rows = []

for row in base.itertuples(index=False):

    # --------------------------------------------------------
    # C_LOW
    # Current admissible state held constant.
    # --------------------------------------------------------

    rows.append(
        {
            "current_state_key":
                row.current_state_key,

            "current_degradation_state_id":
                row.degradation_state_id,

            "policy":
                "C",

            "theta_id":
                "C_LOW",

            "theta_role":
                "OPTIMISTIC_OPERATIONAL_PENALTY_BOUND",

            "endpoint_state_rule":
                "CURRENT_ADMISSIBLE_STATE_HELD_CONSTANT",

            "endpoint_state_id":
                row.degradation_state_id,

            "endpoint_source_id":
                row.source_id,

            "endpoint_envelope_class":
                row.physical_envelope_class,

            "endpoint_capacity_retention":
                row.capacity_retention,

            "endpoint_relative_resistance":
                row.relative_resistance,

            "endpoint_l2_kwh_per_km":
                row.combined_aged_l2_kwh_per_km,

            "endpoint_usable_energy_kwh":
                row.usable_battery_energy_kwh,

            "endpoint_range_km":
                row.technical_range_combined_km,

            "topology_id":
                row.topology_id,

            "cell_resistance_share":
                row.cell_resistance_share,

            "fresh_usable_window_fraction":
                row.fresh_usable_window_fraction,

            "range_feasible_central":
                True,

            "aged_power_capability_status":
                "NOT STATE-RESOLVED",

            "predicted_trajectory":
                False,

            "population_probability":
                None,
        }
    )

    # --------------------------------------------------------
    # C_HIGH
    # Worst technically range-feasible supported endpoint
    # under the same architecture.
    # --------------------------------------------------------

    rows.append(
        {
            "current_state_key":
                row.current_state_key,

            "current_degradation_state_id":
                row.degradation_state_id,

            "policy":
                "C",

            "theta_id":
                "C_HIGH",

            "theta_role":
                "PESSIMISTIC_OPERATIONAL_PENALTY_BOUND",

            "endpoint_state_rule":
                "WORST_CENTRAL_RANGE_FEASIBLE_SUPPORTED_STATE",

            "endpoint_state_id":
                row.worst_endpoint_state_id,

            "endpoint_source_id":
                row.worst_endpoint_source_id,

            "endpoint_envelope_class":
                row.worst_endpoint_envelope_class,

            "endpoint_capacity_retention":
                row.worst_endpoint_capacity_retention,

            "endpoint_relative_resistance":
                row.worst_endpoint_relative_resistance,

            "endpoint_l2_kwh_per_km":
                row.worst_endpoint_l2_kwh_per_km,

            "endpoint_usable_energy_kwh":
                row.worst_endpoint_usable_energy_kwh,

            "endpoint_range_km":
                row.worst_endpoint_range_km,

            "topology_id":
                row.topology_id,

            "cell_resistance_share":
                row.cell_resistance_share,

            "fresh_usable_window_fraction":
                row.fresh_usable_window_fraction,

            "range_feasible_central":
                True,

            "aged_power_capability_status":
                "NOT STATE-RESOLVED",

            "predicted_trajectory":
                False,

            "population_probability":
                None,
        }
    )


# ============================================================
# 9. BUILD THETA_R — IMMEDIATE REPLACEMENT
# ============================================================

for row in base.itertuples(index=False):

    fresh_usable_energy = (
        nominal_pack_kwh
        * row.fresh_usable_window_fraction
    )

    fresh_range_km = (
        fresh_usable_energy
        / fresh_l2_kwh_per_km
    )

    # --------------------------------------------------------
    # R_LOW
    # Fresh replacement held at fresh/reference state.
    # --------------------------------------------------------

    rows.append(
        {
            "current_state_key":
                row.current_state_key,

            "current_degradation_state_id":
                row.degradation_state_id,

            "policy":
                "R",

            "theta_id":
                "R_LOW",

            "theta_role":
                "OPTIMISTIC_OPERATIONAL_PENALTY_BOUND",

            "endpoint_state_rule":
                "FRESH_REFERENCE_STATE_HELD_CONSTANT",

            "endpoint_state_id":
                "FRESH_REFERENCE",

            "endpoint_source_id":
                "P13_FRESH_REFERENCE",

            "endpoint_envelope_class":
                "FRESH_REFERENCE",

            "endpoint_capacity_retention":
                1.0,

            "endpoint_relative_resistance":
                1.0,

            "endpoint_l2_kwh_per_km":
                fresh_l2_kwh_per_km,

            "endpoint_usable_energy_kwh":
                fresh_usable_energy,

            "endpoint_range_km":
                fresh_range_km,

            "topology_id":
                row.topology_id,

            "cell_resistance_share":
                row.cell_resistance_share,

            "fresh_usable_window_fraction":
                row.fresh_usable_window_fraction,

            "range_feasible_central":
                bool(
                    fresh_range_km
                    >= row.central_required_range_km
                ),

            "aged_power_capability_status":
                "NOT_APPLICABLE_FRESH_REFERENCE",

            "predicted_trajectory":
                False,

            "population_probability":
                None,
        }
    )

    # --------------------------------------------------------
    # R_HIGH
    #
    # Same worst-state rule as C_HIGH.
    # This is the core policy-symmetry requirement.
    # --------------------------------------------------------

    rows.append(
        {
            "current_state_key":
                row.current_state_key,

            "current_degradation_state_id":
                row.degradation_state_id,

            "policy":
                "R",

            "theta_id":
                "R_HIGH",

            "theta_role":
                "PESSIMISTIC_OPERATIONAL_PENALTY_BOUND",

            "endpoint_state_rule":
                "WORST_CENTRAL_RANGE_FEASIBLE_SUPPORTED_STATE",

            "endpoint_state_id":
                row.worst_endpoint_state_id,

            "endpoint_source_id":
                row.worst_endpoint_source_id,

            "endpoint_envelope_class":
                row.worst_endpoint_envelope_class,

            "endpoint_capacity_retention":
                row.worst_endpoint_capacity_retention,

            "endpoint_relative_resistance":
                row.worst_endpoint_relative_resistance,

            "endpoint_l2_kwh_per_km":
                row.worst_endpoint_l2_kwh_per_km,

            "endpoint_usable_energy_kwh":
                row.worst_endpoint_usable_energy_kwh,

            "endpoint_range_km":
                row.worst_endpoint_range_km,

            "topology_id":
                row.topology_id,

            "cell_resistance_share":
                row.cell_resistance_share,

            "fresh_usable_window_fraction":
                row.fresh_usable_window_fraction,

            "range_feasible_central":
                True,

            "aged_power_capability_status":
                "NOT STATE-RESOLVED",

            "predicted_trajectory":
                False,

            "population_probability":
                None,
        }
    )


theta = pd.DataFrame(rows)


# ============================================================
# 10. POLICY SYMMETRY HARD GATE
# ============================================================

c_high = (
    theta.loc[
        theta["theta_id"] == "C_HIGH"
    ]
    .set_index("current_state_key")
)

r_high = (
    theta.loc[
        theta["theta_id"] == "R_HIGH"
    ]
    .set_index("current_state_key")
)

assert c_high.index.equals(r_high.index)

symmetry_columns = [
    "endpoint_state_id",
    "endpoint_capacity_retention",
    "endpoint_relative_resistance",
    "endpoint_l2_kwh_per_km",
    "endpoint_usable_energy_kwh",
    "endpoint_range_km",
]

for col in symmetry_columns:

    left = c_high[col]
    right = r_high[col]

    if pd.api.types.is_numeric_dtype(left):
        if (
            (left - right)
            .abs()
            .max()
            > 1e-12
        ):
            raise RuntimeError(
                f"P16R-A3 FAIL — symmetry mismatch: {col}"
            )

    else:
        if not left.equals(right):
            raise RuntimeError(
                f"P16R-A3 FAIL — symmetry mismatch: {col}"
            )


# ============================================================
# 11. EXACT SET MEMBERSHIP
# ============================================================

counts = (
    theta.groupby(
        "current_state_key"
    )["theta_id"]
    .agg(list)
)

required_theta = {
    "C_LOW",
    "C_HIGH",
    "R_LOW",
    "R_HIGH",
}

for members in counts:
    if set(members) != required_theta:
        raise RuntimeError(
            "P16R-A3 FAIL — incomplete Theta membership."
        )


# ============================================================
# 12. TECHNICAL / CLAIM SAFETY
# ============================================================

assert theta["range_feasible_central"].all()

assert not theta["predicted_trajectory"].any()

assert theta["population_probability"].isna().all()

theta["full_technical_feasibility_confirmed"] = False

theta["delta_g_calculated"] = False
theta["decision_bounds_calculated"] = False
theta["carbon_classification_calculated"] = False
theta["identification_leverage_calculated"] = False
theta["replacement_optimization_performed"] = False


# ============================================================
# 13. LABEL SCIENTIFIC SET
# ============================================================

theta["set_architecture"] = (
    "P14.6C_S2_MECHANISTIC_SET_IDENTIFICATION"
)

theta["symmetry_gate_status"] = (
    "PASS"
)

theta["technical_claim_status"] = (
    "RANGE_RESOLVED_POWER_NOT_STATE_RESOLVED"
)


# ============================================================
# 14. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

theta.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 15. SUMMARY
# ============================================================

print(
    f"\nCurrent admissible states: "
    f"{theta['current_state_key'].nunique():,}"
)

print(
    f"Theta rows: {len(theta):,}"
)

print("\nTheta membership:")
print(
    theta["theta_id"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nWorst endpoint capacity range:")
worst_rows = theta.loc[
    theta["theta_id"] == "C_HIGH"
]

print(
    float(
        worst_rows[
            "endpoint_capacity_retention"
        ].min()
    ),
    "to",
    float(
        worst_rows[
            "endpoint_capacity_retention"
        ].max()
    ),
)

print("\nWorst endpoint R10 range:")
print(
    float(
        worst_rows[
            "endpoint_relative_resistance"
        ].min()
    ),
    "to",
    float(
        worst_rows[
            "endpoint_relative_resistance"
        ].max()
    ),
)

print("\nWorst endpoint L2 range:")
print(
    float(
        worst_rows[
            "endpoint_l2_kwh_per_km"
        ].min()
    ),
    "to",
    float(
        worst_rows[
            "endpoint_l2_kwh_per_km"
        ].max()
    ),
    "kWh/km",
)

print("\nPolicy symmetry:")
print("C_HIGH == R_HIGH: PASS")

print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-A3 PASS — THETA_C / THETA_R ENDPOINT SETS CONSTRUCTED"
)

print(
    "POLICY SYMMETRY HARD GATE: PASS"
)

print(
    "C_LOW / C_HIGH / R_LOW / R_HIGH: COMPLETE"
)

print(
    "NO PREDICTED TRAJECTORY CREATED"
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

print("=" * 78)