# IMPLEMENTATION_SPEC P14.5S Revision Proposal

**Status:** PROPOSED ONLY — NOT AUTHORITATIVE  
**Stage:** P14.5S — R3 METHODOLOGICAL REVISION SPECIFICATION & SOURCE FREEZE  
**Date frozen:** 2026-08-21  
**Governing specification:** `docs/IMPLEMENTATION_SPEC.md` remains authoritative until an explicit later gate accepts this proposal.  
**Implementation status:** no R3 bridge, trajectory, lifecycle calculation, or optimization is implemented here.

## Change-control purpose

This document proposes the minimum bounded revision needed to make R3 — HYBRID BOUNDED MAPPING implementable without erasing the P14.5 failure. It does not amend historical decisions. P14.5 remains `REAL-WORLD DEGRADATION BRIDGE FAIL`; P14.5R remains an evidence-expansion candidate with bounds.

The three mandatory scientific phrases are:

- **modeled real-world capacity trajectory**;
- **conditional resistance-state envelope**;
- **real-world resistance trajectory unidentified**.

The prohibited claim is: **“real-world resistance trajectory was identified.”**

## Proposed source roles

| Source | Proposed role | Permitted use | Prohibited use |
|---|---|---|---|
| BLAST-Lite, pinned commit `b093495...` | `CANDIDATE_CAPACITY_BRIDGE_MODEL` | Source-native capacity-retention projections within model domain | Field truth, pack validation, deterministic resistance |
| Wu et al. 2026 | `MODEL_APPLICATION_AND_EXPOSURE_ARCHITECTURE` | Method support for operating/charging/parked states and cell-temperature coupling | Exact project life history, model calibration, field validation |
| Liu et al. 2025 | `PRIMARY_FIELD_CAPACITY_VALIDATION` | External NCM capacity check | BLAST fitting; fully reproducible ground truth; resistance |
| Deng et al. 2023 | `OPEN_FIELD_CAPACITY_VALIDATION` | Open external NCM pack-capacity check | BLAST fitting; parked-state reconstruction; resistance |
| Qiushi Wang et al. 2023 | `NON_EXECUTABLE_FIELD_METHOD_VALIDATION` | Method corroboration only | NMC validation, executable validation, fitting |
| Luh | Existing frozen role unchanged | P12 physical degradation state space | Additive lifetime capacity component |
| Schreiber | Existing frozen role unchanged | Automotive dual-state validation | Central-envelope definition by extreme states |

The five new rows are appended to `data/metadata/SOURCE_MANIFEST.csv`. No previous row or role is rewritten.

## Proposed capacity bridge

### Eligibility

A model is eligible only when chemistry is sufficiently compatible, calendar and cycling ageing are explicit, temperature and SOC dependence exist, required inputs are reproducible, source parameters are inspectable, no essential proprietary input exists, and output is physical capacity retention or can be converted without arbitrary assumptions.

The machine-readable ruling is `data/metadata/P145S_BLAST_NMC_MODEL_ELIGIBILITY.csv`.

### Primary family and envelope

Pre-selected primary family, before any field-model comparison:

1. `Nmc622_Gr_DENSO50Ah_Battery`;
2. `Nmc811_GrSi_LGMJ1_4Ah_Battery`.

Conditional structural sensitivities are the commercial NMC A/B1/B2 classes and LG M50, only inside their narrower source domains. NMC111 classes and NMC-LTO are excluded from the project-primary capacity family for chemistry, era, stress-coverage, or anode incompatibility.

Every eligible primary model is retained as a distinct member of an **ELIGIBLE NMC MODEL ENVELOPE**. Outputs are not averaged into a pseudo-model. No member is selected, weighted, calibrated, or discarded after observing Liu, Deng, carbon, replacement, or optimization outcomes. Source-native parameters are used with `degradation_scalar = 1`.

The model supplies a **modeled real-world capacity trajectory** only. Capacity states outside any member's declared input domain fail closed for that member. If no primary member supports a state, capacity is unsupported.

### Calendar/use interaction

Each BLAST model's own state equations define calendar/cycling interaction or combination. No external sum of a Luh calendar curve and a BLAST cycle curve is allowed. Luh remains P12 validation/state-space evidence.

### Projection label

Every state beyond the direct duration covered by independent field validation must carry exactly:

`MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION`

BLAST's qualitative warning for extrapolation of accelerated cell models to 10+ years remains operational. A computable time horizon is not an empirical validation horizon.

## Proposed exposure generator

### Candidate decision

- E1, Wu-style representative daily profile: retained as method reference, rejected as primary because a single profile over-identifies one exact life and the deposited core pipeline is incomplete.
- E2, bounded duty-cycle family preserving annual mileage: **selected**.
- E3, stochastic generator: rejected because P14 supplies no source-supported joint empirical distribution for the required states.

### E2 contract

The generator creates 15-minute `driving`, `charging`, and `parked_not_charging` states, then aggregates to hourly BLAST inputs. Annual distance is exactly one of P14's frozen values: 3,218.688; 10,729.496448; or 19,312.128 km/year. Distance and equivalent-full-cycle throughput must agree before/after aggregation within 0.5%.

Seven dimensions remain explicit: annual mileage, cell temperature, parked SOC, charging frequency, charging rate, parked duration, and thermal-management behaviour. The design is 17 profiles: one anchor; low/high one-factor bounds for each dimension; and two coherent joint-stress bundles. A full Cartesian grid is prohibited unless a later change-control gate justifies it.

