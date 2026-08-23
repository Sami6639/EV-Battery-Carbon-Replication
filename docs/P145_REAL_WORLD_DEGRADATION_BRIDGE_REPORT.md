# P14.5 Real-World Degradation Exposure & Lifetime Bridge Validation

## 1 Governing Files Read

`PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/CANONICAL_DATA_DICTIONARY.md`, P12/P13/P14 reports and configs, `docs/RESEARCH_DECISION_LOG.md`, Luh/Schreiber selection and metadata records, canonical Luh/Schreiber Parquets, and the retained official Luh workbooks were read. Source context was checked against [Luh & Blank 2024](https://doi.org/10.1038/s41597-024-03831-x) and [Schreiber et al. 2025](https://doi.org/10.1016/j.est.2025.115357).

## 2 Problem Definition

The gate asks whether P12/P13 experimental degradation states can be assigned to P14 real calendar age and mileage without unsupported extrapolation. A valid result requires a joint calendar/use mapping, not merely a use-exposure conversion.

## 3 Laboratory-Time vs Real-World-Time Audit

Luh contains at most 448.184919 experimental days for calendar observations and 448.144988 days for profile observations. Cyclic/profile cells operate continuously between check-ups, with five-minute rests. Therefore experimental elapsed days are laboratory exposure time, not vehicle calendar years. No 0–436.9068-day P12/P13 curve was stretched over 2025–2050.

## 4 Luh Exposure Structure

The canonical data contain 16 calendar conditions, 48 cyclic conditions, and 12 profile conditions with three nominal replicates each. Audited fields include age type, profile, 0/10/25/40°C operating temperature, calendar idle SOC, charge/discharge C-rates, operating cycles, check-up cycles, charge/discharge Ah and elapsed days. Calendar cells have zero operating cycles but nonzero check-up throughput; the source paper notes 43–63 EFC from check-ups by the last check-up. Profile types are full WLTP 10–100%, full WLTP 10–90%, and extra-high WLTP 10–90%.

## 5 Real-World Mileage/Energy Inputs

Annual mileage is 3,218.688 / 10,729.496448 / 19,312.128 km/year. Fresh combined L2 battery-side energy is 0.09324077636479178 kWh/km. Nominal pack energy is 77.413145 kWh and usable-window scenarios are 0.85/0.90/0.95. No charging, grid or carbon term is included.

## 6 Candidate Exposure Mappings

A pack-energy equivalent-cycle proxy is reported as cumulative L2 kWh divided by nominal pack kWh times usable-window fraction. Luh source-native discharge EFC is `(discharge Ah − same-cell baseline discharge Ah) / same-cell baseline capacity Ah`. The two are explicitly different quantities: the pack proxy is not source-cell Ah and cannot alone assign degradation state. No Ah-to-kWh conversion was invented.

## 7 Candidate Bridge Architectures

Three and only three architectures were audited: A profile-ageing throughput, B calendar-plus-use two-component, and C empirical bounded state-transition envelope. A retains partial use-exposure information; B and C are rejected as state bridges.

## 8 Calendar-Ageing Treatment

Calendar ageing is kept separate. Luh covers about 1.23 years under fixed 0/10/25/40°C and 10/50/90/100% idle-SOC conditions, with check-up cycling contamination. The frozen sources contain no validated temperature/SOC residence model or longer-term calendar tail for the representative vehicle.

## 9 Use-Ageing Treatment

Twelve Luh profile conditions cover 36 cells and source-native discharge exposure up to 1,549.801234 EFC. The WLTP power-profile structure and source EFC-to-distance examples support a use-exposure candidate, but continuous laboratory cycling, charging limits, temperature and duty factor differ from annual road use. Therefore use exposure is reported only as a proxy.

## 10 Double-Counting Assessment

Adding a calendar curve to a profile/cyclic curve would double-count elapsed-time effects because profile/cyclic observations already age during laboratory time. Conversely, calendar observations include capacity-check cycling. No separable/additive decomposition is supplied by the frozen sources, so bridge B is rejected.

## 11 Selected Primary Bridge

Selected primary bridge: `NONE`. Result: `REAL-WORLD DEGRADATION BRIDGE SOURCE INSUFFICIENCY`. The main table assigns the exact fresh identity only at age zero; every nonzero real-world age has null capacity/R10/R1s and `DEGRADATION STATE OUTSIDE VALIDATED DOMAIN`.

## 12 Bounded Alternative Bridges

A is retained as `PARTIAL_USE_EXPOSURE_ONLY`. B is `REJECTED_NO_SEPARABLE_ADDITIVE_EVIDENCE`. C is `REJECTED_NO_JOINT_REAL_TIME_USE_SUPPORT`. Lower-degradation, primary/central, higher-degradation and automotive conditional/extreme classes are all represented in the uncertainty table, but none receives a fabricated lifetime trajectory.

## 13 Capacity-State Mapping

Usable capacity may use only physical `reconstructed_capacity_retention`. `source_capacity_soh_percent` is forbidden for this purpose. Age zero is 1.0; all nonzero real-world ages are null because no joint bridge passed.

## 14 Resistance-State Mapping

R10/R10_0 remains primary and R1s/R1s_0 remains separate. Both equal 1.0 only at age zero. No resistance state is assigned afterward and no timescale switching occurs.

## 15 Schreiber Automotive Validation

Nine frozen Schreiber check-ups remain independent validation only. Selected-file laboratory dates are exposed without alignment to Luh. Commuter direction is compatible but later resistance is contact-sensitive; highway CU22 is post-knee/extreme. The paper explicitly identifies relaxation transferability and calendar ageing as future work, so it cannot repair the missing joint bridge.

## 16 Valid Degradation-State Domain

The only validated real-world bridge state is the fresh baseline identity. The broader P12 observed experimental envelope remains valid as a state-space/envelope, not as a vehicle-age trajectory.

## 17 Valid Real-World Time/Usage Domain

Real-world calendar age and accumulated mileage/energy are calculated for 2025–2050. These exposure axes are valid inputs; degradation state is not populated beyond age zero. From age two onward, calendar exposure also exceeds the 448.184919-day Luh calendar domain.

## 18 Technical-Feasibility Interaction

No P13 energy penalty or P14 mobility-feasibility decision is evaluated for nonbaseline years because doing so would consume an unsupported degradation state. P13 usable windows remain exposure denominators only.

## 19 False-Optimum Precursor Gate

Later stages must reject any candidate that uses a nonbaseline state without joint calendar/use support, stretches experimental days into years, adds calendar and use without separability, leaves the P12 envelope, uses source SOH as usable capacity, forces Schreiber alignment, or invents/clips a degradation tail.

## 20 Files Created

Created `src/degradation_bridge/`, its config and deterministic pipeline; three requested Parquets and three metadata files; parameter and artifact-manifest JSON files; `tests/test_p145_degradation_bridge.py`; and this report.

## 21 Files Modified

`docs/RESEARCH_DECISION_LOG.md` was appended only after the final gate was determined. No raw file or earlier canonical output was modified.

## 22 Tests Run

Focused suite: `8 passed`. Full suite: `58 passed` in 96.53 seconds. Tests cover time, mileage, energy, throughput proxy, physical capacity identity, resistance separation, calendar/use double counting, domain status, source roles, outcome leakage and deterministic regeneration.

## 23 Scientific Fitting Performed

Scientific Fitting Performed: NONE

## 24 Lifecycle GHG Calculated

Lifecycle GHG Calculated: NONE

## 25 Replacement Optimization Performed

Replacement Optimization Performed: NONE

## 26 Extrapolation Performed

Unsupported Degradation Extrapolation Performed: NONE

## 27 Frozen-Decision Changes

Frozen-Decision Changes: NONE

## 28 Remaining Limitations

A pass would require approved evidence that jointly resolves calendar ageing, realistic duty/relaxation, thermal and SOC residence, and use throughput for the representative vehicle; or a validated model with those inputs. Schreiber intermediate cycling files alone would not create calendar evidence. No new literature or source was acquired.

## 29 Hard Blockers

`REAL-WORLD DEGRADATION BRIDGE SOURCE INSUFFICIENCY`: no frozen source supplies a separable or jointly validated calendar-plus-use mapping over multi-year real operation. Populating the lifecycle timeline would require extrapolation or additional evidence.

## 30 Final Status

REAL-WORLD DEGRADATION BRIDGE FAIL


