# SRC_TUM_ID3 Staged Acquisition Selection

### Scientific Role

Cell/pack electrical state to vehicle energy-flow plausibility validation only.

### Full Dataset Size

Approximately 11 GB.

### Full File Count

586 files in the official mediaTUM inventory.

### Required Variables

Cell HPPC/DC response across temperature, OCV context, cell/module/pack topology, HV battery voltage/current in one standard cycle, and a source interpretation aid.

### Selected Files

Official source for every path: mediaTUM dataset `10.14459/2022mp1656314`.

| Exact official path | Scientific role | Why required | Size (bytes) | Expected content |
|---|---|---|---:|---|
| `Data.sha512` | Provenance | Official integrity manifest | 113,180 | SHA-512 paths/digests |
| `Data/02_Battery/01_CAD/Cell_Drawing.pdf` | Cell architecture | Form/dimensions without CAD solids | 66,337 | Cell drawing |
| `Data/02_Battery/01_CAD/Energy_density.xlsx` | Scale/topology | Cell/pack scale quantities | 18,100 | Author workbook |
| `Data/02_Battery/01_CAD/Module_Drawing.pdf` | Module architecture | Intermediate arrangement | 30,811 | Module drawing |
| `Data/02_Battery/01_CAD/Pack_Drawing.pdf` | Pack architecture | Pack arrangement | 41,980 | Pack drawing |
| `Data/02_Battery/04_OCV/VW_78Ah_1584_pOCV_C10_20deg.mat` | OCV context | Compact OCV/SOC interpretation | 1,599,437 | Original 20 °C MAT data |
| `Data/02_Battery/06_HPPC/VW_78Ah_1828_HPPC_3C_9steps_0deg.mat` | Cold HPPC | Temperature bound | 22,887,812 | Original 0 °C nine-step 3C data |
| `Data/02_Battery/06_HPPC/VW_78Ah_1794_HPPC_3C_9steps_20deg.mat` | Central HPPC | Central electrical condition | 22,791,721 | Original 20 °C nine-step 3C data |
| `Data/02_Battery/06_HPPC/VW_78Ah_1856_HPPC_3C_9steps_40deg.mat` | Warm HPPC | Temperature bound | 22,784,679 | Original 40 °C nine-step 3C data |
| `Data/03_Vehicle/01_Characteristics/Postprocess.m` | Interpretation aid | Preserves author processing/schema context | 7,152 | Original MATLAB script |
| `Data/03_Vehicle/06_Cycles/02_Standard_Driving/WLTP/WLTP.csv` | Vehicle energy flow | One validated representative cycle | 277,467,865 | Original WLTP time series with source channels |

### Excluded File Categories

STEP CAD/images; redundant CSV/MAT copies; remaining capacity/scattering/EIS/charging collections; FTP and other cycles; real-world collections; vehicle OCV and full steady-state grid.

### Reason for Exclusion

The role is a plausibility bridge, not vehicle fitting. Three-temperature HPPC, topology/OCV context and one WLTP cycle are sufficient; further formats, cycles and sensors are redundant here.

### Expected Coverage

Cell response at 0/20/40 °C, cell-to-module-to-pack documentation, and one vehicle-level WLTP trace expected to include HV battery voltage/current and energy-flow channels.

### Remaining Limitations

No fleet representativeness, charging-efficiency calibration, complete thermal behavior or full vehicle-map reconstruction claim.

### Is Full Dataset Required Later? YES / NO / CONDITIONAL

NO for the locked plausibility role; CONDITIONAL only for an approved charging or real-world-drive gate.

### P11R Format-Level Recovery — 2026-08-20

Decision: `FORMAT-LEVEL IMPLEMENTATION RECOVERY — SCIENTIFIC SOURCE UNCHANGED`.

The selected MAT files are MATLAB MCOS table serializations that the frozen Python environment cannot decode reproducibly. The official mediaTUM inventory and the author-supplied `Data.sha512` manifest contain CSV representations with identical experiment stems, temperatures, and HPPC protocol labels. Each CSV is therefore the alternative representation of the already-selected test, not an independent observation. The MAT files remain unmodified in raw provenance and are not double-counted.

| Original selected MAT | Official alternate representation | Equivalence basis | CSV SHA-256 |
|---|---|---|---|
| `VW_78Ah_1828_HPPC_3C_9steps_0deg.mat` | `VW_78Ah_1828_HPPC_3C_9steps_0deg.csv` | same official directory, exact experiment stem, 0 °C, 3C, nine steps, both listed in author manifest | `39c7597a80455384fe54578ad80f5b299ca301ad372fc49b7692ac6b7e96cde2` |
| `VW_78Ah_1794_HPPC_3C_9steps_20deg.mat` | `VW_78Ah_1794_HPPC_3C_9steps_20deg.csv` | same official directory, exact experiment stem, 20 °C, 3C, nine steps, both listed in author manifest | `5923b69923143247c052f5ee1c6aaff4e3a9120852fdb1527ab77242c9ac622b` |
| `VW_78Ah_1856_HPPC_3C_9steps_40deg.mat` | `VW_78Ah_1856_HPPC_3C_9steps_40deg.csv` | same official directory, exact experiment stem, 40 °C, 3C, nine steps, both listed in author manifest | `5176752a1010daad637396307966d454e331b127ba0cfe5dff09fb33f9676ebe` |

Scientific role remains HPPC-based cell/pack electrical plausibility validation. Source identity remains `SRC_TUM_ID3` / DOI `10.14459/2022mp1656314`. No parser package or scientific environment change was required.
