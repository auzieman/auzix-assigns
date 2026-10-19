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
