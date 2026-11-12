import unittest, json, threading, urllib.request, socket, os
from unittest.mock import patch, Mock
from http.server import ThreadingHTTPServer
from server import execute, Handler, launch_waveform, load_run_manifest

class MockAdapterTests(unittest.TestCase):
    def test_success(self):
        r=execute({}); self.assertEqual(r['exit_code'],0); self.assertEqual(r['mode'],'MOCK')
    def test_failure(self): self.assertEqual(execute({'mock_failure':True})['exit_code'],1)
    def test_missing_simulator(self):
        r=execute({'experiment_id':'bio-smoke','mode':'MOCK'}); self.assertEqual(r['adapter'],'mock'); self.assertEqual(r['artifacts'][0]['verified'],False)
    def test_timeout(self):
        with self.assertRaises(TimeoutError): execute({'timeout':True})
    def test_malformed(self):
        with self.assertRaises(ValueError): execute({'unexpected':True})
    def test_artifact_missing(self): self.assertEqual(execute({'omit_artifact':True})['artifacts'],[])
    def test_wrong_mode(self):
        with self.assertRaises(ValueError): execute({'mode':'HARDWARE'})

    def test_hardware_mode_is_not_executable_through_api_engine(self):
        with self.assertRaisesRegex(PermissionError, 'history-only'):
            execute({'experiment_id':'dabao-fifo-probe','mode':'HARDWARE'})

    def test_physical_run_history_contains_verified_target_response_and_logs(self):
        run_id='d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62'
        from server import RUNS
        run=load_run_manifest(RUNS/run_id)
        self.assertEqual(run['mode'],'HARDWARE')
        self.assertEqual(run['evidence'],'HARDWARE_VERIFIED')
        self.assertEqual(run['actual_result']['value'],'0xB105C0DE')
        self.assertIn('b105c0de',run['stdout'].lower())
        self.assertIn('59 remaining chunks',run['operation_sequence'][2])
        self.assertTrue(any(a['name']=='hardware-result.json' and a['sha256'] for a in run['artifacts']))

    def test_api_flow(self):
        try: srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        except PermissionError: self.skipTest('sandbox denies local socket bind')
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        try:
            base=f'http://127.0.0.1:{srv.server_port}'
            with urllib.request.urlopen(base+'/') as r: page=r.read().decode(); self.assertIn('BIOScope',page)
            asset=page.split('src="')[1].split('"')[0]
            with urllib.request.urlopen(base+asset) as r: self.assertIn('Experiment control room',r.read().decode())
            with urllib.request.urlopen(base+'/api/experiments') as r: self.assertTrue(json.load(r))
            with urllib.request.urlopen(base+'/api/devices') as r:
                inventory=json.load(r)
                self.assertEqual({d['id'] for d in inventory},{'dabao','m5stick'})
                self.assertTrue(all('serial' in d and 'topology' in d for d in inventory))
                self.assertTrue(all(d['serial_opened'] is False for d in inventory))
            with urllib.request.urlopen(base+'/api/hardware/capabilities') as r:
                caps=json.load(r)
                self.assertFalse(caps['physical_execution_enabled'])
                self.assertEqual(caps['last_verified_run']['actual'], '0xB105C0DE')
                self.assertIn('v0.10.1-43', caps['hardware_firmware'])
            with urllib.request.urlopen(base+'/api/experiments') as r:
                catalog=json.load(r)
                self.assertIn('dabao-fifo-probe', {item['id'] for item in catalog})
                physical=next(item for item in catalog if item['id']=='dabao-fifo-probe')
                self.assertIn('HARDWARE',physical['modes'])
                self.assertTrue(physical['requires_manual_approval'])
            req=urllib.request.Request(base+'/api/runs',data=json.dumps({'mode':'MOCK'}).encode(),headers={'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req) as r: self.assertEqual(json.load(r)['mode'],'MOCK')
            req=urllib.request.Request(base+'/api/runs',data=json.dumps({'experiment_id':'dabao-fifo-probe','mode':'SIMULATION'}).encode(),headers={'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req) as r:
                probe=json.load(r)
                self.assertEqual(probe['evidence'],'SIMULATED')
                self.assertTrue(probe['validation']['fifo0_sentinel_received'])
                with urllib.request.urlopen(base+f"/api/runs/{probe['run_id']}/artifacts/trace.fst") as artifact:
                    self.assertEqual(len(artifact.read()),probe['artifacts'][0]['size_bytes'])
            with urllib.request.urlopen(base+'/api/runs') as r: self.assertTrue(json.load(r))
            physical_id='d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62'
            with urllib.request.urlopen(base+f'/api/runs/{physical_id}') as r:
                physical=json.load(r)
                self.assertEqual(physical['evidence'],'HARDWARE_VERIFIED')
                self.assertEqual(physical['actual_result']['value'],'0xB105C0DE')
                self.assertIn('b105c0de',physical['stdout'].lower())
            for artifact_name in ('hardware-result.json','manifest-amendment.json'):
                with urllib.request.urlopen(base+f'/api/runs/{physical_id}/artifacts/{artifact_name}') as r:
                    self.assertTrue(r.read())
            request=urllib.request.Request(base+'/api/runs',data=json.dumps({'experiment_id':'dabao-fifo-probe','mode':'HARDWARE'}).encode(),headers={'Content-Type':'application/json'},method='POST')
            with self.assertRaises(urllib.error.HTTPError) as blocked: urllib.request.urlopen(request)
            self.assertEqual(blocked.exception.code,403)
            blocked.exception.close()
            real=execute({'experiment_id':'blink','mode':'SIMULATION'})
            with urllib.request.urlopen(base+f"/api/runs/{real['run_id']}/artifacts/{real['artifacts'][0]['name']}") as r:
                self.assertEqual(len(r.read()),real['artifacts'][0]['size_bytes'])
        finally: srv.shutdown(); srv.server_close()

    def test_official_smoke_if_built(self):
        from bio_sim import available
        if not available(): self.skipTest('official BIO-sim binary not built')
        r=execute({'experiment_id':'bio-smoke','mode':'SIMULATION'})
        self.assertEqual(r['evidence'],'SIMULATED'); self.assertEqual(r['exit_code'],0)
        self.assertIn('0x10000408',r['stdout']); self.assertTrue(r['artifacts'][0]['verified'])

    def test_official_blink_if_built(self):
        from bio_sim import available
        if not available('blink'): self.skipTest('official blink firmware has not been built')
        r=execute({'experiment_id':'blink','mode':'SIMULATION'})
        self.assertEqual(r['evidence'],'SIMULATED'); self.assertTrue(r['validation']['gpio21_transitions'])
        self.assertGreater(r['artifacts'][0]['size_bytes'],0)

    def test_dabao_target_probe_simulation_if_built(self):
        from bio_sim import available
        if not available('dabao-fifo-probe'): self.skipTest('BIO target probe binary has not been built')
        r=execute({'experiment_id':'dabao-fifo-probe','mode':'SIMULATION'})
        self.assertEqual(r['evidence'],'SIMULATED')
        self.assertTrue(r['validation']['fifo0_sentinel_received'])
        self.assertIn('0xb105c0de',r['stdout'].lower())

    def test_waveform_launcher(self):
        from bio_sim import available
        if not available('blink'): self.skipTest('blink simulation unavailable')
        r=execute({'experiment_id':'blink','mode':'SIMULATION'})
        proc=Mock(pid=4242)
        with patch.dict(os.environ,{'DISPLAY':':1','WAYLAND_DISPLAY':''}), patch('server.shutil.which',return_value='/usr/bin/gtkwave'), patch('server.subprocess.Popen',return_value=proc):
            opened=launch_waveform(r['run_id'])
        self.assertTrue(opened['launched']); self.assertEqual(opened['pid'],4242)

    def test_waveform_launcher_no_display(self):
        from bio_sim import available
        if not available(): self.skipTest('smoke simulation unavailable')
        r=execute({'experiment_id':'bio-smoke','mode':'SIMULATION'})
        with patch.dict(os.environ,{'DISPLAY':'','WAYLAND_DISPLAY':''}), patch('server.shutil.which',return_value='/usr/bin/gtkwave'):
            with self.assertRaises(EnvironmentError): launch_waveform(r['run_id'])

if __name__=='__main__': unittest.main()
