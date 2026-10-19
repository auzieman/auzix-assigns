# Assigns implementation scope
Read README.md, docs/project-contract.md and docs/task.md before work.
The user activated implementation on 2026-10-19 and explicitly approved installing
py3-pyfuse3/py3-trio and unprivileged read-only fixture mounts. Earlier parked-only
restrictions are superseded for this work. Use disposable fixtures first; clean
up mounts and verify backing contents. Do not change boot/root paths or move user
data. Mounting real collections or enabling writes needs a concrete scoped plan.
Preserve lookup/listing/duplicate/failure semantics and report actual acceptance.
Research upstream behavior without copying AROS code; keep source licensing clear.
Keep control-centre/theme projects independent. Add skills only for demonstrated
reusable workflows, not speculative scaffolding.
