from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

AUDIT = (
    ROOT
    / "results"
    / "intermediate"
    / "p16r_d2b0t_temporal_context_audit.parquet"
)

SPEC = ROOT / "docs" / "IMPLEMENTATION_SPEC.md"
LOG = ROOT / "docs" / "RESEARCH_DECISION_LOG.md"

LOCK = (
    ROOT
    / "data"
    / "metadata"
    / "P16R_TEMPORAL_CONTEXT_LOCK.json"
)

REPORT = (
    ROOT
    / "docs"
    / "P16R_TEMPORAL_CONTEXT_LOCK_REPORT.md"
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
print("P16R-D2B0T2 — TEMPORAL CONTEXT FORMAL LOCK")
print("=" * 78)


# ============================================================
# 1. VERIFY AUDIT
# ============================================================

audit = pd.read_parquet(AUDIT)

EXPECTED_YEARS = [
    2025,
    2030,
    2035,
    2040,
    2045,
]

actual_years = (
    audit.loc[
        audit["temporal_context_supported"],
        "decision_calendar_year",
    ]
    .astype(int)
    .tolist()
)

assert actual_years == EXPECTED_YEARS

assert audit["temporal_context_supported"].all()
assert audit["no_grid_extrapolation"].all()
assert audit["no_manufacturing_extrapolation"].all()

assert not audit["time_to_state_interpretation"].any()
assert not audit["degradation_state_assigned_by_year"].any()
assert not audit["carbon_calculated"].any()


# ============================================================
# 2. APPEND-ONLY SPEC LOCK
# ============================================================

spec_before = SPEC.read_bytes()
spec_hash_before = hashlib.sha256(spec_before).hexdigest()
spec_bytes_before = len(spec_before)

HEADING = (
    "# P16R — APPROVED TEMPORAL DECISION-CONTEXT ARCHITECTURE"
)

ADDENDUM = """

---

# P16R — APPROVED TEMPORAL DECISION-CONTEXT ARCHITECTURE

**Status:** FORMALLY LOCKED BEFORE TEMPORAL CONTEXT-MODULATION RESULTS

The prospective trajectory-free analysis uses the following
source-supported decision-calendar contexts:

- 2025
- 2030
- 2035
- 2040
- 2045

These years are matched exogenous decision contexts `z`.

They must never be interpreted as:

- predicted battery retirement years;
- time-to-state;
- mileage-to-state;
- expected time at which a battery reaches a given degradation state.

For every decision year:

- degradation state remains independently conditioned;
- grid CI uses only source-supported calendar values through 2050;
- replacement-battery manufacturing uses the same decision-year
  calendar context;
- no grid extrapolation beyond 2050 is allowed;
- no manufacturing extrapolation is allowed;
- residual vehicle service is truncated consistently at 2050.

The temporal analysis is `CONTEXT MODULATION`.

It is analytically separate from identification leverage.

A decision year cannot be selected or removed after inspecting carbon
classification results merely to strengthen a preferred conclusion.

2050 is not included as a primary decision context because it provides
no meaningful prospective operating horizon within the frozen
source-supported 2050 boundary.

No new carbon result was calculated when this calendar set was locked.
"""


if HEADING in SPEC.read_text(encoding="utf-8"):
    raise RuntimeError(
        "P16R-D2B0T2 STOP — temporal context lock already exists."
    )


try:
    with SPEC.open("a", encoding="utf-8") as f:
        f.write(ADDENDUM)

    amended = SPEC.read_bytes()

    assert (
        hashlib.sha256(
            amended[:spec_bytes_before]
        ).hexdigest()
        == spec_hash_before
    )

    test = subprocess.run(
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

    print("\nArchitecture integrity:")
    print(test.stdout)

    if test.returncode != 0:
        raise RuntimeError(
            "P16R-D2B0T2 FAIL — architecture integrity test failed."
        )

except Exception:
    SPEC.write_bytes(spec_before)
    raise


# ============================================================
# 3. MACHINE-READABLE LOCK
# ============================================================

lock = {
    "stage": "P16R-D2B0T2",

    "final_status":
        "TEMPORAL DECISION-CONTEXT ARCHITECTURE FORMALLY LOCKED — PASS",

    "decision_calendar_years":
        EXPECTED_YEARS,

    "analysis_role":
        "CONTEXT MODULATION",

    "time_to_state_interpretation":
        False,

    "degradation_state_assigned_by_year":
        False,

    "grid_extrapolation":
        False,

    "manufacturing_extrapolation":
        False,

    "operational_horizon_end":
        2050,

    "post_result_year_selection_allowed":
        False,

    "new_carbon_result_calculated":
        False,

    "implementation_spec": {
        "pre_sha256":
            spec_hash_before,

        "post_sha256":
            sha256(SPEC),

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
# 4. DECISION LOG
# ============================================================

LOG_HEADING = (
    "## P16R — Temporal Decision-Context Architecture"
)

if LOG_HEADING not in LOG.read_text(encoding="utf-8"):

    with LOG.open("a", encoding="utf-8") as f:
        f.write(
            """

## P16R — Temporal Decision-Context Architecture

Decision: TEMPORAL DECISION-CONTEXT ARCHITECTURE FORMALLY LOCKED — PASS

Decision calendar years:
2025, 2030, 2035, 2040, 2045.

Scientific role:
CONTEXT MODULATION.

Calendar year is an exogenous decision context and is not time-to-state.

No degradation state is assigned by calendar year.

Grid/manufacturing extrapolation: NONE.

No temporal carbon result was calculated before locking this calendar set.
"""
        )


# ============================================================
# 5. REPORT
# ============================================================

report = """# P16R — Temporal Decision-Context Lock

## Final Status

`TEMPORAL DECISION-CONTEXT ARCHITECTURE FORMALLY LOCKED — PASS`

## Locked Decision Years

- 2025
- 2030
- 2035
- 2040
- 2045

## Interpretation

Decision year is an exogenous context.

It is not time-to-state or predicted battery age.

## Source Support

Grid support: PASS

Manufacturing support: PASS

Survival follow-up support: PASS

Grid extrapolation: NONE

Manufacturing extrapolation: NONE

## Analytical Role

`CONTEXT MODULATION`

Identification-leverage interpretation: PROHIBITED

## Numerical Disclosure

New carbon result calculated: NO
"""


REPORT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT.write_text(
    report,
    encoding="utf-8",
)


print("\n" + "=" * 78)

print(
    "TEMPORAL DECISION-CONTEXT ARCHITECTURE FORMALLY LOCKED — PASS"
)

print(
    "DECISION YEARS: 2025 / 2030 / 2035 / 2040 / 2045"
)

print(
    "TEMPORAL ROLE: CONTEXT MODULATION"
)

print(
    "TIME-TO-STATE INTERPRETATION: PROHIBITED"
)

print(
    "POST-RESULT YEAR SELECTION: PROHIBITED"
)

print(
    "GRID / MANUFACTURING EXTRAPOLATION: NONE"
)

print(
    "IMPLEMENTATION_SPEC: APPEND-ONLY AMENDED"
)

print(
    "NO NEW CARBON RESULT CALCULATED"
)

print("=" * 78)