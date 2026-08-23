# P14.6 — Trajectory-Free Decision Architecture & RQ Salvage Gate

**Assessment date:** 2026-08-21  
**Change-control class:** `METHODOLOGICAL SALVAGE ASSESSMENT`  
**Scope:** Architecture and research-question assessment only. No lifecycle-GHG calculation, carbon multiplication, numerical break-even, replacement optimization, Monte Carlo analysis, manuscript result, P15 work, or frozen-specification amendment was performed.

## 1. Governing Files Read

The following governing chain was read before this assessment:

1. `PROJECT_INSTRUCTIONS.md`
2. `docs/IMPLEMENTATION_SPEC.md`
3. `docs/P12_NMC_DEGRADATION_VALIDATION_REPORT.md`
4. `docs/P13_VEHICLE_ENERGY_TRANSLATION_REPORT.md`
5. `docs/P14_LIFECYCLE_INPUT_ARCHITECTURE_REPORT.md`
6. `docs/P145_REAL_WORLD_DEGRADATION_BRIDGE_REPORT.md`
7. `docs/P145R_EVIDENCE_EXPANSION_ASSESSMENT.md`
8. `docs/P145S_R3_REVISION_SPECIFICATION_REPORT.md`
9. `docs/P145I_R3_CONTROLLED_IMPLEMENTATION_REPORT.md`
10. `docs/RESEARCH_DECISION_LOG.md`

The governing priority remains `scientific validity > novelty claims > methodological complexity > speed`. The frozen change-control rule also remains binding: a scientifically unimplementable decision must not be silently altered, and a revised implementation cannot proceed without explicit approval.

## 2. Preserved Failure Evidence

The following findings are authoritative and are not weakened by this assessment:

- P14.5 ended with `REAL-WORLD DEGRADATION BRIDGE FAIL` because no source supported a multi-year, real-operation mapping from calendar/use exposure to the joint capacity-and-resistance state.
- P14.5I ended with `R3 REAL-WORLD DEGRADATION BRIDGE FAIL`. This was a failure of the pre-registered scientific gate, not an “almost pass”.
- Liu validation failed the pre-registered envelope-width limit; Deng validation failed the pre-registered coverage limit. The worst-source capacity status was therefore `FAIL`.
- No R3 joint bridge row was admissible.
- A deterministic real-world resistance trajectory, `R(t)`, is unavailable. P12/Luh and Schreiber can support only conditional resistance-state evidence within their stated domains.
- Long-horizon BLAST outputs did not cure the failure: input-domain failures, nonphysical long-horizon states, failed external validation, and absent field-compatible resistance evolution remained binding.
- The original P14.5 failure record and the later P14.5I failure record remain preserved. Nothing in P14.6 converts either record into a pass.

## 3. Why P15 Is Currently Prohibited

The frozen implementation architecture defines the decision as a replacement timing/state decision along a joint degradation trajectory. P15 would therefore require non-zero-age joint capacity/resistance states tied to real calendar/use exposure. P14.5I released zero admissible rows for that purpose.

Starting the current P15 would require at least one prohibited act: treating experimental time as vehicle time, accepting a failed capacity bridge, inventing deterministic resistance growth, extrapolating outside supported state domains, or silently changing the locked decision architecture. P15 therefore remains prohibited until an explicit methodological revision is approved and its replacement-stage specification is pre-registered. This report is an assessment of such a possible revision; it is not the approval and does not start the revised computation.

## 4. Scientific Assets Still Valid

The bridge failure does not invalidate the project's validated state and context layers:

- **P12:** observed NMC capacity states, physical `reconstructed_capacity_retention`, primary 10-ms `R10/R10_0`, separate 1-s `R1s/R1s_0`, condition/replicate uncertainty, automotive-compatible evidence, and explicitly labelled extreme/conditional states remain valid inside the observed physical domain. P12 is a state-space, not a real-world clock.
- **P13:** the physics-based mapping from an admissible capacity/resistance state to usable-energy/range feasibility and incremental battery-side loss remains valid with bounds. Capacity is not directly converted into traction-energy growth; relative resistance affects only the ageing-sensitive resistive-loss component.
- **P14:** the fixed mobility service, annual-mileage cases, technical range and power requirements, vehicle-age-conditioned survival, charging conversion, 2025–2050 grid pathways, and prospective replacement-battery manufacturing pathways remain valid with their existing bounds.
- **Accounting invariants:** original-battery manufacturing is included once in a total LCA but is common to both policies and cancels in the replacement contrast. Replacement manufacturing remains replacement capacity multiplied by the pack-level factor for the replacement calendar year and pathway.

