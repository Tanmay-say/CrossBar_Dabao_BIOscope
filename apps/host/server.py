#!/usr/bin/env python3
"""BIOScope local API; mock adapters never claim hardware/simulator evidence."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, shutil, subprocess, time, uuid
import re
import hashlib
from bio_sim import run_experiment, available as biosim_available
from device_discovery import discover
from dabao_hardware import capabilities as dabao_capabilities
from pulselink import PulseLinkStore, PulseLinkSerialService

ROOT=Path(__file__).resolve().parents[2]; RUNS=ROOT/'artifacts'/'runs'
CATALOG=[
 {"id":"bio-smoke","title":"BIO-sim smoke test","category":"Simulation","description":"Run official no-firmware smoke config and validate cfginfo register plus FST output.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Verilator"],"expected":"cfginfo 0x10000408 PASS and genuine FST","available":biosim_available()},
 {"id":"register-inspection","title":"BIO configuration register inspection","category":"Analysis","description":"Run official no-firmware smoke self-check of sfr_cfginfo at offset 0x04.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Verilator"],"expected":"0x10000408 register read and captured FST","available":biosim_available('register-inspection')},
 {"id":"blink","title":"BIO GPIO blink","category":"I/O","description":"Upstream C blink firmware toggles and monitors GPIO 21 in the BIO simulator.","modes":["SIMULATION","MOCK"],"requirements":["BIO-sim","Zig 0.15.2"],"expected":"GPIO 21 transitions and FST waveform","available":biosim_available('blink')},
 {"id":"dabao-fifo-probe","title":"Dabao BIO FIFO0 sentinel probe","category":"Physical BIO","description":"A 20-byte pin-free BIO program emits 0xB105C0DE. One approved physical Dabao run is recorded. The one-shot hardware path is consumed and locked; this catalog entry remains available in simulation.","modes":["SIMULATION","MOCK","HARDWARE"],"requirements":["Dabao with verified Xous BIO console","BIO-sim for simulation"],"expected":"FIFO0 sentinel 0xB105C0DE","available":True,"requires_manual_approval":True,"hardware_state":"HARDWARE_VERIFIED","hardware_evidence":"HARDWARE_VERIFIED","verified_run_id":"d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62"},
 {"id":"pulselink_signal_generator","title":"BIOscope PulseLink — Dabao signal to M5Stick","category":"Two-board hardware","description":"BIO1 generates ten low-speed pulses; Plus2 GPIO32 counts real rising edges and reports interrupt timestamps for an edge-derived VCD. Physical operation is approval-gated.","modes":["SIMULATION","HARDWARE"],"requirements":["Dabao Xous BIO console","Plus2 PulseLink firmware","verified 3.3 V wiring"],"expected":"10 rising/10 falling edges, approximately 1 Hz, safe LOW final state","available":biosim_available('pulselink_signal_generator'),"requires_manual_approval":True,"hardware_state":"PREPARED_NOT_EXECUTED"},
 {"id":"mock-loopback","title":"Host pipeline check","category":"Diagnostics","description":"Exercise run orchestration, logs, metadata, and artifact indexing without hardware.","modes":["MOCK"],"requirements":[],"expected":"Explicit mock result; placeholder trace only","available":True},]

PULSELINK_STORE=PulseLinkStore(capture_root=RUNS)
PULSELINK_SERVICE=None

def devices():
    """Return exact-profile matches from sysfs/by-id without opening serial."""
    return discover()

def execute(config):
    if not isinstance(config,dict) or set(config)-{'experiment_id','mode','timeout','mock_failure','omit_artifact'}: raise ValueError('malformed configuration')
    eid=config.get('experiment_id','mock-loopback'); exp=next((e for e in CATALOG if e['id']==eid),None)
    if not exp: raise ValueError('unknown experiment')
    mode=config.get('mode','MOCK')
    if mode not in exp['modes']: raise ValueError('execution mode is not supported by this experiment')
    if mode=='HARDWARE': raise PermissionError('physical execution is history-only; the one-shot probe is consumed and HTTP hardware writes are disabled')
    if mode=='SIMULATION' and eid not in ('bio-smoke','register-inspection','blink','dabao-fifo-probe','pulselink_signal_generator'): raise ValueError('no verified simulation adapter for this experiment')
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

def load_run_manifest(run_dir):
    """Load a run record, applying a checksum-bound metadata amendment in memory."""
    run_dir=Path(run_dir).resolve()
    if run_dir.parent != RUNS.resolve(): raise ValueError('invalid run directory')
    manifest_path=run_dir/'manifest.json'
    if not manifest_path.is_file(): raise FileNotFoundError('run not found')
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('mode')=='HARDWARE' and manifest.get('experiment_id')=='dabao-fifo-probe':
        run_id=run_dir.name
        amendment_path=ROOT/'docs/hardware-evidence'/f'{run_id}-amendment.json'
        if amendment_path.is_file():
            amendment=json.loads(amendment_path.read_text())
            digest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if amendment.get('run_id')==run_id and amendment.get('original_manifest_sha256')==digest:
                for key,value in amendment.get('corrected_fields',{}).items():
                    if key=='operation_sequence[2]' and len(manifest.get('operation_sequence',[]))>2:
                        manifest['operation_sequence'][2]=value
                manifest['metadata_amendment']={'path':str(amendment_path.relative_to(ROOT)),
                                                'reason':amendment.get('reason'),
                                                'original_manifest_sha256':digest}
        stdout_path=run_dir/'stdout.log'; stderr_path=run_dir/'stderr.log'
        manifest['stdout']=stdout_path.read_text(errors='replace') if stdout_path.is_file() else ''
        manifest['stderr']=stderr_path.read_text(errors='replace') if stderr_path.is_file() else ''
        amendment=manifest.get('metadata_amendment')
        integrity={}
        amendment_path=ROOT/'docs/hardware-evidence'/f'{run_id}-amendment.json'
        if amendment_path.is_file() and amendment:
            integrity=json.loads(amendment_path.read_text()).get('artifact_integrity',{})
        manifest['artifacts']=[
            {'name':'manifest.json','path':f'artifacts/runs/{run_id}/manifest.json','type':'run-manifest','verified':True,
             'size_bytes':manifest_path.stat().st_size,'sha256':integrity.get('manifest.json',{}).get('sha256')},
            {'name':'stdout.log','path':f'artifacts/runs/{run_id}/stdout.log','type':'hardware-console-log','verified':True,
             'size_bytes':stdout_path.stat().st_size if stdout_path.is_file() else 0,'sha256':integrity.get('stdout.log',{}).get('sha256')},
            {'name':'stderr.log','path':f'artifacts/runs/{run_id}/stderr.log','type':'hardware-error-log','verified':True,
             'size_bytes':stderr_path.stat().st_size if stderr_path.is_file() else 0,'sha256':integrity.get('stderr.log',{}).get('sha256')},
            {'name':'hardware-result.json','path':f'artifacts/runs/{run_id}/hardware-result.json','type':'hardware-result','verified':True,
             'size_bytes':(run_dir/'hardware-result.json').stat().st_size if (run_dir/'hardware-result.json').is_file() else 0,
             'sha256':integrity.get('hardware-result.json',{}).get('sha256')},
        ]
        if amendment_path.is_file() and amendment:
            raw=amendment_path.read_bytes()
            manifest['artifacts'].append({'name':'manifest-amendment.json',
                'path':str(amendment_path.relative_to(ROOT)),'type':'manifest-amendment','verified':True,
                'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    return manifest

def history():
    runs = (load_run_manifest(p.parent) for p in RUNS.glob('*/manifest.json')) if RUNS.exists() else ()
    return sorted(runs, key=lambda item: item.get('started_at', item.get('finished_at', 0)), reverse=True)
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

def launch_pulselink_waveform(run_id):
    if not re.fullmatch(r'[a-f0-9-]{36}',run_id): raise ValueError('invalid run id')
    viewer=shutil.which('gtkwave')
    if not viewer: raise FileNotFoundError('GTKWave is not installed or not on PATH')
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')): raise EnvironmentError('No graphical display session is available to this host process')
    manifest_path=RUNS/run_id/'manifest.json'
    if not manifest_path.is_file(): raise FileNotFoundError('PulseLink capture not found')
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('experiment_id')!='pulselink_signal_generator' or manifest.get('evidence')!='LIVE_HARDWARE':
        raise ValueError('run is not a genuine PulseLink hardware capture')
    trace=next((a for a in manifest.get('artifacts',[]) if a.get('type')=='vcd-waveform' and a.get('evidence')=='LIVE_HARDWARE'),None)
    if not trace: raise ValueError('capture has no verified hardware VCD')
    target=(ROOT/trace['path']).resolve()
    if target.parent!=(RUNS/run_id).resolve() or not target.is_file(): raise ValueError('capture artifact missing or outside its run')
    proc=subprocess.Popen([viewer,str(target)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return {'launched':True,'pid':proc.pid,'path':str(target.relative_to(ROOT)),'evidence':'LIVE_HARDWARE'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,status,obj):
        b=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.end_headers()
    def do_GET(self):
        routes={'/api/health':health,'/api/devices':devices,'/api/experiments':lambda:CATALOG,'/api/runs':history,
                '/api/pulselink':PULSELINK_STORE.snapshot,
                '/api/hardware/capabilities':lambda:dabao_capabilities(devices())}
        if self.path in routes: return self.respond(200,routes[self.path]())
        if self.path.startswith('/api/runs/'):
            parts=self.path.strip('/').split('/')
            if len(parts)==5 and parts[3]=='artifacts':
                rid,name=parts[2],parts[4]
                if not re.fullmatch(r'[a-f0-9-]{36}',rid): return self.respond(404,{"error":"artifact not found"})
                target=(ROOT/'docs/hardware-evidence'/f'{rid}-amendment.json').resolve() if name=='manifest-amendment.json' else (RUNS/rid/name).resolve()
                allowed=(target==(ROOT/'docs/hardware-evidence'/f'{rid}-amendment.json').resolve()) if name=='manifest-amendment.json' else (target.parent==(RUNS/rid).resolve())
                if allowed and target.is_file():
                    b=target.read_bytes(); self.send_response(200); self.send_header('Content-Type','application/octet-stream'); self.send_header('Content-Length',str(len(b))); self.send_header('Content-Disposition',f'attachment; filename="{target.name}"'); self.end_headers(); self.wfile.write(b); return
                return self.respond(404,{"error":"artifact not found"})
            rid=self.path.split('/')[-1]
            if not re.fullmatch(r'[a-f0-9-]{36}',rid): return self.respond(404,{"error":"run not found"})
            try: return self.respond(200,load_run_manifest(RUNS/rid))
            except (FileNotFoundError,ValueError,json.JSONDecodeError): return self.respond(404,{"error":"run not found"})
        if self.path=='/':
            built=ROOT/'apps/dashboard/dist/index.html'
            b=(built if built.exists() else ROOT/'apps/dashboard/index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if self.path.startswith('/assets/'):
            target=(ROOT/'apps/dashboard/dist'/self.path.lstrip('/')).resolve()
            if target.parent == (ROOT/'apps/dashboard/dist/assets').resolve() and target.is_file():
                b=target.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/css' if target.suffix=='.css' else 'text/javascript'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.respond(404,{"error":"not found"})
    def do_POST(self):
        pl=re.fullmatch(r'/api/pulselink/captures/([a-f0-9-]{36})/waveform/open',self.path)
        if pl:
            try: return self.respond(200,launch_pulselink_waveform(pl.group(1)))
            except FileNotFoundError as e: return self.respond(404,{'error':str(e)})
            except EnvironmentError as e: return self.respond(503,{'error':str(e)})
            except ValueError as e: return self.respond(400,{'error':str(e)})
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
        except PermissionError as e: self.respond(403,{"error":str(e)})
        except ValueError as e: self.respond(400,{"error":str(e)})

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int,default=8765)
    ap.add_argument('--enable-pulselink-serial',action='store_true',help='opt in to opening the identity-matched M5Stick tty; USB serial open may reset the MCU')
    a=ap.parse_args()
    if a.enable_pulselink_serial:
        PULSELINK_SERVICE=PulseLinkSerialService(PULSELINK_STORE)
        PULSELINK_SERVICE.start()
        print('PulseLink serial explicitly enabled. Only start after BIOScope firmware is installed; tty open may reset the M5Stick.',flush=True)
    print(f'BIOScope host API listening at http://{a.host}:{a.port} (Dabao physical execution is approval-gated; PulseLink telemetry mode={"opt-in" if a.enable_pulselink_serial else "disabled"})',flush=True)
    try: ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
    finally:
        if PULSELINK_SERVICE: PULSELINK_SERVICE.stop()
