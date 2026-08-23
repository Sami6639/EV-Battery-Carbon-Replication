# EV\_Battery\_Carbon\_Footprint — IMPLEMENTATION HANDOFF SPECIFICATION

**Target path:** `EV_Battery_Carbon_Footprint/docs/IMPLEMENTATION_SPEC.md`

**Status:** Frozen implementation handoff specification derived exclusively from Aşama 1–7 locked decisions.

**Governing protocol:** `PROJECT_INSTRUCTIONS.md`. The implementation must preserve scientific integrity, source traceability, reproducibility, uncertainty treatment, raw/processed-data separation, and the rule that scientific validity takes precedence over novelty claims, methodological complexity, and speed. fileciteturn0file0L29-L43 fileciteturn0file0L287-L335 fileciteturn0file0L633-L649

---

## 1. Locked Primary Research Question

### Primary RQ — LOCKED

> **Under what combinations of battery degradation, replacement-battery embodied emissions, remaining vehicle service life, and temporal decarbonization of charging electricity and battery manufacturing does the life-cycle-GHG-minimizing first-life battery decision in a battery electric vehicle favor early replacement, an interior retirement/replacement point, or continued use to the technical mobility boundary?**

### Locked Sub-RQ1

> **How does the balance between degradation-induced operational GHG penalties and replacement-battery embodied GHG emissions influence the preferred first-life battery decision regime?**

### Locked Sub-RQ2

> **How do remaining vehicle service life and technical mobility constraints condition whether replacing a degraded battery can yield a life-cycle GHG advantage over continued first-life use?**

### Locked Sub-RQ3

> **How does the joint decarbonization of charging electricity and replacement-battery manufacturing shift the conditions separating early-replacement, interior-replacement, and use-until-technical-boundary regimes?**

These questions must not be modified during implementation unless an explicit methodological-revision process is triggered.

---

## 2. Scientific Scope

### IN SCOPE

- BEV traction-battery **first-life continue-versus-replace decision**.
- Life-cycle GHG minimization.
- Battery degradation.
- Capacity fade.
- Resistance/loss-state growth.
- Degradation-induced operational energy penalty.
- Replacement-battery embodied GHG.
- Remaining vehicle service life.
- Technical mobility constraints.
- Time-varying charging-grid carbon intensity.
- Time-varying replacement-battery manufacturing carbon intensity.
- Uncertainty in the parameters required by these mechanisms.
- Classification of carbon-minimizing decision regimes.

### OUT OF SCOPE

- Whole-vehicle replacement optimization.
- Second-life optimization.
- Vehicle-fleet transition optimization.
- Battery-chemistry selection optimization.
- Full recycling-pathway optimization.
- Development of a detailed electrochemical degradation model.
- Charging-infrastructure optimization.
- Road-infrastructure optimization.
- Fleet-level technology-transition scenarios.

The scientific unit of analysis remains the **traction battery in a continuing focal BEV**.

---

## 3. Locked Functional Unit

### Functional Unit — LOCKED

> **Delivery of a fixed remaining vehicle-kilometre mobility service by the focal BEV over its residual vehicle service horizon.**

### Primary result metric

**Total kg CO₂e for the fixed remaining mobility service.**

### Secondary reporting metric

**g CO₂e/vkm.**

All candidate battery-retirement policies must deliver the same defined remaining mobility service. Policies must not be compared using unequal mobility outputs.

---

## 4. Locked Decision Architecture

### Decision unit

**The traction battery in the same continuing BEV.**

### Decision

**Continue first-life use versus replace the traction battery.**

### Decision representation

Replacement timing is represented jointly along:

- calendar time;
- cumulative mileage;
- capacity state;
- loss/resistance state.

The decision is therefore a **replacement timing/state decision along a joint degradation trajectory**.

### Hard rule

A fixed SOH threshold must **not** be used as the retirement decision rule.

In particular, a universal 70% or 80% SOH cutoff is prohibited as the optimization/decision criterion.

---

## 5. Locked Geography and Time

### Vehicle-use geography

**United States.**

### Grid geography

**U.S. Cambium architecture.**

Regional Cambium information may be aggregated consistently for the U.S. analysis, but the vehicle-use geography must remain U.S.-based.

### Battery-manufacturing geography

**Scenario-dependent supply-chain geography.**

Vehicle-use geography and battery-manufacturing geography must not be assumed to be identical.

### Temporal architecture

**Calendar-dependent prospective analysis with a dataset-supported horizon extending to 2050.**

Calendar time must determine, where applicable:

- charging-grid carbon intensity;
- replacement-battery manufacturing carbon intensity;
- candidate battery-replacement year;
- remaining vehicle-service horizon.

No unsupported extrapolation beyond the prospective-data horizon is permitted.

---

## 6. Locked Chemistry Strategy

### Primary chemistry

**Commercial mid/high-nickel NMC-family representation.**

The primary physical ageing evidence is NMC-family evidence.

### Manufacturing scenario

Use **NMC811** where explicitly supported by the battery-manufacturing dataset.

This must **not** be interpreted as evidence that the Luh & Blank primary ageing cell is exactly NMC811.

### Chemistry harmonization rule

NMC111, NMC532, NMC622, NMC811, and unspecified commercial NMC must not automatically be treated as identical physical chemistries.

Any subtype mismatch between physical-ageing evidence and manufacturing-carbon evidence must be retained as an uncertainty/interpretation limitation.

### Extension chemistry

**LFP — limited robustness/generalizability extension only.**

### NCA

**Excluded from the core analysis.**

