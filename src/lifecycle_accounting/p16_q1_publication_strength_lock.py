from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

P16 = (
    ROOT
    / "results/intermediate"
    / "p16_final_scientific_manifest.json"
)

Q0 = (
    ROOT
    / "data/metadata"
    / "P16_Q0_MAGNITUDE_BREAK_EVEN_DEFENSE.json"
)

LOCK = (
    ROOT
    / "data/metadata"
    / "P16_Q1_PUBLICATION_STRENGTH_LOCK.json"
)

REPORT = (
    ROOT
    / "docs"
    / "P16_Q1_PUBLICATION_STRENGTH_REPORT.md"
)

LOG = (
    ROOT
    / "docs"
    / "RESEARCH_DECISION_LOG.md"
)


print("=" * 78)
print("P16-Q1 — WOS-Q1 PUBLICATION-STRENGTH FINAL GATE")
print("=" * 78)


with P16.open(encoding="utf-8") as f:
    p16 = json.load(f)

with Q0.open(encoding="utf-8") as f:
    q0 = json.load(f)


assert (
    p16["final_status"]
    ==
    "P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — "
    "READY FOR Q1 PUBLICATION-STRENGTH GATE"
)

assert (
    q0["final_status"]
    ==
    "MAGNITUDE AND MANUFACTURING BREAK-EVEN DEFENSE — PASS"
)

assert (
    p16["primary"]["classification"]
    == "ROBUST CONTINUE"
)

assert (
    p16["temporal"]["classification"]
    == "ROBUST CONTINUE"
)

assert (
    p16["structural_robustness"][
        "r1s_classification_reversals"
    ]
    == 0
)

assert (
    p16["structural_robustness"][
        "lrmer_classification_reversals"
    ]
    == 0
)

assert (
    p16["structural_robustness"][
        "extreme_classification_reversals"
    ]
    == 0
)

assert (
    p16["structural_robustness"][
        "mobility_range_infeasible_rows"
    ]
    == 0
)

assert (
    q0[
        "frozen_envelope_dominates_extreme_threshold"
    ]
    is True
)

assert (
    q0["primary_separation_ratio"] > 1
)

assert (
    q0["extreme_separation_ratio"] > 1
)


status = (
    "WOS-Q1 PUBLICATION POTENTIAL VERY STRONG — "
    "FORMALLY LOCKED WITH BOUNDED CLAIMS"
)


receipt = {
    "stage": "P16-Q1",

    "final_status": status,

    "publication_potential":
        "VERY STRONG",

    "headline_contribution": (
        "TRAJECTORY_FREE_STATE_CONDITIONED_SAME_BEV_"
        "CONTINUE_VS_IMMEDIATE_REPLACEMENT_"
        "LIFECYCLE_GHG_SET_IDENTIFICATION"
    ),

    "headline_mechanism": (
        "REPLACEMENT_MANUFACTURING_BURDEN_DOMINATES_"
        "ADMISSIBLE_DEGRADATION_RELATED_OPERATIONAL_SAVING"
    ),

    "supporting_contributions": [
        "DUAL_CAPACITY_RESISTANCE_STATE_ARCHITECTURE",
        "IDENTIFICATION_LEVERAGE",
        "R10_R1S_STRUCTURAL_ROBUSTNESS",
        "TEMPORAL_CONTEXT_MODULATION",
        "REGIONAL_AND_LRMER_ROBUSTNESS",
    ],

    "primary_break_even_mfg_ci":
        q0[
            "primary_break_even_mfg_ci_kgco2e_per_kwh"
        ],

    "extreme_break_even_mfg_ci":
        q0[
            "extreme_break_even_mfg_ci_kgco2e_per_kwh"
        ],

    "minimum_frozen_nmc811_ci":
        q0[
            "minimum_frozen_nmc811_prospective_ci"
        ],

    "primary_separation_ratio":
        q0["primary_separation_ratio"],

    "extreme_separation_ratio":
        q0["extreme_separation_ratio"],

    "remaining_limitations": [
        "AGED_STATE_POWER_CAPABILITY_NOT_STATE_RESOLVED",
        "XU_2022_NOT_NUMERICALLY_IMPLEMENTED_IN_P16",
        "RECYCLING_CREDIT_SENSITIVITY_NOT_NUMERICALLY_IMPLEMENTED",
    ],

    "prohibited_claims": [
        "FIRST_DEGRADATION_AWARE_EV_LCA",
        "FIRST_CARBON_OPTIMAL_BATTERY_RETIREMENT",
        "RESISTANCE_CHANGES_CARBON_CLASSIFICATION",
        "FULL_ENGINEERING_REPLACEMENT_RECOMMENDATION",
        "UNIVERSAL_RECYCLING_INDEPENDENCE",
        "TIME_TO_STATE_INFERENCE",
    ],

    "manuscript_drafting_authorized":
        True,

    "manuscript_drafting_requires_user_writing_criteria_first":
        True,

    "acceptance_guaranteed":
        False,
}


LOCK.parent.mkdir(
    parents=True,
    exist_ok=True,
)

