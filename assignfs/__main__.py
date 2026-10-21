# SPDX-License-Identifier: GPL-3.0-only
import argparse
import json
import sys
import os
import subprocess
from pathlib import Path
from .core import Registry


def main():
    parser = argparse.ArgumentParser(description='Auzix Assigns — read-only merged locations')
    parser.add_argument('-c', '--config', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    sub.add_parser('status')
    sub.add_parser('list')
    for name in ('ls', 'inspect'):
        sub.add_parser(name).add_argument('path', nargs='?', default='')
    sub.add_parser('mount').add_argument('mountpoint')
    path_parser = sub.add_parser('path')
    path_parser.add_argument('mountpoint')
    path_parser.add_argument('path')
    run_parser = sub.add_parser('exec')
    run_parser.add_argument('mountpoint')
    run_parser.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        registry = Registry.load(args.config)
        if args.command == 'check':
            print(json.dumps({'valid': True, 'assigns': list(registry.sources), 'mode': 'read-only'}))
        elif args.command in ('status', 'list'):
            print(json.dumps(registry.status(), indent=2))
        elif args.command in ('path', 'exec'):
            root = Path(args.mountpoint).resolve()
            if not os.path.ismount(root):
                raise ValueError('Expected a live assign mount')
            def translate(value):
                head = value.split(':', 1)[0]
                if ':' in value and any(head.casefold() == name.casefold() for name in registry.sources):
                    return str(root.joinpath(*registry.parts(value)))
                return value
            if args.command == 'path':
                result = translate(args.path)
                if result == args.path:
                    raise ValueError('Expected a known assign such as C:')
                print(result)
            else:
                command = args.argv
                if command and command[0] == '--': command = command[1:]
                if not command: raise ValueError('Expected a command')
                return subprocess.run([translate(value) for value in command]).returncode
        elif args.command == 'mount':
            from .fuse import mount
            mount(registry, args.mountpoint)
        else:
            parts = registry.parts(args.path)
            print(json.dumps(registry.listing(parts) if args.command == 'ls' else registry.inspect(parts), indent=2))
    except (OSError, ValueError, ImportError) as error:
        print('assignfs: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
