from pathlib import Path
import hashlib
import json
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]

CONFIG = (
    ROOT
    / "src"
    / "vehicle_energy"
    / "p13_config.yaml"
)

PARAMS = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

SPEC = (
    ROOT
    / "docs"
    / "IMPLEMENTATION_SPEC.md"
)

LOG = (
    ROOT
    / "docs"
    / "RESEARCH_DECISION_LOG.md"
)

P15Q_LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_A1D_POWER_EVIDENCE_LIMITATION_LOCK.json"
)

REPORT = (
    ROOT
    / "docs"
    / "P16R_A1D_POWER_EVIDENCE_LIMITATION_REPORT.md"
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
print("P16R-A1D — POWER-EVIDENCE LIMITATION LOCK")
print("=" * 78)


# ============================================================
# 1. REQUIRED FILES
# ============================================================

for path in [
    CONFIG,
    PARAMS,
    SPEC,
    LOG,
    P15Q_LOCK,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P16R-A1D FAIL — missing file: {path}"
        )


# ============================================================
# 2. VERIFY P15Q Q1 LOCK
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
# 3. LOAD MACHINE-READABLE P13 EVIDENCE
# ============================================================

with CONFIG.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)

with PARAMS.open(encoding="utf-8") as f:
    params = json.load(f)


# Exact audited YAML path:
#
# root
# .representative_vehicle
# .synthesized_vehicle_parameters
# .battery_max_power_watts
#
battery_max_power_w = float(
    config[
        "representative_vehicle"
    ][
        "synthesized_vehicle_parameters"
    ][
        "battery_max_power_watts"
    ]
)

battery_max_power_kw = (
    battery_max_power_w / 1000.0
)


# ============================================================
# 4. FRESH DRIVE-CYCLE POWER EVIDENCE
# ============================================================

combined = [
    row
    for row in params["fresh_baseline"]
    if row.get("drive_cycle") == "COMBINED_55_45"
]

assert len(combined) == 1

fresh_max_terminal_kw = float(
    combined[0]["maximum_terminal_power_kw"]
)

fresh_min_terminal_kw = float(
    combined[0]["minimum_terminal_power_kw"]
)

fresh_regen_magnitude_kw = abs(
    fresh_min_terminal_kw
)

assert battery_max_power_kw > 0
assert fresh_max_terminal_kw > 0
assert fresh_regen_magnitude_kw >= 0


fresh_discharge_headroom_ratio = (
    battery_max_power_kw
    / fresh_max_terminal_kw
)


# ============================================================
# 5. SCIENTIFIC INTERPRETATION
# ============================================================

RANGE_STATUS = (
    "STATE_SPECIFIC_RANGE_FEASIBILITY_AVAILABLE"
)

FRESH_POWER_STATUS = (
    "FRESH_POWER_HEADROOM_PLAUSIBILITY_AVAILABLE"
)

AGED_POWER_STATUS = (
    "AGED_STATE_POWER_CAPABILITY_NOT_STATE_RESOLVED"
)


# ============================================================
# 6. PRE-AMENDMENT SPEC IDENTITY
# ============================================================

spec_original_bytes = SPEC.read_bytes()

spec_hash_before = hashlib.sha256(
    spec_original_bytes
).hexdigest()

spec_bytes_before = len(
    spec_original_bytes
)


# ============================================================
# 7. APPEND-ONLY SCIENTIFIC ADDENDUM
# ============================================================

HEADING = (
    "# P16R-A1D — APPROVED POWER-EVIDENCE LIMITATION"
)

