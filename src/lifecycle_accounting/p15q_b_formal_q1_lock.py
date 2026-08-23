from pathlib import Path
import hashlib
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]

PREREG = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_PREREGISTRATION.json"
)

P15R_MANIFEST = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_accounting_engine_manifest.json"
)

SPEC = ROOT / "docs" / "IMPLEMENTATION_SPEC.md"
LOG = ROOT / "docs" / "RESEARCH_DECISION_LOG.md"

LOCK_FILE = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

REPORT = (
    ROOT
    / "docs"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK_REPORT.md"
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
print("P15Q-B — FORMAL Q1 NOVELTY & IDENTIFICATION LOCK")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

for path in [
    PREREG,
    P15R_MANIFEST,
    SPEC,
    LOG,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P15Q-B FAIL — missing file: {path}"
        )


with PREREG.open(encoding="utf-8") as f:
    prereg = json.load(f)

with P15R_MANIFEST.open(encoding="utf-8") as f:
    p15r = json.load(f)


# ============================================================
# 2. PRE-RESULT STATUS
# ============================================================

assert (
    prereg["status"]
    ==
    "Q1 NOVELTY STRENGTHENING PREREGISTERED — PROPOSAL"
)

assert prereg["numerical_analysis_performed"] is False

assert (
    p15r["final_status"]
    ==
    "P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS"
)

assert p15r["delta_g_calculated"] is False
assert p15r["decision_bounds_calculated"] is False
assert p15r["carbon_classification_produced"] is False


# ============================================================
# 3. CONTRIBUTION ARCHITECTURE
# ============================================================

required_contributions = {
    "C1_DUAL_STATE_DECISION_ATLAS",
    "C2_TRAJECTORY_FREE_IDENTIFICATION",
    "C3_IDENTIFICATION_BOTTLENECK",
}

assert set(prereg["contributions"]) == required_contributions


# ============================================================
# 4. DUAL-STATE CONTRACT
# ============================================================

dual = prereg["dual_state_necessity_test"]

assert (
    dual["capacity_matching_rule"]["half_width"]
    == 0.025
)

assert (
    dual["capacity_matching_rule"][
        "post_result_widening"
    ]
    is False
)

assert dual["no_smoothing_for_headline"] is True


# ============================================================
# 5. IDENTIFICATION BOTTLENECK CONTRACT
#
# IMPORTANT:
# primary_name lives under contributions/C3,
# NOT under identification_leverage.
# ============================================================

c3 = prereg["contributions"][
    "C3_IDENTIFICATION_BOTTLENECK"
]

assert (
    c3["primary_name"]
    == "IDENTIFICATION LEVERAGE"
)

assert (
    c3["value_of_information_claim"]
    == "PROHIBITED"
)

assert (
    c3["causal_importance_claim"]
    == "PROHIBITED"
)


leverage = prereg["identification_leverage"]

assert (
    leverage["absolute_leverage"]
    == "L_j = W_full - W_resolved_j"
)

assert (
    leverage["normalized_leverage"]
    == "Lnorm_j = L_j / W_full when W_full > 0"
)

assert leverage["primary_evidence_families"] == [
    "FUTURE_STATE_ENDPOINT_TREATMENT",
    "CURRENT_RESISTANCE_ENVELOPE",
    "PACK_LOSS_SHARE",
]

assert (
    leverage["nonadditivity_rule"]
    ==
    "L_j values are not additive and must not be interpreted "
    "as variance shares or probabilities."
)


# ============================================================
# 6. CONTEXT MODULATION
# ============================================================

context = prereg["context_modulation"]

assert (
    context["analysis_name"]
    == "CONTEXT MODULATION"
)

assert (
    context["identification_leverage_label"]
    ==
    "PROHIBITED_FOR_EXOGENOUS_CONTEXT_SHIFTS"
)


# ============================================================
# 7. PAIRWISE BOTTLENECK RULE
# ============================================================

pairwise = prereg[
    "pairwise_identification_interaction"
]

assert (
    pairwise["status"]
    ==
    "SECONDARY_INTERACTION_DIAGNOSTIC"
)

assert (
    pairwise["post_result_family_substitution"]
    == "PROHIBITED"
)


# ============================================================
# 8. VERIFY CURRENT SPEC IS STILL PRE-P15Q
# ============================================================

expected_pre = prereg[
    "implementation_spec_pre_p15q"
]

current_hash = sha256(SPEC)
current_bytes = SPEC.stat().st_size

assert current_hash == expected_pre["sha256"]
assert current_bytes == expected_pre["bytes"]


# ============================================================
# 9. PRE-AMENDMENT INTEGRITY TEST
# ============================================================

pre_test = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_p146c_formal_revision.py",
    ],
    cwd=ROOT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=180,
)

