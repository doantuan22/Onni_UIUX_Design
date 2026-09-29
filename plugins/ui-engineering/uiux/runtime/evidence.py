"""Evidence validators (internal): runtime session evidence and accessibility scan evidence; no pixel or axe execution.

CLIs: python scripts/validate_runtime_evidence.py <session-dir>, python scripts/validate_accessibility_evidence.py <dir>."""
from __future__ import annotations

import json, sys
from pathlib import Path

from uiux.core import resources

ROOT=resources.get_package_root()
VIEWPORTS=json.loads(resources.get_viewports_path().read_text(encoding="utf-8"))
VIEWPORT_ALIASES={"desktop_1440": {"width": 1440, "height": 900}, "tablet_768": {"width": 768, "height": 1024},
                  "mobile_375": {"width": 375, "height": 812}}
STATUSES={"COMPLETED","PARTIAL","FAILED","BLOCKED"}

def load(path: Path) -> dict:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise ValueError(f"invalid JSON {path.name}: {e}")

def validate_runtime_directory(directory: str | Path) -> dict:
    """Validate an existing runtime evidence directory using the CLI's canonical rules."""
    root=Path(directory).resolve(); errors=[]
    try: manifest,report=load(root/"manifest.json"),load(root/"execution-report.json")
    except ValueError as e: return {"status":"INVALID","errors":[str(e)],"captures":0}
    for name,data in (("manifest",manifest),("report",report)):
        if data.get("schema_version")!=1: errors.append(f"{name} schema_version must be 1")
        if data.get("status") not in STATUSES: errors.append(f"{name} invalid status")
    if manifest.get("session_id")!=report.get("session_id"): errors.append("session IDs differ")
    if manifest.get("status")!=report.get("status"): errors.append("manifest/report statuses differ")
    seen=set(); captured=0
    for item in manifest.get("captures",[]):
        ident=item.get("id")
        if not ident or ident in seen: errors.append(f"duplicate/invalid capture id: {ident}")
        seen.add(ident)
        viewport=item.get("viewport"); expected=VIEWPORTS.get(viewport) or VIEWPORT_ALIASES.get(viewport)
        if not expected or item.get("width")!=expected["width"] or item.get("height")!=expected["height"]: errors.append(f"invalid viewport metadata: {ident}")
        if item.get("status")=="CAPTURED":
            captured+=1; file=item.get("file"); path=(root/file).resolve() if isinstance(file,str) else root
            try: path.relative_to(root)
            except ValueError: errors.append(f"capture path escapes session: {ident}"); continue
            if not path.is_file(): errors.append(f"capture file missing: {ident}")
    if report.get("captures_completed")!=captured: errors.append("captures_completed does not match manifest")
    expected_total=report.get("captures_expected",0)
    if manifest.get("status")=="COMPLETED" and captured!=expected_total: errors.append("completed session has incomplete captures")
    if manifest.get("status")=="PARTIAL" and not (0<captured<expected_total): errors.append("partial session capture counts invalid")
    return {"status":"VALID" if not errors else "INVALID","session_id":manifest.get("session_id"),
            "captures":captured,"errors":errors,"manifest":manifest}

def validate_accessibility_directory(directory: str | Path, *, session_id: str | None = None) -> dict:
    """Validate the scanner's canonical accessibility manifest and return its measured scans."""
    root = Path(directory).resolve()
    errors: list[str] = []
    try:
        manifest = load(root / "accessibility-manifest.json")
    except ValueError as exc:
        return {"status": "INVALID", "errors": [str(exc)], "scans": []}
    if manifest.get("schema_version") != 1:
        errors.append("accessibility manifest schema_version must be 1")
    if session_id and manifest.get("session_id") != session_id:
        errors.append("accessibility and runtime session IDs differ")
    scans = manifest.get("scans")
    if not isinstance(scans, list):
        return {"status": "INVALID", "errors": errors + ["scans must be a list"], "scans": []}
    seen: set[str] = set()
    measured: list[dict] = []
    for scan in scans:
        if not isinstance(scan, dict):
            errors.append("scan entry must be an object")
            continue
        ident = scan.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            errors.append("duplicate or invalid scan id")
            continue
        seen.add(ident)
        viewport = scan.get("viewport")
        expected = VIEWPORTS.get(viewport) or VIEWPORT_ALIASES.get(viewport)
        if not expected or scan.get("width") != expected["width"] or scan.get("height") != expected["height"]:
            errors.append(f"invalid accessibility viewport metadata: {ident}")
            continue
        if scan.get("status") != "SCANNED":
            errors.append(f"accessibility scan did not complete: {ident}")
            continue
        filename = scan.get("file")
        path = (root / filename).resolve() if isinstance(filename, str) else root
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"accessibility scan path escapes session: {ident}")
            continue
        if not path.is_file():
            errors.append(f"accessibility scan file missing: {ident}")
            continue
        try:
            data = load(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        results = data.get("results")
        violations = results.get("violations") if isinstance(results, dict) else None
        if data.get("schema_version") != 1 or not isinstance(violations, list) or scan.get("violations") != len(violations):
            errors.append(f"accessibility scan content/count invalid: {ident}")
            continue
        measured.append({"route": scan.get("route", "/"), "viewport": viewport,
            "status": "SCANNED", "violations": violations, "evidence_ref": f"accessibility:{ident}"})
    if manifest.get("status") != "COMPLETED":
        errors.append("accessibility manifest status is not COMPLETED")
    return {"status": "VALID" if not errors and scans and len(measured) == len(scans) else "INVALID",
        "session_id": manifest.get("session_id"), "scans": measured, "errors": errors}

def main_runtime() -> int:
    if len(sys.argv)!=2: print("usage: validate_runtime_evidence.py <session-dir>",file=sys.stderr); return 3
    root=Path(sys.argv[1]).resolve(); result=validate_runtime_directory(root)
    if result["status"]!="VALID": print("Evidence validation failed:\n"+"\n".join("- "+e for e in result["errors"])); return 1
    print(json.dumps({"status":"VALID","session_id":result.get("session_id"),"captures":result["captures"]}))
    return 0

def main_accessibility() -> int:
 """Validate an accessibility manifest and its scan files (moved from scripts/validate_accessibility_evidence.py)."""
 if len(sys.argv)!=2:return 3
 root=Path(sys.argv[1]);m=json.loads((root/'accessibility-manifest.json').read_text());errs=[];seen=set()
 if m.get('schema_version')!=1:errs+=['schema']
 for s in m.get('scans',[]):
  if not s.get('id') or s['id'] in seen:errs+=['duplicate scan']
  seen.add(s.get('id'));v=VIEWPORTS.get(s.get('viewport'),{})
  if s.get('width')!=v.get('width') or s.get('height')!=v.get('height'):errs+=['viewport']
  if s.get('status')=='SCANNED':
   p=root/s.get('file','');
   if not p.is_file():errs+=['missing scan file'];continue
   d=json.loads(p.read_text());r=d.get('results',{})
   if d.get('schema_version')!=1 or not isinstance(r.get('violations',[]),list) or s.get('violations')!=len(r.get('violations',[])):errs+=['count/schema']
 if errs:print('Accessibility evidence invalid: '+', '.join(errs));return 1
 print(json.dumps({'status':'VALID','scans':len(m.get('scans',[]))}));return 0

main = main_runtime  # backward-compatible name

if __name__=="__main__": raise SystemExit(main_runtime())
