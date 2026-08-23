# P10.5 — Controlled Staged Acquisition of Large Core Datasets

### 1. Governing Files Read

- `PROJECT_INSTRUCTIONS.md`
- `docs/IMPLEMENTATION_SPEC.md`
- `docs/IMPLEMENTATION_BASELINE_REPORT.md`
- `docs/DATA_ACQUISITION_REPORT.md`
- `data/metadata/SOURCE_MANIFEST.csv`
- `docs/RESEARCH_DECISION_LOG.md`

The frozen source identities and locked scientific roles were retained.

### 2. Official Inventories Inspected

- Luh & Blank: official RADAR dataset `10.35097/1947`; public file-table endpoint reported 14 top-level files, exact byte sizes, entity IDs and official MD5 digests.
- Schreiber: official mediaTUM dataset `10.14459/2024mp1755598`; public FTP inventory reported 296 files under commuter, highway and 1C/1C scenarios plus `checksums.sha512`.
- TUM ID.3: official mediaTUM dataset `10.14459/2022mp1656314`; public FTP inventory reported 586 files plus `Data.sha512`.
- Sevdari optional retry: official DTU/Figshare API confirmed Version 1, nine files and CC BY 4.0.

Only names, paths, sizes, source metadata, archive member names and schema/header fields were inspected. No scientific values were processed.

### 3. Luh Minimum Subset

Seven files totaling 105,061,906 bytes were frozen and acquired. `cell_eocv2.zip` provides all 228 cell capacity/energy-SOH result tables; `cell_plsv2.zip` provides all 228 cell 10-ms/1-s resistance tables with SOC and temperature; `cfg.zip` maps cells, replicates, conditions, rates and profiles. Four author workbooks preserve QA, experiment mapping, schema and WLTP-profile documentation. Exact roles, sizes and exclusions are frozen in `data/metadata/SRC_LUH_2024_SELECTION.md`.

### 4. Schreiber Minimum Subset

Nine raw check-up files plus the official checksum manifest total 628,548,497 bytes. The outcome-independent grid contains commuter CU indices 0, 10, 20, 30, 40 and 50, plus highway start/mid/end indices 0, 11 and 22. This retains original Basytec voltage, current, Ah/Wh, temperature, cycle count and protocol channels for automotive validation. Exact scope is frozen in `data/metadata/SRC_SCHREIBER_2025_SELECTION.md`.

### 5. TUM ID.3 Minimum Subset

Ten source files plus the official checksum manifest total 347,809,074 bytes. The subset contains cell/module/pack drawings and energy-density documentation, compact 20 °C OCV, original HPPC MAT files at 0/20/40 °C, the author `Postprocess.m`, and one original WLTP vehicle CSV. Exact scope is frozen in `data/metadata/SRC_TUM_ID3_SELECTION.md`.

### 6. Files Actually Downloaded

Luh (7):

- `Battery Aging Data Plausibility Check v05 (colored).xlsx`
- `cell_eocv2.zip`
- `cell_plsv2.zip`
- `cfg.zip`
- `Cycling Experiment Cell Overview (2024-02-29 20-13).xlsx`
- `Data Structure v05.xlsx`
- `WLTP_Class_3b_cycle_power_profile.xlsx`

Schreiber (10):

- `checksums.sha512`
- `commuter_scenario/Aging_commuter_CU_{0,10,20,30,40,50}.txt`
- `highway_scenario/Aging_highway_CU_{0,11,22}.txt`

TUM ID.3 (11):

- `Data.sha512`
- `Data/02_Battery/01_CAD/{Cell_Drawing.pdf,Energy_density.xlsx,Module_Drawing.pdf,Pack_Drawing.pdf}`
- `Data/02_Battery/04_OCV/VW_78Ah_1584_pOCV_C10_20deg.mat`
- `Data/02_Battery/06_HPPC/VW_78Ah_1828_HPPC_3C_9steps_0deg.mat`
- `Data/02_Battery/06_HPPC/VW_78Ah_1794_HPPC_3C_9steps_20deg.mat`
- `Data/02_Battery/06_HPPC/VW_78Ah_1856_HPPC_3C_9steps_40deg.mat`
- `Data/03_Vehicle/01_Characteristics/Postprocess.m`
- `Data/03_Vehicle/06_Cycles/02_Standard_Driving/WLTP/WLTP.csv`

Sevdari optional retry (1 package):

- `25425262_v1.zip`, containing all nine original Version 1 filenames.

### 7. Total Bytes Downloaded

1,082,475,875 bytes across 29 retained raw files, including the optional Sevdari package. This is below the 2 GiB automatic-acquisition limit of 2,147,483,648 bytes. CORE-only staged bytes are 1,081,419,477.

### 8. Files Deferred

- Luh: EIS/corrected-EIS, large raw logger archives, result plots and duplicate PDF documentation.
- Schreiber: unselected intermediate check-ups, continuous ageing-cycle chunks and 1C/1C scenario.
- TUM ID.3: CAD solids/media, redundant representations, other cycles, real-world collections, optional charging, EIS and full vehicle-map files.
- Lower-priority Wheeler LFP, TUM Model 3 LFP, Hanna recycling and Du recycling sources remain deferred exactly as instructed.

### 9. Manual Action Required

NONE. Every frozen minimum-subset file was acquired from its official repository. No manual file selection is required for preprocessing readiness.

### 10. Metadata Updated

Created/updated `SRC_LUH_2024.yaml`, `SRC_SCHREIBER_2025.yaml`, `SRC_TUM_ID3.yaml`, and `SRC_SEVDARI_2023.yaml`. Every retained raw file has its original filename/package name, official reference, retrieval date, licence, byte size, scientific role, raw path, SHA-256 and `RAW_UNMODIFIED` status.

### 11. Manifest Updated

The three CORE sources are `PARTIALLY_ACQUIRED_AND_CHECKSUMMED`, explicitly denoting intentional scientific subsets. Sevdari is `ACQUIRED_AND_CHECKSUMMED`. Frozen identity fields were not changed.

### 12. SHA-256 Verification

All 29 retained files match their recorded SHA-256 metadata. In addition, all seven Luh files match official RADAR MD5 values; all nine Schreiber scientific files match `checksums.sha512`; and all ten TUM ID.3 scientific files match `Data.sha512`.

### 13. Tests Run

`tests/test_raw_data_provenance.py` and `tests/test_staged_core_data.py`: **8 passed in 16.47 s**. Checks cover existence, positive/exact size, SHA-256 agreement, source-directory confinement, original filenames, selection records, manifest uniqueness/status, no processed/results copies, and the 2 GiB limit.

### 14. Scientific Processing Performed

NONE

### 15. Frozen Source Substitutions

NONE

The corrected EIS addendum was not downloaded or substituted for the frozen Luh primary source.

### 16. Hard Blockers

NONE. RADAR returned transient HTTP 429 rate limits; respectful delayed retries completed all seven selected files. No authentication, paywall or access control was bypassed.

### 17. Final Status

CORE STAGED DATA READY