These assets can answer a conditional decision question without answering when a vehicle reaches the conditioning state.

## 5. Missing Scientific Object

The missing object is not another carbon factor. It is a validated stochastic or deterministic transition law

\[
(x_0,\;a_0,\;u_{0:t}) \longrightarrow x_t,
\]

where (x_t) jointly contains usable-capacity retention and compatible pulse-resistance state under real multi-year vehicle exposure (u_{0:t}). In particular, neither the time to reach a state nor the path occupied after the current state is identified.

For an eventual vehicle-specific application, the current state must itself be observed or estimated at compatible reference conditions: usable capacity plus a supported R10 measure or bound, with R1s kept as an alternative specification. That is a specific measurement requirement, not a reason for another broad source search. For a methodological state-space study, the conditioning states may instead be the explicitly admissible P12/P13 states; they must not be described as the empirical distribution of vehicles in service.

## 6. Candidate S1 Architecture

S1 conditions the decision on a focal BEV's current calendar year (y_0), vehicle age, residual-service representation, current admissible capacity state, primary R10 envelope, and separate R1s envelope. It compares:

- immediate battery replacement in the same continuing vehicle; and
- continued first-life use of the existing battery.

Because later degradation is unidentified, S1 cannot be a point-estimating “replacement break-even” model. It can only define endpoint accounting bounds:

- **continue optimistic bound:** hold the current admissible state fixed over residual service;
- **continue pessimistic bound:** allow operation at the worst technically feasible P12/P13-supported penalty over residual service;
- **replace optimistic bound:** hold fresh/reference replacement performance fixed;
- **replace pessimistic bound:** allow the replacement battery to occupy its own worst technically feasible supported penalty over residual service.

Each bound is an extremal accounting treatment, not a predicted battery path. Common calendar, grid, manufacturing, charging, mileage, and survival assumptions must be matched across the two policies.

## 7. S1 Scientific Validity

S1 is scientifically usable only as a conservative screening layer and only with symmetric treatment. A fresh-forever replacement compared with a worst-state-forever continuation would structurally favour replacement; a fresh-forever continuation compared with a rapidly degrading replacement would create the opposite bias. Both policies therefore need explicit optimistic and pessimistic state treatments under the same eligibility rules.

The state-frozen bound is meaningful because it supplies a transparent minimum operational penalty for a battery already in the conditioning state; it does not assert that ageing stops. The worst-feasible occupancy bound is meaningful because it supplies a transparent maximum supported penalty; it does not assert that the battery jumps to, or remains at, that state in reality.

These bounds may be wide. Width is not a validity failure if the reported answer is `INDETERMINATE`; it is evidence that the available degradation information cannot identify the carbon decision. S1 becomes misleading if it reports an exact break-even, interprets the extrema as probable trajectories, or selects only the policy-favourable corners. S1 should therefore be retained as the accounting engine nested inside S2, not used as a standalone point-break-even architecture.

## 8. Candidate S2 Partial-Identification Architecture

Let (G_R(z,\theta_R)) and (G_C(z,\theta_C)) denote lifecycle GHG for immediate replacement and continued first-life use. Here (z) is a matched exogenous context—calendar year, residual-service case, survival treatment, grid pathway, manufacturing pathway, charging conversion, mileage, and technical-service definition—while (\theta_R\in\Theta_R) and (\theta_C\in\Theta_C) are scientifically admissible future-state treatments for the replacement and existing batteries.

Define the policy contrast:

\[
\Delta G(z,\theta_R,\theta_C)=G_R(z,\theta_R)-G_C(z,\theta_C). \tag{1}
\]

The identified set is bounded by:

\[
\underline{\Delta G}(z)=\inf_{(\theta_R,\theta_C)\in\Theta(z)}\Delta G,
\qquad
\overline{\Delta G}(z)=\sup_{(\theta_R,\theta_C)\in\Theta(z)}\Delta G. \tag{2}
\]

The joint set (\Theta(z)) must preserve shared assumptions and any scientifically necessary coupling; it must not mechanically combine mutually inconsistent scenario corners. Classification is:

