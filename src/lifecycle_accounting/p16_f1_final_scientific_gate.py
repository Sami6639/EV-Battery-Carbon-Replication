from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "primary":
        ROOT / "results/intermediate/"
        "p16r_c2_primary_carbon_classification.parquet",

    "temporal":
        ROOT / "results/intermediate/"
        "p16r_d3a_temporal_identified_bounds.parquet",

    "mechanism":
        ROOT / "results/intermediate/"
        "p16r_d3b_temporal_mechanism_decomposition.parquet",

    "dual_state":
        ROOT / "results/intermediate/"
        "p16r_d1_dual_state_necessity.parquet",

    "endpoint_leverage":
        ROOT / "results/intermediate/"
        "p16r_d2b1_endpoint_leverage.parquet",

    "packloss_leverage":
        ROOT / "results/intermediate/"
        "p16r_d2b1_packloss_leverage.parquet",

    "resistance_leverage":
        ROOT / "results/intermediate/"
        "p16r_d2b2_resistance_leverage.parquet",

    "r1s":
        ROOT / "results/intermediate/"
        "p16r_d4b_r1s_temporal_bounds.parquet",

    "r10_r1s_compare":
        ROOT / "results/intermediate/"
        "p16r_d4b_r10_r1s_comparison.parquet",

    "mobility":
        ROOT / "results/intermediate/"
        "p16r_d4c_mobility_service_robustness.parquet",

    "operational_context":
        ROOT / "results/intermediate/"
        "p16r_d4d1_operational_context_robustness.parquet",

    "vehicle_age":
        ROOT / "results/intermediate/"
        "p16r_d4d2a_vehicle_age_robustness.parquet",

    "regional_static":
        ROOT / "results/intermediate/"
        "p16r_d4d2b_regional_static_robustness.parquet",

    "lrmer":
        ROOT / "results/intermediate/"
        "p16r_d4e1c_cambium2023_lrmer_sensitivity.parquet",

    "extreme":
        ROOT / "results/intermediate/"
        "p16r_d4e4_extreme_physical_stress.parquet",
}

POWER_LOCK = (
    ROOT
    / "data/metadata/"
    "P16R_A1D_POWER_EVIDENCE_LIMITATION_LOCK.json"
)

Q1_LOCK = (
    ROOT
    / "data/metadata/"
    "P15Q_Q1_NOVELTY_FORMAL_LOCK.json"
)

TEMPORAL_LOCK = (
    ROOT
    / "data/metadata/"
    "P16R_TEMPORAL_CONTEXT_LOCK.json"
)

SOURCE_MANIFEST = (
    ROOT
    / "data/metadata/"
    "SOURCE_MANIFEST.csv"
)

SPEC = ROOT / "docs/IMPLEMENTATION_SPEC.md"

LOG = ROOT / "docs/RESEARCH_DECISION_LOG.md"

REPORT = (
    ROOT
    / "docs/"
    "P16_FINAL_SCIENTIFIC_ANALYSIS_REPORT.md"
)

