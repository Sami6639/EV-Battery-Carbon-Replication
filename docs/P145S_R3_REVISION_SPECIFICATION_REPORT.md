# P14.5S R3 Revision Specification & Source Freeze Report

**Gate date:** 2026-08-21  
**Scope:** specification and source freeze only  
**Candidate architecture:** R3 — HYBRID BOUNDED MAPPING  
**Historical state preserved:** P14.5 FAIL; P14.5R bounded candidate

## 1. Governing Files Read

The following were read in full before this specification was frozen: `PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/P12_NMC_DEGRADATION_VALIDATION_REPORT.md`, `docs/P13_VEHICLE_ENERGY_TRANSLATION_REPORT.md`, `docs/P14_LIFECYCLE_INPUT_ARCHITECTURE_REPORT.md`, `docs/P145_REAL_WORLD_DEGRADATION_BRIDGE_REPORT.md`, `docs/P145R_EVIDENCE_EXPANSION_ASSESSMENT.md`, and `docs/RESEARCH_DECISION_LOG.md`.

The existing `IMPLEMENTATION_SPEC.md` remains authoritative. This work creates a proposal, not a silent amendment.

## 2. Revision Scope

This gate audits and freezes only the minimum new sources, exact BLAST NMC candidate set, model eligibility, outcome-independent exposure architecture, external capacity-validation protocol and thresholds, and P12/Schreiber conditional resistance-envelope algorithm. It does not run candidate capacity models or produce any trajectory, energy penalty, carbon result, or replacement optimum.

## 3. Preserved P14.5 Failure

The P14.5 record remains `REAL-WORLD DEGRADATION BRIDGE FAIL`. The P14.5R record remains `EVIDENCE EXPANSION CANDIDATE IDENTIFIED WITH BOUNDS`; it is not rewritten as a pass. This report adds a later P14.5S specification record without deleting or weakening either predecessor.

P14.5 Failure Record Removed: NO

## 4. R3 Scientific Architecture

R3 separates identifiable quantities:

- calendar/use exposure is mapped by eligible, inspectable NMC semi-empirical models to a **modeled real-world capacity trajectory**;
- capacity is checked independently against automotive field evidence;
- resistance is not modeled as deterministic R(t); it remains a **conditional resistance-state envelope**;
- **real-world resistance trajectory unidentified** is a hard invariant;
- all later lifecycle findings remain conditional on capacity-model and resistance-envelope structure.

The claim “real-world resistance trajectory was identified” is prohibited.

## 5. New Source Audit

| Source | Audit outcome | Frozen role | Principal bound |
|---|---|---|---|
| BLAST-Lite | Auditable; full official checkout | `CANDIDATE_CAPACITY_BRIDGE_MODEL` | Cell models, source-domain and extrapolation limits |
| Wu 2026 | Auditable for method/application architecture | `MODEL_APPLICATION_AND_EXPOSURE_ARCHITECTURE` | Reconstructed figure repository; core pipeline incomplete/hard-coded |
| Liu 2025 | Auditable with limited public fleet artifact | `PRIMARY_FIELD_CAPACITY_VALIDATION` | Withheld OCV table; full-fleet endpoint unavailable during audit |
| Deng 2023 | Auditable; full 20-archive official checkout | `OPEN_FIELD_CAPACITY_VALIDATION` | Charging-only records; source environment incompatibilities |
| Qiushi Wang 2023 | Bibliographically auditable, non-executable | `NON_EXECUTABLE_FIELD_METHOD_VALIDATION` | LFP chemistry; raw fleet telemetry not public |

Only implementation-feasibility and validation artifacts were acquired. Luh and Schreiber remain in their existing frozen roles; their manifest rows were not changed.

## 6. Source Provenance and Licenses

