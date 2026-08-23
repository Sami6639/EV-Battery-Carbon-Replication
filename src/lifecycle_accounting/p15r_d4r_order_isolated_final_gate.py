from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

ENGINE = (
    ROOT
    / "src"
    / "lifecycle_accounting"
    / "p15r_d3_generic_accounting_engine.py"
)

OUTPUT = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d3_generic_context_smoke.parquet"
)

REGISTRY = (
    ROOT
    / "results"
    / "intermediate"
    / "p15r_d2_context_registry.parquet"
)

PREREG = (
    ROOT
    / "data"
    / "metadata"
    / "P146C_IDENTIFIED_SET_PREREGISTRATION.json"
)

SPEC = ROOT / "docs" / "IMPLEMENTATION_SPEC.md"

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


# ============================================================
# HELPERS
# ============================================================

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
                    "Frozen scientific output missing: "
                    f"{relative_path}"
                )

            actual_hash = sha256(path)

            if actual_hash != expected_hash:
                raise RuntimeError(
                    "Frozen scientific output changed: "
                    f"{relative_path}"
                )


def run_command(args, timeout):
    result = subprocess.run(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )

    print(result.stdout)

    return result


print("=" * 78)
print("P15R-D4R — ORDER-ISOLATED FINAL ACCOUNTING GATE")
print("=" * 78)


# ============================================================
# 1. REQUIRED FILES
# ============================================================

for path in [
    ENGINE,
    OUTPUT,
    REGISTRY,
    PREREG,
    SPEC,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P15R-D4R FAIL — missing file: {path}"
        )


# ============================================================
# 2. LOAD AUTHORITATIVE PREREGISTRATION
# ============================================================

with PREREG.open(encoding="utf-8") as f:
    prereg = json.load(f)

assert (
    prereg["architecture_roles"]["primary"]
    == "S2_ROBUST_DOMINANCE_MECHANISTIC_SET_IDENTIFICATION"
)

assert (
    prereg["next_stages"]["P15R"]["optimization_search"]
    is False
)

assert (
    prereg["estimand"]["probability_interpretation"]
    == "NONE"
)


# ============================================================
# 3. VERIFY P15R ACCOUNTING OUTPUT
# ============================================================

df = pd.read_parquet(OUTPUT)
registry = pd.read_parquet(REGISTRY)

assert not df.empty
assert not registry.empty

expected_contexts = {
    "PRIMARY_SMOKE",
    "R1S_STRUCTURAL_SMOKE",
    "AGE_USE_SURVIVAL_SMOKE",
    "REGIONAL_GRID_SMOKE",
}

assert set(
    df["context_id"].unique()
) == expected_contexts


required_context_columns = {
    "decision_calendar_year",
    "current_vehicle_age_years",
    "mobility_scenario",
    "survival_scenario",
    "charging_scenario",
    "grid_scenario",
    "grid_geography",
    "grid_region",
    "manufacturing_pathway",
    "manufacturing_benchmark_type",
    "resistance_specification",
}

required_component_columns = {
    "C_operational_kgco2e",
    "C_replacement_manufacturing_kgco2e",
    "R_operational_kgco2e",
    "R_replacement_manufacturing_kgco2e",
    "C_policy_varying_subtotal_kgco2e",
    "R_policy_varying_subtotal_kgco2e",
}

assert required_context_columns <= set(df.columns)
assert required_component_columns <= set(df.columns)


# ============================================================
# 4. ACCOUNTING IDENTITIES
# ============================================================

assert (
    df["C_replacement_manufacturing_kgco2e"]
    == 0
).all()

assert (
    df["R_replacement_manufacturing_kgco2e"]
    >= 0
).all()

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
            + df["R_replacement_manufacturing_kgco2e"]
        )
    )
    .abs()
    .max()
    <= 1e-9
)

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


# ============================================================
# 5. NO P16R LEAKAGE
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
# 6. CONTEXT REGISTRY
# ============================================================

expected_dimensions = {
    "decision_calendar_year",
    "current_vehicle_age_years",
    "mobility_scenario",
    "survival_scenario",
    "charging_scenario",
    "grid_geography",
    "resistance_specification",
}

assert set(
    registry["dimension"]
) == expected_dimensions

assert (
    registry
    .groupby("dimension")["is_primary"]
    .sum()
    .eq(1)
    .all()
)


