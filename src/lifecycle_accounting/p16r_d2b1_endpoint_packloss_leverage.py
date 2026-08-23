from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

B2_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_b2_primary_context_deltag.parquet"
)

BOUNDS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c1_primary_identified_bounds.parquet"
)

D2A_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_D2A_REFERENCE_FREE_LEVERAGE_LOCK.json"
)

D2B0_AUDIT = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_D2B0_LEVERAGE_ANALYSIS_UNIT_AUDIT.json"
)

OUTPUT_ENDPOINT = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b1_endpoint_leverage.parquet"
)

OUTPUT_PACKLOSS = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b1_packloss_leverage.parquet"
)


print("=" * 78)
print("P16R-D2B1 — ENDPOINT + PACK-LOSS IDENTIFICATION LEVERAGE")
print("=" * 78)


# ============================================================
# 1. VERIFY LOCKS
# ============================================================

with D2A_LOCK.open(encoding="utf-8") as f:
    d2a = json.load(f)

with D2B0_AUDIT.open(encoding="utf-8") as f:
    unit_audit = json.load(f)

assert (
    d2a["final_status"]
    ==
    "REFERENCE-FREE IDENTIFICATION-LEVERAGE RULE FORMALLY LOCKED — PASS"
)

assert (
    unit_audit["final_status"]
    ==
    "IDENTIFICATION-LEVERAGE ANALYSIS UNITS AUDITED — PASS"
)

assert (
    d2a["identification_leverage_calculated"]
    is False
)


# ============================================================
# 2. LOAD
# ============================================================

b2 = pd.read_parquet(B2_FILE)
bounds = pd.read_parquet(BOUNDS_FILE)

assert not b2.empty
assert not bounds.empty


# ============================================================
# 3. ENDPOINT-TREATMENT FAMILY
#
# Unit:
# context × current_state_key
#
# Full interval:
# four admissible theta_R × theta_C pairs.
#
# Resolving the ENTIRE endpoint-pair family to one member
# leaves one DeltaG value and therefore width = 0.
#
# This is mathematically valid but is explicitly labelled
# MECHANICAL_COMPLETE_FAMILY_RESOLUTION so it is not
# overinterpreted as a deep scientific bottleneck.
# ============================================================

endpoint_group = [
    "context_id",
    "current_state_key",
]

endpoint_counts = (
    b2.groupby(endpoint_group)
    .size()
)

assert (endpoint_counts == 4).all()


endpoint_full = (
    b2.groupby(
        endpoint_group,
        as_index=False,
    )
    .agg(
        lower_DeltaG=(
            "DeltaG_kgco2e",
            "min",
        ),
        upper_DeltaG=(
            "DeltaG_kgco2e",
            "max",
        ),
    )
)

endpoint_full["W_full_kgco2e"] = (
    endpoint_full["upper_DeltaG"]
    - endpoint_full["lower_DeltaG"]
)

endpoint_full["W_resolved_max_kgco2e"] = 0.0
endpoint_full["W_resolved_min_kgco2e"] = 0.0

endpoint_full["L_guaranteed_kgco2e"] = (
    endpoint_full["W_full_kgco2e"]
)

endpoint_full["L_potential_kgco2e"] = (
    endpoint_full["W_full_kgco2e"]
)

endpoint_full["Lnorm_guaranteed"] = (
    endpoint_full["L_guaranteed_kgco2e"]
    / endpoint_full["W_full_kgco2e"]
)

endpoint_full["Lnorm_potential"] = (
    endpoint_full["L_potential_kgco2e"]
    / endpoint_full["W_full_kgco2e"]
)

endpoint_full["evidence_family"] = (
    "FUTURE_STATE_ENDPOINT_TREATMENT"
)

endpoint_full["analysis_unit"] = (
    "context_id × current_state_key"
)

endpoint_full["interpretation"] = (
    "MECHANICAL_COMPLETE_FAMILY_RESOLUTION"
)

endpoint_full["cross_family_ranking_allowed"] = False
endpoint_full["value_of_information_claim"] = False


# ============================================================
# 4. PACK-LOSS SHARE FAMILY
#
# Unit:
# context × same physical state with share removed
#
# Full interval is the union of the three share-specific
# intervals.
#
# Resolving share to member v leaves that member's
# endpoint-treatment interval.
# ============================================================

