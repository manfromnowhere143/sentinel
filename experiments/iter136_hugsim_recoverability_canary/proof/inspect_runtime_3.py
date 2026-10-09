import pathlib,subprocess,hashlib,json
out={'source_files':{},'commands':[]}
for name in ['HUGSIM','UniAD_SIM']:
 root=pathlib.Path('/opt/sentinel-stack')/name
 raw=subprocess.check_output(['git','-C',str(root),'ls-files','-z'])
 for name in raw.decode().split('\0'):
  if not name:continue
  p=root/name
  if p.is_file() and not p.is_symlink():
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
   out['source_files'][str(p)]=h.hexdigest()
  elif p.is_symlink():out.setdefault('symlinks',{})[str(p)]=str(p.readlink())
  elif not p.is_dir():out.setdefault('missing',[]).append(str(p))
for a in [['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-m','pip','freeze'],['date','-u','+%Y-%m-%dT%H:%M:%SZ'],['cat','/proc/uptime'],['du','-sh','/datasets/nuscenes-full/hugsim/iter112_runs']]:
 p=subprocess.run(a,text=True,capture_output=True,timeout=60);out['commands'].append(dict(argv=a,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
print(json.dumps(out,indent=2))
