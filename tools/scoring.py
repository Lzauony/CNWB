"""Portable offline scoring for STORY32 v2-r10 / SJ6 r0.

Raw judgments remain local. This module never sends a request or changes a grade.
"""
import json
import re
from collections import Counter
from pathlib import Path

import protocol
import sj6_kernel as sj

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = 'cnwb-story32-v1'


def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'),
                      parse_constant=lambda value: fail('Non-finite JSON: ' + value))


def fail(message):
    raise ValueError(message)


def require(condition, message):
    if not condition:
        fail(message)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,180}', value),
            'Invalid identifier')


def unique(items, key):
    require(isinstance(items, list), 'Expected an array')
    result = {}
    for item in items:
        require(isinstance(item, dict) and key in item, 'Missing ' + key)
        require(item[key] not in result, 'Duplicate ' + key)
        result[item[key]] = item
    return result


def validate_generation(g):
    require(type(g.get('schema_version')) is int and g['schema_version'] == 1 and g.get('benchmark_id') == BENCHMARK,
            'Wrong generation schema or benchmark')
    identifier(g['id'])
    identifier(g['model_id'])
    works = unique(g['works'], 'task_id')
    require(set(works) <= {t['id'] for t in protocol.tasks()}, 'Unknown task')
    for w in works.values():
        require(isinstance(w.get('text'), str) and w.get('sha256') == protocol.sha(w['text']),
                'Work hash mismatch')
    return works


def validate_evaluation(e, g):
    require(type(e.get('schema_version')) is int and e['schema_version'] == 1 and e.get('benchmark_id') == BENCHMARK,
            'Wrong evaluation schema or benchmark')
    require(e.get('protocol_id') == 'sj6-r0' and e.get('generation_id') == g['id'],
            'Wrong protocol or generation binding')
    identifier(e['id'])
    identifier(e['judge_id'])
    require(type(e.get('revision')) is int and e['revision'] > 0, 'Invalid revision')
    works = validate_generation(g)
    reviews = unique(e['reviews'], 'task_id')
    require(set(reviews) <= set(works), 'Review without a matching work')
    projections = {}
    for tid, r in reviews.items():
        require(r.get('answer_sha256') == works[tid]['sha256'], 'Review hash mismatch')
        p = sj.project(protocol.task(tid), works[tid]['text'], r['B1'], r.get('B2'))
        if 'projection' in r:
            require(r['projection'] == p, 'Stored projection differs from SJ6')
        projections[tid] = p
    return projections


def complete(p):
    return (p is not None and p['delivery_state'] == 'delivered'
            and all(type(v) is int for v in p['final_grades'].values()))


def aggregate(projections, scope='all32', policy='strict'):
    require(scope in ('all32', 'prose28', 'planning4'), 'Unknown scope')
    require(policy in ('strict', 'available-complete-works'), 'Unknown missing policy')
    cfg = read(ROOT / 'benchmark/scoring.json')
    tasks = [t for t in protocol.tasks() if scope == 'all32'
             or ((t['id'] not in cfg['planning_tasks']) if scope == 'prose28'
                 else (t['id'] in cfg['planning_tasks']))]
    dimensions = {}
    for d in cfg['dimensions']:
        planned = [t for t in tasks if d in t['focus']]
        values = [projections[t['id']]['final_grades'][d] for t in planned
                  if complete(projections.get(t['id']))]
        dimensions[d] = dict(n=len(values), planned=len(planned),
                             mean=sum(values) / len(values) if values else None,
                             score=20 * sum(values) / len(values) if values else None,
                             distribution=dict(Counter(values)))
    n = sum(complete(projections.get(t['id'])) for t in tasks)
    observed_all = all(v['n'] > 0 for v in dimensions.values())
    full = n == len(tasks) and observed_all
    total = (sum(cfg['weights'][d] * v['score'] for d, v in dimensions.items())
             if observed_all and (full or policy == 'available-complete-works') else None)
    excluded = []
    for t in tasks:
        p = projections.get(t['id'])
        if not complete(p):
            reason = ('missing_review' if p is None else 'awaiting_B2' if p['needs_B2']
                      else 'unassessable' if p['delivery_state'] == 'delivered'
                      else p['delivery_state'])
            excluded.append(dict(task_id=t['id'], reason=reason,
                                 dimension_states=p['dimension_states'] if p else {}))
    return dict(n=n, planned=len(tasks), complete=n == len(tasks), total=total,
                dimensions=dimensions, excluded_tasks=excluded, missing_policy=policy)


