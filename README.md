# Auzix Assigns — alpha

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

## Workstation starting pattern

[Initial Alpine config](configs/alpine-workstation.json) defines C:, Programs:,
Libraries: and Sys_Libraries: using this workstation’s existing directories.
See [mapping policy and limits](docs/workstation-mappings.md), including the
planned Libraries/System child and supported symbolic-link behavior.

## Mapping configuration

See [examples/assigns.json](examples/assigns.json). Version 1 uses JSON with named
assigns and an ordered `sources` array. Sources must exist when starting; paths
must be absolute or use `~/`. Earlier sources win duplicate names. Directory
entries merge recursively; a winning file blocks lower directories with that name.
Case is significant. Hidden files are included. No background content hashing.

`Music:Albums/track` is understood by our CLI; other programs use the mounted
`Music/Albums/track` path. No global colon-path translation is installed.

The mount is read-only, including create, rename, unlink and metadata changes.
Relative symlinks that stay within the same assign are followed through the
read-only view. Absolute links and relative links escaping an assign are blocked;
genuine link cycles report ELOOP.
Device/socket/FIFO opens are refused. Underlying permissions still apply, and
permission failures never silently change file precedence. Listings omit inaccessible
or ambiguous entries; `status` reports source-root access. An inaccessible higher-
priority source blocks fallback reads, while known higher-priority entries remain
available when a lower source is inaccessible. All sources denied returns EACCES.

Configuration is fixed for a session: edit and remount. Backing file additions
and removals are visible without remounting. Directory handles keep a bounded
name snapshot; attribute caching is disabled, and file pages are invalidated on open.
Mapped reads are supported for Eina/Efreet desktop-entry parsing. Already-open
files and mappings do not promise immediate coherence with external edits. Existing
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

## EFM and RAM-backed desktop trial

```sh
python3 examples/desktop_demo.py start
python3 -m assignfs -c build/desktop-demo/assigns.json status
python3 examples/desktop_demo.py stop
```

Start creates disposable Music/Programs fixtures, a tiny RAM source under existing
`/dev/shm`, and a read-only view at `build/desktop-demo/view`, then asks EFM to open
it. Programs contains explanatory text, not executable application launchers.
The RAM view is read-only too; this is not a separately mounted writable RAM disk.
No sudo, autostart, real collections or shell-path changes are involved.

The process runs at reduced scheduling priority, with 512 MiB virtual address-space
and 256-descriptor limits; backing IO uses at most four workers. Limits constrain
this demo but do not guarantee protection against every FUSE/kernel/desktop bug.
The demo remains mounted until stopped or the session ends. Stop leaves the disk
fixtures, removes its known RAM note, and preserves any user-added RAM files.

`list` and `status` print source-root health as JSON. They inspect a freshly loaded
configuration, not the live mount's pinned identities. Nested permission errors
remain operation-specific; there is not yet an EFM warning badge or status IPC.
A source may load if its root can be statted even when it cannot be listed; roots
hidden behind unsearchable parent directories still fail configuration loading.

## Real workstation dry run

```sh
python3 examples/workstation_trial.py start
python3 examples/workstation_trial.py status
python3 examples/workstation_trial.py stop
```

This separate trial exposes actual C, Programs, Libraries and Sys_Libraries
sources from configs/alpine-workstation.json at build/workstation-trial/view.
It verifies all four top-level merged listings, compares the E-control launcher
bytes to the installed source, and checks the kernel read-only flag before
requesting EFM. It does not run applications or attempt writes as tests.
The same process resource limits as the sample demo apply. RAM is excluded until
it has a dedicated capacity limit. Symlinks remain visible but cannot be followed;
this is browsing validation, not a replacement PATH or application launcher.
Stop the sample demo before starting this view to avoid confusion. No autostart.

## Cached browsing and colon names

Within the mounted view, ordinary commands now accept case-insensitive assign
prefixes: `ls C:`, `ls c:`, `ls Programs:`, `ls RAM:` and `ls C:/subdirectory`.
Canonical names remain in root listings (C, Programs, RAM); aliases do not create
duplicate icons. The names of files below an assign remain case-sensitive.
These are mount-relative aliases, not globally recognized shell paths.

