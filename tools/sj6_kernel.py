"""SJ6 v1.0 structural validation, evidence diagnostics and B1/B2 projection."""
from copy import deepcopy
import hashlib
sha=lambda text:hashlib.sha256(text.encode()).hexdigest()
from protocol import response_schema, task_evidence_text, source_relation
def validate_schema(value, spec, path='$'):
    errors = []
    if 'enum' in spec and value not in spec['enum']:
        errors.append(path + ':enum')
    if 'enum' in spec and isinstance(value, (bool, float)):
        errors.append(path + ':enum_type')
    typ = spec.get('type')
    if typ == 'object':
        if not isinstance(value, dict):
            return errors + [path + ':object']
        errors += [path + '.' + k + ':missing' for k in spec['required'] if k not in value]
        errors += [path + '.' + k + ':extra' for k in value if k not in spec['properties']]
        for k in value.keys() & spec['properties'].keys():
            errors += validate_schema(value[k], spec['properties'][k], path + '.' + k)
    elif typ == 'array':
        if not isinstance(value, list):
            return errors + [path + ':array']
        for i, item in enumerate(value):
            errors += validate_schema(item, spec['items'], path + f'[{i}]')
    elif typ == 'string' and (not isinstance(value, str)):
        errors.append(path + ':string')
    elif typ == 'integer':
        if type(value) is not int:
            errors.append(path + ':integer')
        elif value < spec.get('minimum', value):
            errors.append(path + ':minimum')
    elif isinstance(typ, list) and value is not None and (type(value) is not int):
        errors.append(path + ':integer_or_null')
    return sorted(errors)

def normalize_review(value, spec):
    """Documented receive-only tolerance; never infer decisions or identity.

    The canonical provider schema stays strict. Every default is an empty
    descriptive value, not an assertion that a check was performed.
    """
    result, changes, supplements = (deepcopy(value), [], {})
    if not isinstance(result, dict):
        return (result, changes, supplements)

    def walk(node, schema, path):
        if schema.get('type') == 'object' and isinstance(node, dict):
            if path != '$.dimensions':
                for key in list(node):
                    if key not in schema['properties']:
                        supplements.setdefault('extra_fields', []).append(dict(parent_path=path, key=key, value=deepcopy(node.pop(key))))
                        changes.append(dict(path=path, key=key, action='extra_to_supplement'))
            for key, child in schema['properties'].items():
                where = path + '.' + key
                empty = '' if child.get('type') == 'string' else [] if child.get('type') == 'array' else None
                if 'enum' not in child and empty is not None and (key not in node or node[key] is None):
                    action = 'missing_to_empty' if key not in node else 'null_to_empty'
                    node[key] = deepcopy(empty)
                    changes.append(dict(path=where, action=action))
                if key in node:
                    walk(node[key], child, where)
        elif schema.get('type') == 'array' and isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, schema['items'], path + f'[{i}]')
    walk(result, spec, '$')
    return (result, changes, supplements)

def validate(t, step, stage, answer, review, assigned=None):
    errors = validate_schema(review, response_schema(t, answer, step, stage, assigned))
    if isinstance(review, dict) and review.get('answer_sha256') != sha(answer):
        errors.append('answer_sha256:mismatch')
    if isinstance(review, dict):
        for key, text in [('source', t['source']), ('task', task_evidence_text(t, step))]:
            if review.get(key + '_sha256') != sha(text):
                errors.append(key + '_sha256:mismatch')
    return errors

def material_texts(t, answer):
    return dict(answer=answer, source=t['source'] if t else '', task=task_evidence_text(t) if t else '')

def quote_spans(text, quote):
    """All exact Unicode code-point intervals; offsets are generated, not model arithmetic."""
    if not quote.strip():
        return []
    spans, start = ([], 0)
    while True:
        start = text.find(quote, start)
        if start < 0:
            return spans
        spans.append([start, start + len(quote)])
        start += 1

def disjoint_pair(evidence, answer):
    located = [(e['quote'], quote_spans(answer, e['quote'])) for e in evidence if e['part'] == 'answer']
    return any((q != r and (b <= c or d <= a) for i, (q, spans) in enumerate(located) for r, others in located[i + 1:] for a, b in spans for c, d in others))

