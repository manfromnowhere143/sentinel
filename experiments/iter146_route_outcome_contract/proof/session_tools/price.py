import json,re,hashlib,datetime
from pathlib import Path
D=Path('experiments/iter146_route_outcome_contract/proof');raw=(D/'gcp_accelerator_pricing.html').read_bytes();s=raw.decode()
script=next(x for x in re.findall(r'<script[^>]*>([\s\S]*?)</script>',s) if 'AF_initDataCallback' in x and 'g2-standard-8' in x)
j,_=json.JSONDecoder().raw_decode(script[script.index('data:')+5:]);path=[0,2,1,40,1,0,1,1,3,6];v=j
for k in path:v=v[k]
assert 'Oregon (us-west1)' in v
row=next(r for r in v[1] if 'g2-standard-8' in str(r))
def strings(a):
 if isinstance(a,list):
  for b in a:yield from strings(b)
 elif isinstance(a,str):yield re.sub('<[^>]*>',' ',a).strip()
values=list(strings(row));header=list(strings(v[0]));assert values[0]=='g2-standard-8';assert header[3]=='Price (USD)';rate=float(re.search(r'\$([0-9.]+) / 1 hour',values[3])[1]);assert rate<1
out=dict(url='https://cloud.google.com/products/compute/pricing/accelerator-optimized',retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),html_sha256=hashlib.sha256(raw).hexdigest(),json_path=path,region='Oregon (us-west1)',machine='g2-standard-8',hourly_usd=rate,header=header,values=values,prospective_compute_hourly_upper_usd=3.,scope='VM compute including attached L4; no new disks; retained persistent disk baseline not charged to incremental execution envelope')
(D/'price_binding.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