NMC resistance parameters must never be transferred directly to LFP.

---

## 7. Locked Degradation State

### Primary dual-state representation

**Capacity SOH + effective internal/pulse resistance state.**

Capacity SOH alone is insufficient.

### Primary resistance specification

**10-ms pulse resistance.**

### Alternative resistance specification

**1-s pulse resistance.**

The 1-s specification is an alternative resistance-timescale specification, not an independent dataset.

### Independent automotive validation

**Schreiber automotive HPPC/DC-resistance evidence.**

### Scale-transfer variable

Use **relative resistance growth,** **`R/R0`****,** as the primary transferable ageing signal rather than directly copying the absolute resistance of a laboratory cell into the representative vehicle pack.

### Required conditioning

- SOC matching/normalization.
- Temperature matching/normalization.

### Primary reference temperature

**25°C.**

Temperature-dependent ageing histories may vary, but instantaneous resistance comparisons used for physical translation must use consistent temperature conditions.

---

## 8. Frozen Core Data Sources

| Parameter / evidenceRolePrimary sourceDOI / dataset IDStatusImplementation note |                                     |                                |                                                                            |                                      |                                                                              |
| ------------------------------------------------------------------------------- | ----------------------------------- | ------------------------------ | -------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------- |
| NMC capacity degradation                                                        | Primary ageing evidence             | Luh & Blank 2024               | Article: `10.1038/s41597-024-03831-x`; Dataset: `10.35097/1947`            | **LOCKED SOURCE**                    | Capacity state, calendar/cycle ageing, operating-condition variability       |
| NMC pulse-resistance degradation                                                | Primary loss-state evidence         | Luh & Blank 2024               | Article: `10.1038/s41597-024-03831-x`; Dataset: `10.35097/1947`            | **LOCKED SOURCE**                    | Primary 10-ms; alternative 1-s; SOC/T matched                                |
| Automotive NMC degradation validation                                           | Independent automotive plausibility | Schreiber et al. 2025          | Article: `10.1016/j.est.2025.115357`; Dataset: `10.14459/2024mp1755598`    | **LOCKED SOURCE**                    | Automotive pouch-cell capacity/resistance behaviour; not forced to equal Luh |
| Cell/pack/vehicle multiscale plausibility                                       | Vehicle-scale physical validation   | TUM VW ID.3 multiscale dataset | `10.14459/2022mp1656314`                                                   | **LOCKED SOURCE**                    | Cell HPPC/EIS, vehicle/dynamometer, driving and charging evidence            |
| Vehicle physics framework                                                       | Baseline/drive-cycle translation    | FASTSim                        | Implementation version: **v3.0.6**; validation DOI: `10.2172/1828851`      | **FROZEN IMPLEMENTATION SOURCE**     | Option A only; no battery-ageing generation                                  |
| U.S. annual mileage/use pattern                                                 | Mobility/exposure                   | NHTS 2022 V2.1                 | Official FHWA/NHTS identifier; DOI **NOT VERIFIED / not required**         | **LOCKED SOURCE**                    | Central empirical use + low/high/use-distribution treatment                  |
| Vehicle survival                                                                | Remaining vehicle life              | Greene & Leard 2024            | `10.1016/j.tra.2024.103982`                                                | **LOCKED SOURCE**                    | Vehicle-age-conditioned U.S. survival                                        |
| Primary grid carbon                                                             | Time-varying average CI             | Cambium 2024                   | `10.7799/2560791`                                                          | **LOCKED SOURCE**                    | Primary U.S. average-grid architecture                                       |
| LRMER sensitivity                                                               | Long-run marginal sensitivity       | Cambium 2023 LRMER             | `10.7799/2305481`                                                          | **SENSITIVITY LIMITATION**           | Must be labelled `Cambium-2023 LRMER sensitivity`                            |
| Prospective battery-manufacturing GHG                                           | Replacement battery embodied GHG    | Llamas-Orozco et al. 2023      | Article: `10.1093/pnasnexus/pgad361`; Data: `10.6084/m9.figshare.23454449` | **LOCKED SOURCE**                    | Primary pack-level prospective manufacturing source                          |
| Manufacturing temporal robustness                                               | Independent prospective trend check | Xu et al. 2022                 | `10.1016/j.resconrec.2022.106606`                                          | **LOCKED SOURCE**                    | Cell-level boundary; do not average directly with pack-level factors         |
| Charging conversion/loss evidence                                               | Battery-side → grid-side conversion | Sevdari et al. 2023            | `10.1016/j.seta.2023.103512`                                               | **LOCKED SOURCE**                    | Independent charging conversion evidence                                     |
| Primary recycling-process evidence                                              | Conservative EoL accounting         | Hanna, Somers & Anctil 2025    | `10.1021/acs.est.4c13838`                                                  | **PROVISIONAL / ACCOUNTING SOURCE**  | Use process burdens only where boundary separation is supported              |
| Recycling allocation sensitivity                                                | Sensitivity-only allocation check   | Du et al. 2022                 | `10.1021/acs.est.2c05755`                                                  | **PROVISIONAL / SENSITIVITY SOURCE** | Never drive primary retirement objective                                     |
| LFP ageing extension                                                            | Limited LFP robustness              | Wheeler et al. 2025            | `10.1038/s41597-025-04712-7`                                               | **VALIDATION/EXTENSION SOURCE**      | Chemistry-specific LFP treatment only                                        |
| LFP vehicle-scale plausibility                                                  | Limited LFP validation              | TUM Tesla Model 3 LFP dataset  | `10.14459/2024mp1735494`                                                   | **LOCKED VALIDATION SOURCE**         | Validation only; no NMC parameter transfer                                   |

