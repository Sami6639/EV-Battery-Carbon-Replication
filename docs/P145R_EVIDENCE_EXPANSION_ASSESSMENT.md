# P14.5R — Targeted Evidence Expansion & Methodological Revision Gate

**Assessment date:** 2026-08-20  
**Change-control class:** `METHODOLOGICAL REVISION CANDIDATE`  
**Scope:** Evidence assessment only. No source freeze, fitting, bridge implementation, lifecycle calculation, replacement optimization, Monte Carlo analysis, manuscript work, or P15 work was performed.

## 1 Governing Files Read

The governing chain was read before assessment: `PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/CANONICAL_DATA_DICTIONARY.md`, `docs/RESEARCH_DECISION_LOG.md`, the P12, P13, P14, and P14.5 reports, and their cited source/configuration records.

The binding constraints remain unchanged:

- the physical degradation state is joint usable-capacity retention plus resistance growth;
- `reconstructed_capacity_retention` is the usable-capacity quantity;
- 10-ms pulse resistance (`R10/R10_0`) is primary and 1-s resistance (`R1s/R1s_0`) remains separate;
- Luh is the physical state-space source, Schreiber is automotive validation, and P13 translates only admissible states to vehicle-energy effects;
- no Luh experimental day/EFC or Schreiber check-up may be stretched onto P14 calendar time without an approved bridge;
- all P14 calendar, mileage, survival, grid, manufacturing, and charging-conversion decisions remain frozen.

## 2 P14.5 Hard Blocker

The preserved blocker is `REAL-WORLD DEGRADATION BRIDGE SOURCE INSUFFICIENCY`.

P14.5 found no separable or jointly validated mapping from real vehicle calendar age and use to both capacity and resistance. Luh covers about 1.23 experimental years and approximately 1,550 source-native discharge EFC at the upper end of the profile subset, but continuous laboratory exercise is not intermittent vehicle use. Schreiber supplies highly relevant automotive-grade realistic and accelerated ageing evidence, yet identifies relaxation transferability and calendar ageing as unresolved. P14.5 therefore populated only the fresh identity state and left every non-zero real-world age null.

This assessment does not overwrite that failure. It tests whether evidence published from 2020 through 2026-08-20 identifies a defensible change-controlled candidate.

## 3 Exact Missing Evidence

The missing object is a traceable mapping:

`calendar age + mileage/energy/Ah throughput + realistic driving/charging duty + parked/rest exposure + temperature history + SOC/charging history -> usable capacity retention + R10/R10_0 (and separately R1s/R1s_0)`.

Acceptable evidence would be either:

1. longitudinal, multi-year automotive field observations of those exposures and health outputs; or
2. a chemistry-relevant, inspectable semi-empirical calendar-plus-cycle model with explicit parked and operating exposure and independent field validation.

A total field trajectory may be useful without statistical calendar/cycle separation if its domain is explicit. A capacity estimator alone cannot resolve the frozen dual-state requirement. Capacity–resistance correlation alone does not identify a real-world resistance trajectory.

## 4 Search Strategy

The search covered 2020–2026-08-20 peer-reviewed primary literature, publisher records, institutional repositories, author/agency code repositories, and authoritative datasets. Terms combined automotive/EV battery, longitudinal field data, calendar ageing, parking/rest/relaxation, mileage/throughput, temperature, SOC/charging, capacity fade, resistance/impedance growth, and real-world validation.

The targeted review included Liu 2025, Schreiber 2025, Zhao 2022, Qiushi Wang 2023, Qichen Wang 2025, Deng 2023, NREL BLAST-Lite, Wu 2026, Luh and Blank 2024, Pozzato 2022, and recent capacity–resistance evidence. Citation chaining was used only to locate primary papers or official data/code records.

Evidence tiers were:

- **Tier 1:** longitudinal field/automotive evidence, preferably multi-year and vehicle-resolved;
- **Tier 2:** inspectable semi-empirical calendar-plus-cycle models with independent real-world validation;
- **supporting only:** lab/cross-study evidence for bounds that cannot supply a field-time bridge.