| Source | DOI / official identity | Repository/version | License | Frozen artifacts |
|---|---|---|---|---:|
| BLAST-Lite | Official NLR/NREL BLAST software; model DOIs in §7 | `NatLabRockies/BLAST-Lite`, `b093495...`, `v1.1.0-12-gb093495` | BSD-3-Clause | 124; 140,766,384 bytes |
| Wu | `10.1038/s41558-026-02579-z`; software `10.5281/zenodo.17173892` | `ASSET-Lab/EVBatteryClimateChange`, `25dd34...`; Zenodo record 17173892 | CC BY 4.0 | 63; 28,638,827 bytes |
| Liu | `10.1038/s41467-025-56485-7` | `HoraceLiu1010/...`, `56c1ef...` | MIT repository; CC BY-NC-ND 4.0 publisher artifacts | 47; 122,635,294 bytes |
| Deng | `10.1016/j.apenergy.2023.120954` | `BatICM/...`, `36fef4...` | MIT | 26; 234,904,980 bytes |
| Qiushi Wang | `10.1016/j.xcrp.2023.101720` | Official Cell Press record | CC BY-NC-ND 4.0 | 0 executable local artifacts |

The artifact inventory contains exact filenames, byte sizes, SHA-256 values, versions, roles and prohibited roles for 260 acquired files. Its SHA-256 is `cee9c80d86dda80cb811a94296982ed0a060050e3575688c4da52ecbb45e6423`. Wu's official Zenodo ZIP additionally matched publisher MD5 `bd32a7654900fe3499ccd8e8aaf39357`; its SHA-256 is `fea8741f58bf4347a75d5667f1597a3871f6af35bb984ebf4de1ad0113b1ace0`.

The pre-append source manifest had 16 lines and SHA-256 `d2889702f49b0ece440f57915d84491908d6c8428f86d535a3695db7e79867a9`. Five rows were appended only after audit; the first 16-line byte prefix was preserved.

## 7. BLAST NMC Model Inventory

The pinned software contains nine commercially relevant NMC/NMC-like classes. “Training duration not stated” is retained rather than inferred; the repository-wide description concerns roughly 1–3 years of accelerated cell testing, not a model-specific guarantee.

| Class | Chemistry / format | Original data | Calendar/cycle and inputs | Output / resistance | Domain and warning |
|---|---|---|---|---|---|
| `NMC_Gr_75Ah_A` | commercial NMC-Gr A, large pouch 75 Ah; subtype undisclosed | `10.1016/j.est.2023.109042` | explicit calendar + cycle; T, SOC, DOD, C-rate, throughput | relative capacity q; no R | T 10–45°C, DOD 0.8–1, SOC 0–1, ≤2C; narrow DOD |
| `NMC_Gr_50Ah_B1` | commercial NMC-Gr B1, pouch 50 Ah; subtype undisclosed | same | same source-native interaction | q; no R | T 10–45°C, DOD 0.8–1, ≤1.75C; 10°C charge ≤0.3C |
| `NMC_Gr_50Ah_B2` | commercial NMC-Gr B2, pouch 50 Ah; subtype undisclosed | same | same | q; no R | same narrow domain/low-T warning |
| `Nmc622_Gr_DENSO50Ah_Battery` | NMC622-Gr DENSO EV cell, 50 Ah | `10.1149/1945-7111/ac2ebd`, 32 cells | explicit calendar T/SOC; cycling voltage, DOD, charge C-rate, T, throughput | q; no R | T 10–60°C, DOD 0.1–1, ≤1C; cycling centered at 50% SOC; no knee observed |
| `Nmc811_GrSi_LGMJ1_4Ah_Battery` | NMC811-GrSi LG MJ1 18650; code nominal 3.5 Ah | EVERLASTING D2.3 public data | explicit calendar/cycle; T, SOC, DOD, C-rate, throughput | q; no R | T 0–50°C, DOD 0.2–0.8, SOC 0.1–0.9; DOD linearity assumed; no knee; high-DOD warning |
| `Nmc811_GrSi_LGM50_5Ah_Battery` | NMC811-GrSi LG M50 21700, 5 Ah | `10.1109/ACCESS.2021.3128774`; chemistry `10.1016/j.electacta.2022.140700` | full-factorial calendar T/SOC; cycle T/discharge rate; DOD fixed 1 | q; no R | cycling T 0–25°C, charge 0.3C; inadequate general-duty DOD/charge-rate coverage |
| `Nmc111_Gr_Kokam75Ah_Battery` | NMC111-like Gr pouch 75 Ah | IEEE `07963578` | calendar/cycle; T/SOC/DOD/throughput; no C-rate sensitivity | q plus relative 10-s DC R | chemistry/stress mismatch; 10-s R is neither R10 nor R1s |
| `Nmc111_Gr_Sanyo2Ah_Battery` | NMC111-Gr Sanyo UR18650E 2.15 Ah | `10.1016/j.jpowsour.2014.02.012` | calendar/cycle; cycling chiefly 35°C/1C | q plus relative 10-s DC R near 50% SOC | old lower-Ni chemistry, restricted stress sensitivity, incompatible R endpoint |
| `Nmc_Lto_10Ah_Battery` | NMC-LTO 10.2 Ah | `10.1016/j.jpowsour.2020.228566` | explicit calendar/cycle; T/SOC/DOD/C-rate/throughput | q; no R | LTO anode outside project scope |

