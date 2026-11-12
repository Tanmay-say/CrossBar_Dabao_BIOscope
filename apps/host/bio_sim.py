"""Allow-listed adapter for the acquired official BIO-sim smoke target."""
from pathlib import Path
import hashlib, os, shutil, subprocess, time
import json

ROOT=Path(__file__).resolve().parents[2]
UPSTREAM=ROOT/'vendor'/'bio-sim'

def available(experiment='bio-smoke'):
    if not (UPSTREAM/'build'/'bio_sim').is_file(): return False
    if experiment == 'dabao-fifo-probe':
        return (ROOT/'artifacts/builds/dabao_fifo_probe/dabao_fifo_probe.bin').is_file()
    return (UPSTREAM/'configs'/'smoke.jsonc').is_file() if experiment in ('bio-smoke','register-inspection') else experiment=='blink' and (UPSTREAM/'sw/blink/blink.bin').is_file()

def run_experiment(experiment: str, run_dir: Path, timeout: int=120):
    """Run an allow-listed upstream configuration or the fixed BIO probe config."""
    if not available(experiment): raise FileNotFoundError(f'official BIO-sim target unavailable: {experiment}')
    config_name='blink.jsonc' if experiment=='blink' else 'smoke.jsonc'
    waveform_name='blink.fst' if experiment=='blink' else 'trace.fst'
    run_dir=run_dir.resolve(); run_dir.mkdir(parents=True,exist_ok=True); start=time.time()
    physical_probe = experiment == 'dabao-fifo-probe'
    if physical_probe:
        build_manifest_path = ROOT/'artifacts/builds/dabao_fifo_probe/manifest.json'
        build_manifest = json.loads(build_manifest_path.read_text())
        config = run_dir/'probe-simulation.json'
        waveform_name = 'trace.fst'
        waveform_dest = run_dir/waveform_name
        config_data = {
            'fclk_mhz': 350,
            'commands': [
                {'cmd':'load','core':0,'bin':os.path.relpath(ROOT/build_manifest['binary'],UPSTREAM)},
                {'cmd':'clock','core':0,'style':'frac','freq_hz':1000000},
                {'cmd':'start','cores':[0]},
                {'cmd':'run','cycles':2000,'stop_on_trap':False},
                {'cmd':'fifo_drain','bank':0,'max':1},
            ],
            'trace': {'file': os.path.relpath(waveform_dest,UPSTREAM)},
        }
        config.write_text(json.dumps(config_data,indent=2)+'\n')
        configuration_path = str(config.relative_to(ROOT))
    else:
        config = UPSTREAM/'configs'/config_name
        configuration_path = f'configs/{config_name}'
    p=subprocess.run([str(UPSTREAM/'build'/'bio_sim'),str(config)],cwd=UPSTREAM,capture_output=True,text=True,timeout=timeout,check=False)
    (run_dir/'stdout.log').write_text(p.stdout); (run_dir/'stderr.log').write_text(p.stderr)
    src=waveform_dest if physical_probe else UPSTREAM/'waveform'/waveform_name; artifacts=[]
    if src.is_file() and src.stat().st_size>0:
        dest=run_dir/'trace.fst'
        if src.resolve() != dest.resolve(): shutil.copy2(src,dest)
        artifacts.append({'name':dest.name,'path':str(dest.relative_to(ROOT)),'type':'fst-waveform','verified':True,'size_bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    checks={'process_exit_zero':p.returncode==0,'cfginfo_pass':'[selftest] sfr_cfginfo @0x04 = 0x10000408 (expect 0x10000408) -> PASS' in p.stdout,'waveform_present':bool(artifacts)}
    if experiment=='blink': checks['gpio21_transitions']=p.stdout.count('gpio_out[21]:')>=2
    if physical_probe:
        checks['fifo0_sentinel_received']='[fifo_drain]   [0] = 0xb105c0de' in p.stdout.lower()
    cfgsha=hashlib.sha256(config.read_bytes()).hexdigest()
    rev=subprocess.run(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    ver=subprocess.run(['verilator','--version'],capture_output=True,text=True).stdout.strip()
    zig=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','ziglang','version'],capture_output=True,text=True).stdout.strip() if (ROOT/'.venv/bin/python').exists() else None
    passed=all(checks.values())
    configuration={'path':configuration_path,'sha256':cfgsha,'values':json.loads(config.read_text())}
    if physical_probe:
        configuration.update({'bio_program_sha256':build_manifest['binary_sha256'],'bio_build_manifest_sha256':hashlib.sha256(build_manifest_path.read_bytes()).hexdigest()})
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'started_at':start,'finished_at':time.time(),'duration_seconds':round(time.time()-start,4),'artifacts':artifacts,'validation':checks,'configuration':configuration,'source_revision':rev,'tool_versions':{'verilator':ver,'zig':zig},'evidence':'SIMULATED' if passed else 'SIMULATION_FAILED'}

run_smoke=lambda run_dir,timeout=120: run_experiment('bio-smoke',run_dir,timeout)
