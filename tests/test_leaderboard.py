import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import leaderboard


class LeaderboardTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'results/published-leaderboard.json').read_bytes())

    def test_snapshot_average_and_coverage(self):
        entries = leaderboard.rows(self.data)
        self.assertEqual(len(entries), 24)
        self.assertEqual(len({r['model'] for r in entries}), 23)
        by_run = {r['generation_id']: r for r in entries}
        kimi = by_run['run-24']
        self.assertEqual(kimi['coverage'], [{'n': 32, 'planned': 32}, {'n': 31, 'planned': 32}])
        self.assertEqual(kimi['total'], 75.35175438596491 * 0.5 + 81.38137009189641 * 0.5)
        # A declared display aggregate is used, not the incomplete strict total.
        self.assertIsNone(next(b for b in self.data['boards'] if b['evaluation_id'] == 'run-24--judge-2')['scopes']['all32']['total'])

    def test_missing_judge_is_not_a_single_judge_average(self):
        self.data['boards'] = [b for b in self.data['boards'] if b['evaluation_id'] != 'run-01--judge-2']
        row = next(r for r in leaderboard.rows(self.data) if r['generation_id'] == 'run-01')
        self.assertIsNone(row['total'])
        self.assertIsNone(row['rank'])
        self.assertIsNone(row['coverage'][1])
        self.assertTrue(all(v is None for v in row['dimensions'].values()))

    def test_explicit_evaluation_and_default_run_selection(self):
        newer = copy.deepcopy(self.data['boards'][0])
        newer['evaluation_id'] = 'new-revision'
        newer['revision'] = 2
        newer['scopes']['all32']['total'] = 99
        self.data['boards'].append(newer)
        row = next(r for r in leaderboard.rows(self.data) if r['generation_id'] == 'run-01')
        self.assertEqual(row['judge_scores'][0], 99)
        self.data['catalog']['default_evaluations']['run-01'] = 'run-01--judge-1'
        row = next(r for r in leaderboard.rows(self.data) if r['generation_id'] == 'run-01')
        self.assertNotEqual(row['judge_scores'][0], 99)
        self.data['catalog']['additional_default_runs'] = []
        self.assertNotIn('run-11', [r['generation_id'] for r in leaderboard.rows(self.data)])

    def test_precise_sorting_and_competition_ties(self):
        self.data['catalog']['default_runs'] = dict(a='run-01', b='run-02', c='run-03')
        self.data['catalog']['additional_default_runs'] = []
        for b in self.data['boards']:
            if b['generation_id'] in ('run-01', 'run-02', 'run-03'):
                b['scopes']['all32']['total'] = 80.00001 if b['generation_id'] != 'run-03' else 80.0
        entries = leaderboard.rows(self.data)
        self.assertEqual([r['rank'] for r in entries], [1, 1, 3])
        self.assertEqual(entries[-1]['generation_id'], 'run-03')
        self.assertEqual(len({f"{r['total']:.2f}" for r in entries}), 1)

    def test_homepage_tables_match_snapshot(self):
        for name, english in (('README.md', False), ('README.en.md', True)):
            content = (ROOT / name).read_text(encoding='utf-8')
            table = content.split(leaderboard.START)[1].split(leaderboard.END)[0].strip()
            self.assertEqual(table, leaderboard.markdown(leaderboard.load(), english))


if __name__ == '__main__':
    unittest.main()
