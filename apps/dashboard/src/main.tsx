import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import './hardware.css';

type Exp = { id: string; title: string; description: string; modes: string[]; requirements: string[]; available: boolean };
type Device = {
  id: string; name: string; connected: boolean; status: string; serial: string; vid: string; pid: string;
  topology: string; usb_topology: string | null; persistent_port: string | null; linux_device: string | null;
  confidence: string; identity_basis: string; manufacturer: string; product: string;
  manufacturer_descriptor: string | null; interfaces: { number: string | null; driver: string | null }[];
  safety: string; serial_opened: boolean; serial_link_available: boolean;
  connection_event: string; last_connection_change_at: string | null; last_verified_at: string | null;
};
type Run = {
  run_id: string; experiment_id: string; experiment_title: string; mode: string; state: string;
  exit_code: number; started_at: number; duration_seconds: number; evidence: string; stdout: string; stderr: string;
  artifacts: { name: string; path: string; size_bytes: number; verified: boolean; type?: string }[];
  validation?: Record<string, boolean>; configuration?: { path: string; sha256: string; values: unknown };
  source_revision?: string; tool_versions?: Record<string, string | null>;
  observed_signals?: Record<string, { from: number; to: number }[]>;
};
type Health = { simulator: { available: boolean; version: string | null; bio_sim: string } };

async function get<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || response.statusText);
  return data;
}