No unverified DOI or identifier may be invented during implementation.

---

## 9. Locked Cell-to-Pack-to-Vehicle Chain

The implementation must preserve the following conceptual chain:

**cell degradation state**
→ **capacity + relative resistance state**
→ **topology-aware pack equivalent state**
→ **drive-cycle power/current demand**
→ **incremental degradation-dependent electrical loss**
→ **battery-side energy for fixed mobility**
→ **charging conversion**
→ **grid-side electricity**
→ **calendar-specific operational GHG**

### Hard prohibition

> **A percentage increase in cell resistance must NEVER be mapped directly to the same percentage increase in vehicle kWh/km.**

Cell state, pack state, and vehicle state are distinct scales.

Pack topology, voltage/current conditions, SOC, regenerative operation, and baseline non-ageing losses must mediate the physical translation.

---

## 10. FASTSim Role

### FASTSim — Option A only

FASTSim may be used for:

- fresh/reference vehicle power demand;
- representative drive-cycle vehicle physics;
- baseline battery-side energy translation;
- physical feasibility/plausibility checks at vehicle scale.

FASTSim must **not** be used to:

- generate battery capacity-ageing trajectories;
- generate resistance-ageing trajectories;
- replace the locked experimental NMC ageing datasets;
- infer ageing parameters from carbon results.

Battery ageing comes from the locked experimental degradation sources.

FASTSim implementation must use the frozen version:

**v3.0.6**

unless an explicit methodological-revision process is approved.

---

## 11. Locked Energy Accounting Boundary

### Primary calculation pipeline

**FASTSim / vehicle physics**
→ **HV battery-side electrical energy**
→ **degradation-dependent incremental pack loss**
→ **independently parameterized charging conversion**
→ **grid-side charging electricity**
→ **calendar-specific grid carbon intensity**

### Validation pipeline

**EPA / Transportation ATB charging-inclusive wall/grid-side metrics.**

EPA/ATB values are external plausibility benchmarks, not additional charging-loss components.

### Hard no-double-counting rule

If an EPA/ATB metric already includes charging/EVSE/onboard-conversion losses:

> **DO NOT add an additional charging-loss factor.**

Primary and validation pipelines must remain separate.

---

## 12. Technical Mobility Boundary

There is no universal 70% or 80% SOH technical EOL rule.

Technical feasibility requires the simultaneous satisfaction of:

1. **minimum energy/range service**;
2. **minimum power service**.

These boundaries must be defined from the required vehicle/mobility service, not by arbitrary SOH percentages.

Potential physical quantities underlying the boundary may include usable energy, deliverable pack power, voltage sag, and BMS voltage/current feasibility, but implementation must remain parsimonious and must not expand into a detailed vehicle-dynamics research project.

---

## 13. Vehicle-Life Representation

### Locked representation

**Vehicle-age-conditioned survival distribution.**

### Primary provenance

**Greene & Leard 2024 — DOI** **`10.1016/j.tra.2024.103982`****.**

The remaining service horizon must therefore depend on current vehicle age rather than a single arbitrary remaining-life assumption.

### Replacement-battery burden rule

The embodied GHG burden of a replacement battery is incurred when the replacement occurs.

If the vehicle retires before the replacement battery reaches its own physical end of life:

- no automatic burden amortization beyond actual vehicle service;
- no automatic second-life credit;
- no assumption that unused battery capacity is environmentally recovered.

This is necessary for the remaining-vehicle-life mechanism in the locked RQ.

---

## 14. Grid Architecture

### Primary grid accounting

**Cambium 2024 time-varying average grid carbon intensity.**

Official dataset identifier:

`10.7799/2560791`

### Sensitivity

**Cambium 2023 LRMER.**

Official dataset identifier:

`10.7799/2305481`

### Mandatory label

> **Cambium-2023 LRMER sensitivity**

### Forbidden label

> `Cambium-2024 marginal emissions`

unless a future explicit methodological revision verifies and adopts a version-matched 2024 LRMER source.

The current mismatch is a **documented sensitivity limitation**, not an architecture conflict.

Average-grid accounting remains the primary model.

---

## 15. Battery Manufacturing Architecture

### Primary

**Time-varying prospective pack-level battery-manufacturing GHG from Llamas-Orozco et al. 2023.**

Article DOI:

`10.1093/pnasnexus/pgad361`

Data DOI:

`10.6084/m9.figshare.23454449`

Replacement-battery manufacturing burden must vary with calendar time according to the selected source-defined pathway.

### Static benchmark

Freeze the **same source's entry/base-year manufacturing factor** through time.

This static benchmark must therefore differ from the primary model only in temporal treatment, not through an unrelated system boundary.

### Robustness

**Xu et al. 2022 — DOI** **`10.1016/j.resconrec.2022.106606`****.**

Xu et al. may be used for temporal/manufacturing trend robustness.

### Hard boundary rule

Do **not** directly average or pool:

- cell-level kg CO₂e/kWh;
- pack-level kg CO₂e/kWh

across incompatible system boundaries.

Cell-to-pack LCA boundary conversion is not a simple unit conversion.

---

## 16. Recycling Architecture

### Primary treatment

**Conservative cut-off treatment.**

Include only the recycling-process burdens required by the locked system boundary.

Where material and supported by the inventory, these may include:

- collection/transport;
- dismantling;
- recycling-process energy/emissions.

### Primary-objective rule

