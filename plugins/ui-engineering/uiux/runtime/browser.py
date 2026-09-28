"""Playwright runtime orchestrator. Uses only project-local Playwright; never installs tools.

Public entry: ``execute(raw, project, dry_run=False, allow_start=False)`` (exposed as ``uiux.api.run_runtime``).
The CLI ``python scripts/run_browser_execution.py`` keeps its original arguments, output and exit codes.
"""
from __future__ import annotations

import argparse, json, os, re, signal, subprocess, sys, time, urllib.request
from pathlib import Path

from uiux.core import config, resources
from uiux.runtime import capabilities
from uiux.runtime.probes import LAYOUT_PROBE_JS, PROBE_JS

ROOT = resources.get_package_root()
VIEWPORTS = json.loads(resources.get_viewports_path().read_text(encoding="utf-8"))
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

HELPER = r'''const fs=require('fs'),path=require('path');const PROBE=__PROBE__;const LAYOUT=__LAYOUT__;
const i=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let pw;
try{pw=require('playwright')}catch(e){try{pw=require('@playwright/test')}catch(e2){console.error('PLAYWRIGHT_IMPORT_FAILURE');process.exit(2)}}
(async()=>{const out={captures:[],errors:[],console:[]};let browser;
 try{browser=await pw[i.browser].launch({headless:true});
  for(const r of i.routes) for(const v of i.viewports){let c,p,sfx=i.reduced_motion==='reduce'?'__reduced-motion':'',id=`${r.page_id}:${v.id}:${i.iteration}${i.reduced_motion==='reduce'?':reduced-motion':''}`,file=`pages/${r.safe_id}__${v.id}__iter-${String(i.iteration).padStart(2,'0')}${sfx}.png`;
   try{const co={viewport:{width:v.width,height:v.height}};if(i.reduced_motion)co.reducedMotion=i.reduced_motion;c=await browser.newContext(co);p=await c.newPage();
    if(i.collect_console){p.on('console',m=>{if(m.type()==='error')out.console.push({page_id:r.page_id,viewport:v.id,message:m.text()})});p.on('pageerror',e=>out.console.push({page_id:r.page_id,viewport:v.id,message:String(e.message||e)}))}
    await p.goto(new URL(r.route,i.base_url).href,{waitUntil:'domcontentloaded',timeout:i.navigation_timeout_ms});
    const basic=await p.evaluate(()=>({body:!!document.body,text:(document.body?.innerText||'').trim().length,root:!!document.querySelector('main,[role="main"],#root,#app')}));
    if(!basic.body||!basic.text)throw Object.assign(new Error('blank render'),{code:'BLANK_RENDER'});
    if(r.expected_selector && !await p.locator(r.expected_selector).count())throw Object.assign(new Error('expected selector missing'),{code:'NAVIGATION_FAILURE'});
    if(r.expected_text && !await p.getByText(r.expected_text,{exact:false}).count())throw Object.assign(new Error('expected text missing'),{code:'NAVIGATION_FAILURE'});
    await p.screenshot({path:path.join(i.output_dir,file),fullPage:i.full_page,timeout:i.screenshot_timeout_ms});
    let probe;if(i.motion_probe){try{probe=await p.evaluate(PROBE,i.probe_wait_ms)}catch(e){probe={error:String(e.message||e).slice(0,200)}}}
    let layout;if(i.layout_probe){try{layout=await p.evaluate(LAYOUT)}catch(e){layout={error:String(e.message||e).slice(0,200)}}}
    out.captures.push({id,page_id:r.page_id,route:r.route,viewport:v.id,width:v.width,height:v.height,iteration:i.iteration,status:'CAPTURED',file,basic_render:basic,...(i.reduced_motion?{reduced_motion:i.reduced_motion}:{}),...(probe?{motion_probe:probe}:{}),...(layout?{layout_probe:layout}:{})});
   }catch(e){out.errors.push({code:e.code||'SCREENSHOT_FAILURE',page_id:r.page_id,route:r.route,viewport:v.id,message:String(e.message||e).slice(0,500),recoverable:true});out.captures.push({id,page_id:r.page_id,route:r.route,viewport:v.id,width:v.width,height:v.height,iteration:i.iteration,status:'SCREENSHOT_FAILURE',file:null})}
   finally{if(c)await c.close().catch(()=>{})}
  }
 }catch(e){out.errors.push({code:'BROWSER_LAUNCH_FAILURE',page_id:null,route:null,viewport:null,message:String(e.message||e).slice(0,500),recoverable:false})}
 finally{if(browser)await browser.close().catch(()=>{});console.log(JSON.stringify(out))}
})();'''.replace("__PROBE__", PROBE_JS).replace("__LAYOUT__", LAYOUT_PROBE_JS)
REDUCED_MOTION = {"reduce", "no-preference"}

