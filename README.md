# marketing-core

Shared core for the client marketing projects (Catice, Classmat). Client-specific values
live in each project's `client.json`, never in this repo.

- `scripts/` — reached from each project as `.claude/scripts` (symlink). Run them from inside
  a client project: `client_config.py` walks up from the current directory to the nearest
  `client.json` and resolves every credential path relative to that project.
- Agents and skills move here next (step 3), then this repo is installed as a plugin.
