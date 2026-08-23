from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CLASS_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c2_primary_carbon_classification.parquet"
)

D1_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d1_dual_state_necessity.parquet"
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

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b2_resistance_leverage.parquet"
)


print("=" * 78)
print("P16R-D2B2 — CURRENT-RESISTANCE ENVELOPE LEVERAGE")
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


# ============================================================
# 2. LOAD
# ============================================================

df = pd.read_parquet(CLASS_FILE)
d1 = pd.read_parquet(D1_FILE)

assert not df.empty
assert not d1.empty

CAPACITY_HALF_WINDOW = 0.025


# ============================================================
# 3. HOLD NON-RESISTANCE DIMENSIONS CONSTANT
# ============================================================

group_cols = [
    "context_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "topology_id",
]


# ============================================================
# 4. D1 AUDIT LOOKUP
# ============================================================

d1_lookup = d1.set_index(
    [
        "context_id",
        "current_state_key",
    ]
)


# ============================================================
# 5. MATCHED-CAPACITY RESISTANCE SETS
# ============================================================

rows = []

for _, group in df.groupby(
    group_cols,
    sort=False,
    dropna=False,
):

    g = group.reset_index(drop=True)

    capacities = (
        g["current_capacity_retention"]
        .to_numpy(dtype=float)
    )

    for _, anchor in g.iterrows():

        anchor_capacity = float(
            anchor["current_capacity_retention"]
        )

        mask = (
            np.abs(
                capacities - anchor_capacity
            )
            <= CAPACITY_HALF_WINDOW
        )

        peers = g.loc[mask].copy()

        peer_n = len(peers)

        distinct_resistance_n = (
            peers[
                "current_relative_resistance"
            ]
            .nunique()
        )

        support_ok = (
            peer_n >= 3
            and distinct_resistance_n >= 2
        )

        # ----------------------------------------------------
        # Verify exact agreement with D1 support construction
        # ----------------------------------------------------

        audit_key = (
            anchor["context_id"],
            anchor["current_state_key"],
        )

        if audit_key not in d1_lookup.index:
            raise RuntimeError(
                "P16R-D2B2 FAIL — D1 audit row missing."
            )

        audit_row = d1_lookup.loc[
            audit_key
        ]

        if bool(
            audit_row[
                "dual_state_support_sufficient"
            ]
        ) != support_ok:
            raise RuntimeError(
                "P16R-D2B2 FAIL — D1 support mismatch."
            )

        if int(
            audit_row["matched_state_n"]
        ) != peer_n:
            raise RuntimeError(
                "P16R-D2B2 FAIL — matched-state count mismatch."
            )

        if int(
            audit_row[
                "distinct_resistance_state_n"
            ]
        ) != distinct_resistance_n:
            raise RuntimeError(
                "P16R-D2B2 FAIL — resistance-count mismatch."
            )


        # ====================================================
        # 6. INSUFFICIENT SUPPORT
        # ====================================================

        if not support_ok:

            rows.append(
                {
                    "context_id":
                        anchor["context_id"],

                    "current_state_key":
                        anchor["current_state_key"],

                    "anchor_capacity_retention":
                        anchor[
                            "current_capacity_retention"
                        ],

                    "anchor_relative_resistance":
                        anchor[
                            "current_relative_resistance"
                        ],

                    "cell_resistance_share":
                        anchor[
                            "cell_resistance_share"
                        ],

                    "fresh_usable_window_fraction":
                        anchor[
                            "fresh_usable_window_fraction"
                        ],

                    "topology_id":
                        anchor["topology_id"],

                    "capacity_match_half_width":
                        CAPACITY_HALF_WINDOW,

                    "matched_state_n":
                        peer_n,

                    "distinct_resistance_state_n":
                        distinct_resistance_n,

                    "support_sufficient":
                        False,

                    "W_full_kgco2e":
                        None,

                    "W_resolved_max_kgco2e":
                        None,

                    "W_resolved_min_kgco2e":
                        None,

                    "L_guaranteed_kgco2e":
                        None,

                    "L_potential_kgco2e":
                        None,

                    "Lnorm_guaranteed":
                        None,

                    "Lnorm_potential":
                        None,

                    "full_union_classification":
                        None,

                    "member_classification_n":
                        None,

                    "classification_discordance":
                        False,

                    "guaranteed_sign_recovery":
                        False,

                    "potential_sign_recovery":
                        False,

                    "evidence_family":
                        "CURRENT_RESISTANCE_ENVELOPE",

                    "analysis_unit":
                        "D1_MATCHED_CAPACITY_PEER_SET",

                    "cross_family_ranking_allowed":
                        False,

                    "value_of_information_claim":
                        False,
                }
            )

            continue


        # ====================================================
        # 7. FULL RESISTANCE-UNRESOLVED UNION
        #
        # Union across all supported resistance members in the
        # fixed ±0.025 capacity window.
        # ====================================================

        full_lower = float(
            peers[
                "lower_DeltaG_kgco2e"
            ].min()
        )

        full_upper = float(
            peers[
                "upper_DeltaG_kgco2e"
            ].max()
        )

        W_full = (
            full_upper - full_lower
        )


        # ====================================================
        # 8. RESOLVE RESISTANCE TO EACH ADMISSIBLE MEMBER
        #
        # Each member retains its own endpoint-treatment
        # interval.
        # ====================================================

        member_widths = (
            peers[
                "identified_width_kgco2e"
            ]
            .to_numpy(dtype=float)
        )

        W_resolved_max = float(
            member_widths.max()
        )

        W_resolved_min = float(
            member_widths.min()
        )

        L_guaranteed = (
            W_full - W_resolved_max
        )

        L_potential = (
            W_full - W_resolved_min
        )


        # Floating-point protection only.
        if (
            L_guaranteed < 0
            and abs(L_guaranteed) <= 1e-12
        ):
            L_guaranteed = 0.0

        if (
            L_potential < 0
            and abs(L_potential) <= 1e-12
        ):
            L_potential = 0.0


        if L_guaranteed < -1e-12:
            raise RuntimeError(
                "P16R-D2B2 FAIL — "
                "negative guaranteed leverage."
            )

        if L_potential < -1e-12:
            raise RuntimeError(
                "P16R-D2B2 FAIL — "
                "negative potential leverage."
            )


        # ====================================================
        # 9. MEMBER CLASSIFICATIONS
        # ====================================================

        member_labels = (
            peers[
                "carbon_classification"
            ]
            .tolist()
        )

        member_classification_n = len(
            set(member_labels)
        )

        classification_discordance = (
            member_classification_n > 1
        )


        # ====================================================
        # 10. FULL UNION CLASSIFICATION
        # ====================================================

        if full_lower > 0:

            full_union_classification = (
                "ROBUST CONTINUE"
            )

        elif full_upper < 0:

            full_union_classification = (
                "ROBUST REPLACE"
            )

        else:

            full_union_classification = (
                "CARBON DECISION INDETERMINATE"
            )


        # ====================================================
        # 11. SIGN RECOVERY
        #
        # Only meaningful if unresolved full union is
        # indeterminate.
        # ====================================================

        guaranteed_sign_recovery = False
        potential_sign_recovery = False

        if (
            full_union_classification
            == "CARBON DECISION INDETERMINATE"
        ):

            robust_labels = [
                x
                for x in member_labels
                if x
                != "CARBON DECISION INDETERMINATE"
            ]

            potential_sign_recovery = (
                len(robust_labels) > 0
            )

            guaranteed_sign_recovery = (
                len(set(member_labels)) == 1
                and member_labels[0]
                != "CARBON DECISION INDETERMINATE"
            )


        # ====================================================
        # 12. OUTPUT ROW
        # ====================================================

        rows.append(
            {
                "context_id":
                    anchor["context_id"],

                "current_state_key":
                    anchor["current_state_key"],

                "anchor_capacity_retention":
                    anchor[
                        "current_capacity_retention"
                    ],

                "anchor_relative_resistance":
                    anchor[
                        "current_relative_resistance"
                    ],

                "cell_resistance_share":
                    anchor[
                        "cell_resistance_share"
                    ],

                "fresh_usable_window_fraction":
                    anchor[
                        "fresh_usable_window_fraction"
                    ],

                "topology_id":
                    anchor["topology_id"],

                "capacity_match_half_width":
                    CAPACITY_HALF_WINDOW,

                "matched_state_n":
                    peer_n,

                "distinct_resistance_state_n":
                    distinct_resistance_n,

                "matched_resistance_min":
                    float(
                        peers[
                            "current_relative_resistance"
                        ].min()
                    ),

                "matched_resistance_max":
                    float(
                        peers[
                            "current_relative_resistance"
                        ].max()
                    ),

                "support_sufficient":
                    True,

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

                "full_union_classification":
                    full_union_classification,

                "member_classification_n":
                    member_classification_n,

                "classification_discordance":
                    classification_discordance,

                "guaranteed_sign_recovery":
                    guaranteed_sign_recovery,

                "potential_sign_recovery":
                    potential_sign_recovery,

                "evidence_family":
                    "CURRENT_RESISTANCE_ENVELOPE",

                "analysis_unit":
                    "D1_MATCHED_CAPACITY_PEER_SET",

                "cross_family_ranking_allowed":
                    False,

                "value_of_information_claim":
                    False,
            }
        )