## 5 Candidate Sources

1. **Liu et al. (2025), Nature Communications.** Three years from 300 NCM EVs; cumulative mileage, SOC, current, pack/cell voltage, charging behavior, temperature features, and capacity/SOH labels. Idle records are absent because BMS logging stops when vehicles are off. Data/code are linked, but the OEM OCV–SOC table used for correction is withheld. [Article](https://www.nature.com/articles/s41467-025-56485-7) · [repository](https://github.com/HoraceLiu1010/Multi-modal-SOH-estimation-framework)

2. **Qiushi Wang et al. (2023), Cell Reports Physical Science.** More than four years from 60 electric buses in two cities. Features include mileage, Ah throughput, temperature, voltage, SOC, DOD, current, calendar time, operating time, and inferred parking time; capacity trajectories are predicted. Only derived statistical features, not the underlying fleet telemetry, were identified as public. [Article](https://doi.org/10.1016/j.xcrp.2023.101720)

3. **Deng et al. (2023), Applied Energy.** Public charging records for 20 BAIC EU500 vehicles with CATL NCM packs over about 29 months, including current, cell voltage, SOC, and 32 pack temperature sensors; capacity-extraction code is published. It covers charging, not complete driving/parked history, and contains no repeated resistance measurement. [Dataset/code](https://github.com/BatICM/battery-charging-data-of-on-road-electric-vehicles) · [article](https://doi.org/10.1016/j.apenergy.2023.120954)

4. **Wu et al. (2026), Nature Climate Change, with NREL BLAST-Lite.** Driving, parked-charging, and parked-not-charging modes generate hourly battery temperature, SOC, and charging-rate inputs for calendar/cycle degradation models. The study reports fleet-level benchmarking and a 25-year cap, but acknowledges cell-to-pack optimism. BLAST warns that its 1–3-year accelerated-ageing training basis is extrapolated to 10+ years and should be treated qualitatively. [Article](https://www.nature.com/articles/s41558-026-02579-z) · [BLAST-Lite](https://github.com/NatLabRockies/BLAST-Lite) · [study code](https://github.com/ASSET-Lab/EVBatteryClimateChange)

5. **Schreiber et al. (2025), Journal of Energy Storage.** Volkswagen ID.3 automotive NMC pouch cells under commuter, highway, and accelerated protocols, with capacity and resistance check-ups and comparison to a real vehicle around 60,000 km. The vehicle was parked about 96% of the time. The work shows that omitted rest can distort apparent capacity/resistance and calls for dedicated relaxation and calendar-ageing work. [Article](https://doi.org/10.1016/j.est.2025.115357)

6. **Luh and Blank (2024), Scientific Data.** Open NMC/C–SiO lab data with capacity, EIS, R0/R1, 10-ms and 1-s resistance, temperature, SOC, throughput, and calendar/cycle/profile metadata. It remains the strongest project dual-state source but has a 449-day lab horizon. [Article/data description](https://www.nature.com/articles/s41597-024-03831-x)

7. **Pozzato et al. (2022), Data in Brief.** About 23 months of NMC cells under EV-derived profiles, with capacity, HPPC, and EIS. It adds realistic load-shape and dual-state evidence but remains fixed-environment laboratory evidence. [Article](https://doi.org/10.1016/j.dib.2022.107995)

8. **Zhao et al. (2022), Applied Energy.** Field framework decoupling ambient temperature and total distance effects on range and energy consumption across ten Chinese urban areas. Outcomes are vehicle range/energy, not direct battery capacity/resistance; no attached data files appear in the institutional record. [Record](https://hub.hku.hk/handle/10722/336525)

9. **Qichen Wang et al. (2025), Carbon Neutral Systems.** Reuses Deng data for capacity trajectories and smart retirement decisions for 20 NCM EVs over about 29 months. Internal resistance is explicitly omitted and identified as future work. [Article](https://link.springer.com/article/10.1007/s44438-025-00017-9)

10. **2025 capacity–resistance synthesis.** A peer-reviewed analysis of 814 NMC/NCA/LFP lab cells reports strong capacity-fade/resistance-growth correlation. Chemistry mixture, heterogeneous protocols, and no automotive longitudinal exposure limit it to directional envelope support. [Article](https://doi.org/10.1016/j.jpowsour.2025.237921)

## 6 Candidate Source Comparison

| Source | Field/lab | Chemistry | Duration | Mileage/throughput | Calendar ageing | Cycle ageing | Temperature | SOC/charging | Capacity | Resistance | Code/data access | Real-world validation | Project fit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Liu 2025 | 300-EV field | NCM; subtype undisclosed | 3 y; most >800 d | mileage; most >10,000 km | elapsed age; parked state unlogged | driving/charging telemetry | operating/charging features | SOC; fast/slow charging | estimated labels/trajectory | none | data link; sample/code MIT; OCV table withheld | direct multi-EV capacity | strongest open Tier-1 capacity evidence; incomplete rest/resistance |
| Qiushi Wang 2023 | 60-bus field | exact subtype not established | >4 y | >400,000 km/vehicle; Ah | calendar/parking time features | use features | yes | SOC, DOD, current | predicted trajectory | none identified | article/derived supplement; no raw fleet | direct field internal evaluation | strongest identification design; not independently reproducible |
| Deng 2023 | 20-EV charging field | CATL NCM | ~29 mo | charging throughput | timestamp span | charging only | 32 sensors | SOC/current/voltage | extracted/predicted | none | public archives/code; MIT | direct field capacity | reproducible capacity anchor; incomplete use/rest |
| Wu 2026 + BLAST | simulation + lab-trained model | multiple Li-ion, including NMC | to 25 y; training 1–3 y typical | FEC/VMT/profile inputs | explicit; parked modes | explicit | hourly cell T | hourly SOC/rate | modelled retention | no acceptable field-R output identified | BLAST BSD-3; public study code/data | fleet comparison; cell-trained | strongest Tier-2 capacity candidate; qualitative long-horizon bounds |
| Schreiber 2025 | realistic lab + vehicle | ID.3 NMC pouch | lab ~1.5 y; field >60,000 km | EFC and km | vehicle mostly parked; no separate model | realistic/accelerated profiles | controlled + field | realistic/fast charge | lab + field comparison | lab only | official TUM package, CC BY 4.0 | direct vehicle comparison | validation/envelope, not joint trajectory |
| Luh 2024 | lab | NMC/C–SiO | 449 d | up to ~1,550 EFC | dedicated fixed-T/SOC | cycle/WLTP profile | 0/10/25/40°C | explicit | physical | EIS, R0/R1, R10/R1s | open CC BY 4.0 | none | frozen state-space, not field-time bridge |
| Pozzato 2022 | realistic-profile lab | NMC | ~23 mo | EV-profile cycles | elapsed only | dynamic profiles | mainly 23°C | controlled | yes | HPPC/EIS | open | none | supporting dual-state evidence |
| Zhao 2022 | fleet field | multiple/unspecified | not sufficient in accessible record | total distance | no battery state | vehicle use | ambient | insufficient | no direct state | none | article; no record files | range/energy only | confounding context; wrong output |
| Qichen Wang 2025 | Deng field reuse | CATL NCM | ~29 mo | charging exposure | calendar sequence | charging only | yes | current/voltage/SOC | predicted | explicitly omitted | underlying Deng public; study data on request | same-fleet evaluation | capacity-only |
| 2025 synthesis | multi-study lab | NMC/NCA/LFP | heterogeneous | heterogeneous | heterogeneous | heterogeneous | heterogeneous | heterogeneous | yes | yes | source-dependent | none | conditional direction only |

No chart was added because the decisive evidence is categorical—coverage, observability, access, and validation domain—and is more accurately represented in the table.

## 7 Calendar/Use Identifiability

**Total field capacity degradation is partially identifiable.** Liu supplies age, mileage, operation, charging, temperature features, and capacity labels over three years. Deng supplies a downloadable 29-month NCM charging record. Qiushi Wang publishes the most complete feature design: calendar/parking/operating time, mileage, throughput, temperature, SOC/DOD, and current jointly predict capacity.

**Separation is not fully identifiable from open field data.** Liu has no vehicle-off records. Deng records charging only. Qiushi Wang infers parking time, but raw data needed for independent reconstruction are unavailable. None continuously observes parked SOC and cell temperature across its full field horizon.

**Tier-2 separation is operational but model-dependent.** BLAST represents calendar/cycle ageing as functions of temperature/use, while Wu supplies driving, charging, and parked modes. This is a reproducible capacity-model candidate, not direct field identification. The documented 10+ year extrapolation caveat is binding.

**Relaxation remains separate.** A parked step is not automatically a validated electrochemical relaxation model. Schreiber shows reversible capacity/resistance effects and altered mechanisms after rest. No recovery correction may be invented.

## 8 Resistance Identifiability

`RESISTANCE REAL-WORLD TRAJECTORY NOT IDENTIFIED`

No Tier-1 field source supplies repeated, compatible 10-ms pulse resistance or 1-s resistance/impedance across multiple vehicle years. Liu, Deng, Qiushi Wang, and Qichen Wang are capacity-focused. Zhao predicts range/energy. Schreiber measures lab resistance and field capacity/degradation modes, not a longitudinal vehicle resistance series compatible with P12.

Luh, Schreiber lab data, Pozzato, and the 2025 synthesis can support a **conditional resistance envelope** at observed capacity/stress states. They cannot be relabeled as real-world `R(t)`. No automatic Luh resistance trajectory, deterministic capacity-to-resistance conversion, or R10/R1s switching is approved.

## 9 Data Accessibility

- **Liu:** article source data/code public; repository MIT; article CC BY-NC-ND 4.0. Full OEM-hosted artifact terms and stability require verification. OCV table is withheld.
- **Qiushi Wang:** article and small derived feature supplement accessible under CC BY-NC-ND 4.0; raw four-year telemetry and full pipeline not identified.
- **Deng:** public vehicle archives and extraction code in an MIT repository; most reproducible Tier-1 capacity candidate.
- **Wu/BLAST:** BLAST public under BSD-3-Clause with cited NMC model sources; Wu code/data public. Artifact-level Wu licenses must be recorded individually.
- **Schreiber and Luh:** official open packages under CC BY 4.0; existing roles retained.
- **Qichen Wang:** study data on request; underlying Deng source public; no resistance.
- **Zhao:** institutional record has no data attachment.

Before any registry change, each artifact needs stable locator, checksum, license/terms, retrieval date, paper linkage, schema audit, and explicit missingness assessment.

## 10 Candidate Resolution Architectures

Only three architectures were evaluated.

### R1 — Direct field mapping

Reconstruct capacity from Liu, Deng, or Qiushi Wang using calendar age/use covariates. It is attractive within 2.4–4 years but fails as a complete bridge because open sources lack full parked exposure and compatible resistance; the strongest feature set is not reproducible from public raw data.

### R2 — Validated semi-empirical model

Use a chemistry-relevant BLAST-Lite NMC model driven by explicit time, temperature, SOC, charging, parked state, and use. Validate capacity against held-out Liu/Deng/Schreiber evidence. It provides calendar/use mechanics and long horizons but retains model-form, cell-to-pack, subtype, and extrapolation uncertainty. No compatible field resistance path was identified.

### R3 — Hybrid bounded mapping

Use R2 for a bounded capacity trajectory, constrain its near-term behavior with R1 field evidence, and retain P12/Schreiber resistance only as a source-native conditional envelope at matched physical capacity/stress. Resistance is bounded as uncertainty, not asserted as a field-time prediction.

R3 is defensible only as a methodological revision candidate. It is not a source substitution and requires explicit approval, pre-registered selection, validation thresholds, and false-optimum tests.

## 11 Compatibility with P12

R3 can preserve P12 if Luh is neither refit nor redefined. `reconstructed_capacity_retention`, primary R10, alternative R1s, 25°C/50% SOC normalization, and observed domains remain unchanged. The capacity model supplies a field-time capacity coordinate but never authorizes interpolation outside P12 support.

Resistance must remain an explicit observed conditional distribution/envelope with chemistry and stress labels. Unsupported combinations remain invalid rather than clipped.

## 12 Compatibility with P13

P13’s translation can remain unchanged in form and may consume only joint states that pass a revised bridge. Capacity affects usable energy/window feasibility; R10 remains primary and R1s separate. No capacity-only timeline may enter P13 as though resistance were known.

R3 would expand P13 inputs because each capacity path carries resistance and model-structure bounds. No energy translation is run in this gate.

## 13 Compatibility with P14

P14 mileage, mobility service, survival, grid, manufacturing, charging conversion, and 2025–2050 calendar remain unchanged. The bridge consumes P14 inputs.

Hourly SOC, charging, parked state, battery temperature, and thermal-management assumptions are not locked P14 facts. They require a separate bounded exposure layer and cannot be inferred from annual mileage alone. The 2050 truncation remains.

## 14 Source-Registry Impact

No registry was modified. Later approval would minimally add:

- BLAST-Lite plus selected NMC model sources: `CANDIDATE_CAPACITY_BRIDGE_MODEL`;
- Wu 2026: `MODEL_APPLICATION_AND_REAL_WORLD_BENCHMARK`;
- Liu 2025: `PRIMARY_FIELD_CAPACITY_VALIDATION`, conditional on artifact audit;
- Deng 2023: `OPEN_FIELD_CAPACITY_VALIDATION`;
- Qiushi Wang 2023: `NON_EXECUTABLE_FIELD_METHOD_VALIDATION` unless raw data are obtained;
- 2025 synthesis: `DIRECTIONAL_CONDITIONAL_ENVELOPE_SUPPORT`, never trajectory;
- Luh/Schreiber: existing roles unchanged.

Rows must record chemistry, cell/pack level, field/lab status, horizon, output definition, locator, license, checksum, validation role, and prohibitions.

## 15 Uncertainty Impact

Separate layers must remain separate:

1. BLAST NMC model selection;
2. model form/parameters;
3. partial-charge/SOC capacity-label error;
4. cell-to-pack transfer;
5. parked SOC/temperature and relaxation;
6. field horizon versus 10–25-year projection;
7. capacity-conditioned resistance envelope;
8. use/climate/charging/thermal-management scenarios;
9. cross-source chemistry/protocol mismatch.

The evidence supports bounded scenarios, not a calibrated joint distribution or Monte Carlo sampling in this gate.

## 16 False-Optimum Impact

A capacity-only central curve could create a falsely precise replacement optimum while power loss, charging acceptance, and resistance-driven energy penalty remain unknown. A single BLAST fit creates the same risk if its tail is treated as measured.

Later work must reject/flag optima that:

- lie outside field-validation or P12 support;
- change materially across admissible NMC models/resistance envelopes;
- depend on unvalidated parked-temperature/SOC assumptions;
- infer resistance solely from capacity correlation;
- benefit from clipping, tail extension, chemistry pooling, or silent cell-to-pack scaling;
- treat the 25-year cap as physical evidence;
- appear stable only because structural uncertainty was omitted.

## 17 Revision Options

- **R1 only:** improves near-term field capacity but leaves resistance/full-life coverage unresolved.
- **R2 only:** supplies calendar/use mechanics and long-horizon capacity but remains extrapolative and lacks validated resistance.
- **R3:** combines explicit calendar/use capacity modeling, near-term field validation, and transparent resistance bounds. It is the only candidate that materially advances the blocker without claiming a field resistance trajectory.

No frozen decision changes until R3 specification, source audit, and acceptance tests are separately approved.

## 18 Recommended Source/Architecture

The recommended candidate is **R3 — hybrid bounded mapping**:

1. pre-register one or an envelope of commercial NMC BLAST-Lite models for capacity only; do not average unrelated chemistries or select by favorable lifecycle outcomes;
2. drive it with explicit operating, charging, parked, SOC, and battery-temperature histories;
3. validate near-term capacity independently against Liu, open Deng, and Schreiber vehicle evidence; use Qiushi Wang as methodological corroboration unless raw data become available;
4. retain Luh/Schreiber resistance as a capacity/stress-conditioned envelope, never a real-world resistance prediction;
5. label all years beyond direct field support as model projections with qualitative/structural bounds;
6. require P12 domain checks and a false-optimum gate before later replacement work.

This materially closes the capacity/calendar/use part, while leaving resistance explicit and unresolved. It does not close P14.5.

## 19 RQ Impact

The primary RQ can remain only if R3 is a bounded methodological revision and the future wording distinguishes:

- modeled real-world capacity trajectory;
- observed lab/automotive conditional resistance envelope;
- unidentified real-world resistance trajectory.

If a directly observed deterministic resistance path is mandatory, the evidence is inadequate and the RQ must narrow. If bounded resistance-state uncertainty is acceptable, the RQ can remain, with replacement timing conditional on the envelope rather than empirically identified `R(t)`.

## 20 Implementation Impact

No implementation occurred. A later approved revision would require isolated ingestion, pinned sources/checksums, an exposure generator, capacity-model wrappers, held-out field validation, P12 domain matching, resistance-envelope construction, and deterministic manifests.

Tests must cover source/version pinning, chemistry separation, calendar/use accounting, parked coverage, R10/R1s separation, absence of field-resistance claims, calibration/validation leakage, domain enforcement, long-horizon labels, deterministic regeneration, and false-optimum rejection. Existing P12–P14 artifacts must stay byte-identical unless separately approved.

## 21 Additional Data Required

Before implementation approval:

1. acquire/checksum the full Liu fleet, verify terms/schema, and document withheld-OCV impact;
2. acquire/checksum all Deng archives and reproduce capacity extraction unchanged;
3. inspect pinned BLAST classes, parameters, original data, outputs, licenses, exact subtype, and any genuine resistance output;
4. obtain/construct independently sourced driving/parking/charging/temperature profiles consistent with P14 mileage cases;
5. define quantitative field-validation criteria before model selection;
6. seek longitudinal automotive pack pulse-resistance/impedance data at compatible reference conditions;
7. if unavailable, pre-register a P12/Schreiber conditional-envelope algorithm that never leaves observed support;
8. record missingness, precision, maintenance/replacement, and software changes where available.

## 22 Hard Blockers Remaining

The original blocker is narrowed, not removed:

- `RESISTANCE REAL-WORLD TRAJECTORY NOT IDENTIFIED`;
- no independent 10–25-year field validation;
- incomplete parked SOC, cell-temperature, and relaxation observability;
- chemistry-subtype and cell-to-pack uncertainty;
- Liu full-artifact terms and exact label reproducibility unverified;
- no approved hourly exposure architecture from P14 mileage to model inputs;
- no approved validation threshold or resistance-envelope method;
- no change-control approval to add sources or revise the bridge.

P14.5 remains failed, the fresh-only canonical bridge remains authoritative, and P15 remains prohibited.

## 23 Final Recommendation

**Recommendation:** `SOURCE EXPANSION POSSIBLE WITH BOUNDS`

**Source-expansion test:** passed only for identifying a material candidate. Liu/Deng/Qiushi Wang strengthen near-term field capacity evidence, and Wu/BLAST supplies an inspectable calendar-plus-use capacity architecture. Evidence does not identify a compatible field resistance trajectory or validate a deterministic 10–25-year joint path. This is neither implementation approval nor a P14.5 pass.

**Final status:** `EVIDENCE EXPANSION CANDIDATE IDENTIFIED WITH BOUNDS`

**Stop condition:** No source freeze, code, configuration, bridge artifact, P13/P14 output, decision-log entry, lifecycle GHG result, replacement result, Monte Carlo result, manuscript text, or P15 work was created or modified. Await explicit approval for any next change-controlled step.
