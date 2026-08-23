from pathlib import Path
import json

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]

MECHANISM_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d3b_temporal_mechanism_decomposition.parquet"
)

EXTREME_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d4e4_extreme_physical_stress.parquet"
)

MFG_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p14_battery_manufacturing_pathways.parquet"
)

ENERGY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

CONFIG_FILE = (
    ROOT
    / "src"
    / "vehicle_energy"
    / "p13_config.yaml"
)

P16_MANIFEST = (
    ROOT
    / "results"
    / "intermediate"
    / "p16_final_scientific_manifest.json"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16_q0_break_even_defense.parquet"
)

REPORT_FILE = (
    ROOT
    / "docs"
    / "P16_Q0_MAGNITUDE_BREAK_EVEN_DEFENSE_REPORT.md"
)

RECEIPT_FILE = (
    ROOT
    / "data"
    / "metadata"
    / "P16_Q0_MAGNITUDE_BREAK_EVEN_DEFENSE.json"
)


print("=" * 78)
print("P16-Q0 — MAGNITUDE & MANUFACTURING BREAK-EVEN DEFENSE")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED P16 OUTPUTS
# ============================================================

mechanism = pd.read_parquet(
    MECHANISM_FILE
)

extreme = pd.read_parquet(
    EXTREME_FILE
)

mfg = pd.read_parquet(
    MFG_FILE
)

energy = pd.read_parquet(
    ENERGY_FILE
)

with CONFIG_FILE.open(
    encoding="utf-8"
) as f:
    config = yaml.safe_load(f)

with P16_MANIFEST.open(
    encoding="utf-8"
) as f:
    p16 = json.load(f)


assert (
    p16["final_status"]
    ==
    "P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — "
    "READY FOR Q1 PUBLICATION-STRENGTH GATE"
)


# ============================================================
# 2. NOMINAL PACK ENERGY
# ============================================================

nominal_pack_kwh = float(
    config[
        "representative_vehicle"
    ][
        "nominal_pack_energy_kwh"
    ]
)

assert nominal_pack_kwh > 0


# ============================================================
# 3. PRIMARY-DOMAIN MAXIMUM OPERATIONAL SAVING
#
# Already derived in P16-D3B.
# No new degradation model.
# ============================================================

primary_max_operational_saving = float(
    mechanism[
        "max_operational_saving_kgco2e"
    ].max()
)

assert primary_max_operational_saving >= 0


primary_break_even_mfg_ci = (
    primary_max_operational_saving
    / nominal_pack_kwh
)


# ============================================================
# 4. EXTREME / CONDITIONAL STRESS-DOMAIN
#    MAXIMUM OPERATIONAL SAVING
#
# In D4E4:
#
# lower_DeltaG =
# replacement manufacturing
# - maximum admissible operational saving
#
# Therefore:
#
# max operational saving =
# manufacturing - lower_DeltaG
#
# This is a conservative physical stress defense.
# ============================================================

extreme = extreme.copy()

extreme[
    "implied_max_operational_saving_kgco2e"
] = (
    extreme[
        "replacement_manufacturing_kgco2e"
    ]
    - extreme[
        "lower_DeltaG"
    ]
)

if (
    extreme[
        "implied_max_operational_saving_kgco2e"
    ] < -1e-9
).any():
    raise RuntimeError(
        "P16-Q0 FAIL — negative implied operational saving."
    )

extreme[
    "implied_max_operational_saving_kgco2e"
] = (
    extreme[
        "implied_max_operational_saving_kgco2e"
    ]
    .clip(lower=0)
)


extreme_max_operational_saving = float(
    extreme[
        "implied_max_operational_saving_kgco2e"
    ].max()
)


extreme_break_even_mfg_ci = (
    extreme_max_operational_saving
    / nominal_pack_kwh
)


# ============================================================
# 5. FROZEN NMC811 PROSPECTIVE MANUFACTURING ENVELOPE
#
# No Xu 2022 values are introduced here.
# No recycling credits are introduced here.
#
# Use only the already processed P14 NMC811 evidence.
# ============================================================

nmc811 = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (
        mfg["benchmark_type"]
        == "PROSPECTIVE"
    )
].copy()

if nmc811.empty:
    raise RuntimeError(
        "P16-Q0 FAIL — no frozen prospective NMC811 pathway."
    )


