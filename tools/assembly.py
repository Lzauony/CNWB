"""Assemble local works and selected responses without model calls or retries."""
from pathlib import Path

import intake
import protocol
import scoring
import sj6_kernel as sj


def read_text(path):
    # Text bytes are material: retain CRLF, BOM, titles and outer whitespace.
    return Path(path).read_bytes().decode('utf-8')


def response(path, task_id, answer, stage, dimensions=None):
    raw = read_text(path)
    selected, _ = intake.parse(raw)
    if isinstance(selected, dict) and 'raw_text' in selected and 'review' in selected:
        scoring.require(isinstance(selected['raw_text'], str), 'Invalid receive evidence text')
        checked = intake.receive(task_id, answer, selected['raw_text'], stage, dimensions)
        scoring.require(selected['review'] == checked['review'], 'Receive evidence review was changed')
        scoring.require(selected.get('raw_sha256') == checked['raw_sha256'], 'Receive evidence hash mismatch')
    else:
        checked = intake.receive(task_id, answer, raw, stage, dimensions)
    return checked['review']


def assemble(path):
    path = Path(path).resolve()
    plan = scoring.read(path)
    scoring.require(isinstance(plan, dict), 'Assembly input must be an object')
    required = {'generation_id', 'model_id', 'evaluation_id', 'judge_id', 'revision', 'works'}
    scoring.require(required <= plan.keys(), 'Assembly input is missing required fields')
    scoring.require(set(plan) <= required | {'synthetic'}, 'Unknown assembly input field')
    for key in ('generation_id', 'model_id', 'evaluation_id', 'judge_id'):
        scoring.identifier(plan[key])
    scoring.require(type(plan['revision']) is int and plan['revision'] > 0, 'Invalid revision')
    scoring.require('synthetic' not in plan or type(plan['synthetic']) is bool, 'synthetic must be boolean')
    items = scoring.unique(plan['works'], 'task_id')
    scoring.require(set(items) <= {t['id'] for t in protocol.tasks()}, 'Unknown task')
    generation = dict(schema_version=1, benchmark_id=scoring.BENCHMARK,
                      id=plan['generation_id'], model_id=plan['model_id'], works=[])
    evaluation = dict(schema_version=1, benchmark_id=scoring.BENCHMARK,
                      id=plan['evaluation_id'], generation_id=plan['generation_id'],
                      judge_id=plan['judge_id'], protocol_id='sj6-v1', revision=plan['revision'], reviews=[])
    if 'synthetic' in plan:
        generation['synthetic'] = evaluation['synthetic'] = plan['synthetic']

    def local_file(value):
        scoring.require(isinstance(value, str) and value.strip(), 'File path must be a nonempty string')
        return path.parent / value

    for task_id, item in items.items():
        scoring.require(set(item) <= {'task_id', 'answer_file', 'B1_file', 'B2_file'},
                        'Unknown work field: ' + task_id)
        scoring.require('answer_file' in item, 'Missing answer_file: ' + task_id)
        scoring.require('B2_file' not in item or 'B1_file' in item, 'B2 requires B1: ' + task_id)
        answer = read_text(local_file(item['answer_file']))
        digest = protocol.sha(answer)
        generation['works'].append(dict(task_id=task_id, text=answer, sha256=digest))
        if 'B1_file' not in item:
            continue
        b1 = response(local_file(item['B1_file']), task_id, answer, 'B1')
        row = dict(task_id=task_id, answer_sha256=digest, B1=b1)
        if 'B2_file' in item:
            eligible = sj.qualified(b1) if answer.strip() else []
            scoring.require(bool(eligible), 'Unsolicited B2: ' + task_id)
            row['B2'] = response(local_file(item['B2_file']), task_id, answer, 'B2', eligible)
        evaluation['reviews'].append(row)
    # Missing B1/B2 is allowed and remains missing; invalid supplied material is rejected.
    scoring.validate_evaluation(evaluation, generation)
    return generation, evaluation
