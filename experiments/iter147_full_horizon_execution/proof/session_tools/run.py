import datetime,json,subprocess,sys,time
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');P=R/'experiments/iter147_full_horizon_execution/proof/commands';P.mkdir(exist_ok=True)
label=sys.argv[1];args=sys.argv[2:];start=time.time()
command_cwd=R
if args[:1]==['--cwd']:
 command_cwd=Path(args[1]);args=args[2:]
receipts={P/(label+'.'+suffix) for suffix in ['stdout','stderr','json']}
if '--output' in args:
 output=Path(args[args.index('--output')+1]);output=output if output.is_absolute() else R/output
 if output.resolve() in {p.resolve() for p in receipts}:raise ValueError('output/receipt collision before invocation')
if any(p.exists() for p in receipts):raise FileExistsError('command receipt already exists')
r=subprocess.run(args,cwd=command_cwd,capture_output=True)
for suffix,raw in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (P/(label+'.'+suffix)).open('xb') as f:f.write(raw)
with (P/(label+'.json')).open('x') as f:json.dump(dict(argv=args,cwd=str(command_cwd),start_utc=datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-start,returncode=r.returncode),f,indent=2);f.write('\n')
print(label,r.returncode,r.stdout.decode()[-2500:],r.stderr.decode()[-1000:]);sys.exit(r.returncode)