- (\underline{\Delta G}>0): `ROBUST CONTINUE`—replacement is carbon-worse for every admissible treatment;
- (\overline{\Delta G}<0): `ROBUST REPLACE`—replacement is carbon-better for every admissible treatment;
- (\underline{\Delta G}\le 0\le\overline{\Delta G}): `CARBON DECISION INDETERMINATE`;
- an interval with only some negative values may additionally be described as `POTENTIALLY BENEFICIAL`, but never as a replacement recommendation.

Technical feasibility is evaluated before this carbon classification and is reported on a separate axis.

## 9. S2 Scientific Validity

S2 is methodologically stronger than S1 because it makes non-identification the object of analysis rather than hiding it in a central scenario. It is falsifiable: a proposed robust classification fails if any admissible, correctly matched treatment reverses its sign. It is also auditable: the result depends on explicit state sets, technical constraints, and pathway sets rather than an unvalidated time path.

S2 is not equivalent to statistical partial identification from a representative random sample. In this project it is a **mechanistic set-identification** design: the identified set follows from validated physical states, bounded engineering translations, and frozen context scenarios. Claims about population prevalence or probability require separate evidence and are prohibited.

Relative to the original point-optimum architecture, S2 is scientifically stronger in identification discipline and weaker in temporal resolution. It cannot identify when to replace or an optimal retirement age. It can identify whether a decision sign is invariant to unresolved degradation-path treatments. That is a meaningful but narrower scientific object.

## 10. Current-State vs Time-to-State Distinction

The revised architecture must keep two propositions separate:

1. **Current-state proposition:** a focal battery is observed in, or an analysis is conditioned on, a capacity–resistance state supported by P12/P13.
2. **Time-to-state proposition:** a real vehicle reaches that state after a particular age, mileage, duty cycle, or calendar/use history.

P12/P13 support the first proposition within their domains. P14.5 and P14.5I show that the second proposition is not identified. Consequently, a state may be indexed by a prospective decision year without claiming that a vehicle of that age is expected to possess the state. State-by-year combinations are conditional decision experiments, not forecasts of fleet ageing.

## 11. Technical-Feasibility Treatment

Before carbon comparison, each current state must pass the locked mobility/range requirement and power-service requirement under the P13 translation and P14 service family. No universal 70% or 80% SOH threshold may be introduced.

Technical and carbon conclusions must remain separate:

- If continued use can deliver the defined service, the carbon dominance test may proceed.
- If continued use cannot deliver the service but a replacement can, `CONTINUE TECHNICALLY INFEASIBLE` is reported. Replacement is required within the two-action service-preserving choice set, but this is not evidence that replacement is carbon-beneficial.
- If neither policy delivers the service, the state is outside the defined decision problem.
- If replacement feasibility depends on an unsupported power or range assumption, no technical conclusion is released.

`TECHNICALLY REQUIRED REPLACEMENT` may be used only as a technical action label and must never be merged with `ROBUST REPLACE`, which is a carbon-dominance label.

## 12. Temporal Grid Role

The P14 grid architecture remains decision-relevant. For a fixed current physical state, the operational-GHG consequence of an energy-penalty bound varies with the calendar-specific charging-grid pathway over residual service. This is a legitimate prospective comparison because calendar year is an observed decision context, not an inferred battery-age coordinate.

Cambium 2024 average grid CI remains primary; all 18 regional series and the load-weighted U.S. series retain their frozen roles. `Cambium-2023 LRMER sensitivity` remains separately labelled and cannot be substituted for the primary average-CI accounting. A grid pathway may alter the sign or width of the decision contrast, but it cannot identify degradation.

## 13. Temporal Manufacturing Role

Replacement-battery embodied burden is incurred in the replacement year:

\[
G_{\mathrm{mfg,rep}}(y_0)=Q_{\mathrm{rep}}\,I_{\mathrm{pack}}(y_0,p,c), \tag{3}
\]

where (Q_{\mathrm{rep}}) is replacement capacity and (I_{\mathrm{pack}}) is the chemistry-, pathway-, year-, unit-, and boundary-specific pack manufacturing factor. Equation (3) is an accounting identity only; no values are calculated here.

Thus the same admissible battery state considered in different decision years can face different replacement burdens. Llamas-Orozco `Current`, `SPS`, and `SDS` paths, the same-source static benchmark, chemistry separation, and the unresolved manufacturing-geography limitation remain unchanged. Temporal manufacturing variation does not require a degradation trajectory.

