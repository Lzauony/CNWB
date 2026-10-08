import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import protocol
import scoring
import intake
import sj6_kernel as sj


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.g = scoring.read(ROOT / 'examples/generation.json')
        self.e = scoring.read(ROOT / 'examples/evaluation.json')
        self.answer = (ROOT / 'examples/answer.txt').read_bytes().decode('utf-8')
        self.b1 = scoring.read(ROOT / 'examples/B1.json')
        self.b2 = scoring.read(ROOT / 'examples/B2.json')

    def projections(self):
        return scoring.validate_evaluation(self.e, self.g)

    def test_inventory_and_dimension_coverage(self):
        self.assertEqual(len(protocol.tasks()), 32)
        self.assertEqual([sum(d in t['focus'] for t in protocol.tasks()) for d in ('T1','T2','T3','T4','T5','T6')],
                         [19,16,15,19,12,15])
        self.assertTrue(all(len(set(t['focus'])) == 3 for t in protocol.tasks()))

    def test_all_generation_messages_are_copied_exactly(self):
        for t in protocol.tasks():
            self.assertEqual(protocol.generation_messages(t['id']),
                             scoring.read(ROOT / f"benchmark/prompts/generation/{t['id']}.json"))

    def test_all_b2_subsets_and_material_binding(self):
        import itertools
        for t in protocol.tasks():
            for n in range(1, 4):
                for dims in itertools.combinations(t['focus'], n):
                    v = json.loads(protocol.judge_messages(t['id'], self.answer, 'B2', list(dims))[1]['content'])
                    self.assertEqual(set(v['output_contract']['template']['dimensions']), set(dims))
                    self.assertEqual(v['input']['answer_sha256'], protocol.sha(self.answer))
                    self.assertNotIn('B1', v['input'])

    def test_hash_mismatch_rejected(self):
        self.g['works'][0]['text'] += 'changed'
        with self.assertRaisesRegex(ValueError, 'hash'):
            scoring.validate_generation(self.g)

    def test_review_for_other_work_rejected(self):
        self.e['reviews'][0]['answer_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.projections()

    def test_duplicate_task_rejected(self):
        self.g['works'].append(self.g['works'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            scoring.validate_generation(self.g)

    def test_wrong_material_and_stage_rejected(self):
        for field, value in [('task_sha256', '0'*64), ('source_sha256','0'*64), ('stage','B2')]:
            bad = copy.deepcopy(self.b1)
            bad[field] = value
            with self.assertRaises(ValueError):
                sj.project(protocol.task('A15'), self.answer, bad)

    def test_invalid_grade_types_rejected(self):
        for value in (True, 3.0, '3', 0, 5, 99):
            bad = copy.deepcopy(self.b1)
            bad['dimensions']['T1']['grade'] = value
            with self.assertRaises(ValueError):
                sj.project(protocol.task('A15'), self.answer, bad)

    def test_b2_is_independent_and_replaces_not_maximizes(self):
        p = sj.project(protocol.task('A15'), self.answer, self.b1, self.b2)
        self.assertEqual(p['final_grades'], {d: v['grade'] for d, v in self.b2['dimensions'].items()})
        self.assertIn(1, p['final_grades'].values())
        self.assertIn(5, p['final_grades'].values())
        self.assertIn(None, p['final_grades'].values())

    def test_required_b2_missing_never_gets_a_grade(self):
        p = sj.project(protocol.task('A15'), self.answer, self.b1)
        self.assertTrue(p['needs_B2'])
        self.assertTrue(all(v is None for v in p['final_grades'].values()))
        self.assertFalse(scoring.complete(p))

    def test_unrequested_b2_rejected(self):
        for v in self.b1['dimensions'].values():
            v['grade'] = 3
        with self.assertRaisesRegex(ValueError, 'Unsolicited'):
            sj.project(protocol.task('A15'), self.answer, self.b1, self.b2)

    def test_complete_score_and_planning_no_total(self):
        result = scoring.score(self.g, self.e)
        self.assertEqual(result['scopes']['all32']['total'], 60)
        self.assertEqual(result['scopes']['prose28']['total'], 60)
        self.assertIsNone(result['scopes']['planning4']['total'])
        self.assertEqual(result['scopes']['planning4']['dimensions']['T4']['n'], 0)

    def test_one_null_excludes_whole_work_not_only_one_dimension(self):
        review = next(r for r in self.e['reviews'] if r['task_id'] == 'A15')
        review['B1']['dimensions']['T1']['grade'] = None
        result = scoring.score(self.g, self.e)
        self.assertEqual(result['scopes']['all32']['n'], 31)
        self.assertIsNone(result['scopes']['all32']['total'])
        for d in protocol.task('A15')['focus']:
            self.assertEqual(result['scopes']['all32']['dimensions'][d]['n'],
                             sum(d in t['focus'] for t in protocol.tasks()) - 1)

    def test_available_work_policy_needs_reason_and_keeps_coverage(self):
        self.e['reviews'] = [r for r in self.e['reviews'] if r['task_id'] != 'A15']
        with self.assertRaises(ValueError):
            scoring.score(self.g, self.e, 'available-complete-works')
        result = scoring.score(self.g, self.e, 'available-complete-works', 'Explicit example policy')
        self.assertEqual(result['scopes']['all32']['total'], 60)
        self.assertFalse(result['scopes']['all32']['complete'])
        self.assertEqual(result['scopes']['all32']['excluded_tasks'][0]['task_id'], 'A15')

    def test_incomplete_non_delivery_and_conflict_are_separate(self):
        for state in ('incomplete', 'non_delivery'):
            bad = copy.deepcopy(self.b1)
            bad['delivery'] = state
            p = sj.project(protocol.task('A15'), self.answer, bad)
            self.assertEqual(p['delivery_state'], state)
            self.assertFalse(scoring.complete(p))
        self.b2['delivery'] = 'non_delivery'
        p = sj.project(protocol.task('A15'), self.answer, self.b1, self.b2)
        self.assertEqual(p['delivery_state'], 'delivery_conflict')
        self.assertTrue(all(v is None for v in p['final_grades'].values()))

    def test_semantic_diagnostic_does_not_rewrite_a_grade(self):
        review = self.e['reviews'][0]['B1']
        for d in review['dimensions'].values():
            d['evidence'][0]['quote'] = '不存在的引文'
        p = self.projections()[self.e['reviews'][0]['task_id']]
        self.assertTrue(p['diagnostics'])
        self.assertTrue(all(v == 3 for v in p['final_grades'].values()))

    def test_receive_fence_bom_and_identical_duplicates(self):
        raw = json.dumps(self.b1, ensure_ascii=False)
        raw = raw[:-1] + ',"stage":"B1"}'
        result = intake.receive('A15', self.answer, '\ufeff  ```json\n' + raw + '\n```  ')
        self.assertEqual(result['review'], self.b1)
        self.assertTrue(any(c['action'] == 'identical_duplicate_merged' for c in result['normalizations']))

    def test_conflicting_or_different_type_duplicates_rejected(self):
        for raw in ('{"x":1,"x":true}', '{"x":1,"x":1.0}', '{"x":1,"x":2}'):
            with self.assertRaises(ValueError):
                intake.parse(raw)

    def test_mixed_truncated_and_nonfinite_json_rejected(self):
        for raw in ('prefix {}', '{} trailing', '{', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                intake.parse(raw)

    def test_descriptive_tolerance_keeps_supplements(self):
        bad = copy.deepcopy(self.b1)
        del bad['dimensions']['T1']['achievement']
        bad['dimensions']['T1']['extra_note'] = {'nested': 'preserved'}
        result = intake.receive('A15', self.answer, json.dumps(bad, ensure_ascii=False))
        self.assertEqual(result['review']['dimensions']['T1']['achievement'], '')
        self.assertEqual(result['supplements']['extra_fields'][0]['value'], {'nested': 'preserved'})
        self.assertEqual(result['review']['dimensions']['T1']['grade'], 4)

    def test_extra_dimension_or_missing_grade_not_repaired(self):
        for mode in ('extra_dimension', 'missing_grade'):
            bad = copy.deepcopy(self.b1)
            if mode == 'extra_dimension':
                bad['dimensions']['T2'] = copy.deepcopy(bad['dimensions']['T1'])
            else:
                del bad['dimensions']['T1']['grade']
            with self.assertRaises(ValueError):
                intake.receive('A15', self.answer, json.dumps(bad, ensure_ascii=False))

    def test_average_uses_unrounded_independent_scores(self):
        a = scoring.score(self.g, self.e)
        self.e['judge_id'] = 'synthetic-judge-b'
        self.e['id'] = 'synthetic-evaluation-b'
        self.e['reviews'][0]['B1']['dimensions']['T3']['grade'] = 2
        b = scoring.score(self.g, self.e)
        result = scoring.average(a, b)
        self.assertEqual(result['scopes']['all32']['total'],
                         (a['scopes']['all32']['total'] + b['scopes']['all32']['total']) / 2)
        self.assertEqual(result['scopes']['all32']['dimensions']['T3'],
                         (a['scopes']['all32']['dimensions']['T3']['score'] + b['scopes']['all32']['dimensions']['T3']['score']) / 2)

    def test_average_missing_total_stays_null_and_no_common_subset(self):
        a = scoring.score(self.g, self.e)
        self.e['judge_id'] = 'synthetic-judge-b'
        self.e['reviews'].pop()
        b = scoring.score(self.g, self.e)
        result = scoring.average(a, b)
        self.assertIsNone(result['scopes']['all32']['total'])
        self.assertEqual([x['n'] for x in result['scopes']['all32']['judge_coverage']], [32,31])

    def test_average_different_works_or_same_judge_rejected(self):
        a = scoring.score(self.g, self.e)
        with self.assertRaises(ValueError):
            scoring.average(a, a)
        b = copy.deepcopy(a)
        b['judge_id'] = 'other'
        b['input_sha256']['generation'] = '0'*64
        with self.assertRaises(ValueError):
            scoring.average(a, b)

    def test_rank_precise_ties_and_null_last(self):
        a = scoring.score(self.g, self.e)
        rows = []
        for run, total in [('a',60.001), ('b',60.002), ('c',60.002), ('d',None)]:
            value = copy.deepcopy(a)
            value['generation_id'] = run
            value['scopes']['all32']['total'] = total
            rows.append(value)
        ranked = scoring.rank(rows)['rows']
        self.assertEqual([r['generation_id'] for r in ranked], ['b','c','a','d'])
        self.assertEqual([r['rank'] for r in ranked], [1,1,3,None])

    def test_cli_smoke_and_crlf_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            answer = Path(directory)/'answer.txt'
            answer.write_bytes('甲\r\n乙\ufeff'.encode('utf-8'))
            output = Path(directory)/'request.json'
            result = subprocess.run([sys.executable, '-B', str(ROOT/'cnwb.py'), 'prompt', '--task','A15',
                                     '--answer',str(answer),'--output',str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(scoring.read(output)[1]['content'])
            self.assertEqual(payload['input']['answer'], '甲\r\n乙\ufeff')
            result = subprocess.run([sys.executable, '-B', str(ROOT/'cnwb.py'), 'prompt', '--task','A15',
                                     '--output',str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