ADDENDUM = f"""

---

# P16R-A1D — APPROVED POWER-EVIDENCE LIMITATION

**Status:** FORMALLY LOCKED BEFORE P16R DECISION RESULTS

P13 provides source-backed evidence for:

- state-specific usable-energy/range precursor;
- fresh representative battery maximum power;
- fresh drive-cycle terminal-power demand.

P13 does not provide a validated aged-state:

- maximum deliverable battery power;
- BMS current limit;
- terminal-voltage cutoff;
- voltage-sag feasibility threshold; or
- resistance-to-maximum-power transition model.

Machine-readable fresh evidence is:

- fresh battery maximum power = {battery_max_power_kw:.9f} kW;
- combined-cycle maximum discharge demand = {fresh_max_terminal_kw:.9f} kW;
- combined-cycle regenerative magnitude = {fresh_regen_magnitude_kw:.9f} kW;
- fresh discharge-power headroom ratio = {fresh_discharge_headroom_ratio:.9f}.

The headroom ratio is a **fresh-state plausibility check only**.

It must never be interpreted as aged-state power feasibility.

## Locked Technical-Evidence Structure

P16R must distinguish exactly:

1. `RANGE FEASIBILITY — STATE RESOLVED`
2. `FRESH POWER HEADROOM — PLAUSIBILITY ONLY`
3. `AGED-STATE POWER CAPABILITY — NOT STATE RESOLVED`

No aged current limit, voltage threshold, BMS cutoff, maximum deliverable
power, or deterministic resistance-to-power-capability relationship may
be invented.

## Technical Classification Rule

Where the P13 state-specific technical-range precursor meets the locked
mobility requirement, the permitted interpretation is:

`RANGE-FEASIBLE; AGED-STATE POWER CAPABILITY NOT STATE-RESOLVED`

It must not be reported as:

`FULL TECHNICAL FEASIBILITY CONFIRMED`

If the state-specific range precursor fails the required mobility service,
continuation may be reported as:

`CONTINUE TECHNICALLY INFEASIBLE — RANGE`

because that conclusion does not require an aged-state power model.

## Carbon / Engineering Separation

Carbon classification remains analytically separate from technical
engineering evidence.

A later `ROBUST REPLACE`, `ROBUST CONTINUE`, or
`CARBON DECISION INDETERMINATE` classification must not be presented as
a complete engineering recommendation when aged-state power capability
remains unresolved.

## Q1 Claim Discipline

This limitation must remain visible in:

- Methods;
- Results interpretation;
- Discussion/limitations; and
- the mandatory post-P16R Q1 publication-strength gate.

No DeltaG, identified interval, carbon classification, identification
leverage, or replacement optimization is calculated in P16R-A1D.
"""


spec_text = SPEC.read_text(
    encoding="utf-8"
)

if HEADING in spec_text:
    raise RuntimeError(
        "P16R-A1D STOP — power-evidence addendum already exists."
    )


