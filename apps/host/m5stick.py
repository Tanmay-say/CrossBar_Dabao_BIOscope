"""Application-level M5Stick protocol handler; transport remains unopened."""
from serial_protocol import PROTOCOL_VERSION, run_result, run_status
from server import CATALOG, execute

class M5StickAdapter:
    def handle(self,message):
        if not isinstance(message,dict) or message.get('protocol')!=PROTOCOL_VERSION:
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'unsupported protocol frame'}]
        kind=message.get('type')
        if kind=='hello': return [{'type':'hello_ack','protocol':PROTOCOL_VERSION}]
        if kind!='run_request': return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'unsupported message type'}]
        experiment=message.get('experiment_id'); mode=message.get('mode')
        item=next((e for e in CATALOG if e['id']==experiment),None)
        if not item or mode not in item['modes'] or mode=='HARDWARE':
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'experiment or execution mode is unavailable'}]
        try:
            run=execute({'experiment_id':experiment,'mode':mode})
            status=run_status(run['state'])
            result=run_result(f"{run['experiment_title']}: {run['evidence']} (exit {run['exit_code']})")
            return [status,result]
        except (ValueError,TimeoutError,FileNotFoundError) as e:
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':str(e)[:96]}]