def atomic(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)

def err(code: str, message: str, **extra: object) -> dict[str, object]:
    return {"code": code, "page_id": extra.get("page_id"), "route": extra.get("route"), "viewport": extra.get("viewport"), "message": message[:500], "recoverable": bool(extra.get("recoverable", False))}

def inside(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    try: resolved.relative_to(root.resolve())
    except ValueError: raise ValueError("output_dir must remain inside project root")
    return resolved

def request(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response: return response.status < 500
    except Exception: return False

def ready(url: str, timeout_ms: int) -> bool:
    end = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < end:
        if request(url): return True
        time.sleep(.5)
    return False

def detector(project: Path, browser: str | None = None) -> dict[str, object]:
    """Read-only capability report (in-process; formerly a subprocess call to scripts/detect_capabilities.py)."""
    return capabilities.detect(project, browser=browser or config.get()["browser"]["default_browser"])

def blocking_reason(cap: dict[str, object]) -> tuple[str, str] | None:
    """(error code, message) when the runtime cannot run; None when Playwright is usable."""
    node = cap["runtime"]["node"]["status"] == "AVAILABLE"
    state = cap["playwright"]["runtime_state"]["state"]
    if not node or state in (capabilities.NOT_DECLARED, capabilities.DECLARED_NOT_INSTALLED):
        return "PLAYWRIGHT_IMPORT_FAILURE", f"project-local Playwright or Node unavailable (runtime state {state}, node {'available' if node else 'missing'})"
    if state == capabilities.PACKAGE_AVAILABLE_BROWSER_MISSING and config.get()["browser"]["preflight_browser_check"]:
        return "PLAYWRIGHT_BROWSER_UNAVAILABLE", "Playwright package present but no browser build in the local cache; the runner never downloads browsers"
    return None

def validate(raw: object, project: Path) -> tuple[dict[str, object], Path]:
    if not isinstance(raw, dict): raise ValueError("input must be an object")
    sid, base, routes, names, iteration = raw.get("session_id"), raw.get("base_url"), raw.get("routes"), raw.get("viewports"), raw.get("iteration", 1)
    if not isinstance(sid, str) or not SESSION_RE.fullmatch(sid): raise ValueError("invalid session_id")
    if not isinstance(base, str) or not re.match(r"^https?://[^/]+", base): raise ValueError("invalid base_url")
    if not isinstance(routes, list) or not routes: raise ValueError("routes must be non-empty")
    if not isinstance(names, list) or not names or any(v not in VIEWPORTS for v in names): raise ValueError("unknown viewport ID")
    if not isinstance(iteration, int) or iteration < 1: raise ValueError("iteration must be >= 1")
    for route in routes:
        if not isinstance(route, dict) or not isinstance(route.get("page_id"), str) or not isinstance(route.get("route"), str) or not route["route"].startswith("/"):
            raise ValueError("each route needs page_id and absolute route")
    if isinstance(raw.get("options"), dict): validate_options(raw["options"])  # non-object options stay ignored, as before
    output = Path(raw.get("output_dir", project / config.get()["browser"]["evidence_dir"]))
    output = inside(project, output if output.is_absolute() else project / output)
    return raw, output / sid

def validate_options(opts: object) -> dict[str, object]:
    if not isinstance(opts, dict): raise ValueError("options must be an object")
    reduced = opts.get("reduced_motion")
    if reduced is not None and reduced not in REDUCED_MOTION: raise ValueError("options.reduced_motion must be reduce or no-preference")
    if "motion_probe" in opts and not isinstance(opts["motion_probe"], bool): raise ValueError("options.motion_probe must be boolean")
    if "layout_probe" in opts and not isinstance(opts["layout_probe"], bool): raise ValueError("options.layout_probe must be boolean")
    wait = opts.get("probe_wait_ms", config.get()["browser"]["probe_wait_ms"])
    if not isinstance(wait, int) or not 0 <= wait <= 10000: raise ValueError("options.probe_wait_ms must be 0..10000")
    return opts

def stop(process: subprocess.Popen[str] | None, timeout_ms: int) -> bool:
    if not process or process.poll() is not None: return True
    process.terminate()
    try: process.wait(timeout=timeout_ms / 1000); return True
    except subprocess.TimeoutExpired:
        process.kill(); process.wait(timeout=timeout_ms / 1000); return False

def execute(raw: object, project: Path, dry_run: bool = False, allow_start: bool = False) -> tuple[int, dict[str, object]]:
    """Validate, preflight and (unless dry_run) capture. Returns (exit code, summary) exactly as the CLI prints them."""
    project = Path(project).resolve()
    try: raw, session=validate(raw, project)
    except ValueError as exc:
        return 3, {"status":"INVALID_INPUT","error":str(exc)}
    browser_cfg=config.get()["browser"]; opts=raw.get("options",{}) if isinstance(raw.get("options",{}),dict) else {}
    allow_start = allow_start or bool(browser_cfg["allow_start"])
    cap=detector(project, opts.get("browser", browser_cfg["default_browser"])); blocked=blocking_reason(cap)
    plan={"status":"DRY_RUN","strategy":"playwright" if not blocked else "BLOCKED","session_id":raw["session_id"],"output_dir":str(session),"routes":[r["route"] for r in raw["routes"]],"viewports":raw["viewports"],"runtime_state":cap["playwright"]["runtime_state"]["state"],"capability":cap["playwright"]}
    if dry_run: return 0, plan
    session.mkdir(parents=True,exist_ok=True); (session/"pages").mkdir(exist_ok=True); (session/"logs").mkdir(exist_ok=True)
    report={"schema_version":1,"session_id":raw["session_id"],"strategy":"playwright","base_url":raw["base_url"],"iteration":raw["iteration"],"status":"BLOCKED","routes_total":len(raw["routes"]),"captures_expected":len(raw["routes"])*len(raw["viewports"]),"captures_completed":0,"errors":[],"server_owned":False,"readiness":None,"runtime_state":cap["playwright"]["runtime_state"]["state"],"cleanup":{"browser_closed":False,"server_stopped":False,"temporary_files_removed":False}}
    if blocked:
        report["errors"].append(err(*blocked)); atomic(session/"execution-report.json",report); atomic(session/"manifest.json",{**report,"captures":[]}); return 2, {"status":"BLOCKED","report":str(session/"execution-report.json")}
    process=None; captures=[]; helper=None; payload=None
    try:
        if not request(raw["base_url"]):
            start=raw.get("start",{}); command=start.get("command") if isinstance(start,dict) else None
            if not allow_start or not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command): raise RuntimeError("SERVER_START_FAILURE: no explicit --allow-start argv command")
            process=subprocess.Popen(command,cwd=project,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,text=True); report["server_owned"]=True
        timeout=int(raw.get("readiness",{}).get("timeout_ms",60000)); report["readiness"]={"url":raw["base_url"],"timeout_ms":timeout}
        if not ready(raw["base_url"],timeout): raise RuntimeError("READINESS_TIMEOUT")
        helper=session/"runtime-helper.cjs"; payload=session/"runtime-input.json"; helper.write_text(HELPER,encoding="utf-8")
        payload_data={"base_url":raw["base_url"],"routes":[{**r,"safe_id":re.sub(r"[^A-Za-z0-9_-]","-",r["page_id"])} for r in raw["routes"]],"viewports":[{"id":v,**VIEWPORTS[v]} for v in raw["viewports"]],"iteration":raw["iteration"],"output_dir":str(session),"browser":opts.get("browser",browser_cfg["default_browser"]),"collect_console":bool(opts.get("collect_console",False)),"full_page":bool(opts.get("full_page",True)),"navigation_timeout_ms":int(opts.get("navigation_timeout_ms",browser_cfg["navigation_timeout_ms"])),"screenshot_timeout_ms":int(opts.get("screenshot_timeout_ms",browser_cfg["screenshot_timeout_ms"])),"reduced_motion":opts.get("reduced_motion"),"motion_probe":bool(opts.get("motion_probe",config.get()["feature_flags"]["motion_probe"])),"probe_wait_ms":int(opts.get("probe_wait_ms",browser_cfg["probe_wait_ms"])),"layout_probe":bool(opts.get("layout_probe",False))}
        atomic(payload,payload_data); run=subprocess.run(["node",str(helper),str(payload)],cwd=project,capture_output=True,text=True,timeout=max(60,payload_data["navigation_timeout_ms"]//1000*len(raw["routes"])*len(raw["viewports"])+30))
        result=json.loads(run.stdout) if run.stdout.strip() else {"captures":[],"errors":[err("BROWSER_LAUNCH_FAILURE",run.stderr or "helper produced no output")]}
        report["errors"].extend(result.get("errors",[])); captures=result.get("captures",[]); report["captures_completed"]=sum(c.get("status")=="CAPTURED" for c in captures)
        if result.get("console"): atomic(session/"logs/console.json",{"schema_version":1,"events":result["console"]})
        report["status"]="COMPLETED" if report["captures_completed"]==report["captures_expected"] else "PARTIAL" if report["captures_completed"] else "FAILED"
        if report["status"]=="PARTIAL": report["errors"].append(err("PARTIAL_EXECUTION","some requested captures failed",recoverable=True))
        manifest={"schema_version":1,"session_id":raw["session_id"],"strategy":"playwright","base_url":raw["base_url"],"iteration":raw["iteration"],"status":report["status"],"captures":captures}
        atomic(session/"manifest.json",manifest)
    except Exception as exc:
        code=str(exc).split(":",1)[0] if re.match(r"^[A-Z_]+",str(exc)) else "RUNTIME_RUNNER_FAILURE"; report["errors"].append(err(code,str(exc))); report["status"]="PARTIAL" if captures else ("FAILED" if code not in {"SERVER_START_FAILURE","READINESS_TIMEOUT"} else "BLOCKED"); atomic(session/"manifest.json",{**report,"captures":captures})
    finally:
        removed=True
        for temporary in (helper,payload):
            if temporary:
                try: temporary.unlink(missing_ok=True)
                except OSError: removed=False
        report["cleanup"]["temporary_files_removed"]=removed
        report["cleanup"]["server_stopped"]=stop(process,int(raw.get("cleanup_timeout_ms",5000))) if report["server_owned"] else False; report["cleanup"]["browser_closed"]=True; atomic(session/"execution-report.json",report)
    return {"COMPLETED":0,"PARTIAL":4,"BLOCKED":2}.get(report["status"],1), {"status":report["status"],"report":str(session/"execution-report.json"),"manifest":str(session/"manifest.json")}

def main() -> int:
    ap=argparse.ArgumentParser(description="Run existing project-local Playwright visual capture")
    ap.add_argument("--input", required=True); ap.add_argument("--project", default="."); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--allow-start", action="store_true"); ap.add_argument("--debug", action="store_true")
    args=ap.parse_args(); project=Path(args.project).resolve()
    try: raw=json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"INVALID_INPUT","error":str(exc)})); return 3
    code, summary = execute(raw, project, dry_run=args.dry_run, allow_start=args.allow_start)
    print(json.dumps(summary)); return code

if __name__=="__main__":
    raise SystemExit(main())
