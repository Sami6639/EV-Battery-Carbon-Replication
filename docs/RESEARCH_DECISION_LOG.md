# Research Decision Log


## P09 &mdash; Implementation Baseline

Stage: P09 &mdash; Implementation Baseline

Decision: IMPLEMENTATION BASELINE PASS

Evidence: `docs/IMPLEMENTATION_BASELINE_REPORT.md`

Scientific consequence: Frozen implementation specification may proceed to controlled source acquisition.

## P10 — Frozen Source Acquisition

Stage: Frozen Source Acquisition

Decision: RAW DATA PROVENANCE PASS

Evidence: `docs/DATA_ACQUISITION_REPORT.md`

## P10.5 — Controlled Staged Acquisition

Stage: Controlled Staged Acquisition

Decision: CORE STAGED DATA READY

Evidence: `docs/STAGED_CORE_DATA_REPORT.md`


## P11 — Canonical Schema, Lossless Extraction & Reproducible Preprocessing

Stage: Canonical Schema, Lossless Extraction & Reproducible Preprocessing

Decision: CANONICAL PREPROCESSING FAIL

Evidence: docs/P11_PREPROCESSING_REPORT.md

Reason: The staged Cambium 2024 workbook contains LRMER rather than the frozen primary average-grid-CI metric, and the three selected TUM HPPC MATLAB MCOS tables could not be parsed reproducibly in the staged environment.

## P11R — Blocker Resolution & Canonical Preprocessing Recovery

Stage: P11R Technical Recovery

Decision: CANONICAL PREPROCESSING RECOVERED — PASS

Technical change control: `FORMAT-LEVEL RECOVERY — SCIENTIFIC SOURCE UNCHANGED`; Cambium correction classified as `SOURCE RESOURCE / METRIC RESOLUTION` within Cambium 2024.

Evidence: `docs/P11R_BLOCKER_RESOLUTION_REPORT.md`

Reason: Official Cambium 2024 Scenario Viewer annual GEA data supplied verified `aer_load_co2e`; official TUM CSV equivalents supplied the same selected 0/20/40 °C HPPC experiments. Two complete raw-to-canonical runs were byte-deterministic, all previous raw checksums remained unchanged, and the full test suite passed.

## P12 — NMC Degradation-State Construction & Automotive Validation

Stage: P12 — NMC Degradation-State Construction & Automotive Validation

Decision: NMC DEGRADATION STATE VALIDATED WITH BOUNDS

Baseline rule: `luh_same_cell_soc_rt_first_valid_v1`; first valid source-identified RT pulse check-up for the same cell and SOC at 25 ± 0.5°C. All 1,140 cell-SOC baselines were present.

Primary resistance definition: `R10_rel = R10 / same-cell same-SOC R10_0` at the 10-ms source timescale; primary reporting basis 50% SOC and 25°C.

Alternative resistance definition: separate `R1s_rel = R1s / same-cell same-SOC R1s_0`; never mixed with the 10-ms specification.

Selected representation family: cell-balanced, observed-domain, bounded-monotone isotonic/PAVA central representation with empirical uncertainty layers and zero extrapolation. Source-supplied capacity SOH remains separate from reconstructed capacity retention.

Automotive validation status: `PASS WITH BOUNDS`. Schreiber commuter/highway capacity and resistance directions are compatible, but matched-capacity automotive resistance magnitudes and the highway post-knee/contact-sensitive states require conditional bounds. TUM ID.3 remains fresh HPPC plausibility evidence only.

Envelope rules: primary 10-ms and alternative 1-s physical specifications are restricted to the observed Luh domain. The automotive-compatible envelope is the bounded union of observed Luh and Schreiber state-space, not a pooled fit. Luh tails, contact-sensitive Schreiber resistance, and highway post-knee states are `EXTREME / CONDITIONAL`; cross-cell, cross-SOC, cross-temperature, mixed-timescale, and extrapolated trajectories are `REJECTED AS AUTOMOTIVE-INCOMPATIBLE`.

Evidence: `docs/P12_NMC_DEGRADATION_VALIDATION_REPORT.md`

Verification: 28 tests passed; two complete final P12 builds produced identical SHA-256 values for all 17 checked scientific artifacts.

## P13 — Fresh BEV Baseline & Cell/Pack → Vehicle Incremental Energy Translation

Stage: P13 — Fresh BEV Baseline & Cell/Pack → Vehicle Incremental Energy Translation

Decision: VEHICLE ENERGY TRANSLATION VALIDATED WITH BOUNDS

