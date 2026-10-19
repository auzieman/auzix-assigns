# Auzix Assigns — working read-only experiment

Amiga-inspired named locations backed by ordered directories. A real FUSE mount
presents their combined contents to ordinary Linux applications. Existing files
stay where they are. This is an initial filesystem prototype, not a boot-layout
replacement or an Amiga compatibility implementation.

## Try the disposable demo

Alpine dependencies: `py3-pyfuse3`, `py3-trio`, and working FUSE3 support.
Run as your normal desktop user, from this directory:

```sh
python3 examples/make_demo.py
python3 -m assignfs -c build/demo/assigns.json check
python3 -m assignfs -c build/demo/assigns.json ls Music:Albums
python3 -m assignfs -c build/demo/assigns.json inspect Music:readme.txt
python3 -m assignfs -c build/demo/assigns.json mount build/demo/view
```

The last command remains in the foreground. In another terminal or file manager,
open `build/demo/view/Music`: both collections appear together. The two files
named `readme.txt` resolve to the local copy. `inspect` reports both source paths
and stable path-derived IDs; these IDs are not file-content hashes and change
when a source path/name changes. No icons or persistent metadata database yet.

Unmount from another terminal:

```sh
fusermount3 -u "$PWD/build/demo/view"
```

On this workstation, fusermount3 can detach successfully but return a BusyBox
`umount --no-canonicalize` warning during cleanup. Check `mountpoint`/`mount`
before treating that as a mount failure; the acceptance test verifies actual
detachment. Do not delete fixture directories while mounted.

## Mapping configuration

See [examples/assigns.json](examples/assigns.json). Version 1 uses JSON with named
assigns and an ordered `sources` array. Sources must exist when starting; paths
must be absolute or use `~/`. Earlier sources win duplicate names. Directory
entries merge recursively; a winning file blocks lower directories with that name.
Case is significant. Hidden files are included. No background content hashing.

`Music:Albums/track` is understood by our CLI; other programs use the mounted
`Music/Albums/track` path. No global colon-path translation is installed.

The mount is read-only, including create, rename, unlink and metadata changes.
Symlinks are visible to lstat but following/reading their targets returns ELOOP;
this intentionally avoids presenting writable escape paths through the view.
Device/socket/FIFO opens are refused. Underlying permissions still apply, and
permission failures are reported rather than silently changing precedence.

Configuration is fixed for a session: edit and remount. Backing file additions
and removals are visible without remounting. Directory handles keep a bounded
name snapshot; attributes and regular-file reads bypass FUSE caching. Existing
file handles retain their opened file if a source disappears. Missing sources
are skipped; a different device/inode at a source root returns ESTALE and requires
remounting. All sources missing yields ENOENT. Nested mount replacement and
stalled network filesystems are not fully managed; use local fixture trees first.

Bounds: 64 assigns, 16 sources each, 64 levels below an assign, 10,000 unique names
per directory, 256 concurrent directory handles, and 100,000 session path inodes.
The inode map is bounded but not reclaimed until unmount. No assign references
or recursive mount/source overlap. Source IO runs in Trio worker threads, though
an unresponsive backing filesystem can still stall reads and shutdown.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 tests/mounted.py
```

The second test mounts disposable fixtures as an unprivileged user, checks real
ls/open calls, recursive merges, duplicates, refused writes, live changes, source
disappearance and open-handle lifetime, then verifies unmount and source hashes.
See [validation](docs/validation.md) for actual results and limitations.

Next: deliberate write-destination/copy-up semantics, reconnect controls, metadata
and icon associations, then an EFL assign editor. Newest-file duplicate policy,
GUI, APK, autostart and system path changes are not implemented.

Original implementation: GPL-3.0-only; see [LICENSE](LICENSE). Dependencies retain their own licenses.