## 14. Vehicle-Survival Role

P14 vehicle-age-conditioned survival can weight or bound the residual service delivered after the decision. Survival describes whether the focal vehicle remains in service; it is not a battery degradation model and must not be used to assign a battery state.

Survival-weighted residual service is compatible with S1/S2 if both policies are evaluated over the same vehicle-survival realization or matched survival scenario and deliver the same functional unit. A replacement battery receives no automatic service or environmental credit beyond actual focal-vehicle operation. Residual survival at the 2050 truncation remains disclosed, and no post-2050 carbon pathway is invented.

## 15. Original RQ Compatibility

The locked Primary RQ asks when the life-cycle-GHG-minimizing decision favours **early replacement**, an **interior retirement/replacement point**, or **continued use to the technical mobility boundary**. The frozen specification further defines this as a timing/state decision along a joint degradation trajectory.

Those regime labels require an ordered feasible path and knowledge of how decision opportunities evolve through time. Without time-to-state and future state transitions, P14.6 cannot distinguish “early” from “interior”, locate a retirement point, or establish use *until* a future technical boundary. The original Primary RQ therefore fundamentally depends on the missing scientific object and cannot remain unchanged under a trajectory-free design.

Several mechanisms in the RQ survive—current degradation state, replacement manufacturing, residual service, technical feasibility, and temporal grid/manufacturing context—but the estimand changes from a point-optimal timing regime to a conditional dominance set. Preserving the original wording would overstate what the evidence can identify.

## 16. Candidate Revised RQs

At most three candidates were developed:

**RQ-A — decision-regime form**

> Conditional on an empirically admissible current battery capacity–resistance state, under what combinations of remaining vehicle service, replacement-battery embodied emissions, and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths are unidentified?

**RQ-B — identified-set form**

> What bounds can be placed on the life-cycle-GHG contrast between immediate battery replacement and continued first-life use for a focal BEV, conditional on an admissible capacity–resistance state and residual mobility service, without assuming a real-world degradation trajectory?

**RQ-C — uncertainty-mechanism form**

> How do capacity–resistance state uncertainty, remaining vehicle service, and temporal decarbonization jointly constrain carbon-robust battery replacement decisions when time-to-state and future degradation paths are unidentified?

No wording is adopted in this gate. The locked Primary RQ remains unchanged pending explicit approval.

## 17. Comparative RQ Evaluation

| Criterion | RQ-A | RQ-B | RQ-C |
|---|---|---|---|
| Gap alignment | Directly addresses the unsupported timing problem while retaining the original mechanisms | Most exact expression of the set-identification estimand | Strong on uncertainty interaction but less explicit about the policy contrast |
| Novelty | Good domain-specific combination; requires careful non-priority positioning | Good methodological distinctiveness; may read narrower and more technical | Moderate; overlaps broad robust-decision language |
| Falsifiability | High: one admissible sign reversal defeats robustness | Highest: bounds and inclusion rules are directly auditable | Moderate-high: “constrain” requires operational definition |
| Methodological validity | High if `empirically admissible` is restricted to observed state support | Highest; makes conditional scope explicit | High, but could drift toward qualitative sensitivity analysis |
| Reviewer defensibility | Strong balance of decision relevance and limitations | Strongest for methods reviewers; less immediately accessible | Acceptable, but less precise about the final classification |
| P12/P13/P14 compatibility | Full, subject to stated bounds | Full, subject to stated bounds | Full, subject to stated bounds |
| Dependence on unavailable trajectories | None | None | None |
| WoS/Q1 potential | Viable with careful positioning | Viable with careful positioning; strongest as a methodological sub-question | Viable mainly as a mechanism sub-question |

RQ-A is the recommended Primary RQ candidate because it preserves the project’s decision relevance while stating the non-identification condition. RQ-B is the strongest candidate methodological sub-RQ. RQ-C may organize mechanism-focused sensitivities but is not recommended as the primary question.

## 18. Narrow Novelty Stress Test

The search was deliberately restricted to state-conditioned EV-battery carbon replacement, robust/partial-identification replacement, trajectory-free degradation-state break-even, and lifecycle-GHG dominance bounds. No broad degradation-source search was conducted.

