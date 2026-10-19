# SPDX-License-Identifier: GPL-3.0-only
import errno
import os
from pathlib import Path
import tempfile
import unittest
from assignfs.core import Registry


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a, self.b = self.root/'a', self.root/'b'
        self.a.mkdir(); self.b.mkdir()
        (self.a/'same').write_text('first')
        (self.b/'same').write_text('second')
        (self.b/'unique').write_text('unique')
        for p in (self.a, self.b): (p/'nested').mkdir()
        (self.a/'nested/one').write_text('one')
        (self.b/'nested/two').write_text('two')
        self.r = Registry({'version': 1, 'assigns': {'Music': {'sources': [str(self.a), str(self.b)]}}})

    def test_union_and_priority(self):
        self.assertEqual(self.r.listing(('Music',)), ['nested', 'same', 'unique'])
        fd = self.r.open_read(('Music', 'same'))
        try: self.assertEqual(os.read(fd, 50), b'first')
        finally: os.close(fd)
        self.assertEqual(len(self.r.inspect(('Music','same'))), 2)

    def test_nested_merge(self):
        self.assertEqual(self.r.listing(('Music','nested')), ['one','two'])

    def test_file_blocks_directory(self):
        (self.a/'block').write_text('file')
        (self.b/'block').mkdir(); (self.b/'block/child').write_text('hidden')
        with self.assertRaises(OSError) as caught: self.r.metadata(('Music','block','child'))
        self.assertEqual(caught.exception.errno, errno.ENOTDIR)

    def test_directory_beats_file(self):
        (self.b/'nested').rename(self.b/'elsewhere')
        (self.b/'nested').write_text('hidden')
        self.assertEqual(self.r.listing(('Music','nested')), ['one'])

    def test_missing_branch_and_existing_handle(self):
        fd = self.r.open_read(('Music','same'))
        self.a.rename(self.root/'offline')
        try: self.assertEqual(os.read(fd,50), b'first')
        finally: os.close(fd)
        fd = self.r.open_read(('Music','same'))
        try: self.assertEqual(os.read(fd,50), b'second')
        finally: os.close(fd)

    def test_replacement_is_stale(self):
        self.a.rename(self.root/'offline'); self.a.mkdir()
        with self.assertRaises(OSError) as caught: self.r.listing(('Music',))
        self.assertEqual(caught.exception.errno, errno.ESTALE)

    def test_symlink_refused(self):
        (self.a/'link').symlink_to(self.b/'same')
        with self.assertRaises(OSError) as caught: self.r.open_read(('Music','link'))
        self.assertEqual(caught.exception.errno, errno.ELOOP)

    def test_traversal_and_depth(self):
        for path in ['Music:../secret', 'Music/a/../b', 'Music/'+'/'.join(['a']*65)]:
            with self.assertRaises(OSError): self.r.parts(path)
        self.assertEqual(self.r.parts('Music:nested/one'), ('Music','nested','one'))

    def test_no_mount_recursion(self):
        for mount in [self.a, self.a/'mount', self.root]:
            with self.assertRaises(ValueError): self.r.check_mount(mount)

    def test_config_rejects_write_policy(self):
        with self.assertRaises(ValueError):
            Registry({'version':1,'assigns':{'Music':{'sources':[str(self.a)],'destination':str(self.a)}}})

    def test_changes_are_visible(self):
        (self.b/'new').write_text('new')
        self.assertIn('new', self.r.listing(('Music',)))
        (self.a/'same').unlink()
        self.assertEqual(self.r.inspect(('Music','same'))[0]['source'], str(self.b))

    def test_permission_error_not_hidden(self):
        self.a.chmod(0)
        try:
            with self.assertRaises(PermissionError): self.r.listing(('Music',))
        finally: self.a.chmod(0o700)
