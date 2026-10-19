# Design questions and first experiment

## Namespace and lookup

An assign has a logical name and an ordered list of backing directory references.
Lookup and combined enumeration must follow the same documented visibility rules.
A native resolver can understand Programs:relative/path; a FUSE directory can
expose the equivalent conventional path to unmodified applications.

Default collision policy candidate: ordered branch priority. User-suggested
alternative: newest file wins. Keep the latter optional pending timestamp,
reproducibility and compatibility tests; copying and clock differences can change
mtime. Any timestamp policy needs deterministic ties, missing-metadata handling
and consistent lookup/stat/readdir results. Never silently adopt it for Programs
or Libraries. Expose all candidate copies and their origins through an inspection
interface. Define file-versus-directory collisions and recursive directory merging.
Linux case sensitivity and any optional case folding need separate decisions.

## Bounds and failure handling

Specify configurable limits before implementation: backing branches per assign,
assign nesting, symlink expansion, directory traversal depth, enumeration/cache
memory, and concurrent outstanding work. Numerical defaults remain unselected.
Detect cycles in assign references and filesystem traversal, not merely long paths.
Distinguish depth-limit, permission, missing-path, offline-drive and provider errors.
Specify symlink escape policy instead of claiming the mount provides confinement.
Avoid recursively merging an assign's own mount back into itself.

Check backing mount identity so a disconnected drive does not redirect access to
an underlying empty mountpoint directory. Define reconnect behaviour, open-handle
lifetime, configuration changes during enumeration and cache invalidation.

## Writes are a later contract

A winning read copy does not implicitly select a write destination. Define an
explicit creation destination/policy and distinguish create, overwrite, rename,
move, unlink and directory removal. Decide whether deleting a visible winner
reveals a lower-priority copy or uses a masking mechanism. Never delete every
copy by default. Cross-filesystem rename and atomicity require honest behaviour.
Do not enable writes in the initial experiment.

## Bounded first prototype, when resumed

Use three disposable directories containing unique files, duplicate names,
nested directories, file/directory collisions and symlink cycles. Start with a
pure registry/resolver and read-only merged enumeration, then expose the same
semantics through an unprivileged FUSE mount if suitable on the target host.
No kernel module, custom device node or workstation root-layout migration.

Acceptance: all unique fixture names appear, collisions resolve deterministically,
inspection identifies their origins, lookups agree with listings, limits fail
clearly, inaccessible/offline branches are distinguished, and unmount/recovery
works without modifying fixture data. Test ordinary ls/stat/open behaviour and
configuration changes. Measure overhead before claiming lightweight operation.
Assess existing mergerfs capabilities before writing a new filesystem.

Later: native file-manager presentation as disk-like named locations, application
resolver integration and a separate write-policy experiment. System boot paths,
dynamic-linker integration and /System or /Programs migration remain future work.