Selected U.S. BEV archetype rule: pre-locked, markasız 2023 U.S. light-duty midsize BEV; NREL Transportation ATB 2024 `Mid`, 300-mile, 77.413145-kWh row. FASTSim 3.0.6 vehicle-level mass/aero/power parameters use the pre-specified midpoint of its two packaged U.S. BEV definitions; commercial resources are implementation templates, not universal main vehicles.

Fresh baseline energy boundary: FASTSim 3.0.6 fresh UDDS and HWFET only; primary output is L2 HV battery-side stored-energy draw. L1 mechanical service and L2 terminal/storage terms remain separate; L3 grid electricity and charging conversion were not calculated.

Cell→pack scaling rule: drive-cycle terminal power and bounded nominal pack voltage give bidirectional current; FASTSim fresh storage loss and `integral(I²dt)` give effective pack resistance. Only relative P12 cell resistance transfers. Absolute Luh/Schreiber/TUM cell ohms are not equated to the representative pack.

Ageing-sensitive pack-loss treatment: pre-specified 0.50/0.75/1.00 cell-sensitive loss-share scenarios; all remaining busbar/contact/BMS/current-path loss is fixed and does not automatically age. No single fitted central share is asserted.

Selected primary vehicle-energy translation: `T1_PHYSICS_BASED_RESISTANCE_LOSS_INCREMENT`; `ΔE = integral[I² R_cell-path,fresh (R_rel−1) dt]`. Capacity uses only `reconstructed_capacity_retention` and changes usable stored energy/range feasibility, not traction energy directly.

TUM validation status: `PASS WITH BOUNDS`; measured WLTP voltage/current/energy and topology-scaled 0/20/40°C HPPC resistance are compatible in automotive order of magnitude. TUM remains validation-only.

Physical representations: P12 10-ms primary and 1-s alternative remain separate. Schreiber early observations remain automotive-envelope evidence; contact-sensitive/highway post-knee and Luh tails remain `EXTREME / CONDITIONAL`. No degradation extrapolation occurred.

Evidence: `docs/P13_VEHICLE_ENERGY_TRANSLATION_REPORT.md`

Verification: full suite `41 passed`; two final P13 generations produced identical SHA-256 values for all 21 manifest-listed artifacts.

## P14 — Mobility Service, Vehicle Survival & Temporal Carbon-Pathway Input Lock

Stage: P14 — Mobility Service, Vehicle Survival & Temporal Carbon-Pathway Input Lock

Decision: LIFECYCLE INPUT ARCHITECTURE VALIDATED WITH BOUNDS

Annual mileage representation: NHTS 2022 V2.1 survey-weighted p25/p50/p75 = 3,218.688 / 10,729.496448 / 19,312.128 km/year after source-dictionary exclusion of `ANNMILES=-9` only.

Mobility-service rule: bounded NHTS family; weighted trip p95 lower, long-distance p50 central, and long-distance p75 upper. No universal 70/80% SOH threshold.

Power-service rule: P13 fixed-cycle HV terminal envelope, 37.745525 kW discharge and 35.614420 kW regenerative acceptance magnitude.

Survival representation: Greene & Leard passenger-car conditional survival. Published logistic method and 2020 median anchor are retained; scale is an explicit 3.5/4.5/5.5-year bounded assumption because machine-readable fitted curve coefficients were unavailable.

Grid: Cambium 2024 load-weighted U.S. central plus 18-region robustness using official `enduse_load`; piecewise-linear 2025–2050 interpolation. Cambium-2023 LRMER remains sensitivity-only.

Manufacturing: chemistry-specific Llamas-Orozco prospective paths use in-domain interpolation. Static benchmark is the same-source 2020 Current factor held constant. Charging: Sevdari p10/p50/p90 L2-to-L3 conversion with no ATB/EPA double counting.

2050 horizon rule: one 2025 entry cohort, operation truncated at 2050, residual survival reported, and no post-2050 extrapolation.

Evidence: `docs/P14_LIFECYCLE_INPUT_ARCHITECTURE_REPORT.md`

Verification: full suite `50 passed`; two complete builds were deterministic. Lifecycle GHG and replacement optimization: `NONE`.

## P14.5 — Real-World Degradation Exposure & Lifetime Bridge Validation

Stage: P14.5 — Real-World Degradation Exposure & Lifetime Bridge Validation

Decision: REAL-WORLD DEGRADATION BRIDGE FAIL

Failure class: `REAL-WORLD DEGRADATION BRIDGE SOURCE INSUFFICIENCY`.

Exposure decision: P14 mileage and P13 L2 energy support a transparent pack-energy equivalent-cycle proxy. Luh discharge Ah supports a separate source-native EFC axis. These axes are not treated as identical cell throughput and do not by themselves assign capacity or resistance.

