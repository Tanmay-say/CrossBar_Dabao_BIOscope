"""Application-level M5Stick protocol handler; transport remains unopened."""
from serial_protocol import PROTOCOL_VERSION, run_result, run_status
from server import CATALOG, execute

class M5StickAdapter:
    def handle(self,message):
        if not isinstance(message,dict) or message.get('protocol')!=PROTOCOL_VERSION:
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'unsupported protocol frame'}]
        kind=message.get('type')
        if kind=='hello':
            if set(message)!={'type','protocol'}:
                return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'invalid hello fields'}]
            return [{'type':'hello_ack','protocol':PROTOCOL_VERSION}]
        if kind!='run_request': return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'unsupported message type'}]
        if set(message)!={'type','protocol','experiment_id','mode'} or not all(isinstance(message[k],str) for k in ('experiment_id','mode')):
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'invalid run request fields'}]
        experiment=message.get('experiment_id'); mode=message.get('mode')
        item=next((e for e in CATALOG if e['id']==experiment),None)
        if not item or mode not in item['modes'] or mode=='HARDWARE':
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':'experiment or execution mode is unavailable'}]
        try:
            run=execute({'experiment_id':experiment,'mode':mode})
            success=run['exit_code']==0 and run['state']=='COMPLETED'
            status=run_status('SUCCESS' if success else 'FAILED')
            result=run_result(f"{'PASS' if success else 'FAIL'} · {run['evidence']} · {run['run_id']}")
            return [status,result]
        except (ValueError,TimeoutError,FileNotFoundError) as e:
            return [{'type':'error','protocol':PROTOCOL_VERSION,'message':str(e)[:96]}]
