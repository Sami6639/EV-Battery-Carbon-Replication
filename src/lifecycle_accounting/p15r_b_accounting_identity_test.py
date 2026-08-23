from math import isclose

print("=" * 78)
print("P15R-B — ACCOUNTING IDENTITY & UNIT TEST")
print("=" * 78)

# ============================================================
# SYNTHETIC VALUES ONLY
# These are NOT project results.
# This script tests accounting identities and units only.
# ============================================================

distance_km = 100.0

fresh_l2_kwh_per_km = 0.100
degradation_increment_kwh_per_km = 0.002

charging_efficiency = 0.90
grid_ci_gco2e_per_kwh = 400.0

replacement_pack_kwh = 75.0
replacement_mfg_kgco2e_per_kwh = 60.0

# Common invariant burden.
# Synthetic test value only.
original_battery_mfg_kgco2e = 4000.0


# ============================================================
# BASIC DOMAIN CHECKS
# ============================================================

assert distance_km > 0
assert fresh_l2_kwh_per_km > 0
assert degradation_increment_kwh_per_km >= 0

assert 0 < charging_efficiency <= 1

assert grid_ci_gco2e_per_kwh >= 0

assert replacement_pack_kwh > 0
assert replacement_mfg_kgco2e_per_kwh >= 0

assert original_battery_mfg_kgco2e >= 0


# ============================================================
# CONTINUE POLICY — C
# ============================================================

continue_l2_kwh_per_km = (
    fresh_l2_kwh_per_km
    + degradation_increment_kwh_per_km
)

continue_l3_kwh_per_km = (
    continue_l2_kwh_per_km
    / charging_efficiency
)

continue_grid_kwh = (
    continue_l3_kwh_per_km
    * distance_km
)

continue_operational_kgco2e = (
    continue_grid_kwh
    * grid_ci_gco2e_per_kwh
    / 1000.0
)

G_C_total = (
    original_battery_mfg_kgco2e
    + continue_operational_kgco2e
)


# ============================================================
# IMMEDIATE REPLACEMENT POLICY — R
# ============================================================

replace_l2_kwh_per_km = fresh_l2_kwh_per_km

replace_l3_kwh_per_km = (
    replace_l2_kwh_per_km
    / charging_efficiency
)

replace_grid_kwh = (
    replace_l3_kwh_per_km
    * distance_km
)

replace_operational_kgco2e = (
    replace_grid_kwh
    * grid_ci_gco2e_per_kwh
    / 1000.0
)

replacement_mfg_kgco2e = (
    replacement_pack_kwh
    * replacement_mfg_kgco2e_per_kwh
)

G_R_total = (
    original_battery_mfg_kgco2e
    + replacement_mfg_kgco2e
    + replace_operational_kgco2e
)


# ============================================================
# POLICY CONTRAST
#
# DeltaG = G_R - G_C
#
# Positive DeltaG:
# replacement has higher lifecycle GHG.
#
# Negative DeltaG:
# replacement has lower lifecycle GHG.
# ============================================================

DeltaG_full = (
    G_R_total
    - G_C_total
)

DeltaG_driver_only = (
    replacement_mfg_kgco2e
    + replace_operational_kgco2e
    - continue_operational_kgco2e
)


# ============================================================
# ACCOUNTING IDENTITY TESTS
# ============================================================

# L2 -> L3 conversion identity.
assert isclose(
    continue_l3_kwh_per_km,
    continue_l2_kwh_per_km / charging_efficiency,
    rel_tol=1e-12,
    abs_tol=1e-12,
)

assert isclose(
    replace_l3_kwh_per_km,
    replace_l2_kwh_per_km / charging_efficiency,
    rel_tol=1e-12,
    abs_tol=1e-12,
)

# Replacement manufacturing identity.
assert isclose(
    replacement_mfg_kgco2e,
    replacement_pack_kwh
    * replacement_mfg_kgco2e_per_kwh,
    rel_tol=1e-12,
    abs_tol=1e-12,
)

# Common original-battery manufacturing burden
# must cancel from the policy contrast.
cancellation_difference = abs(
    DeltaG_full
    - DeltaG_driver_only
)

assert cancellation_difference <= 1e-9

# Synthetic physical ordering test only.
assert continue_l2_kwh_per_km > replace_l2_kwh_per_km
assert continue_l3_kwh_per_km > replace_l3_kwh_per_km


# ============================================================
# DISPLAY
# ============================================================

print("\nSynthetic L2 -> L3 conversion")
print("-" * 78)

print(
    f"Continue L2 : "
    f"{continue_l2_kwh_per_km:.9f} kWh/km"
)

print(
    f"Continue L3 : "
    f"{continue_l3_kwh_per_km:.9f} kWh/km"
)

print(
    f"Replace L2  : "
    f"{replace_l2_kwh_per_km:.9f} kWh/km"
)

print(
    f"Replace L3  : "
    f"{replace_l3_kwh_per_km:.9f} kWh/km"
)


print("\nSynthetic operational GHG")
print("-" * 78)

print(
    f"Continue operational GHG : "
    f"{continue_operational_kgco2e:.9f} kg CO2e"
)

print(
    f"Replace operational GHG  : "
    f"{replace_operational_kgco2e:.9f} kg CO2e"
)


print("\nSynthetic replacement manufacturing")
print("-" * 78)

print(
    f"Replacement manufacturing GHG : "
    f"{replacement_mfg_kgco2e:.9f} kg CO2e"
)


print("\nCommon-invariant cancellation")
print("-" * 78)

print(
    f"DeltaG full accounting : "
    f"{DeltaG_full:.12f} kg CO2e"
)

print(
    f"DeltaG driver-only     : "
    f"{DeltaG_driver_only:.12f} kg CO2e"
)

print(
    f"Absolute numerical difference : "
    f"{cancellation_difference:.15e}"
)


print("\n" + "=" * 78)
print("P15R-B PASS — ACCOUNTING IDENTITIES AND UNITS VERIFIED")
print("COMMON ORIGINAL-BATTERY BURDEN CANCELS WITHIN NUMERICAL PRECISION")
print("NO PROJECT LIFECYCLE GHG RESULT CALCULATED")
print("NO IDENTIFIED DECISION BOUNDS CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")
print("=" * 78)