Bridge decision: A profile-throughput is retained only as partial use exposure; B calendar-plus-use is rejected because separability/additivity is unsupported and risks double counting; C empirical state transition is rejected because the joint observed domain ends near 449 experimental days and has no matched multi-year field trajectory.

State decision: only age-zero identity is assigned. Every nonzero real-world age is `DEGRADATION STATE OUTSIDE VALIDATED DOMAIN`; physical capacity would use only `reconstructed_capacity_retention`, with R10 and R1s kept separate.

Automotive role: Schreiber remains validation-only, with no forced exposure alignment. Contact-sensitive commuter resistance and highway post-knee states remain conditional/extreme.

Evidence: `docs/P145_REAL_WORLD_DEGRADATION_BRIDGE_REPORT.md`.

Verification: focused suite `8 passed`; full suite `58 passed`. Two final P14.5 generations produced identical SHA-256 values for all four scientific outputs/parameter artifacts. Lifecycle GHG, replacement optimization and unsupported degradation extrapolation: `NONE`. P15 was not started.


## P14.5R — Targeted Evidence Expansion & Methodological Revision Gate

Stage: P14.5R — Targeted Evidence Expansion & Methodological Revision Gate

Decision: EVIDENCE EXPANSION CANDIDATE IDENTIFIED WITH BOUNDS

The P14.5 failure was not reversed. R3 — HYBRID BOUNDED MAPPING was identified only as a candidate architecture: an inspectable chemistry-relevant capacity model, independent near-term field capacity evidence, and P12/Schreiber conditional resistance state support without a deterministic real-world R(t).

Evidence: `docs/P145R_EVIDENCE_EXPANSION_ASSESSMENT.md`.

Status note: candidate identification is not a pass and did not authorize P15.

## P14.5S — R3 Methodological Revision Specification & Source Freeze

Stage: P14.5S — R3 METHODOLOGICAL REVISION SPECIFICATION & SOURCE FREEZE

Decision: R3 METHODOLOGICAL REVISION SPECIFIED WITH BOUNDS

The original P14.5 `REAL-WORLD DEGRADATION BRIDGE FAIL` remains authoritative. Five candidate sources were audited and appended without rewriting prior manifest rows. BLAST-Lite was pinned at `b093495b47dc40dd96dba865d91f553619501e94`; its exact nine-class NMC/NMC-like inventory and pre-run eligibility table identify DENSO NMC622 and LG MJ1 NMC811 as the primary model family. Eligible outputs remain a non-averaged structural envelope with source-native parameters.

The selected exposure architecture is E2, a deterministic bounded duty-cycle family preserving P14 annual mileage while explicitly representing driving, charging, parked SOC, cell temperature, charge rate, parked duration and thermal management. Liu and Deng are external validation only; quantitative PASS/PASS WITH BOUNDS/FAIL thresholds were frozen before any candidate model run. Liu is `FIELD VALIDATION WITH LABEL-REPRODUCIBILITY LIMITATION` because the OEM OCV-SOC table is withheld.

Resistance remains non-identifiable as a real-world time trajectory. `BLAST REAL-WORLD RESISTANCE OUTPUT = NOT AVAILABLE / NOT APPROVED`. P12 Luh and Schreiber may support only a pre-registered `conditional resistance-state envelope`; primary R10 and alternative R1s remain separate and unsupported states return `RESISTANCE STATE UNSUPPORTED`. All predictions beyond direct field duration carry `MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION`.

RQ decision: `RQ PRESERVED — INTERPRETATION BOUNDED`.

Evidence: `docs/P145S_R3_REVISION_SPECIFICATION_REPORT.md` and `docs/IMPLEMENTATION_SPEC_P145S_REVISION_PROPOSAL.md`.

Lifecycle GHG Calculated: `NONE`. Replacement Optimization Performed: `NONE`. Scientific Bridge Implemented: `NONE`. Existing P12/P13/P14 Scientific Outputs Modified: `NONE`. P15 was not started.

## P14.5I — R3 Controlled Implementation & Validation

Stage: P14.5I — R3 Controlled Implementation & Validation

Decision: R3 REAL-WORLD DEGRADATION BRIDGE FAIL

The approved P14.5S R3 architecture was implemented without altering the original P14.5 failure. Exactly 17 E2 exposure profiles preserved the three P14 mileage values at 15-minute state resolution and hourly BLAST aggregation. DENSO NMC622 and LG MJ1 NMC811 remained separate source-native primary members with `degradation_scalar = 1`; A/B1/B2/M50 were structural sensitivities only. Domain and nonphysical output states failed closed.