Every class uses inspectable source code at commit `b093495b47dc40dd96dba865d91f553619501e94`. Capacity q is relative discharge capacity under each source's reference checks; the cell-level output is not automatically a pack-level SOH measure. Repository documentation treats 10+ year extrapolation as qualitative and warns that pack-life rules require pack evidence.

## 8. Capacity Model Eligibility

Eligibility was frozen before any model run. Required criteria are compatible NMC chemistry, explicit calendar and cycling ageing, temperature and SOC dependence, reproducible required inputs, inspectable source/parameters, no essential proprietary input, and physical capacity-retention output.

Rulings:

- **ELIGIBLE_PRIMARY_FAMILY:** DENSO NMC622 and LG MJ1 NMC811.
- **CONDITIONAL_NOT_PRIMARY / STRUCTURAL_SENSITIVITY:** commercial NMC A/B1/B2 because subtype and DOD coverage are limited; LG M50 because cycle DOD and charge-rate coverage are inadequate for general duty.
- **INELIGIBLE:** Kokam/Sanyo NMC111 and NMC-LTO because chemistry/anode, era, stress coverage, and/or endpoint are incompatible.

The full row-by-row criteria are frozen in `data/metadata/P145S_BLAST_NMC_MODEL_ELIGIBILITY.csv`.

## 9. Capacity Model Selection Architecture

The selected architecture is **PRIMARY MODEL FAMILY + ELIGIBLE NMC MODEL ENVELOPE**. Both eligible primary members are run under the same pre-registered exposure profiles; each output remains distinct. No averaging, retrospective weighting, best-fit selection, hidden scalar, or field/lifecycle tuning is allowed. `degradation_scalar = 1` and all other parameters remain source-native.

Conditional commercial-NMC models are reported only as separately named structural sensitivities inside their declared domains. A disagreement is scientific uncertainty, not a reason to select the favorable model.

## 10. Long-Horizon Projection Rule

Any modeled state after the maximum directly comparable field-validation duration must be labelled exactly:

`MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION`

The label also applies to apparently smooth predictions. A mathematical horizon does not become “validated degradation.” The BLAST 10+ year qualitative-extrapolation warning and each model's no-knee/domain warning must remain visible in every later table/figure.

## 11. Liu Field Dataset Audit

The article covers 300 NCM vehicles, nominal 155 Ah packs with 96 series cells, about three years, generally >10,000 km and >800 days, at 0.1 Hz. Fast charging reaches about 0.8C and slow charging about 0.15C. Available telemetry includes timestamp, SOC, speed, odometer, charge state, pack voltage/current, cell-voltage extrema, temperature extrema, cell-voltage arrays, and probe-temperature arrays. BMS-off parked intervals are absent.

The official GitHub sample contains six RAR parts for one vehicle: 1,203,513 rows over 1,321.9428 days and a 66,294.6 km odometer range. Core time/SOC/current/voltage extrema have no missing values; speed has 8,297 missing values and cell-voltage/probe-temperature arrays 10,389 each.

Published capacity labels require >1 h rest, an OEM OCV–SOC correction at the maximum-cell voltage, starting SOC ≤0.6, and current integration to first full charge. The OEM/supplier OCV table is withheld as a trade secret. The authors report 20 laboratory checks with 0.60% MAPE, but an independent party cannot exactly reconstruct the field labels. Classification is therefore:

`FIELD VALIDATION WITH LABEL-REPRODUCIBILITY LIMITATION`

The full 300-vehicle URL timed out during this audit. The sample permits schema/telemetry feasibility checks, not 300-vehicle fleet validation. The paper's random sample split could mix observations from the same vehicle or temporally dependent records; R3 will not refit its ML model and uses whole-vehicle external partitions only. Repository code is MIT; publisher article/supplements are CC BY-NC-ND 4.0, so redistribution boundaries are preserved.

## 12. Deng Field Dataset Audit

The official repository contains 20 RAR archives, the publisher supplement, figures, and `capacity_extract.py`. It covers 20 BAIC EU500 vehicles with CATL NCM 145 Ah packs, 90 series cells and 32 pack-temperature sensors for about 29 months. Vehicle identity is preserved by archive number. Records cover charging events, not continuous parked exposure.

The published extraction segments at timestamp gaps >10 s, rejects segments with <100 rows or SOC jumps >2 / declines <−0.1, permits current missingness ≤10% with forward-fill, integrates current over time, and normalizes by SOC interval. Exact source execution fails in the pinned present environment because `scipy.integrate.trapz` was removed and undeclared `pyGPs`, `sklearn`, and `natsort` imports are unavailable. The audit therefore attempted the unchanged scientific extraction functions under a compatibility wrapper (`trapezoid` alias and unused-import stubs). The 20-archive job remained CPU-active but produced no completed summary by a 45-minute audit cutoff and was stopped; no partial capacity output was accepted. Exact end-to-end reproduction was therefore **not obtained**. The environment differences and non-completion are frozen in the diagnostics record cited in §33; no BLAST fitting was performed.

## 13. Independent Validation Architecture

BLAST models are selected only by the eligibility criteria in §8. Model parameters remain source-native. Liu and Deng are exclusively external validation; Qiushi Wang is methodological corroboration. None may both tune/select a model and validate it.

If diagnostic/confirmation separation becomes necessary, whole vehicles are ordered by SHA-256 of `source_id|vehicle_id`; the first 60% form a diagnostic set and last 40% remain untouched confirmation. No vehicle contributes rows to both. This deterministic partition is frozen before outcomes; it is not a random row split.

Liu cannot exceed PASS WITH BOUNDS while its OCV label dependency remains unresolved. Overall validation status is the worst source-specific status. No field data are inspected against BLAST outputs in P14.5S.

## 14. Validation Metrics

The parsimonious frozen metric set is:

1. absolute capacity-retention error in percentage points;
2. overall median absolute error (MdAE, pp);
3. signed median bias (pp);
4. MdAE by age and cumulative-use stratum;
5. fraction of observations covered by the non-averaged eligible-model envelope;
6. median eligible-model envelope width (pp), preventing vacuous coverage.

Age strata are `[0,1]`, `(1,2]`, `(2,3]`, and `>3` years. Use strata are within-source cumulative-mileage tertiles frozen without capacity outcomes. Only strata with at least 20 comparable observations are scored. R² is descriptive at most and cannot determine acceptance.

## 15. Pre-Registered Validation Thresholds

| Status | Overall MdAE | |Bias| | Every scored-stratum MdAE | Coverage | Median width |
|---|---:|---:|---:|---:|---:|
| PASS | ≤3.0 pp | ≤1.5 pp | ≤4.0 pp | ≥80% | ≤10.0 pp |
| PASS WITH BOUNDS | ≤5.0 pp | ≤3.0 pp | ≤7.0 pp | ≥60% | ≤15.0 pp |
| FAIL | any bounded threshold missed | any bounded threshold missed | any bounded threshold missed | <60% | >15.0 pp |

FAIL also results if any source-specific assessment fails, >50% of otherwise comparable field points lie outside model input domains, or chemistry/required-input compatibility fails. Overall status is the worst source status.

Three percentage points is practically material and conservatively exceeds Liu's reported 0.60% laboratory label-check MAPE; five percentage points acknowledges field-label, BMS-SOC, partial-charge and pack/cell translation uncertainty without declaring an arbitrarily wide envelope valid. Width caps prevent trivial coverage. These thresholds were frozen before candidate model execution.