# ============================================================
# 7. SCIENTIFIC INTEGRITY BEFORE TESTING
# ============================================================

verify_frozen_outputs(prereg)

spec_hash_before = sha256(SPEC)

output_hash_before = sha256(OUTPUT)


# ============================================================
# 8. D3 DETERMINISM
# ============================================================

print("\nRunning D3 determinism regeneration 1/2...")

run1 = run_command(
    [
        sys.executable,
        str(ENGINE),
    ],
    timeout=180,
)

if run1.returncode != 0:
    raise RuntimeError(
        "P15R-D4R FAIL — D3 regeneration 1 failed."
    )

hash_run1 = sha256(OUTPUT)

if hash_run1 != output_hash_before:
    raise RuntimeError(
        "P15R-D4R FAIL — D3 SHA mismatch on run 1."
    )


print("\nRunning D3 determinism regeneration 2/2...")

run2 = run_command(
    [
        sys.executable,
        str(ENGINE),
    ],
    timeout=180,
)

if run2.returncode != 0:
    raise RuntimeError(
        "P15R-D4R FAIL — D3 regeneration 2 failed."
    )

hash_run2 = sha256(OUTPUT)

if hash_run2 != output_hash_before:
    raise RuntimeError(
        "P15R-D4R FAIL — D3 SHA mismatch on run 2."
    )


# ============================================================
# 9. ORDER-ISOLATED FULL TEST COVERAGE
#
# Two legacy tests are stateful/order-sensitive:
#
# - test_all_three_hppc_temperatures_and_lineage_are_present
# - test_boundary_missingness_and_no_filtering
#
# They are NOT skipped.
#
# First:
# all other repository tests run.
#
# Second:
# these two tests run in a clean separate pytest process.
#
# Expected total coverage:
# 83 + 2 = 85 tests.
# ============================================================

print("\n" + "=" * 78)
print("Running repository tests — main isolated group")
print("=" * 78)

main_tests = run_command(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-k",
        (
            "not "
            "test_all_three_hppc_temperatures_and_lineage_are_present "
            "and not "
            "test_boundary_missingness_and_no_filtering"
        ),
    ],
    timeout=600,
)

if main_tests.returncode != 0:
    raise RuntimeError(
        "P15R-D4R FAIL — main isolated test group failed."
    )


print("\n" + "=" * 78)
print("Running repository tests — two legacy order-sensitive tests")
print("=" * 78)

legacy_tests = run_command(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_p11r_recovery.py::"
        "test_all_three_hppc_temperatures_and_lineage_are_present",
        "tests/test_preprocessing.py::"
        "test_boundary_missingness_and_no_filtering",
    ],
    timeout=180,
)

if legacy_tests.returncode != 0:
    raise RuntimeError(
        "P15R-D4R FAIL — isolated legacy tests failed."
    )


# ============================================================
# 10. VERIFY TEST COVERAGE CONTRACT
# ============================================================

main_text = main_tests.stdout.lower()
legacy_text = legacy_tests.stdout.lower()

if "83 passed" not in main_text:
    raise RuntimeError(
        "P15R-D4R FAIL — expected 83 main tests "
        "did not all pass."
    )

if "2 deselected" not in main_text:
    raise RuntimeError(
        "P15R-D4R FAIL — expected exactly "
        "2 isolated legacy tests."
    )

if "2 passed" not in legacy_text:
    raise RuntimeError(
        "P15R-D4R FAIL — expected 2/2 legacy tests."
    )


# ============================================================
# 11. SCIENTIFIC INTEGRITY AFTER TESTING
# ============================================================

verify_frozen_outputs(prereg)

spec_hash_after = sha256(SPEC)

if spec_hash_after != spec_hash_before:
    raise RuntimeError(
        "P15R-D4R FAIL — IMPLEMENTATION_SPEC changed."
    )

final_output_hash = sha256(OUTPUT)

if final_output_hash != output_hash_before:
    raise RuntimeError(
        "P15R-D4R FAIL — final accounting artifact changed."
    )