print("\nPre-amendment P14.6C integrity:")
print(pre_test.stdout)

if pre_test.returncode != 0:
    raise RuntimeError(
        "P15Q-B FAIL — pre-amendment integrity failed."
    )


# ============================================================
# 10. APPEND-ONLY ADDENDUM
# ============================================================

HEADING = (
    "# P15Q — APPROVED Q1 NOVELTY "
    "AND IDENTIFICATION STRENGTHENING"
)

spec_original_bytes = SPEC.read_bytes()

spec_text = spec_original_bytes.decode("utf-8")

if HEADING in spec_text:
    raise RuntimeError(
        "P15Q-B STOP — P15Q addendum already exists."
    )


ADDENDUM = r"""

---

# P15Q — APPROVED Q1 NOVELTY AND IDENTIFICATION STRENGTHENING

**Status:** FORMALLY LOCKED BEFORE P16R RESULTS

This amendment strengthens the approved P14.6C trajectory-free
architecture without changing the revised Primary RQ, DeltaG sign
convention, policy symmetry, Theta_R, Theta_C, Theta(z), or the
prohibition on trajectory optimization.

## P15Q.1 Contribution 1 — Dual-State Carbon-Decision Atlas

P16R must condition the decision jointly on:

- reconstructed capacity retention; and
- supported relative pulse-resistance state.

Capacity SOH alone is not assumed sufficient.

The primary scientific object is:

capacity retention × relative resistance
→ conditional carbon-decision classification.

Unsupported states must not be smoothed or interpolated for headline
results.

## P15Q.2 Contribution 2 — Trajectory-Free Identification

P16R must bound the immediate-replacement versus continued-first-life
life-cycle-GHG contrast without imposing an unsupported real-world
degradation trajectory.

Primary classifications remain:

- ROBUST CONTINUE
- ROBUST REPLACE
- CARBON DECISION INDETERMINATE

No claim may be made that partial identification or carbon-optimal
battery retirement was invented by this study.

## P15Q.3 Contribution 3 — Identification Bottleneck

For wide or indeterminate intervals, P16R must determine which unresolved
physical/model-evidence family most constrains sign identification.

Definitions:

W_full = upper_DeltaG - lower_DeltaG

W_resolved_j = interval width after evidence family j is fixed to its
pre-registered reference/supportable setting while all other admissible
evidence uncertainty remains active.

L_j = W_full - W_resolved_j

When W_full > 0:

Lnorm_j = L_j / W_full

The approved term is:

IDENTIFICATION LEVERAGE

or:

EVIDENCE-RESOLUTION LEVERAGE

It must not be described as:

- probability;
- causal importance;
- variance contribution;
- value of information.

Leverage values are conditional, descriptive, and non-additive.

## P15Q.4 Primary Evidence-Resolution Families

The primary identification-leverage families are:

1. FUTURE_STATE_ENDPOINT_TREATMENT
2. CURRENT_RESISTANCE_ENVELOPE
3. PACK_LOSS_SHARE

R10 versus R1s remains a separate structural physical robustness test.

No evidence family may be fixed to a value selected after observing
DeltaG.

## P15Q.5 Matched-Capacity Dual-State Necessity Test

Capacity matching uses a fixed symmetric:

±0.025 capacity-retention window.

The window cannot be widened after observing results.

When supported resistance states inside the same matched-capacity and
matched-context comparison produce different primary carbon
classifications, report:

DUAL-STATE DECISION DISCORDANCE

When support is inadequate, report:

INSUFFICIENT DUAL-STATE SUPPORT

Absence of discordance does not prove universal sufficiency of
capacity-only SOH.

## P15Q.6 Context Modulation

Exogenous context is distinct from uncertainty inside Theta(z).

The following are analysed as CONTEXT MODULATION rather than
identification leverage:

- decision calendar year;
- current vehicle age;
- annual mileage;
- mobility requirement;
- vehicle survival;
- charging efficiency;
- grid pathway;
- grid geography;
- battery-manufacturing pathway;
- battery-manufacturing temporal treatment.

## P15Q.7 Pairwise Bottleneck Diagnostic

Pairwise evidence-resolution analysis may run only when:

1. the full interval is CARBON DECISION INDETERMINATE; and
2. no single pre-registered evidence family recovers a robust sign.

Only the three evidence families with the largest single-family absolute
identification leverage are eligible for pairwise analysis.

Pairwise findings are not causal interaction effects.

## P15Q.8 P16R Result Architecture

P16R reporting order is:

1. PRIMARY DUAL-STATE DECISION ATLAS
2. MATCHED-CAPACITY DUAL-STATE NECESSITY TEST
3. IDENTIFICATION-BOTTLENECK ANALYSIS
4. CONTEXT MODULATION
5. STRUCTURAL ROBUSTNESS
6. EXTREME / STRESS RESULTS
7. TECHNICAL FEASIBILITY

Stress/extreme evidence is not headline-eligible.

## P15Q.9 Reviewer-Defense Rules

P16R must not:

- claim invention of partial identification;
- claim first-ever carbon-optimal retirement;
- call identification leverage value of information;
- treat P12 state space as fleet prevalence;
- interpolate unsupported states for headline results;
- widen uncertainty bounds after seeing results;
- narrow indeterminate intervals for publication appearance;
- merge R10 and R1s;
- treat technical replacement as carbon benefit;
- treat context variation as identification leverage.

Indeterminacy is a valid scientific result.

## P15Q.10 Mandatory Post-P16R Q1 Gate

Before manuscript drafting, a separate publication-strength gate must
determine whether P16R demonstrates:

- non-trivial dual-state decision structure;
- whether resistance adds information beyond capacity;
- interpretable evidence bottlenecks;
- interpretable residual-service and temporal-carbon mechanisms; and
- information stronger than conventional sensitivity analysis.

If results are predominantly indeterminate, bounds must not be narrowed
post hoc.

The manuscript may proceed only if the identification-bottleneck
analysis itself provides a sufficiently strong evidence-gap contribution.

## P15Q.11 Authorization Boundary

P15Q calculates no:

- DeltaG;
- lower_DeltaG;
- upper_DeltaG;
- carbon classification;
- identification leverage result;
- dual-state discordance result.

P16R numerical work begins only after this lock.
"""


