from pathlib import Path
import json

import pandas as pd


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

POWER_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_A1D_POWER_EVIDENCE_LIMITATION_LOCK.json"
)

P15Q_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_a2_current_state_admissibility.parquet"
)


print("=" * 78)
print("P16R-A2 — CURRENT-STATE ADMISSIBILITY + CENTRAL RANGE SCREEN")
print("=" * 78)


# ============================================================
# 1. VERIFY PRE-RESULT LOCKS
# ============================================================

with POWER_LOCK.open(encoding="utf-8") as f:
    power_lock = json.load(f)

with P15Q_LOCK.open(encoding="utf-8") as f:
    p15q = json.load(f)

assert (
    power_lock["final_status"]
    ==
    "POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS"
)

assert (
    power_lock["aged_power_evidence"]
    ==
    "AGED_STATE_POWER_CAPABILITY_NOT_STATE_RESOLVED"
)

assert (
    p15q["final_status"]
    ==
    "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS"
)

assert (
    p15q["numerical_p16r_result_calculated"]
    is False
)


# ============================================================
# 2. LOAD INPUTS
# ============================================================

energy = pd.read_parquet(ENERGY_FILE)
service = pd.read_parquet(SERVICE_FILE)


# ============================================================
# 3. CENTRAL MOBILITY REQUIREMENT
# ============================================================

central_service = service.loc[
    service["scenario_id"] == "mobility_central"
].copy()

assert len(central_service) == 1

required_range_km = float(
    central_service.iloc[0][
        "required_single_service_distance_km"
    ]
)

print(
    f"Central required service distance: "
    f"{required_range_km:.6f} km"
)


# ============================================================
# 4. PRIMARY R10 MAIN IDENTIFIED-SET STATES
# ============================================================

allowed_classes = {
    "PRIMARY PHYSICAL SPECIFICATION",
    "AUTOMOTIVE-COMPATIBLE ENVELOPE",
}

allowed_status = {
    "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
    "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
}

states = energy.loc[
    (energy["resistance_specification"] == "10-ms")
    & (~energy["conditional_extreme"])
    & (
        energy["physical_envelope_class"]
        .isin(allowed_classes)
    )
    & (
        energy["valid_domain_status"]
        .isin(allowed_status)
    )
    & (
        energy["drive_cycle"]
        .isin(["UDDS", "HWFET"])
    )
].copy()

if states.empty:
    raise RuntimeError(
        "P16R-A2 FAIL — no admissible primary R10 states."
    )


# ============================================================
# 5. STATE IDENTITY
# ============================================================

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


# ============================================================
# 6. REQUIRE ONE UDDS + ONE HWFET ROW PER STATE
# ============================================================

dup = states.duplicated(
    subset=key_cols + ["drive_cycle"],
    keep=False,
)

if dup.any():
    raise RuntimeError(
        "P16R-A2 FAIL — duplicate state/cycle rows found."
    )


# ============================================================
# 7. CHECK USABLE ENERGY CONSISTENCY ACROSS CYCLES
# ============================================================

usable_check = (
    states.groupby(key_cols)[
        "usable_battery_energy_kwh"
    ]
    .nunique()
)

if (usable_check > 1).any():
    raise RuntimeError(
        "P16R-A2 FAIL — usable energy differs "
        "between drive cycles for the same state."
    )


# ============================================================
# 8. BUILD LOCKED 55/45 COMBINED STATE
# ============================================================

