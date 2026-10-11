import time,json
from i148f_ops import E,stop,P
b=json.loads((E/'budget.json').read_text())
while time.monotonic()<b['deadline_monotonic']:
 if (E/'cleanup_verified.json').exists():print('watchdog cancelled after verified cleanup',flush=True);break
 time.sleep(5)
else:
 if (P/'gpu_ready_instance.json').exists():stop('watchdog')
 else:raise RuntimeError('owned start identity unavailable; inspect provider immediately')
