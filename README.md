# marketing-core

Shared core for the client marketing projects (Catice, Classmat). Client-specific values
live in each project's `client.json`, never in this repo. Installed in each client project as
the project-scope plugin `marketing-core@marketing-team-local` (this folder is also the local
marketplace).

| Folder | How a client project gets it | Edits take effect |
| --- | --- | --- |
| `agents/`, `skills/` | plugin, namespaced `marketing-core:<name>` | after `version` bump + `claude plugin marketplace update marketing-team-local` + `claude plugin update marketing-core@marketing-team-local --scope project` in each project, then a new session (loaded from a cache copy) |
| `scripts/` | `.claude/scripts` symlink | immediately |
| `workflows/` | per-file symlink into `.claude/workflows/` | immediately |

Scripts must run from inside a client project: `client_config.py` walks up from the current
directory to the nearest `client.json` and resolves every credential path relative to it.

Per-project on purpose: Catice keeps occasion-specific skills (`event-calendar`, `calendar-notice`, `knowledge-article`, `image-alt-text`) and short always-on rules; Classmat keeps its `flowtone-content-format` rule. Promote one here only when a second client needs it, moving its IDs into `client.json`.
