# P11R Blocker Resolution & Canonical Preprocessing Recovery

### 1. Governing Files Read

Read in full before recovery: `PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/P11_PREPROCESSING_REPORT.md`, `docs/CANONICAL_DATA_DICTIONARY.md`, `docs/STAGED_CORE_DATA_REPORT.md`, `data/metadata/SOURCE_MANIFEST.csv`, `data/metadata/SRC_TUM_ID3_SELECTION.md`, `docs/RESEARCH_DECISION_LOG.md`, and `src/preprocessing/p11_pipeline.py`.

### 2. Original P11 Failure Conditions

P11 remains recorded as `CANONICAL PREPROCESSING FAIL`. Issue C1 was classified `SOURCE RESOURCE / METRIC RESOLUTION`: the staged Cambium 2024 workbook did not expose the required average-CI series. Issue H1 was classified `TECHNICAL SERIALIZATION / PARSER RESOLUTION`: the selected HPPC MAT files contained MATLAB MCOS tables not reproducibly decoded by the frozen Python environment.

### 3. Cambium 2024 Resource Diagnosis

The existing `1744314776-Cambium24_Workbook.xlsx` was preserved unchanged and remains traceable. The official Cambium 2024 Scenario Viewer project exposes a compact annual, all-scenario, all-year, 18-GEA ZIP (project UUID `5c7bef16-7e38-4094-92ce-8b03dfa93380`, file ID `69141`), avoiding the full hourly database. This is a resource-level correction inside the frozen Cambium 2024 source family, not a source substitution. Official references: <https://data.nlr.gov/submissions/289>, <https://scenarioviewer.nlr.gov/>.

### 4. Verified Primary Average-CI Metric

