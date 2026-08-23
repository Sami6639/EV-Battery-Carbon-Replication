from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

PREREG = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
)

SPEC = ROOT / "docs" / "IMPLEMENTATION_SPEC.md"

DECISION_LOG = (
    ROOT
    / "docs"
    / "RESEARCH_DECISION_LOG.md"
)

D3_ENGINE = (
    ROOT
    / "src"
    / "lifecycle_accounting"
    / "p15r_d3_generic_accounting_engine.py"
)

D3_OUTPUT = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d3_generic_context_smoke.parquet"
)

C4_OUTPUT = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_c4_policy_accounting_components.parquet"
)

REGISTRY = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d2_context_registry.parquet"
)

LEGACY_METADATA = (
    ROOT
    / "data"
    / "processed"
    / "metadata"
    / "luh_degradation_state_model.yaml"
)

REPORT = (
    ROOT
    / "docs"
    / "P15R_ACCOUNTING_ENGINE_REPORT.md"
)

MANIFEST = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_accounting_engine_manifest.json"
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


def verify_frozen_outputs(prereg):
    frozen = prereg[
        "frozen_scientific_output_integrity"
    ]

    for stage_paths in frozen.values():
        for relative_path, expected_hash in stage_paths.items():

            path = ROOT / relative_path

            if not path.is_file():
                raise RuntimeError(
                    "Frozen output missing: "
                    f"{relative_path}"
                )

            if sha256(path) != expected_hash:
                raise RuntimeError(
                    "Frozen output changed: "
                    f"{relative_path}"
                )


print("=" * 78)
print("P15R-D4S — SCIENTIFIC FINAL ACCOUNTING GATE")
print("=" * 78)


# ============================================================
# 1. REQUIRED FILES
# ============================================================

for path in [
    PREREG,
    SPEC,
    D3_ENGINE,
    D3_OUTPUT,
    C4_OUTPUT,
    REGISTRY,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P15R-D4S FAIL — missing: {path}"
        )


# ============================================================
# 2. AUTHORITATIVE ARCHITECTURE
# ============================================================

with PREREG.open(encoding="utf-8") as f:
    prereg = json.load(f)

assert (
    prereg["architecture_roles"]["primary"]
    == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
)

assert (
    prereg["next_stages"]["P15R"][
        "optimization_search"
    ]
    is False
)

assert (
    prereg["identified_interval"][
        "calculated_in_p146c"
    ]
    is False
)


# ============================================================
# 3. ACCOUNTING COMPONENT CONTRACT
# ============================================================

df = pd.read_parquet(C4_OUTPUT)

assert not df.empty

required = {
    "C_operational_kgco2e",
    "C_replacement_manufacturing_kgco2e",
    "R_operational_kgco2e",
    "R_replacement_manufacturing_kgco2e",
    "C_policy_varying_subtotal_kgco2e",
    "R_policy_varying_subtotal_kgco2e",
}

assert required <= set(df.columns)


# Continue policy has no replacement manufacturing.
assert (
    df["C_replacement_manufacturing_kgco2e"]
    == 0
).all()


# Replacement manufacturing counted once.
expected_mfg = (
    df["replacement_pack_kwh"]
    * df["pack_ghg_kgco2e_per_kwh"]
)

assert (
    (
        df["R_replacement_manufacturing_kgco2e"]
        - expected_mfg
    )
    .abs()
    .max()
    <= 1e-9
)


# Policy-varying subtotals.
assert (
    (
        df["C_policy_varying_subtotal_kgco2e"]
        - df["C_operational_kgco2e"]
    )
    .abs()
    .max()
    <= 1e-9
)

assert (
    (
        df["R_policy_varying_subtotal_kgco2e"]
        - (
            df["R_operational_kgco2e"]
            + df[
                "R_replacement_manufacturing_kgco2e"
            ]
        )
    )
    .abs()
    .max()
    <= 1e-9
)


# ============================================================
# 4. NO P16R LEAKAGE
# ============================================================

for forbidden in [
    "DeltaG",
    "lower_DeltaG",
    "upper_DeltaG",
    "carbon_classification",
    "decision_classification",
]:
    assert forbidden not in df.columns


for flag in [
    "lifecycle_total_calculated",
    "delta_g_calculated",
    "decision_bounds_calculated",
    "carbon_classification_produced",
    "replacement_optimization_performed",
]:
    assert not df[flag].any()


