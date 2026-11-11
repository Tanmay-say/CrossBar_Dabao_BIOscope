"""Transport-agnostic newline JSON protocol for the prepared M5Stick firmware."""
import json

PROTOCOL_VERSION=1
MAX_FRAME_BYTES=1024

class FrameError(ValueError): pass

def encode(message):
    if not isinstance(message,dict): raise FrameError('frame must be a JSON object')
    if message.get('protocol')!=PROTOCOL_VERSION: raise FrameError('unsupported protocol version')
    data=json.dumps(message,separators=(',',':')).encode('utf-8')
    if len(data)>MAX_FRAME_BYTES: raise FrameError('frame too large')
    return data+b'\n'

class JsonLineDecoder:
    def __init__(self): self.buffer=bytearray()
    def feed(self,data:bytes):
        if not isinstance(data,(bytes,bytearray)): raise FrameError('transport data must be bytes')
        frames=[]
        for byte in data:
            if byte==10:
                if not self.buffer: continue
                raw=bytes(self.buffer); self.buffer.clear()
                try: msg=json.loads(raw.decode('utf-8'))
                except (UnicodeDecodeError,json.JSONDecodeError) as e: raise FrameError('malformed JSON frame') from e
                if not isinstance(msg,dict) or msg.get('protocol')!=PROTOCOL_VERSION: raise FrameError('invalid protocol frame')
                if msg.get('type') not in {'hello','hello_ack','run_request','run_status','run_result','error'}: raise FrameError('unknown message type')
                frames.append(msg)
            elif len(self.buffer)>=MAX_FRAME_BYTES: self.buffer.clear(); raise FrameError('frame too large')
            else: self.buffer.append(byte)
        return frames

def hello_ack(): return {'type':'hello_ack','protocol':PROTOCOL_VERSION}
def run_status(state): return {'type':'run_status','protocol':PROTOCOL_VERSION,'state':str(state)[:48]}
def run_result(result): return {'type':'run_result','protocol':PROTOCOL_VERSION,'result':str(result)[:96]}
