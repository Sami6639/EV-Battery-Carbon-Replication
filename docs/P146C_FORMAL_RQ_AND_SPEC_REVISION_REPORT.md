# P14.6C — Formal RQ Revision, Identified-Set Preregistration & Specification Amendment

**Stage:** P14.6C  
**Scope:** Formal change control and preregistration only  
**Architecture:** `OPTION B — TRAJECTORY-FREE STATE-CONDITIONED ROBUST / PARTIAL-IDENTIFICATION ARCHITECTURE`

## 1. Governing Files Read

`PROJECT_INSTRUCTIONS.md`, the complete historical and newly amended `docs/IMPLEMENTATION_SPEC.md`, the P12, P13, P14, P14.5, P14.5R, P14.5S, P14.5I and P14.6 reports, and `docs/RESEARCH_DECISION_LOG.md` were read before this revision was finalized. Existing configs, manifests, P14 scenario parameters, and the P14.5S/P14.5I test contracts were also inspected to preserve physical roles and audit history.

## 2. Change-Control Approval

The user instruction is explicit approval of Option B and authorizes only formal RQ revision, identified-set preregistration, prospective specification amendment, decision-log append, and tests. It does not authorize lifecycle computation, decision-bound calculation, optimization, P15R, P16R, or manuscript work.

The approval satisfies the frozen change-control requirement because it names the failed frozen architecture, evidence of conflict, approved replacement architecture, scientific consequence, and required append-only implementation amendment.

## 3. Historical Failure Preservation

P14.5 remains `REAL-WORLD DEGRADATION BRIDGE FAIL`. P14.5I remains `R3 REAL-WORLD DEGRADATION BRIDGE FAIL`. Its pre-registered capacity validation failed, zero joint R3 rows were admissible, and deterministic real-world `R(t)` remains unavailable. Neither failure is described as an almost-pass or removed from the decision log.

All P14.5R and P14.5S candidate/specification records also remain intact. They document the attempted remedy and its constraints; they do not authorize reuse of the failed R3 trajectories.

## 4. Option B Formal Adoption

The formally adopted architecture is:

`OPTION B — TRAJECTORY-FREE STATE-CONDITIONED ROBUST / PARTIAL-IDENTIFICATION ARCHITECTURE`

`S2 = PRIMARY`: mechanistic set identification and robust sign classification.  
`S1 = SUPPORTING ONLY`: symmetric policy accounting and endpoint-bound construction.

No prospective work may return to degradation-trajectory optimization without a new explicit scientific revision.

## 5. Original RQ Supersession

The original Primary RQ remains verbatim in the historical opening section of `docs/IMPLEMENTATION_SPEC.md`. Its prospective status is now:

`SUPERSEDED BY APPROVED METHODOLOGICAL REVISION`

The reason is scientific, not computational: early/interior/use-until-boundary timing regimes require an ordered joint degradation trajectory, and P14.5/P14.5I failed to establish that object.

## 6. Revised Primary RQ

Status: `REVISED PRIMARY RQ — LOCKED`

> **Conditional on an empirically admissible current battery capacity–resistance state, under what combinations of remaining vehicle service, replacement-battery embodied emissions, and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths are unidentified?**

The wording is frozen before numerical results and may not be changed after observing future carbon classifications.

## 7. Revised Sub-RQs

**Revised Sub-RQ1 — Identified set:**

> What lower and upper bounds can be placed on the life-cycle-GHG contrast between immediate battery replacement and continued first-life use, conditional on an empirically admissible current capacity–resistance state and residual mobility service, without assuming a real-world degradation trajectory?

**Revised Sub-RQ2 — Technical feasibility:**

> How do the current usable-capacity and pulse-resistance states, evaluated against the required mobility and power service, determine whether continued first-life use and immediate replacement are technically admissible before carbon comparison?

**Revised Sub-RQ3 — Temporal carbon context:**

> How do residual vehicle service and temporal charging-grid and replacement-battery manufacturing decarbonization widen, narrow, or change the sign classification of the identified life-cycle-GHG interval?

None restores time-to-state or retirement-timing optimization.

## 8. Scientific Estimand

For immediate replacement (R), continuation (C), matched exogenous context (z), and admissible policy-state treatments:

\[
\Delta G(z,\theta_R,\theta_C)=G_R(z,\theta_R)-G_C(z,\theta_C).
\]

Positive values mean replacement has higher lifecycle GHG; negative values mean replacement has lower lifecycle GHG. P14.6C defines this identity but calculates no value.

## 9. Identified-Set Definition

The locked identified interval is:

\[
\underline{\Delta G}(z)=\inf_{(\theta_R,\theta_C)\in\Theta(z)}\Delta G,
\qquad
\overline{\Delta G}(z)=\sup_{(\theta_R,\theta_C)\in\Theta(z)}\Delta G.
\]

