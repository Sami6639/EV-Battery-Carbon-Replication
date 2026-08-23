from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[2]

P146C = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
)

P15R_MANIFEST = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_accounting_engine_manifest.json"
)

P15R_REPORT = (
    ROOT
    / "docs"
    / "P15R_ACCOUNTING_ENGINE_REPORT.md"
)

SPEC = (
    ROOT
    / "docs"
    / "IMPLEMENTATION_SPEC.md"
)

JSON_OUT = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_PREREGISTRATION.json"
)

REPORT_OUT = (
    ROOT
    / "docs"
    / "P15Q_Q1_NOVELTY_PREREGISTRATION_REPORT.md"
)

PROPOSAL_OUT = (
    ROOT
    / "docs"
    / "P15Q_IMPLEMENTATION_SPEC_ADDENDUM_PROPOSAL.md"
)


def sha256(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


print("=" * 78)
print("P15Q-A — Q1 NOVELTY & IDENTIFICATION-LEVERAGE PREREGISTRATION")
print("=" * 78)


# ============================================================
# 1. REQUIRED AUTHORITY
# ============================================================

for path in [
    P146C,
    P15R_MANIFEST,
    P15R_REPORT,
    SPEC,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P15Q-A FAIL — missing required file: {path}"
        )


with P146C.open(encoding="utf-8") as f:
    prereg = json.load(f)

with P15R_MANIFEST.open(encoding="utf-8") as f:
    p15r = json.load(f)


assert (
    prereg["architecture_roles"]["primary"]
    == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
)

assert (
    prereg["research_questions"]["revised_primary_status"]
    == "REVISED PRIMARY RQ — LOCKED"
)

assert (
    p15r["final_status"]
    == "P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS"
)

assert p15r["delta_g_calculated"] is False
assert p15r["decision_bounds_calculated"] is False
assert p15r["carbon_classification_produced"] is False


# ============================================================
# 2. Q1 CONTRIBUTION ARCHITECTURE
# ============================================================

contributions = {

    "C1_DUAL_STATE_DECISION_ATLAS": {
        "statement": (
            "Condition the EV battery carbon decision on an "
            "empirically admissible joint capacity–pulse-resistance "
            "state rather than battery age or capacity SOH alone."
        ),

        "scientific_object": (
            "capacity_retention × relative_resistance "
            "→ conditional carbon-decision class"
        ),

        "primary_axes": [
            "reconstructed_capacity_retention",
            "R10_relative_resistance",
        ],

        "alternative_physical_specification":
            "R1s_relative_resistance",

        "headline_interpolation":
            "PROHIBITED",

        "population_prevalence_interpretation":
            "PROHIBITED",
    },


    "C2_TRAJECTORY_FREE_IDENTIFICATION": {
        "statement": (
            "Bound the lifecycle-GHG contrast between immediate "
            "replacement and continued first-life use without "
            "imposing an empirically unsupported real-world "
            "degradation trajectory."
        ),

        "estimand":
            "DeltaG = G_R - G_C",

        "classification_labels": [
            "ROBUST CONTINUE",
            "ROBUST REPLACE",
            "CARBON DECISION INDETERMINATE",
        ],

        "identification_type":
            "MECHANISTIC SET IDENTIFICATION",

        "probability_interpretation":
            "NONE",
    },


    "C3_IDENTIFICATION_BOTTLENECK": {
        "statement": (
            "Identify which unresolved physical or model-evidence "
            "family prevents the replacement-versus-continuation "
            "carbon decision from being sign-identified."
        ),

        "primary_name":
            "IDENTIFICATION LEVERAGE",

        "alternative_name":
            "EVIDENCE-RESOLUTION LEVERAGE",

        "value_of_information_claim":
            "PROHIBITED",

        "causal_importance_claim":
            "PROHIBITED",

        "additive_variance_decomposition_claim":
            "PROHIBITED",
    },
}


# ============================================================
# 3. DUAL-STATE NECESSITY TEST
# ============================================================

dual_state_test = {

    "name":
        "MATCHED_CAPACITY_RESISTANCE_DECISION_TEST",

    "purpose": (
        "Test whether capacity retention alone is sufficient "
        "to identify the carbon decision."
    ),

    "capacity_matching_rule": {
        "type":
            "SYMMETRIC_FIXED_WINDOW",

        "half_width":
            0.025,

        "unit":
            "capacity_retention_fraction",

        "post_result_widening":
            False,
    },

    "minimum_support": {
        "admissible_state_rows":
            3,

        "distinct_resistance_states":
            2,

        "insufficient_support_label":
            "INSUFFICIENT DUAL-STATE SUPPORT",
    },

    "discordance_label":
        "DUAL-STATE DECISION DISCORDANCE",

    "discordance_definition": (
        "Within the same admissible capacity window and matched "
        "exogenous context, supported resistance states produce "
        "different primary carbon classifications."
    ),

    "non_discordance_claim_limit": (
        "Absence of observed discordance does not prove that "
        "capacity-only SOH is universally sufficient."
    ),

    "no_smoothing_for_headline":
        True,
}


# ============================================================
# 4. IDENTIFICATION LEVERAGE
# ============================================================

identification_leverage = {

    "scope": (
        "Evaluated within a fixed matched exogenous context z. "
        "It does not pool incompatible grid, manufacturing, "
        "vehicle-life or geography contexts."
    ),

    "full_width":
        "W_full = upper_DeltaG - lower_DeltaG",

    "resolved_width":
        "W_resolved_j = width after family j is fixed to its "
        "pre-registered reference/supportable setting while all "
        "other admissible families remain unresolved",

    "absolute_leverage":
        "L_j = W_full - W_resolved_j",

    "normalized_leverage":
        "Lnorm_j = L_j / W_full when W_full > 0",

    "sign_recovery": (
        "YES when the full identified interval is "
        "CARBON DECISION INDETERMINATE and resolution of family j "
        "produces a sign-robust interval."
    ),

    "primary_evidence_families": [

        "FUTURE_STATE_ENDPOINT_TREATMENT",

        "CURRENT_RESISTANCE_ENVELOPE",

        "PACK_LOSS_SHARE",
    ],

    "structural_physical_family": [
        "RESISTANCE_TIMESCALE_R10_VS_R1s",
    ],

    "reference_resolution_rule": (
        "Use only the already pre-registered primary/reference "
        "setting. No family is fixed to a value selected after "
        "observing DeltaG."
    ),

    "ranking_rule": (
        "Rank families by absolute leverage L_j. "
        "The ranking is descriptive of interval narrowing only."
    ),

    "nonadditivity_rule": (
        "L_j values are not additive and must not be interpreted "
        "as variance shares or probabilities."
    ),
}


# ============================================================
# 5. PAIRWISE IDENTIFICATION INTERACTION
# ============================================================

pairwise_rule = {

    "status":
        "SECONDARY_INTERACTION_DIAGNOSTIC",

    "trigger": (
        "Run only when the full interval is indeterminate and "
        "no single pre-registered evidence family recovers a "
        "robust sign."
    ),

    "selection_rule": (
        "Select the three families with the largest single-family "
        "absolute leverage L_j, then evaluate their three pairwise "
        "combinations."
    ),

    "post_result_family_substitution":
        "PROHIBITED",

    "claim_limit": (
        "Pairwise results identify interacting evidence bottlenecks; "
        "they are not causal interaction effects."
    ),
}


# ============================================================
# 6. CONTEXT MODULATION — SEPARATE FROM IDENTIFICATION LEVERAGE
# ============================================================

context_modulation = {

    "principle": (
        "Exogenous decision context z is analytically distinct "
        "from uncertainty inside Theta(z)."
    ),

    "context_families": [

        "DECISION_CALENDAR_YEAR",

        "CURRENT_VEHICLE_AGE",

        "ANNUAL_MILEAGE",

        "MOBILITY_REQUIREMENT",

        "VEHICLE_SURVIVAL",

        "CHARGING_EFFICIENCY",

        "GRID_PATHWAY",

        "GRID_GEOGRAPHY",

        "BATTERY_MANUFACTURING_PATHWAY",

        "BATTERY_MANUFACTURING_TEMPORAL_TREATMENT",
    ],

    "analysis_name":
        "CONTEXT MODULATION",

    "identification_leverage_label":
        "PROHIBITED_FOR_EXOGENOUS_CONTEXT_SHIFTS",

    "purpose": (
        "Quantify how matched exogenous contexts shift interval "
        "location, width or carbon classification without "
        "misrepresenting context variation as evidence resolution."
    ),
}


# ============================================================
# 7. Q1 RESULT ARCHITECTURE
# ============================================================

result_architecture = {

    "R1_PRIMARY_DECISION_ATLAS": {
        "output": (
            "Observed/admissible dual-state map of primary "
            "carbon classification."
        ),

        "headline_eligible":
            True,
    },

    "R2_DUAL_STATE_NECESSITY": {
        "output": (
            "Matched-capacity test of whether resistance state "
            "materially changes the decision."
        ),

        "headline_eligible":
            True,
    },

    "R3_IDENTIFICATION_BOTTLENECK": {
        "output": (
            "Identification-leverage ranking for indeterminate "
            "or wide identified intervals."
        ),

        "headline_eligible":
            True,
    },

    "R4_CONTEXT_MODULATION": {
        "output": (
            "Effect of residual service and temporal carbon "
            "context on interval location/width/classification."
        ),

        "headline_eligible":
            True,
    },

    "R5_STRUCTURAL_ROBUSTNESS": {
        "output": (
            "R1s, mileage, mobility, survival, charging, regional "
            "grid and manufacturing structural checks."
        ),

        "headline_eligible":
            False,
    },

    "R6_EXTREME_STRESS": {
        "output":
            "Separately labelled extreme/conditional stress tests.",

        "headline_eligible":
            False,
    },
}


# ============================================================
# 8. REVIEWER-DEFENSE RULES
# ============================================================

reviewer_defense = [

    "DO_NOT_CLAIM_PARTIAL_IDENTIFICATION_WAS_INVENTED",

    "DO_NOT_CLAIM_FIRST_EVER_CARBON_OPTIMAL_RETIREMENT",

    "DO_NOT_CALL_IDENTIFICATION_LEVERAGE_VALUE_OF_INFORMATION",

    "DO_NOT_TREAT_P12_STATE_SPACE_AS_FLEET_PREVALENCE",

    "DO_NOT_INTERPOLATE_OR_SMOOTH_UNSUPPORTED_PHYSICAL_STATES_FOR_HEADLINE_RESULTS",

    "DO_NOT_SELECT_UNCERTAINTY_BOUNDS_AFTER_OBSERVING_CLASSIFICATIONS",

    "DO_NOT_NARROW_INDETERMINATE_INTERVALS_FOR_PUBLICATION_APPEAL",

    "DO_NOT_MERGE_R10_AND_R1s",

    "DO_NOT_TREAT_TECHNICAL_REPLACEMENT_AS_CARBON_BENEFIT",

    "DO_NOT_TREAT_CONTEXT_VARIATION_AS_IDENTIFICATION_LEVERAGE",

    "REPORT_INDETERMINACY_AS_A_SCIENTIFIC_RESULT_WHEN_REQUIRED",
]


# ============================================================
# 9. POST-P16R PUBLICATION-STRENGTH REVIEW
# ============================================================

publication_strength_review = {

    "scientific_validity_independent_of_publication_strength":
        True,

    "mandatory_review_before_manuscript":
        True,

    "questions": [

        "Does the dual-state map reveal non-trivial robust or "
        "indeterminate structure?",

        "Does matched-capacity resistance variation materially "
        "change interval width or classification?",

        "Can indeterminate decisions be traced to specific "
        "evidence bottlenecks rather than an undifferentiated "
        "mega-envelope?",

        "Do temporal grid/manufacturing and residual-service "
        "contexts change the mechanism in an interpretable way?",

        "Are the results more informative than a conventional "
        "one-at-a-time sensitivity analysis?",

        "Can the contribution be stated without priority or "
        "first-ever claims?",
    ],

    "if_results_are_mostly_indeterminate": (
        "Do not narrow bounds post hoc. Evaluate whether "
        "identification-bottleneck results provide a sufficiently "
        "strong evidence-gap contribution before manuscript drafting."
    ),
}


# ============================================================
# 10. MACHINE-READABLE PREREGISTRATION
# ============================================================

payload = {

    "schema_version":
        "1.0.0",

    "stage":
        "P15Q",

    "status":
        "Q1 NOVELTY STRENGTHENING PREREGISTERED — PROPOSAL",

    "revised_primary_rq":
        prereg["research_questions"]["revised_primary"],

    "architecture":
        prereg["architecture_status"],

    "contributions":
        contributions,

    "dual_state_necessity_test":
        dual_state_test,

    "identification_leverage":
        identification_leverage,

    "pairwise_identification_interaction":
        pairwise_rule,

    "context_modulation":
        context_modulation,

    "result_architecture":
        result_architecture,

    "reviewer_defense_rules":
        reviewer_defense,

    "publication_strength_review":
        publication_strength_review,

    "prohibited_outputs_before_p16r": [

        "DeltaG",

        "lower_DeltaG",

        "upper_DeltaG",

        "ROBUST CONTINUE",

        "ROBUST REPLACE",

        "CARBON DECISION INDETERMINATE",

        "IDENTIFICATION LEVERAGE RESULT",

        "DUAL-STATE DECISION DISCORDANCE RESULT",
    ],

    "p15r_status":
        p15r["final_status"],

    "implementation_spec_pre_p15q": {

        "sha256":
            sha256(SPEC),

        "bytes":
            SPEC.stat().st_size,
    },

    "numerical_analysis_performed":
        False,
}


JSON_OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

JSON_OUT.write_text(
    json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 11. REPORT
# ============================================================

report = """# P15Q — Q1 Novelty & Identification-Leverage Preregistration

## Status

`Q1 NOVELTY STRENGTHENING PREREGISTERED — PROPOSAL`

## Purpose

P15Q strengthens the revised EV-battery carbon-decision study before P16R results are observed.

No lifecycle decision result is calculated in P15Q.

## Contribution 1 — Dual-State Carbon-Decision Atlas

The primary decision state is joint usable-capacity retention and pulse-resistance state.

The study will test whether batteries with comparable capacity retention but different supported resistance states can yield different carbon-decision classifications.

Capacity SOH alone is therefore treated as an empirical question rather than assumed sufficient.

## Contribution 2 — Trajectory-Free Mechanistic Set Identification

The study bounds the immediate-replacement versus continuation lifecycle-GHG contrast without imposing an unsupported real-world degradation trajectory.

Primary labels remain:

- ROBUST CONTINUE
- ROBUST REPLACE
- CARBON DECISION INDETERMINATE

## Contribution 3 — Identification Bottleneck

For wide or indeterminate intervals, the study will quantify which unresolved physical/model-evidence family most constrains sign identification.

The metric is identification leverage, not causal importance, probability, variance decomposition, or value of information.

## Identification-Leverage Metric

For a fixed exogenous context:

W_full = upper_DeltaG - lower_DeltaG

For evidence family j:

W_resolved_j = identified width after fixing family j to its pre-registered reference/supportable setting while retaining all other admissible uncertainty.

L_j = W_full - W_resolved_j

Normalized leverage is reported only when W_full > 0.

Leverage values are not additive.

## Context Modulation

Grid pathway, manufacturing pathway, mileage, survival, charging, geography and other exogenous contexts are evaluated separately from identification leverage.

They may shift the interval or classification, but are not described as evidence-resolution leverage.

## Dual-State Necessity Test

Capacity states are compared within a fixed ±0.025 capacity-retention window.

Headline results use observed/admissible state support only.

No outcome-driven widening, smoothing or unsupported state interpolation is allowed.

## Pairwise Evidence Bottlenecks

Pairwise evidence-resolution analysis is secondary and runs only if:

1. the full interval is indeterminate; and
2. no single pre-registered evidence family recovers a robust sign.

The top three single-family leverage dimensions define the only eligible pairwise comparisons.

## Reviewer-Defense Rules

The study will not claim invention of partial identification, first-ever carbon-optimal battery retirement, population prevalence, or probability of replacement.

Identification leverage will not be called value of information.

Indeterminate regions will not be narrowed after results merely to improve publication appearance.

## Publication-Strength Gate

After P16R, but before manuscript drafting, a separate publication-strength review will determine whether the empirical results provide:

- meaningful dual-state decision structure;
- evidence that resistance adds information beyond capacity;
- identifiable evidence bottlenecks;
- interpretable temporal/residual-service mechanisms; and
- a contribution stronger than conventional sensitivity analysis.

Scientific validity is not conditional on producing a preferred result.

## Numerical Disclosures

Lifecycle decision bounds calculated: `NO`

Carbon classifications calculated: `NO`

Identification leverage calculated: `NO`

Dual-state discordance calculated: `NO`

P16R started: `NO`

## Next Step

This document is a proposal only.

A short P15Q-B integrity/change-control gate must formally lock the preregistration before P16R begins.
"""


REPORT_OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_OUT.write_text(
    report,
    encoding="utf-8",
)


# ============================================================
# 12. IMPLEMENTATION-SPEC ADDENDUM PROPOSAL
# ============================================================

proposal = """# P15Q — Proposed Q1 Novelty Strengthening Addendum

**Status:** PROPOSED ONLY — NOT YET AUTHORITATIVE

This proposal adds three pre-result scientific analyses to P16R:

1. dual capacity–resistance carbon-decision atlas;
2. matched-capacity resistance necessity test;
3. identification-leverage / evidence-bottleneck analysis.

It also distinguishes identification leverage from exogenous context modulation.

No existing P14.6C research question, estimand, sign convention, policy symmetry rule, evidence tier, or prohibited claim is weakened.

No numerical P16R result has been inspected.

The proposal may become authoritative only after a separate P15Q-B integrity gate.
"""


PROPOSAL_OUT.write_text(
    proposal,
    encoding="utf-8",
)


# ============================================================
# 13. FINAL
# ============================================================

print("\nCreated:")

print(
    JSON_OUT.relative_to(ROOT)
)

print(
    REPORT_OUT.relative_to(ROOT)
)

print(
    PROPOSAL_OUT.relative_to(ROOT)
)

print("\n" + "=" * 78)

print(
    "P15Q-A PASS — Q1 NOVELTY STRENGTHENING PROPOSAL PREREGISTERED"
)

print(
    "DUAL-STATE NECESSITY TEST: PRE-REGISTERED"
)

print(
    "IDENTIFICATION LEVERAGE: PRE-REGISTERED"
)

print(
    "CONTEXT MODULATION: SEPARATED FROM IDENTIFICATION LEVERAGE"
)

print(
    "PAIRWISE BOTTLENECK RULE: PRE-REGISTERED"
)

print(
    "IMPLEMENTATION_SPEC: NOT MODIFIED"
)

print(
    "NO P16R RESULT CALCULATED"
)

print("=" * 78)