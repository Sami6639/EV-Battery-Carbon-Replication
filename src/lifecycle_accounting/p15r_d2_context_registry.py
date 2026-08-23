from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

PREREG_FILE = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
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

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d2_context_registry.parquet"
)


print("=" * 78)
print("P15R-D2 — CONTEXT REGISTRY & PARAMETERIZATION LOCK")
print("=" * 78)


# ============================================================
# 1. LOAD AUTHORITATIVE PREREGISTRATION
# ============================================================

with PREREG_FILE.open(encoding="utf-8") as f:
    prereg = json.load(f)

assert (
    prereg["architecture_roles"]["primary"]
    == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
)

assert (
    prereg["next_stages"]["P15R"]["optimization_search"]
    is False
)


# ============================================================
# 2. LOAD REAL FROZEN INPUT TABLES
# ============================================================

mobility = pd.read_parquet(MOBILITY_FILE)
survival = pd.read_parquet(SURVIVAL_FILE)
charging = pd.read_parquet(CHARGING_FILE)
grid = pd.read_parquet(GRID_FILE)
energy = pd.read_parquet(ENERGY_FILE)


# ============================================================
# 3. EXACT ALLOWED VALUES
# ============================================================

allowed = {
    "decision_calendar_year": [2025],

    "current_vehicle_age_years": sorted(
        int(x)
        for x in survival[
            "current_vehicle_age_years"
        ].unique()
    ),

    "mobility_scenario": sorted(
        mobility["scenario_id"]
        .dropna()
        .unique()
        .tolist()
    ),

    "survival_scenario": sorted(
        survival["survival_scenario"]
        .dropna()
        .unique()
        .tolist()
    ),

    "charging_scenario": sorted(
        charging["scenario_id"]
        .dropna()
        .unique()
        .tolist()
    ),

    "grid_geography": sorted(
        grid["geography_level"]
        .dropna()
        .unique()
        .tolist()
    ),

    "resistance_specification": sorted(
        energy["resistance_specification"]
        .dropna()
        .unique()
        .tolist()
    ),
}


# ============================================================
# 4. PREREGISTERED PRIMARY VALUES
# ============================================================

primary = {
    "decision_calendar_year": 2025,
    "current_vehicle_age_years": 0,
    "mobility_scenario": "central_use",
    "survival_scenario": "central",
    "charging_scenario": "central_efficiency",
    "grid_geography": "US_LOAD_WEIGHTED",
    "resistance_specification": "10-ms",
}


# ============================================================
# 5. VERIFY PRIMARY VALUES ARE REAL SOURCE VALUES
# ============================================================

for dimension, value in primary.items():
    if value not in allowed[dimension]:
        raise RuntimeError(
            f"P15R-D2 FAIL — primary value {value!r} "
            f"not present for {dimension}"
        )


# ============================================================
# 6. VERIFY PREREGISTRATION CONSISTENCY
# ============================================================

scenario_tiers = prereg["scenario_hierarchy"]

assert (
    scenario_tiers["primary_identified_set"]["mileage"]
    == "central_use"
)

assert (
    scenario_tiers["primary_identified_set"][
        "charging_efficiency"
    ]
    == "p50"
)

assert (
    scenario_tiers["primary_identified_set"][
        "grid_geography"
    ]
    == "LOAD_WEIGHTED_US"
)

assert (
    prereg["r10_r1s_rules"]["primary"]
    == "R10"
)

assert (
    prereg["r10_r1s_rules"][
        "alternative_physical_robustness"
    ]
    == "R1s"
)


# ============================================================
# 7. BUILD MACHINE-READABLE REGISTRY
# ============================================================

rows = []

for dimension, values in allowed.items():
    for value in values:

        tier = (
            "PRIMARY"
            if value == primary[dimension]
            else "STRUCTURAL_ROBUSTNESS"
        )

        rows.append(
            {
                "dimension": dimension,
                "value": str(value),
                "tier": tier,
                "is_primary": (
                    value == primary[dimension]
                ),
                "source_stage": (
                    "P14"
                    if dimension
                    != "resistance_specification"
                    else "P13"
                ),
                "trajectory_role": "NONE",
                "optimization_role": "NONE",
            }
        )

registry = pd.DataFrame(rows)


# ============================================================
# 8. HARD CHECKS
# ============================================================

assert not registry.empty

assert (
    registry.groupby("dimension")["is_primary"]
    .sum()
    .eq(1)
    .all()
)

assert (
    set(registry["dimension"])
    == set(allowed)
)

assert (
    registry["trajectory_role"]
    == "NONE"
).all()

assert (
    registry["optimization_role"]
    == "NONE"
).all()


# ============================================================
# 9. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

registry.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 10. DISPLAY
# ============================================================

print("\nPrimary P15R context:")

for key, value in primary.items():
    print(f"  {key}: {value}")


print("\nRegistered dimensions:")

for dimension in allowed:
    print(
        f"  {dimension}: "
        f"{len(allowed[dimension])} allowed value(s)"
    )


print("\nRegistry rows:", len(registry))

print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P15R-D2 PASS — CONTEXT REGISTRY "
    "PREREGISTRATION CONSISTENT"
)

print(
    "PRIMARY AND STRUCTURAL CONTEXTS "
    "ARE MACHINE-READABLE"
)

print(
    "NO LIFECYCLE GHG CALCULATED"
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

print(
    "NO REPLACEMENT OPTIMIZATION PERFORMED"
)

print("=" * 78)