The design is `MECHANISTIC SET IDENTIFICATION`. No probability distribution, population frequency, likelihood, or statistical confidence interpretation is implied.

## 10. Carbon Classification Rules

The primary labels and rules are exact:

- `lower_DeltaG > 0` → `ROBUST CONTINUE`;
- `upper_DeltaG < 0` → `ROBUST REPLACE`;
- `lower_DeltaG <= 0 <= upper_DeltaG` → `CARBON DECISION INDETERMINATE`.

`POTENTIALLY BENEFICIAL` is allowed only as a non-recommendation qualifier when some admissible replacement contrasts are negative but robustness is absent. Early/interior/use-until-boundary terminology is prohibited as a future carbon classification.

## 11. Technical Classification Rules

The allowed technical labels are `CONTINUE TECHNICALLY FEASIBLE`, `CONTINUE TECHNICALLY INFEASIBLE`, `REPLACEMENT TECHNICALLY FEASIBLE`, `REPLACEMENT TECHNICALLY INFEASIBLE`, and `STATE OUTSIDE DECISION DOMAIN`.

Technical feasibility is evaluated before carbon. If continuation fails required service and replacement passes, replacement may be technically required within the defined two-policy choice set; this does not imply `ROBUST REPLACE`.

## 12. Current-State Admissibility

Entry requires physical `reconstructed_capacity_retention`, a supported primary R10 state/envelope, separate R1s alternative where available, compatible SOC and reference temperature, and P12/P13 domain validity.

For this methodological study, “empirically admissible current state” means only a capacity/resistance combination inside the validated P12/P13 physical evidence domain. It does not mean fleet prevalence, state probability, or a typical age-conditioned field state. Experimental elapsed day is not vehicle age, and time-to-state is unused. A later vehicle-specific application would require a compatible current-state measurement.

## 13. Θ_C Definition

`C_LOW` holds the current admissible state constant over matched residual service. It is the optimistic continuation operational-penalty bound, not a prediction that degradation stops.

`C_HIGH` allows the worst technically feasible P12/P13-supported degradation-energy state under the same chemistry/reference architecture. It is the pessimistic continuation operational-penalty bound, not a predicted jump or path.

## 14. Θ_R Definition

`R_LOW` holds fresh/reference replacement performance constant over matched residual service. It is the optimistic replacement operational-penalty bound, not a prediction.

`R_HIGH` applies the same scientifically admissible worst-state rules used for continuation, subject to chemistry/system compatibility. It is the pessimistic replacement operational-penalty bound, not a trajectory.

## 15. Policy Symmetry

Policy symmetry is a hard gate. Future-state uncertainty treatment must be symmetric unless a physical difference is pre-specified and justified before results. Fresh-forever replacement versus worst-state-forever continuation, or the reverse biased comparison, cannot be the sole analysis. Any asymmetry must identify its physical mechanism, evidence, affected policy, and interval consequence.

## 16. Joint Θ(z) Compatibility Rules

`Θ(z)` is not an unrestricted Cartesian product. It must preserve chemistry, system, SOC, reference temperature, resistance timescale, and shared-context compatibility; exclude mutually incompatible combinations; retain necessary scientific coupling; prevent cross-matched exogenous corners selected to maximize width; and fail closed where compatibility is unresolved.

## 17. Shared Exogenous Context

Within each policy contrast, decision year, current vehicle age, mileage/residual-service treatment, survival treatment, charging conversion, grid pathway/geography, technical-service definition, logically shared manufacturing context, and 2050 truncation are matched.

Grid and manufacturing cases are separate (z) contexts. They are not mixed into (\Theta) by comparing a favourable replacement corner with an unfavourable continuation corner.

## 18. Operational-Energy Bound Architecture

P13 supplies state-conditioned energy and feasibility consequences only within its validated domain. Capacity affects usable stored energy and range feasibility. Relative resistance affects the ageing-sensitive incremental resistive loss. Capacity retention never directly scales traction energy, and percent resistance growth never maps directly to percent vehicle-energy growth. L2-to-L3 charging conversion remains separate and avoids EPA/ATB double counting.

## 19. Replacement Manufacturing Accounting

Replacement manufacturing applies only to policy (R) as replacement pack capacity multiplied by the calendar-year, chemistry/pathway-specific Llamas pack-level factor. Original battery manufacturing is included once in total LCA but is a common invariant in (\Delta G). No second-life credit or post-vehicle-retirement service is assumed.

## 20. Grid Treatment

Cambium 2024 average CI remains primary with the load-weighted U.S. representation, 18 GEA regional robustness, exact `MidCase`, `LowRECost`, and `HighRECost` labels, piecewise-linear in-domain interpolation, and 2025–2050 horizon. `Cambium-2023 LRMER sensitivity` remains separately labelled sensitivity only.

