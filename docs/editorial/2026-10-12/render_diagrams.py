"""Render the current presentation with the locally available Mermaid CLI."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'diagrams'
OUT.mkdir(exist_ok=True)
config = HERE / 'puppeteer.json'
config.write_text(json.dumps({'executablePath': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'headless': True}) + '\n')
inputs = []
for name, prefix in [('README.md', 'readme'), ('docs/ARCHITECTURE.md', 'architecture')]:
    for i, block in enumerate(re.findall(r'```mermaid\n(.*?)```', (ROOT / name).read_text(), re.S), 1):
        assert len(block) < 1100, (name, i, len(block))
        source = OUT / f'{prefix}-{i}.mmd'
        source.write_text(block)
        inputs.append(source)

def render(job):
    source, theme = job
    svg = OUT / f'{source.stem}-{theme}.svg'
    argv = ['mmdc', '-i', str(source), '-o', str(svg), '-p', str(config), '-t', 'dark' if theme == 'dark' else 'default', '-b', '#0d1117' if theme == 'dark' else 'white', '-w', '960']
    result = subprocess.run(argv, capture_output=True, text=True, timeout=55)
    return {'source': source.name, 'theme': theme, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr, 'svg': svg.name, 'sha256': hashlib.sha256(svg.read_bytes()).hexdigest() if svg.exists() else None}

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(render, [(p, t) for p in inputs for t in ('light', 'dark')]))
report = {'mermaid_cli': subprocess.check_output(['mmdc', '--version'], text=True).strip(), 'scope': 'Local rendering; not hosted GitHub rendering', 'results': results}
(HERE / 'diagram_render_results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'diagrams': len(inputs), 'renders': len(results), 'failures': [r for r in results if r['returncode']]}))
