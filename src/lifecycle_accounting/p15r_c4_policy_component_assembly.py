from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_c3_residual_operational_components.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_c4_policy_accounting_components.parquet"
)


print("=" * 78)
print("P15R-C4 — POLICY COMPONENT ASSEMBLY & NO-DOUBLE-COUNTING GATE")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED P15R-C3 COMPONENTS
# ============================================================

df = pd.read_parquet(INPUT_FILE)

assert not df.empty


# ============================================================
# 2. CONTINUE POLICY — C
#
# Policy-varying components currently implemented:
#
# - residual operational GHG
#
# Replacement manufacturing must be ZERO for C.
# ============================================================

df["C_operational_kgco2e"] = (
    df["continue_residual_operational_kgco2e"]
)

df["C_replacement_manufacturing_kgco2e"] = 0.0


# ============================================================
# 3. IMMEDIATE REPLACEMENT POLICY — R
#
# Policy-varying components:
#
# - residual operational GHG
# - replacement battery manufacturing GHG
#
# Replacement manufacturing is incurred ONCE at decision year.
# It is NOT multiplied by survival, mileage, or service years.
# ============================================================

df["R_operational_kgco2e"] = (
    df["replace_residual_operational_kgco2e"]
)

df["R_replacement_manufacturing_kgco2e"] = (
    df["replacement_manufacturing_kgco2e"]
)


# ============================================================
# 4. COMMON INVARIANT ACCOUNTING
#
# Original battery manufacturing belongs to total LCA,
# but is common to both policies at the decision point.
#
# P15R-C4 therefore does NOT invent or duplicate a numerical
# original-battery manufacturing value here.
#
# Its cancellation identity was already verified in P15R-B.
# ============================================================

df["common_original_battery_manufacturing_status"] = (
    "COMMON_INVARIANT_INCLUDED_ONCE_IN_TOTAL_LCA_NOT_A_POLICY_DRIVER"
)

df["common_invariant_numeric_added_in_c4"] = False


# ============================================================
# 5. POLICY-VARYING SUBTOTALS
#
# These are NOT final lifecycle totals.
# They contain only presently implemented decision-varying
# accounting components.
# ============================================================

df["C_policy_varying_subtotal_kgco2e"] = (
    df["C_operational_kgco2e"]
    + df["C_replacement_manufacturing_kgco2e"]
)

df["R_policy_varying_subtotal_kgco2e"] = (
    df["R_operational_kgco2e"]
    + df["R_replacement_manufacturing_kgco2e"]
)


# ============================================================
# 6. HARD ACCOUNTING CHECKS
# ============================================================

assert (
    df["C_replacement_manufacturing_kgco2e"] == 0
).all()

assert (
    df["R_replacement_manufacturing_kgco2e"] >= 0
).all()

assert (
    df["C_operational_kgco2e"] >= 0
).all()

assert (
    df["R_operational_kgco2e"] >= 0
).all()

assert (
    df["C_policy_varying_subtotal_kgco2e"]
    == df["C_operational_kgco2e"]
).all()

assert (
    df["R_policy_varying_subtotal_kgco2e"]
    ==
    (
        df["R_operational_kgco2e"]
        + df["R_replacement_manufacturing_kgco2e"]
    )
).all()

assert not df["common_invariant_numeric_added_in_c4"].any()


# ============================================================
# 7. VERIFY REPLACEMENT MANUFACTURING IS NOT ANNUALIZED
# ============================================================

required = {
    "replacement_pack_kwh",
    "pack_ghg_kgco2e_per_kwh",
    "replacement_manufacturing_kgco2e",
}

assert required <= set(df.columns)

expected_mfg = (
    df["replacement_pack_kwh"]
    * df["pack_ghg_kgco2e_per_kwh"]
)

difference = (
    df["replacement_manufacturing_kgco2e"]
    - expected_mfg
).abs()

assert difference.max() <= 1e-9


# ============================================================
# 8. FORBIDDEN P16R OUTPUTS
# ============================================================

for forbidden_column in [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "carbon_classification",
    "decision_classification",
]:
    assert forbidden_column not in df.columns


# ============================================================
# 9. STAGE DISCLOSURES
# ============================================================

df["accounting_stage"] = "P15R-C4"

df["lifecycle_total_calculated"] = False
df["delta_g_calculated"] = False
df["decision_bounds_calculated"] = False
df["carbon_classification_produced"] = False
df["replacement_optimization_performed"] = False


# ============================================================
# 10. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 11. SUMMARY
# ============================================================

print(f"\nRows: {len(df):,}")

print("\nC policy-varying subtotal range:")
print(
    float(
        df["C_policy_varying_subtotal_kgco2e"].min()
    ),
    "to",
    float(
        df["C_policy_varying_subtotal_kgco2e"].max()
    ),
    "kg CO2e",
)

print("\nR policy-varying subtotal range:")
print(
    float(
        df["R_policy_varying_subtotal_kgco2e"].min()
    ),
    "to",
    float(
        df["R_policy_varying_subtotal_kgco2e"].max()
    ),
    "kg CO2e",
)

print("\nReplacement manufacturing range:")
print(
    float(
        df["R_replacement_manufacturing_kgco2e"].min()
    ),
    "to",
    float(
        df["R_replacement_manufacturing_kgco2e"].max()
    ),
    "kg CO2e",
)

print("\nOutput:")
print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P15R-C4 PASS — POLICY ACCOUNTING COMPONENTS ASSEMBLED"
)

print(
    "REPLACEMENT MANUFACTURING COUNTED ONCE IN POLICY R"
)

print(
    "REPLACEMENT MANUFACTURING ABSENT FROM POLICY C"
)

print(
    "COMMON ORIGINAL-BATTERY BURDEN RETAINED AS INVARIANT"
)

print(
    "NO LIFECYCLE TOTAL CALCULATED"
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