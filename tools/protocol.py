"""Standalone reconstruction of the frozen SJ6 r0 requests; no network access."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda text:hashlib.sha256(text.encode('utf-8')).hexdigest()

@lru_cache(maxsize=300)
def _read(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))

def tasks():return _read('benchmark/tasks.json')
def task(key):return next(t for t in tasks() if t['id']==key)

def generation_messages(task_id):
    return json.loads(json.dumps(_read(f'benchmark/prompts/generation/{task_id}.json'),ensure_ascii=False))

def judge_messages(task_id,answer,stage='B1',assigned=None):
    if stage not in ('B1','B2'):raise ValueError('Only B1/B2 are part of this release')
    if stage=='B2' and (not assigned or len(set(assigned))!=len(assigned)):raise ValueError('B2 requires unique eligible dimensions')
    key=task_id+'-'+stage+('' if stage=='B1' else '-'+''.join(sorted(assigned)))
    messages=json.loads(json.dumps(_read(f'benchmark/prompts/judge/{key}.json'),ensure_ascii=False))
    value=json.loads(messages[1]['content']);h=sha(answer)
    value['input']['answer']=answer;value['input']['answer_sha256']=h
    value['output_contract']['schema']['properties']['answer_sha256']['enum']=[h]
    value['output_contract']['template']['answer_sha256']=h
    messages[1]['content']=json.dumps(value,ensure_ascii=False)
    return messages

def response_schema(t,answer,step='main',stage='B1',assigned=None):
    if step!='main':raise ValueError('Story32 uses main-stage artifacts only')
    return json.loads(judge_messages(t['id'],answer,stage,assigned)[1]['content'])['output_contract']['schema']

def task_evidence_text(t,step='main'):
    return json.loads(_read(f'benchmark/prompts/judge/{t["id"]}-B1.json')[1]['content'])['input']['task_evidence_text']

def source_relation(t):
    if t['support']=='opening':return 'source_continuation'
    if t['type']=='R':return 'revision_comparison'
    return 'source_transformation' if t['source'] else None