out = pd.DataFrame(rows)


# ============================================================
# 13. HARD CONTRACT
# ============================================================

assert len(out) == len(d1)

assert (
    out["capacity_match_half_width"]
    == 0.025
).all()

assert not out[
    "cross_family_ranking_allowed"
].any()

assert not out[
    "value_of_information_claim"
].any()


supported = out.loc[
    out["support_sufficient"]
].copy()

assert len(supported) == 2916

assert (
    supported[
        "L_guaranteed_kgco2e"
    ]
    <= supported[
        "L_potential_kgco2e"
    ]
).all()


# ============================================================
# 14. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

out.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 15. SUMMARY
# ============================================================

print(
    f"\nResistance-leverage rows: "
    f"{len(out):,}"
)

print(
    "Supported rows:",
    len(supported),
)

print(
    "Insufficient-support rows:",
    int(
        (
            ~out["support_sufficient"]
        ).sum()
    ),
)


print("\nFull-union width range:")

print(
    float(
        supported[
            "W_full_kgco2e"
        ].min()
    ),
    "to",
    float(
        supported[
            "W_full_kgco2e"
        ].max()
    ),
    "kg CO2e",
)


print("\nGuaranteed resistance leverage range:")

print(
    float(
        supported[
            "L_guaranteed_kgco2e"
        ].min()
    ),
    "to",
    float(
        supported[
            "L_guaranteed_kgco2e"
        ].max()
    ),
    "kg CO2e",
)


