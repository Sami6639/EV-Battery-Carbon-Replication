# SRC_LUH_2024 Staged Acquisition Selection

### Scientific Role

Primary NMC/C-SiO capacity/energy degradation and 10-ms/1-s pulse-resistance source for the locked architecture.

### Full Dataset Size

69.4 GB on the official RADAR record.

### Full File Count

14 top-level files.

### Required Variables

Capacity/energy; 10-ms/1-s resistance; SOC; temperature; ageing type, SOC, C-rate and profile; cell/replicate IDs; calendar/cycle exposure; schema and experiment mapping.

### Selected Files

| Exact filename | Official source | Scientific role | Why required | Size (bytes) | Expected content |
|---|---|---|---|---:|---|
| `cell_eocv2.zip` | RADAR `10.35097/1947`, `tRlKWnIpaOUgrqEa` | Capacity/energy and exposure | Primary capacity-SOH observations | 80,961,324 | 228 cell CSVs: capacity, energy, SOH, SOC, T, conditions, throughput |
| `cell_plsv2.zip` | RADAR `10.35097/1947`, `uEtROzxMiabpTrYb` | Pulse resistance | Frozen 10-ms/1-s resistance with SOC/T | 20,815,992 | 228 cell CSVs: resistance, SOC, T, pulse voltage/current |
| `cfg.zip` | RADAR `10.35097/1947`, `spqNhBDlfJGZWpgB` | Condition/ID map | Interprets cells, conditions, C-rate/profile | 92,635 | Per-cell configuration CSVs |
| `Battery Aging Data Plausibility Check v05 (colored).xlsx` | RADAR `10.35097/1947`, `KinNAvNqAnmUGPIL` | Author QA context | Preserves annotations without filtering | 2,211,741 | Plausibility workbook |
| `Cycling Experiment Cell Overview (2024-02-29 20-13).xlsx` | RADAR `10.35097/1947`, `rlySOSkzlhgBUFXd` | Experiment map | Documents replicates and conditions | 253,364 | Experiment overview |
| `Data Structure v05.xlsx` | RADAR `10.35097/1947`, `HLndwPrRzzsGmZTv` | Schema | Interprets selected archives | 184,289 | Data-structure workbook |
| `WLTP_Class_3b_cycle_power_profile.xlsx` | RADAR `10.35097/1947`, `DuigxrqgfPHkOrDM` | Profile documentation | Interprets WLTP ageing profile | 542,561 | Class 3b power profile |

### Excluded File Categories

EIS/corrected-EIS; `cell_log_age.7z`, `cell_logext.7z`, `pool_log.7z`, `slave_log.7z`; plot examples; duplicate PDF overview.

### Reason for Exclusion

EIS is validation-only. Large logger archives are unnecessary because selected author tables retain every locked variable. Other exclusions are derived or duplicate material.

### Expected Coverage

All 228 cell/replicate result files in both primary archives, with conditions, exposure counters and schema. Selection used roles/schemas before scientific-value analysis.

### Remaining Limitations

No raw-event reconstruction or EIS validation.

### Is Full Dataset Required Later? YES / NO / CONDITIONAL

CONDITIONAL — only for a later approved raw-event or EIS gate.
