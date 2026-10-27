import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from .records import Records, DEFAULT_TODAY

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Onboarding document and records utilities')
    parser.add_argument('--data', type=Path, default=ROOT / 'data')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inspect')
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--size', type=int, default=700)
    prepare.add_argument('--overlap', type=int, default=100)
    context = commands.add_parser('context')
    context.add_argument('--asker', required=True)
    context.add_argument('--target', required=True)
    context.add_argument('--today', type=date.fromisoformat, default=DEFAULT_TODAY)
    args = parser.parse_args()
    output = ROOT / 'artifacts'
    output.mkdir(exist_ok=True)
    if args.command in ('inspect', 'prepare'):
        from .documents import manifest, chunks
        if args.command == 'inspect':
            print(json.dumps(manifest(args.data), indent=2))
        else:
            entries = list(chunks(args.data, args.size, args.overlap))
            destination = output / f'chunks-{args.size}.jsonl'
            with destination.open('w', encoding='utf-8') as stream:
                for entry in entries:
                    stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
            print(f'Prepared {len(entries)} chunks: {destination}')
            print('Inspect tables and Arabic text before embedding. No vector index created yet.')
    else:
        outcome = 'context_prepared'
        try:
            result = Records(args.data).context(args.asker, args.target, args.today)
        except PermissionError as error:
            outcome = 'declined'
            result = {'outcome': outcome, 'message': str(error)}
        with (output / 'audit.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'ts': datetime.now(timezone.utc).isoformat(),
                'scenario_today': args.today.isoformat(), 'asker': args.asker,
                'record_used': args.target if outcome != 'declined' else None,
                'operation': 'context', 'outcome': outcome, 'docs_cited': []}) + '\n')
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