> **Do not include avoided virgin-production credits in the primary retirement optimization objective.**

### Alternative treatment

Recycling-credit/allocation methods may be used **only as sensitivity analyses**.

### Decision-variable rule

Recycling is **not** an optimization decision variable.

Recycling assumptions must not create an artificial incentive for early battery replacement.

---

## 17. False-Optimum Hard Gate

An interior retirement regime must **not** be reported as a robust scientific result if any of the following applies:

- it appears only under the 10-ms resistance specification and disappears under the alternative specification;
- it disappears under Schreiber-compatible automotive evidence;
- it requires resistance growth outside automotive plausibility bounds;
- it occurs only in the extreme tail of the admissible physical envelope;
- it requires extrapolation outside the observed ageing domain;
- it relies on a proportional `R-growth → proportional kWh/km-growth` shortcut;
- it relies on assuming that all pack parasitic losses age proportionally with cell resistance;
- it disappears under plausible grid pathways;
- it disappears under plausible battery-manufacturing pathways;
- it appears only under extreme remaining-vehicle-life assumptions.

### Required regime classifications

Implementation outputs must classify outcomes using, as appropriate:

- **ROBUST INTERIOR REGIME**
- **CONDITIONAL INTERIOR REGIME**
- **NON-ROBUST PHYSICAL OPTIMUM**
- **EARLY-REPLACEMENT REGIME**
- **USE-UNTIL-TECHNICAL-BOUNDARY REGIME**

An interior optimum is **not** the required scientific result.

Persistent dominance of **USE-UNTIL-TECHNICAL-BOUNDARY** is an equally valid scientific outcome.

---

## 18. Admissible Physical Envelope

Only degradation/loss trajectories satisfying **all** of the following may enter the main simulation:

1. trajectory remains within the observed Luh degradation domain;
2. SOC and temperature are matched/normalized appropriately;
3. behaviour is physically compatible with Schreiber automotive NMC evidence;
4. resulting pack/vehicle behaviour remains feasible under TUM/FASTSim vehicle constraints;
5. no arbitrary extrapolation outside the validated degradation domain occurs.

### Additional rules

- No single best-fit trajectory may represent the complete physical uncertainty.
- 10-ms and 1-s resistance definitions remain distinct physical specifications.
- Schreiber evidence is an independent automotive plausibility test.
- TUM evidence is a multiscale vehicle-level plausibility test.
- Envelope-tail cases must be explicitly labelled **conditional** or **extreme**.
- Cases outside the admissible envelope must not be silently clipped or retained.

---

## 19. Uncertainty Architecture

### No-cherry-picking rule

Parameter values must never be selected because they produce a desirable, publishable, or visually attractive interior optimum.

Use only:

- source-derived distributions;
- replicate variability;
- literature-supported ranges;
- pre-specified scenario sets;
- source-defined prospective pathways.

### Minimum propagated uncertainties

Implementation must propagate uncertainty in at least:

- capacity degradation;
- resistance growth;
- annual mileage;
- vehicle survival;
- grid pathway;
- battery-manufacturing pathway;
- charging conversion;
- mobility-boundary parameters materially affecting feasibility.

Where an exact probability distribution is not scientifically supported, use bounded scenarios/ranges rather than inventing a probability model.

Parameter uncertainty and scenario uncertainty must remain distinguishable.

---

## 20. Data Storage Contract

Required project structure:

```
EV_Battery_Carbon_Footprint/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── literature/
├── src/
├── results/
├── tables/
├── figures/
├── manuscript/
├── docs/
│   └── IMPLEMENTATION_SPEC.md
└── PROJECT_INSTRUCTIONS.md
```

This structure is consistent with the governing project's required separation of data, code, results, tables, figures, manuscript files, and supporting documentation. fileciteturn0file0L517-L571

### `data/raw/`

- Immutable.
- Source files preserved exactly as obtained.
- Never overwritten.
- Never manually edited.

### `data/processed/`

- Harmonized/filtered/model-ready data.
- Must always be reproducible from raw data by code.
- No manual numerical corrections.

### `data/metadata/`

For every external dataset/source, record where applicable:

- source title;
- authors/institution;
- DOI or official identifier;
- source URL/reference;
- dataset/software version;
- retrieval date;
- licence/use restrictions;
- original filename;
- chemistry;
- geography;
- temporal scope;
- system/measurement level;
- original units;
- transformation lineage;
- processing script/version;
- SHA-256 checksum where practical.

---

## 21. Implementation Reproducibility Rules

All implementation must be reproducible.

Required controls:

- Python environment managed through **Anaconda/Conda**;
- pinned package versions;
- deterministic random seeds wherever stochastic operations occur;
- configuration-driven scientific parameters;
- no manually edited numerical model outputs;
- no overwrite of raw data;
- all processed datasets reproducible by code;
- all tables generated from code;
- all figures generated from code;
- dataset versions logged;
- model/configuration versions logged;
- run configuration logged;
- separation of raw data, processed data, code, intermediate results, final results, tables, and figures.

The governing protocol explicitly requires reproducible quantitative work, deterministic handling of randomness where applicable, immutable raw data, and code-generated tables/figures. fileciteturn0file0L283-L335

---

## 22. Forbidden Implementation Shortcuts

The following are prohibited:

1. Hard-coding a desired optimum.
2. Adjusting/fitting degradation parameters after inspecting carbon-regime results.
3. Changing resistance definitions because another definition generates a more attractive result.
4. Silently changing system boundaries.
5. Mixing incompatible cell-level and pack-level battery-manufacturing footprints without explicit boundary reconciliation.
6. Double counting charging losses.
7. Using a fixed 70% or 80% SOH as technical EOL.
8. Treating capacity SOH as the sole degradation descriptor.
9. Transferring NMC resistance parameters directly to LFP.
10. Transferring old LMO numerical degradation penalties directly to modern NMC/LFP.
11. Using second-life credits to artificially favour early replacement.
12. Using recycling avoided-burden credits in the primary optimization objective.
13. Treating Cambium-2023 LRMER sensitivity as the primary grid-accounting result.
14. Calling Cambium-2023 LRMER `Cambium-2024 marginal emissions`.
15. Directly mapping a percentage increase in cell resistance to the same percentage increase in kWh/km.
16. Assuming all pack parasitic losses grow proportionally with cell resistance.
17. Arbitrarily extrapolating degradation outside the experimentally supported domain.
18. Selecting only the grid, manufacturing, mileage, or vehicle-life scenario that produces the preferred regime.
19. Reporting excessive numerical precision unsupported by input uncertainty.
20. Manually changing generated results, tables, or figures.
21. Quietly replacing a locked dataset because another dataset produces a cleaner result.

---

## 23. Implementation Order

Implementation must proceed in the following sequence.

### Step 1 — Environment and reproducibility setup

- Create Conda environment.
- Pin Python/packages.
- Record environment specification.
- Pin FASTSim v3.0.6.
- Establish deterministic-seed convention.

### Step 2 — Source-data acquisition

Acquire only frozen/approved sources or sources explicitly required by the existing registry.

### Step 3 — Raw-data provenance and checksums

- Preserve original files.
- Record DOI/identifier/version/licence.
- Compute checksum where practical.

### Step 4 — Data schemas

Define canonical schemas and units before numerical transformation.

### Step 5 — NMC degradation preprocessing

Process capacity ageing while preserving experimental-condition identifiers and replicate information.

### Step 6 — Resistance-state preprocessing

Prepare:

- primary 10-ms resistance state;
- alternative 1-s resistance state;
- SOC/T conditioning;
- relative `R/R0` representation.

### Step 7 — Automotive validation

Test Luh-derived behaviour against Schreiber automotive NMC evidence.

Do not tune Luh behaviour to match carbon outcomes.

### Step 8 — Representative BEV / FASTSim baseline

Establish reference vehicle physics, drive-cycle demand, and battery-side baseline energy.

### Step 9 — Cell → pack scaling

Apply topology-aware scaling and maintain separation between ageing cell resistance and non-ageing pack parasitics.

### Step 10 — Pack → vehicle energy translation

Generate degradation-dependent incremental battery-side energy penalty within the admissible physical envelope.

### Step 11 — Mobility and survival data

Integrate:

- annual mileage/use pattern;
- remaining mobility;
- vehicle-age-conditioned survival;
- technical range/power feasibility.

### Step 12 — Grid pathways

Prepare Cambium 2024 average-grid pathways.

Cambium-2023 LRMER remains sensitivity-only.

### Step 13 — Battery-manufacturing pathways

Prepare:

- Llamas-Orozco prospective pack-level primary pathway;
- frozen static benchmark;
- Xu temporal robustness treatment.

### Step 14 — Recycling accounting

Implement conservative primary cut-off treatment and clearly separate optional allocation sensitivity.

### Step 15 — Integrated lifecycle engine

Integrate all policy-varying and accounting-only GHG components without changing locked system boundaries.

### Step 16 — Candidate replacement decision logic

Evaluate continue-versus-replace candidate decisions over the feasible battery/vehicle state domain.

No desired optimum may be encoded.

### Step 17 — Uncertainty propagation

Propagate the pre-specified physical, mobility, survival, grid, manufacturing, charging, and technical-boundary uncertainties.

### Step 18 — False-optimum robustness gates

Apply the physical, temporal-carbon, and vehicle-life gates defined in this specification.

### Step 19 — Validation

Perform internal consistency, boundary, unit, physical plausibility, and external vehicle-energy checks.

### Step 20 — Final tables and figures

Generate all numerical outputs from the validated pipeline.

No implementation step may bypass a required validation gate.

---

## 24. Change-Control Rule

All scientific and methodological decisions contained in this `IMPLEMENTATION_SPEC.md` are **FROZEN**.

If implementation shows that a frozen decision cannot be implemented scientifically:

# STOP

Do not silently modify the implementation.

Create an explicit methodological-revision record containing:

1. **Frozen decision**
2. **Implementation conflict**
3. **Evidence demonstrating the conflict**
4. **Proposed change**
5. **Scientific consequence**
6. **Effect on comparability with previous locked design**
7. **Whether Primary RQ, architecture, data provenance, or interpretation is affected**

No revised implementation may proceed until the methodological revision is explicitly approved.

A computational inconvenience is **not** sufficient reason to change a frozen scientific decision.

A result that fails to produce an interior optimum is **not** sufficient reason to change a frozen decision.

---

## 25. Final Handoff Status

# IMPLEMENTATION HANDOFF READY

Aşama 1–7 boyunca kilitlenen:

- Primary RQ;
- sub-RQs;
- scientific scope;
- functional unit;
- decision architecture;
- geography;
- temporal structure;
- chemistry strategy;
- degradation-state representation;
- core provenance sources;
- cell→pack→vehicle physical bridge;
- energy-accounting boundary;
- technical mobility boundary;
- vehicle-life architecture;
- grid architecture;
- battery-manufacturing architecture;
- recycling treatment;
- uncertainty architecture;
- false-optimum rejection rules;
- reproducibility contract;
- change-control procedure

