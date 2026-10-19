# SPDX-License-Identifier: GPL-3.0-only
import argparse
import json
import sys
from .core import Registry


def main():
    parser = argparse.ArgumentParser(description='Auzix Assigns — read-only merged locations')
    parser.add_argument('-c', '--config', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    for name in ('ls', 'inspect'):
        sub.add_parser(name).add_argument('path', nargs='?', default='')
    sub.add_parser('mount').add_argument('mountpoint')
    args = parser.parse_args()
    try:
        registry = Registry.load(args.config)
        if args.command == 'check':
            print(json.dumps({'valid': True, 'assigns': list(registry.sources), 'mode': 'read-only'}))
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
