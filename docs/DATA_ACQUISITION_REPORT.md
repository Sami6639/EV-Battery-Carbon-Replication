# P10 Frozen Source Acquisition and Raw-Data Provenance Report

Audit date: 2026-08-20

Scope was limited to frozen-source access verification, safe acquisition, immutable raw storage, provenance metadata, checksums, and non-scientific provenance tests. No preprocessing or scientific analysis was performed.

## 1. Governing Files Read

The following files were read completely before acquisition work:

- `PROJECT_INSTRUCTIONS.md`
- `docs/IMPLEMENTATION_SPEC.md`
- `docs/IMPLEMENTATION_BASELINE_REPORT.md`
- `environment.yml`
- `requirements-lock.txt`

`docs/RESEARCH_DECISION_LOG.md` was created with only the permitted P09 decision record.

## 2. Frozen Sources Audited

Fourteen frozen/approved source records were audited:

1. Luh and Blank 2024
2. Schreiber et al. 2025
3. TUM Volkswagen ID.3 multiscale dataset
4. NHTS 2022 V2.1
5. Greene and Leard 2024
6. Cambium 2024
7. Cambium-2023 LRMER sensitivity
8. Llamas-Orozco et al. 2023
9. Xu et al. 2022
10. Sevdari et al. 2023
11. Hanna Somers and Anctil 2025
12. Du et al. 2022
13. Wheeler et al. 2025
14. TUM Tesla Model 3 LFP dataset

All source identities remain consistent with `docs/IMPLEMENTATION_SPEC.md`.

## 3. Source Manifest Created

Created `data/metadata/SOURCE_MANIFEST.csv` with 14 unique source IDs and all requested manifest columns.

Final acquisition-status counts:

- `ACQUIRED_AND_CHECKSUMMED`: 4
- `MANUAL_OR_STAGED_DOWNLOAD_REQUIRED`: 4
- `ACCESS_VERIFIED_DOWNLOAD_DEFERRED`: 4
- `ARTICLE_ONLY_PARAMETER_SOURCE`: 1
- `SUPPLEMENTARY_DATA_NOT_VERIFIED`: 1

## 4. Sources Acquired

The following official files were downloaded without renaming or modification:

- NHTS 2022 V2.1 official CSV archive: 4,533,528 bytes
- Cambium 2024 official workbook: 26,541,986 bytes
- Cambium-2023 LRMER sensitivity official workbook: 17,363,130 bytes
- Llamas-Orozco associated Figshare Version 2 workbook: 601,886 bytes

All four files are non-empty, readable ZIP/Open XML containers where applicable, and checksummed after download.

## 5. Sources Deferred

- Sevdari et al. 2023: official DTU Version 1 dataset manifest verified; download deferred after two official endpoints failed to transfer the first file.
- Hanna Somers and Anctil 2025: open article and two official supporting files verified; lower-priority download deferred.
- Du et al. 2022: official free supporting-information PDF verified; lower-priority download deferred.
- TUM Tesla Model 3 LFP: official 984 MB two-file dataset verified; lower-priority extension download deferred.
- Greene and Leard 2024: retained as `ARTICLE_ONLY_PARAMETER_SOURCE`; no raw supplementary dataset was assumed.
- Xu et al. 2022: open article verified; supplementary material was not sufficiently inventoried for acquisition and is recorded as `SUPPLEMENTARY_DATA_NOT_VERIFIED`.

## 6. Manual/Staged Downloads Required

- Luh and Blank 2024: official RADAR4KIT archive is 69.4 GB. It exceeds the 2 GB automatic-download limit. Official file-level staging is required. The official record also identifies a corrected EIS addendum; it was not silently substituted for the frozen dataset.
- Schreiber et al. 2025: official mediaTUM dataset contains 296 files totaling 31 GB under CC BY 4.0. File-level or official rsync staging is required.
- TUM Volkswagen ID.3: official mediaTUM dataset contains 586 files totaling 11 GB under CC BY 4.0. The exact multiscale subset must be selected before staged acquisition.
- Wheeler et al. 2025: official Recherche Data Gouv dataset contains many large per-cell archives and exceeds 2 GB in total. Custom dataset terms and an exact LFP subset require staged acquisition.

These are verified official paths and do not change any frozen source identity.

## 7. Access Problems

- Sevdari official dataset identity, Version 1 metadata, CC BY 4.0 licence, nine-file inventory, and total size of 1,054,912 bytes were verified through the official DTU record/API. The Figshare download endpoint closed the transport connection; the DTU-domain alternative returned no payload. No empty or partial file was retained. Status: `ACCESS_VERIFIED_DOWNLOAD_DEFERRED`.
- Xu supplementary data inventory remains unverified. Status: `SUPPLEMENTARY_DATA_NOT_VERIFIED`.

No critical Tier P10-A source is `ACCESS_BLOCKED` or `NOT_FOUND`.

## 8. Raw Storage Paths

- `data/raw/SRC_NHTS_2022/csv.zip`
- `data/raw/SRC_CAMBIUM_2024/1744314776-Cambium24_Workbook.xlsx`
- `data/raw/SRC_CAMBIUM_LRMER_2023/1707947178-Cambium23_LRMER_GEAregions_0.xlsx`
- `data/raw/SRC_LLAMAS_OROZCO_2023/LIBs-LCA Supplmentary tables_final_final.xlsx`

No raw file was extracted, renamed, overwritten, moved into `processed/`, or copied into `results/`.

## 9. Metadata Records

Created:

- `data/metadata/SRC_NHTS_2022.yaml`
- `data/metadata/SRC_CAMBIUM_2024.yaml`
- `data/metadata/SRC_CAMBIUM_LRMER_2023.yaml`
- `data/metadata/SRC_LLAMAS_OROZCO_2023.yaml`

Every acquired file record includes the official source, retrieval date, version, licence status, original filename, byte size, raw relative path, SHA-256, and `transformation_status: RAW_UNMODIFIED`.

## 10. SHA-256 Checksums

- NHTS `csv.zip`: `64530C396D5F164D2259A22F7042F27BEE5147BABCD367568DDBFAFE6C8BF34C`
- Cambium 2024 workbook: `80E930A78640D423ACE34517EB8101A07A38B9A5C1D899E3ED33F0F63F9A63EB`
- Cambium-2023 LRMER sensitivity workbook: `E4C0CDB757C4CDA608D41333614E1FB7DAD4480D446A8616F6AFB9F671A8D722`
- Llamas-Orozco associated Figshare workbook: `19842D347627B95A46D1B9A0ED91C81219846651D20EB1494907A3DD4D5AE24F`

Checksums were computed from the preserved original downloads. The files were not changed afterward.

## 11. Provenance Tests

Created `tests/test_raw_data_provenance.py`.

It verifies:

- manifest existence and 14 unique frozen source IDs;
- representation of every critical Tier P10-A source;
- use of only allowed final acquisition statuses;
- metadata existence for each acquired source;
- raw paths remaining under `data/raw/`;
- non-empty raw files;
- byte-size agreement;
- complete 64-character SHA-256 values and checksum equality;
- exact correspondence between acquired raw files and metadata records;
- absence of acquired raw filenames from `data/processed/` and `results/`.

Combined baseline and provenance test result: `8 passed`.

## 12. Frozen-Source Substitutions

NONE

## 13. Scientific Data Processing Performed

NONE

## 14. Hard Blockers

NONE

All critical Tier P10-A sources are either acquired and checksummed or have officially verified staged/manual acquisition paths that preserve the frozen source identity.

## 15. Final Status

`RAW DATA PROVENANCE PASS`