## 21. Survival / Residual Service

P14 vehicle-age-conditioned survival may define or weight residual service but cannot assign degradation state. Both policies use the same survival treatment. The focal vehicle receives no operation after retirement, and the replacement battery receives no automatic residual-service or second-life credit beyond focal-vehicle use.

## 22. Resistance Evidence Tiers

The `MAIN IDENTIFIED SET` uses the P12 `PRIMARY PHYSICAL SPECIFICATION` and `AUTOMOTIVE-COMPATIBLE ENVELOPE`, subject to P12/P13 validity. The separately labelled `STRESS / EXTREME SET` may include the `EXTREME / CONDITIONAL ENVELOPE`. Stress evidence cannot silently become headline evidence or create a main classification through opportunistic inclusion/exclusion.

## 23. R10 / R1s Treatment

R10 is primary. R1s is the separate alternative physical robustness specification. If sign classification reverses between them, the main result is not robust. Intervals are not merged numerically, and timescale switching is prohibited.

## 24. Pack-Loss-Share Treatment

The P13 0.50/0.75/1.00 ageing-sensitive loss-share cases all remain in the declared main robustness set. A single share cannot be chosen after results. A robust main classification must survive the relevant declared share set.

## 25. Mobility / Technical-Service Treatment

`mobility_central` is the primary service requirement. `mobility_lower` and `mobility_upper` are structured robustness requirements. The P13 fixed-cycle discharge and regenerative-acceptance power requirements apply throughout. This pre-result hierarchy retains the bounded P14 family without allowing the most extreme service threshold to silently determine the headline classification.

## 26. Uncertainty / Scenario Hierarchy

The `PRIMARY IDENTIFIED SET` uses main P12/P13-supported states, R10, all three loss shares, central mobility/mileage, central 4.5-year survival-scale assumption, p50 charging conversion, and load-weighted U.S. grid geography. The three official grid pathways and prospective SPS/SDS manufacturing pathways are separate matched (z) contexts.

The `STRUCTURAL ROBUSTNESS SET` contains R1s, lower/higher mileage, lower/upper mobility requirements, 3.5/5.5-year survival-scale assumptions, p10/p90 charging efficiency, 18 GEA regional series, the static same-source 2020 `Current` manufacturing benchmark, and the correctly labelled LRMER sensitivity.

The `EXTREME / STRESS SET` contains separately labelled extreme/conditional physical evidence and is not headline-eligible. Future reporting order is primary classification, structural robustness, extreme/stress result, then separate technical feasibility. No undifferentiated mega-envelope is authorized.

## 27. Revised Non-Robustness Gate

A carbon classification is non-robust if it depends only on extreme states; reverses between R10/R1s or across loss shares; uses unsupported mobility/power; exists only under one extreme residual-service or one target-set carbon pathway; treats bounds as trajectories; requires unsupported interpolation/extrapolation/clipping; uses unjustified asymmetric policy assumptions; depends on mismatched exogenous corners; or changes sign when a required admissible treatment is restored.

This gate is frozen before carbon results and cannot be relaxed after inspection.

## 28. Prohibited Scientific Claims

The revised architecture prohibits optimal retirement year, optimal SOH, optimal resistance, optimal battery age, time-to-state, mileage-to-state, predicted real-world degradation path, deterministic age-resistance growth, early/interior/use-until-boundary carbon outputs, percentage of EVs that should replace, probability of robust replacement, and degradation-state prevalence without a separate representative fleet distribution.

## 29. P12 Compatibility

P12 is unchanged and is used only as an admissible dual physical state-space. `reconstructed_capacity_retention`, R10, separate R1s, SOC/temperature conditioning, automotive-compatible evidence, and extreme/conditional labels retain their existing meanings. Experimental time is not transferred to vehicle time.

## 30. P13 Compatibility

P13 is unchanged and remains the domain-limited state-to-vehicle translation. Its topology-aware resistance-loss mechanism, capacity role, pack-loss shares, technical feasibility precursors, and no-direct-scaling prohibitions remain binding. It does not generate a trajectory.

## 31. P14 Compatibility

P14 is unchanged and supplies matched mobility, survival, charging, grid, manufacturing, and calendar contexts. Survival/mileage cannot assign state. Existing grid, manufacturing-geography, survival-scale, and horizon limitations remain visible bounds.

## 32. P14.5 / P14.5I Failure Role

The failures are the evidentiary reason for changing the estimand, not inputs to the revised calculation. Failed R3 capacity paths and zero-admissible-row bridge outputs cannot enter P15R/P16R. The revised design uses only still-valid P12/P13/P14 assets and explicitly avoids the missing bridge.

## 33. IMPLEMENTATION_SPEC Amendment