prospective_mfg_min = float(
    nmc811[
        "pack_ghg_kgco2e_per_kwh"
    ].min()
)

prospective_mfg_max = float(
    nmc811[
        "pack_ghg_kgco2e_per_kwh"
    ].max()
)


min_row = (
    nmc811.loc[
        nmc811[
            "pack_ghg_kgco2e_per_kwh"
        ].idxmin()
    ]
)


# ============================================================
# 6. SAME-SOURCE STATIC BENCHMARK
# ============================================================

static = mfg.loc[
    (mfg["chemistry"] == "NMC811")
    & (
        mfg["benchmark_type"]
        == "STATIC_SAME_SOURCE_2020"
    )
].copy()


static_mfg_ci = (
    float(
        static[
            "pack_ghg_kgco2e_per_kwh"
        ].iloc[0]
    )
    if not static.empty
    else None
)


# ============================================================
# 7. BREAK-EVEN SEPARATION RATIOS
#
# These are NOT probability or uncertainty metrics.
#
# They answer:
#
# How many times larger is the smallest frozen prospective
# manufacturing intensity than the manufacturing intensity
# required for replacement to break even with the largest
# admissible operational saving?
# ============================================================

if primary_break_even_mfg_ci > 0:

    primary_separation_ratio = (
        prospective_mfg_min
        / primary_break_even_mfg_ci
    )

else:

    primary_separation_ratio = float("inf")


if extreme_break_even_mfg_ci > 0:

    extreme_separation_ratio = (
        prospective_mfg_min
        / extreme_break_even_mfg_ci
    )

else:

    extreme_separation_ratio = float("inf")


# ============================================================
# 8. REQUIRED MANUFACTURING REDUCTION
#
# Relative to the minimum already-frozen NMC811 prospective CI.
# ============================================================

primary_required_reduction_fraction = (
    1.0
    - (
        primary_break_even_mfg_ci
        / prospective_mfg_min
    )
)


extreme_required_reduction_fraction = (
    1.0
    - (
        extreme_break_even_mfg_ci
        / prospective_mfg_min
    )
)


# ============================================================
# 9. ENERGY-PENALTY MAGNITUDE AUDIT
# ============================================================

primary_r10 = energy.loc[
    (energy["resistance_specification"] == "10-ms")
    & (~energy["conditional_extreme"])
].copy()

primary_r1s = energy.loc[
    (energy["resistance_specification"] == "1-s")
    & (~energy["conditional_extreme"])
].copy()

extreme_energy = energy.loc[
    energy["conditional_extreme"]
].copy()


primary_r10_max_penalty_pct = float(
    primary_r10[
        "incremental_battery_side_energy_percent"
    ].max()
)

primary_r1s_max_penalty_pct = float(
    primary_r1s[
        "incremental_battery_side_energy_percent"
    ].max()
)

extreme_max_penalty_pct = float(
    extreme_energy[
        "incremental_battery_side_energy_percent"
    ].max()
)


# ============================================================
# 10. HARD PLAUSIBILITY DEFENSE
#
# Strongest conservative test:
#
# even the MINIMUM frozen prospective NMC811 manufacturing
# intensity must remain above the EXTREME physical-stress
# break-even manufacturing intensity.
#
# No arbitrary 10x / 100x publication threshold is imposed.
# ============================================================

frozen_envelope_dominates_extreme_threshold = (
    prospective_mfg_min
    > extreme_break_even_mfg_ci
)

if not frozen_envelope_dominates_extreme_threshold:
    raise RuntimeError(
        "P16-Q0 FAIL — frozen NMC811 manufacturing envelope "
        "does not dominate extreme break-even threshold."
    )


# ============================================================
# 11. OUTPUT TABLE
# ============================================================

out = pd.DataFrame(
    [
        {
            "domain":
                "PRIMARY_IDENTIFIED_DOMAIN",

            "maximum_operational_saving_kgco2e":
                primary_max_operational_saving,

            "break_even_manufacturing_ci_kgco2e_per_kwh":
                primary_break_even_mfg_ci,

            "minimum_frozen_nmc811_prospective_ci":
                prospective_mfg_min,

            "separation_ratio":
                primary_separation_ratio,

            "required_reduction_fraction_vs_min_frozen_ci":
                primary_required_reduction_fraction,
        },

        {
            "domain":
                "EXTREME_CONDITIONAL_STRESS_DOMAIN",

            "maximum_operational_saving_kgco2e":
                extreme_max_operational_saving,

            "break_even_manufacturing_ci_kgco2e_per_kwh":
                extreme_break_even_mfg_ci,

            "minimum_frozen_nmc811_prospective_ci":
                prospective_mfg_min,

            "separation_ratio":
                extreme_separation_ratio,

            "required_reduction_fraction_vs_min_frozen_ci":
                extreme_required_reduction_fraction,
        },
    ]
)


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