Liu's 2,610 accessible plotted SOH observations failed the pre-registered envelope-width limit. A modern compatibility wrapper completed all 20 Deng archives and produced 53,926 comparable charging-capacity events, but Deng coverage failed the pre-registered lower bound. Worst-source capacity status is `FAIL`.

P12 Luh evidence produced only a `conditional resistance-state envelope` using fixed ±0.025 capacity matching, 25 °C, 50% SOC, same-cell baseline and frozen support minima. R10 and R1s remained separate; Schreiber extreme/contact-sensitive states did not define central bounds. The `real-world resistance trajectory unidentified` invariant remains binding.

No joint real-world bridge row is admissible. `docs/IMPLEMENTATION_SPEC.md` is therefore not amended and P15 is not authorized.

Evidence: `docs/P145I_R3_CONTROLLED_IMPLEMENTATION_REPORT.md`.

Scientific Fitting Performed: `NONE`. Field Calibration Performed: `NONE`. Lifecycle GHG Calculated: `NONE`. Replacement Optimization Performed: `NONE`. Unsupported Extrapolation Performed: `NONE`. Existing P12/P13/P14 Scientific Outputs Modified: `NONE`. P14.5 Failure Record Removed: `NO`.

Verification: focused P14.5I suite `9 passed`; full suite `74 passed`; two complete corrected final R3 generations produced identical SHA-256 values for all 10 checked scientific artefacts.

## P14.6C — Formal RQ Revision, Identified-Set Preregistration & Specification Amendment

Stage: P14.6C — Formal RQ Revision, Identified-Set Preregistration & Specification Amendment

Decision: TRAJECTORY-FREE METHODOLOGICAL REVISION FORMALLY LOCKED WITH BOUNDS

Option B is formally approved as `OPTION B — TRAJECTORY-FREE STATE-CONDITIONED ROBUST / PARTIAL-IDENTIFICATION ARCHITECTURE`. S2 robust dominance through mechanistic set identification is primary. S1 is retained only as the symmetric policy-accounting and endpoint-bound layer. No trajectory optimization may resume without a new explicit scientific revision.

The original trajectory-based Primary RQ remains verbatim in `docs/IMPLEMENTATION_SPEC.md` as historical audit text and is prospectively classified `SUPERSEDED BY APPROVED METHODOLOGICAL REVISION` because P14.5 and P14.5I did not validate the required joint multi-year degradation trajectory.

Revised Primary RQ — LOCKED:

> Conditional on an empirically admissible current battery capacity–resistance state, under what combinations of remaining vehicle service, replacement-battery embodied emissions, and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths are unidentified?

The estimand is `DeltaG = G_R - G_C`, conditional on a matched exogenous context and the pre-registered admissible joint policy-state set `Theta(z)`. Main carbon labels are exactly `ROBUST CONTINUE`, `ROBUST REPLACE`, and `CARBON DECISION INDETERMINATE`. Technical feasibility remains a separate classification axis.

`Theta_C` contains `C_LOW` current-state-frozen and `C_HIGH` worst-technically-feasible supported endpoint treatments. `Theta_R` contains symmetric `R_LOW` fresh-state-frozen and `R_HIGH` compatible worst-supported endpoint treatments. These are accounting bounds, not predicted trajectories. Policy symmetry, joint-set compatibility, matched exogenous context, R10/R1s separation, evidence/scenario tiers, and the revised non-robustness gate are frozen in `data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json`.

Prospective stages are redefined as `P15R — STATE-CONDITIONED LIFECYCLE-GHG ACCOUNTING ENGINE` and, only after P15R passes, `P16R — IDENTIFIED-SET DECISION BOUNDS & ROBUSTNESS CLASSIFICATION`. Neither stage may search for a point optimum or produce time-to-state. P17 is reserved for later result synthesis and is not authorized.

Evidence: `docs/P146_TRAJECTORY_FREE_ARCHITECTURE_ASSESSMENT.md`, the append-only `P14.6C — APPROVED TRAJECTORY-FREE METHODOLOGICAL REVISION` in `docs/IMPLEMENTATION_SPEC.md`, `data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json`, and `docs/P146C_FORMAL_RQ_AND_SPEC_REVISION_REPORT.md`.

Lifecycle GHG Calculated: `NONE`. Decision Bounds Calculated: `NONE`. Replacement Optimization Performed: `NONE`. Original P14.5/P14.5I Failure Records Removed: `NO`. P12/P13/P14 Scientific Outputs Modified: `NONE`. P15R was not started.
