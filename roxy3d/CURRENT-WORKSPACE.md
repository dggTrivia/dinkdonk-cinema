# Current editing workspace

Prepared 6 Nov 2026 using Blender 5.2.3. Open `current/sources/auditorium.blend` for the cinema,
`current/sources/auditorium-dim.blend` for lights down, or `current/sources/lobby.blend` for the lobby building.
See `current/README.md`, `current/dependency-report.json` and `current/verification.json`.

The local-only current folder is already excluded by the project's existing art-folder ignore rules.
It contains isolated working copies, not the live runtime. Originals and historical files remain in place.
The pre-edit backup is in the sibling `dinkdonk-cinema-backups/20261105T225845Z/` directory, with byte-verified
runtime art/code, original Blender sources/scripts and a SHA-256 manifest (11,353 files, 920,675,451 bytes).
10,984 protected original files were checked unchanged after preparing the workspace. No rendering was performed.

The saved scenes are self-contained for editing; the historical layered render/export script chain is not:
some source/QA inputs were never in GitHub. Do not run that pipeline assuming it is portable.

Optional community Blender/Codex connection (not installed by this setup):
https://github.com/ahujasid/mcp-for-blender
https://www.mcp-for-blender.com/docs/codex-plugin
