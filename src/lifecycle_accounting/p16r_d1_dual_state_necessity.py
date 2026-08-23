from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_c2_primary_carbon_classification.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d1_dual_state_necessity.parquet"
)


print("=" * 78)
print("P16R-D1 — MATCHED-CAPACITY DUAL-STATE NECESSITY TEST")
print("=" * 78)


# ============================================================
# 1. LOAD PRIMARY CLASSIFICATION
# ============================================================

df = pd.read_parquet(INPUT_FILE)

assert not df.empty

required = {
    "context_id",
    "current_state_key",
    "current_capacity_retention",
    "current_relative_resistance",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "topology_id",
    "lower_DeltaG_kgco2e",
    "upper_DeltaG_kgco2e",
    "identified_width_kgco2e",
    "carbon_classification",
}

assert required <= set(df.columns)


# ============================================================
# 2. FIXED PRE-REGISTERED MATCHING RULE
# ============================================================

CAPACITY_HALF_WINDOW = 0.025

MIN_STATE_ROWS = 3
MIN_DISTINCT_RESISTANCE_STATES = 2


# ============================================================
# 3. HOLD NON-RESISTANCE ARCHITECTURE CONSTANT
#
# This prevents pack-loss share, usable-window assumption,
# topology or exogenous context from masquerading as a
# resistance-state effect.
# ============================================================

group_cols = [
    "context_id",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "topology_id",
]


rows = []


# ============================================================
# 4. MATCHED-CAPACITY PEER SETS
# ============================================================

for group_key, group in df.groupby(
    group_cols,
    sort=False,
    dropna=False,
):

    g = group.reset_index(drop=True)

    capacities = (
        g["current_capacity_retention"]
        .to_numpy(dtype=float)
    )

    resistances = (
        g["current_relative_resistance"]
        .to_numpy(dtype=float)
    )

    for i, anchor in g.iterrows():

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
            peers["current_relative_resistance"]
            .nunique()
        )

        support_ok = (
            peer_n >= MIN_STATE_ROWS
            and distinct_resistance_n
            >= MIN_DISTINCT_RESISTANCE_STATES
        )

        if support_ok:

            classification_n = (
                peers["carbon_classification"]
                .nunique()
            )

            classification_discordance = (
                classification_n > 1
            )

            if classification_discordance:
                support_label = (
                    "DUAL-STATE DECISION DISCORDANCE"
                )
            else:
                support_label = (
                    "NO OBSERVED DUAL-STATE DECISION DISCORDANCE"
                )

            resistance_min = float(
                peers[
                    "current_relative_resistance"
                ].min()
            )

            resistance_max = float(
                peers[
                    "current_relative_resistance"
                ].max()
            )

            lower_span = float(
                peers["lower_DeltaG_kgco2e"].max()
                - peers["lower_DeltaG_kgco2e"].min()
            )

            upper_span = float(
                peers["upper_DeltaG_kgco2e"].max()
                - peers["upper_DeltaG_kgco2e"].min()
            )

            width_span = float(
                peers["identified_width_kgco2e"].max()
                - peers["identified_width_kgco2e"].min()
            )

        else:

            classification_n = None
            classification_discordance = False

            support_label = (
                "INSUFFICIENT DUAL-STATE SUPPORT"
            )

            resistance_min = (
                float(
                    peers[
                        "current_relative_resistance"
                    ].min()
                )
                if peer_n > 0
                else None
            )

            resistance_max = (
                float(
                    peers[
                        "current_relative_resistance"
                    ].max()
                )
                if peer_n > 0
                else None
            )

            lower_span = None
            upper_span = None
            width_span = None


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

                "anchor_carbon_classification":
                    anchor[
                        "carbon_classification"
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

                "dual_state_support_sufficient":
                    support_ok,

                "matched_classification_n":
                    classification_n,

                "classification_discordance":
                    classification_discordance,

                "dual_state_test_label":
                    support_label,

                "matched_resistance_min":
                    resistance_min,

                "matched_resistance_max":
                    resistance_max,

                "matched_resistance_span":
                    (
                        resistance_max
                        - resistance_min
                        if (
                            resistance_min is not None
                            and resistance_max is not None
                        )
                        else None
                    ),

                "matched_lower_DeltaG_span_kgco2e":
                    lower_span,

                "matched_upper_DeltaG_span_kgco2e":
                    upper_span,

                "matched_identified_width_span_kgco2e":
                    width_span,

                "classification_threshold_added":
                    False,

                "post_result_window_widening":
                    False,

                "unsupported_state_smoothing":
                    False,

                "identification_leverage_calculated":
                    False,

                "context_modulation_completed":
                    False,

                "structural_robustness_completed":
                    False,
            }
        )


