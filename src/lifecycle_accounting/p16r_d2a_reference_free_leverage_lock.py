from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[2]

SPEC = ROOT / "docs" / "IMPLEMENTATION_SPEC.md"
LOG = ROOT / "docs" / "RESEARCH_DECISION_LOG.md"

P15Q_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_D2A_REFERENCE_FREE_LEVERAGE_LOCK.json"
)

REPORT = (
    ROOT
    / "docs"
    / "P16R_D2A_REFERENCE_FREE_LEVERAGE_REPORT.md"
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
print("P16R-D2A — REFERENCE-FREE IDENTIFICATION-LEVERAGE LOCK")
print("=" * 78)


# ============================================================
# 1. VERIFY Q1 LOCK
# ============================================================

with P15Q_LOCK.open(encoding="utf-8") as f:
    p15q = json.load(f)

assert (
    p15q["final_status"]
    ==
    "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS"
)

assert (
    p15q["numerical_p16r_result_calculated"]
    is False
)


# ============================================================
# 2. SCIENTIFIC REASON FOR CLARIFICATION
# ============================================================

reason = (
    "P15Q preregistered identification leverage before its numerical "
    "calculation, but did not designate a unique reference member for "
    "every multi-member evidence family. Selecting one member after "
    "observing primary DeltaG classifications would create avoidable "
    "post-result reference-selection risk."
)


# ============================================================
# 3. LOCK REFERENCE-FREE DEFINITIONS
# ============================================================

definitions = {

    "full_width":
        "W_full = upper_DeltaG - lower_DeltaG",

    "member_resolved_width":
        "W_jv = identified interval width after evidence family j "
        "is fixed to admissible member v while all other declared "
        "evidence uncertainty remains active",

    "member_leverage":
        "L_jv = W_full - W_jv",

    "guaranteed_leverage":
        "L_guaranteed_j = W_full - max_v(W_jv)",

    "potential_leverage":
        "L_potential_j = W_full - min_v(W_jv)",

    "normalized_guaranteed":
        "Lnorm_guaranteed_j = L_guaranteed_j / W_full "
        "when W_full > 0",

    "normalized_potential":
        "Lnorm_potential_j = L_potential_j / W_full "
        "when W_full > 0",
}


# ============================================================
# 4. INTERPRETATION RULES
# ============================================================

rules = {

    "reference_member_selected_post_result":
        False,

    "all_preregistered_members_evaluated":
        True,

    "leverage_additive":
        False,

    "probability_interpretation":
        False,

    "variance_share_interpretation":
        False,

    "causal_importance_interpretation":
        False,

    "value_of_information_label":
        False,

    "primary_language": [
        "GUARANTEED EVIDENCE-RESOLUTION LEVERAGE",
        "POTENTIAL EVIDENCE-RESOLUTION LEVERAGE",
    ],
}


# ============================================================
# 5. SIGN-RECOVERY RULE
# ============================================================

sign_recovery = {

    "guaranteed_sign_recovery":
        (
            "YES only if fixing family j to every admissible member "
            "produces a sign-robust interval with the same carbon "
            "classification."
        ),

    "potential_sign_recovery":
        (
            "YES if at least one admissible resolved member produces "
            "a sign-robust interval, but this is not a robust "
            "recommendation."
        ),
}


# ============================================================
# 6. FAMILIES
# ============================================================

families = {

    "FUTURE_STATE_ENDPOINT_TREATMENT": {
        "members":
            "all pre-registered admissible endpoint treatments",

        "single_reference":
            "NONE",
    },

    "CURRENT_RESISTANCE_ENVELOPE": {
        "members":
            "all supported matched-capacity resistance states",

        "single_reference":
            "NONE",
    },

    "PACK_LOSS_SHARE": {
        "members": [
            0.50,
            0.75,
            1.00,
        ],

        "single_reference":
            "NONE",
    },
}


# ============================================================
# 7. NO IDENTIFICATION RESULT YET
# ============================================================

receipt = {

    "stage":
        "P16R-D2A",

    "final_status":
        "REFERENCE-FREE IDENTIFICATION-LEVERAGE RULE FORMALLY LOCKED — PASS",

    "reason":
        reason,

    "definitions":
        definitions,

    "rules":
        rules,

    "sign_recovery":
        sign_recovery,

    "families":
        families,

    "identification_leverage_calculated":
        False,

    "new_carbon_classification_calculated":
        False,

    "post_result_reference_selection":
        False,
}


# ============================================================
# 8. APPEND-ONLY SPECIFICATION NOTE
# ============================================================

spec_before = SPEC.read_bytes()

spec_hash_before = hashlib.sha256(
    spec_before
).hexdigest()

spec_bytes_before = len(spec_before)


HEADING = (
    "# P16R-D2A — REFERENCE-FREE "
    "IDENTIFICATION-LEVERAGE CLARIFICATION"
)


ADDENDUM = """

---

# P16R-D2A — REFERENCE-FREE IDENTIFICATION-LEVERAGE CLARIFICATION

**Status:** FORMALLY LOCKED BEFORE IDENTIFICATION-LEVERAGE CALCULATION

P15Q preregistered identification-leverage analysis before P16R
leverage results but did not designate a unique reference member for
every multi-member evidence family.

Selecting a single reference member after observing primary carbon
classifications is prohibited.

Identification leverage is therefore implemented reference-free.

For full interval width:

W_full = upper_DeltaG - lower_DeltaG

For evidence family j and each admissible family member v:

W_jv = identified interval width after fixing j to v while all other
declared evidence uncertainty remains active.

L_jv = W_full - W_jv

Report:

L_guaranteed_j = W_full - max_v(W_jv)

and

L_potential_j = W_full - min_v(W_jv)

When W_full > 0, corresponding normalized values may also be reported.

No single post-result reference member is selected.

All pre-registered members are evaluated.

Identification leverage:

- is non-additive;
- is not a probability;
- is not a variance share;
- is not causal importance;
- is not value of information.

Primary terminology is:

- GUARANTEED EVIDENCE-RESOLUTION LEVERAGE
- POTENTIAL EVIDENCE-RESOLUTION LEVERAGE

Guaranteed sign recovery requires all admissible resolved members of
the evidence family to yield the same sign-robust classification.

Potential sign recovery means at least one resolved member yields a
sign-robust interval and must not be presented as a robust
recommendation.

No identification-leverage value is calculated in P16R-D2A.
"""


if HEADING in SPEC.read_text(encoding="utf-8"):
    raise RuntimeError(
        "P16R-D2A STOP — clarification already exists."
    )


with SPEC.open(
    "a",
    encoding="utf-8",
) as f:
    f.write(ADDENDUM)


raw = SPEC.read_bytes()

assert (
    hashlib.sha256(
        raw[:spec_bytes_before]
    ).hexdigest()
    ==
    spec_hash_before
)


receipt["implementation_spec"] = {
    "pre_sha256":
        spec_hash_before,

    "post_sha256":
        sha256(SPEC),

    "append_only_prefix_preserved":
        True,
}


# ============================================================
# 9. SAVE LOCK
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        receipt,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 10. DECISION LOG
# ============================================================

LOG_HEADING = (
    "## P16R-D2A — Reference-Free Identification Leverage"
)

if LOG_HEADING not in LOG.read_text(
    encoding="utf-8"
):

    with LOG.open(
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            """

## P16R-D2A — Reference-Free Identification Leverage

Stage: P16R-D2A — Identification-Leverage Clarification

Decision: REFERENCE-FREE IDENTIFICATION-LEVERAGE RULE FORMALLY LOCKED — PASS

Reason: P15Q did not define one unique reference member for every
multi-member evidence family. Selecting such a member after observing
primary carbon classifications would create post-result selection risk.

Scientific rule: all pre-registered family members will be evaluated.
Both guaranteed and potential evidence-resolution leverage will be
reported.

Identification leverage remains non-additive and is not probability,
variance contribution, causal importance, or value of information.

No identification-leverage value was calculated in this stage.
"""
        )


# ============================================================
# 11. REPORT
# ============================================================

report = """# P16R-D2A — Reference-Free Identification-Leverage Lock

## Final Status

`REFERENCE-FREE IDENTIFICATION-LEVERAGE RULE FORMALLY LOCKED — PASS`

## Reason

No unique reference member had been preregistered for every evidence
family.

A post-result reference choice is therefore prohibited.

## Locked Metrics

W_full = upper_DeltaG - lower_DeltaG

L_jv = W_full - W_jv

L_guaranteed_j = W_full - max_v(W_jv)

L_potential_j = W_full - min_v(W_jv)

## Interpretation

Guaranteed leverage is the interval narrowing that remains even under
the least favourable admissible resolved member.

Potential leverage is the largest interval narrowing among admissible
resolved members.

Neither quantity is a probability, variance contribution, causal effect,
or value of information.

## Numerical Disclosures

Identification leverage calculated: NO

New carbon classification calculated: NO
"""


REPORT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT.write_text(
    report,
    encoding="utf-8",
)


# ============================================================
# 12. FINAL
# ============================================================

print("\n" + "=" * 78)

print(
    "REFERENCE-FREE IDENTIFICATION-LEVERAGE RULE "
    "FORMALLY LOCKED — PASS"
)

print(
    "POST-RESULT SINGLE REFERENCE SELECTION: PROHIBITED"
)

print(
    "ALL PRE-REGISTERED FAMILY MEMBERS: REQUIRED"
)

print(
    "GUARANTEED EVIDENCE-RESOLUTION LEVERAGE: LOCKED"
)

print(
    "POTENTIAL EVIDENCE-RESOLUTION LEVERAGE: LOCKED"
)

print(
    "IDENTIFICATION LEVERAGE IS NON-ADDITIVE"
)

print(
    "NO IDENTIFICATION-LEVERAGE VALUE CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION CALCULATED"
)

print("=" * 78)