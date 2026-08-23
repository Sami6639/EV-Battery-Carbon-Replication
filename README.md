# EV Battery Carbon Replication

Reproducibility package for the study:

**Battery Replacement as a Lifecycle Carbon Decision: Trajectory-Free Set Identification in the Same BEV**

Repository: https://github.com/Sami6639/EV-Battery-Carbon-Replication

## Overview

This repository contains the computational workflow, provenance metadata, validation reports, environment specifications, and tests used to support a trajectory-free, state-conditioned lifecycle greenhouse-gas (GHG) comparison between:

- **C — Continue:** continued first-life use of the installed traction battery; and
- **R — Replace:** immediate traction-battery replacement in the **same BEV**.

The analysis does **not** infer a battery replacement age, time-to-state, or long-run degradation trajectory. Instead, it conditions the comparison on empirically admissible current battery states and evaluates policy-symmetric lifecycle-GHG bounds across matched vehicle-service and carbon contexts.

The core policy contrast is

\[
\Delta G = G_R - G_C,
\]

where positive values indicate lower lifecycle GHG for continued first-life use and negative values indicate lower lifecycle GHG for immediate replacement.

## Main scientific result

Within the implemented and source-supported domain:

- **567** admissible dual-state NMC battery states were evaluated.
- **3,402 / 3,402** primary state-context intervals were classified as **ROBUST CONTINUE**.
- The minimum primary lower lifecycle-GHG margin was approximately **5,464.41 kg CO2e**.
- **17,010 / 17,010** temporal state-context intervals across 2025–2045 remained **ROBUST CONTINUE**.
- The global temporal minimum lower margin was approximately **4,011.59 kg CO2e**.
- The maximum primary operational-carbon saving from replacement was approximately **3.1787 kg CO2e**.
- The primary manufacturing-intensity break-even threshold was approximately **0.0411 kg CO2e/kWh_pack**, compared with a minimum frozen prospective NMC811 manufacturing intensity of approximately **48.9176 kg CO2e/kWh_pack**.

These results are bounded to the implemented evidence architecture and should not be interpreted as a universal engineering rule against battery replacement.

## Methodological boundary

The repository implements a **trajectory-free** decision architecture. The following are intentionally **not** inferred:

- no real-world degradation trajectory;
- no time-to-state;
- no calendar-time assignment of battery state;
- no replacement-time optimization;
- no universal state-of-health retirement threshold;
- no complete aged-state engineering replacement rule.

Calendar year enters only as an exogenous grid-carbon, battery-manufacturing, and residual-service context.

## Repository structure

```text
EV-Battery-Carbon-Replication/
├── data/
│   └── metadata/              # Provenance, source manifests, source selections, contracts
├── docs/                      # Scientific validation, architecture, and decision reports
├── src/
│   ├── preprocessing/         # Canonical preprocessing and verification
│   ├── degradation/           # NMC dual-state degradation processing
│   ├── degradation_bridge/    # Historical bridge assessment code
│   ├── degradation_bridge_r3/ # Controlled bridge-revision code and audits
│   ├── vehicle_energy/        # FASTSim-based vehicle-energy translation
│   ├── lifecycle_inputs/      # Mobility, survival, grid, charging, manufacturing inputs
│   ├── lifecycle_accounting/  # P15/P16 accounting, bounds, classification, robustness
│   └── source_freeze/         # Source-artifact freeze utilities
├── tests/                     # Validation and regression tests
├── environment.yml            # Conda environment specification
├── requirements-lock.txt      # Pinned Python package versions
└── .gitignore
```

## Software environment

The frozen analysis environment is based on:

- **Python 3.11.15**
- **FASTSim 3.0.6**
- NumPy
- pandas
- SciPy
- PyArrow
- Matplotlib
- OpenPyXL
- PyYAML
- pytest

The exact environment is defined in `environment.yml` and `requirements-lock.txt`.

### Create the Conda environment

```bash
conda env create -f environment.yml
conda activate ev-battery-carbon
```

If the environment already exists:

```bash
conda env update -f environment.yml --prune
conda activate ev-battery-carbon
```

## Reproduction workflow

The computational workflow is organized sequentially rather than as a single black-box script.

### 1. Canonical preprocessing

Relevant modules are located in:

```text
src/preprocessing/
```

These scripts standardize source data, enforce schema and provenance rules, and generate canonical machine-readable inputs.

### 2. NMC battery-state construction

Relevant modules are located in:

```text
src/degradation/
```

The primary state representation preserves both:

- usable-capacity retention; and
- relative pulse resistance.

The primary resistance specification uses the validated **10-ms, 50% SOC, 25°C** domain. A separate **1-s** specification is retained for robustness.

