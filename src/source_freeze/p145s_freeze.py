"""Create the P14.5S byte-level source-artifact freeze only."""
from __future__ import annotations
import csv, hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "metadata" / "P145S_SOURCE_ARTIFACT_FREEZE.csv"
SUMMARY = ROOT / "data" / "metadata" / "P145S_SOURCE_FREEZE_SUMMARY.json"
MANIFEST = ROOT / "data" / "metadata" / "SOURCE_MANIFEST.csv"
RETRIEVAL_DATE = "2026-08-21"
PRE_MANIFEST_LINE_COUNT = 16
PRE_MANIFEST_SHA256 = "d2889702f49b0ece440f57915d84491908d6c8428f86d535a3695db7e79867a9"
SOURCES = {
"SRC_BLAST_LITE": ["BLAST-Lite v1.1.0 plus pinned official repository commit", "NOT_APPLICABLE_SOFTWARE; model-specific DOI in eligibility table", "https://github.com/NatLabRockies/BLAST-Lite", "v1.1.0-12-gb093495; b093495b47dc40dd96dba865d91f553619501e94", "BSD-3-Clause", "Multiple; NMC/NMC-like candidates audited", "Cell-level semi-empirical software models", "CANDIDATE_CAPACITY_BRIDGE_MODEL", "Deterministic real-world resistance trajectory; field ground truth; direct pack validation"],
"SRC_WU_2026": ["Wu et al. 2026, Nature Climate Change 16, 460-467", "10.1038/s41558-026-02579-z; software 10.5281/zenodo.17173892", "https://github.com/ASSET-Lab/EVBatteryClimateChange; https://zenodo.org/records/17173892", "25dd34bd04c1184c22746843c909fb426af741f1; Zenodo record 17173892", "CC BY 4.0", "Multiple commercial cell models", "Model application: cell model coupled to vehicle/climate simulation", "MODEL_APPLICATION_AND_EXPOSURE_ARCHITECTURE", "Project capacity calibration; field validation; exact project exposure history"],
"SRC_LIU_2025": ["Liu et al. 2025, Nature Communications 16, 1137", "10.1038/s41467-025-56485-7", "https://github.com/HoraceLiu1010/Multi-modal-SOH-estimation-framework", "56c1ef4dd0c5efe005368624e17a1c76a32b6c16", "MIT repository; CC BY-NC-ND 4.0 article/supplement", "NCM, exact subtype not disclosed", "Vehicle/fleet telemetry and field-derived SOH labels", "PRIMARY_FIELD_CAPACITY_VALIDATION", "BLAST fitting/tuning; fully reproducible ground truth; resistance trajectory"],
"SRC_DENG_2023": ["Deng et al. 2023, Applied Energy 339, 120954", "10.1016/j.apenergy.2023.120954", "https://github.com/BatICM/battery-charging-data-of-on-road-electric-vehicles", "36fef4bd99f626561e2d138a40ccff3d1f3ddfc2", "MIT", "CATL NCM", "Twenty vehicle-level battery-pack charging records", "OPEN_FIELD_CAPACITY_VALIDATION", "BLAST fitting/tuning; resistance trajectory; parked-state reconstruction"],
"SRC_QIUSHI_WANG_2023": ["Wang et al. 2023, Cell Reports Physical Science 4, 101720", "10.1016/j.xcrp.2023.101720", "Official Cell Press article and supplemental landing page", "Version of record, December 2023", "CC BY-NC-ND 4.0", "LFP/graphite (not project NMC)", "Fleet methodology; public supplement is not raw telemetry", "NON_EXECUTABLE_FIELD_METHOD_VALIDATION", "NMC validation; fitting; executable raw-data validation; resistance trajectory"]}
FIELDS = ["source_id", "bibliographic_identity", "doi", "official_repository", "exact_filename", "relative_path", "byte_size", "sha256", "version_tag_commit", "license", "retrieval_date", "chemistry", "measurement_level", "scientific_role", "prohibited_roles"]
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576), b""): h.update(chunk)
    return h.hexdigest()
def git_head(path):
    if not (path/".git").exists(): return None
    return subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],check=True,capture_output=True,text=True).stdout.strip()
def main():
    manifest_prefix = b"".join(MANIFEST.read_bytes().splitlines(keepends=True)[:PRE_MANIFEST_LINE_COUNT])
    if hashlib.sha256(manifest_prefix).hexdigest() != PRE_MANIFEST_SHA256:
        raise RuntimeError("Historical SOURCE_MANIFEST prefix changed; refusing to freeze sources.")
    rows=[]; per={}
    keys=["bibliographic_identity","doi","official_repository","version_tag_commit","license","chemistry","measurement_level","scientific_role","prohibited_roles"]
    for sid, values in SOURCES.items():
        meta=dict(zip(keys,values)); d=RAW/sid
        files=sorted(p for p in d.rglob("*") if p.is_file() and ".git" not in p.relative_to(d).parts) if d.exists() else []
        for p in files: rows.append({"source_id":sid,**meta,"exact_filename":p.name,"relative_path":p.relative_to(ROOT).as_posix(),"byte_size":p.stat().st_size,"sha256":sha256(p),"retrieval_date":RETRIEVAL_DATE})
        per[sid]={"artifact_count":len(files),"byte_total":sum(p.stat().st_size for p in files),"git_head":git_head(d),"acquisition_note":"All acquired artifacts inventoried; .git internals excluded." if files else "No local artifact acquired; no executable official raw-data artifact was available."}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    summary={"stage":"P14.5S","retrieval_date":RETRIEVAL_DATE,"source_count":len(SOURCES),"artifact_count":len(rows),"artifact_freeze_sha256":sha256(OUT),"source_manifest_pre_append_sha256":PRE_MANIFEST_SHA256,"source_manifest_pre_append_line_count":PRE_MANIFEST_LINE_COUNT,"per_source":per,"scientific_bridge_implemented":"NONE","lifecycle_ghg_calculated":"NONE"}
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__": main()