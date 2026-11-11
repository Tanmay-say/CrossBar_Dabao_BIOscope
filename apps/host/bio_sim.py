"""Allow-listed adapter for the acquired official BIO-sim smoke target."""
from pathlib import Path
import hashlib, shutil, subprocess, time

ROOT=Path(__file__).resolve().parents[2]
UPSTREAM=ROOT/'vendor'/'bio-sim'

def available(experiment='bio-smoke'):
    if not (UPSTREAM/'build'/'bio_sim').is_file(): return False
    return (UPSTREAM/'configs'/'smoke.jsonc').is_file() if experiment in ('bio-smoke','register-inspection') else experiment=='blink' and (UPSTREAM/'sw/blink/blink.bin').is_file()

def run_experiment(experiment: str, run_dir: Path, timeout: int=120):
    """Run only upstream configs/smoke.jsonc. Returns structured evidence."""
    if not available(experiment): raise FileNotFoundError(f'official BIO-sim target unavailable: {experiment}')
    config_name='blink.jsonc' if experiment=='blink' else 'smoke.jsonc'
    waveform_name='blink.fst' if experiment=='blink' else 'trace.fst'
    config=UPSTREAM/'configs'/config_name
    run_dir=run_dir.resolve(); run_dir.mkdir(parents=True,exist_ok=True); start=time.time()
    p=subprocess.run([str(UPSTREAM/'build'/'bio_sim'),str(config)],cwd=UPSTREAM,capture_output=True,text=True,timeout=timeout,check=False)
    (run_dir/'stdout.log').write_text(p.stdout); (run_dir/'stderr.log').write_text(p.stderr)
    src=UPSTREAM/'waveform'/waveform_name; artifacts=[]
    if src.is_file() and src.stat().st_size>0:
        dest=run_dir/'trace.fst'; shutil.copy2(src,dest)
        artifacts.append({'name':dest.name,'path':str(dest.relative_to(ROOT)),'type':'fst-waveform','verified':True,'size_bytes':dest.stat().st_size})
    checks={'process_exit_zero':p.returncode==0,'cfginfo_pass':'[selftest] sfr_cfginfo @0x04 = 0x10000408 (expect 0x10000408) -> PASS' in p.stdout,'waveform_present':bool(artifacts)}
    if experiment=='blink': checks['gpio21_transitions']=p.stdout.count('gpio_out[21]:')>=2
    cfgsha=hashlib.sha256(config.read_bytes()).hexdigest()
    rev=subprocess.run(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    ver=subprocess.run(['verilator','--version'],capture_output=True,text=True).stdout.strip()
    zig=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','ziglang','version'],capture_output=True,text=True).stdout.strip() if (ROOT/'.venv/bin/python').exists() else None
    passed=all(checks.values())
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'started_at':start,'finished_at':time.time(),'duration_seconds':round(time.time()-start,4),'artifacts':artifacts,'validation':checks,'configuration':{'path':f'configs/{config_name}','sha256':cfgsha,'values':__import__('json').loads(config.read_text())},'source_revision':rev,'tool_versions':{'verilator':ver,'zig':zig},'evidence':'SIMULATED' if passed else 'SIMULATION_FAILED'}

run_smoke=lambda run_dir,timeout=120: run_experiment('bio-smoke',run_dir,timeout)