| Close work | What it does | Why it does not pre-empt the revised contribution |
|---|---|---|
| [Yang et al. (2018), *Considering Battery Degradation in Life Cycle Greenhouse Gas Emission Analysis of Electric Vehicles*](https://doi.org/10.1016/j.procir.2017.12.008) | Integrates an LMO-graphite degradation trajectory and required battery replacement into EV lifecycle GHG analysis. | It is trajectory-based and does not identify robust continue/replace regions across an admissible capacity–resistance state set under path non-identification. |
| [Liu et al. (2024), *Life cycle assessment: Driving strategies for promoting electric vehicles in China*](https://doi.org/10.1080/15568318.2024.2410362) | Compares vehicle powertrains and regional grid conditions; battery-life/replacement assumptions enter sensitivity analysis. | It uses assumed battery life and continued efficiency decline rather than conditioning a focal same-vehicle replacement contrast on dual physical state with partial-identification bounds. |
| [Qichen Wang et al. (2025), *AI-driven echelon utilization of retired electric vehicle batteries and their life cycle carbon mitigation potential*](https://doi.org/10.1007/s44438-025-00017-9) | Couples capacity forecasting with lifecycle carbon and retirement/echelon decisions using field charging data. | It predicts capacity trajectories, omits compatible internal-resistance evolution, and addresses retirement/repurposing; it is not a trajectory-free robust-dominance test for continue versus immediate pack replacement in the same BEV. |
| Requested “Parés Olguín 2025” comparator | An exact 2025 scholarly record matching that label was not verified in the narrow check. The closest authoritative records are the [2024 UC Davis final report](https://doi.org/10.7922/G23T9FKX) and the associated [2023 *Transportation Research Part D* article](https://doi.org/10.1016/j.trd.2023.103934) on U.S.–Mexico second-hand EV trade, battery circularity, and EOL policy. | These works study cross-border second-hand vehicle flows, remaining battery life, disposal, and policy burdens—not state-conditioned, same-vehicle carbon dominance under unresolved degradation paths. The year discrepancy should not be silently normalized. |
| [Busch, Chen, and Kendall (2026), *Life Cycle Performance and Carbon Handprint of Lithium-Ion Batteries in Electric Vehicles*](https://doi.org/10.1007/s44498-026-00112-1) | Evaluates U.S. fleet-level EV-versus-ICE lifecycle performance and battery-enabled carbon handprint through 2050. | Its counterfactual and unit of analysis are fleet electrification, not first-life continue-versus-replace decisions conditional on a current battery state. |
| [Nan Wang et al. (2026), *Life cycle carbon emissions of lithium-ion batteries considering dynamic round-trip efficiency degradation: From assessment to reduction*](https://doi.org/10.1016/j.est.2026.122148) | Uses a dynamic round-trip-efficiency degradation model to derive a carbon-optimized retirement strategy for energy-storage batteries. | It is explicitly trajectory- and point-retirement-based, concerns ESS service, and does not solve the EV dual-state/path-non-identification problem. It is close enough that the revised paper must emphasize bounds rather than “carbon-optimized retirement”. |
| [Chen et al. (2024), *A critical comparison of LCA calculation models for the power lithium-ion battery in electric vehicles during use-phase*](https://doi.org/10.1016/j.energy.2024.131175) | Shows that use-phase LCA results are highly sensitive to the calculation model and battery efficiency treatment. | It strengthens the need for model-form robustness but does not provide a state-conditioned replacement identified set. |
| [Wu et al. (2024), *Pathway decisions for reuse and recycling of retired lithium-ion batteries considering economic and environmental functions*](https://doi.org/10.1038/s41467-024-52030-0) | Optimizes reuse/recycling pathways at assumed retirement SOH levels. | It concerns post-retirement pathways and fixed SOH cases, not whether a technically feasible focal BEV should immediately replace or continue under trajectory uncertainty. |

The narrow check found adjacent trajectory-based LCA, assumed-lifetime replacement sensitivity, retirement/repurposing optimization, use-phase model comparison, and fleet carbon-handprint studies. It did not identify a genuinely close study that combines (i) an observed dual capacity–resistance state space, (ii) state-to-vehicle-energy physics, (iii) residual vehicle service and temporal carbon pathways, and (iv) a trajectory-free identified interval for the immediate replace-minus-continue GHG contrast.

That absence supports meaningful distinctiveness, not a “first ever” claim. Search-language and indexing limitations mean novelty must be stated as a carefully delimited contribution rather than universal priority.

## 19. Revised Contribution Mechanism

The defensible contribution is:

> Rather than estimating an unsupported optimal battery retirement age, the study identifies regions of the conditional decision space in which immediate replacement or continued first-life use is robust to unresolved degradation-path uncertainty, and regions in which the evidence requires an indeterminate conclusion.

This contribution has four linked mechanisms:

1. P12 supplies an observed, dual capacity–resistance physical state space without converting experimental time to vehicle age.
2. P13 translates only supported states into technical feasibility and bounded vehicle-energy consequences.
3. P14 supplies residual service and time-varying charging/manufacturing context without acting as a degradation model.
4. S2 propagates the admissible policy-specific state treatments into an identified interval for the policy contrast.

The architecture is scientifically stronger than the original in identification honesty and robustness logic, but materially narrower because it relinquishes optimal timing, time-to-state, and empirical lifetime claims. It is not a weaker or misleading paper if that narrower estimand is explicit from title through conclusion.

## 20. Revised False-Optimum Architecture

The old interior-optimum labels and gates must be retired for this architecture. Before any later numerical analysis, a replacement conclusion must be pre-registered as `NON-ROBUST` if any of the following applies:

- it exists only at an extreme/conditional R10 or R1s envelope tail;
- R10 and the separate R1s alternative reverse the carbon classification;
- it disappears across admissible ageing-sensitive pack-loss shares;
- it depends on a technically unsupported mobility or power assumption;
- it exists only under one extreme remaining-service or survival treatment;
- it exists only under one grid or manufacturing pathway when those pathways are in the declared target set;
- it treats a state-frozen or worst-state bound as a predicted trajectory;
- it requires unsupported state interpolation, extrapolation, clipping, or capacity-to-resistance conversion;
- it gives the replacement battery a more favourable future-state rule than the existing battery without scientific justification;
- it depends on selecting mismatched exogenous scenario corners across the two policies;
- its interval classification changes when a scientifically admissible state treatment is restored to the set.

Report the carbon result only as `ROBUST CONTINUE`, `ROBUST REPLACE`, or `CARBON DECISION INDETERMINATE`, with `POTENTIALLY BENEFICIAL` allowed only as a non-recommendation qualifier. Report technical infeasibility separately.

## 21. Minimum Numerical Model

A later, separately approved implementation would minimally require:

1. a current P12-supported `reconstructed_capacity_retention` state;
2. a supported primary R10 bound and separate R1s alternative bound at compatible SOC/temperature;
3. the P13 state-to-energy-penalty and usable-energy/power-feasibility translation;
4. policy-specific admissible future-state sets, including symmetric optimistic and pessimistic treatments;
5. a P14 residual-service/mileage and survival representation;
6. calendar-specific primary grid CI plus declared robustness pathways;
7. calendar-specific replacement-pack manufacturing GHG and replacement capacity;
8. charging conversion without double counting;
9. matched technical mobility and power requirements;
10. an identified-set engine that preserves common scenarios and returns the infimum/supremum of Equation (1).

No item requires a degradation trajectory to calculate conditional bounds. A trajectory would be required only to assign probabilities to future state occupancy, narrow the interval through transition restrictions, map state to age/mileage, or optimize replacement timing. Those outputs remain outside the revised minimum model.

Conceptually, operational energy for policy (p\in\{R,C\}) may be bounded as

\[
E_p(\theta_p)=\sum_y M_y\,S_y\,
\frac{e_{\mathrm{fresh},y}+\delta e_p(x_y;\theta_p)}{\eta_y}, \tag{4}
\]

where (M_y) is matched mobility, (S_y) is the chosen survival/service treatment, (\eta_y) is charging efficiency, and (\delta e_p) is a P13-supported state penalty. Multiplying Equation (4) by carbon intensity is deliberately not performed in P14.6.

## 22. P12 Compatibility

P12 is retained without refitting or reinterpretation. The revised design uses its capacity and resistance observations as conditional physical states only. Experimental elapsed time, EFC, stress condition, or check-up order cannot be relabelled as vehicle calendar time.

Primary R10 and alternative R1s remain separate. Automotive-compatible and extreme/conditional evidence remain labelled and cannot be pooled into a central trajectory. Unsupported chemistry/SOC/temperature/timescale combinations fail closed. The revised architecture may use the extreme/conditional set only in explicitly named stress tests; a robust main conclusion cannot depend solely on it.

## 23. P13 Compatibility

P13's validated physical translation remains unchanged in form. Capacity affects usable stored energy and range feasibility; it does not directly scale traction energy. Relative resistance affects the ageing-sensitive resistive-loss component through the existing topology-aware physics and bounded pack-loss shares.

Only P12/P13-supported state combinations may be queried. No non-zero-age timeline is created, no FASTSim ageing model is introduced, and no percent-resistance-to-percent-kWh shortcut is permitted. P13 provides a conditional response surface for S2, not a battery-lifetime predictor.

## 24. P14 Compatibility

P14 is retained as the exogenous service and temporal-context layer. Its mobility family, power requirement, mileage cases, survival bounds, charging conversion, grid pathways, manufacturing pathways, and 2050 truncation can be evaluated conditional on a current state.

The same state may be examined at multiple calendar years as separate prospective experiments. This preserves the temporal-decarbonization mechanism without implying that a battery takes a stated number of years to reach that state. P14 survival and mileage do not assign state occupancy. Original manufacturing remains a common invariant; replacement manufacturing enters only the replacement policy in its actual decision year.

## 25. Implementation-Spec Impact

No file is amended in this gate. If Option B is explicitly approved, a formal revision package would need to record:

- **P12/P13/P14:** retained as validated bounded inputs with unchanged scientific roles;
- **P14.5:** original `REAL-WORLD DEGRADATION BRIDGE FAIL` retained as the reason trajectory optimization is abandoned;
- **P14.5R/P14.5S:** retained as evidence of the attempted bounded bridge and its pre-registered design, not as authority to reuse failed trajectories;
- **P14.5I:** `R3 REAL-WORLD DEGRADATION BRIDGE FAIL` retained; failed capacity paths and zero-admissible-row joint bridge cannot enter the revised model;
- **`IMPLEMENTATION_SPEC.md`:** unchanged now; later change control would replace the trajectory/timing estimand, regime labels, admissible-state logic, uncertainty propagation, false-optimum gate, and Steps 15–18 with the approved state-conditioned identified-set architecture;
- **Primary RQ:** unchanged now; later explicit approval would replace it with the selected revised RQ;
- **Sub-RQs:** unchanged now; later revision should align them with the identified GHG interval, technical-feasibility conditioning, and temporal grid/manufacturing mechanisms;
- **future P15/P16:** current versions remain unauthorized. A new P15 would first specify and test the state-conditioned accounting/identified-set engine without claiming a result; a new P16 would apply pre-registered robustness and validation gates. Stage names and entry criteria must be approved before execution.

The revision is scientifically material: it changes the estimand and interpretation, although it preserves the validated evidence layers and the focal-BEV functional unit.

## 26. Scientific Claim Limits

The revised study must not claim:

- a real-world optimal retirement age or year;
- an empirical battery-lifetime optimum;
- time or mileage required to reach an analysed state;
- a predicted real-world capacity or resistance path;
- deterministic resistance growth with age;
- a population frequency or probability of `ROBUST REPLACE` states;
- an exact optimal SOH, resistance value, or break-even state;
- a carbon advantage for replacement when the identified interval crosses zero;
- generalization beyond the declared chemistry, state, vehicle, service, geography, and calendar domains.

Potentially supportable claims are conditional carbon-decision bounds, robust sign classifications within a pre-specified admissible set, technical-feasibility classifications, mechanisms that widen or narrow the identified interval, and explicit identification of regions where current evidence cannot decide.

## 27. Publication-Potential Assessment

**Classification: `VIABLE WITH CAREFUL POSITIONING`.**

The paper can retain sufficient value for a high-quality WoS journal because it combines unusually explicit physical state admissibility, a topology-aware vehicle-energy translation, residual vehicle service, temporal grid/manufacturing context, and a fail-closed decision-bound architecture. A well-supported indeterminate region is itself informative: it shows where degradation-path assumptions, rather than carbon accounting, control the policy claim.

Potential is not classified as `HIGH POTENTIAL` at this gate. Robust decision-making and partial identification are established methodological ideas; adjacent studies already integrate degradation, replacement, dynamic efficiency, retirement, and lifecycle carbon. The contribution therefore depends on rigorous domain-specific synthesis and transparent negative identification—not on claiming invention of robust bounds. Reviewers may also consider the bounds too wide unless the paper demonstrates decision-relevant robust regions or clearly explains why indeterminacy changes scientific or managerial interpretation.

The design becomes too weak if it is presented as a disguised sensitivity analysis, uses arbitrary extrema, lacks symmetric policy treatment, or oversells P12 laboratory states as representative field prevalence. With pre-registration, clear set construction, and claim discipline, it remains aligned with the project's publication goal.

## 28. Option A/B/C Comparison

| Option | Scientific assessment | Consequence | Decision |
|---|---|---|---|
| **A — keep original trajectory-based RQ** | Not defensible. Early/interior/use-until timing regimes require the failed joint real-world transition object. | Would contradict P14.5/P14.5I and invite unsupported trajectory assumptions. | **Reject** |
| **B — trajectory-free, state-conditioned robust/partial-identification architecture** | Defensible with bounds. It uses validated current-state, physical translation, service, and temporal-context assets while returning indeterminate where evidence does not identify the sign. | Requires explicit RQ/specification revision and a new pre-registered implementation gate; yields conditional dominance, not timing optimization. | **Recommend** |
| **C — fundamentally new question or new primary experiment/data collection** | Scientifically valid but not presently necessary for a meaningful conditional-bounds paper. New longitudinal capacity/resistance measurement would be needed to restore timing/lifetime claims or materially narrow bounds. | Highest cost and delay; appropriate only if the project insists on the original point-timing estimand or later finds all decision intervals uninformative. | **Do not recommend now** |

Exactly one option is recommended: **Option B**.

## 29. Recommended Architecture

Adopt S2 as the governing architecture, with S1 retained only as its transparent policy-accounting and endpoint-bound construction. The core workflow after future approval would be:

1. condition on a technically interpretable, P12/P13-supported current dual state;
2. establish continue/replace technical feasibility under the same service requirement;
3. construct symmetric policy-specific admissible future-state sets without a time path;
4. match grid, manufacturing, charging, mileage, survival, and horizon assumptions across policies;
5. bound the immediate replace-minus-continue GHG contrast over the joint admissible set;
6. classify only the sign-invariant regions as `ROBUST CONTINUE` or `ROBUST REPLACE` and report all sign-crossing regions as `CARBON DECISION INDETERMINATE`;
7. apply the revised false-optimum/non-robustness gates before interpretation.

This is a trajectory-free conditional decision analysis. It is not an optimization over retirement time and must not inherit the original early/interior/boundary labels.

## 30. RQ Recommendation

The original Primary RQ cannot be preserved unchanged. Upon explicit change-control approval, adopt **RQ-A** as the revised Primary RQ candidate:

> Conditional on an empirically admissible current battery capacity–resistance state, under what combinations of remaining vehicle service, replacement-battery embodied emissions, and temporal charging-grid and battery-manufacturing pathways is immediate battery replacement robustly carbon-better, robustly carbon-worse, or indeterminate when future degradation paths are unidentified?

Use RQ-B as the likely methodological sub-RQ concerning the bounds on (\Delta G). Sub-RQs should separately address technical feasibility and the temporal grid/manufacturing mechanisms, without restoring time-to-state language.

This recommendation does not edit or supersede the locked RQ. Formal RQ and specification changes must wait for explicit approval.

## 31. Remaining Hard Blockers

The following blockers remain before any revised numerical stage:

- no approved change-control amendment authorizes the revised estimand, terminology, or P15/P16 sequence;
- no pre-registered definition yet exists for the joint admissible future-state sets (\Theta_R) and (\Theta_C), including scientifically justified coupling and symmetry rules;
- no pre-registered rule yet determines whether automotive-compatible only or extreme/conditional states enter each reported tier;
- a vehicle-specific application requires a compatible current usable-capacity and R10/R1s state measurement or a clearly labelled hypothetical admissible state;
- technical-feasibility handling across the entire conditional state set must be specified without inventing power capability;
- the potentially wide identified intervals may yield mostly indeterminate decisions; this is an empirical outcome to be accepted, not narrowed after inspection;
- manufacturing geography and P14 survival-scale bounds remain unresolved as already documented;
- no lifecycle GHG, carbon contrast, or regime result exists, and none is authorized by this report.

These blockers prohibit immediate computation but do not invalidate Option B as a scientifically defensible architecture.

## 32. Final Status

`TRAJECTORY-FREE ARCHITECTURE VIABLE WITH BOUNDS — RQ REVISION RECOMMENDED`

**STOP — `IMPLEMENTATION_SPEC.md` and the locked Primary RQ were not modified. P15 was not started. Await explicit approval.**