print("\nPotential resistance leverage range:")

print(
    float(
        supported[
            "L_potential_kgco2e"
        ].min()
    ),
    "to",
    float(
        supported[
            "L_potential_kgco2e"
        ].max()
    ),
    "kg CO2e",
)


print(
    "\nClassification-discordance rows:"
)

print(
    int(
        supported[
            "classification_discordance"
        ].sum()
    )
)


print(
    "Guaranteed sign-recovery rows:"
)

print(
    int(
        supported[
            "guaranteed_sign_recovery"
        ].sum()
    )
)


print(
    "Potential sign-recovery rows:"
)

print(
    int(
        supported[
            "potential_sign_recovery"
        ].sum()
    )
)


print("\nFull-union classifications:")

print(
    supported[
        "full_union_classification"
    ]
    .value_counts()
    .to_string()
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D2B2 PASS — RESISTANCE-ENVELOPE "
    "IDENTIFICATION LEVERAGE CALCULATED"
)

print(
    "FIXED ±0.025 MATCHED-CAPACITY UNIT PRESERVED"
)

print(
    "D1 SUPPORT COUNTS REPRODUCED EXACTLY"
)

print(
    "REFERENCE-FREE GUARANTEED/POTENTIAL LEVERAGE: APPLIED"
)

print(
    "CROSS-FAMILY ADDITIVE RANKING: NOT PERFORMED"
)

print(
    "VALUE-OF-INFORMATION CLAIM: NOT MADE"
)

print("=" * 78)