def evidence_locations(review, answer, t=None):
    texts = material_texts(t, answer)

    def locate(items):
        return [dict(index=i, part=e['part'], quote=e['quote'], material_sha256=sha(texts[e['part']]), spans=quote_spans(texts[e['part']], e['quote'])) for i, e in enumerate(items)]
    return {**{d: dict(evidence=locate(v['evidence']), relations=[x['evidence_indices'] for x in v['relations']], issues=[x['evidence_indices'] for x in v['issues']]) for d, v in review['dimensions'].items()}, 'compliance': [locate(x['evidence']) for x in review['compliance']]}

def referenced_evidence(v, item):
    return [v['evidence'][i] for i in item['evidence_indices'] if 0 <= i < len(v['evidence'])]

def diagnostics(review, answer, t=None):
    notes = []
    texts = material_texts(t, answer)
    for d, v in review['dimensions'].items():

        def add(code):
            notes.append(d + ':' + code)
        g = v['grade']
        if g is None:
            if not v['unassessable_reason'].strip():
                add('null_reason_empty')
        else:
            if v['unassessable_reason'].strip():
                add('numeric_grade_with_null_reason')
            for key in ('achievement', 'mechanism', 'scope', 'limitation'):
                if not v[key].strip():
                    add('reasoning_' + key + '_empty')
            if not v['evidence']:
                add('evidence_empty')
            if not any((e['part'] == 'answer' and quote_spans(answer, e['quote']) for e in v['evidence'])):
                add('answer_evidence_missing')
            if v['expression']['state'] == 'not_assessable':
                add('numeric_grade_expression_not_assessable')
            for key in ('distribution', 'basis'):
                if not v['expression'][key].strip():
                    add('expression_' + key + '_empty')
            if review['delivery'] == 'non_delivery':
                add('non_delivery_with_grade')
        for e in v['evidence']:
            matches = quote_spans(texts[e['part']], e['quote'])
            if not e['quote'].strip():
                add('quote_empty')
            elif not matches:
                add('quote_not_found')
            elif len(matches) > 1:
                add('quote_location_ambiguous')
            if not e['effect'].strip():
                add('evidence_effect_empty')
        quotes = [(e['part'], e['quote']) for e in v['evidence'] if e['quote'].strip()]
        if len(quotes) != len(set(quotes)):
            add('duplicate_evidence')
        for name in ('issues', 'relations'):
            for i, item in enumerate(v[name]):
                prefix = f'{name}.{i}:'
                refs = item['evidence_indices']
                if not refs:
                    add(prefix + 'evidence_indices_empty')
                if any((n < 0 or n >= len(v['evidence']) for n in refs)):
                    add(prefix + 'evidence_index_out_of_range')
                if len(refs) != len(set(refs)):
                    add(prefix + 'duplicate_evidence_index')
                if name == 'issues':
                    for key in ('claim', 'impact'):
                        if not item[key].strip():
                            add(prefix + key + '_empty')
                    continue
                ev = referenced_evidence(v, item)
                if not item['link'].strip():
                    add(prefix + 'link_empty')
                if item['relation'] == 'within_answer':
                    if not disjoint_pair(ev, answer):
                        add(prefix + 'cross_passage_evidence_insufficient')
                else:
                    if t is None or not t['source'] or item['relation'] != source_relation(t):
                        add(prefix + 'source_relation_mismatch')
                    if not all((any((e['part'] == part and quote_spans(texts[part], e['quote']) for e in ev)) for part in ('source', 'answer'))):
                        add(prefix + 'source_answer_evidence_insufficient')
        argument_fields = ('achievement', 'mechanism', 'scope', 'above_three', 'limitation', 'above_four')
        arguments = [(k, v.get(k, '').strip()) for k in argument_fields if len(v.get(k, '').strip()) >= 12]
        for i, (key, value) in enumerate(arguments):
            for other, text in arguments[i + 1:]:
                if value == text:
                    add('repeated_argument:' + key + ':' + other)
        if g is not None and g >= 4:
            if not v['above_three'].strip() or v['expression']['state'] not in ('controlled', 'localized'):
                add('four_proof_conflict')
            if d == 'T6' and (not v['given'].strip()):
                add('distinctiveness_given_empty')
        if g == 5:
            if not v.get('above_four', '').strip():
                add('five_proof_conflict')
            if not disjoint_pair(v['evidence'], answer):
                add('five_evidence_insufficient')
            if v['expression']['state'] == 'localized' and (not any((i['severity'] == 'local' and i['claim'].strip() and i['impact'].strip() and any((quote_spans(answer, e['quote']) for e in referenced_evidence(v, i) if e['part'] == 'answer')) for i in v['issues']))):
                add('localized_five_impact_missing')
    if t and t['type'] == 'R' and any((v['grade'] is not None for v in review['dimensions'].values())):
        if not any((r['relation'] == 'revision_comparison' and all((any((e['part'] == part and quote_spans(texts[part], e['quote']) for e in referenced_evidence(v, r))) for part in ('source', 'answer'))) for v in review['dimensions'].values() for r in v['relations'])):
            notes.append('revision_source_comparison_missing')
    for i, c in enumerate(review['compliance']):
        if not c['requirement'].strip():
            notes.append(f'compliance.{i}:requirement_empty')
        for e in c['evidence']:
            if not e['quote'].strip():
                notes.append(f'compliance.{i}:quote_empty')
            elif not quote_spans(texts[e['part']], e['quote']):
                notes.append(f'compliance.{i}:quote_not_found')
            if not e['effect'].strip():
                notes.append(f'compliance.{i}:evidence_effect_empty')
    for d, v in review['dimensions'].items():
        if v['grade'] not in (4, 5):
            continue
        above = v.get('above_three', '')
        if any((p in above for p in ('成熟三级只需', '成熟三级仅要求', '成熟完成只需', '三级只要'))):
            notes.append(d + ':mature_baseline_wording_review')
        if any((p in v.get('limitation', '') for p in ('链条未断', '未致推断链断裂', '未切断', '不影响基本成立'))):
            notes.append(d + ':limitation_gain_link_review')
        if above.strip() and above.strip() in (v.get('achievement', '').strip(), v.get('mechanism', '').strip()):
            notes.append(d + ':above_three_repeats_existing_reason')
        if any((i.get('severity') in ('important', 'core') for i in v['issues'])):
            notes.append(d + ':high_grade_with_major_issue_review')
    return list(dict.fromkeys(notes))