The amendment was appended under `P14.6C — APPROVED TRAJECTORY-FREE METHODOLOGICAL REVISION`; no historical text was rewritten. Pre-amendment identity was recorded before the edit:

- SHA-256: `f8e29917daa0a4f999088005e0c85dffd6cc3cf3f828b1198dce4b6c1c1d3a80`
- byte size: `32002`
- line count: `844`

The original 32,002-byte prefix still has the recorded SHA-256. The amended specification SHA-256 is `c01c06bb989492ee4e31aa3369ad6721ac93b83e39de6691780a278b56513e40`; size is 49,090 bytes and line count is 1,146. Conflicting historical trajectory/timing directions are explicitly superseded prospectively.

## 34. Machine-Readable Preregistration

`data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json` encodes the exact revised RQs, estimand/sign convention, interval/classifications, technical labels, admissibility, `Θ_C`, `Θ_R`, `Θ(z)`, symmetry/coupling, state and scenario tiers, R10/R1s, loss shares, technical service, non-robustness gate, prohibited outputs, next-stage names, disclosures, pre-amendment specification identity, and frozen P12/P13/P14 scientific-output hashes. It contains no lifecycle or decision-result values.

## 35. Revised P15R Definition

`P15R — STATE-CONDITIONED LIFECYCLE-GHG ACCOUNTING ENGINE` is the prospective accounting-validation stage. Its role is limited to implementing (G_R)/(G_C), verifying units and boundaries, creating policy-specific components, and checking common-invariant cancellation. It cannot search for an optimum or release a final decision classification before accounting validation passes. P15R is not started.

## 36. Revised P16R Definition

`P16R — IDENTIFIED-SET DECISION BOUNDS & ROBUSTNESS CLASSIFICATION` may begin only after P15R passes and a separate explicit instruction. It will construct lower/upper (\Delta G), apply `Θ(z)`, separate technical feasibility, classify the three carbon outcomes, and apply all preregistered robustness gates. It cannot optimize a trajectory.

## 37. Files Created

- `data/metadata/P146C_IDENTIFIED_SET_PREREGISTRATION.json`
- `docs/P146C_FORMAL_RQ_AND_SPEC_REVISION_REPORT.md`
- `tests/test_p146c_formal_revision.py`

No numerical lifecycle artifact was created.

## 38. Files Modified

- `docs/IMPLEMENTATION_SPEC.md`: append-only authoritative P14.6C amendment.
- `docs/RESEARCH_DECISION_LOG.md`: append-only P14.6C decision record after specification prechecks passed.
- `tests/test_p145i_r3_implementation.py`: historical integrity check updated to verify the exact P14.5I-era specification byte prefix while allowing the later approved append-only P14.6C amendment.
- `results/intermediate/p145_artifact_manifest.json`: mechanically regenerated by the legacy full-suite P14.5 test because that manifest embeds the append-only decision-log hash; its scientific P14.5 Parquet hashes remain unchanged.

No P12/P13/P14 scientific output was modified.

## 39. Tests / Integrity Checks

The P14.6C focused tests validate exact RQ preservation/revision, append-only prefix identity, S2/S1 roles, estimand/sign labels, `Θ_C`/`Θ_R`/`Θ(z)`, symmetry, state and scenario tiers, technical/carbon separation, R10/R1s, prohibited outputs, stage names, failure-history retention, frozen P12/P13/P14 output hashes, report structure, and absence of numerical P14.6C result artifacts.

Focused P14.6C result: `11 passed`.  
Combined P14.6C plus amended P14.5I historical-integrity result: `20 passed`.  
Complete repository result: `85 passed in 86.70s`.

## 40. Lifecycle GHG Calculated

Lifecycle GHG Calculated: `NONE`

## 41. Decision Bounds Calculated

Decision Bounds Calculated: `NONE`

## 42. Replacement Optimization Performed

Replacement Optimization Performed: `NONE`

Original P14.5/P14.5I Failure Records Removed: `NO`

P12/P13/P14 Scientific Outputs Modified: `NONE`

## 43. Hard Blockers

No blocker prevents formal locking of the trajectory-free architecture. Existing bounded limitations remain: P14 survival-scale uncertainty, unresolved/implicit manufacturing geography, charging-conversion transferability, conditional automotive resistance evidence, and possible future identified intervals that cross zero. These limitations justify a bounded status and must be propagated rather than resolved after inspecting results.

Numerical work remains blocked until P15R receives a separate explicit instruction and passes its accounting-validation gate. P16R remains blocked until P15R passes and is separately authorized.

## 44. Final Status

`TRAJECTORY-FREE METHODOLOGICAL REVISION FORMALLY LOCKED WITH BOUNDS`

**STOP — P15R not started. Await explicit next instruction.**
