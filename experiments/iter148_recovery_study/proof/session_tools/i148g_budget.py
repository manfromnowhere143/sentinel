import datetime,time,json
from i148g_ops import E,P
from pathlib import Path
assert (E/'gpu_packet.tar.gz').exists() and not (E/'budget.json').exists()
now=time.monotonic();epoch=time.time()
b=dict(iteration=148,block=0,status='armed',vm_id='3834622546652649531',vm_name='sentinel-gpu',project='sunlit-unison-487018-b0',zone='us-west1-a',source_commit=json.loads((P/'gpu_source_packet.json').read_text())['commit'],start_epoch=epoch,start_monotonic=now,deadline_monotonic=now+10800,deadline_epoch=epoch+10800,started_utc=datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat(),whole_seconds=10800,child_seconds=1200,conservative_hourly_usd=3,compute_cap_usd=9,scope='one owned start, eight fixed study slots, first scenario only; no initialized retry')
(E/'budget.json').write_text(json.dumps(b,indent=2)+'\n');(P/'gpu_budget.json').write_text(json.dumps(b,indent=2)+'\n');print(json.dumps(b))