### 3. Vehicle-energy translation

Relevant modules are located in:

```text
src/vehicle_energy/
```

FASTSim v3.0.6 is used to translate supported battery resistance states into vehicle-level battery-side energy consequences. Resistance percentages are **not** directly equated to energy-use percentages.

### 4. Lifecycle input architecture

Relevant modules are located in:

```text
src/lifecycle_inputs/
```

This stage constructs matched mobility, vehicle-survival, charging-efficiency, grid-carbon, and prospective battery-manufacturing contexts.

### 5. Lifecycle accounting and identified-set analysis

Relevant modules are located in:

```text
src/lifecycle_accounting/
```

The P15/P16 workflow implements:

- same-BEV continuation-versus-immediate-replacement accounting;
- policy-symmetric admissible endpoint sets;
- lower and upper lifecycle-GHG bounds;
- sign-based carbon classification;
- temporal context modulation;
- resistance-timescale robustness;
- mobility, mileage, survival, charging, regional-grid, and vehicle-age robustness;
- Cambium-2023 LRMER sensitivity;
- conditional/extreme physical stress tests; and
- manufacturing-intensity break-even analysis.

## Decision rule

For each matched context, the identified lifecycle-GHG interval is classified as:

\[
\text{ROBUST CONTINUE}
\quad \text{if} \quad
\underline{\Delta G} > 0,
\]

\[
\text{CARBON DECISION INDETERMINATE}
\quad \text{if} \quad
\underline{\Delta G} \le 0 \le \overline{\Delta G},
\]

and

\[
\text{ROBUST REPLACE}
\quad \text{if} \quad
\overline{\Delta G} < 0.
\]

No probabilistic interpretation is attached to these identified intervals.

## Tests

Regression and scientific-contract tests are located in `tests/`.

Where all required source artifacts are available locally, tests can be run with:

```bash
pytest -q
```

Some tests and pipeline stages depend on third-party source artifacts that are **not redistributed in this public repository**. Those stages require independent source acquisition before execution.

## Data provenance and third-party data

The repository is designed to preserve provenance without redistributing third-party raw data where licences or source terms do not permit redistribution.

Source metadata, source identifiers, acquisition records, selection documents, and processing lineage are stored under:

```text
data/metadata/
docs/
```

Important source families include:

- Luh & Blank (2024) NMC capacity and impedance ageing evidence;
- Schreiber et al. (2025) automotive NMC validation evidence;
- Volkswagen ID.3 multiscale evidence;
- FASTSim v3.0.6;
- 2022 NextGen NHTS;
- Greene & Leard (2024) vehicle survival;
- Cambium 2024 average grid-carbon pathways;
- Cambium-2023 LRMER sensitivity;
- Llamas-Orozco et al. (2023) prospective battery-manufacturing pathways; and
- Sevdari et al. (2023) charging-efficiency evidence.

Users should obtain any non-redistributed third-party data directly from the original providers and comply with the corresponding licences and terms of use.

## Important robustness boundaries

The following layers are **not** represented as completed numerical robustness analyses:

- Xu et al. (2022) as a separate manufacturing sensitivity; and
- recycling-credit sensitivity.

These sources are used for literature positioning and limitations, not as implemented numerical P16 result layers.

Aged-state power capability is also not resolved state by state. Therefore, the repository supports a lifecycle-GHG classification, **not** a complete engineering replacement recommendation.

## Reproducibility and provenance

The project uses:

- pinned software dependencies;
- deterministic processing;
- machine-readable intermediate artifacts;
- source manifests and metadata;
- schema and integrity checks;
- explicit evidence-role separation; and
- regression tests.

Scientific design decisions and validation history are documented in `docs/`.

## Associated manuscript

**Battery Replacement as a Lifecycle Carbon Decision: Trajectory-Free Set Identification in the Same BEV**

Journal citation and DOI will be added here after publication.

## Citation

Until a publication DOI or archived software DOI is available, please cite the associated manuscript and this repository URL:

> Sami Küçükoğlu. *EV Battery Carbon Replication*.  
> https://github.com/Sami6639/EV-Battery-Carbon-Replication

For reproducible reporting, users are encouraged to record the exact Git commit hash used in their analysis.

## Funding

This research received no external funding.

## Conflict of Interest

The author declares no conflict of interest.

## Licence and reuse

Third-party datasets remain subject to their original licences and terms of use.

No rights to third-party raw data are granted by this repository. Code reuse should follow the repository's `LICENSE` file if and when one is added.

## Contact

Questions concerning the replication workflow may be submitted through the repository's GitHub Issues page.
