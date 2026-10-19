# SPDX-License-Identifier: GPL-3.0-only
"""Small read-only pyfuse3 adapter; configuration is fixed for a mount session."""
import errno
import os
import stat
import time
import pyfuse3 as f
import trio


class AssignFS(f.Operations):
    def __init__(self, registry):
        super().__init__()
        self.registry = registry
        self.paths = {1: ()}
        self.inodes = {(): 1}
        self.handles = {}
        self.next_handle = 1
        self.started = time.time_ns()

    def inode(self, parts):
        if parts not in self.inodes:
            if len(self.paths) >= 100000:
                raise f.FUSEError(errno.ENOSPC)
            number = len(self.paths) + 1
            self.inodes[parts] = number
            self.paths[number] = parts
        return self.inodes[parts]

    async def io(self, function, *args):
        try:
            return await trio.to_thread.run_sync(function, *args)
        except OSError as error:
            raise f.FUSEError(error.errno or errno.EIO) from error

    async def getattr(self, inode, ctx=None):
        st = await self.io(self.registry.metadata, self.paths[inode])
        attr = f.EntryAttributes()
        attr.st_ino = inode
        attr.generation = 0
        attr.entry_timeout = attr.attr_timeout = 0
        attr.st_mode = (st.st_mode & ~0o222) if st else stat.S_IFDIR | 0o555
        attr.st_uid = st.st_uid if st else os.getuid()
        attr.st_gid = st.st_gid if st else os.getgid()
        attr.st_nlink = 2 if stat.S_ISDIR(attr.st_mode) else 1
        attr.st_size = st.st_size if st else 0
        attr.st_atime_ns = st.st_atime_ns if st else self.started
        attr.st_mtime_ns = st.st_mtime_ns if st else self.started
        attr.st_ctime_ns = st.st_ctime_ns if st else self.started
        attr.st_blksize = 4096
        attr.st_blocks = (attr.st_size + 511) // 512
        return attr

    async def lookup(self, parent_inode, name, ctx=None):
        parent = self.paths[parent_inode]
        if name == b'.':
            parts = parent
        elif name == b'..':
            parts = parent[:-1]
        else:
            parts = await self.io(self.registry.parts, '/'.join(parent + (os.fsdecode(name),)))
        # Validate before allocating an inode.
        await self.io(self.registry.metadata, parts)
        return await self.getattr(self.inode(parts))

    async def opendir(self, inode, ctx):
        if len(self.handles) >= 256:
            raise f.FUSEError(errno.EMFILE)
        parts = self.paths[inode]
        names = await self.io(self.registry.listing, parts)
        handle = self.next_handle
        self.next_handle += 1
        self.handles[handle] = (parts, names)
        return handle

    async def readdir(self, fh, start_id, token):
        parts, names = self.handles[fh]
        for offset in range(start_id, len(names)):
            name = names[offset]
            try:
                attr = await self.lookup(self.inode(parts), os.fsencode(name))
            except f.FUSEError as error:
                if error.errno == errno.ENOENT:
                    continue
                raise
            if not f.readdir_reply(token, os.fsencode(name), attr, offset + 1):
                break

    async def releasedir(self, fh):
        del self.handles[fh]

    async def open(self, inode, flags, ctx):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_TRUNC | os.O_APPEND):
            raise f.FUSEError(errno.EROFS)
        fd = await self.io(self.registry.open_read, self.paths[inode])
        return f.FileInfo(fh=fd, direct_io=True, keep_cache=False)

    async def read(self, fh, off, size):
        return await self.io(os.pread, fh, size, off)

    async def release(self, fh):
        os.close(fh)

    async def readlink(self, inode, ctx):
        # Do not turn a read-only union into an escape to a writable backing path.
        raise f.FUSEError(errno.ELOOP)


def mount(registry, path):
    registry.check_mount(path)
    if not os.path.isdir(path) or os.listdir(path):
        raise ValueError('Mountpoint must be an existing empty directory')
    f.init(AssignFS(registry), path, set(f.default_options) | {'fsname=auzix-assigns', 'ro', 'default_permissions', 'nodev', 'nosuid'})
    try:
        trio.run(f.main)
    finally:
        f.close(unmount=True)