From the project directory, translate arguments explicitly from anywhere:

```sh
python3 -m assignfs -c build/workstation-trial/assigns.json path build/workstation-trial/view C:
python3 -m assignfs -c build/workstation-trial/assigns.json exec build/workstation-trial/view -- ls Programs:
```

The wrapper translates complete arguments with known assign prefixes, without
shell evaluation. It does not translate embedded `--option=C:...` expressions,
globs, or install aliases into your shell. Ordinary `ls C:` outside the mounted
view still looks for a local directory named C:.

Directory snapshots reuse metadata during enumeration. A one-second LRU cache
holds at most 16,000 weighted entries (each directory member counts toward the
limit). Regular-file getattr and all file opens resolve fresh; cached listing
metadata can lag backing changes by up to a second. Existing directory handles
retain their snapshots. Failed operations are not cached. No content cache is
implemented here; mapped reads retain the previously documented kernel behavior.

The current local trial config includes RAM, backed by `build/ram-drive`: a
separate tmpfs capped at 2 GiB and 65,536 inodes, user-owned and mounted with
nosuid,nodev,noexec. It allocates on demand, not 2 GiB upfront. The backing folder
is writable directly; RAM: is read-only through Assigns. It is volatile and has
no boot persistence. Stopping Assigns does not erase or unmount that RAM backing.
The tracked workstation config stays portable; build/workstation-trial/assigns.json
records this host-specific RAM addition and is selected automatically when present.

## Root navigation aliases

On this workstation, `/C:` (also `/c:`), `/Programs:`, `/Libraries:`,
`/Sys_Libraries:` and `/RAM:` link to the corresponding trial directories.
For example, `ls /C:` or `cd /Programs:` works from any working directory.
Bare `C:` remains relative unless passed through the explicit assign wrapper.

These are navigation links, not block devices or PATH entries. They expose the
same unprivileged, read-only FUSE view and its symlink boundaries. They
are usable by the mounting user; this is not a multi-user system mount. Links
persist on disk, but become unavailable when the trial mount is stopped or after
reboot until it is started again. No boot service was installed, and the RAM
backing remains volatile. Do not add these experimental views to root's PATH.

The idempotent helper refuses existing conflicting paths and removes only links
whose targets match this project:

```sh
python3 examples/root_aliases.py status
python3 examples/root_aliases.py remove
# With the trial mounted again:
python3 examples/root_aliases.py install
```

Install/remove use sudo for the root links only; the filesystem continues running
as the desktop user. No operating-system directories are moved or replaced.

## Writable RAM desktop integration — 2026-10-22

`/RAM:` now points directly to `build/ram-drive`, bypassing the read-only FUSE
mirror. The desktop and EFM Favorites contain **RAM Disk**, using the installed
Enlightenment-X media-memory icon. Normal-user drag/drop and writes are available
there. The same RAM directory inside the merged trial remains read-only; use the
desktop shortcut or `/RAM:` when writing.

The dedicated tmpfs is user-owned (mode 0700), size=2G, nr_inodes=65536,
noswap,nosuid,nodev,noexec. noswap could not be enabled by remount, so the verified
empty RAM filesystem was recreated and the FUSE mirror refreshed. No stored user
files were discarded. Normal-user create/read/delete and desktop-file validation
passed. No executable startup helper or boot service was installed.

Files are volatile. Native EFM copying is limited by filesystem capacity but no
custom preflight has been added: an oversized copy can fail after a partial write.
After reboot/unmount the backing path is an ordinary directory until tmpfs is
mounted again; do not use the shortcut as RAM storage without checking the mount.
The icon references an existing installed asset; none was copied into this repo.

Relative symbolic links within an assign are supported in new mount sessions,
including library version links. Absolute links and relative links that escape
an assign are blocked; genuine cycles still report a symbolic-link loop. Existing
mounts must be restarted to load this change.