LOCK.write_text(
    json.dumps(
        receipt,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


report = f"""# P16-Q1 — WoS-Q1 Publication-Strength Gate

## Final Status

`{status}`

## Publication Potential

`VERY STRONG`

This is a publication-potential assessment, not a guarantee of journal
acceptance.

## Headline Scientific Contribution

The manuscript will be positioned around trajectory-free,
state-conditioned lifecycle-GHG set identification for the same BEV's
traction battery:

continued first-life use versus immediate battery replacement.

The framework conditions the decision on empirically supported battery
health states without imposing an unsupported real-world degradation
trajectory.

## Headline Mechanism

The central mechanism is the asymmetry between replacement-battery
manufacturing burden and the admissible degradation-related operational
carbon saving.

Primary manufacturing break-even intensity:

`{q0["primary_break_even_mfg_ci_kgco2e_per_kwh"]:.9f} kg CO2e/kWh_pack`

Extreme physical-stress break-even intensity:

`{q0["extreme_break_even_mfg_ci_kgco2e_per_kwh"]:.9f} kg CO2e/kWh_pack`

Minimum frozen prospective NMC811 manufacturing intensity:

`{q0["minimum_frozen_nmc811_prospective_ci"]:.6f} kg CO2e/kWh_pack`

Primary separation ratio:

`{q0["primary_separation_ratio"]:.3f}×`

Extreme-stress separation ratio:

`{q0["extreme_separation_ratio"]:.3f}×`

## Supporting Contributions

Dual capacity-resistance state architecture remains scientifically
important but is not positioned as a classification-changing headline
result.

Identification leverage is retained as supporting uncertainty-mechanism
analysis.

Temporal grid/manufacturing decarbonization, R10/R1s, regional grid,
Cambium-2023 LRMER, mobility, mileage, survival, charging, vehicle-age
and extreme-state analyses provide the robustness architecture.

## Remaining Bounded Limitations

Aged-state power capability remains not state-resolved.

Xu 2022 was not numerically implemented in P16.

Recycling-credit sensitivity was not numerically implemented in P16.

These limitations must be stated explicitly and must not be represented
as completed analyses.

## Prohibited Priority / Overreach Claims

The manuscript must not claim:

- first degradation-aware EV LCA;
- first carbon-optimal battery retirement study;
- that resistance changes the carbon classification;
- a complete engineering replacement recommendation;
- universal independence from recycling assumptions;
- any time-to-state relationship.

## Literature Positioning Anchors

Yang et al. (2018):
10.1038/s41467-018-04826-0

Etxandi-Santolaya et al. (2024):
10.1016/j.heliyon.2024.e26066

Wang et al. (2026):
10.1016/j.est.2026.122148

Xu et al. (2022):
10.1016/j.resconrec.2022.106606

Kim et al. (2026):
10.1016/j.etran.2026.100627

Hanna et al. (2025):
10.1021/acs.est.4c13838

Du et al. (2022):
10.1021/acs.est.2c05755

## Manuscript Authorization

Scientific analysis is sufficient to move to manuscript architecture.

No manuscript prose may be drafted until the user's manuscript-writing
criteria are explicitly discussed and locked.
"""


REPORT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT.write_text(
    report,
    encoding="utf-8",
)


heading = (
    "## P16-Q1 — WoS-Q1 Publication-Strength Gate"
)

if heading not in LOG.read_text(
    encoding="utf-8"
):

    with LOG.open(
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            f"""

{heading}

Decision: {status}

Publication potential: VERY STRONG.

Headline contribution: trajectory-free, state-conditioned, same-BEV
continued-first-life versus immediate-replacement lifecycle-GHG set
identification.

Headline mechanism: replacement manufacturing burden dominates the
admissible degradation-related operational-carbon saving.

Dual-state and identification-leverage analyses remain supporting
contributions.

Aged-state power capability remains not state-resolved.

Xu 2022 and recycling-credit sensitivities were not numerically
implemented and must not be represented as completed.

Manuscript drafting is scientifically authorized, but user-specific
writing criteria must be discussed before any manuscript prose is
written.
"""
        )


print("\n" + "=" * 78)

print(
    "WOS-Q1 PUBLICATION POTENTIAL VERY STRONG — "
    "FORMALLY LOCKED WITH BOUNDED CLAIMS"
)

print(
    "HEADLINE NOVELTY: TRAJECTORY-FREE STATE-CONDITIONED "
    "SAME-BEV CARBON DECISION"
)

print(
    "HEADLINE MECHANISM: MANUFACTURING BURDEN VS "
    "OPERATIONAL-SAVING ASYMMETRY"
)

print(
    f"PRIMARY BREAK-EVEN SEPARATION: "
    f"{q0['primary_separation_ratio']:.1f}x"
)

print(
    f"EXTREME-STRESS BREAK-EVEN SEPARATION: "
    f"{q0['extreme_separation_ratio']:.1f}x"
)

print(
    "DUAL-STATE / IDENTIFICATION LEVERAGE: SUPPORTING CONTRIBUTIONS"
)

print(
    "AGED-STATE POWER LIMITATION: RETAINED"
)

print(
    "XU / RECYCLING NON-IMPLEMENTATION: DISCLOSED"
)

print(
    "MANUSCRIPT SCIENTIFICALLY AUTHORIZED: YES"
)

print(
    "MANUSCRIPT WRITING BEFORE USER CRITERIA DISCUSSION: NO"
)

print("=" * 78)