tek bir frozen implementation specification altında birleştirilmiştir.

Documented limitation remains:

> **Cambium-2023 LRMER is sensitivity-only and must not be represented as a version-matched Cambium-2024 marginal-emissions source.**

Bu sınırlama primary modelin implementation readiness durumunu bozmaz.

**Next action:**

> **Anaconda environment setup + Codex implementation initialization.**

---

# P14.6C — APPROVED TRAJECTORY-FREE METHODOLOGICAL REVISION

**Change-control approval date:** 2026-08-21  
**Authority:** explicit approval of Option B following `docs/P146_TRAJECTORY_FREE_ARCHITECTURE_ASSESSMENT.md`  
**Pre-amendment SHA-256:** `f8e29917daa0a4f999088005e0c85dffd6cc3cf3f828b1198dce4b6c1c1d3a80`  
**Pre-amendment byte size:** `32002`  
**Pre-amendment line count:** `844`

This append-only amendment is authoritative for all prospective work. Conflicting earlier trajectory-, timing-, early/interior-, and use-until-boundary instructions remain above as immutable audit history but are **superseded prospectively** by P14.6C. No future implementation may return to trajectory optimization without a new explicit scientific revision.

## P14.6C.1 Reason and Preserved Failure Evidence

The original decision architecture required an ordered joint capacity/resistance degradation trajectory to identify early replacement, an interior retirement/replacement point, or continued use until a future technical boundary. That required scientific object was not validated:

- P14.5 remains `REAL-WORLD DEGRADATION BRIDGE FAIL`;
- P14.5I remains `R3 REAL-WORLD DEGRADATION BRIDGE FAIL`;
- the P14.5I external capacity gate failed its pre-registered criteria;
- zero R3 joint bridge rows were admissible; and
- deterministic real-world `R(t)` remains unavailable.

These are binding failures, not near-passes. All historical reports and decision-log entries remain immutable. The revision salvages only the scientifically supported current-state, vehicle-translation, and exogenous-context evidence.

## P14.6C.2 Formal Architecture Decision

The approved architecture is:

> **OPTION B — TRAJECTORY-FREE STATE-CONDITIONED ROBUST / PARTIAL-IDENTIFICATION ARCHITECTURE**

Roles are locked:

- **S2 = PRIMARY:** robust dominance through mechanistic set identification;
- **S1 = SUPPORTING ONLY:** symmetric policy accounting and endpoint-bound construction;
- trajectory optimization, time-to-state prediction, and point-optimal retirement are not part of the prospective architecture.

## P14.6C.3 Original and Revised Research Questions

The original Primary RQ and Sub-RQs remain in §1 as historical text. Their prospective status is:

> `SUPERSEDED BY APPROVED METHODOLOGICAL REVISION`

### REVISED PRIMARY RQ — LOCKED

> **Conditional on an empirically admissible current battery capacity–resistance state, under what combinations of remaining vehicle service, replacement-battery embodied emissions, and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths are unidentified?**

### REVISED SUB-RQ1 — LOCKED

> **What lower and upper bounds can be placed on the life-cycle-GHG contrast between immediate battery replacement and continued first-life use, conditional on an empirically admissible current capacity–resistance state and residual mobility service, without assuming a real-world degradation trajectory?**

### REVISED SUB-RQ2 — LOCKED

> **How do the current usable-capacity and pulse-resistance states, evaluated against the required mobility and power service, determine whether continued first-life use and immediate replacement are technically admissible before carbon comparison?**

### REVISED SUB-RQ3 — LOCKED

> **How do residual vehicle service and temporal charging-grid and replacement-battery manufacturing decarbonization widen, narrow, or change the sign classification of the identified life-cycle-GHG interval?**

These wordings are frozen before numerical lifecycle results and must not be altered after inspecting future carbon results.

## P14.6C.4 Scientific Estimand and Sign Convention

For immediate replacement policy (R), continuation policy (C), matched exogenous decision context (z), replacement future-state treatment (\theta_R\in\Theta_R), and continuation future-state treatment (\theta_C\in\Theta_C), the estimand is:

\[
\Delta G(z,\theta_R,\theta_C)
=G_R(z,\theta_R)-G_C(z,\theta_C). \tag{P14.6C-1}
\]

Positive (\Delta G) means replacement has higher lifecycle GHG than continuation. Negative (\Delta G) means replacement has lower lifecycle GHG. No probability interpretation is implied.

The identification design is exactly:

> `MECHANISTIC SET IDENTIFICATION`

It is not population-statistical partial identification and cannot support fleet prevalence or policy probabilities without separate representative evidence.

## P14.6C.5 Identified Interval and Carbon Classifications

The locked interval is:

\[
\underline{\Delta G}(z)=
\inf_{(\theta_R,\theta_C)\in\Theta(z)}
\Delta G(z,\theta_R,\theta_C),
\qquad
\overline{\Delta G}(z)=
\sup_{(\theta_R,\theta_C)\in\Theta(z)}
\Delta G(z,\theta_R,\theta_C). \tag{P14.6C-2}
\]

Primary carbon labels are locked exactly:

- if `lower_DeltaG > 0`: `ROBUST CONTINUE`;
- if `upper_DeltaG < 0`: `ROBUST REPLACE`;
- if `lower_DeltaG <= 0 <= upper_DeltaG`: `CARBON DECISION INDETERMINATE`.

`POTENTIALLY BENEFICIAL` is allowed only as a non-recommendation qualifier when some admissible replacement contrasts are negative but robustness is absent.

