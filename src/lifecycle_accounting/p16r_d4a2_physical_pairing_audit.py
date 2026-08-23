from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)

df = pd.read_parquet(FILE)

VALID_STATUS = {
    "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
    "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
}


def select(spec, classes):

    return df.loc[
        (df["resistance_specification"] == spec)
        & (~df["conditional_extreme"])
        & (df["physical_envelope_class"].isin(classes))
        & (df["valid_domain_status"].isin(VALID_STATUS))
        & (df["drive_cycle"].isin(["UDDS", "HWFET"]))
    ].copy()


r10 = select(
    "10-ms",
    {
        "PRIMARY PHYSICAL SPECIFICATION",
        "AUTOMOTIVE-COMPATIBLE ENVELOPE",
    },
)

r1s = select(
    "1-s",
    {
        "ALTERNATIVE 1-S SPECIFICATION",
        "AUTOMOTIVE-COMPATIBLE ENVELOPE",
    },
)


print("=" * 78)
print("P16R-D4A2 — R10/R1S PHYSICAL PAIRING AUDIT")
print("=" * 78)


# ============================================================
# 1. SHOW ACTUAL ID STRUCTURE
# ============================================================

print("\nR10 example state IDs:")

print(
    r10[
        [
            "degradation_state_id",
            "exposure_days",
            "capacity_retention",
            "relative_resistance",
            "drive_cycle",
        ]
    ]
    .drop_duplicates()
    .head(12)
    .to_string(index=False)
)


print("\nR1s example state IDs:")

print(
    r1s[
        [
            "degradation_state_id",
            "exposure_days",
            "capacity_retention",
            "relative_resistance",
            "drive_cycle",
        ]
    ]
    .drop_duplicates()
    .head(12)
    .to_string(index=False)
)


# ============================================================
# 2. TEST PHYSICAL PAIRING WITHOUT SPEC-SPECIFIC STATE ID
#
# Capacity is included explicitly.
# Resistance is NOT included because that is the quantity
# whose timescale specification differs.
# ============================================================

PAIR_KEY = [
    "source_id",
    "exposure_days",
    "capacity_retention",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "drive_cycle",
]


r10_dup = int(
    r10.duplicated(
        subset=PAIR_KEY,
        keep=False,
    ).sum()
)

r1s_dup = int(
    r1s.duplicated(
        subset=PAIR_KEY,
        keep=False,
    ).sum()
)


print("\nPhysical pairing-key duplicate rows:")

print("R10:", r10_dup)
print("R1s:", r1s_dup)


# ============================================================
# 3. ONLY ATTEMPT ONE-TO-ONE MERGE IF KEY IS UNIQUE
# ============================================================

if r10_dup == 0 and r1s_dup == 0:

    a = r10[
        PAIR_KEY
        + [
            "degradation_state_id",
            "relative_resistance",
            "aged_battery_side_kwh_per_km",
        ]
    ].rename(
        columns={
            "degradation_state_id":
                "r10_state_id",

            "relative_resistance":
                "r10_relative_resistance",

            "aged_battery_side_kwh_per_km":
                "r10_aged_l2",
        }
    )

    b = r1s[
        PAIR_KEY
        + [
            "degradation_state_id",
            "relative_resistance",
            "aged_battery_side_kwh_per_km",
        ]
    ].rename(
        columns={
            "degradation_state_id":
                "r1s_state_id",

            "relative_resistance":
                "r1s_relative_resistance",

            "aged_battery_side_kwh_per_km":
                "r1s_aged_l2",
        }
    )

    merged = a.merge(
        b,
        on=PAIR_KEY,
        how="outer",
        indicator=True,
        validate="one_to_one",
    )

    counts = (
        merged["_merge"]
        .value_counts()
    )

    common = int(
        counts.get("both", 0)
    )

    r10_only = int(
        counts.get("left_only", 0)
    )

    r1s_only = int(
        counts.get("right_only", 0)
    )

    print("\nPhysical row alignment:")

    print("common rows:", common)
    print("R10-only rows:", r10_only)
    print("R1s-only rows:", r1s_only)

    paired = merged.loc[
        merged["_merge"] == "both"
    ].copy()

    state_pair_key = [
        "source_id",
        "exposure_days",
        "capacity_retention",
        "topology_id",
        "cell_resistance_share",
        "fresh_usable_window_fraction",
    ]

    cycle_counts = (
        paired.groupby(
            state_pair_key
        )["drive_cycle"]
        .nunique()
    )

    complete_state_pairs = int(
        (cycle_counts == 2).sum()
    )

    incomplete_state_pairs = int(
        (cycle_counts != 2).sum()
    )

    print("\nPhysical state alignment:")

    print(
        "complete paired states:",
        complete_state_pairs,
    )

    print(
        "incomplete paired states:",
        incomplete_state_pairs,
    )

    print("\nR10 relative-resistance range:")

    print(
        float(
            paired[
                "r10_relative_resistance"
            ].min()
        ),
        "to",
        float(
            paired[
                "r10_relative_resistance"
            ].max()
        ),
    )

    print("\nR1s relative-resistance range:")

    print(
        float(
            paired[
                "r1s_relative_resistance"
            ].min()
        ),
        "to",
        float(
            paired[
                "r1s_relative_resistance"
            ].max()
        ),
    )

    full_physical_alignment = (
        common == len(r10)
        and common == len(r1s)
        and r10_only == 0
        and r1s_only == 0
        and complete_state_pairs == 567
        and incomplete_state_pairs == 0
    )

else:

    full_physical_alignment = False

    print(
        "\nPAIRING KEY IS NOT UNIQUE — "
        "NO SCIENTIFIC ALIGNMENT INFERRED"
    )


# ============================================================
# 4. FINAL
# ============================================================

print("\n" + "=" * 78)

if full_physical_alignment:

    print(
        "P16R-D4A2 PASS — R10/R1S PHYSICAL "
        "COMMON-SUPPORT DOMAIN FULLY ALIGNED"
    )

    print(
        "PREVIOUS ZERO COMMON-ID RESULT: "
        "SPECIFICATION-SPECIFIC IDENTITY EFFECT"
    )

else:

    print(
        "P16R-D4A2 WITH BOUNDS — "
        "PHYSICAL COMMON SUPPORT NOT YET FULLY RESOLVED"
    )

print(
    "NO R10/R1S STATE ID EQUALITY ASSUMED"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)