# Validation — 2026-10-19

Host: Alpine 3.24, Python 3.14, packaged pyfuse3 3.4.2 and Trio 0.33.0.
Explicitly approved dependency installation added 26 packages including split
Python bytecode/dependencies; no existing packages were upgraded.

- 12 resolver tests passed: union/priority, recursive merging, both file/directory
  collision directions, disappearing/replaced roots, existing descriptors,
  symlink refusal, traversal/depth, mount overlap, unsupported write configuration,
  source changes and permission errors.
- Real unprivileged FUSE fixture mount passed ordinary ls/open, recursive merge,
  read priority, write/unlink/rename refusal, symlink refusal, fresh backing files,
  source disappearance with an open descriptor, and unchanged source-byte hashes.
- Actual mount detachment and mount-process exit verified. No mounts remain from
  testing. Demo sources are under build/demo and are not mounted automatically.
- First live test encountered a nonzero fusermount status after successful kernel
  detach: its external BusyBox umount lacks --no-canonicalize. Confirmed no mount
  remained. Test cleanup now checks actual mount state and reports the warning;
  it does not suppress failed detachment. No host umount replacement was installed.

This does not establish production filesystem compatibility, performance under
large collections, network mount timeouts, reconnect automation, write behavior,
or graphical file-manager integration. Root identity uses dev/inode for this
session, not a persistent removable-volume UUID. Symlinks are intentionally
unusable; ls -l can report an error while trying to display their target.

## Design references

Reviewed [pyfuse3's documented operations/examples](https://pyfuse3.readthedocs.io/en/latest/example.html)
and [mergerfs](https://trapexit.github.io/mergerfs/latest/). Mergerfs is an existing
union filesystem and remains a useful comparison. This small independent adapter
lets one mount expose multiple named assigns and share the exact resolver with
our provenance CLI. It is not a replacement for mergerfs's mature write policies.
No AROS implementation source was copied.

## 2026-10-20 — controlled desktop trial

15 resolver tests passed, including all-denied, lower-source-denied and denied-at-
load cases. Live fixture checks passed again, with mounted permission checks added.
The fixture mount detached and exited; its source byte hashes were unchanged.

Desktop demo start/stop/start passed. A fresh read-only demo is deliberately left
mounted for user review at build/desktop-demo/view. EFM open requests returned
success; visual layout has not been independently inspected. This E build lacks
the Window.List D-Bus method, so enlightenment_remote could not enumerate windows.

Measured before the small read loop: 28,232 KiB RSS, 36,776 KiB virtual size.
100 small sequential mounted reads completed in 1.051 seconds. This is a smoke
measurement, not a throughput benchmark. Demo limits: 512 MiB address space,
256 descriptors, nice +5; adapter worker concurrency limited to four.
RAM fixture uses existing /dev/shm; no new tmpfs/system mount was configured.

Still experimental: no write semantics, working symlink targets, inode reclamation,
EFM metadata integration, long-running stress/reconnect coverage, or production
beta acceptance. The desktop trial is for observing ordinary read-only browsing.

## Real mappings and EFM desktop-entry parsing — 2026-10-20

Real read-only mount validated: C 1220 entries, Programs 99, Libraries 2638,
Sys_Libraries 8. Listings matched resolver results, E-control desktop bytes
matched the installed source, and kernel read-only flag was verified. Added
statfs support: the logical view reports no allocatable capacity instead of
inventing pooled backing storage totals.

EFM icon investigation found a real interoperability defect: FUSE direct_io
made mmap fail with ENODEV, and efreet_desktop_new consequently returned NULL.
After disabling direct_io (keep_cache remains false), the installed E-control
launcher and its mounted copy both mapped 211 bytes and parsed successfully
through native libefreet. Live fixture acceptance including mmap passed.
Symlinked Flatpak desktop entries remain unsupported; this fix addresses ordinary
files only. EFM was asked to reopen Programs; visual rendering awaits user review.

Old trial was busy in EFM and required targeted lazy detach before remount;
no desktop process was killed. Close old EFM views to release retained references.

## Cache/colon/RAM activation — 2026-10-20

17 unit tests plus the real disposable mount suite passed during implementation.
Tests cover cache expiry/bounds, colon aliases, mmap, permission changes and a
source disappearing while open. The first regular-file metadata cache approach
failed the source-size-switch test and was discarded; regular-file attributes
remain uncached. Directory snapshot metadata eliminates per-entry worker trips.

Resumed after usage-limit interruption and activated the tested implementation.
Real listings matched C 1220, Programs 99, Libraries 2638, Sys_Libraries 8, RAM 0.
E-control desktop bytes and kernel read-only flag verified. Literal C:, c:,
Programs: and wrapped RAM: commands completed successfully.

Same C directory measurement before: 4.453, 2.959, 4.021 seconds. After activation:
0.163, 0.033, 0.034 seconds. This is a small sequential listing measurement, not
a general filesystem benchmark. Dedicated auzix-ram tmpfs confirmed at 2 GiB,
empty at activation. No shell PATH changes, application execution or boot setup.