function App() {
  const [experiments, setExperiments] = useState<Exp[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [selected, setSelected] = useState('bio-smoke');
  const [mode, setMode] = useState('SIMULATION');
  const [result, setResult] = useState<Run | null>(null);
  const [error, setError] = useState('');
  const [viewerMessage, setViewerMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState('');
  const pageKeys = ['overview', 'hardware', 'experiments', 'simulation', 'waveform', 'history', 'diagnostics'] as const;
  type Page = typeof pageKeys[number];
  const initialPage = (pageKeys.find(key => window.location.hash === `#${key}`) || 'overview') as Page;
  const [activePage, setActivePage] = useState<Page>(initialPage);
  const [hardwareOpen, setHardwareOpen] = useState(initialPage === 'hardware');
  function navigate(next: Page) {
    setActivePage(next); setHardwareOpen(next === 'hardware');
    window.location.hash = next;
    if (next !== 'hardware') window.setTimeout(() => document.getElementById(next)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0);
  }

  async function refresh() {
    try {
      const [h, e, r] = await Promise.all([
        get<Health>('/api/health'), get<Exp[]>('/api/experiments'), get<Run[]>('/api/runs'),
      ]);
      setHealth(h); setExperiments(e); setRuns(r); setError('');
    } catch (reason) { setError((reason as Error).message); }
  }
  async function refreshDevices() {
    try { setDevices(await get<Device[]>('/api/devices')); }
    catch (reason) { setError((reason as Error).message); }
  }
  useEffect(() => {
    void refresh(); void refreshDevices();
    const mainTimer = window.setInterval(() => void refresh(), 8000);
    const deviceTimer = window.setInterval(() => void refreshDevices(), 2000);
    return () => { window.clearInterval(mainTimer); window.clearInterval(deviceTimer); };
  }, []);

  const experiment = experiments.find(item => item.id === selected);
  const filtered = experiments.filter(item => (item.title + item.description).toLowerCase().includes(query.toLowerCase()));
  const waveformRun = (result?.artifacts.some(a => a.type === 'fst-waveform' && a.verified) ? result : null)
    || runs.find(run => run.artifacts?.some(a => a.type === 'fst-waveform' && a.verified)) || null;
  function choose(id: string) {
    setSelected(id);
    const choice = experiments.find(item => item.id === id);
    if (choice && !choice.modes.includes(mode)) setMode(choice.modes[0]);
  }
  async function execute() {
    setBusy(true); setError('');
    try {
      const run = await get<Run>('/api/runs', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ experiment_id: selected, mode }),
      });
      setResult(run); await refresh();
    } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }
  async function openWaveform(runId: string) {
    setViewerMessage('');
    try {
      const response = await get<{ launched: boolean }>(`/api/runs/${encodeURIComponent(runId)}/waveform/open`, { method: 'POST' });
      setViewerMessage(response.launched ? 'GTKWave launched on the host display.' : 'GTKWave could not be launched.');
    } catch (reason) { setViewerMessage((reason as Error).message); }
  }

  return <div className="layout">
    <aside className="sidebar">
      <div className="logo">BIO<span>SCOPE</span></div><small>OPEN-SILICON LABORATORY</small>
      <nav>
        {([['overview','◈','Overview'],['hardware','▦','Hardware devices'],['experiments','⌘','Experiment explorer'],['simulation','⌁','Simulation console'],['waveform','∿','Waveform viewer'],['history','▤','Run history'],['diagnostics','⚙','Diagnostics']] as [Page,string,string][]).map(([key,icon,label]) =>
          <button key={key} className={activePage === key ? 'navitem active' : 'navitem'} onClick={() => navigate(key)}>{icon} &nbsp; {label}</button>)}
      </nav>
      <footer>MANJARO HOST<br />LOCAL SESSION</footer>
    </aside>
    <main>
      <header>
        <div><label>{activePage === 'hardware' ? 'HARDWARE LABORATORY / USB INVENTORY' : 'DEVELOPER LABORATORY / HOST'}</label>
          <h1>{({overview:'Experiment control room',hardware:'Hardware devices',experiments:'Experiment explorer',simulation:'Simulation console',waveform:'Waveform viewer',history:'Run history',diagnostics:'Diagnostics'} as Record<Page,string>)[activePage]}</h1></div>
        <span className={health ? 'pill good' : 'pill bad'}>● {health ? 'HOST ONLINE' : 'API OFFLINE'}</span>
      </header>
      {hardwareOpen ? <HardwarePage devices={devices} error={error} /> : <>
        <div className="notice"><b>SIMULATION EVIDENCE</b> — simulator runs execute official BIO-sim. MOCK runs only exercise the host pipeline. Neither implies physical hardware execution.</div>
        <section className="metrics" id="overview">
          <Metric title="Host API" value={health ? 'Online' : 'Offline'} note="Local service health" />
          <Metric title="BIO-sim" value={health?.simulator.bio_sim || 'Checking'} note={health?.simulator.version || 'Verilator status unknown'} />
          <Metric title="Experiment catalog" value={String(experiments.length)} note="Upstream grounded entries" />
          <Metric title="Recorded runs" value={String(runs.length)} note="Persistent manifests" />
        </section>
        <section className="cols">
          <article className="panel"><div className="panelhead"><h2>Device laboratory</h2><button className="quiet" onClick={() => navigate('hardware')}>Details →</button></div>
            {devices.map(device => <div className="device" key={device.id}><div><b><i className={device.connected ? 'dot' : 'dot off'} />{device.name}</b><small>{device.status} · {device.serial || 'serial unavailable'}</small></div><span className="tag">{device.connected ? 'CONNECTED' : 'OFFLINE'}</span></div>)}
            <p className="muted">Descriptor and /dev/serial/by-id discovery only. No serial ports opened.</p>
          </article>
          <article className="panel" id="experiments"><div className="panelhead"><h2>Experiment explorer</h2><input placeholder="Filter catalog…" value={query} onChange={event => setQuery(event.target.value)} /></div>
            <div className="cards">{filtered.map(item => <button className={`exp ${selected === item.id ? 'chosen' : ''}`} key={item.id} onClick={() => choose(item.id)}><span className="tag">{item.available ? 'READY' : 'UPSTREAM REQUIRED'}</span><b>{item.title}</b><small>{item.description}</small></button>)}</div>
            {experiment && <><div className="detail"><span>Needs: {experiment.requirements.join(', ') || 'none'}</span><span>Modes: {experiment.modes.join(' / ')}</span></div><div className="actions"><select value={mode} onChange={event => setMode(event.target.value)}>{experiment.modes.map(value => <option key={value}>{value}</option>)}</select><button disabled={busy || !experiment.available} onClick={execute}>{busy ? 'Executing…' : `Run ${mode}`}</button></div></>}
          </article>
          <article className="panel" id="history"><h2>Run history</h2>{runs.map(run => <button className="history" key={run.run_id} onClick={() => { setResult(run); navigate('simulation'); }}><b>{run.experiment_title}</b><span>{run.mode} · {run.state} · exit {run.exit_code}</span><small>{new Date(run.started_at * 1000).toLocaleString()}</small></button>)}{!runs.length && <p className="muted">No runs yet. Select an experiment to begin.</p>}</article>
          <article className="panel" id="diagnostics"><h2>Toolchain & diagnostics</h2><div className="device"><b>Verilator</b><span>{health?.simulator.version || 'Not detected'}</span></div><div className="device"><b>Official simulator</b><span>{health?.simulator.bio_sim || 'Unknown'}</span></div><div className="device"><b>Hardware mode</b><span>Safety locked</span></div><p className="muted">M5Stick Bruce firmware preserved. BIOScope protocol firmware has not been installed.</p></article>
        </section>
        <section className="panel console" id="simulation"><h2>Simulation console & artifacts</h2>{error && <p className="error">{error}</p>}{result ? <>
          <p className="muted">{result.run_id} · {result.mode} · {result.evidence} · {result.duration_seconds}s · exit {result.exit_code}</p>
          <p className="muted">Source {result.source_revision || 'n/a'} · {result.configuration?.path || ''} · SHA-256 {result.configuration?.sha256 || 'n/a'}</p>
          {result.validation && <pre>{JSON.stringify(result.validation, null, 2)}</pre>}
          {result.observed_signals && Object.entries(result.observed_signals).map(([signal, edges]) => <p key={signal} className="signal"><b>{signal}</b> {edges.map(edge => `${edge.from}→${edge.to}`).join('  ')}</p>)}
          <pre>{`STDOUT\n${result.stdout}\nSTDERR\n${result.stderr || '(empty)'}`}</pre>
          {result.artifacts.map(artifact => <span key={artifact.name}><a className="artifact" href={`/api/runs/${result.run_id}/artifacts/${encodeURIComponent(artifact.name)}`}>Download {artifact.name} · {artifact.size_bytes.toLocaleString()} bytes · {artifact.verified ? 'verified' : 'placeholder'}</a>{artifact.type === 'fst-waveform' && <button onClick={() => openWaveform(result.run_id)}>Open in GTKWave</button>}</span>)}
          {viewerMessage && <p className="muted">{viewerMessage}</p>}
        </> : <p className="muted">Run an experiment or select history to inspect output.</p>}</section>
        <section className="panel console" id="waveform"><h2>Waveform viewer</h2>{waveformRun ? <>
          <p className="muted">Genuine verified FST · {waveformRun.experiment_title} · {waveformRun.run_id}</p>
          {waveformRun.observed_signals && Object.entries(waveformRun.observed_signals).map(([signal, edges]) => <p key={signal} className="signal"><b>{signal}</b> {edges.map(edge => `${edge.from}→${edge.to}`).join('  ')}</p>)}
          {waveformRun.artifacts.filter(a => a.type === 'fst-waveform' && a.verified).map(artifact => <span key={artifact.name}><a className="artifact" href={`/api/runs/${waveformRun.run_id}/artifacts/${encodeURIComponent(artifact.name)}`}>Download {artifact.name} · {artifact.size_bytes.toLocaleString()} bytes</a><button onClick={() => openWaveform(waveformRun.run_id)}>Open in GTKWave</button></span>)}
          {viewerMessage && <p className="muted">{viewerMessage}</p>}
        </> : <p className="muted">No verified FST artifact in the run history yet.</p>}</section>
      </>}
      <p className="end">BIOScope · Simulation and physical execution are reported as separate evidence classes.</p>
    </main>
  </div>;
}