def project(t, answer, b1, b2=None, step='main'):
    errors = validate(t, step, 'B1', answer, b1)
    if errors:
        raise ValueError(errors)
    need = qualified(b1) if answer.strip() else []
    if b2 is not None:
        if not need:
            raise ValueError('Unsolicited B2')
        errors = validate(t, step, 'B2', answer, b2, need)
        if errors:
            raise ValueError(errors)
    final, states, sources = ({}, {}, {})
    for d, v in b1['dimensions'].items():
        if d in need and b2 is None:
            final[d], states[d], sources[d] = (None, 'awaiting_B2', None)
        else:
            r = b2 if d in need else b1
            final[d] = r['dimensions'][d]['grade']
            states[d] = 'unassessable' if final[d] is None else 'rated'
            sources[d] = r['stage']
    reviews = {'B1': b1, **({'B2': b2} if b2 is not None else {})}
    deliveries = {k: r['delivery'] for k, r in reviews.items()}
    disagreement = len(set(deliveries.values())) > 1
    delivery = 'non_delivery' if not answer.strip() or b1['delivery'] == 'non_delivery' else 'delivery_conflict' if b2 is not None and b2['delivery'] == 'non_delivery' else 'incomplete' if 'incomplete' in deliveries.values() else 'delivered'
    if delivery in ('non_delivery', 'delivery_conflict'):
        final = {d: None for d in final}
        states = {d: delivery for d in final}
        sources = {d: None for d in final}
        need = []
    stage_notes = {k: diagnostics(r, answer, t) for k, r in reviews.items()}
    notes = [n for ns in stage_notes.values() for n in ns]
    if disagreement:
        notes.append('delivery_stage_disagreement')
    return dict(final_grades=final, dimension_states=states, provenance=sources, needs_B2=need if b2 is None else [], delivery_state=delivery, stage_deliveries=deliveries, delivery_disagreement=disagreement, reported_grades={k: {d: v['grade'] for d, v in r['dimensions'].items()} for k, r in reviews.items()}, diagnostics=notes, stage_diagnostics=stage_notes, evidence_locations={k: evidence_locations(r, answer, t) for k, r in reviews.items()}, review_assurance=dict(format_valid=True, literary_verified=False, diagnostic_status='issues_recorded' if notes else 'no_mechanical_issue_detected'), formal_eligible=False)

def qualified(b1):
    if b1['delivery'] == 'non_delivery':
        return []
    return [d for d, v in b1['dimensions'].items() if v['grade'] == 4]