out.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 12. RECEIPT
# ============================================================

receipt = {
    "stage":
        "P16-Q0",

    "final_status":
        "MAGNITUDE AND MANUFACTURING BREAK-EVEN DEFENSE — PASS",

    "nominal_pack_kwh":
        nominal_pack_kwh,

    "primary_max_operational_saving_kgco2e":
        primary_max_operational_saving,

    "extreme_max_operational_saving_kgco2e":
        extreme_max_operational_saving,

    "primary_break_even_mfg_ci_kgco2e_per_kwh":
        primary_break_even_mfg_ci,

    "extreme_break_even_mfg_ci_kgco2e_per_kwh":
        extreme_break_even_mfg_ci,

    "minimum_frozen_nmc811_prospective_ci":
        prospective_mfg_min,

    "maximum_frozen_nmc811_prospective_ci":
        prospective_mfg_max,

    "minimum_frozen_ci_identity": {
        "pathway":
            str(min_row["pathway"]),

        "calendar_year":
            int(min_row["calendar_year"]),

        "value":
            prospective_mfg_min,
    },

    "static_same_source_ci":
        static_mfg_ci,

    "primary_separation_ratio":
        primary_separation_ratio,

    "extreme_separation_ratio":
        extreme_separation_ratio,

    "primary_required_reduction_fraction":
        primary_required_reduction_fraction,

    "extreme_required_reduction_fraction":
        extreme_required_reduction_fraction,

    "primary_r10_max_energy_penalty_percent":
        primary_r10_max_penalty_pct,

    "primary_r1s_max_energy_penalty_percent":
        primary_r1s_max_penalty_pct,

    "extreme_max_energy_penalty_percent":
        extreme_max_penalty_pct,

    "frozen_envelope_dominates_extreme_threshold":
        frozen_envelope_dominates_extreme_threshold,

    "xu_2022_used":
        False,

    "recycling_credit_used":
        False,

    "new_degradation_model_fitted":
        False,

    "break_even_time_calculated":
        False,

    "replacement_optimization_performed":
        False,
}


RECEIPT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