function HardwarePage({ devices, error }: { devices: Device[]; error: string }) {
  return <>
    <div className="notice safety"><b>READ ONLY INVENTORY</b> — BIOScope reads USB sysfs descriptors and persistent serial link names. No device serial port is opened, no DTR/RTS line is toggled, and no device command is sent.</div>
    {error && <p className="error">{error}</p>}
    <section className="hardware-grid">{devices.map(device => <article className="panel hardware-card" key={device.id}>
      <div className="hardware-title"><div><span className={device.connected ? 'hardware-indicator online' : 'hardware-indicator'} />{device.connected ? 'CONNECTED' : 'DISCONNECTED'}</div><span className="tag">{device.id === 'dabao' ? 'BAOCHIP-1X' : 'M5STACK'}</span></div>
      <h2>{device.name}</h2><p className="muted">{device.status}</p>
      <dl className="identity-grid"><dt>USB identity</dt><dd>{device.vid}:{device.pid}</dd><dt>Manufacturer</dt><dd>{device.manufacturer_descriptor || `${device.manufacturer} (database; USB string absent)`}</dd><dt>Product</dt><dd>{device.product}</dd><dt>USB serial</dt><dd>{device.serial || 'not present'}</dd><dt>USB topology</dt><dd>{device.usb_topology || 'not connected'} · expected {device.topology}</dd><dt>Persistent port</dt><dd className="break">{device.persistent_port || 'not available'}</dd><dt>Linux node</dt><dd>{device.linux_device || 'not available'}</dd><dt>USB interfaces</dt><dd>{device.interfaces?.map(item => `${item.number || '?'} (${item.driver || 'unbound'})`).join(', ') || 'not connected'}</dd><dt>Identity confidence</dt><dd>{device.confidence}</dd></dl>
      <div className="safety-card"><b>Safety status</b><span>{device.safety}</span><span>Port state: {device.serial_opened ? 'OPEN' : 'CLOSED'}</span></div>
      <dl className="identity-grid verification-times"><dt>Last profile verification</dt><dd>{formatTime(device.last_verified_at)}</dd><dt>Last connection change</dt><dd>{formatTime(device.last_connection_change_at)} · {device.connection_event}</dd></dl>
      <small className="muted">Correlation: {device.identity_basis}. Matching VID/PID alone is never sufficient.</small>
    </article>)}</section>
    <p className="muted refresh-note">Device state refreshes every 2 seconds from read-only USB and /dev/serial/by-id discovery.</p>
  </>;
}

function formatTime(value: string | null) { return value ? new Date(value).toLocaleString() : 'not recorded'; }

function Metric({ title, value, note }: { title: string; value: string; note: string }) {
  return <article className="panel metric"><small>{title}</small><strong>{value}</strong><span>{note}</span></article>;
}

createRoot(document.getElementById('root')!).render(<App />);
