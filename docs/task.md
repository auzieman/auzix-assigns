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
