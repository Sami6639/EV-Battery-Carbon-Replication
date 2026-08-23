from pathlib import Path
import io,json,zipfile
import pandas as pd
import pyarrow.parquet as pq
import yaml

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw"
OUT=ROOT/"data/processed"

def test_cambium_primary_metric_identity_and_lossless_unit_conversion():
    out=pd.read_parquet(OUT/"cambium_2024_average_grid_ci.parquet")
    assert set(out.metric_identity)=={"aer_load_co2e"}
    assert set(out.dataset_version)=={2024}
    assert set(out.scenario)=={"MidCase","LowRECost","HighRECost"}
    assert out.region.nunique()==18
    assert set(out.calendar_year)=={2025,2030,2035,2040,2045,2050}
    assert not out.metric_identity.str.contains("lrmer",case=False).any()
    raw=RAW/"SRC_CAMBIUM_2024/ScenarioViewer_Cambium2024_Annual_GEA_file_69141.zip"
    with zipfile.ZipFile(raw) as z:
        source=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),skiprows=5,usecols=["scenario","gea","t","aer_load_co2e"])
    source=source[source.scenario.isin(out.scenario)].sort_values(["scenario","gea","t"]).reset_index(drop=True)
    got=out.sort_values(["scenario","region","calendar_year"]).reset_index(drop=True)
    assert source.aer_load_co2e.equals(got.grid_ci_gco2e_per_kwh)

def test_primary_average_and_lrmer_sensitivity_are_separate():
    primary=pd.read_parquet(OUT/"cambium_2024_average_grid_ci.parquet",columns=["source_id","metric_identity"])
    sensitivity=pd.read_parquet(OUT/"cambium_lrmer_2023_components.parquet",columns=["source_id","dataset_version","metric_identity"])
    assert set(primary.source_id)=={"SRC_CAMBIUM_2024"}
    assert set(sensitivity.source_id)=={"SRC_CAMBIUM_LRMER_2023"}
    assert set(sensitivity.dataset_version)=={2023}
    assert not set(primary.metric_identity)&set(sensitivity.metric_identity)

def test_all_three_hppc_temperatures_and_lineage_are_present():
    path=OUT/"tum_id3_hppc_observations.parquet"
    pf=pq.ParquetFile(path)
    assert pf.metadata.num_rows>0
    table=pq.read_table(path,columns=["source_id","source_filename","test_temperature_c"])
    d=table.to_pandas()
    assert set(d.source_id)=={"SRC_TUM_ID3"}
    assert set(d.test_temperature_c)=={0.0,20.0,40.0}
    assert d.source_filename.str.endswith(".csv").all()
    meta=yaml.safe_load((OUT/"metadata/tum_id3_hppc_observations.yaml").read_text(encoding="utf-8"))
    assert len(meta["input_raw_files"])==3
    assert all(p.endswith(".csv") for p in meta["input_raw_files"])
    core=pq.read_table(path,columns=["time_s","voltage_v","current_a"])
    assert all(core.column(name).null_count==0 for name in core.column_names)

def test_hppc_has_observed_channels_but_no_scientific_derivations():
    names=set(pq.ParquetFile(OUT/"tum_id3_hppc_observations.parquet").schema.names)
    assert {"source_row","protocol_line","time_s","voltage_v","current_a","charge_ah","energy_wh"}<=names
    banned={"fitted_resistance","r_over_r0","degradation_penalty","pack_loss","vehicle_energy_penalty","soc_fraction"}
    assert not names&banned

def test_p11r_raw_pre_recovery_files_remain_unchanged():
    import hashlib
    baseline=json.loads((ROOT/"data/metadata/P11R_PRE_RECOVERY_RAW_SHA256.json").read_text(encoding="utf-8"))
    for rel,expected in baseline.items():
        h=hashlib.sha256()
        with (ROOT/rel).open("rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
        assert h.hexdigest()==expected
