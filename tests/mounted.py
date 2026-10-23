# SPDX-License-Identifier: GPL-3.0-only
"""Real kernel FUSE acceptance against disposable fixtures; no user data."""
import errno
import hashlib
import json
import mmap
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

project = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='assigns-acceptance-') as tmp:
    root = Path(tmp)
    a,b,mount = [root/n for n in ('a','b','view')]
    for p in (a,b,mount): p.mkdir()
    for p in (a,b): (p/'nested').mkdir()
    (a/'same').write_bytes(b'first')
    (b/'same').write_bytes(b'second')
    (a/'nested/a').write_bytes(b'one')
    (b/'nested/b').write_bytes(b'two')
    (b/'unique').write_bytes(b'unique')
    (a/'loop').symlink_to('loop')
    (a/'lib.so.1').symlink_to('lib.so.1.2')
    (a/'lib.so.1.2').write_bytes(b'library')
    (a/'escape').symlink_to('../outside')
    (a/'absolute').symlink_to('/etc/passwd')
    (a/'nested/link').symlink_to('../lib.so.1')
    def hashes():
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for base in (a,b) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}
    before=hashes()
    config=root/'assigns.json'
    config.write_text(json.dumps({'version':1,'assigns':{'Music':{'sources':[str(a),str(b)]}}}))
    with (root/'mount.log').open('w+') as log:
        process=subprocess.Popen([sys.executable,'-m','assignfs','-c',str(config),'mount',str(mount)],cwd=project,stdout=log,stderr=log)
        try:
            for _ in range(100):
                if os.path.ismount(mount): break
                if process.poll() is not None: log.seek(0);raise RuntimeError(log.read())
                time.sleep(.05)
            assert os.path.ismount(mount),'mount timed out'
            assert os.statvfs(mount).f_flag & os.ST_RDONLY
            assert os.statvfs(mount).f_bavail == 0
            subprocess.run(['ls','-a',str(mount/'Music')],check=True)
            assert (mount/'Music:/same').read_bytes()==b'first'
            assert (mount/'music:/same').read_bytes()==b'first'
            assert (mount/'Music/same').read_bytes()==b'first'
            with (mount/'Music/same').open('rb') as mapped_file:
                with mmap.mmap(mapped_file.fileno(),0,access=mmap.ACCESS_READ) as mapped:
                    assert mapped[:]==b'first'
            assert sorted(p.name for p in (mount/'Music/nested').iterdir())==['a','b','link']
            for operation in [lambda:(mount/'Music/new').write_text('no'),lambda:(mount/'Music/same').unlink(),lambda:(mount/'Music/same').rename(mount/'Music/renamed')]:
                try: operation()
                except OSError as e: assert e.errno in (errno.EROFS,errno.EACCES)
                else: raise AssertionError('write succeeded')
            assert os.readlink(mount/'Music/lib.so.1') == 'lib.so.1.2'
            assert (mount/'Music/lib.so.1').read_bytes() == b'library'
            assert (mount/'Music/nested/link').read_bytes() == b'library'
            for link in ('escape', 'absolute'):
                try: os.readlink(mount/'Music'/link)
                except OSError as e: assert e.errno == errno.EACCES
                else: raise AssertionError('unsafe symlink exposed')
            try: (mount/'Music/loop').read_bytes()
            except OSError as e: assert e.errno==errno.ELOOP
            else: raise AssertionError('symlink followed')
            (b/'fresh').write_text('visible')
            assert (mount/'Music/fresh').read_text()=='visible'
            (b/'fresh').unlink()
            with (mount/'Music/same').open('rb') as opened:
                a.rename(root/'offline')
                assert opened.read()==b'first'
                assert (mount/'Music/same').read_bytes()==b'second'
                (root/'offline').rename(a)
            b.chmod(0)
            time.sleep(1.1)  # bounded metadata visibility lag
            try:
                assert (mount/'Music/same').read_bytes()==b'first'
                assert 'unique' not in os.listdir(mount/'Music')
                try: (mount/'Music/unique').read_bytes()
                except OSError as error: assert error.errno==errno.EACCES
                else: raise AssertionError('inaccessible priority silently bypassed')
            finally: b.chmod(0o700)
            assert hashes()==before,'backing file bytes changed'
            print('PASS: native ls/open, recursive union, priority, live changes, read-only operations, safe symlinks and escape refusal, source disappearance and open handle lifetime')
        finally:
            if os.path.ismount(mount):
                result = subprocess.run(['fusermount3','-u',str(mount)],capture_output=True,text=True,timeout=10)
                # Some Alpine fusermount builds detach successfully but fail mtab cleanup
                # when their external umount is BusyBox. Verify the actual mount state.
                if result.returncode:
                    assert not os.path.ismount(mount), result.stderr
                    print('NOTE: fusermount returned nonzero after successful detach (BusyBox mtab cleanup)')
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.terminate();process.wait(timeout=5)
            assert not os.path.ismount(mount)
            if process.returncode: log.seek(0);print(log.read());raise RuntimeError('mount process failed')
    print('PASS: clean unmount; fixture contents unchanged')
