# P14 — Mobility Service, Vehicle Survival & Temporal Carbon-Pathway Input Lock

## 1. Governing Files Read

P14 governing files and all named canonical inputs were read. `PROJECT_INSTRUCTIONS.md` and `docs/IMPLEMENTATION_SPEC.md` remained binding.

## 2. Frozen P13 Inputs

The L2 HV battery-side boundary, 0.093241 kWh/km fresh combined baseline, primary 10-ms and alternative 1-s resistance specifications, bounded pack-loss decomposition, and physical `reconstructed_capacity_retention` field remain unchanged.

## 3. NHTS Data Semantics

The official NHTS 2022 V2.1 codebook defines `ANNMILES=-9` as Not ascertained (213 records), `TRPMILES=-9` as Not ascertained (14), and `GCDTOT=-1` as Appropriate skip (3,604) plus `GCDTOT=-9` as Not ascertained (372). P14 excludes exactly these codes mechanically after preserving the raw/canonical records. Valid counts are 14,471 vehicle-mileage, 31,060 trip, and 13,021 long-distance observations. Published survey weights remain unchanged.

## 4. Annual Mileage Representation

The pre-specified survey-weighted p25/p50/p75 representation is 3,218.688 / 10,729.496448 / 19,312.128 km/year. Quantiles were locked before any lifecycle result and are not probabilities.

## 5. Mobility-Service Requirement Assessment

Candidate A, weighted trip p95, has direct ordinary-trip support but is not a daily-distance distribution. Candidate B, weighted long-distance median, represents a typical observed long-distance movement but not universal range. Candidate C bounds A with long-distance p50 and p75; it is less falsely precise and retains survey weighting.

## 6. Locked Mobility-Service Rule

`BOUNDED_NHTS_TRIP_LONG_DISTANCE_FAMILY` is locked: lower = weighted trip p95 (59.898534 km), central = weighted long-distance p50 (201.174405 km), upper = weighted long-distance p75 (540.621590 km). These are single-service-distance requirements, not universal SOH cutoffs.

## 7. Power-Service Requirement

Technical feasibility uses only the P13 fixed-cycle terminal-power envelope: 37.745525 kW maximum discharge and 35.614420 kW maximum regenerative acceptance magnitude. No new vehicle-dynamics model or SOH cutoff was introduced.

## 8. Vehicle Survival Source and Extraction

Greene & Leard (2024), DOI `10.1016/j.tra.2024.103982`, is retained. The P13 midsize BEV maps to passenger cars, not SUVs/vans or pickups. The publication provides modified-logistic survival methodology, cumulative survival as the product of conditional probabilities, a 2020 passenger-car median of 16.1 years, 0.67%/year projection method, and a 0.5% first-year scrappage adjustment. No microdata or machine-readable fitted curve was claimed.

## 9. Locked Survival Representation

P14 uses the published logistic form and median projection anchor, with `S(a|c)=S(a)/S(c)`. Because the usable passenger-car scale coefficient is not machine-readable in the acquired evidence, 3.5/4.5/5.5-year scale scenarios are explicit bounded assumptions, never source estimates. This is the principal reason for `WITH BOUNDS`.

## 10. Vehicle-Age / Cohort Treatment

Continuous integer-age conditioning (0–25 years within the calendar horizon) is selected over representative age cohorts. The prospective calendar has one 2025 new-vehicle entry cohort. Mileage and survival are independent layers; no correlation was invented.

## 11. Grid Geography Assessment

A preserves 18 GEA regions; B is possible because official Cambium annual data contain `enduse_load`; C combines a load-weighted U.S. central series with all regions as robustness. Equal weighting is rejected.

## 12. Locked Grid Geography

C is locked. For year `y`, national CI is `sum_r(CI[r,y] * enduse_load[r,y]) / sum_r(enduse_load[r,y])`; weights are positive and normalize to one. All 18 regional series remain present.

## 13. Grid Scenario Set

Exact labels `MidCase`, `LowRECost`, and `HighRECost` are preserved without carbon-order nicknames.