def score(g, e, policy='strict', reason=None):
    require(policy == 'strict' or isinstance(reason, str) and reason.strip(),
            'Available-work scoring needs an explicit documented reason')
    projections = validate_evaluation(e, g)
    missing_works = [t['id'] for t in protocol.tasks() if t['id'] not in validate_generation(g)]
    return dict(schema_version=1, benchmark_id=BENCHMARK, protocol_id='sj6-r0',
                generation_id=g['id'], model_id=g['model_id'], judge_id=e['judge_id'],
                evaluation_id=e['id'], revision=e['revision'], missing_policy=policy,
                missing_reason=reason, synthetic=bool(g.get('synthetic')),
                missing_works=missing_works,
                input_sha256=dict(generation=protocol.sha(json.dumps(g, ensure_ascii=False, sort_keys=True)),
                                  evaluation=protocol.sha(json.dumps(e, ensure_ascii=False, sort_keys=True))),
                scopes={s: aggregate(projections, s, policy)
                        for s in ('all32', 'prose28', 'planning4')},
                assurance=dict(format_valid=True, literary_verified=False), api_calls=0)


def average(left, right):
    for k in ('benchmark_id', 'protocol_id', 'generation_id', 'model_id'):
        require(left[k] == right[k], 'Average input differs: ' + k)
    require(left['judge_id'] != right['judge_id'], 'Two distinct judges required')
    require(left['input_sha256']['generation'] == right['input_sha256']['generation'],
            'The judges scored different works')
    scopes = {}
    for scope in ('all32', 'prose28', 'planning4'):
        a, b = left['scopes'][scope], right['scopes'][scope]
        mean = lambda x, y: (x + y) / 2 if x is not None and y is not None else None
        scopes[scope] = dict(total=mean(a['total'], b['total']),
                             dimensions={d: mean(a['dimensions'][d]['score'], b['dimensions'][d]['score'])
                                         for d in a['dimensions']},
                             judge_coverage=[dict(judge_id=x['judge_id'], n=x['scopes'][scope]['n'],
                                                  excluded_tasks=x['scopes'][scope]['excluded_tasks'],
                                                  missing_policy=x['missing_policy']) for x in (left, right)])
    return dict(schema_version=1, benchmark_id=BENCHMARK, protocol_id='sj6-r0',
                generation_id=left['generation_id'], model_id=left['model_id'],
                aggregation='two_judge_equal_mean_of_independent_scores',
                judges=[dict(judge_id=x['judge_id'], evaluation_id=x['evaluation_id'], revision=x['revision'])
                        for x in (left, right)], scopes=scopes,
                synthetic=left.get('synthetic', False), api_calls=0)


def rank(records, scope='all32', metric='total'):
    require(scope in ('all32', 'prose28', 'planning4'), 'Unknown scope')
    require(metric in ('total', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6'), 'Unknown metric')
    rows = []
    identities = set()
    for r in records:
        require(r['benchmark_id'] == BENCHMARK and r['protocol_id'] == 'sj6-r0', 'Wrong ranking version')
        kind = (r['aggregation'] + ':' + ','.join(sorted(j['judge_id'] for j in r['judges']))
                if 'aggregation' in r else 'single_judge:' + r.get('judge_id', ''))
        identities.add(kind)
        v = r['scopes'][scope]
        value = v['total'] if metric == 'total' else v['dimensions'][metric]
        if isinstance(value, dict):
            value = value['score']
        rows.append(dict(generation_id=r['generation_id'], model_id=r['model_id'], score=value))
    require(len(identities) <= 1, 'Do not mix independent judges and average tracks')
    require(len({r['generation_id'] for r in rows}) == len(rows), 'Duplicate generation in ranking')
    rows.sort(key=lambda r: (r['score'] is None, -(r['score'] or 0), r['generation_id']))
    previous = None
    place = None
    for i, r in enumerate(rows, 1):
        if r['score'] is None:
            r['rank'] = None
        else:
            if r['score'] != previous:
                place = i
            r['rank'] = place
            previous = r['score']
    return dict(scope=scope, metric=metric, rows=rows, api_calls=0)
