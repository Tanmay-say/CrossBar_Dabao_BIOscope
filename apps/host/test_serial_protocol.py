import unittest
from serial_protocol import JsonLineDecoder,FrameError,encode,hello_ack
from m5stick import M5StickAdapter

class SerialProtocolTests(unittest.TestCase):
    def test_roundtrip_fragmented(self):
        frame=encode({'type':'hello','protocol':1}); d=JsonLineDecoder()
        self.assertEqual(d.feed(frame[:3]),[]); self.assertEqual(d.feed(frame[3:]),[{'type':'hello','protocol':1}])
    def test_multiple_frames(self):
        d=JsonLineDecoder(); self.assertEqual(len(d.feed(encode({'type':'hello','protocol':1})+encode(hello_ack()))),2)
    def test_invalid_json(self):
        with self.assertRaises(FrameError): JsonLineDecoder().feed(b'{nope}\n')
    def test_wrong_version(self):
        with self.assertRaises(FrameError): encode({'type':'hello','protocol':2})
    def test_oversized(self):
        with self.assertRaises(FrameError): JsonLineDecoder().feed(b'x'*1100)
    def test_host_hello(self): self.assertEqual(M5StickAdapter().handle({'type':'hello','protocol':1})[0]['type'],'hello_ack')
    def test_host_rejects_hardware_mode(self):
        r=M5StickAdapter().handle({'type':'run_request','protocol':1,'experiment_id':'blink','mode':'HARDWARE'})
        self.assertEqual(r[0]['type'],'error')
    def test_host_executes_mock_request(self):
        r=M5StickAdapter().handle({'type':'run_request','protocol':1,'experiment_id':'mock-loopback','mode':'MOCK'})
        self.assertEqual(r[-1]['type'],'run_result')

if __name__=='__main__': unittest.main()
