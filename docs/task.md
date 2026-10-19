# Active — assigns implementation

2026-10-19: user requested implementation, then explicitly approved installing
Alpine py3-pyfuse3/py3-trio and an unprivileged read-only fixture mount.
Implemented a pure resolver, JSON registry, CLI inspection, and real FUSE adapter.
The initial scope is bounded, read-only and local-filesystem focused. Write
policies, GUI and metadata remain separate follow-on stages.

Acceptance: unit tests plus actual mounted fixture reads/listings, conflicts,
blocked mutations, disappearing source, live updates and verified cleanup.
No actual music collections mounted, boot changes, service activation or file moves.
