# Active — assigns implementation

2026-10-19: user requested implementation, then explicitly approved installing
Alpine py3-pyfuse3/py3-trio and an unprivileged read-only fixture mount.
Implemented a pure resolver, JSON registry, CLI inspection, and real FUSE adapter.
The initial scope is bounded, read-only and local-filesystem focused. Write
policies, GUI and metadata remain separate follow-on stages.

Acceptance: unit tests plus actual mounted fixture reads/listings, conflicts,
blocked mutations, disappearing source, live updates and verified cleanup.
No actual music collections mounted, boot changes, service activation or file moves.

2026-10-20: user authorized building out a controlled desktop trial. Added partial
permission-aware browsing and source status; tested with fixtures. Disposable EFM
trial includes a RAM source under existing /dev/shm, with process limits and a
start/stop command. Real workstation mappings remain unmounted. User review of
EFM behavior is next; no production-beta claim.

2026-10-20: user authorized a real-ish dry run after reviewing the sample demo.
Scope: existing workstation config, unprivileged read-only mount, root listing
comparison, installed E-control desktop-file byte comparison, then EFM browse.
No writes, execution tests, PATH/loader changes, or uncapped RAM assign.

Cache and colon alias pass completed: one-second bounded directory snapshots,
mount-relative C:/c:/Programs:/RAM:, explicit path/exec CLI translation. Real
trial activated with 2 GiB-capped RAM backing, read-only through Assigns. Source
files remain in their natural filesystems. No global shell rewriting installed.

2026-10-22: user requested base-path navigation. Installed scoped root symlinks
/C:, /c:, /Programs:, /Libraries:, /Sys_Libraries:, /RAM: to the existing live
trial. Verified all listings and inode equivalence from /tmp. No collisions,
root directory replacement, PATH changes, privileges for FUSE, or boot changes.

2026-10-22 RAM usability: direct /RAM: alias now targets capped user-owned tmpfs
rather than read-only FUSE. Added Desktop/EFM favorite RAM Disk link with installed
media-memory icon. Empty mount recreated with noswap after remount rejected that
flag; normal-user write/read/delete verified. No boot persistence or write support
for other assigns. Refresh FUSE after RAM source identity changes.

2026-10-23: permit relative symbolic links that stay within the same assign;
absolute links and links escaping an assign remain blocked. Kernel link traversal
retains normal cycle detection and stays on the read-only mount. Verified unit
suite, disposable mounted fixtures including loops and escapes, and a separate
real workstation mount where libzstd.so.1 resolves to libzstd.so.1.5.7. The
existing workstation mount runs the previous process until it is restarted.