The earlier `EARLY-REPLACEMENT REGIME`, `INTERIOR`/`ROBUST INTERIOR REGIME`, and `USE-UNTIL-TECHNICAL-BOUNDARY REGIME` labels are historical only and are prohibited as prospective carbon-regime outputs.

## P14.6C.6 Technical Classifications Are Independent

Allowed technical labels are:

- `CONTINUE TECHNICALLY FEASIBLE`;
- `CONTINUE TECHNICALLY INFEASIBLE`;
- `REPLACEMENT TECHNICALLY FEASIBLE`;
- `REPLACEMENT TECHNICALLY INFEASIBLE`;
- `STATE OUTSIDE DECISION DOMAIN`.

Technical feasibility is evaluated before carbon classification. If continuation fails the required service and replacement passes it, replacement may be technically required within the two-policy service-preserving choice set. This does not imply `ROBUST REPLACE` on carbon grounds. No universal 70% or 80% SOH technical rule is permitted.

## P14.6C.7 Current-State Admissibility

An `empirically admissible current state` means a capacity/resistance combination inside the validated P12/P13 physical evidence domain. Entry requires:

- physical `reconstructed_capacity_retention`;
- a supported primary R10 state or envelope;
- a separate R1s alternative where available;
- compatible SOC and reference temperature;
- P12 state-domain validity; and
- P13 translation-domain validity.

It does not mean representative fleet frequency, probability of observing the state, or a typical real-vehicle state at a specified age. P12 experimental elapsed day must not become vehicle age. Time-to-state is not used. A future vehicle-specific case study requires a separately compatible current-state measurement.

## P14.6C.8 Continue Policy Set Θ_C

The minimum continuation endpoint construction is pre-registered:

- `C_LOW`: hold the current admissible state constant over matched residual service. This is an optimistic operational-penalty bound, not a prediction that degradation stops.
- `C_HIGH`: allow the worst technically feasible P12/P13-supported degradation-energy state under the same chemistry and reference architecture. This is a pessimistic operational-penalty bound, not a predicted jump or trajectory.

No intermediate path or state-occupancy probability is inferred.

## P14.6C.9 Replacement Policy Set Θ_R

The minimum replacement endpoint construction is pre-registered:

- `R_LOW`: hold fresh/reference replacement performance constant over matched residual service. This is an optimistic operational-penalty bound, not a prediction.
- `R_HIGH`: allow the replacement battery to occupy the same scientifically admissible worst-state rules used for continuation, subject to chemistry and system compatibility. This is a pessimistic operational-penalty bound, not a trajectory.

Replacement cannot receive a structurally more favourable future-state rule than continuation.

## P14.6C.10 Policy Symmetry Hard Gate

Future-state uncertainty treatment must be policy-symmetric unless a physical difference is pre-specified and scientifically justified before carbon results.

The following are prohibited as the only comparison:

- fresh-forever replacement versus worst-state-forever continuation; and
- worst-state-forever replacement versus current-state-forever continuation.

Any permitted asymmetry must name its physical mechanism, affected policy, evidence, and consequence for interval interpretation.

## P14.6C.11 Joint Set Θ(z) and Coupling

`Θ(z)` is the admissible joint policy-state set conditional on a matched exogenous context. It is not automatically the unrestricted Cartesian product of all policy states and all scenarios.

The joint set must:

1. preserve chemistry, system, SOC, temperature, and resistance-timescale compatibility;
2. preserve the same applicable exogenous context across both policies;
3. exclude mutually incompatible state combinations;
4. preserve any scientifically necessary coupling;
5. reject cross-matched exogenous corners chosen merely to maximize interval width; and
6. fail closed when compatibility cannot be established.

## P14.6C.12 Shared Exogenous Context z

For each contrast, both policies share the same applicable:

- decision calendar year;
- current vehicle age;
- mileage and residual-service treatment;
- vehicle-survival treatment;
- charging-conversion scenario;
- grid pathway and geography;
- technical-service definition;
- logically shared manufacturing context; and
- 2050 operational truncation.

Grid and manufacturing pathway choices are evaluated as matched (z) contexts, not mixed into (\Theta) by pairing a favourable policy corner with an unfavourable one.

## P14.6C.13 Policy Accounting and Operational Energy

Original battery manufacturing is included once in total LCA and is a common invariant in (\Delta G). It must not drive the policy contrast.

Replacement manufacturing applies only to policy (R): replacement pack capacity multiplied by the calendar-year, chemistry/pathway-specific Llamas pack-level GHG factor. The same boundary rules, manufacturing-geography limitation, and in-domain temporal treatment remain binding.

P13 enters operational bounds as follows:

- capacity affects usable stored energy and range feasibility;
- resistance affects only the incremental ageing-sensitive resistive-energy penalty;
- capacity retention does not directly scale traction energy;
- percent resistance growth is not percent vehicle-energy growth; and
- P14 charging conversion is applied without EPA/ATB double counting.

No automatic second-life credit or post-retirement service for the replacement battery is permitted.

## P14.6C.14 Grid, Survival, and Remaining Service

Primary grid accounting remains Cambium 2024 average CI with the load-weighted U.S. representation, 18-region robustness, exact `MidCase`/`LowRECost`/`HighRECost` labels, piecewise-linear in-domain interpolation, and the 2025–2050 limit. `Cambium-2023 LRMER sensitivity` remains sensitivity-only.

Vehicle survival may define or weight residual service but cannot assign degradation state. Both policies use matched survival treatment. No service is credited after focal-vehicle retirement, and no second-life credit is introduced.