The official Cambium 2024 documentation (<https://docs.nlr.gov/docs/fy25osti/93005.pdf>) defines `aer_load_co2e` as the average emission rate of generation allocated to a region's end-use load. Unit: `kg CO2e/MWh_end-use`. It includes imported/exported power effects, combined combustion and precombustion CO2e, and average distribution losses. Precombustion includes fuel extraction, processing, transport, and fugitive emissions. The dataset covers 18 contiguous-U.S. GEA regions, eight scenarios, and projection years through 2050. No conflict with the frozen energy boundary was found.

### 5. Cambium Recovery Acquisition

Acquired only `ScenarioViewer_Cambium2024_Annual_GEA_file_69141.zip` (263,574 bytes; SHA-256 `b5438ee16c0cf03054bac62520155cbfdc8e98797aba025e48e793fb1527c189`; `RAW_UNMODIFIED`). Its preserved member is `Cambium24_allScenarios_annual_gea.csv`. Selected official machine scenario names are `MidCase`, `LowRECost`, and `HighRECost`; years are 2025, 2030, 2035, 2040, 2045, 2050; all 18 GEA regions are retained.

### 6. Cambium Canonical Output

`data/processed/cambium_2024_average_grid_ci.parquet` contains 324 rows and the required ten fields, with zero missing values or technical rejections. The official numeric value is retained under `grid_ci_gco2e_per_kwh`; the lossless identity `1 kg/MWh = 1 g/kWh` is documented. No national aggregation was performed. `Cambium 2024 average grid CI` remains separate from `Cambium-2023 LRMER sensitivity`.

### 7. TUM HPPC Serialization Diagnosis

The original selected 0/20/40 °C MAT files remain unchanged. Their HPPC payload is a MATLAB MCOS table serialization that SciPy cannot reconstruct as an ordinary numeric struct in the frozen environment. Because an official equivalent format exists, no decoder installation or isolated conversion environment was needed.

### 8. Official Alternate Representation Search

The official mediaTUM dataset (<https://mediatum.ub.tum.de/1656314>, DOI `10.14459/2022mp1656314`) lists CSV and MAT pairs in the same HPPC directory. Each pair has the exact experiment stem, cell/test ID, `3C_9steps` protocol, and temperature. The author `Data.sha512` manifest independently lists and checksums all six files.

### 9. HPPC Recovery Method

The three official CSV equivalents were acquired by exact path. Their author-manifest SHA-512 values matched. The pipeline reads every CSV row, assigns source row and temperature provenance, preserves observed protocol/electrical channels, and only converts source hours to seconds by multiplication by 3600. The CSV and MAT forms are treated as the same experiments and are not double-counted. Classification: `FORMAT-LEVEL IMPLEMENTATION RECOVERY — SCIENTIFIC SOURCE UNCHANGED`.

### 10. HPPC Canonical Output

`data/processed/tum_id3_hppc_observations.parquet` contains 2,801,203 rows, 24 columns, all three temperatures `{0, 20, 40}` °C, and zero technical rejections. It includes provenance, test/protocol identifiers, time, voltage, current, charge/energy, temperature, author RAC/RDC source channels, cycle/state fields, and `parse_issue_flag`. No fitted resistance, R/R0, degradation, pack-loss, vehicle-penalty, or inferred SOC field was created.

### 11. Change-Control Records

Cambium resource history was appended to `data/metadata/SRC_CAMBIUM_2024.yaml`. TUM format equivalence and checksums were appended to `data/metadata/SRC_TUM_ID3_SELECTION.md` and `data/metadata/SRC_TUM_ID3.yaml`. The P11 failure record was retained and this P11R decision was appended afterward.

### 12. Raw Integrity Verification

All 33 pre-recovery raw files matched their pre-recovery SHA-256 values. Four newly acquired files have recorded byte sizes and SHA-256 values; all are `RAW_UNMODIFIED`. The three TUM CSVs also match the author's SHA-512 manifest. No raw file was overwritten and no raw scientific value was manually edited. Evidence: `data/metadata/P11R_PRE_RECOVERY_RAW_SHA256.json` and `data/metadata/P11R_RAW_INTEGRITY_VERIFICATION.json`.

### 13. P11 Pipeline Re-run

Two complete executions of `p11_pipeline.main()` followed by `p11_pipeline.extras()` regenerated the full canonical set from raw inputs. Final reconciliation contains 14 canonical Parquet outputs, including the two recovered outputs. No Parquet was manually patched.

### 14. Determinism Verification

The first and second corrected complete runs produced identical file sets and identical SHA-256 values for all 32 pipeline-generated canonical output and metadata files; mismatches: none. The final HPPC Parquet SHA-256 is `e035360aae5ddd1fb815660e72b30257c8a9f2428a112f5a98b769277893e61b`; Cambium average Parquet SHA-256 is `a315b23d9b4e055ae6cf8864ddd9d6d74513cc3057c4f78c1e871de7450efcc6`. Evidence: `data/processed/metadata/p11r_determinism.json`.

### 15. Tests Run

Complete suite: `22 passed` in 111.02 seconds. Focused tests verify metric identity/version/unit identity, 18 regions/six years/three scenarios, LRMER separation, all three HPPC temperatures, non-empty canonical output, complete core HPPC channels across chunk boundaries, source lineage, absence of scientific-derived fields, and all pre-recovery raw checksums. One non-substantive pytest-cache permission warning occurred; it did not affect tests or outputs.

### 16. Scientific Fitting Performed

`NONE`

### 17. Scientific Filtering Performed

`NONE`

### 18. Frozen Source Substitutions

`NONE`

### 19. Methodological Changes

`NONE`

### 20. Remaining Validation Items

`BASELINE_DEFINITION_VALIDATION_REQUIRED`, `NATIONAL_AGGREGATION_VALIDATION_REQUIRED`, and NHTS mobility-threshold selection remain unresolved for later authorized stages. No national grid weighting, HPPC resistance interpretation, or SOC inference was introduced.

### 21. Hard Blockers

`NONE`

### 22. Final Status

`CANONICAL PREPROCESSING RECOVERED — PASS`