MANIFEST = (
    ROOT
    / "results/intermediate/"
    "p16_final_scientific_manifest.json"
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


def require_all_robust_continue(df, column="carbon_classification"):
    if column not in df.columns:
        raise RuntimeError(
            f"Missing classification column: {column}"
        )

    bad = df.loc[
        df[column] != "ROBUST CONTINUE"
    ]

    if not bad.empty:
        raise RuntimeError(
            "P16-F1 FAIL — non-ROBUST-CONTINUE "
            f"rows found: {len(bad)}"
        )


print("=" * 78)
print("P16-F1 — FINAL SCIENTIFIC CONSOLIDATION & INTEGRITY GATE")
print("=" * 78)


# ============================================================
# 1. REQUIRED ARTIFACTS
# ============================================================

for name, path in FILES.items():

    if not path.is_file():
        raise RuntimeError(
            f"P16-F1 FAIL — missing {name}: {path}"
        )

for path in [
    POWER_LOCK,
    Q1_LOCK,
    TEMPORAL_LOCK,
    SOURCE_MANIFEST,
    SPEC,
    LOG,
]:
    if not path.is_file():
        raise RuntimeError(
            f"P16-F1 FAIL — missing required file: {path}"
        )


# ============================================================
# 2. LOAD
# ============================================================

data = {
    name: pd.read_parquet(path)
    for name, path in FILES.items()
}

with POWER_LOCK.open(encoding="utf-8") as f:
    power_lock = json.load(f)

with Q1_LOCK.open(encoding="utf-8") as f:
    q1_lock = json.load(f)

with TEMPORAL_LOCK.open(encoding="utf-8") as f:
    temporal_lock = json.load(f)


# ============================================================
# 3. LOCK INTEGRITY
# ============================================================

assert (
    q1_lock["final_status"]
    ==
    "Q1 NOVELTY STRENGTHENING FORMALLY LOCKED — PASS"
)

assert (
    power_lock["final_status"]
    ==
    "POWER-EVIDENCE LIMITATION FORMALLY LOCKED — PASS"
)

assert (
    power_lock["aged_power_evidence"]
    ==
    "AGED_STATE_POWER_CAPABILITY_NOT_STATE_RESOLVED"
)

assert (
    temporal_lock["final_status"]
    ==
    "TEMPORAL DECISION-CONTEXT ARCHITECTURE FORMALLY LOCKED — PASS"
)

assert temporal_lock["decision_calendar_years"] == [
    2025,
    2030,
    2035,
    2040,
    2045,
]


# ============================================================
# 4. PRIMARY RESULT
# ============================================================

primary = data["primary"]

assert len(primary) == 3402
assert primary["context_id"].nunique() == 6
assert primary["current_state_key"].nunique() == 567

require_all_robust_continue(primary)

primary_min_lower = float(
    primary["lower_DeltaG_kgco2e"].min()
)

primary_max_upper = float(
    primary["upper_DeltaG_kgco2e"].max()
)

assert primary_min_lower > 0


# ============================================================
# 5. TEMPORAL RESULT
# ============================================================

temporal = data["temporal"]

assert len(temporal) == 17010
assert temporal["context_id"].nunique() == 30
assert temporal["current_state_key"].nunique() == 567

require_all_robust_continue(temporal)

temporal_min_lower = float(
    temporal["lower_DeltaG_kgco2e"].min()
)

temporal_max_upper = float(
    temporal["upper_DeltaG_kgco2e"].max()
)

assert temporal_min_lower > 0


# ============================================================
# 6. MECHANISM
# ============================================================

mechanism = data["mechanism"]

assert len(mechanism) == 17010

mechanism_min_margin = float(
    mechanism["dominance_margin_kgco2e"].min()
)

max_operational_saving = float(
    mechanism["max_operational_saving_kgco2e"].max()
)

max_saving_fraction = float(
    mechanism[
        "max_operational_saving_fraction_of_manufacturing"
    ].max()
)

positive_ratios = (
    mechanism[
        "manufacturing_to_max_saving_ratio"
    ]
    .dropna()
)

minimum_mfg_to_saving_ratio = (
    float(positive_ratios.min())
    if not positive_ratios.empty
    else None
)

assert mechanism_min_margin > 0


# ============================================================
# 7. DUAL-STATE RESULT
# ============================================================

dual = data["dual_state"]

supported_dual = int(
    dual["dual_state_support_sufficient"].sum()
)

dual_discordance = int(
    dual["classification_discordance"].sum()
)

assert supported_dual == 2916
assert dual_discordance == 0

assert not dual[
    "capacity_only_sufficiency_proven"
].any()


# ============================================================
# 8. IDENTIFICATION LEVERAGE
# ============================================================

packloss = data["packloss_leverage"]
resistance = data["resistance_leverage"]

packloss_guaranteed_max = float(
    packloss["L_guaranteed_kgco2e"].max()
)

packloss_potential_max = float(
    packloss["L_potential_kgco2e"].max()
)

res_supported = resistance.loc[
    resistance["support_sufficient"]
].copy()

resistance_guaranteed_max = float(
    res_supported["L_guaranteed_kgco2e"].max()
)

resistance_potential_max = float(
    res_supported["L_potential_kgco2e"].max()
)

assert int(
    packloss["guaranteed_sign_recovery"].sum()
) == 0

assert int(
    packloss["potential_sign_recovery"].sum()
) == 0

assert int(
    res_supported["guaranteed_sign_recovery"].sum()
) == 0

assert int(
    res_supported["potential_sign_recovery"].sum()
) == 0


# ============================================================
# 9. R1S STRUCTURAL ROBUSTNESS
# ============================================================

r1s = data["r1s"]
compare = data["r10_r1s_compare"]

assert len(r1s) == 17010

require_all_robust_continue(r1s)

r1s_min_lower = float(
    r1s["lower_DeltaG"].min()
)

r1s_reversals = int(
    compare["classification_reversal"].sum()
)

assert r1s_min_lower > 0
assert r1s_reversals == 0


# ============================================================
# 10. MOBILITY TECHNICAL ROBUSTNESS
# ============================================================

mobility = data["mobility"]

assert len(mobility) == 1701

mobility_infeasible = int(
    (~mobility["range_feasible"]).sum()
)

assert mobility_infeasible == 0

assert not mobility[
    "full_technical_feasibility_confirmed"
].any()


# ============================================================
# 11. MILEAGE / SURVIVAL / CHARGING
# ============================================================

operational = data["operational_context"]

assert len(operational) == 5103

require_all_robust_continue(operational)

operational_min_lower = float(
    operational["lower_DeltaG"].min()
)

assert operational_min_lower > 0


# ============================================================
# 12. VEHICLE AGE
# ============================================================

age = data["vehicle_age"]

assert len(age) == 26 * 567

require_all_robust_continue(age)

age_min_lower = float(
    age["lower_DeltaG"].min()
)

assert age_min_lower > 0


# ============================================================
# 13. REGIONAL GRID + STATIC MANUFACTURING
# ============================================================

regional_static = data["regional_static"]

require_all_robust_continue(regional_static)

regional = regional_static.loc[
    regional_static["structural_family"]
    == "REGIONAL_GRID"
].copy()

static = regional_static.loc[
    regional_static["structural_family"]
    == "STATIC_MANUFACTURING"
].copy()

assert regional["structural_member"].nunique() == 18
assert regional["current_state_key"].nunique() == 567
assert static["current_state_key"].nunique() == 567

regional_min_lower = float(
    regional["lower_DeltaG"].min()
)

static_min_lower = float(
    static["lower_DeltaG"].min()
)

assert regional_min_lower > 0
assert static_min_lower > 0


# ============================================================
# 14. CAMBIUM-2023 LRMER
# ============================================================

lrmer = data["lrmer"]

assert len(lrmer) == 81648
assert lrmer["lrmer_scenario"].nunique() == 8
assert lrmer["gea_region"].nunique() == 18

require_all_robust_continue(lrmer)

lrmer_reversals = int(
    lrmer[
        "classification_reversal_vs_primary_average"
    ].sum()
)

lrmer_min_lower = float(
    lrmer["lower_DeltaG"].min()
)

assert lrmer_reversals == 0
assert lrmer_min_lower > 0

assert not lrmer[
    "project_selected_gwp"
].any()

assert not lrmer[
    "national_lrmer_aggregation"
].any()


# ============================================================
# 15. EXTREME / CONDITIONAL PHYSICAL STRESS
# ============================================================

extreme = data["extreme"]

assert len(extreme) == 1080

require_all_robust_continue(extreme)

extreme_min_lower = float(
    extreme["lower_DeltaG"].min()
)

extreme_reversals = int(
    (
        extreme["carbon_classification"]
        != "ROBUST CONTINUE"
    ).sum()
)

assert extreme_reversals == 0
assert extreme_min_lower > 0

assert not extreme["headline_eligible"].any()
assert not extreme["primary_domain_member"].any()


# ============================================================
# 16. XU / RECYCLING SOURCE STATUS
# ============================================================

source_manifest = pd.read_csv(
    SOURCE_MANIFEST
)

required_source_ids = [
    "SRC_XU_2022",
    "SRC_HANNA_2025",
    "SRC_DU_2022",
]

source_limitations = {}

for source_id in required_source_ids:

    row = source_manifest.loc[
        source_manifest["source_id"] == source_id
    ]

    if len(row) != 1:
        raise RuntimeError(
            f"P16-F1 FAIL — manifest row issue: {source_id}"
        )

    record = row.iloc[0]

    source_limitations[source_id] = {
        "acquisition_status":
            str(
                record.get(
                    "acquisition_status",
                    ""
                )
            ),

        "access_status":
            str(
                record.get(
                    "access_status",
                    ""
                )
            ),

        "raw_storage_path":
            str(
                record.get(
                    "raw_storage_path",
                    ""
                )
            ),

        "numerically_implemented_in_p16":
            False,
    }


# ============================================================
# 17. ARCHITECTURE INTEGRITY
# ============================================================

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

print("\nP14.6C architecture integrity:")
print(test.stdout)

if test.returncode != 0:
    raise RuntimeError(
        "P16-F1 FAIL — architecture integrity failed."
    )


# ============================================================
# 18. ARTIFACT HASH MANIFEST
# ============================================================

artifact_records = []

for name, path in FILES.items():

    artifact_records.append(
        {
            "name": name,
            "path": str(
                path.relative_to(ROOT)
            ),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )


# ============================================================
# 19. FINAL MACHINE-READABLE MANIFEST
# ============================================================

final_manifest = {
    "stage": "P16",

    "final_status":
        "P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — "
        "READY FOR Q1 PUBLICATION-STRENGTH GATE",

    "primary": {
        "rows": len(primary),
        "contexts": int(
            primary["context_id"].nunique()
        ),
        "states": int(
            primary["current_state_key"].nunique()
        ),
        "classification":
            "ROBUST CONTINUE",
        "minimum_lower_DeltaG_kgco2e":
            primary_min_lower,
        "maximum_upper_DeltaG_kgco2e":
            primary_max_upper,
    },

    "temporal": {
        "decision_years": [
            2025,
            2030,
            2035,
            2040,
            2045,
        ],
        "contexts": 30,
        "classification":
            "ROBUST CONTINUE",
        "minimum_lower_DeltaG_kgco2e":
            temporal_min_lower,
        "maximum_upper_DeltaG_kgco2e":
            temporal_max_upper,
    },

    "mechanism": {
        "maximum_operational_saving_kgco2e":
            max_operational_saving,
        "minimum_dominance_margin_kgco2e":
            mechanism_min_margin,
        "maximum_operational_saving_fraction_of_manufacturing":
            max_saving_fraction,
        "minimum_manufacturing_to_operational_saving_ratio":
            minimum_mfg_to_saving_ratio,
    },

    "dual_state": {
        "supported_rows":
            supported_dual,
        "classification_discordance_rows":
            dual_discordance,
        "capacity_only_sufficiency_proven":
            False,
    },

    "identification_leverage": {
        "packloss_guaranteed_max_kgco2e":
            packloss_guaranteed_max,
        "packloss_potential_max_kgco2e":
            packloss_potential_max,
        "resistance_guaranteed_max_kgco2e":
            resistance_guaranteed_max,
        "resistance_potential_max_kgco2e":
            resistance_potential_max,
        "sign_recovery_observed":
            False,
        "headline_bottleneck_claim":
            False,
    },

    "structural_robustness": {
        "r1s_classification_reversals":
            r1s_reversals,
        "r1s_minimum_lower_DeltaG_kgco2e":
            r1s_min_lower,
        "mobility_range_infeasible_rows":
            mobility_infeasible,
        "operational_context_minimum_lower_DeltaG_kgco2e":
            operational_min_lower,
        "vehicle_age_minimum_lower_DeltaG_kgco2e":
            age_min_lower,
        "regional_grid_minimum_lower_DeltaG_kgco2e":
            regional_min_lower,
        "static_manufacturing_minimum_lower_DeltaG_kgco2e":
            static_min_lower,
        "lrmer_minimum_lower_DeltaG_kgco2e":
            lrmer_min_lower,
        "lrmer_classification_reversals":
            lrmer_reversals,
        "extreme_minimum_lower_DeltaG_kgco2e":
            extreme_min_lower,
        "extreme_classification_reversals":
            extreme_reversals,
    },

    "technical_limitations": {
        "aged_state_power_capability":
            "NOT STATE-RESOLVED",
        "full_engineering_recommendation_allowed":
            False,
    },

    "unimplemented_prespecified_robustness": {
        "SRC_XU_2022":
            source_limitations["SRC_XU_2022"],
        "SRC_HANNA_2025":
            source_limitations["SRC_HANNA_2025"],
        "SRC_DU_2022":
            source_limitations["SRC_DU_2022"],
    },

    "replacement_optimization_performed":
        False,

    "time_to_state_used":
        False,

    "architecture_integrity_tests":
        "PASS",

    "artifacts":
        artifact_records,
}


MANIFEST.parent.mkdir(
    parents=True,
    exist_ok=True,
)

MANIFEST.write_text(
    json.dumps(
        final_manifest,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# 20. FINAL SCIENTIFIC REPORT
# ============================================================

report = f"""# P16 — Final Scientific Analysis Report

## Final Status

`P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — READY FOR Q1 PUBLICATION-STRENGTH GATE`

## Primary Result

Primary identified-set rows: {len(primary):,}

Primary matched contexts: {primary["context_id"].nunique()}

Current physical states: {primary["current_state_key"].nunique()}

Primary carbon classification:

`ROBUST CONTINUE`

Minimum primary lower DeltaG:

`{primary_min_lower:.6f} kg CO2e`

Maximum primary upper DeltaG:

`{primary_max_upper:.6f} kg CO2e`

## Temporal Context Modulation

Locked decision years:

2025, 2030, 2035, 2040, 2045.

Matched temporal contexts:

30.

All temporal state-context results:

`ROBUST CONTINUE`

Global temporal minimum lower DeltaG:

`{temporal_min_lower:.6f} kg CO2e`

Calendar year remains an exogenous context and is not interpreted as time-to-state.

## Mechanism

Maximum admissible operational-carbon saving:

`{max_operational_saving:.6f} kg CO2e`

Minimum replacement-manufacturing dominance margin:

`{mechanism_min_margin:.6f} kg CO2e`

Maximum operational-saving fraction of replacement manufacturing:

`{max_saving_fraction:.9f}`

Minimum manufacturing-to-operational-saving ratio:

`{minimum_mfg_to_saving_ratio:.6f}`

The observed carbon dominance is therefore associated with the asymmetry
between replacement-battery manufacturing burden and the much smaller
degradation-related operational-carbon saving available inside the
supported state domain.

## Dual-State Result

Matched-capacity dual-state support rows:

{supported_dual:,}

Observed classification discordance:

{dual_discordance}

Resistance changes identified intervals but does not produce an observed
primary classification reversal.

Absence of discordance is not interpreted as universal proof that
capacity-only SOH is sufficient.

## Identification Leverage

Pack-loss guaranteed leverage maximum:

`{packloss_guaranteed_max:.9f} kg CO2e`

Pack-loss potential leverage maximum:

`{packloss_potential_max:.9f} kg CO2e`

Resistance guaranteed leverage maximum:

`{resistance_guaranteed_max:.9f} kg CO2e`

Resistance potential leverage maximum:

`{resistance_potential_max:.9f} kg CO2e`

No sign recovery was produced by these evidence-resolution layers.

Identification leverage is therefore retained as a supporting
mechanistic/uncertainty analysis rather than forced into a headline
bottleneck claim.

## Structural Robustness

R1s temporal classification reversals:

{r1s_reversals}

Mobility-service range-infeasible rows:

{mobility_infeasible}

Regional GEA regions tested:

18/18.

Cambium-2023 LRMER scenario-region contexts:

144/144.

Cambium-2023 LRMER classification reversals:

{lrmer_reversals}

Extreme/conditional stress classification reversals:

{extreme_reversals}

Extreme minimum lower DeltaG:

`{extreme_min_lower:.6f} kg CO2e`

## Technical Evidence Limitation

State-specific range feasibility is available and all locked mobility
service requirements remained range-feasible in the supported primary
domain.

Aged-state power capability is:

`NOT STATE-RESOLVED`

Therefore the carbon result must not be presented as a complete
engineering replacement recommendation.

## Pre-Specified Robustness Not Numerically Implemented in P16

- Xu et al. 2022 manufacturing robustness source.
- Hanna et al. 2025 recycling-process source.
- Du et al. 2022 recycling-allocation source.

These sources were registered but their numerical supporting artifacts
were not part of the frozen processed evidence available for P16.

They are not represented as completed sensitivities.

## Claim Discipline

No degradation trajectory was generated.

No time-to-state relationship was inferred.

No replacement-time optimization was performed.

No population prevalence interpretation was assigned to the physical
state space.

Extreme/conditional evidence is not headline-eligible.

## Next Gate

A mandatory post-P16 WoS-Q1 publication-strength and novelty review
must be completed before manuscript drafting.
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
# 21. DECISION LOG
# ============================================================

HEADING = (
    "## P16 — Final Scientific Analysis"
)

if HEADING not in LOG.read_text(
    encoding="utf-8"
):

    with LOG.open(
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            f"""

{HEADING}

Decision: P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — READY FOR Q1 PUBLICATION-STRENGTH GATE

Primary result: ROBUST CONTINUE across all 3,402 primary state-context rows.

Temporal result: ROBUST CONTINUE across all 17,010 locked 2025–2045 temporal state-context rows.

R10/R1s classification reversals: 0.

Cambium-2023 LRMER classification reversals: 0.

Extreme/conditional physical-stress classification reversals: 0.

Aged-state power capability remains NOT STATE-RESOLVED.

Xu 2022 and Hanna/Du recycling sources were preregistered but were not numerically implemented because processed numerical artifacts were unavailable in the frozen P16 evidence.

No time-to-state inference or replacement optimization was performed.

Evidence: `docs/P16_FINAL_SCIENTIFIC_ANALYSIS_REPORT.md`
"""
        )


# ============================================================
# 22. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 78)

print(
    "P16 SCIENTIFIC ANALYSIS COMPLETE WITH BOUNDS — "
    "READY FOR Q1 PUBLICATION-STRENGTH GATE"
)

print(
    "PRIMARY: 3402/3402 ROBUST CONTINUE"
)

print(
    "TEMPORAL 2025–2045: 17010/17010 ROBUST CONTINUE"
)

print(
    "R10/R1S CLASSIFICATION REVERSALS: 0"
)

print(
    "MOBILITY RANGE-INFEASIBLE PRIMARY STATES: 0"
)

print(
    "REGIONAL GRID: 18/18 TESTED"
)

print(
    "CAMBIUM-2023 LRMER: 144/144 CONTEXTS TESTED"
)

print(
    "LRMER CLASSIFICATION REVERSALS: 0"
)

print(
    "EXTREME/CONDITIONAL CLASSIFICATION REVERSALS: 0"
)

print(
    "AGED-STATE POWER CAPABILITY: NOT STATE-RESOLVED"
)

print(
    "XU 2022 NUMERICAL ROBUSTNESS: NOT IMPLEMENTED"
)

print(
    "RECYCLING NUMERICAL SENSITIVITY: NOT IMPLEMENTED"
)

print(
    "P14.6C ARCHITECTURE INTEGRITY: PASS"
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