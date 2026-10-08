"""Display the public aggregate snapshot; never reconstruct per-work judgments."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUDGES = ('judge-1', 'judge-2')
START = '<!-- CNWB:LEADERBOARD:BEGIN -->'
END = '<!-- CNWB:LEADERBOARD:END -->'


def value(scope, metric='total'):
    if scope is None:
        return None
    if 'available_display' in scope:
        display = scope['available_display']
        return display['total'] if metric == 'total' else display['dimensions'].get(metric)
    if metric == 'total':
        return scope.get('total')
    dim = scope['dimensions'][metric]
    return dim['score'] if dim['n'] == dim['planned'] and dim['n'] > 0 else None


def rows(snapshot):
    catalog = snapshot['catalog']
    models = {m['id']: m['name'] for m in catalog['models']}
    visible = set(catalog['default_runs'].values()) | set(catalog.get('additional_default_runs', []))
    preferred = catalog.get('default_evaluations', {})
    selected = {}
    for board in snapshot['boards']:
        key = (board['generation_id'], board['judge_id'])
        old = selected.get(key)
        choice = preferred.get(key[0])
        if (old is None or board['evaluation_id'] == choice
                or (old['evaluation_id'] != choice and board['revision'] > old['revision'])):
            selected[key] = board
    result = []
    for run in catalog['generation_runs']:
        if run['id'] not in visible:
            continue
        boards = [selected.get((run['id'], judge)) for judge in JUDGES]
        scopes = [b['scopes']['all32'] if b else None for b in boards]
        scores = [value(s) for s in scopes]
        dimensions = {}
        for dim in snapshot['scoring']['weights']:
            parts = [value(s, dim) for s in scopes]
            dimensions[dim] = parts[0] * 0.5 + parts[1] * 0.5 if all(v is not None for v in parts) else None
        result.append(dict(generation_id=run['id'], model=models[run['model_id']], configuration=run['label'],
                           evaluations=[b['evaluation_id'] if b else None for b in boards],
                           judge_scores=scores, dimensions=dimensions,
                           total=scores[0] * 0.5 + scores[1] * 0.5 if all(v is not None for v in scores) else None,
                           coverage=[dict(n=s['n'], planned=s['planned']) if s else None for s in scopes]))
    result.sort(key=lambda r: (r['total'] is None, -(r['total'] or 0), r['model'], r['generation_id']))
    previous = None
    rank = None
    for index, row in enumerate(result, 1):
        if row['total'] is None:
            row['rank'] = None
        else:
            if row['total'] != previous:
                rank = index
            row['rank'] = rank
            previous = row['total']
    return result


def load():
    return rows(json.loads((ROOT / 'results/published-leaderboard.json').read_bytes()))


def markdown(entries, english=False):
    def number(v):
        return '\u2014' if v is None else f'{v:.2f}'
    def cell(v):
        return str(v).replace('|', '\\|').replace('\n', ' ')
    title = ('Rank | Model | Configuration | Mean | DeepSeek | MiMo | Scored tasks (DS / MiMo)' if english else
             '排名 | 模型 | 生成配置 | 均分 | DeepSeek | MiMo | 完整计分题数（DS / MiMo）')
    lines = ['| ' + title + ' |', '|---:|---|---|---:|---:|---:|---|']
    for row in entries:
        coverage = ' / '.join(f"{p['n']}/{p['planned']}" if p else '\u2014' for p in row['coverage'])
        label = row['configuration']
        if english and label == '默认':
            label = 'default'
        cells = [row['rank'] if row['rank'] is not None else '\u2014', row['model'], label,
                 number(row['total']), *[number(v) for v in row['judge_scores']], coverage]
        lines.append('| ' + ' | '.join(cell(v) for v in cells) + ' |')
    return '\n'.join(lines)
