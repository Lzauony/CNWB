"""Documented receive-only tolerance; original text is retained, never repaired."""
import hashlib
import json
import re

import protocol
import sj6_kernel as sj


class Pairs(list):
    pass


def same(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def parse(raw):
    text = raw.strip().lstrip('\ufeff').strip()
    changes = []
    if text != raw:
        changes.append(dict(path='$', action='outer_BOM_or_whitespace_removed'))
    fence = re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```', text, re.IGNORECASE)
    if fence:
        text = fence[1]
        changes.append(dict(path='$', action='whole_json_fence_removed'))

    def reject(value):
        raise ValueError('Non-finite JSON: ' + value)

    value = json.loads(text, object_pairs_hook=Pairs, parse_constant=reject)

    def resolve(node, path):
        if isinstance(node, Pairs):
            result = {}
            for key, value in node:
                value = resolve(value, path + '.' + key)
                if key in result:
                    if not same(result[key], value):
                        raise ValueError('Conflicting duplicate key: ' + path + '.' + key)
                    changes.append(dict(path=path + '.' + key, action='identical_duplicate_merged',
                                        value_sha256=protocol.sha(json.dumps(value, ensure_ascii=False))))
                else:
                    result[key] = value
            return result
        if isinstance(node, list):
            return [resolve(v, path + f'[{i}]') for i, v in enumerate(node)]
        return node

    return resolve(value, '$'), changes


def receive(task_id, answer, raw, stage='B1', assigned=None):
    received, changes = parse(raw)
    task = protocol.task(task_id)
    spec = protocol.response_schema(task, answer, stage=stage, assigned=assigned)
    canonical, normalization, supplements = sj.normalize_review(received, spec)
    errors = sj.validate(task, 'main', stage, answer, canonical, assigned)
    if errors:
        raise ValueError(errors)
    return dict(raw_text=raw, raw_sha256=protocol.sha(raw), received_value=received,
                review=canonical, canonical_sha256=protocol.sha(json.dumps(canonical, ensure_ascii=False)),
                normalizations=changes + normalization, supplements=supplements,
                diagnostics=sj.diagnostics(canonical, answer, task),
                assurance=dict(format_valid=True, literary_verified=False), api_calls=0)