RECEIPT_FILE.write_text(
    json.dumps(
        receipt,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 13. REPORT
# ============================================================

report = f"""# P16-Q0 — Magnitude & Manufacturing Break-Even Defense

## Final Status

`MAGNITUDE AND MANUFACTURING BREAK-EVEN DEFENSE — PASS`

## Purpose

This gate addresses whether the robust continuation result is merely an
artifact of a small degradation-energy penalty.

No new degradation model, trajectory, replacement optimization, Xu 2022
parameterization, or recycling credit is introduced.

## Pack Energy

Nominal pack energy:

`{nominal_pack_kwh:.6f} kWh`

## Primary Identified Domain

Maximum admissible operational-carbon saving from replacement:

`{primary_max_operational_saving:.6f} kg CO2e`

Corresponding manufacturing-intensity break-even threshold:

`{primary_break_even_mfg_ci:.9f} kg CO2e/kWh_pack`

## Extreme / Conditional Physical Stress Domain

Maximum operational-carbon saving under the physics-translated extreme
stress envelope:

`{extreme_max_operational_saving:.6f} kg CO2e`

Corresponding conservative break-even manufacturing intensity:

`{extreme_break_even_mfg_ci:.9f} kg CO2e/kWh_pack`

## Frozen NMC811 Manufacturing Evidence

Minimum processed prospective NMC811 manufacturing intensity:

`{prospective_mfg_min:.6f} kg CO2e/kWh_pack`

Maximum processed prospective NMC811 manufacturing intensity:

`{prospective_mfg_max:.6f} kg CO2e/kWh_pack`

Minimum-value pathway/year:

`{min_row["pathway"]} / {int(min_row["calendar_year"])}`

## Separation

Minimum frozen prospective NMC811 CI divided by primary break-even CI:

`{primary_separation_ratio:.3f}×`

Minimum frozen prospective NMC811 CI divided by extreme-stress break-even CI:

`{extreme_separation_ratio:.3f}×`

Required manufacturing-intensity reduction relative to the already-lowest
frozen prospective NMC811 value:

Primary-domain threshold:

`{100.0 * primary_required_reduction_fraction:.6f}%`

Extreme-stress threshold:

`{100.0 * extreme_required_reduction_fraction:.6f}%`

## Energy-Penalty Magnitudes

Maximum non-extreme 10-ms incremental battery-side penalty:

`{primary_r10_max_penalty_pct:.6f}%`

Maximum non-extreme 1-s incremental battery-side penalty:

`{primary_r1s_max_penalty_pct:.6f}%`

Maximum extreme/conditional physics-translated penalty:

`{extreme_max_penalty_pct:.6f}%`

## Scientific Interpretation

The strongest conservative break-even test uses the extreme/conditional
physics-translated operational saving rather than the primary-domain
saving.

Even under that stress domain, the minimum manufacturing intensity already
present in the frozen prospective NMC811 evidence remains above the
manufacturing-intensity threshold required for replacement to break even.

This result does not prove that all conceivable future battery production
systems must satisfy the same condition.

It shows that the robust-continuation result is not dependent solely on the
central degradation-energy penalty within the frozen evidence architecture.

## Prohibited Claims

Break-even time calculated: NO

Replacement optimization performed: NO

Xu 2022 values introduced: NO

Recycling credits introduced: NO

New degradation fit introduced: NO
"""


REPORT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_FILE.write_text(
    report,
    encoding="utf-8",
)


# ============================================================
# 14. DISPLAY
# ============================================================

print(
    f"\nNominal pack energy: "
    f"{nominal_pack_kwh:.6f} kWh"
)


print("\nPRIMARY DOMAIN")

print(
    "Maximum operational saving:",
    primary_max_operational_saving,
    "kg CO2e",
)

print(
    "Break-even manufacturing CI:",
    primary_break_even_mfg_ci,
    "kg CO2e/kWh_pack",
)


print("\nEXTREME / CONDITIONAL STRESS DOMAIN")

print(
    "Maximum operational saving:",
    extreme_max_operational_saving,
    "kg CO2e",
)

print(
    "Break-even manufacturing CI:",
    extreme_break_even_mfg_ci,
    "kg CO2e/kWh_pack",
)


print("\nFROZEN NMC811 PROSPECTIVE MANUFACTURING")

print(
    "Minimum CI:",
    prospective_mfg_min,
    "kg CO2e/kWh_pack",
)

print(
    "Maximum CI:",
    prospective_mfg_max,
    "kg CO2e/kWh_pack",
)

print(
    "Minimum CI pathway/year:",
    min_row["pathway"],
    int(min_row["calendar_year"]),
)


print("\nSEPARATION RATIOS")

print(
    "Primary:",
    primary_separation_ratio,
    "x",
)

print(
    "Extreme:",
    extreme_separation_ratio,
    "x",
)


print("\nENERGY PENALTY MAGNITUDES")

print(
    "10-ms non-extreme max:",
    primary_r10_max_penalty_pct,
    "%",
)

print(
    "1-s non-extreme max:",
    primary_r1s_max_penalty_pct,
    "%",
)

print(
    "Extreme max:",
    extreme_max_penalty_pct,
    "%",
)


print("\n" + "=" * 78)

print(
    "P16-Q0 PASS — MAGNITUDE & MANUFACTURING "
    "BREAK-EVEN DEFENSE COMPLETED"
)

print(
    "PRIMARY BREAK-EVEN MANUFACTURING INTENSITY: CALCULATED"
)

print(
    "EXTREME-STRESS BREAK-EVEN MANUFACTURING INTENSITY: CALCULATED"
)

print(
    "MINIMUM FROZEN NMC811 PROSPECTIVE CI: COMPARED"
)

print(
    "FROZEN NMC811 ENVELOPE DOMINATES EXTREME THRESHOLD: YES"
)

print(
    "NEW DEGRADATION MODEL: NONE"
)

print(
    "XU / RECYCLING VALUES INTRODUCED: NONE"
)

print(
    "BREAK-EVEN TIME: NOT CALCULATED"
)

print(
    "REPLACEMENT OPTIMIZATION: NONE"
)

print("=" * 78)