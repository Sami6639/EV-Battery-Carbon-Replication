# P11 Preprocessing Report
## 1. Governing Files Read
PROJECT_INSTRUCTIONS.md, docs/IMPLEMENTATION_SPEC.md, the P09/P10/P10.5 reports, source manifest, three frozen selection records, and the research decision log were read before processing. Frozen scientific decisions were binding.
## 2. Raw Sources Processed
In-place reads covered Luh, Schreiber, TUM ID.3, NHTS 2022 V2.1, Cambium 2024, Cambium-2023 LRMER, Llamas-Orozco, and Sevdari Version 1. Archives were not expanded into data/raw.
## 3. Raw Checksums Reverified
The pre-P11 provenance/baseline suite passed (13 tests). The full post-P11 suite also passed. No raw file was edited, renamed, deleted, or overwritten.
## 4. Canonical Data Dictionary
docs/CANONICAL_DATA_DICTIONARY.md was created before numerical transformation. It records source fields, units, dtypes, null rules, transformation status, and scientific role. Only observed and LOSSLESS_DERIVED fields exist.
## 5. Luh Schema and Outputs
The 228 EOCV members produced 1,098,399 capacity rows; 228 pulse members produced 2,149,823 resistance rows; 228 cell CFG members produced 228 condition rows. Rejections and detected exact duplicates were zero. Capacity and source SOH are missing in 591,132 EOCV rows and remain null. Absolute 10-ms and 1-s resistance were retained; mOhm-to-ohm is explicit. No R/R0 was calculated.
## 6. Schreiber Schema and Outputs
Nine files (six commuter, three highway) produced 2,287,818 rows. Scenario, CU, identity, time, voltage, current, Ah, Wh, temperatures, cycle count and protocol markers were retained. No rows were rejected or combined into a synthetic trajectory.
## 7. TUM ID.3 Schema and Outputs
OCV produced 23,174 rows and WLTP 322,720 rows. The architecture workbook became tum_id3_pack_architecture.yaml. Three HPPC files expose MATLAB MCOS table objects whose 262 MB function-workspace serialization cannot be decoded by the staged Python environment; zero HPPC rows were emitted and all three failures are explicit.
## 8. NHTS Schema and Outputs
Vehicle (14,684), trip (31,074), and long-distance (16,997) rows were retained. ANNMILES, TRPMILES, GCDTOT, identifiers and weights were preserved. Mile-to-km uses 1.609344. No quantile, threshold, exclusion, or aggregation was selected. The ZIP has a citation PDF but no official variable dictionary; final semantic choices remain validation items.
## 9. Cambium 2024 Schema and Outputs
The staged file is internally an LRMER workbook. It does not contain time-varying average grid carbon intensity. No average-CI output was fabricated and LRMER was not substituted. Processed rows: 0; source-identity conflicts: 1.
## 10. Cambium-2023 LRMER Schema and Outputs
The separate 2023 workbook produced 5,184 regional annual component rows with scenario, GEA, year, gas/stage metric, unit and source coordinates. No GWP combination or national aggregation was performed. The filename explicitly includes lrmer_2023.
## 11. Battery-Manufacturing Schema and Outputs
Llamas-Orozco S18 produced 49 chemistry/pathway/year pack-production rows. All seven chemistries remain distinct. The explicit Total per kWh battery boundary is pack-level; geography is null because it is not explicit in these columns. No interpolation or averaging occurred.
## 12. Sevdari Schema and Outputs
All nine package files were inventoried. Three numerical workbooks produced 854 validation rows. Missingness is preserved: efficiency 497, power factor 538, reactive power 510. Percent was divided by 100; no central parameter was created.
## 13. Unit Harmonization
Applied: mOhm-to-ohm times 0.001, miles-to-km times 1.609344, percent-to-fraction divided by 100. No Ah-to-kWh, cell-to-pack, GWP, or national aggregation conversion was done.
## 14. Missingness and Parse Issues
No imputation, interpolation, fill, clipping, or outlier deletion occurred. Issues are three unsupported HPPC MCOS tables and the Cambium 2024 source-identity conflict. No silent row loss occurred in emitted tables.
## 15. Derived Variables Created
LOSSLESS_DERIVED only: provenance, filename labels, CU index, mechanical conversions, pack boundary, and descriptive baseline-candidate flag. SCIENTIFIC_DERIVED: NONE.
## 16. Files Created
Created: canonical dictionary; three preprocessing source files; one test file; 12 Parquet datasets; one architecture YAML; 12 lineage YAML files; reproducibility/reconciliation metadata; and this report.
## 17. Files Modified
docs/RESEARCH_DECISION_LOG.md was appended only after the gate result was known. No frozen governing document or raw source was modified.
## 18. Tests Run
Pre-transform: 13 passed. Final: 17 passed in 30.57 s. Coverage includes raw provenance, schemas, identities, conversions, pack boundary, missingness, no scientific filtering, blockers, and row agreement. A second complete run produced identical SHA-256 hashes for all 12 Parquet outputs (semantically_identical = true).
## 19. Scientific Fitting Performed
NONE
## 20. Scientific Filtering Performed
NONE
## 21. Frozen-Decision Changes
NONE
## 22. Open Validation Items
BASELINE_DEFINITION_VALIDATION_REQUIRED; NATIONAL_AGGREGATION_VALIDATION_REQUIRED; NHTS semantic/quantile/mobility-threshold selection; reproducible MATLAB MCOS decoding for HPPC.
## 23. Hard Blockers
1. Frozen Cambium 2024 architecture requires average grid CI, but the staged workbook is LRMER. This source-identity conflict meets the explicit FAIL condition.
2. All three HPPC files use unsupported MATLAB MCOS table serialization, so a critical selected subset did not parse reproducibly.
## 24. Final Status
CANONICAL PREPROCESSING FAIL
