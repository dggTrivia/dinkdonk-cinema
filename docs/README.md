# Documentation

| Doc | For |
|---|---|
| [owner-workflow.md](owner-workflow.md) | How the streamer runs it in OBS on movie nights, and how the AI agents are used |
| [lobby.md](lobby.md) | `lobby.html`: structure, every URL option, coordinates and art layers, chatters, director, control commands, recipes |
| [auditorium.md](auditorium.md) | `auditorium.html`: layout JSON, banded art, seating, phases and lights, the film screen, director, recipes |
| [server-and-shared.md](server-and-shared.md) | `standby-server.js` routes, chat relay, OBS bridge, dinkdonk.js, LAN proxy, control protocol, `shared/` APIs |
| [art-pipeline.md](art-pipeline.md) | Blender + Codex art workflow, the art pack contract, cloud rendering, auditorium drafts, history of briefs |
| [../AGENTS.md](../AGENTS.md) | Rules and context for AI coding agents (Claude Code reads it through `CLAUDE.md`) |
| [../web/README.md](../web/README.md) | Hosted edition (work in progress) |

Each doc ends with the inconsistencies found in the code while writing it (5 Nov 2026). Line numbers drift as the
pages change; the function names next to them don't.