bounds = bounds.copy()

bounds["physical_state_without_share"] = (
    bounds["current_degradation_state_id"].astype(str)
    + "|"
    + bounds["topology_id"].astype(str)
    + "|window="
    + bounds["fresh_usable_window_fraction"].astype(str)
)

pack_group = [
    "context_id",
    "physical_state_without_share",
]


# Must have exactly 0.50 / 0.75 / 1.00
share_counts = (
    bounds.groupby(pack_group)[
        "cell_resistance_share"
    ]
    .nunique()
)

assert (share_counts == 3).all()


pack_rows = []

for group_key, group in bounds.groupby(
    pack_group,
    sort=False,
):

    g = group.copy()

    full_lower = float(
        g["lower_DeltaG_kgco2e"].min()
    )

    full_upper = float(
        g["upper_DeltaG_kgco2e"].max()
    )

    W_full = (
        full_upper
        - full_lower
    )

    member_widths = (
        g[
            [
                "cell_resistance_share",
                "identified_width_kgco2e",
                "lower_DeltaG_kgco2e",
                "upper_DeltaG_kgco2e",
            ]
        ]
        .sort_values(
            "cell_resistance_share"
        )
    )

    assert set(
        member_widths[
            "cell_resistance_share"
        ].tolist()
    ) == {
        0.5,
        0.75,
        1.0,
    }

    W_resolved_max = float(
        member_widths[
            "identified_width_kgco2e"
        ].max()
    )

    W_resolved_min = float(
        member_widths[
            "identified_width_kgco2e"
        ].min()
    )

    L_guaranteed = (
        W_full
        - W_resolved_max
    )

    L_potential = (
        W_full
        - W_resolved_min
    )

    # Floating-point protection only.
    if L_guaranteed < 0 and abs(L_guaranteed) <= 1e-12:
        L_guaranteed = 0.0

    if L_potential < 0 and abs(L_potential) <= 1e-12:
        L_potential = 0.0

    if L_guaranteed < -1e-12:
        raise RuntimeError(
            "P16R-D2B1 FAIL — negative guaranteed leverage."
        )

    if L_potential < -1e-12:
        raise RuntimeError(
            "P16R-D2B1 FAIL — negative potential leverage."
        )

    classifications = []

    for row in g.itertuples(index=False):

        if row.lower_DeltaG_kgco2e > 0:
            label = "ROBUST CONTINUE"

        elif row.upper_DeltaG_kgco2e < 0:
            label = "ROBUST REPLACE"

        else:
            label = "CARBON DECISION INDETERMINATE"

        classifications.append(label)

    full_classification = (
        "ROBUST CONTINUE"
        if full_lower > 0
        else (
            "ROBUST REPLACE"
            if full_upper < 0
            else "CARBON DECISION INDETERMINATE"
        )
    )

    guaranteed_sign_recovery = False
    potential_sign_recovery = False

    # Sign recovery only applies if the FULL union is indeterminate.
    if (
        full_classification
        == "CARBON DECISION INDETERMINATE"
    ):

        robust_member_labels = [
            x
            for x in classifications
            if x != "CARBON DECISION INDETERMINATE"
        ]

        potential_sign_recovery = (
            len(robust_member_labels) > 0
        )

        guaranteed_sign_recovery = (
            len(set(classifications)) == 1
            and classifications[0]
            != "CARBON DECISION INDETERMINATE"
        )

    pack_rows.append(
        {
            "context_id":
                group_key[0],

            "physical_state_without_share":
                group_key[1],

            "W_full_kgco2e":
                W_full,

            "W_resolved_max_kgco2e":
                W_resolved_max,

            "W_resolved_min_kgco2e":
                W_resolved_min,

            "L_guaranteed_kgco2e":
                L_guaranteed,

            "L_potential_kgco2e":
                L_potential,

            "Lnorm_guaranteed":
                (
                    L_guaranteed / W_full
                    if W_full > 0
                    else None
                ),

            "Lnorm_potential":
                (
                    L_potential / W_full
                    if W_full > 0
                    else None
                ),

            "full_classification":
                full_classification,

            "guaranteed_sign_recovery":
                guaranteed_sign_recovery,

            "potential_sign_recovery":
                potential_sign_recovery,

            "member_classification_n":
                len(set(classifications)),

            "evidence_family":
                "PACK_LOSS_SHARE",

            "analysis_unit":
                (
                    "context_id × "
                    "physical_state_without_share"
                ),

            "cross_family_ranking_allowed":
                False,

            "value_of_information_claim":
                False,
        }
    )


