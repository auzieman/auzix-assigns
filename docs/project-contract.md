# Project contract

Explore logical names backed by ordered directories, combined directory listings
and transparent conventional paths for ordinary Linux applications. Preserve
Alpine's established filesystem layout, package management and loader behaviour.
The namespace organizes access; it does not grant access beyond underlying
permissions or automatically change executable/library search paths.

Current deliverable is a parked research scaffold. Future implementation choices
follow an observable semantics specification and isolated prototype. No runtime,
mount, performance, compatibility or license-reuse acceptance is claimed here.

## Activated implementation — 2026-10-19
The parked deliverable above is superseded by the user's implementation request.
Version 0.1 implements JSON assigns, ordered recursive unions, provenance lookup,
and an unprivileged read-only FUSE adapter. README defines exact current behavior;
writes, graphical management and system-path integration remain future stages.
