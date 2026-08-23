from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "prereg": ROOT / "data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json",

    "p13_baseline": ROOT / "data/processed/representative_bev_baseline.parquet",
    "p13_energy_penalty": ROOT / "data/processed/p13_incremental_energy_penalty.parquet",
    "p13_energy_uncertainty": ROOT / "data/processed/p13_energy_translation_uncertainty.parquet",

    "p14_mobility_use": ROOT / "data/processed/p14_mobility_use_scenarios.parquet",
    "p14_mobility_service": ROOT / "data/processed/p14_mobility_service_requirements.parquet",
    "p14_survival": ROOT / "data/processed/p14_vehicle_survival.parquet",
    "p14_grid": ROOT / "data/processed/p14_grid_pathways.parquet",
    "p14_manufacturing": ROOT / "data/processed/p14_battery_manufacturing_pathways.parquet",
    "p14_charging": ROOT / "data/processed/p14_charging_conversion.parquet",
    "p14_calendar": ROOT / "data/processed/p14_calendar_architecture.parquet",
}

KEYWORDS = (
    "energy", "kwh", "penalty", "capacity", "resistance",
    "year", "age", "km", "mileage", "survival",
    "grid", "co2", "ghg", "manufact", "efficien",
    "scenario", "pathway", "region", "mobility"
)

print("=" * 78)
print("P15R-A1 — INPUT & SCHEMA AUDIT")
print("=" * 78)

missing = []

for name, path in FILES.items():
    if not path.is_file():
        missing.append(str(path))
        print(f"[MISSING] {name}: {path}")
        continue

    if path.suffix == ".json":
        print(f"[OK] {name}: JSON")
        continue

    pf = pq.ParquetFile(path)
    cols = pf.schema.names
    selected = [
        c for c in cols
        if any(k in c.lower() for k in KEYWORDS)
    ]

    print(f"\n[{name}]")
    print(f"rows={pf.metadata.num_rows:,}  columns={len(cols)}")
    print("candidate columns:")
    for c in selected:
        print("  -", c)

if missing:
    print("\n" + "=" * 78)
    print("P15R-A1 FAIL — REQUIRED INPUT FILE(S) MISSING")
    for x in missing:
        print(" -", x)
    raise SystemExit(1)

with FILES["prereg"].open(encoding="utf-8") as f:
    prereg = json.load(f)

checks = {
    "architecture":
        prereg.get("architecture_status")
        == "OPTION B — TRAJECTORY-FREE STATE-CONDITIONED ROBUST / PARTIAL-IDENTIFICATION ARCHITECTURE",

    "primary_S2":
        prereg.get("architecture_roles", {}).get("primary")
        == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION",

    "trajectory_superseded":
        prereg.get("architecture_roles", {}).get("trajectory_optimization")
        == "SUPERSEDED_PROSPECTIVELY",

    "estimand":
        prereg.get("estimand", {}).get("symbolic_definition")
        == "DeltaG(z, theta_R, theta_C) = G_R(z, theta_R) - G_C(z, theta_C)",

    "probability_none":
        prereg.get("estimand", {}).get("probability_interpretation")
        == "NONE",

    "p15r_name":
        prereg.get("next_stages", {}).get("P15R", {}).get("name")
        == "P15R — STATE-CONDITIONED LIFECYCLE-GHG ACCOUNTING ENGINE",

    "optimization_off":
        prereg.get("next_stages", {}).get("P15R", {}).get("optimization_search")
        is False,

    "time_to_state_off":
        prereg.get("current_state_admissibility", {}).get("time_to_state_used")
        is False,
}

print("\n" + "=" * 78)
print("PREREGISTRATION CHECKS")
print("=" * 78)

for name, ok in checks.items():
    print(f"{name}: {'PASS' if ok else 'FAIL'}")

if not all(checks.values()):
    print("\nP15R-A1 FAIL — PREREGISTRATION CONTRACT MISMATCH")
    raise SystemExit(2)

print("\n" + "=" * 78)
print("P15R-A1 PASS — INPUTS PRESENT, PREREGISTRATION CONSISTENT")
print("NO LIFECYCLE GHG CALCULATED")
print("NO DECISION BOUNDS CALCULATED")
print("NO REPLACEMENT OPTIMIZATION PERFORMED")
print("=" * 78)