pack = pd.DataFrame(pack_rows)


# ============================================================
# 5. HARD REFERENCE-FREE CONTRACT
# ============================================================

assert (
    endpoint_full[
        "L_guaranteed_kgco2e"
    ]
    <= endpoint_full[
        "L_potential_kgco2e"
    ]
).all()

assert (
    pack[
        "L_guaranteed_kgco2e"
    ]
    <= pack[
        "L_potential_kgco2e"
    ]
).all()

assert not endpoint_full[
    "cross_family_ranking_allowed"
].any()

assert not pack[
    "cross_family_ranking_allowed"
].any()

assert not endpoint_full[
    "value_of_information_claim"
].any()

assert not pack[
    "value_of_information_claim"
].any()


# ============================================================
# 6. SAVE
# ============================================================

OUTPUT_ENDPOINT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

endpoint_full.to_parquet(
    OUTPUT_ENDPOINT,
    index=False,
)

pack.to_parquet(
    OUTPUT_PACKLOSS,
    index=False,
)


# ============================================================
# 7. SUMMARY
# ============================================================

print(
    "\nENDPOINT-TREATMENT FAMILY"
)

print(
    "Rows:",
    len(endpoint_full),
)

print(
    "W_full range:",
    float(
        endpoint_full[
            "W_full_kgco2e"
        ].min()
    ),
    "to",
    float(
        endpoint_full[
            "W_full_kgco2e"
        ].max()
    ),
)

print(
    "Guaranteed leverage range:",
    float(
        endpoint_full[
            "L_guaranteed_kgco2e"
        ].min()
    ),
    "to",
    float(
        endpoint_full[
            "L_guaranteed_kgco2e"
        ].max()
    ),
)

print(
    "Potential leverage range:",
    float(
        endpoint_full[
            "L_potential_kgco2e"
        ].min()
    ),
    "to",
    float(
        endpoint_full[
            "L_potential_kgco2e"
        ].max()
    ),
)


print(
    "\nPACK-LOSS-SHARE FAMILY"
)

print(
    "Rows:",
    len(pack),
)

print(
    "W_full range:",
    float(
        pack[
            "W_full_kgco2e"
        ].min()
    ),
    "to",
    float(
        pack[
            "W_full_kgco2e"
        ].max()
    ),
)

print(
    "Guaranteed leverage range:",
    float(
        pack[
            "L_guaranteed_kgco2e"
        ].min()
    ),
    "to",
    float(
        pack[
            "L_guaranteed_kgco2e"
        ].max()
    ),
)

print(
    "Potential leverage range:",
    float(
        pack[
            "L_potential_kgco2e"
        ].min()
    ),
    "to",
    float(
        pack[
            "L_potential_kgco2e"
        ].max()
    ),
)

print(
    "Pack-loss classification reversals:",
    int(
        (
            pack[
                "member_classification_n"
            ] > 1
        ).sum()
    ),
)

print(
    "Guaranteed sign recovery rows:",
    int(
        pack[
            "guaranteed_sign_recovery"
        ].sum()
    ),
)

print(
    "Potential sign recovery rows:",
    int(
        pack[
            "potential_sign_recovery"
        ].sum()
    ),
)


print("\nOutputs:")

print(
    OUTPUT_ENDPOINT.relative_to(ROOT)
)

print(
    OUTPUT_PACKLOSS.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D2B1 PASS — ENDPOINT AND PACK-LOSS "
    "IDENTIFICATION LEVERAGE CALCULATED"
)

print(
    "REFERENCE-FREE GUARANTEED/POTENTIAL LEVERAGE: APPLIED"
)

print(
    "ENDPOINT FAMILY COMPLETE RESOLUTION: "
    "EXPLICITLY LABELLED MECHANICAL"
)

print(
    "PACK-LOSS FAMILY ANALYSED ON SAME-PHYSICAL-STATE UNIT"
)

print(
    "CROSS-FAMILY ADDITIVE RANKING: NOT PERFORMED"
)

print(
    "VALUE-OF-INFORMATION CLAIM: NOT MADE"
)

print("=" * 78)