"""Development checks and explicit, Git-scoped software release manifests."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

import leaderboard
import protocol
import scoring

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'tools/manifests/source.json'
RELEASE = 'tools/manifests/release.json'
IGNORED = {'.git', '__pycache__', 'out', '.venv'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
            and not any(part in IGNORED for part in p.relative_to(root).parts)}


def frozen_materials(root, source):
    expected = source['material_files']
    actual = {n for n in inventory(root) if n.startswith('benchmark/')}
    scoring.require(actual == set(expected), 'Frozen material inventory changed; create a new benchmark version')
    for name, wanted in expected.items():
        scoring.require(digest(root / name) == wanted,
                        'Frozen material changed; create a new benchmark version: ' + name)


def check(release=False):
    source = scoring.read(ROOT / SOURCE)
    frozen_materials(ROOT, source)
    tasks = protocol.tasks()
    scoring.require(len(tasks) == 32 and len({t['id'] for t in tasks}) == 32, 'Task inventory mismatch')
    coverage = {d: sum(d in t['focus'] for t in tasks) for d in ('T1', 'T2', 'T3', 'T4', 'T5', 'T6')}
    scoring.require(list(coverage.values()) == [19, 16, 15, 19, 12, 15], 'Coverage mismatch')
    sample = scoring.score(scoring.read(ROOT / 'examples/generation.json'),
                           scoring.read(ROOT / 'examples/evaluation.json'))
    scoring.require(sample['scopes']['all32']['total'] == 60, 'Synthetic smoke check failed')
    for name, english in (('README.md', False), ('README.en.md', True)):
        readme = (ROOT / name).read_text(encoding='utf-8')
        scoring.require(readme.count(leaderboard.START) == readme.count(leaderboard.END) == 1,
                        'Missing or duplicate leaderboard markers: ' + name)
        table = readme.split(leaderboard.START)[1].split(leaderboard.END)[0].strip()
        scoring.require(table == leaderboard.markdown(leaderboard.load(), english),
                        'Homepage leaderboard does not match public snapshot: ' + name)
    files = inventory(ROOT)
    for name in sorted(files):
        path = ROOT / name
        scoring.require(path.resolve().is_relative_to(ROOT), 'File leaves the project: ' + name)
        if path.suffix == '.json':
            scoring.read(path)
        elif path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=name)
        elif path.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                target = link.strip('<>').split('#')[0]
                if not target or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    continue
                dest = (path.parent / target).resolve()
                scoring.require(dest.is_relative_to(ROOT) and dest.exists(),
                                'Broken local link: ' + name + ' -> ' + target)
    if release:
        manifest = scoring.read(ROOT / RELEASE)
        scoring.require(files - {RELEASE} == set(manifest['files']), 'Unexpected or missing release files')
        for name, wanted in manifest['files'].items():
            scoring.require(digest(ROOT / name) == wanted, 'Release hash mismatch: ' + name)
        for name, wanted in source['core_tools'].items():
            scoring.require(digest(ROOT / name) == wanted, 'Source tool hash mismatch: ' + name)
        scoring.require(digest(ROOT / 'results/published-leaderboard.json') == source['public_results_sha256'],
                        'Public results source hash mismatch')
    return dict(verified=True, mode='release' if release else 'development', tasks=32,
                coverage=coverage, files=len(files), frozen_materials=True, api_calls=0)


def tracked_files(root):
    # Maintainer command only. Normal checks and scoring do not require Git.
    names = subprocess.check_output(['git', '-c', 'safe.directory=' + root.as_posix(),
                                     '-C', str(root), 'ls-files', '-z'])
    return set(names.decode('utf-8').rstrip('\0').split('\0'))


def encoded(value, previous):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if b'\r\n' in previous:
        text = text.replace('\n', '\r\n')
    return text.encode('utf-8')


def manifest_plan(root, version):
    root = Path(root).resolve()
    scoring.require(bool(re.fullmatch(r'\d+\.\d+\.\d+', version)), 'Use a software version such as 1.0.4')
    source = scoring.read(root / SOURCE)
    old = scoring.read(root / RELEASE)
    frozen_materials(root, source)
    scoring.require(digest(root / 'results/published-leaderboard.json') == source['public_results_sha256'],
                    'Public snapshot changed; review its provenance separately')
    names = tracked_files(root)
    actual = inventory(root)
    scoring.require(names == actual, 'Stage file additions/deletions and remove untracked release files first')
    for name in names:
        path = root / name
        scoring.require(path.resolve().is_relative_to(root), 'Tracked file leaves the project: ' + name)
        scoring.require(not any(part in {'.local', 'private'} for part in path.relative_to(root).parts)
                        and not path.name.startswith('.env')
                        and path.suffix.lower() not in {'.key', '.pem', '.dpapi', '.log', '.pid', '.lock'},
                        'Local/private file cannot enter a release: ' + name)
    citation = (root / 'CITATION.cff').read_text(encoding='utf-8')
    match = re.search(r'^version:\s*[\"\']?([0-9.]+)', citation, re.MULTILINE)
    scoring.require(match is not None and match[1] == version, 'Update CITATION.cff to the software version first')
    changed = sorted(n for n in names - {SOURCE, RELEASE}
                     if old['files'].get(n) != digest(root / n))
    removed = sorted(set(old['files']) - names)
    scoring.require(version != old['release'] or not changed and not removed,
                    'Changed release content requires a new software version')
    source['core_tools'] = {n: digest(root / n) for n in sorted(names)
                            if n.startswith('tools/') and n.endswith('.py') and n.count('/') == 1}
    source_bytes = encoded(source, (root / SOURCE).read_bytes())
    new = dict(old, release=version)
    new['files'] = {n: hashlib.sha256(source_bytes).hexdigest() if n == SOURCE else digest(root / n)
                    for n in sorted(names - {RELEASE})}
    return source_bytes, encoded(new, (root / RELEASE).read_bytes()), dict(
        release=version, files=len(names), changed_files=changed, removed_files=removed,
        frozen_materials_unchanged=True, public_results_unchanged=True, api_calls=0)


def update_manifests(version, write=False):
    check()
    source_bytes, release_bytes, report = manifest_plan(ROOT, version)
    report['written'] = write
    if write:
        # These are the only existing files this explicit maintainer command updates.
        (ROOT / SOURCE).write_bytes(source_bytes)
        (ROOT / RELEASE).write_bytes(release_bytes)
        check(release=True)
    return report
