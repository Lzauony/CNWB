"""CNWB public reference release: offline requests, validation and scoring."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import protocol
import scoring
import intake
import leaderboard


def text(path):
    # Preserve CRLF and BOM; these are part of the work hash.
    return Path(path).read_bytes().decode('utf-8')


def write(path, value):
    target = Path(path).resolve()
    protected = [ROOT / name for name in ('benchmark', 'tools', 'schemas', 'docs', 'examples', 'results')]
    if target.is_relative_to(ROOT) and not target.is_relative_to(ROOT / 'out'):
        raise ValueError('Inside this release, save outputs only under out/')
    if any(target.is_relative_to(p) for p in protected):
        raise ValueError('Cannot overwrite release materials')
    if target.exists():
        raise ValueError('Output exists; choose a new path')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def check():
    manifest_path = ROOT / 'tools/manifests/release.json'
    manifest = scoring.read(manifest_path)
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
              and not any(x in p.relative_to(ROOT).parts for x in ('.git', '__pycache__', 'out', '.venv'))
              and p != manifest_path}
    scoring.require(actual == set(manifest['files']), 'Unexpected or missing release files')
    for name, digest in manifest['files'].items():
        scoring.require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                        'Release hash mismatch: ' + name)
    tasks = protocol.tasks()
    scoring.require(len(tasks) == 32 and len({t['id'] for t in tasks}) == 32, 'Task inventory mismatch')
    coverage = {d: sum(d in t['focus'] for t in tasks) for d in ('T1', 'T2', 'T3', 'T4', 'T5', 'T6')}
    scoring.require(list(coverage.values()) == [19, 16, 15, 19, 12, 15], 'Coverage mismatch')
    result = scoring.score(scoring.read(ROOT / 'examples/generation.json'),
                           scoring.read(ROOT / 'examples/evaluation.json'))
    scoring.require(result['scopes']['all32']['total'] == 60, 'Synthetic smoke check failed')
    for name, english in (('README.md', False), ('README.en.md', True)):
        readme = (ROOT / name).read_text(encoding='utf-8')
        table = readme.split(leaderboard.START)[1].split(leaderboard.END)[0].strip()
        scoring.require(table == leaderboard.markdown(leaderboard.load(), english),
                        'Homepage leaderboard does not match public snapshot: ' + name)
    print(json.dumps(dict(verified=True, tasks=32, coverage=coverage, files=len(actual), api_calls=0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    sub.add_parser('tasks')
    p = sub.add_parser('leaderboard', help='Display the published two-judge average leaderboard')
    p.add_argument('--output', help='Save full-precision aggregate JSON instead of printing the table')
    p = sub.add_parser('prompt')
    p.add_argument('--task', required=True)
    p.add_argument('--answer')
    p.add_argument('--stage', choices=('B1', 'B2'), default='B1')
    p.add_argument('--dimensions', nargs='+')
    p.add_argument('--output', required=True)
    p = sub.add_parser('receive')
    p.add_argument('--task', required=True)
    p.add_argument('--answer', required=True)
    p.add_argument('--response', required=True)
    p.add_argument('--stage', choices=('B1', 'B2'), default='B1')
    p.add_argument('--dimensions', nargs='+')
    p.add_argument('--output', required=True)
    p = sub.add_parser('score')
    p.add_argument('--generation', required=True)
    p.add_argument('--evaluation', required=True)
    p.add_argument('--missing-policy', choices=('strict', 'available-complete-works'), default='strict')
    p.add_argument('--missing-reason')
    p.add_argument('--output', required=True)
    p = sub.add_parser('average')
    p.add_argument('--left', required=True)
    p.add_argument('--right', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('rank')
    p.add_argument('files', nargs='+')
    p.add_argument('--scope', choices=('all32', 'prose28', 'planning4'), default='all32')
    p.add_argument('--metric', choices=('total', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6'), default='total')
    p.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'check':
        check()
        return
    if args.command == 'leaderboard':
        entries = leaderboard.load()
        if args.output:
            write(args.output, dict(scope='all32', judge_ids=list(leaderboard.JUDGES),
                                    weights=[0.5, 0.5], rows=entries))
        else:
            print(leaderboard.markdown(entries))
        return
    if args.command == 'tasks':
        titles = scoring.read(ROOT / 'benchmark/display_titles.json')
        for t in protocol.tasks():
            print(f"{t['id']}\t{titles[t['id']]}\t{','.join(t['focus'])}\t{t['delivery_form']}")
        return
    if args.command == 'prompt':
        if args.answer:
            value = protocol.judge_messages(args.task, text(args.answer), args.stage, args.dimensions)
        else:
            scoring.require(args.stage == 'B1' and not args.dimensions, 'Judge options require --answer')
            value = protocol.generation_messages(args.task)
    elif args.command == 'receive':
        value = intake.receive(args.task, text(args.answer), text(args.response), args.stage, args.dimensions)
    elif args.command == 'score':
        value = scoring.score(scoring.read(args.generation), scoring.read(args.evaluation),
                              args.missing_policy, args.missing_reason)
    elif args.command == 'average':
        value = scoring.average(scoring.read(args.left), scoring.read(args.right))
    else:
        value = scoring.rank([scoring.read(p) for p in args.files], args.scope, args.metric)
    write(args.output, value)
    print('Saved offline artifact. API calls: 0.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, StopIteration, OSError, TypeError) as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        sys.exit(2)
