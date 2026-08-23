from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_c4_policy_accounting_components.parquet"
)

df = pd.read_parquet(FILE)

print("=" * 78)
print("P15R-D1 — ACCOUNTING ENGINE GENERALIZATION READINESS AUDIT")
print("=" * 78)

required_identity_columns = [
    "degradation_state_id",
    "physical_envelope_class",
    "valid_domain_status",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
    "grid_scenario",
    "manufacturing_pathway",
    "replacement_chemistry",
    "replacement_pack_kwh",
    "pack_ghg_kgco2e_per_kwh",
]

required_accounting_columns = [
    "C_operational_kgco2e",
    "C_replacement_manufacturing_kgco2e",
    "R_operational_kgco2e",
    "R_replacement_manufacturing_kgco2e",
    "C_policy_varying_subtotal_kgco2e",
    "R_policy_varying_subtotal_kgco2e",
]

missing_identity = [
    c for c in required_identity_columns
    if c not in df.columns
]

missing_accounting = [
    c for c in required_accounting_columns
    if c not in df.columns
]

print("\nMissing identity columns:")
print(missing_identity)

print("\nMissing accounting columns:")
print(missing_accounting)

print("\nCurrent accounting dimensions:")

for col in [
    "grid_scenario",
    "manufacturing_pathway",
    "cell_resistance_share",
    "physical_envelope_class",
]:
    if col in df.columns:
        print(
            f"{col}:",
            sorted(
                df[col]
                .dropna()
                .unique()
                .tolist()
            ),
        )

expected_future_dimensions = {
    "decision_calendar_year": "REQUIRED_FOR_FULL_P15R",
    "current_vehicle_age_years": "REQUIRED_FOR_FULL_P15R",
    "mobility_scenario": "REQUIRED_FOR_FULL_P15R",
    "survival_scenario": "REQUIRED_FOR_FULL_P15R",
    "charging_scenario": "REQUIRED_FOR_FULL_P15R",
    "grid_geography": "REQUIRED_FOR_FULL_P15R",
    "resistance_specification": "REQUIRED_FOR_FULL_P15R",
}

print("\nFuture-context readiness:")

not_ready = []

for col, role in expected_future_dimensions.items():
    present = col in df.columns
    print(
        f"{col}: "
        f"{'PRESENT' if present else 'MISSING'} "
        f"— {role}"
    )
    if not present:
        not_ready.append(col)

forbidden = [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "carbon_classification",
    "decision_classification",
]

for col in forbidden:
    assert col not in df.columns

if missing_identity or missing_accounting:
    print("\nP15R-D1 FAIL — CORE ACCOUNTING SCHEMA INCOMPLETE")
    raise SystemExit(1)

if not_ready:
    print("\n" + "=" * 78)
    print("P15R-D1 WITH BOUNDS — CORE ACCOUNTING VALID,")
    print("BUT FULL CONTEXT PARAMETERIZATION STILL REQUIRED")
    print("Missing future-context fields:")
    for x in not_ready:
        print(" -", x)
    print("P15R FINAL GATE NOT YET AUTHORIZED")
    print("=" * 78)

else:
    print("\n" + "=" * 78)
    print("P15R-D1 PASS — ACCOUNTING SCHEMA GENERALIZATION READY")
    print("P15R FINAL GATE MAY PROCEED")
    print("=" * 78)

print("\nNO NEW LIFECYCLE GHG CALCULATION PERFORMED")
print("NO DELTAG CALCULATED")
print("NO DECISION BOUNDS CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")