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
print("P15R-D4 — FINAL ACCOUNTING ENGINE GATE")
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
            f"P15R-D4 FAIL — missing file: {path}"
        )


# ============================================================
# 2. LOAD AUTHORITY
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
# 3. ACCOUNTING OUTPUT CONTRACT
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
    ).abs().max()
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
    ).abs().max()
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
    ).abs().max()
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
# 6. CONTEXT REGISTRY CONTRACT
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
    registry.groupby("dimension")["is_primary"]
    .sum()
    .eq(1)
    .all()
)


# ============================================================
# 7. FROZEN P12/P13/P14 INTEGRITY — BEFORE
# ============================================================

def verify_frozen_outputs():
    for stage_paths in (
        prereg[
            "frozen_scientific_output_integrity"
        ].values()
    ):
        for relative_path, expected_hash in (
            stage_paths.items()
        ):
            path = ROOT / relative_path

            if not path.is_file():
                raise RuntimeError(
                    "Frozen scientific output missing: "
                    f"{relative_path}"
                )

            actual = sha256(path)

            if actual != expected_hash:
                raise RuntimeError(
                    "Frozen scientific output changed: "
                    f"{relative_path}"
                )


verify_frozen_outputs()

spec_hash_before = sha256(SPEC)


# ============================================================
# 8. D3 DETERMINISM — TWO REGENERATIONS
# ============================================================

hash_initial = sha256(OUTPUT)

for run_number in [1, 2]:

    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
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
            f"P15R-D4 FAIL — D3 regeneration "
            f"{run_number} failed."
        )

    current_hash = sha256(OUTPUT)

    if current_hash != hash_initial:
        raise RuntimeError(
            "P15R-D4 FAIL — D3 artifact "
            "SHA-256 mismatch."
        )

hash_final = sha256(OUTPUT)


# ============================================================
# 9. FULL REPOSITORY TEST SUITE
# ============================================================

print("\nRunning full pytest suite...")

pytest_result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
    ],
    cwd=ROOT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=600,
)

print(pytest_result.stdout)

if pytest_result.returncode != 0:
    raise RuntimeError(
        "P15R-D4 FAIL — full pytest suite failed."
    )


# ============================================================
# 10. FROZEN INTEGRITY — AFTER FULL SUITE
# ============================================================

verify_frozen_outputs()

spec_hash_after = sha256(SPEC)

if spec_hash_after != spec_hash_before:
    raise RuntimeError(
        "P15R-D4 FAIL — IMPLEMENTATION_SPEC changed."
    )


# ============================================================
# 11. ARTIFACT MANIFEST
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
            f"P15R-D4 FAIL — missing artifact {relative}"
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
    "d3_sha256": hash_final,
    "full_pytest_passed": True,
    "implementation_spec_unchanged": True,
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
# 12. SHORT SCIENTIFIC REPORT
# ============================================================

report = f"""# P15R — State-Conditioned Lifecycle-GHG Accounting Engine

## Final Status

`P15R ACCOUNTING ENGINE VALIDATED WITH BOUNDS`

## Accounting Scope

P15R implements policy-specific accounting components for immediate replacement and continued first-life use under the approved trajectory-free P14.6C architecture.

It does not calculate identified decision bounds or carbon classifications.

## Verified Boundaries

- P13 L2 battery-side energy remains distinct from P14 L3 grid-side electricity.
- Charging conversion is applied once.
- Operational GHG uses calendar-specific grid carbon intensity.
- Replacement battery manufacturing is counted once in policy R.
- Replacement battery manufacturing is absent from policy C.
- Original battery manufacturing remains a common invariant in the policy contrast.
- Vehicle survival is used only as residual-service weighting.
- Survival does not assign a degradation state.
- R10 and R1s remain distinct context specifications.

## Generic Context Verification

Four pre-specified smoke contexts passed:

- PRIMARY_SMOKE
- R1S_STRUCTURAL_SMOKE
- AGE_USE_SURVIVAL_SMOKE
- REGIONAL_GRID_SMOKE

Output rows: {len(df)}

## Determinism

Two complete P15R-D3 regenerations produced the same SHA-256:

`{hash_final}`

## Historical Scientific Integrity

Frozen P12, P13, and P14 scientific-output hashes remained unchanged.

`IMPLEMENTATION_SPEC.md` remained unchanged during P15R-D4.

## Numerical Decision Disclosures

Lifecycle total calculated: `NO`

DeltaG calculated: `NO`

Decision bounds calculated: `NO`

Carbon classification produced: `NO`

Replacement optimization performed: `NO`

## Remaining Bounds

P15R validates accounting mechanics, not the scientific decision sign.

Physical-state uncertainty, R10/R1s specification, pack-loss share, mobility, survival, charging, regional grid variation, manufacturing pathways, and other pre-registered structural uncertainty remain for P16R.

No trajectory optimization is authorized.

## Next Gate

P16R may begin only after explicit instruction.

P16R will construct identified-set decision bounds and apply the pre-registered robustness classifications.
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
# 13. FINAL OUTPUT
# ============================================================

print("=" * 78)

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
    "FULL PYTEST SUITE: PASS"
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
print(REPORT.relative_to(ROOT))

print("\nManifest:")
print(MANIFEST.relative_to(ROOT))

print("=" * 78)