out = pd.DataFrame(rows)


# ============================================================
# 5. HARD PREREGISTRATION CHECKS
# ============================================================

assert (
    out["capacity_match_half_width"]
    == 0.025
).all()

assert not out[
    "post_result_window_widening"
].any()

assert not out[
    "unsupported_state_smoothing"
].any()

assert not out[
    "classification_threshold_added"
].any()


# ============================================================
# 6. NO OVERCLAIM
#
# Absence of discordance cannot be interpreted as proof
# that capacity-only SOH is universally sufficient.
# ============================================================

out["capacity_only_sufficiency_proven"] = False

assert not out[
    "capacity_only_sufficiency_proven"
].any()


# ============================================================
# 7. SAVE
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
# 8. SUMMARY
# ============================================================

print(
    f"\nDual-state test rows: "
    f"{len(out):,}"
)

print(
    "Supported matched-capacity rows:",
    int(
        out[
            "dual_state_support_sufficient"
        ].sum()
    ),
)

print(
    "Insufficient-support rows:",
    int(
        (
            ~out[
                "dual_state_support_sufficient"
            ]
        ).sum()
    ),
)


print("\nDual-state test labels:")

print(
    out[
        "dual_state_test_label"
    ]
    .value_counts()
    .to_string()
)


supported = out.loc[
    out[
        "dual_state_support_sufficient"
    ]
].copy()


if not supported.empty:

    print(
        "\nMatched resistance span range:"
    )

    print(
        float(
            supported[
                "matched_resistance_span"
            ].min()
        ),
        "to",
        float(
            supported[
                "matched_resistance_span"
            ].max()
        ),
    )

    print(
        "\nMatched lower_DeltaG span range:"
    )

    print(
        float(
            supported[
                "matched_lower_DeltaG_span_kgco2e"
            ].min()
        ),
        "to",
        float(
            supported[
                "matched_lower_DeltaG_span_kgco2e"
            ].max()
        ),
        "kg CO2e",
    )

    print(
        "\nMatched upper_DeltaG span range:"
    )

    print(
        float(
            supported[
                "matched_upper_DeltaG_span_kgco2e"
            ].min()
        ),
        "to",
        float(
            supported[
                "matched_upper_DeltaG_span_kgco2e"
            ].max()
        ),
        "kg CO2e",
    )

    print(
        "\nMatched identified-width span range:"
    )

    print(
        float(
            supported[
                "matched_identified_width_span_kgco2e"
            ].min()
        ),
        "to",
        float(
            supported[
                "matched_identified_width_span_kgco2e"
            ].max()
        ),
        "kg CO2e",
    )


print(
    "\nObserved classification discordance rows:"
)

print(
    int(
        out[
            "classification_discordance"
        ].sum()
    )
)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D1 PASS — MATCHED-CAPACITY DUAL-STATE TEST COMPLETED"
)

print(
    "FIXED ±0.025 CAPACITY WINDOW PRESERVED"
)

print(
    "NON-RESISTANCE ARCHITECTURE HELD CONSTANT"
)

print(
    "CLASSIFICATION DISCORDANCE TESTED"
)

print(
    "BOUND SHIFTS REPORTED DESCRIPTIVELY"
)

print(
    "ABSENCE OF DISCORDANCE DOES NOT PROVE "
    "CAPACITY-ONLY SUFFICIENCY"
)

print(
    "NO IDENTIFICATION LEVERAGE CALCULATED"
)

print("=" * 78)