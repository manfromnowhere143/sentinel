from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json
q=Path('/Users/danielwahnich/workspace/sentinel/docs/editorial/2026-10-11');d=q/'diagrams'
def render(job):
 src,theme=job;out=d/(src.stem+'-'+theme+'.png')
 command=['mmdc','-i',str(src),'-o',str(out),'-p',str(q/'puppeteer.json'),'-t','dark' if theme=='dark' else 'default','-b','#0d1117' if theme=='dark' else 'white','-w','960']
 r=subprocess.run(command,capture_output=True,text=True,timeout=55)
 return {'source':src.name,'theme':theme,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'output':out.name}
jobs=[(s,t) for s in sorted(d.glob('*.mmd')) for t in ('light','dark') if not (s.stem=='readme-1' and t=='light')]
with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(render,jobs))
(q/'diagram_render_results.json').write_text(json.dumps({'mermaid_cli':'11.4.2','browser':'existing Google Chrome, fresh headless processes','results':results},indent=2)+'\n')
print(json.dumps({'rendered':len(results),'failures':[r for r in results if r['returncode']]}))
