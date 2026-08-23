from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "data"
    / "processed"
    / "cambium_lrmer_2023_components.parquet"
)

SEARCH_ROOTS = [
    ROOT / "src",
    ROOT / "data" / "processed" / "metadata",
    ROOT / "docs",
]


print("=" * 78)
print("P16R-D4E1A2 — CAMBIUM-2023 LRMER COMPONENT CONTRACT AUDIT")
print("=" * 78)


# ============================================================
# 1. LOAD
# ============================================================

d = pd.read_parquet(FILE)

assert not d.empty


# ============================================================
# 2. EXACT COMPONENT CONTRACT
# ============================================================

component_table = (
    d.groupby(
        [
            "metric_identity",
            "unit",
        ],
        as_index=False,
    )
    .agg(
        rows=("metric_value", "size"),
        min_value=("metric_value", "min"),
        max_value=("metric_value", "max"),
    )
    .sort_values(
        [
            "metric_identity",
            "unit",
        ]
    )
)


print("\nExact metric identities:")

print(
    component_table.to_string(
        index=False
    )
)


# ============================================================
# 3. EXPECTED PANEL COMPLETENESS
# ============================================================

print("\nPanel dimensions:")

print(
    "scenarios:",
    d["scenario"].nunique(),
)

print(
    "regions:",
    d["region"].nunique(),
)

print(
    "years:",
    sorted(
        d["calendar_year"]
        .unique()
        .tolist()
    ),
)

print(
    "metrics:",
    d["metric_identity"].nunique(),
)


key = [
    "scenario",
    "region",
    "calendar_year",
    "metric_identity",
]

duplicate_rows = int(
    d.duplicated(
        subset=key,
        keep=False,
    ).sum()
)

print(
    "duplicate key rows:",
    duplicate_rows,
)


panel = (
    d.groupby(
        [
            "scenario",
            "region",
            "calendar_year",
        ]
    )["metric_identity"]
    .nunique()
)

print(
    "metric-count distribution per scenario-region-year:"
)

print(
    panel.value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# 4. PARSE ISSUES
# ============================================================

print("\nParse issues:")

print(
    d["parse_issue_flag"]
    .value_counts(
        dropna=False
    )
    .to_string()
)


# ============================================================
# 5. SEARCH LOCAL AUTHORITATIVE FILES FOR
#    GWP / CO2E CONVERSION OR LRMER AGGREGATION RULES
# ============================================================

patterns = [
    "gwp",
    "co2e",
    "ch4",
    "n2o",
    "lrmer",
    "global warming potential",
]

hits = []

for root in SEARCH_ROOTS:

    if not root.exists():
        continue

    for path in root.rglob("*"):

        if (
            not path.is_file()
            or path.suffix.lower()
            not in {
                ".py",
                ".yaml",
                ".yml",
                ".json",
                ".md",
                ".txt",
            }
        ):
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        lower = text.lower()

        if any(
            pattern in lower
            for pattern in patterns
        ):
            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                line_lower = line.lower()

                if any(
                    pattern in line_lower
                    for pattern in patterns
                ):
                    hits.append(
                        (
                            str(
                                path.relative_to(ROOT)
                            ),
                            line_number,
                            line.strip(),
                        )
                    )


print("\nLocal provenance / conversion-rule hits:")

for path, line_no, text in hits[:120]:
    print(
        f"{path}:{line_no}: {text}"
    )


# ============================================================
# 6. SCIENTIFIC STATUS
# ============================================================

has_ready_co2e_metric = any(
    "co2e" in str(x).lower()
    for x in d[
        "metric_identity"
    ].unique()
)

has_us_load_weighted = any(
    "US_LOAD_WEIGHTED"
    == str(x)
    for x in d[
        "region"
    ].unique()
)


print("\nScientific readiness:")

print(
    "ready-made CO2e metric:",
    has_ready_co2e_metric,
)

print(
    "US_LOAD_WEIGHTED region:",
    has_us_load_weighted,
)


print("\n" + "=" * 78)

print(
    "P16R-D4E1A2 PASS — LRMER COMPONENT CONTRACT AUDITED"
)

print(
    "NO GWP FACTOR INVENTED"
)

print(
    "NO REGIONAL AVERAGE INVENTED"
)

print(
    "NO LRMER DELTAG CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)