try:

    with SPEC.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(ADDENDUM)

    # ========================================================
    # 11. VERIFY PREFIX IDENTITY
    # ========================================================

    amended_bytes = SPEC.read_bytes()

    assert (
        hashlib.sha256(
            amended_bytes[:expected_pre["bytes"]]
        ).hexdigest()
        ==
        expected_pre["sha256"]
    )

    # ========================================================
    # 12. POST-AMENDMENT INTEGRITY TEST
    # ========================================================

    post_test = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_p146c_formal_revision.py",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=180,
    )

    print("\nPost-amendment P14.6C integrity:")
    print(post_test.stdout)

    if post_test.returncode != 0:
        raise RuntimeError(
            "P15Q-B FAIL — post-amendment integrity failed."
        )

except Exception:

    # Fail closed: restore exact original spec.
    SPEC.write_bytes(spec_original_bytes)

    raise


# ============================================================
# 13. FINAL SPEC IDENTITY
# ============================================================

spec_hash_after = sha256(SPEC)

assert spec_hash_after != expected_pre["sha256"]


# ============================================================
# 14. DECISION LOG
# ============================================================

LOG_HEADING = (
    "## P15Q — Q1 Novelty and "
    "Identification Strengthening"
)

LOG_ENTRY = """

## P15Q — Q1 Novelty and Identification Strengthening

Stage: P15Q — Q1 Novelty & Identification-Leverage Preregistration

Decision: Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS

Scientific consequence: P16R must evaluate dual-state decision
structure, trajectory-free mechanistic set identification, and
identification bottlenecks.

Matched-capacity rule: fixed ±0.025 capacity-retention window.

Identification leverage is interval narrowing only and must not be
described as probability, causal importance, variance contribution, or
value of information.

Exogenous grid, manufacturing, mileage, survival and charging contexts
are analysed separately as context modulation.

A separate post-P16R Q1 publication-strength gate is mandatory before
manuscript drafting.

Numerical P16R result calculated: NONE.
"""


