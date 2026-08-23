import pandas as pd
from pathlib import Path

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

KEY = [
    "degradation_state_id",
    "topology_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
]


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
print("P16R-D4A — R1S STRUCTURAL SUPPORT AUDIT")
print("=" * 78)


print("\nR10")
print("raw rows:", len(r10))
print("state keys:", r10[KEY].drop_duplicates().shape[0])

r10_pairs = (
    r10.groupby(KEY)["drive_cycle"]
    .nunique()
)

print("complete UDDS/HWFET pairs:", int((r10_pairs == 2).sum()))
print("incomplete pairs:", int((r10_pairs != 2).sum()))


print("\nR1s")
print("raw rows:", len(r1s))
print("state keys:", r1s[KEY].drop_duplicates().shape[0])

r1s_pairs = (
    r1s.groupby(KEY)["drive_cycle"]
    .nunique()
)

print("complete UDDS/HWFET pairs:", int((r1s_pairs == 2).sum()))
print("incomplete pairs:", int((r1s_pairs != 2).sum()))


if r1s.empty:
    raise RuntimeError(
        "P16R-D4A FAIL — no admissible 1-s states."
    )


print("\nR1s capacity-retention range:")
print(
    float(r1s["capacity_retention"].min()),
    "to",
    float(r1s["capacity_retention"].max()),
)

print("\nR1s relative-resistance range:")
print(
    float(r1s["relative_resistance"].min()),
    "to",
    float(r1s["relative_resistance"].max()),
)

print("\nR1s physical-envelope classes:")
print(
    sorted(
        r1s["physical_envelope_class"]
        .unique()
        .tolist()
    )
)


r10_keys = set(
    map(
        tuple,
        r10[KEY].drop_duplicates().to_numpy(),
    )
)

r1s_keys = set(
    map(
        tuple,
        r1s[KEY].drop_duplicates().to_numpy(),
    )
)


print("\nR10/R1s state-key alignment:")
print("common keys:", len(r10_keys & r1s_keys))
print("R10-only keys:", len(r10_keys - r1s_keys))
print("R1s-only keys:", len(r1s_keys - r10_keys))


full_alignment = (
    r10_keys == r1s_keys
    and (r1s_pairs == 2).all()
)


print("\n" + "=" * 78)

if full_alignment:

    print(
        "P16R-D4A SUPPORT AUDIT PASS — "
        "R1S STRUCTURAL COMPARISON FULLY ALIGNED"
    )

else:

    print(
        "P16R-D4A SUPPORT AUDIT WITH BOUNDS — "
        "R1S COMPARISON REQUIRES COMMON-SUPPORT DOMAIN"
    )

print("NO NEW DELTAG CALCULATED")
print("NO NEW CARBON CLASSIFICATION PRODUCED")
print("=" * 78)