## 16. Exposure Generator Candidates

- **E1 — Wu representative daily profiles:** scientifically relevant method reference, but rejected as primary. One profile would imply an exact hourly life; the deposited core code is trimmed, hard-coded, and missing large dependencies.
- **E2 — bounded duty-cycle family preserving annual mileage:** selected. It preserves material states and structural uncertainty with deterministic accounting.
- **E3 — reproducibly seeded stochastic schedules:** rejected at this gate because P14 contains annual mileage only and no source-backed joint empirical distribution for driving, charging, parking, temperature, and SOC.

The simplest sufficient architecture is E2.

## 17. Selected Exposure Architecture

E2 creates 15-minute driving/charging/parked-not-charging states and aggregates time-weighted cell temperature/SOC and energy/throughput to hourly BLAST inputs. Frozen annual distance is exactly 3,218.688, 10,729.496448, or 19,312.128 km/year. Distance and equivalent-full-cycle throughput must agree before/after aggregation within 0.5%.

The seven dimensions are annual mileage, cell temperature, parked SOC, charging frequency, charging power/rate, daily parked duration, and thermal management. The parsimonious family has 17 profiles: one anchor, low/high one-factor variants for seven dimensions, and two coherent joint-stress bundles. No full Cartesian grid is permitted without later change control.

## 18. Temperature Treatment

Ambient temperature is never passed directly as cell temperature. The implementation must use a documented thermal layer coupling ambient/solar, driving/charging heat and thermal-management behavior, following the Wu/TUM architecture where reproducible. The deposited Wu core is reference-only and not runnable as-is; therefore an implementation must either independently reconstruct and verify that thermal layer or use source-bounded cell-temperature profiles explicitly labelled as thermal proxies.

Every profile records temporal resolution, cooling/heating assumptions, model/source, and valid temperature range. Any time step outside a BLAST member's valid cell-temperature domain is unsupported for that member, not clipped.

## 19. Parked-SOC / Charging Treatment

Charging policies are frozen before model outputs: immediate, balanced, and home 23:00–08:00. Nominal powers are 3.7 kW home, 11 kW workplace, and 22 kW public; 75/150 kW fast charging is sensitivity-only and must be required by the specified energy balance.

Parked SOC results from energy balance and policy, rather than being selected for low degradation. Each profile reports parked time shares in `[0,0.3)`, `[0.3,0.7]`, and `(0.7,1.0]`, charging frequency, power, and time parked. Hidden parked SOC is prohibited.

## 20. Calendar/Use Interaction

The approved capacity model's source-native equations alone combine or interact calendar and cycling ageing. P12 Luh calendar fade is not added to BLAST cycle fade. This prevents double counting. P12 remains observed capacity/resistance state-space evidence and later resistance conditioning support, not an additive lifetime component.
## 21. Resistance Identifiability

The two capacity-eligible mid/high-nickel BLAST models output relative capacity q and no scientifically usable project resistance endpoint. The two NMC111 models that expose resistance report relative 10-second DC resistance, not frozen 10-ms R10 or 1-s R1s, and fail chemistry/stress eligibility. Resistance cannot be inferred from capacity fade.

`BLAST REAL-WORLD RESISTANCE OUTPUT = NOT AVAILABLE / NOT APPROVED`

The only permitted claim is **conditional resistance-state envelope**. The invariant is **real-world resistance trajectory unidentified**.

## 22. Proposed Resistance-Envelope Algorithm

For every modeled capacity state, the later implementation must:

1. retain P12 Luh raw observed states at compatible reference temperature/SOC and same-cell baseline;
2. select a compatible ageing/stress class (`calendar_dominant`, `use_dominant`, or a declared mixed union), never carbon or calendar year;
3. match physical reconstructed capacity retention using a fixed symmetric ±0.025 window;
4. require ≥10 observations, ≥3 cells, and ≥2 experimental conditions; the window may not be widened;
5. calculate Luh 10th–90th percentile central envelopes separately for normalized R10 and R1s;
6. allow compatible Schreiber observations to expand only an outer automotive envelope;
7. keep contact-sensitive commuter and highway post-knee evidence `EXTREME / CONDITIONAL`, never central;
8. return no point estimate or midpoint as R(t); do not regress, interpolate gaps, clip tails, or substitute timescales;
9. return the fail-closed string in §24 when support is absent.