try:

    with SPEC.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(ADDENDUM)

    # ========================================================
    # 8. VERIFY APPEND-ONLY PREFIX
    # ========================================================

    amended_bytes = SPEC.read_bytes()

    assert (
        hashlib.sha256(
            amended_bytes[:spec_bytes_before]
        ).hexdigest()
        ==
        spec_hash_before
    )

    # ========================================================
    # 9. ARCHITECTURE INTEGRITY TEST
    # ========================================================

    result = subprocess.run(
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

    print("\nP14.6C integrity:")
    print(result.stdout)

    if result.returncode != 0:
        raise RuntimeError(
            "P16R-A1D FAIL — architecture integrity failed."
        )

except Exception:

    # Fail closed:
    # restore exact pre-A1D specification.
    SPEC.write_bytes(
        spec_original_bytes
    )

    raise


spec_hash_after = sha256(SPEC)


# ============================================================
# 10. LOCK RECEIPT
# ============================================================

lock = {
    "stage": "P16R-A1D",

    "final_status":
        "POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS",

    "fresh_battery_max_power_kw":
        battery_max_power_kw,

    "fresh_combined_max_terminal_power_kw":
        fresh_max_terminal_kw,

    "fresh_combined_regen_magnitude_kw":
        fresh_regen_magnitude_kw,

    "fresh_discharge_power_headroom_ratio":
        fresh_discharge_headroom_ratio,

    "range_evidence":
        RANGE_STATUS,

    "fresh_power_evidence":
        FRESH_POWER_STATUS,

    "aged_power_evidence":
        AGED_POWER_STATUS,

    "full_aged_technical_feasibility_claim_allowed":
        False,

    "fresh_headroom_is_aged_power_feasibility":
        False,

    "delta_g_calculated":
        False,

    "decision_bounds_calculated":
        False,

    "carbon_classification_calculated":
        False,

    "identification_leverage_calculated":
        False,

    "replacement_optimization_performed":
        False,

    "implementation_spec": {
        "pre_sha256":
            spec_hash_before,

        "pre_bytes":
            spec_bytes_before,

        "post_sha256":
            spec_hash_after,

        "append_only_prefix_preserved":
            True,
    },
}


LOCK.parent.mkdir(
    parents=True,
    exist_ok=True,
)

LOCK.write_text(
    json.dumps(
        lock,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 11. DECISION LOG
# ============================================================

LOG_HEADING = (
    "## P16R-A1D — Power-Evidence Limitation"
)

LOG_ENTRY = f"""

## P16R-A1D — Power-Evidence Limitation

Stage: P16R-A1D — Power-Evidence Limitation Lock

Decision: POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS

Fresh representative battery maximum power:
{battery_max_power_kw:.6f} kW.

Combined fresh maximum terminal discharge demand:
{fresh_max_terminal_kw:.6f} kW.

Fresh discharge headroom ratio:
{fresh_discharge_headroom_ratio:.6f}.

Scientific consequence: P13 supports state-specific range feasibility
and fresh power-headroom plausibility, but not aged-state maximum power
capability.

Aged-state power capability must therefore remain
`NOT STATE-RESOLVED`.

Fresh power headroom cannot be interpreted as aged power feasibility.

No DeltaG, decision bounds, carbon classification, identification
leverage, or optimization was calculated.

Evidence:
`docs/P16R_A1D_POWER_EVIDENCE_LIMITATION_REPORT.md`
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
# 12. REPORT
# ============================================================

report = f"""# P16R-A1D — Power-Evidence Limitation Report

## Final Status

`POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS`

## Exact P13 Source Path

`representative_vehicle.synthesized_vehicle_parameters.battery_max_power_watts`

## Fresh Power Evidence

Fresh battery maximum power:

`{battery_max_power_kw:.6f} kW`

Combined-cycle maximum discharge terminal demand:

`{fresh_max_terminal_kw:.6f} kW`

Combined-cycle regenerative magnitude:

`{fresh_regen_magnitude_kw:.6f} kW`

Fresh discharge-power headroom ratio:

`{fresh_discharge_headroom_ratio:.6f}`

## Scientific Interpretation

Fresh discharge-power headroom is a plausibility check only.

It is not evidence of aged-state power feasibility.

## State-Resolved Technical Evidence

Range feasibility:

`AVAILABLE`

Fresh power-headroom plausibility:

`AVAILABLE`

Aged-state power capability:

`NOT STATE-RESOLVED`

## Prohibited Inference

The analysis will not invent:

- aged current limits;
- aged BMS cutoff;
- voltage-sag thresholds;
- aged maximum deliverable power; or
- deterministic R/R0-to-power-capability conversion.

## Allowed Technical Language

Where range is sufficient:

`RANGE-FEASIBLE; AGED-STATE POWER CAPABILITY NOT STATE-RESOLVED`

Where range is insufficient:

`CONTINUE TECHNICALLY INFEASIBLE — RANGE`

## Numerical Disclosures

DeltaG calculated: `NO`

Decision bounds calculated: `NO`

Carbon classification calculated: `NO`

Identification leverage calculated: `NO`

Replacement optimization performed: `NO`
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

print("\n" + "=" * 78)

print(
    "POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS"
)

print(
    f"FRESH BATTERY MAX POWER: "
    f"{battery_max_power_kw:.3f} kW"
)

print(
    f"FRESH MAX CYCLE DEMAND: "
    f"{fresh_max_terminal_kw:.3f} kW"
)

print(
    f"FRESH DISCHARGE HEADROOM: "
    f"{fresh_discharge_headroom_ratio:.3f}x"
)

print(
    "STATE-SPECIFIC RANGE FEASIBILITY: AVAILABLE"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print(
    "NO AGED-POWER ASSUMPTION ADDED"
)

print(
    "IMPLEMENTATION_SPEC: APPEND-ONLY AMENDED"
)

print(
    "P14.6C INTEGRITY TESTS: PASS"
)

print(
    "NO DELTAG CALCULATED"
)

print(
    "NO CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)