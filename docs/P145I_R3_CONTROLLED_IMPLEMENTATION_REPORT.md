# P14.5I — R3 Controlled Implementation & Validation Report

## 1. Governing Files Read

`PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, the P12/P13/P14 reports and manifests, the original P14.5 failure report, P14.5R, P14.5S, the revision proposal, preregistration, eligibility matrix, source freeze, and decision log were read before implementation.

## 2. Controlled Revision Acceptance

`docs/P145I_CONTROLLED_REVISION_ACCEPTANCE.md` records approval of the frozen P14.5S proposal for P14.5I only. P15, lifecycle GHG, replacement analysis, regimes, Monte Carlo and manuscript work were not authorized.

## 3. Historical P14.5 Failure Preservation

The original `REAL-WORLD DEGRADATION BRIDGE FAIL` remains in its report, artefacts and decision-log entry. P14.5R and P14.5S remain later bounded records; neither was rewritten.

## 4. Frozen R3 Invariants

The implementation preserves `modeled real-world capacity trajectory`, `conditional resistance-state envelope`, and `real-world resistance trajectory unidentified`. `RQ PRESERVED — INTERPRETATION BOUNDED`. A deterministic field resistance trajectory is not claimed.

## 5. Source and Version Verification

All 260 frozen P14.5S artefacts matched their SHA-256 inventory before execution. BLAST-Lite commit `b093495b47dc40dd96dba865d91f553619501e94` supplies the model code. Wu, Liu and Deng remain at their frozen commits; Luh/TUM/Schreiber processed evidence remains unchanged.

## 6. E2 Exposure Implementation

Exactly 17 profiles were generated: one anchor, low/high one-factor bounds for seven dimensions, and two joint stress bundles. Each profile has 35,064 15-minute intervals and only `driving`, `charging`, and `parked_not_charging`; BLAST receives 8,766 hourly aggregates.

## 7. Mileage/Energy Preservation

The exact P14 mileage values are 3,218.688, 10,729.496448 and 19,312.128 km/year. Across all profiles, distance and battery-throughput relative errors are below 0.5% and in practice at floating-point precision. No carbon or grid series was constructed.

## 8. Charging and Parked-SOC Architecture

Policies are frozen as `immediate`, `balanced`, and `home_23_to_08`; power levels are 3.7, 11, 22, 75 and 150 kW where the E2 factor requires them. Parked SOC evolves from energy balance after a preselected initial target, and time shares are reported for `[0,0.3)`, `[0.3,0.7]`, and `(0.7,1.0]`.

## 9. Cell-Temperature Implementation

Wu's deposited orchestration references a missing `tum_model`, so its full thermophysical solver was not reconstructed. P14.5S's authorized bounded proxy was used: exact Wu driving/charging boundaries (15/35 and 30/50 °C), TUM 20/40 °C test levels, and the 25 °C reference only. Ambient temperature was never substituted for cell temperature.

## 10. BLAST Input-Domain Audit

Every model/profile member was checked against its source `experimental_range`. Of 2,652 model/profile/year rows, 572 are in-domain and 2,080 return `CAPACITY MODEL MEMBER OUTSIDE VALIDATED INPUT DOMAIN` with `CAPACITY STATE UNSUPPORTED`. No member was clipped into domain.

## 11. DENSO NMC622 Capacity Results

For the in-domain anchor, DENSO retention is 1.000000, 0.975854, 0.963781, 0.955732, 0.921151 and 0.877142 at ages 0, 1, 2, 3, 10 and 25 years. These are source-native outputs with `degradation_scalar = 1`, not field-fitted values.

## 12. LG MJ1 NMC811 Capacity Results

For the in-domain anchor, MJ1 retention is 1.000000, 0.900315, 0.826385, 0.765445 and 0.436692 at ages 0, 1, 2, 3 and 10 years. Its unmodified 25-year equation crosses below zero; the raw projection is not clipped and that nonphysical state is marked `CAPACITY STATE UNSUPPORTED`.

## 13. Structural Model Comparison

DENSO NMC622 and LG MJ1 NMC811 remain separate primary members; no average, outcome-based weight or favorable-model selection was applied. Their large divergence is retained as model-form uncertainty.

## 14. Conditional Model Sensitivities

Only `NMC_Gr_75Ah_A`, `NMC_Gr_50Ah_B1`, `NMC_Gr_50Ah_B2`, and `Nmc811_GrSi_LGM50_5Ah_Battery` were run as named `STRUCTURAL_SENSITIVITY` members. Every sensitivity is subject to the same input-domain fail-closed rule.

## 15. Long-Horizon Projection Treatment

Every row after three years carries `MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION`. No artificial knee, tail, EOL clipping, survival extension, or empirical long-horizon correction was added.

## 16. Liu Validation Implementation

The accessible publisher table `Figure 2(h).csv` contributes 2,610 plotted mileage/SOH observations. Validation is mileage-coordinate external checking only; no record entered fitting or model selection, and the withheld OEM OCV–SOC table imposes a `PASS WITH BOUNDS` ceiling.

## 17. Liu Validation Results

Median absolute envelope error is 0.000 percentage points, signed median bias 0.000 points, coverage 80.268%, and median envelope width 47.990 points. The width exceeds the pre-registered 15-point bounded limit, so Liu status is `FAIL`. These 2,610 points are not claimed to represent 300 independently identifiable public vehicles.

## 18. Deng Compatibility Wrapper

The modern wrapper replaces removed `scipy.integrate.trapz` with mathematically equivalent `numpy.trapezoid` and bypasses unused undeclared imports. The scientific rules remain: gaps >10 s, at least 100 rows, SOC-jump rejection, ≤10% current missingness with forward fill, trapezoidal current integration, and SOC-interval normalization.

## 19. Deng Reproduction Results

All 20 official RAR archives completed independently; `archive_attempted = archive_completed = 20`. They produced 53,926 comparable capacity events. The checkpoint is retained. The exact incomplete label `DENG FIELD VALIDATION INCOMPLETE` was not triggered.

## 20. Capacity Validation Metrics

Liu: MdAE 0.000 pp, bias 0.000 pp, coverage 80.268%, width 47.990 pp. Deng: MdAE 1.325 pp, bias 1.319 pp, coverage 35.640%, width 12.327 pp, maximum scored-stratum MdAE 5.020 pp.

## 21. Capacity Validation Gate

Both source-specific statuses are `FAIL`: Liu misses the envelope-width limit; Deng misses the minimum coverage. The pre-registered worst-source rule therefore yields overall capacity validation `FAIL`.

## 22. Resistance-Envelope Implementation

Each modeled capacity coordinate is matched at 25 °C, 50% SOC and same-cell-normalized baseline using the fixed symmetric ±0.025 window. Minimum support is 10 observations, 3 cells and 2 experimental conditions; stress classes are `calendar_dominant`, `use_dominant`, and `mixed_union`.

## 23. R10 Support and Envelopes

R10/R10_0 is primary. Supported windows report Luh 10th–90th percentiles plus a separately named automotive outer bound; they never report a midpoint or deterministic R(t).

## 24. R1s Support and Envelopes

R1s/R1s_0 is alternative and is computed in separate rows with separate support counts and quantiles. It is never substituted for R10.

## 25. Schreiber Automotive Outer Envelope

Compatible commuter CU0–CU20 and highway CU0/CU11 observations may expand only the outer automotive envelope. Contact-sensitive commuter CU30–CU50 and highway post-knee CU22 remain `EXTREME / CONDITIONAL` and are excluded from central and compatible outer bounds.

## 26. Unsupported Resistance States

Of 15,912 resistance rows, 13,798 fail source/conditioning/minimum-support requirements and return exactly `RESISTANCE STATE UNSUPPORTED`; 2,114 are supported conditional envelopes. No window widening, interpolation or timescale switching occurred.

## 27. Joint R3 Bridge Construction

Capacity and resistance rows were joined only by model, profile and modeled age after their independent gates. The joint table retains model role, domain status, field-validation status, stress class, endpoint, bounds and projection label.

## 28. Valid Real-World Bridge Domain

There are zero admissible joint rows because the independent capacity-validation gate is `FAIL`, even where conditional resistance support exists. The bridge therefore does not define a valid real-world degradation domain.

## 29. P13 Compatibility

Only schema/unit compatibility was tested: capacity is dimensionless retention and R10/R1s are dimensionless relative bounds with ordered positive endpoints when supported. P13 energy translation, FASTSim propagation and energy/carbon time series were not run.

## 30. False-Optimum Precursor Audit

The gate rejects single-model dependence, unvalidated long-horizon conclusions, unsupported resistance, extreme-only Schreiber support, arbitrary SOC/temperature dependence, clipping, deterministic capacity-to-resistance inference and results that vanish under structural bounds. With zero admissible joint rows, no optimization precursor is released.

## 31. Files Created

Created: controlled acceptance, this report, pre-integrity JSON, six requested Parquets and their metadata, parameters, artefact manifest, Deng event checkpoint/cache, BLAST domain audit, determinism record, isolated `src/degradation_bridge_r3/` modules and focused tests. The full-suite run also restored the manifest-listed P12 model metadata YAML that its legacy test generation requires.

## 32. Files Modified

`docs/RESEARCH_DECISION_LOG.md` is appended after the final gate. The legacy P14.5 artefact manifest is mechanically regenerated by its historical full-suite test because it embeds the append-only decision-log hash; its three scientific Parquet hashes remain exactly frozen. No historical scientific output or source file is edited.

## 33. Tests Run

Focused tests cover exact report structure, E2 profiles, mileage/throughput preservation, model roles/domains, long-horizon labels, external validation, all-archive Deng completion, R10/R1s separation, resistance support, joint fail-closed behavior, P13 schema compatibility and historical integrity. Focused result: `9 passed`. Full-suite result: `74 passed`.

## 34. Determinism Verification

Two complete corrected final R3 generations use the same frozen sources and deterministic Deng event checkpoint following the completed 20-archive extraction. All 10 manifest-listed scientific artefact SHA-256 values matched; mismatch count is zero and determinism status is `PASS`. The final manifest SHA-256 is `5841d4402782249046a0ea45da2a315b7db03aefba0b2b4a5e87b603dfe1279c`.

## 35. Scientific Fitting Performed

Scientific Fitting Performed: NONE

## 36. Field Calibration Performed

Field Calibration Performed: NONE

## 37. Lifecycle GHG Calculated

Lifecycle GHG Calculated: NONE

## 38. Replacement Optimization Performed

Replacement Optimization Performed: NONE

## 39. Unsupported Extrapolation Performed

Unsupported Extrapolation Performed: NONE

## 40. Existing P12/P13/P14 Outputs Modified

Existing P12/P13/P14 Scientific Outputs Modified: NONE

## 41. P14.5 Failure Record Removed

P14.5 Failure Record Removed: NO

## 42. IMPLEMENTATION_SPEC Amendment

No amendment is made because the final gate is `FAIL`. The pre-amendment `docs/IMPLEMENTATION_SPEC.md` SHA-256 is `f8e29917daa0a4f999088005e0c85dffd6cc3cf3f828b1198dce4b6c1c1d3a80`.

## 43. Remaining Bounds

Cell temperature is a source-bounded proxy because Wu's deposited thermophysical dependency is absent; Liu labels are not independently reconstructible; Deng observes charging rather than complete exposure; BLAST is cell-trained and long-horizon qualitative; resistance remains laboratory-conditioned rather than a field-time trajectory.

## 44. Hard Blockers

The pre-registered external capacity gate fails in both sources, 2,080/2,652 model/profile/year rows are outside validated input domain, nonphysical long-horizon states fail closed, 13,798/15,912 resistance rows are unsupported, and no joint row is admissible. These blockers prevent R3 validation and P15.

## 45. Final Status

`R3 REAL-WORLD DEGRADATION BRIDGE FAIL`

P15 was not started.
