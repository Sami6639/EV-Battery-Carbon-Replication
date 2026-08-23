# SRC_SCHREIBER_2025 Staged Acquisition Selection

### Scientific Role

Independent automotive-grade NMC capacity/SOH and DC-resistance validation; never the primary ageing fit.

### Full Dataset Size

Approximately 31 GB.

### Full File Count

296 files in the official mediaTUM inventory.

### Required Variables

Capacity/SOH, HPPC/DC response, SOC/protocol, temperature, cycle/time exposure, cell/test identity, realistic commuter ageing and a bounded highway envelope.

### Selected Files

Official source for every path: mediaTUM dataset `10.14459/2024mp1755598`.

| Exact official path | Scientific role | Why required | Size (bytes) | Expected content |
|---|---|---|---:|---|
| `checksums.sha512` | Provenance | Official integrity manifest | 52,887 | SHA-512 paths/digests |
| `commuter_scenario/Aging_commuter_CU_0.txt` | Commuter baseline | Fixed start | 45,093,386 | Original Basytec check-up schema |
| `commuter_scenario/Aging_commuter_CU_10.txt` | Commuter trajectory | Fixed 10-step grid | 44,351,230 | V/I, Ah/Wh, T, cycle/protocol fields |
| `commuter_scenario/Aging_commuter_CU_20.txt` | Commuter trajectory | Fixed 10-step grid | 43,682,476 | Same original schema |
| `commuter_scenario/Aging_commuter_CU_30.txt` | Commuter trajectory | Fixed 10-step grid | 107,197,760 | Same original schema |
| `commuter_scenario/Aging_commuter_CU_40.txt` | Commuter trajectory | Fixed 10-step grid | 105,400,058 | Same original schema |
| `commuter_scenario/Aging_commuter_CU_50.txt` | Late commuter | Fixed 10-step late point in 0-54 series | 104,546,144 | Same original schema |
| `highway_scenario/Aging_highway_CU_0.txt` | Highway baseline | Start of envelope | 45,642,794 | Original Basytec check-up schema |
| `highway_scenario/Aging_highway_CU_11.txt` | Highway midpoint | Deterministic midpoint of 0-22 series | 42,569,075 | Same original schema |
| `highway_scenario/Aging_highway_CU_22.txt` | Highway endpoint | Deterministic endpoint | 90,012,687 | Same original schema |

### Excluded File Categories

Other commuter/highway check-ups, continuous `Aging_*_cyc_*.txt` chunks, and the complete `1C1C_cycling` scenario.

### Reason for Exclusion

The source is validation-only. An outcome-independent index grid preserves start, trajectory and late/end coverage while avoiding redundant volume. Exposure/protocol counters remain in check-up records.

### Expected Coverage

Six commuter and three start/mid/end highway check-ups with original time, V/I, Ah/Wh, temperature, cycle-count and protocol fields.

### Remaining Limitations

Not every intermediate check-up or continuous ageing cycle is present; the subset cannot replace Luh or fit Schreiber-specific lifetime parameters.

### Is Full Dataset Required Later? YES / NO / CONDITIONAL

NO for the locked validation role; CONDITIONAL only for an approved source-specific reconstruction.
