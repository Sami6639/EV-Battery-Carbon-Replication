from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

PACK_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_pack_electrical_states.parquet"
)

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

PARAM_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

print("=" * 78)
print("P16R-A1C — POWER-SERVICE CONTRACT AUDIT")
print("=" * 78)

pack = pd.read_parquet(PACK_FILE)
energy = pd.read_parquet(ENERGY_FILE)

with PARAM_FILE.open(encoding="utf-8") as f:
    params = json.load(f)

print("\nP13 pack-state candidate power columns:")

power_cols = [
    c for c in pack.columns
    if any(
        key in c.lower()
        for key in (
            "power",
            "voltage",
            "current",
            "sag",
            "feasib",
        )
    )
]

for c in power_cols:
    print(" -", c)

print("\nP13 energy-state candidate power/range columns:")

energy_cols = [
    c for c in energy.columns
    if any(
        key in c.lower()
        for key in (
            "power",
            "voltage",
            "current",
            "range",
            "feasib",
        )
    )
]

for c in energy_cols:
    print(" -", c)

print("\nFresh baseline terminal-power records:")

for row in params.get("fresh_baseline", []):
    print(
        row.get("drive_cycle"),
        "min_terminal_kw=",
        row.get("minimum_terminal_power_kw"),
        "max_terminal_kw=",
        row.get("maximum_terminal_power_kw"),
    )

state_specific_power_fields = [
    c for c in pack.columns
    if any(
        token in c.lower()
        for token in (
            "deliverable_power",
            "available_power",
            "power_feasible",
            "voltage_sag",
            "current_limit",
        )
    )
]

print("\nState-specific aged power fields:")
print(state_specific_power_fields)

if state_specific_power_fields:
    status = "STATE_SPECIFIC_POWER_FEASIBILITY_MACHINE_READABLE"
else:
    status = "STATE_SPECIFIC_POWER_FEASIBILITY_NOT_MACHINE_READABLE"

print("\n" + "=" * 78)
print(status)
print("NO POWER FEASIBILITY ASSUMPTION ADDED")
print("NO DELTAG CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")
print("=" * 78)