log_text = LOG.read_text(
    encoding="utf-8"
)

if LOG_HEADING not in log_text:

    with LOG.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(LOG_ENTRY)


# ============================================================
# 15. LOCK RECEIPT
# ============================================================

lock = {
    "stage": "P15Q",

    "final_status":
        "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS",

    "locked_before_p16r_results":
        True,

    "contribution_layers": [
        "DUAL_STATE_CARBON_DECISION_ATLAS",
        "TRAJECTORY_FREE_MECHANISTIC_SET_IDENTIFICATION",
        "IDENTIFICATION_BOTTLENECK",
    ],

    "matched_capacity_window":
        0.025,

    "identification_leverage_primary_families":
        leverage["primary_evidence_families"],

    "context_modulation_separate":
        True,

    "pairwise_trigger_preregistered":
        True,

    "post_p16r_q1_gate_required":
        True,

    "numerical_p16r_result_calculated":
        False,

    "implementation_spec": {
        "pre_sha256":
            expected_pre["sha256"],

        "pre_bytes":
            expected_pre["bytes"],

        "post_sha256":
            spec_hash_after,

        "append_only_prefix_preserved":
            True,
    },
}


LOCK_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

LOCK_FILE.write_text(
    json.dumps(
        lock,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 16. REPORT
# ============================================================

report = f"""# P15Q — Formal Q1 Novelty Strengthening Lock

## Final Status

`Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS`

## Locked Before P16R

YES

## Contribution Layers

1. Dual-state carbon-decision atlas.
2. Trajectory-free mechanistic set identification.
3. Identification-bottleneck analysis.

## Matched-Capacity Rule

±0.025 capacity retention.

Outcome-driven widening: PROHIBITED.

## Identification Leverage

Primary families:

- FUTURE_STATE_ENDPOINT_TREATMENT
- CURRENT_RESISTANCE_ENVELOPE
- PACK_LOSS_SHARE

Identification leverage is not probability, causal importance,
variance contribution, or value of information.

## Context Modulation

Exogenous contexts remain separate from evidence-resolution leverage.

## Pairwise Rule

Pre-registered and conditional.

## Post-P16R Q1 Gate

MANDATORY BEFORE MANUSCRIPT DRAFTING.

## Specification

Pre SHA-256:

`{expected_pre["sha256"]}`

Post SHA-256:

`{spec_hash_after}`

Historical prefix preserved:

YES

## Numerical Disclosures

DeltaG calculated: NO

Decision bounds calculated: NO

Carbon classifications calculated: NO

Identification leverage calculated: NO

Dual-state discordance calculated: NO

P16R started: NO
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
# 17. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 78)

print(
    "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS"
)

print(
    "DUAL-STATE DECISION ATLAS: LOCKED"
)

print(
    "MATCHED-CAPACITY NECESSITY TEST: LOCKED"
)

print(
    "IDENTIFICATION LEVERAGE: LOCKED"
)

print(
    "CONTEXT MODULATION: LOCKED AS SEPARATE ANALYSIS"
)

print(
    "PAIRWISE BOTTLENECK TRIGGER: LOCKED"
)

print(
    "POST-P16R Q1 PUBLICATION-STRENGTH GATE: MANDATORY"
)

print(
    "IMPLEMENTATION_SPEC: APPEND-ONLY AMENDED"
)

print(
    "P14.6C INTEGRITY TESTS: PASS"
)

print(
    "NO P16R RESULT CALCULATED"
)

print("\nLock receipt:")
print(
    LOCK_FILE.relative_to(ROOT)
)

print("\nReport:")
print(
    REPORT.relative_to(ROOT)
)

print("=" * 78)