Reference temperature, SOC, capacity retention, stress class and automotive validation class are legitimate conditioning variables. Future lifecycle carbon and calendar year are prohibited predictors.

## 23. R10/R1s Separation

Primary remains the 10-ms `R10/R10_0` envelope. Alternative remains the 1-s `R1s/R1s_0` envelope. They are evaluated and reported separately. They are never averaged and never switched to fill a gap. A 10-second BLAST resistance output cannot populate either endpoint.

## 24. Unsupported-State Rule

If chemistry, reference condition, capacity window, stress class, minimum observations, cell count, condition count, or timescale support fails, the only result is:

`RESISTANCE STATE UNSUPPORTED`

No interpolation, extrapolation, tail clipping, alternate-timescale substitution, or deterministic capacity-to-resistance inference is permitted to make a trajectory complete.

## 25. Compatibility with P12

P12 remains the physical NMC capacity and pulse-resistance state space. Its raw observations, reference checks, same-cell normalization, R10 primary endpoint, R1s alternative endpoint and scenario exclusions are unchanged. This proposal consumes P12 only as conditional observed-state support and does not add its calendar fade to BLAST.

## 26. Compatibility with P13

P13 code and scientific outputs are unchanged. A later authorized stage may pass a modeled capacity state plus every admissible R10 envelope bound to P13 only after independent capacity and resistance support gates pass. No energy penalty, FASTSim propagation, or hidden central resistance path is calculated here.

## 27. Compatibility with P14

P14's vehicle, annual mileage scenarios, grid architecture, manufacturing inputs and other frozen lifecycle inputs are unchanged. E2 expands annual mileage into bounded operating-state families without asserting an observed exact schedule. There is no grid-carbon multiplication, manufacturing integration or lifecycle calculation.

## 28. False-Optimum Gate

Before any carbon result, a later replacement optimum is frozen as NON-ROBUST if it:

- depends on one BLAST model when another eligible NMC model reverses it;
- appears only beyond direct field-validation horizon;
- depends on `RESISTANCE STATE UNSUPPORTED` regions;
- relies only on extreme Schreiber states;
- depends on one arbitrary parked-SOC assumption;
- depends on one arbitrary temperature scenario;
- requires tail clipping;
- requires deterministic capacity-to-resistance inference;
- relies on an unvalidated 10–25-year projection; or
- disappears under reasonable capacity/resistance structural bounds.

These rejection rules cannot be loosened after results are observed.

## 29. RQ Preservation Test

The primary question remains scientifically recognizable if later interpretation is “replacement timing conditional on admissible degradation-state uncertainty,” not an empirically observed deterministic R(t).

`RQ PRESERVED — INTERPRETATION BOUNDED`

No fundamental RQ change is required at this specification gate; claim strength is explicitly reduced and bounded.

## 30. Proposed IMPLEMENTATION_SPEC Revision

`docs/IMPLEMENTATION_SPEC_P145S_REVISION_PROPOSAL.md` contains only proposed additions: new source roles, capacity-family/envelope architecture, E2 exposure generator, independent validation roles/metrics/thresholds, conditional resistance-envelope algorithm, long-horizon label, false-optimum gates and prohibited claims. It does not overwrite or supersede `docs/IMPLEMENTATION_SPEC.md`.

## 31. Files Created

- `docs/IMPLEMENTATION_SPEC_P145S_REVISION_PROPOSAL.md`
- `docs/P145S_R3_REVISION_SPECIFICATION_REPORT.md`
- `data/metadata/P145S_BLAST_NMC_MODEL_ELIGIBILITY.csv`
- `data/metadata/P145S_R3_PREREGISTRATION.json`
- `data/metadata/P145S_SOURCE_ARTIFACT_FREEZE.csv`
- `data/metadata/P145S_SOURCE_FREEZE_SUMMARY.json`
- `data/metadata/SRC_BLAST_LITE.yaml`
- `data/metadata/SRC_WU_2026.yaml`
- `data/metadata/SRC_LIU_2025.yaml`
- `data/metadata/SRC_DENG_2023.yaml`
- `data/metadata/SRC_QIUSHI_WANG_2023.yaml`
- `results/diagnostics/P145S_DENG_CAPACITY_EXTRACTION_AUDIT.json`
- `src/source_freeze/p145s_freeze.py`
- `tests/test_p145s_specification.py`
- required official artifacts under `data/raw/SRC_BLAST_LITE`, `SRC_WU_2026`, `SRC_LIU_2025`, and `SRC_DENG_2023`.