## 14. Grid Temporal Interpolation

`GRID_TEMPORAL_INTERPOLATION_LOCK = piecewise_linear_in_domain`. Annual values are generated only for 2025–2050 from the six official nodes. Stepwise holding was considered but not selected because it creates artificial five-year jumps; no official alternative prescription was identified.

## 15. Cambium-2023 LRMER Sensitivity

Mandatory label: `Cambium-2023 LRMER sensitivity`. It remains in its separate 2023 component artifact and is never merged with primary Cambium 2024 average CI.

## 16. Battery-Manufacturing Pathways

Llamas-Orozco pack-level `Current`, `SPS`, and `SDS` values remain chemistry-, pathway-, year-, unit-, and boundary-specific. Seven chemistries are retained separately. NMC811 is not asserted to be the P12 physical cell.

## 17. Manufacturing Temporal Interpolation

`BATTERY_MFG_TEMPORAL_INTERPOLATION_LOCK = piecewise_linear_in_domain`. Each SPS/SDS path connects the same-chemistry 2020 Current node to its 2030/2040/2050 nodes; annual 2025–2050 values are produced. No beyond-horizon extrapolation occurs.

## 18. Static Manufacturing Benchmark

The static benchmark is the same Llamas-Orozco chemistry-specific 2020 Current pack factor held constant. No second source is used.

## 19. Manufacturing Geography Treatment

Canonical geography is absent in all 49 source rows. It remains `UNRESOLVED / SOURCE-IMPLICIT`; U.S. vehicle use is not translated into U.S. manufacturing.

## 20. Xu Robustness Role

Xu et al. (2022) remains directional temporal robustness only. No cell-level absolute value is pooled with Llamas pack-level factors.

## 21. Charging-Conversion Architecture

Sevdari observations define L2→L3 conversion as `E_L3=E_L2/eta`. The simplest bounded p10/p50/p90 efficiencies are 0.827339 / 0.881815 / 0.913573 after the mechanical physical-domain rule `0<eta<=1`; one zero observation is excluded and disclosed. ATB/EPA wall-side values remain validation-only and receive no extra loss factor.

## 22. Calendar Architecture

One `ENTRY_2025` cohort distinguishes entry/current year, vehicle age, battery age, operation year, grid-CI year, candidate replacement year, replacement-manufacturing year, and retirement year. Replacement/retirement fields remain intentionally unset.

## 23. 2050 Horizon Treatment

Operations are truncated transparently at 2050. Residual 2050 survival is retained as a field/parameter; neither grid nor manufacturing values are extended. No post-2050 burden or credit is silently discarded into another period.

## 24. Uncertainty Layers

Mileage, mobility requirement, survival, grid scenario/geography, manufacturing pathway, and charging efficiency remain separate scenario layers. No joint probability distribution or Monte Carlo model was created.

## 25. Input Artifacts Created

Seven requested Parquets, `p14_input_layer_parameters.json`, and `p14_artifact_manifest.json` were generated.

## 26. Files Modified

Added `src/lifecycle_inputs/`, the P14 test module, this report, seven processed inputs, two intermediate JSON files, and—only after the gate—the P14 decision-log entry.

## 27. Tests Run

The full repository suite passed: `50 passed`. Two complete P14 generations produced identical SHA-256 values for all 16 generated Parquet, metadata, configuration, and parameter artifacts checked.

## 28. Lifecycle GHG Calculated

NONE

## 29. Replacement Optimization Performed

NONE

## 30. Extrapolation Performed

NONE

## 31. Frozen-Decision Changes

NONE

## 32. Remaining Validation Items

Passenger-car survival scale coefficients, manufacturing geography, interpretation of long-distance person-trip thresholds as focal-vehicle service, and charger operating-condition transferability remain bounded. Regional load weighting is resolved from official Cambium `enduse_load`.

## 33. Hard Blockers

NONE

## 34. Final Status

LIFECYCLE INPUT ARCHITECTURE VALIDATED WITH BOUNDS
