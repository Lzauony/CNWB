import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import assembly
import intake
import maintenance
import protocol
import scoring


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.plan = scoring.read(ROOT / 'examples/run-input.json')
        for name in ('answer.txt', 'B1.json', 'B2.json'):
            (self.folder / name).write_bytes((ROOT / 'examples' / name).read_bytes())

    def run_plan(self):
        save(self.folder / 'input.json', self.plan)
        return assembly.assemble(self.folder / 'input.json')

    def test_example_keeps_null_and_whole_work_exclusion(self):
        generation, evaluation = self.run_plan()
        projected = scoring.validate_evaluation(evaluation, generation)['A15']
        self.assertEqual(projected['final_grades'], {'T1': 1, 'T3': 5, 'T6': None})
        result = scoring.score(generation, evaluation)
        self.assertEqual(result['scopes']['all32']['n'], 0)
        self.assertIsNone(result['scopes']['all32']['total'])

    def test_receive_evidence_is_revalidated(self):
        answer = assembly.read_text(self.folder / 'answer.txt')
        evidence = intake.receive('A15', answer, assembly.read_text(self.folder / 'B1.json'))
        save(self.folder / 'B1.json', evidence)
        self.run_plan()
        evidence['review']['dimensions']['T1']['grade'] = 3
        save(self.folder / 'B1.json', evidence)
        with self.assertRaisesRegex(ValueError, 'was changed'):
            self.run_plan()

    def test_text_hash_preserves_bom_and_crlf(self):
        answer = '\ufeff甲\r\n乙\r\n'
        (self.folder / 'answer.txt').write_bytes(answer.encode('utf-8'))
        self.plan['works'][0].pop('B1_file')
        self.plan['works'][0].pop('B2_file')
        generation, evaluation = self.run_plan()
        self.assertEqual(generation['works'][0]['text'], answer)
        self.assertEqual(generation['works'][0]['sha256'], protocol.sha(answer))
        self.assertEqual(evaluation['reviews'], [])

    def test_wrong_work_hash_is_rejected(self):
        (self.folder / 'answer.txt').write_bytes(b'changed work')
        with self.assertRaises(ValueError):
            self.run_plan()

    def test_missing_b2_remains_pending(self):
        self.plan['works'][0].pop('B2_file')
        generation, evaluation = self.run_plan()
        p = scoring.validate_evaluation(evaluation, generation)['A15']
        self.assertEqual(p['needs_B2'], ['T1', 'T3', 'T6'])
        self.assertTrue(all(v is None for v in p['final_grades'].values()))

    def test_duplicate_and_orphan_b2_are_rejected(self):
        self.plan['works'].append(copy.deepcopy(self.plan['works'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.run_plan()
        self.plan['works'].pop()
        self.plan['works'][0].pop('B1_file')
        with self.assertRaisesRegex(ValueError, 'B2 requires B1'):
            self.run_plan()

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'cnwb.py'), *map(str, args)],
                              cwd=self.folder, capture_output=True, text=True, encoding='utf-8')

    def test_cli_full32_assembly_and_scoring(self):
        generation = scoring.read(ROOT / 'examples/generation.json')
        evaluation = scoring.read(ROOT / 'examples/evaluation.json')
        reviews = {r['task_id']: r for r in evaluation['reviews']}
        self.plan['works'] = []
        for work in generation['works']:
            tid = work['task_id']
            (self.folder / (tid + '.txt')).write_bytes(work['text'].encode('utf-8'))
            save(self.folder / (tid + '.json'), reviews[tid]['B1'])
            self.plan['works'].append(dict(task_id=tid, answer_file=tid + '.txt', B1_file=tid + '.json'))
        save(self.folder / 'input.json', self.plan)
        g, e, score = [self.folder / name for name in ('generation.json', 'evaluation.json', 'score.json')]
        result = self.cli('assemble', '--input', self.folder / 'input.json',
                          '--generation-output', g, '--evaluation-output', e)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('score', '--generation', g, '--evaluation', e, '--output', score)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = scoring.read(score)
        self.assertEqual(output['scopes']['all32']['n'], 32)
        self.assertEqual(output['scopes']['all32']['total'], 60)
        self.assertIsNone(output['scopes']['planning4']['total'])

    def test_cli_preflights_both_output_paths(self):
        save(self.folder / 'input.json', self.plan)
        g, e = self.folder / 'generation.json', self.folder / 'existing.json'
        e.write_bytes(b'keep existing')
        result = self.cli('assemble', '--input', self.folder / 'input.json',
                          '--generation-output', g, '--evaluation-output', e)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(g.exists())
        self.assertEqual(e.read_bytes(), b'keep existing')
        result = self.cli('assemble', '--input', self.folder / 'input.json',
                          '--generation-output', g, '--evaluation-output', g)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(g.exists())


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        for name, value in [('benchmark/material.txt', b'frozen'), ('tools/example.py', b'pass\n'),
                            ('CITATION.cff', b'version: 1.0.3\n'),
                            ('results/published-leaderboard.json', b'{}')]:
            path = self.folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        source = dict(material_files={'benchmark/material.txt': maintenance.digest(self.folder / 'benchmark/material.txt')},
                      core_tools={'tools/example.py': maintenance.digest(self.folder / 'tools/example.py')},
                      public_results_sha256=maintenance.digest(self.folder / 'results/published-leaderboard.json'))
        save(self.folder / maintenance.SOURCE, source)
        old = dict(release='1.0.3', files={n: maintenance.digest(self.folder / n) for n in maintenance.inventory(self.folder)})
        save(self.folder / maintenance.RELEASE, old)
        (self.folder / 'CITATION.cff').write_bytes(b'version: 1.0.4\n')
        self.names = maintenance.inventory(self.folder)
        self.patch = mock.patch.object(maintenance, 'tracked_files', return_value=self.names)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_manifest_preview_does_not_write_and_binds_new_tools(self):
        tool = self.folder / 'tools/new.py'
        tool.write_bytes(b'pass\n')
        self.names.add('tools/new.py')
        before = (self.folder / maintenance.RELEASE).read_bytes()
        source, release, report = maintenance.manifest_plan(self.folder, '1.0.4')
        self.assertEqual((self.folder / maintenance.RELEASE).read_bytes(), before)
        self.assertIn('tools/new.py', json.loads(source)['core_tools'])
        self.assertEqual(json.loads(release)['files'][maintenance.SOURCE], hashlib.sha256(source).hexdigest())
        self.assertIn('tools/new.py', report['changed_files'])

    def test_changed_frozen_material_cannot_be_rehashed(self):
        (self.folder / 'benchmark/material.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Frozen material changed'):
            maintenance.manifest_plan(self.folder, '1.0.4')

    def test_untracked_and_private_files_cannot_enter_manifest(self):
        path = self.folder / '.env'
        path.write_bytes(b'not a real secret')
        with self.assertRaisesRegex(ValueError, 'untracked'):
            maintenance.manifest_plan(self.folder, '1.0.4')
        self.names.add('.env')
        with self.assertRaisesRegex(ValueError, 'private file'):
            maintenance.manifest_plan(self.folder, '1.0.4')

    def test_software_version_must_change_with_content(self):
        (self.folder / 'CITATION.cff').write_bytes(b'version: 1.0.3\n')
        (self.folder / 'tools/example.py').write_bytes(b'new = True\n')
        with self.assertRaisesRegex(ValueError, 'new software version'):
            maintenance.manifest_plan(self.folder, '1.0.3')

    def test_snapshot_update_requires_separate_review(self):
        (self.folder / 'results/published-leaderboard.json').write_bytes(b'{"changed":true}')
        with self.assertRaisesRegex(ValueError, 'provenance separately'):
            maintenance.manifest_plan(self.folder, '1.0.4')

    def test_dev_checks_do_not_require_current_software_hashes(self):
        original = scoring.read
        def stale_manifest(path):
            result = original(path)
            if Path(path) == ROOT / maintenance.RELEASE:
                result['files'] = {name: maintenance.digest(ROOT / name)
                                   for name in maintenance.inventory(ROOT) - {maintenance.RELEASE}}
                result['files']['README.md'] = '0' * 64
            return result
        with mock.patch.object(scoring, 'read', side_effect=stale_manifest):
            self.assertEqual(maintenance.check()['mode'], 'development')
            with self.assertRaisesRegex(ValueError, 'Release hash mismatch'):
                maintenance.check(release=True)


if __name__ == '__main__':
    unittest.main()
