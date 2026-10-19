# Initial workstation mapping — 2026-10-19

[Config](../configs/alpine-workstation.json) uses existing directories on this
Alpine workstation. It is a purpose-based browsing pattern, not a package
classification engine. Earlier sources take precedence; nothing is relocated.

| Assign | Sources, highest priority first | Meaning |
| --- | --- | --- |
| C: | ~/.local/bin, /usr/local/bin, /usr/bin, /bin | Command-facing executable directories, including some graphical programs |
| Programs: | User desktop entries, user Flatpak exports, system Flatpak exports, system desktop entries | Graphical launchers, not merged application payloads |
| Libraries: | ~/.local/lib, /usr/local/lib, /usr/lib | User/local additions followed by general installed libraries |
| Sys_Libraries: | /lib | Low-level system library tree, kept separately visible |

Here “userland” means non-kernel software, not necessarily files owned by the
user. /usr/lib also contains core system components, helpers and other package
resources; /lib may contain kernel modules. This split is a convenient initial
layout, not a reliable ABI, privilege or package-ownership boundary. Flatpak
private runtimes stay inside Flatpak and are not merged into host Libraries.

Programs gives explicit user entries priority, then user Flatpak, then system
Flatpak, then native system launchers. This is our chosen policy rather than a
claim that it matches every desktop's XDG_DATA_DIRS ordering. Duplicate filenames
merge according to source order; different desktop IDs for the same app may both
appear. No application-type or Hidden=true filtering is performed by the raw
filesystem; a future launcher view must honor desktop-entry semantics.

/usr/local/share/applications does not currently exist and is omitted. Add it
before /usr/share/applications if created later. On this host /bin and /usr/bin
are separate directories. Do not use this config unchanged on a merged-/usr
system: inspect and deduplicate canonical source roots first. Version 1 requires
all source roots to exist when loading and refuses symlink source roots.

## Nested libraries

Use Sys_Libraries as the working sibling assign now. The preferred eventual
presentation can be Libraries/System, backed by /lib, while the Libraries root
merges the general library sources. That requires explicit virtual child mapping
support. Reserve “System” for that child; a collision with a backing directory
must be rejected or exposed elsewhere, never silently hidden. No nested mapping
syntax or synthesized directory is implied by this config.

## Check without mounting

From the project directory:

```sh
python3 -m assignfs -c configs/alpine-workstation.json check
python3 -m assignfs -c configs/alpine-workstation.json ls Programs:
python3 -m assignfs -c configs/alpine-workstation.json inspect Programs:e-control.desktop
```

This is configuration preparation and listing validation only. Existing symlink
restrictions matter: Flatpak exports, BusyBox command names and library SONAMEs
are often symlinks, which the current FUSE implementation lists but refuses to
follow. Therefore these views are not yet accepted as executable/launcher/linker
search paths. Safe symlink semantics are the next prerequisite for that use.
No PATH, dynamic-loader configuration, mount or service is changed by this file.
