"""CNWB public reference release: offline requests, validation and scoring."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import protocol
import scoring
import intake
import leaderboard
import assembly
import maintenance


def text(path):
    # Preserve CRLF and BOM; these are part of the work hash.
    return Path(path).read_bytes().decode('utf-8')


def output_path(path):
    target = Path(path).resolve()
    if target.is_relative_to(ROOT) and not target.is_relative_to(ROOT / 'out'):
        raise ValueError('Inside this release, save outputs only under out/')
    if target.exists():
        raise ValueError('Output exists; choose a new path')
    return target


def write_many(items):
    targets = [(output_path(path), (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
               for path, value in items]
    scoring.require(len({path for path, _ in targets}) == len(targets), 'Output paths must be distinct')
    created = []
    try:
        for path, content in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                created.append(path)
                handle.write(content)
    except OSError:
        for path in created:
            path.unlink()
        raise


def write(path, value):
    write_many([(path, value)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('check', help='Check frozen materials, local links and offline behavior')
    p.add_argument('--release', action='store_true', help='Also require exact release file inventory and hashes')
    p = sub.add_parser('manifest', help='Preview or update reviewed software release manifests (requires Git)')
    p.add_argument('--version', required=True)
    p.add_argument('--write', action='store_true', help='Explicitly update only the two maintenance manifests')
    sub.add_parser('tasks')
    p = sub.add_parser('leaderboard', help='Display the published two-judge average leaderboard')
    p.add_argument('--output', help='Save full-precision aggregate JSON instead of printing the table')
    p = sub.add_parser('assemble', help='Assemble work files and B1/B2 responses from a local input list')
    p.add_argument('--input', required=True)
    p.add_argument('--generation-output', required=True)
    p.add_argument('--evaluation-output', required=True)
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
        print(json.dumps(maintenance.check(args.release)))
        return
    if args.command == 'manifest':
        print(json.dumps(maintenance.update_manifests(args.version, args.write), ensure_ascii=False))
        return
    if args.command == 'assemble':
        generation, evaluation = assembly.assemble(args.input)
        write_many([(args.generation_output, generation), (args.evaluation_output, evaluation)])
        print('Saved generation and evaluation records. API calls: 0.')
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
