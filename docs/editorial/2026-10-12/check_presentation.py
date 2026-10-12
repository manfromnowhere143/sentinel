"""One-off editorial audit; does not amend any scientific or publication gate."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT = '4d2998ef8d1c6df8facabb271af49569154259d8'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def anchors(text):
    result = []
    for heading in re.findall(r'^#{1,6} (.+)$', text, re.M):
        heading = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', heading)
        result.append(re.sub(r'[^\w\s-]', '', heading.lower()).replace(' ', '-'))
    return result

files = ['README.md', 'docs/ARCHITECTURE.md', 'HANDOFF.md', 'docs/editorial/2026-10-12/REVIEW.md']
links = 0
for name in files:
    path = ROOT / name
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if target.startswith(('http:', 'https:', 'mailto:')):
            continue
        rel, _, fragment = target.partition('#')
        dest = path.parent / rel if rel else path
        assert dest.exists(), (name, target)
        if fragment and dest.suffix == '.md':
            assert fragment in anchors(dest.read_text()), (name, target, 'anchor')
        links += 1

old = git('show', PARENT + ':README.md').decode()
new = (ROOT / 'README.md').read_text()
start = '## Measured results'
end = '## What the monitor actually uses'
old_results = old[old.index(start):old.index(end)]
new_results = new[new.index(start):new.index('## How the question changed')]
assert old_results == new_results
old_rows = [line for line in old[old.index('## Complete experiment index'):].splitlines() if line.startswith('|')]
new_rows = [line for line in new[new.index('## Complete experiment index'):].splitlines() if line.startswith('|')]
assert old_rows == new_rows
results = sorted(ROOT.glob('experiments/*/RESULT.md'))
assert all(str(p.relative_to(ROOT)) in new for p in results)
assert new.index('## What Sentinel does') < new.index('## Measured results')
assert new.index('## Reproduce and inspect') < new.index('## Repository status')
assert 'not been independently replayed' not in new
assert 'corrected cloud\nexecution is unobserved' not in (ROOT / 'docs/ARCHITECTURE.md').read_text()

witness = json.loads((ROOT / 'experiments/iter155_background_witness/proof/admission.json').read_text())
assert witness['selected_points'] == 276519 and witness['population_points'] == 1345702
assert [(f['time'], f['count'], f['source_count'], f['mask_disagreements']) for f in witness['frames']] == [(3.0, 0, 0, []), (3.25, 273, 273, [])]
assert witness['new_driving_episodes'] == 0
assert all(witness[key] is None for key in ['physical_occupancy', 'road_compliance', 'live_recovery', 'information_benefit'])

diagrams = []
for name, prefix in [('README.md', 'readme'), ('docs/ARCHITECTURE.md', 'architecture')]:
    for i, source in enumerate(re.findall(r'```mermaid\n(.*?)```', (ROOT / name).read_text(), re.S), 1):
        stem = f'{prefix}-{i}'
        assert 0 < len(source) < 1100
        assert 'classDef' not in source or 'color:' in source
        assert 'accTitle:' in source and 'accDescr:' in source
        assert (HERE / 'diagrams' / (stem + '.mmd')).read_text() == source
        for theme in ['light', 'dark']:
            for suffix in ['svg', 'png']:
                assert (HERE / 'diagrams' / f'{stem}-{theme}.{suffix}').stat().st_size > 100
        diagrams.append({'name': stem, 'source_characters': len(source), 'source_sha256': hashlib.sha256(source.encode()).hexdigest()})
layout = json.loads((HERE / 'diagrams/layout_check.json').read_text())
assert len(layout) == 14 and all(not x['clipped'] for x in layout)
assert len(diagrams) == 7
changed = git('diff', '--name-only', PARENT).decode().splitlines()
assert set(changed) <= {'README.md', 'docs/ARCHITECTURE.md', 'HANDOFF.md', 'CONTINUITY.md'} | {p for p in changed if p.startswith('docs/editorial/2026-10-12/')}
assert not git('diff', PARENT, '--', 'experiments', 'tests', 'scripts', 'tools', 'AGENTS.md', 'MISSION_STATE.json', '.github', 'pyproject.toml')
report = {'status': 'supported', 'scope': 'Editorial checks, not scientific admission or hosted CI', 'research_parent': PARENT, 'links_and_anchors': links, 'result_files_linked': len(results), 'index_rows_retained': len(old_rows), 'measured_results_unchanged': True, 'scientific_source_and_evidence_unchanged': True, 'diagram_count_before': 5, 'diagram_count_after': 7, 'diagrams': diagrams, 'light_dark_renders': len(layout), 'out_of_canvas_labels': 0, 'readme_words_before': len(old.split()), 'readme_words_after': len(new.split())}
(HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'diagrams'}, indent=2))
