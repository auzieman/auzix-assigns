# Research references

Initial review: 2026-10-15. URLs point at evolving upstream sources; pin a commit
and preserve per-file notices before implementation/source reuse work.

- [AROS project](https://www.aros.org/): independent Amiga-compatible reimplementation.
- [AROS DOS source](https://github.com/aros-development-team/AROS/tree/master/rom/dos):
  AssignLock creates/replaces an assign; AssignAdd appends directory targets;
  GetDeviceProc iterates primary/additional targets; Lock/Open use the iterator.
- [Open implementation](https://github.com/aros-development-team/AROS/blob/master/rom/dos/open.c):
  retry on object-not-found differs for MODE_NEWFILE; do not generalize read
  lookup into a universal write policy.
- [Multiassign enumeration](https://wiki.amigaos.net/wiki/Multiple_Assigns):
  GetDeviceProc iteration plus per-target scanning; a single underlying directory
  handle does not automatically enumerate the entire logical assign.
- [AROS Public License](https://www.aros.org/license.html): APL-covered code is
  not automatically GPLv3 code. Review actual file notices and compatibility
  before copying; conceptual study is the current approach.
- [mergerfs](https://github.com/trapexit/mergerfs): existing FUSE union-filesystem
  implementation to evaluate for reuse/comparison before inventing equivalent work.

No source implementation was imported into this scaffold. AROS examination does
not establish that a Linux resolver or filesystem has been implemented or tested.
