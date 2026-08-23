from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "data"
    / "processed"
    / "p13_incremental_energy_penalty.parquet"
)


print("=" * 78)
print("P16R-D4A3 — CANONICAL R10/R1S PHYSICAL-STATE PAIRING AUDIT")
print("=" * 78)


df = pd.read_parquet(FILE)


VALID_STATUS = {
    "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
    "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
}


def select(spec, classes):

    return df.loc[
        (df["resistance_specification"] == spec)
        & (~df["conditional_extreme"])
        & (
            df["physical_envelope_class"]
            .isin(classes)
        )
        & (
            df["valid_domain_status"]
            .isin(VALID_STATUS)
        )
        & (
            df["drive_cycle"]
            .isin(["UDDS", "HWFET"])
        )
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


assert len(r10) == 1134
assert len(r1s) == 1134


# ============================================================
# 1. CANONICAL UNDERLYING PHYSICAL STATE ID
#
# Remove only the resistance-timescale token.
#
# Examples:
#
# LUH_10ms_00 -> LUH_00
# LUH_1s_00   -> LUH_00
#
# SCHREIBER_COMMUTER_CU0_10ms
# -> SCHREIBER_COMMUTER_CU0
#
# No fuzzy matching is allowed.
# ============================================================

def canonical_state_id(value):

    s = str(value)

    s = re.sub(
        r"_10ms(?=_|$)",
        "",
        s,
        flags=re.IGNORECASE,
    )

    s = re.sub(
        r"_1s(?=_|$)",
        "",
        s,
        flags=re.IGNORECASE,
    )

    return s


r10["canonical_physical_state_id"] = (
    r10["degradation_state_id"]
    .map(canonical_state_id)
)

r1s["canonical_physical_state_id"] = (
    r1s["degradation_state_id"]
    .map(canonical_state_id)
)


# ============================================================
# 2. NORMALIZE EVIDENCE ROLE
#
# Primary 10-ms and alternative 1-s are the same underlying
# Luh physical-state role but different resistance timescales.
# ============================================================

ROLE_MAP = {

    "PRIMARY PHYSICAL SPECIFICATION":
        "CORE_PHYSICAL_STATE",

    "ALTERNATIVE 1-S SPECIFICATION":
        "CORE_PHYSICAL_STATE",

    "AUTOMOTIVE-COMPATIBLE ENVELOPE":
        "AUTOMOTIVE_COMPATIBLE_STATE",
}


r10["canonical_evidence_role"] = (
    r10["physical_envelope_class"]
    .map(ROLE_MAP)
)

r1s["canonical_evidence_role"] = (
    r1s["physical_envelope_class"]
    .map(ROLE_MAP)
)


if (
    r10["canonical_evidence_role"].isna().any()
    or r1s["canonical_evidence_role"].isna().any()
):
    raise RuntimeError(
        "P16R-D4A3 FAIL — unknown evidence role."
    )


# ============================================================
# 3. EXACT PAIRING KEY
# ============================================================

PAIR_KEY = [

    "canonical_physical_state_id",

    "canonical_evidence_role",

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


print("\nCanonical pairing-key duplicate rows:")

print("R10:", r10_dup)
print("R1s:", r1s_dup)


if r10_dup != 0 or r1s_dup != 0:

    print("\nExample R10 duplicates:")

    print(
        r10.loc[
            r10.duplicated(
                subset=PAIR_KEY,
                keep=False,
            ),
            PAIR_KEY
            + [
                "degradation_state_id",
                "source_id",
                "capacity_retention",
                "exposure_days",
            ],
        ]
        .head(20)
        .to_string(index=False)
    )

    raise RuntimeError(
        "P16R-D4A3 WITH BOUNDS — canonical "
        "physical-state key is not unique."
    )


# ============================================================
# 4. PREPARE ONE-TO-ONE MERGE
# ============================================================

a = r10[
    PAIR_KEY
    + [
        "degradation_state_id",
        "source_id",
        "exposure_days",
        "capacity_retention",
        "relative_resistance",
        "aged_battery_side_kwh_per_km",
        "valid_domain_status",
    ]
].rename(
    columns={
        "degradation_state_id":
            "r10_state_id",

        "source_id":
            "r10_source_id",

        "exposure_days":
            "r10_exposure_days",

        "capacity_retention":
            "r10_capacity_retention",

        "relative_resistance":
            "r10_relative_resistance",

        "aged_battery_side_kwh_per_km":
            "r10_aged_l2",

        "valid_domain_status":
            "r10_domain_status",
    }
)


b = r1s[
    PAIR_KEY
    + [
        "degradation_state_id",
        "source_id",
        "exposure_days",
        "capacity_retention",
        "relative_resistance",
        "aged_battery_side_kwh_per_km",
        "valid_domain_status",
    ]
].rename(
    columns={
        "degradation_state_id":
            "r1s_state_id",

        "source_id":
            "r1s_source_id",

        "exposure_days":
            "r1s_exposure_days",

        "capacity_retention":
            "r1s_capacity_retention",

        "relative_resistance":
            "r1s_relative_resistance",

        "aged_battery_side_kwh_per_km":
            "r1s_aged_l2",

        "valid_domain_status":
            "r1s_domain_status",
    }
)


merged = a.merge(
    b,
    on=PAIR_KEY,
    how="outer",
    indicator=True,
    validate="one_to_one",
)


# ============================================================
# 5. ALIGNMENT COUNTS
# ============================================================

counts = (
    merged["_merge"]
    .value_counts()
)


common_rows = int(
    counts.get("both", 0)
)

r10_only_rows = int(
    counts.get("left_only", 0)
)

r1s_only_rows = int(
    counts.get("right_only", 0)
)


print("\nCanonical physical row alignment:")

print(
    "common rows:",
    common_rows,
)

print(
    "R10-only rows:",
    r10_only_rows,
)

print(
    "R1s-only rows:",
    r1s_only_rows,
)


paired = merged.loc[
    merged["_merge"] == "both"
].copy()


# ============================================================
# 6. SCIENTIFIC IDENTITY CHECKS
# ============================================================

source_mismatch = int(
    (
        paired["r10_source_id"]
        != paired["r1s_source_id"]
    ).sum()
)


domain_mismatch = int(
    (
        paired["r10_domain_status"]
        != paired["r1s_domain_status"]
    ).sum()
)


capacity_difference = (
    paired["r10_capacity_retention"]
    - paired["r1s_capacity_retention"]
).abs()


max_capacity_difference = float(
    capacity_difference.max()
)


# Exposure:
# both NaN is valid;
# one NaN and one finite is not.
r10_nan = (
    paired["r10_exposure_days"]
    .isna()
)

r1s_nan = (
    paired["r1s_exposure_days"]
    .isna()
)

exposure_missingness_mismatch = int(
    (r10_nan != r1s_nan).sum()
)


finite_exposure = (
    ~r10_nan
    & ~r1s_nan
)

if finite_exposure.any():

    max_exposure_difference = float(
        (
            paired.loc[
                finite_exposure,
                "r10_exposure_days",
            ]
            -
            paired.loc[
                finite_exposure,
                "r1s_exposure_days",
            ]
        )
        .abs()
        .max()
    )

else:

    max_exposure_difference = 0.0


print("\nScientific identity checks:")

print(
    "source mismatches:",
    source_mismatch,
)

print(
    "domain-status mismatches:",
    domain_mismatch,
)

print(
    "max capacity difference:",
    f"{max_capacity_difference:.15e}",
)

print(
    "exposure missingness mismatches:",
    exposure_missingness_mismatch,
)

print(
    "max finite exposure difference:",
    f"{max_exposure_difference:.15e}",
)


# ============================================================
# 7. STATE-LEVEL ALIGNMENT
# ============================================================

STATE_KEY = [
    "canonical_physical_state_id",
    "canonical_evidence_role",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
]


cycle_counts = (
    paired.groupby(
        STATE_KEY
    )["drive_cycle"]
    .nunique()
)


complete_state_pairs = int(
    (cycle_counts == 2).sum()
)

incomplete_state_pairs = int(
    (cycle_counts != 2).sum()
)


print("\nCanonical physical state alignment:")

print(
    "complete paired states:",
    complete_state_pairs,
)

print(
    "incomplete paired states:",
    incomplete_state_pairs,
)


# ============================================================
# 8. R10 / R1S DIFFERENCES ARE ALLOWED ONLY IN RESISTANCE
#    AND RESULTING ENERGY PENALTY
# ============================================================

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


paired["aged_l2_difference_r1s_minus_r10"] = (
    paired["r1s_aged_l2"]
    - paired["r10_aged_l2"]
)


print("\nR1s - R10 aged-L2 difference range:")

print(
    float(
        paired[
            "aged_l2_difference_r1s_minus_r10"
        ].min()
    ),
    "to",
    float(
        paired[
            "aged_l2_difference_r1s_minus_r10"
        ].max()
    ),
    "kWh/km",
)


# ============================================================
# 9. HARD COMMON-SUPPORT GATE
# ============================================================

full_alignment = (

    common_rows == 1134

    and r10_only_rows == 0

    and r1s_only_rows == 0

    and source_mismatch == 0

    and domain_mismatch == 0

    and max_capacity_difference <= 1e-12

    and exposure_missingness_mismatch == 0

    and max_exposure_difference <= 1e-12

    and complete_state_pairs == 567

    and incomplete_state_pairs == 0
)


print("\n" + "=" * 78)


if full_alignment:

    print(
        "P16R-D4A3 PASS — R10/R1S CANONICAL "
        "PHYSICAL COMMON SUPPORT FULLY ALIGNED"
    )

    print(
        "COMMON ROWS: 1134/1134"
    )

    print(
        "COMMON PHYSICAL STATES: 567/567"
    )

    print(
        "TIMESCALE-SPECIFIC STATE IDs: "
        "CORRECTLY KEPT DISTINCT"
    )

else:

    print(
        "P16R-D4A3 WITH BOUNDS — "
        "CANONICAL COMMON SUPPORT INCOMPLETE"
    )


print(
    "NO FUZZY STATE MATCHING USED"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)