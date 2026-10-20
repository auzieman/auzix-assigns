# SPDX-License-Identifier: GPL-3.0-only
"""Resolver independent of FUSE. No AROS implementation code is used."""
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def fail(code, message):
    raise OSError(code, message)


class Registry:
    def __init__(self, config):
        if set(config) - {'version', 'assigns'} or config.get('version') != 1:
            raise ValueError('Expected version 1 and assigns')
        assigns = config.get('assigns')
        if not isinstance(assigns, dict) or not 1 <= len(assigns) <= 64:
            raise ValueError('Use 1–64 assigns')
        self.sources = {}
        for name, spec in assigns.items():
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', name):
                raise ValueError('Invalid assign name: ' + name)
            if not isinstance(spec, dict) or set(spec) != {'sources'}:
                raise ValueError('Each assign needs only sources; writes are not supported yet')
            paths = spec['sources']
            if not isinstance(paths, list) or not 1 <= len(paths) <= 16:
                raise ValueError('Use 1–16 sources per assign')
            branches = []
            for raw in paths:
                if not isinstance(raw, str) or not os.path.isabs(os.path.expanduser(raw)):
                    raise ValueError('Source paths must be absolute (or start with ~/ )')
                path = os.path.abspath(os.path.expanduser(raw))
                # Pin existing roots: disappearance is allowed, replacement requires remount.
                st = os.stat(path, follow_symlinks=False)
                if not stat.S_ISDIR(st.st_mode):
                    raise ValueError('Source must be a real directory: ' + path)
                branches.append((path, (st.st_dev, st.st_ino)))
            if len({p for p, _ in branches}) != len(branches):
                raise ValueError('Duplicate source path')
            self.sources[name] = branches

    @classmethod
    def load(cls, filename):
        with open(filename) as f:
            return cls(json.load(f))

    def parts(self, value):
        if ':' in value:
            name, tail = value.split(':', 1)
            value = name + '/' + tail.lstrip('/')
        parts = tuple(value.strip('/').split('/')) if value.strip('/') else ()
        if any(p in ('', '.', '..') or '\x00' in p for p in parts):
            fail(errno.EINVAL, 'Invalid path component')
        if len(parts) > 65:
            fail(errno.ENAMETOOLONG, 'Maximum depth is 64 below an assign')
        if parts and parts[0] not in self.sources:
            fail(errno.ENOENT, 'Unknown assign')
        return parts

    def check_mount(self, mountpoint):
        mount = Path(mountpoint).resolve()
        for branches in self.sources.values():
            for source, _ in branches:
                root = Path(source).resolve()
                if mount == root or mount in root.parents or root in mount.parents:
                    raise ValueError('Mount and source must not contain one another')

    def branch_fd(self, source, relative):
        path, identity = source
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) != identity:
                fail(errno.ESTALE, 'Source identity changed; remount: ' + path)
            for component in relative:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            return fd
        except BaseException:
            os.close(fd)
            raise

    def candidates(self, parts, partial=False):
        """Keep inaccessible branches in priority order until the final lookup."""
        if not parts:
            return []
        branches = self.sources[parts[0]]
        for depth in range(len(parts)):
            matches = []
            for source in branches:
                try:
                    parent = self.branch_fd(source, parts[1:depth])
                    try:
                        st = os.fstat(parent) if depth == 0 else os.stat(parts[depth], dir_fd=parent, follow_symlinks=False)
                    finally:
                        os.close(parent)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    st = None
                matches.append((source, st))
            if not matches:
                fail(errno.ENOENT, 'No available source for path')
            known = [(source, st) for source, st in matches if st is not None]
            if not known:
                fail(errno.EACCES, 'Additional permissions required')
            if depth == len(parts) - 1:
                if matches[0][1] is None and not partial:
                    fail(errno.EACCES, 'Higher-priority source inaccessible; refusing fallback')
                return known
            if depth and matches[0][1] is None:
                fail(errno.EACCES, 'Cannot determine higher-priority directory')
            if not stat.S_ISDIR(known[0][1].st_mode):
                fail(errno.ENOTDIR, 'Winning entry is not a directory')
            branches = [source for source, st in matches if st is None or stat.S_ISDIR(st.st_mode)]

    def metadata(self, parts):
        if not parts:
            return None
        return self.candidates(parts, partial=len(parts) == 1)[0][1]

    def listing(self, parts):
        if not parts:
            return sorted(self.sources)
        matches = self.candidates(parts, partial=len(parts) == 1)
        if not stat.S_ISDIR(matches[0][1].st_mode):
            fail(errno.ENOTDIR, 'Not a directory')
        names = set()
        readable = 0
        for source, st in matches:
            if not stat.S_ISDIR(st.st_mode):
                continue
            try:
                fd = self.branch_fd(source, parts[1:])
                try:
                    with os.scandir(fd) as entries:
                        for entry in entries:
                            names.add(entry.name)
                            if len(names) > 10000:
                                fail(errno.EOVERFLOW, 'Directory exceeds 10000 unique entries')
                    readable += 1
                finally:
                    os.close(fd)
            except PermissionError:
                continue
        if not readable:
            fail(errno.EACCES, 'Additional permissions required')
        # Never present an ambiguous lower-priority file as the winning entry.
        visible = []
        for name in sorted(names):
            try:
                self.metadata(parts + (name,))
                visible.append(name)
            except (PermissionError, FileNotFoundError):
                continue
        return visible

    def status(self):
        result = {}
        for name, branches in self.sources.items():
            rows = []
            for source in branches:
                try:
                    fd = self.branch_fd(source, ())
                    os.close(fd)
                    state = 'available'
                except OSError as error:
                    state = {errno.EACCES: 'permission-required', errno.EPERM: 'permission-required',
                             errno.ENOENT: 'missing', errno.ESTALE: 'replaced-remount-required'}.get(error.errno, 'error')
                rows.append({'source': source[0], 'state': state})
            result[name] = rows
        return result

    def open_read(self, parts):
        source, st = self.candidates(parts)[0]
        if not stat.S_ISREG(st.st_mode):
            fail(errno.ELOOP if stat.S_ISLNK(st.st_mode) else errno.EACCES, 'Only regular files can be opened')
        parent = self.branch_fd(source, parts[1:-1])
        try:
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            actual = os.fstat(fd)
            if not stat.S_ISREG(actual.st_mode) or (actual.st_dev, actual.st_ino) != (st.st_dev, st.st_ino):
                os.close(fd)
                fail(errno.ESTALE, 'Entry changed during open; retry')
            return fd
        finally:
            os.close(parent)

    def inspect(self, parts):
        if not parts:
            return {'assigns': list(self.sources)}
        return [{'source': source[0], 'path': os.path.join(source[0], *parts[1:]),
                 'identity': hashlib.sha256((source[0] + '\0' + '/'.join(parts)).encode()).hexdigest()[:16],
                 'visible': i == 0, 'kind': 'directory' if stat.S_ISDIR(st.st_mode) else 'symlink' if stat.S_ISLNK(st.st_mode) else 'file',
                 'size': st.st_size} for i, (source, st) in enumerate(self.candidates(parts))]