No executable Qiushi Wang raw artifact was created or substituted.

## 32. Files Modified

- `data/metadata/SOURCE_MANIFEST.csv`: five candidate rows appended after audit; prior 15 rows unchanged.
- `docs/RESEARCH_DECISION_LOG.md`: a new P14.5S decision entry appended; P14.5/P14.5R entries preserved.

No existing P12, P13, or P14 scientific output was modified.

## 33. Tests / Integrity Checks

The source freeze inventories 260 acquired artifacts and records repository commits and SHA-256 values. The source-manifest pre-append SHA-256 and line count are frozen, and tests verify that the historical byte prefix remains exact. Tests also verify:

- exactly 38 numbered report sections, in the required order;
- all mandatory claim phrases, unsupported-state and long-horizon labels;
- nine BLAST NMC/NMC-like inventory rows and two primary-family eligible models;
- valid machine-readable JSON/CSV files;
- five appended manifest IDs with 21 columns and no duplicate IDs;
- exact disclosure/final-status strings;
- no forbidden deterministic resistance claim except as an explicitly prohibited quotation;
- no created/modified file under frozen P12/P13/P14 scientific-output paths.

Deng's source-code execution incompatibilities and 45-minute non-completed compatibility attempt are recorded in `results/diagnostics/P145S_DENG_CAPACITY_EXTRACTION_AUDIT.json`; no partial capacity result was accepted. This is an extraction audit only and performs no model fitting.

Focused P14.5S tests: `7 passed`. Provenance plus P14.5S tests: `10 passed`. Full project suite: `65 passed` (one non-scientific pytest cache-permission warning).

## 34. Lifecycle GHG Calculated

Lifecycle GHG Calculated: NONE

Existing P12/P13/P14 Scientific Outputs Modified: NONE

## 35. Replacement Optimization Performed

Replacement Optimization Performed: NONE

No retirement-regime, replacement, or false-optimum result was computed.

## 36. Scientific Bridge Implemented

Scientific Bridge Implemented: NONE

No modeled real-world capacity trajectory, conditional resistance-state envelope values, P13 energy penalty, or R3 bridge output was generated.

## 37. Hard Blockers

No blocker prevents a bounded specification: at least two pre-selected eligible NMC capacity models exist, E2 can reproducibly generate required inputs, independent external validation roles/thresholds are frozen, and resistance fails closed.

Bounds that remain hard for any later implementation/result are:

- Liu full-fleet access was unavailable and its OCV–SOC table is withheld; exact labels are not independently reproducible;
- Wu's deposited core pipeline is reference-only and incomplete, requiring a separately verified thermal/exposure implementation;
- Deng observes charging rather than continuous parked exposure and requires a documented modern-environment compatibility wrapper;
- Qiushi Wang is LFP and offers no public raw fleet telemetry, so it is non-executable corroboration only;
- BLAST has no approved R10/R1s real-world resistance output;
- capacity states outside model domains and resistance states without P12/Schreiber support remain unsupported;
- predictions beyond direct field duration remain projections, with BLAST 10+ year warnings operational.

These bounds require `WITH BOUNDS`; they cannot be hidden by later simulation completeness.

## 38. Final Status

R3 METHODOLOGICAL REVISION SPECIFIED WITH BOUNDS

Lifecycle GHG Calculated: NONE  
Replacement Optimization Performed: NONE  
Scientific Bridge Implemented: NONE  
Existing P12/P13/P14 Scientific Outputs Modified: NONE  
P14.5 Failure Record Removed: NO

**STOP — P15 not started. Await explicit next instruction.**