Charging policies are pre-selected from the Wu architecture: immediate, balanced, and home 23:00–08:00. Nominal charger levels are home 3.7 kW, workplace 11 kW, and public 22 kW. Fast charging at 75/150 kW is sensitivity-only and must be required by the energy balance, not selected after degradation results.

Parked SOC emerges from energy balance and the frozen charging policy. It is summarized as time shares in `[0,0.3)`, `[0.3,0.7]`, and `(0.7,1.0]`; a low parked SOC cannot be selected because it reduces degradation.

Cell temperature, not ambient temperature, is passed to BLAST. A documented thermal layer must convert ambient/solar/operating states to cell temperature. If the Wu/TUM layer cannot be independently reproduced, bounded cell-temperature proxies are permitted only with their source, time resolution, thermal-management class, and validity range recorded. Ambient temperature is never substituted directly.

## Proposed independent field validation

BLAST parameters remain source-native. Liu and Deng are external validation and cannot simultaneously select/tune the model. Qiushi Wang is method corroboration only.

If a later diagnostic/confirmation split is required, whole vehicles are ordered by SHA-256 of `source_id|vehicle_id`: first 60% diagnostic, last 40% untouched confirmation. Rows from one vehicle never cross partitions. No field record enters parameter fitting in this revision.

Liu is classified exactly as **FIELD VALIDATION WITH LABEL-REPRODUCIBILITY LIMITATION**. The withheld OEM/supplier OCV–SOC table prevents exact reconstruction of published capacity labels; therefore Liu cannot by itself confer an unbounded PASS. Missing BMS-off parked periods also prevent exposure reconstruction.

Metrics are absolute retention error, median absolute error (MdAE), signed median bias, error by age/use stratum, observed coverage by the non-averaged model envelope, and median envelope width. R² is not an acceptance metric.

Age strata are `[0,1]`, `(1,2]`, `(2,3]`, and `>3` years. Use strata are source-specific cumulative-mileage tertiles frozen before outcome comparison. A stratum is scored at `n >= 20` comparable observations.

### Pre-registered thresholds

| Status | Overall MdAE | Absolute bias | Every scored-stratum MdAE | Envelope coverage | Median envelope width |
|---|---:|---:|---:|---:|---:|
| PASS | ≤3.0 pp | ≤1.5 pp | ≤4.0 pp | ≥80% | ≤10.0 pp |
| PASS WITH BOUNDS | ≤5.0 pp | ≤3.0 pp | ≤7.0 pp | ≥60% | ≤15.0 pp |
| FAIL | any bounded threshold missed | or | any source-specific FAIL | or >50% domain-invalid comparable points | or input/chemistry incompatibility |

Overall status is the worst source-specific status. The 3 pp target exceeds Liu's reported 0.60% laboratory label-check MAPE yet remains practically material; 5 pp accommodates field/partial-charge uncertainty. Width limits prevent trivial apparent coverage. Liu's ceiling is PASS WITH BOUNDS unless its label reconstruction dependency is independently resolved.

## Proposed resistance treatment

BLAST capacity-eligible mid/high-Ni classes provide capacity, not a project-compatible resistance endpoint. NMC111 implementations with relative 10-second DC resistance are chemically and temporally incompatible with frozen R10/R1s endpoints.

`BLAST REAL-WORLD RESISTANCE OUTPUT = NOT AVAILABLE / NOT APPROVED`

The bridge must never infer resistance from capacity fade. The only permitted object is a **conditional resistance-state envelope**; the **real-world resistance trajectory unidentified** invariant remains true.

For each modeled capacity state:

1. Match only against P12 Luh observations at compatible reference temperature, SOC, and ageing/stress class.
2. Use a fixed symmetric capacity-retention window of ±0.025; never widen it.
3. Require at least 10 observations, 3 cells, and 2 experimental conditions.
4. Calculate the central 10th–90th percentile envelope separately for `R10/R10_0` and `R1s/R1s_0`.
5. Compatible Schreiber observations may expand an outer automotive envelope. Contact-sensitive commuter states and highway post-knee states remain `EXTREME / CONDITIONAL` and never define the central envelope.
6. Do not interpolate gaps, clip tails, substitute timescales, or report an interval midpoint as R(t).
7. If any support condition fails, return exactly `RESISTANCE STATE UNSUPPORTED`.

Primary is the 10-ms R10 envelope. The 1-s R1s envelope is an alternative. They are never averaged and never switched to fill support.

P13 may later consume a modeled capacity state plus every admissible R10 bound only after both pass their own validity checks. P13 is unchanged and no energy penalty is calculated here.

## Proposed false-optimum gate

A later replacement optimum is NON-ROBUST if it:

- depends on one BLAST model when another eligible NMC model reverses it;
- appears only beyond direct field-validation duration;
- depends on `RESISTANCE STATE UNSUPPORTED` regions;
- relies only on extreme Schreiber states;
- depends on one arbitrary parked-SOC or temperature assumption;
- requires tail clipping or deterministic capacity-to-resistance inference;
- relies on an unvalidated 10–25-year projection; or
- disappears under reasonable capacity/resistance structural bounds.

These rules precede and cannot be relaxed after carbon results.

## Proposed RQ interpretation

`RQ PRESERVED — INTERPRETATION BOUNDED`

The scientific question remains replacement timing, but any later answer is conditional on admissible capacity-model and resistance-state uncertainty. It is not an empirically observed deterministic R(t) analysis.

## Explicit non-actions

Lifecycle GHG Calculated: NONE  
Replacement Optimization Performed: NONE  
Scientific Bridge Implemented: NONE  
Existing P12/P13/P14 Scientific Outputs Modified: NONE  
P14.5 Failure Record Removed: NO