# ============================================================
# 12. ARTIFACT MANIFEST
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
            f"P15R-D4R FAIL — missing artifact: {relative}"
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

    "test_execution_mode":
        "ORDER_ISOLATED_FULL_COVERAGE",

    "test_coverage": {
        "main_group_passed": 83,
        "legacy_isolated_passed": 2,
        "total_passed": 85,
        "skipped": 0,
        "failed": 0,
    },

    "legacy_test_order_limitation": {
        "present": True,
        "scientific_output_effect": "NONE",
        "tests": [
            "test_all_three_hppc_temperatures_and_lineage_are_present",
            "test_boundary_missingness_and_no_filtering",
        ],
    },

    "d3_smoke_contexts_passed": "4/4",

    "d3_deterministic": True,

    "d3_sha256": final_output_hash,

    "implementation_spec_unchanged": True,

    "p12_p13_p14_frozen_outputs_unchanged": True,

    "lifecycle_total_calculated": False,

    "delta_g_calculated": False,

    "decision_bounds_calculated": False,

    "carbon_classification_produced": False,

    "replacement_optimization_performed": False,

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
# 13. SCIENTIFIC REPORT
# ============================================================

report = f"""# P15R — State-Conditioned Lifecycle-GHG Accounting Engine

## Final Status

`P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS`

## Architecture

P15R implements policy-specific accounting components under the approved P14.6C trajectory-free architecture.

P15R does not identify a replacement decision and does not calculate DeltaG bounds.

## Verified Accounting Boundaries

- P13 L2 battery-side energy remains separate from P14 L3 grid-side electricity.
- Charging conversion is applied once.
- Calendar-specific grid CI is applied to grid-side electricity.
- Replacement-battery manufacturing is counted once in policy R.
- Replacement-battery manufacturing is absent from policy C.
- Original-battery manufacturing remains a common invariant in the policy contrast.
- Vehicle survival is used only for residual-service weighting.
- Survival never assigns battery degradation state.
- R10 and R1s remain separate physical specifications.

## Generic Context Verification

Four pre-specified generic smoke contexts passed:

1. PRIMARY_SMOKE
2. R1S_STRUCTURAL_SMOKE
3. AGE_USE_SURVIVAL_SMOKE
4. REGIONAL_GRID_SMOKE

Accounting rows: {len(df)}

## Determinism

Two complete D3 regenerations produced the same SHA-256:

`{final_output_hash}`

## Repository Test Coverage

The complete repository test inventory was covered using an order-isolated execution because two historical preprocessing/recovery tests are stateful with respect to generated lineage metadata.

Main group:

`83 passed`

Legacy isolated group:

`2 passed`

Total:

`85 passed`

Skipped:

`0`

Failed:

`0`

The two legacy tests were not disabled or skipped. They were run separately after the main group.

This is a test-order/isolation limitation only. No P12/P13/P14 scientific Parquet or frozen scientific hash changed.

## Historical Scientific Integrity

Frozen P12, P13 and P14 scientific outputs remained unchanged.

`IMPLEMENTATION_SPEC.md` remained unchanged.

## Numerical Decision Disclosures

Lifecycle total calculated: `NO`

DeltaG calculated: `NO`

Decision bounds calculated: `NO`

Carbon classification produced: `NO`

Replacement optimization performed: `NO`

## Remaining Bounds

P15R validates the accounting engine only.

The following remain for P16R:

- admissible Theta_R and Theta_C construction;
- R10/R1s robustness;
- pack-loss-share robustness;
- mobility and survival robustness;
- charging-conversion robustness;
- grid pathway and geography robustness;
- manufacturing pathway robustness;
- technical-feasibility classification;
- lower_DeltaG and upper_DeltaG;
- robust carbon classification.

The legacy pytest order dependency is retained transparently as a non-scientific reproducibility limitation.

## Next Gate

P16R may begin only after explicit scientific approval.

No trajectory optimization is authorized.
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
# 14. FINAL
# ============================================================

print("\n" + "=" * 78)

print(
    "P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS"
)

print(
    "D3 DETERMINISM: PASS — 2/2 IDENTICAL SHA-256"
)

print(
    "GENERIC SMOKE CONTEXTS: PASS — 4/4"
)

print(
    "REPOSITORY TEST COVERAGE: PASS — 85/85"
)

print(
    "TEST EXECUTION MODE: ORDER-ISOLATED FULL COVERAGE"
)

print(
    "P12/P13/P14 FROZEN SCIENTIFIC OUTPUTS: UNCHANGED"
)

print(
    "IMPLEMENTATION_SPEC: UNCHANGED"
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
