import json,time,datetime
from i148f_ops import E,P
E.mkdir(exist_ok=False)
b=json.loads((P/'BINDING.json').read_text());now=time.monotonic();epoch=time.time()
r=dict(iteration=148,block=0,scope=b['scope'],vm_id='3834622546652649531',start_monotonic=now,start_epoch=epoch,deadline_monotonic=now+900,deadline_epoch=epoch+900,whole_seconds=900,compute_cap_usd=.75,conservative_hourly_usd=3,started_utc=datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat(),no_driving=True)
(E/'budget.json').write_text(json.dumps(r,indent=2)+'\n');(P/'gpu_budget.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
