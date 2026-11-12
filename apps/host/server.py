#!/usr/bin/env python3
"""BIOScope local API; mock adapters never claim hardware/simulator evidence."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, shutil, subprocess, time, uuid
import re
from bio_sim import run_experiment, available as biosim_available
from device_discovery import discover

ROOT=Path(__file__).resolve().parents[2]; RUNS=ROOT/'artifacts'/'runs'
CATALOG=[
 {"id":"bio-smoke","title":"BIO-sim smoke test","category":"Simulation","description":"Run official no-firmware smoke config and validate cfginfo register plus FST output.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Verilator"],"expected":"cfginfo 0x10000408 PASS and genuine FST","available":biosim_available()},
 {"id":"register-inspection","title":"BIO configuration register inspection","category":"Analysis","description":"Run official no-firmware smoke self-check of sfr_cfginfo at offset 0x04.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Verilator"],"expected":"0x10000408 register read and captured FST","available":biosim_available('register-inspection')},
 {"id":"blink","title":"BIO GPIO blink","category":"I/O","description":"Upstream C blink firmware toggles and monitors GPIO 21 in the BIO simulator.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Zig 0.15.2"],"expected":"GPIO 21 transitions and FST waveform","available":biosim_available('blink')},
 {"id":"mock-loopback","title":"Host pipeline check","category":"Diagnostics","description":"Exercise run orchestration, logs, metadata, and artifact indexing without hardware.","modes":["MOCK"],"requirements":[],"expected":"Explicit mock result; placeholder trace only","available":True},]

def devices():
    """Return exact-profile matches from sysfs/by-id without opening serial."""
    return discover()

def execute(config):
    if not isinstance(config,dict) or set(config)-{'experiment_id','mode','timeout','mock_failure','omit_artifact'}: raise ValueError('malformed configuration')
    eid=config.get('experiment_id','mock-loopback'); exp=next((e for e in CATALOG if e['id']==eid),None)
    if not exp: raise ValueError('unknown experiment')
    mode=config.get('mode','MOCK')
    if mode not in exp['modes']: raise ValueError('execution mode is not supported by this experiment')
    if mode=='SIMULATION' and eid not in ('bio-smoke','register-inspection','blink'): raise ValueError('no verified simulation adapter for this experiment')
    if mode not in ('MOCK','SIMULATION'): raise ValueError('hardware mode is safety locked')
    if config.get('timeout'): raise TimeoutError('mock run timed out')
    rid=str(uuid.uuid4()); out=RUNS/rid; out.mkdir(parents=True)
    if mode=='SIMULATION':
        result=run_experiment(eid,out)
        stdout=result['stdout']; stderr=result['stderr']; code=result['exit_code']; started=result['started_at']; artifacts=result['artifacts']
        evidence=result['evidence']; state='COMPLETED' if evidence=='SIMULATED' else 'FAILED'
    else:
        started=time.time(); code=1 if config.get('mock_failure') else 0
        stdout=f"BIOSCOPE MOCK ADAPTER | experiment={eid}\nNo BIO-sim or hardware process executed.\n"+("Mock pipeline completed.\n" if not code else "Mock failure injected.\n")
        stderr='Simulated adapter failure (test fixture).\n' if code else ''
        artifacts=[]; evidence='MOCK ONLY — not BIO-sim or hardware evidence'; state='FAILED' if code else 'COMPLETED'
        if not code and not config.get('omit_artifact'):
            f=out/'mock-waveform-placeholder.fst'; f.write_text('BIOSCOPE MOCK PLACEHOLDER — not an FST waveform.\n')
            artifacts.append({"name":f.name,"path":str(f.relative_to(ROOT)),"type":"waveform-placeholder","verified":False,"size_bytes":f.stat().st_size})
    (out/'stdout.log').write_text(stdout); (out/'stderr.log').write_text(stderr)
    manifest={"run_id":rid,"experiment_id":eid,"experiment_title":exp['title'],"mode":mode,"adapter":"official-bio-sim" if mode=='SIMULATION' else "mock","state":state,"started_at":started,"finished_at":time.time(),"duration_seconds":round(time.time()-started,4),"exit_code":code,"stdout_path":str((out/'stdout.log').relative_to(ROOT)),"stderr_path":str((out/'stderr.log').relative_to(ROOT)),"stdout":stdout,"stderr":stderr,"artifacts":artifacts,"evidence":evidence}
    if mode=='SIMULATION': manifest.update({k:result[k] for k in ('validation','configuration','source_revision','tool_versions')})
    if mode=='SIMULATION':
        transitions=re.findall(r"\[mon\].*?(gpio_(?:out|dir)\[\d+\]): ([01]) -> ([01])",stdout)
        manifest['observed_signals']={}
        for signal,old,new in transitions: manifest['observed_signals'].setdefault(signal,[]).append({'from':int(old),'to':int(new)})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); return manifest

def history():
    return sorted((json.loads(p.read_text()) for p in RUNS.glob('*/manifest.json')),key=lambda x:x['started_at'],reverse=True) if RUNS.exists() else []
def health():
    return {"ok":True,"service":"BIOScope host","simulator":{"available":biosim_available(),"version":subprocess.run(['verilator','--version'],capture_output=True,text=True).stdout.strip() if shutil.which('verilator') else None,"bio_sim":"ready" if biosim_available() else "not acquired"}}

def launch_waveform(run_id):
    if not re.fullmatch(r'[a-f0-9-]{36}',run_id): raise ValueError('invalid run id')
    viewer=shutil.which('gtkwave')
    if not viewer: raise FileNotFoundError('GTKWave is not installed or not on PATH')
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')): raise EnvironmentError('No graphical display session is available to this host process')
    manifest_path=RUNS/run_id/'manifest.json'
    if not manifest_path.is_file(): raise FileNotFoundError('run not found')
    manifest=json.loads(manifest_path.read_text())
    fst=next((a for a in manifest.get('artifacts',[]) if a.get('type')=='fst-waveform' and a.get('verified') is True),None)
    if not fst: raise ValueError('run has no verified FST waveform')
    target=(ROOT/fst['path']).resolve()
    if target.parent!=(RUNS/run_id).resolve() or not target.is_file(): raise ValueError('waveform artifact is missing or outside its run directory')
    proc=subprocess.Popen([viewer,str(target)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return {'launched':True,'pid':proc.pid,'path':str(target.relative_to(ROOT))}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,status,obj):
        b=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.end_headers()
    def do_GET(self):
        routes={'/api/health':health,'/api/devices':devices,'/api/experiments':lambda:CATALOG,'/api/runs':history}
        if self.path in routes: return self.respond(200,routes[self.path]())
        if self.path.startswith('/api/runs/'):
            parts=self.path.strip('/').split('/')
            if len(parts)==5 and parts[3]=='artifacts':
                rid,name=parts[2],parts[4]; target=(RUNS/rid/name).resolve()
                if target.parent== (RUNS/rid).resolve() and target.is_file():
                    b=target.read_bytes(); self.send_response(200); self.send_header('Content-Type','application/octet-stream'); self.send_header('Content-Length',str(len(b))); self.send_header('Content-Disposition',f'attachment; filename="{target.name}"'); self.end_headers(); self.wfile.write(b); return
                return self.respond(404,{"error":"artifact not found"})
            rid=self.path.split('/')[-1]; p=RUNS/rid/'manifest.json'
            return self.respond(200,json.loads(p.read_text())) if p.exists() and p.parent.parent==RUNS else self.respond(404,{"error":"run not found"})
        if self.path=='/':
            built=ROOT/'apps/dashboard/dist/index.html'
            b=(built if built.exists() else ROOT/'apps/dashboard/index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if self.path.startswith('/assets/'):
            target=(ROOT/'apps/dashboard/dist'/self.path.lstrip('/')).resolve()
            if target.parent == (ROOT/'apps/dashboard/dist/assets').resolve() and target.is_file():
                b=target.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/css' if target.suffix=='.css' else 'text/javascript'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.respond(404,{"error":"not found"})
    def do_POST(self):
        m=re.fullmatch(r'/api/runs/([a-f0-9-]{36})/waveform/open',self.path)
        if m:
            try: return self.respond(200,launch_waveform(m.group(1)))
            except FileNotFoundError as e: return self.respond(404,{'error':str(e)})
            except EnvironmentError as e: return self.respond(503,{'error':str(e)})
            except ValueError as e: return self.respond(400,{'error':str(e)})
        if self.path!='/api/runs': return self.respond(404,{"error":"not found"})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>16384: return self.respond(413,{"error":"request too large"})
            result=execute(json.loads(self.rfile.read(n))); self.respond(200,result)
        except json.JSONDecodeError: self.respond(400,{"error":"malformed JSON"})
        except TimeoutError as e: self.respond(408,{"error":str(e)})
        except ValueError as e: self.respond(400,{"error":str(e)})

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int,default=8765); a=ap.parse_args()
    print(f'BIOScope host API listening at http://{a.host}:{a.port} (MOCK only)'); ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