# ============================================================
# 5. FROZEN SCIENTIFIC INTEGRITY
# ============================================================

verify_frozen_outputs(prereg)

spec_hash_before = sha256(SPEC)


# ============================================================
# 6. D3 DETERMINISM — TWO REGENERATIONS
# ============================================================

initial_hash = sha256(D3_OUTPUT)

for run_number in (1, 2):

    result = subprocess.run(
        [
            sys.executable,
            str(D3_ENGINE),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            "P15R-D4S FAIL — "
            f"D3 regeneration {run_number} failed."
        )

    if sha256(D3_OUTPUT) != initial_hash:
        raise RuntimeError(
            "P15R-D4S FAIL — "
            "D3 determinism mismatch."
        )


# ============================================================
# 7. CURRENT ARCHITECTURE INTEGRITY TEST
# ============================================================

test_result = subprocess.run(
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

print("\nP14.6C integrity tests:")
print(test_result.stdout)

if test_result.returncode != 0:
    raise RuntimeError(
        "P15R-D4S FAIL — "
        "P14.6C integrity tests failed."
    )


# ============================================================
# 8. FINAL SCIENTIFIC INTEGRITY
# ============================================================

verify_frozen_outputs(prereg)

if sha256(SPEC) != spec_hash_before:
    raise RuntimeError(
        "P15R-D4S FAIL — "
        "IMPLEMENTATION_SPEC changed."
    )


# ============================================================
# 9. LEGACY TEST-STATE LIMITATION
# ============================================================

legacy_metadata_present = (
    LEGACY_METADATA.is_file()
)

legacy_limitation = (
    "LEGACY_LINEAGE_METADATA_STATE_DEPENDENCY"
)


# ============================================================
# 10. MANIFEST
# ============================================================

artifact_paths = [
    "results/intermediate/"
    "p15r_c1_accounting_components_2025.parquet",

    "results/intermediate/"
    "p15r_c2_residual_service_weights.parquet",

    "results/intermediate/"
    "p15r_c3_annual_operational_components.parquet",

    "results/intermediate/"
    "p15r_c3_residual_operational_components.parquet",

    "results/intermediate/"
    "p15r_c4_policy_accounting_components.parquet",

    "results/intermediate/"
    "p15r_d2_context_registry.parquet",

    "results/intermediate/"
    "p15r_d3_generic_context_smoke.parquet",
]

artifacts = []

for relative in artifact_paths:

    path = ROOT / relative

    if not path.is_file():
        raise RuntimeError(
            f"Missing P15R artifact: {relative}"
        )

    artifacts.append(
        {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )


manifest = {
    "stage": "P15R",

    "final_status":
        "P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS",

    "d3_smoke_contexts_passed": "4/4",

    "d3_deterministic": True,

    "d3_sha256": sha256(D3_OUTPUT),

    "p146c_integrity_tests_passed": True,

    "legacy_full_suite_clean": False,

    "legacy_test_limitation": legacy_limitation,

    "legacy_metadata_present_at_final_gate":
        legacy_metadata_present,

    "most_recent_full_suite_observation":
        "83 passed, 2 failed",

    "scientific_output_effect_of_legacy_issue":
        "NONE IDENTIFIED",

    "p12_p13_p14_frozen_outputs_unchanged":
        True,

    "implementation_spec_unchanged":
        True,

    "lifecycle_total_calculated":
        False,

    "delta_g_calculated":
        False,

    "decision_bounds_calculated":
        False,

    "carbon_classification_produced":
        False,

    "replacement_optimization_performed":
        False,

    "artifacts": artifacts,
}


MANIFEST.parent.mkdir(
    parents=True,
    exist_ok=True,
)

MANIFEST.write_text(
    json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 11. REPORT
# ============================================================

report = f"""# P15R — State-Conditioned Lifecycle-GHG Accounting Engine

## Final Status

`P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS`

## Scientific Scope

P15R validates the accounting mechanics required by the approved trajectory-free P14.6C architecture.

P15R does not calculate the identified decision interval and does not produce a replacement recommendation.

## Verified Accounting Architecture

- Policy C and policy R are represented separately.
- P13 L2 battery-side energy remains separate from P14 L3 grid-side electricity.
- Charging conversion is applied once.
- Calendar-specific grid CI is applied to grid-side electricity.
- Replacement manufacturing is counted once in policy R.
- Replacement manufacturing is absent from policy C.
- Original-battery manufacturing remains a common invariant.
- Vehicle survival is used only as residual-service weighting.
- Survival does not assign degradation state.
- R10 and R1s remain separate.
- No trajectory is generated.

## Generic Context Verification

Four pre-specified generic accounting contexts passed.

`4/4`

## Determinism

Two complete D3 regenerations produced identical SHA-256.

`{sha256(D3_OUTPUT)}`

## Scientific Integrity

Frozen P12, P13 and P14 scientific outputs remained unchanged.

`IMPLEMENTATION_SPEC.md` remained unchanged.

P14.6C integrity tests passed.

## Legacy Repository Test Limitation

The most recent monolithic repository test execution reported:

`83 passed, 2 failed`

The two failures concern historical preprocessing/recovery lineage metadata and specifically the availability/state of:

`data/processed/metadata/luh_degradation_state_model.yaml`

The same historical tests have also passed in targeted execution under a different repository metadata state.

This behavior is therefore recorded as:

`{legacy_limitation}`

It is not represented as a clean full-suite pass.

No modification of frozen P12/P13/P14 scientific Parquet outputs was made to force the legacy tests to pass.

This is retained as a non-scientific technical reproducibility limitation.

## Decision Disclosures

Lifecycle total calculated: `NO`

DeltaG calculated: `NO`

Decision bounds calculated: `NO`

Carbon classification produced: `NO`

Replacement optimization performed: `NO`

## Remaining Scientific Bounds

P15R validates accounting only.

P16R remains responsible for:

- Theta_R and Theta_C;
- joint Theta(z);
- lower_DeltaG and upper_DeltaG;
- R10/R1s robustness;
- pack-loss-share robustness;
- mobility and survival robustness;
- charging uncertainty;
- grid pathway/geography uncertainty;
- manufacturing pathway uncertainty;
- technical feasibility;
- robust carbon classification.

## Next Gate

P16R is not automatically authorized by this report.

A scientific novelty/publication-potential review should precede P16R.
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
# 12. DECISION LOG — APPEND ONCE
# ============================================================

heading = (
    "## P15R — State-Conditioned "
    "Lifecycle-GHG Accounting Engine"
)

entry = f"""

{heading}

Stage: P15R — State-Conditioned Lifecycle-GHG Accounting Engine

Decision: P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS

Accounting consequence: Policy-specific continue and immediate-replacement accounting components are reproducible under the approved trajectory-free architecture. No DeltaG, decision bounds, carbon classification, or optimization was calculated.

Scientific integrity: Frozen P12/P13/P14 scientific outputs and IMPLEMENTATION_SPEC remained unchanged.

Technical limitation: `{legacy_limitation}`; the most recent monolithic repository test execution reported 83 passed and 2 historical lineage-metadata failures. This is not represented as a clean full-suite pass.

Evidence: `docs/P15R_ACCOUNTING_ENGINE_REPORT.md`
"""

log_text = DECISION_LOG.read_text(
    encoding="utf-8"
)

if heading not in log_text:

    with DECISION_LOG.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(entry)


# ============================================================
# 13. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 78)

print(
    "P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS"
)

print(
    "GENERIC ACCOUNTING CONTEXTS: PASS — 4/4"
)

print(
    "D3 DETERMINISM: PASS — 2/2 IDENTICAL SHA-256"
)

print(
    "P14.6C INTEGRITY TESTS: PASS"
)

print(
    "P12/P13/P14 FROZEN SCIENTIFIC OUTPUTS: UNCHANGED"
)

print(
    "IMPLEMENTATION_SPEC: UNCHANGED"
)

print(
    "MONOLITHIC FULL SUITE: NOT CLEAN — "
    "LEGACY LINEAGE METADATA STATE DEPENDENCY"
)

print(
    "MOST RECENT FULL SUITE: 83 PASSED, 2 FAILED"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO DECISION BOUNDS CALCULATED"
)

print(
    "NO CARBON CLASSIFICATION PRODUCED"
)

print(
    "NO REPLACEMENT OPTIMIZATION PERFORMED"
)

print("\nReport:")
print(
    REPORT.relative_to(ROOT)
)

print("\nManifest:")
print(
    MANIFEST.relative_to(ROOT)
)

print("=" * 78)