wide = (
    states[
        key_cols
        + [
            "drive_cycle",
            "aged_battery_side_kwh_per_km",
            "usable_battery_energy_kwh",
        ]
    ]
    .pivot(
        index=key_cols,
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


required_cols = [
    "aged_battery_side_kwh_per_km_UDDS",
    "aged_battery_side_kwh_per_km_HWFET",
    "usable_battery_energy_kwh_UDDS",
    "usable_battery_energy_kwh_HWFET",
]

if wide[required_cols].isna().any().any():
    raise RuntimeError(
        "P16R-A2 FAIL — incomplete UDDS/HWFET state pair."
    )


# ============================================================
# 9. VERIFY USABLE ENERGY EQUALITY
# ============================================================

usable_diff = (
    wide["usable_battery_energy_kwh_UDDS"]
    - wide["usable_battery_energy_kwh_HWFET"]
).abs()

if usable_diff.max() > 1e-10:
    raise RuntimeError(
        "P16R-A2 FAIL — usable energy mismatch."
    )


wide["usable_battery_energy_kwh"] = (
    wide["usable_battery_energy_kwh_UDDS"]
)


# ============================================================
# 10. LOCKED COMBINED AGED L2 INTENSITY
# ============================================================

wide["combined_aged_l2_kwh_per_km"] = (
    0.55
    * wide["aged_battery_side_kwh_per_km_UDDS"]
    +
    0.45
    * wide["aged_battery_side_kwh_per_km_HWFET"]
)

assert (
    wide["combined_aged_l2_kwh_per_km"] > 0
).all()


# ============================================================
# 11. STATE-SPECIFIC TECHNICAL RANGE
# ============================================================

wide["technical_range_combined_km"] = (
    wide["usable_battery_energy_kwh"]
    / wide["combined_aged_l2_kwh_per_km"]
)

assert (
    wide["technical_range_combined_km"] > 0
).all()


# ============================================================
# 12. CENTRAL RANGE FEASIBILITY
# ============================================================

wide["central_required_range_km"] = (
    required_range_km
)

wide["range_feasible_central"] = (
    wide["technical_range_combined_km"]
    >= wide["central_required_range_km"]
)


# ============================================================
# 13. TECHNICAL EVIDENCE LABEL
# ============================================================

wide["aged_power_capability_status"] = (
    "NOT STATE-RESOLVED"
)

wide["full_technical_feasibility_confirmed"] = False


wide["technical_evidence_classification"] = (
    wide["range_feasible_central"].map(
        {
            True:
            "RANGE-FEASIBLE; AGED-STATE POWER CAPABILITY NOT STATE-RESOLVED",

            False:
            "CONTINUE TECHNICALLY INFEASIBLE — RANGE",
        }
    )
)


# ============================================================
# 14. CURRENT-STATE ADMISSIBILITY
# ============================================================

wide["current_state_admissible"] = True

wide["state_admissibility_basis"] = (
    "P12_P13_SUPPORTED_R10_MAIN_IDENTIFIED_SET"
)

wide["time_to_state_used"] = False
wide["fleet_prevalence_interpretation"] = False


# ============================================================
# 15. Q1 DUAL-STATE METADATA
# ============================================================

wide["dual_state_atlas_eligible"] = True

wide["capacity_match_half_width"] = 0.025

wide["resistance_specification"] = "10-ms"

wide["headline_state_tier"] = "MAIN_IDENTIFIED_SET"


# ============================================================
# 16. NO DECISION/CARBON LEAKAGE
# ============================================================

wide["delta_g_calculated"] = False
wide["decision_bounds_calculated"] = False
wide["carbon_classification_calculated"] = False
wide["identification_leverage_calculated"] = False
wide["replacement_optimization_performed"] = False


for forbidden in [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "carbon_classification",
]:
    assert forbidden not in wide.columns


# ============================================================
# 17. CLEAN UNUSED CYCLE-SPECIFIC USABLE ENERGY
# ============================================================

wide = wide.drop(
    columns=[
        "usable_battery_energy_kwh_UDDS",
        "usable_battery_energy_kwh_HWFET",
    ]
)


# ============================================================
# 18. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

wide.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 19. SUMMARY
# ============================================================

print(f"\nAdmissible dual-state rows: {len(wide):,}")

print(
    "Capacity retention range:",
    float(wide["capacity_retention"].min()),
    "to",
    float(wide["capacity_retention"].max()),
)

print(
    "Relative R10 range:",
    float(wide["relative_resistance"].min()),
    "to",
    float(wide["relative_resistance"].max()),
)

print(
    "Combined technical range:",
    float(
        wide["technical_range_combined_km"].min()
    ),
    "to",
    float(
        wide["technical_range_combined_km"].max()
    ),
    "km",
)

print(
    "\nCentral range-feasible rows:",
    int(wide["range_feasible_central"].sum()),
)

print(
    "Central range-infeasible rows:",
    int((~wide["range_feasible_central"]).sum()),
)


print("\nTechnical evidence classifications:")

print(
    wide[
        "technical_evidence_classification"
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
    "P16R-A2 PASS — CURRENT-STATE ADMISSIBILITY "
    "AND RANGE SCREEN CONSTRUCTED"
)

print(
    "DUAL-STATE ATLAS ELIGIBLE STATES: "
    f"{len(wide):,}"
)

print(
    "STATE-SPECIFIC RANGE FEASIBILITY: CALCULATED"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print(
    "NO FULL TECHNICAL FEASIBILITY CLAIM PRODUCED"
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