## P14.6C.15 Resistance Evidence and Timescale Tiers

Two physical-evidence tiers are locked:

- **MAIN IDENTIFIED SET:** `PRIMARY PHYSICAL SPECIFICATION` plus `AUTOMOTIVE-COMPATIBLE ENVELOPE`, subject to P12/P13 validity;
- **STRESS / EXTREME SET:** separately labelled `EXTREME / CONDITIONAL ENVELOPE` only.

Stress states cannot silently become headline evidence. A main `ROBUST REPLACE` or `ROBUST CONTINUE` claim cannot exist solely because extreme states were included or excluded opportunistically.

R10 is the primary resistance specification. R1s is a separate alternative physical robustness specification. If their sign classifications reverse, the main result is not robust. Their intervals are not numerically merged, and timescale switching is prohibited.

## P14.6C.16 Pack-Loss Share and Technical-Service Hierarchy

All P13 ageing-sensitive pack-loss shares—0.50, 0.75, and 1.00—remain in the declared main robustness set. No share may be selected after results because it creates a more decisive classification.

The P14 technical service hierarchy is locked before carbon results:

- `mobility_central` is the primary mobility requirement;
- `mobility_lower` and `mobility_upper` are structured robustness requirements;
- the P13 fixed-cycle discharge and regenerative-acceptance power requirements apply to every tier.

This hierarchy prevents the most extreme mobility threshold from silently defining the headline classification while retaining the full bounded family for robustness.

## P14.6C.17 Scenario and Result Hierarchy

The **PRIMARY IDENTIFIED SET** uses P12/P13-supported main physical states, R10, all declared P13 pack-loss shares, central mobility, central mileage, the central 4.5-year survival-scale assumption, p50 charging efficiency, and load-weighted U.S. grid geography. `MidCase`, `LowRECost`, and `HighRECost`, together with prospective `SPS` and `SDS` manufacturing pathways, are evaluated as separate matched (z) contexts rather than pooled corners.

The **STRUCTURAL ROBUSTNESS SET** contains R1s, lower/higher mileage, lower/upper mobility requirements, 3.5/5.5-year survival-scale assumptions, p10/p90 charging efficiency, 18 GEA regional series, the static same-source 2020 `Current` manufacturing benchmark, and `Cambium-2023 LRMER sensitivity` under its mandatory label.

The **EXTREME / STRESS SET** contains only explicitly labelled extreme/conditional physical-state evidence and is not headline-eligible.

Future reporting order is locked:

1. `PRIMARY CLASSIFICATION`;
2. `STRUCTURAL ROBUSTNESS`;
3. `EXTREME/STRESS RESULT`;
4. `TECHNICAL FEASIBILITY`.

No undifferentiated mega-envelope may pool all layers unless a later explicit scientific revision justifies it.

## P14.6C.18 Revised Non-Robustness Gate

A carbon classification is `NON-ROBUST` if it:

- depends only on extreme/conditional resistance states;
- reverses between R10 and R1s;
- reverses across admissible pack-loss shares;
- depends on an unsupported mobility or power assumption;
- exists only under one extreme residual-service treatment;
- exists only under one grid/manufacturing pathway when those pathways are part of the target uncertainty set;
- treats state bounds as predicted trajectories;
- requires unsupported interpolation, extrapolation, or clipping;
- uses asymmetric policy-state assumptions without physical justification;
- depends on mismatched exogenous scenario corners; or
- changes sign when any required admissible state treatment is restored.

The gate is applied before interpretation and cannot be relaxed after seeing carbon results.

## P14.6C.19 Prohibited Prospective Claims and Outputs

The revised architecture must never output or claim:

- optimal retirement year;
- optimal SOH;
- optimal resistance;
- optimal battery age;
- time-to-state or mileage-to-state;
- a predicted real-world degradation path;
- deterministic resistance growth with age;
- early/interior/use-until-boundary carbon regimes;
- percentage of EVs that should replace;
- probability of `ROBUST REPLACE`; or
- prevalence of a degradation state without a separately validated representative fleet-state distribution.

The estimand is only the sign and bounds of immediate replacement versus continuation conditional on current admissible state and matched context.

## P14.6C.20 Revised Prospective Stage Sequence

### P15R — STATE-CONDITIONED LIFECYCLE-GHG ACCOUNTING ENGINE

P15R may begin only after a separate explicit instruction. Its role is limited to implementing (G_R) and (G_C), verifying units and boundaries, producing policy-specific accounting components, and verifying that common invariants cancel. It must produce no final decision classification until accounting validation passes and must not search for an optimum.

### P16R — IDENTIFIED-SET DECISION BOUNDS & ROBUSTNESS CLASSIFICATION

P16R may begin only after P15R passes and a separate explicit instruction. Its role is to construct `lower_DeltaG` and `upper_DeltaG`, apply `Θ(z)`, apply the three primary carbon classifications, keep technical feasibility separate, and apply all pre-registered robustness gates. It must not optimize a trajectory.

### P17 — Publication-Quality Result Synthesis and Robustness Audit

P17 is reserved for a later explicitly authorized stage covering result synthesis, robustness audit, tables, and figures. It is not authorized by P14.6C.

## P14.6C.21 Machine-Readable Authority and Current Stop

The machine-readable preregistration is `data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json`. The prose and JSON contracts must remain consistent; a conflict requires change control before numerical work.

P14.6C calculates no lifecycle GHG, no decision bounds, and no replacement result. P15R is not started by this amendment.
