# Teams bot — Phase 0 (read-only, owner only)

A Microsoft Teams bot backed by the Claude Agent SDK, running in Docker on the company Ubuntu server behind the existing nginx + Cloudflare. Design and admin checklist: `../../docs/team-deployment.md`.

**Phase 0 can only read** company docs and the web: no Bash, no file writes, no subagents, no MCP servers, nothing published. Only Entra object IDs in `ALLOWED_USERS` get an answer, and an empty list means nobody. Each request is capped by `MAX_BUDGET_USD`.

## How it works

1. Teams POSTs to `/api/messages`. The Microsoft 365 Agents SDK validates the Bot Framework JWT.
2. The bot replies "รับแล้ว…" immediately, then runs the Claude agent in the background. Teams retries if the HTTP call takes too long, which would duplicate the work.
3. The agent runs with `cwd` = the company folder (`setting_sources=["project"]` loads its CLAUDE.md, rules and skills) plus the `platform-core` and `marketing-core` plugins baked into the image.
4. The answer goes back as a proactive message, split under the Teams size limit.
5. Each Teams conversation keeps its own Claude session (`/data/sessions.json`). Every run logs user, company, cost and turns to `/data/usage.jsonl`.

The company is chosen per channel (`CHANNEL_COMPANY_MAP`), otherwise `DEFAULT_COMPANY`.

## Deploy on the server

```bash
git clone https://github.com/bhurivaj/ai-team-plugins.git && cd ai-team-plugins/deploy/teams-bot
cp .env.example .env && chmod 600 .env        # fill in the values
mkdir companies                                # copy company folders in, WITHOUT secrets:
rsync -a --exclude .secret --exclude medias --exclude '*.local.json' <mac>:/…/marketing_team/Catice/ companies/catice/
docker compose up -d --build
curl -s 127.0.0.1:3978/healthz                 # {"status": "ok"}
```

Then add `nginx.conf.example` as a site, `nginx -t && systemctl reload nginx`, and point the bot's messaging endpoint at `https://<bot-host>/api/messages`.

**Update:** `git pull && docker compose up -d --build`. Plugins are copied in at build time, so a rebuild picks up new plugin versions.

## Still to prove in Phase 0 (needs the real API key and bot registration)

- [ ] The agent sees the plugin skills and the company CLAUDE.md inside the container. Ask: "สรุป brand guideline ของบริษัทนี้".
- [x] The company's `.claude/settings.json` `enabledPlugins` (marketplace `ai-team-plugins`, which is not installed in the container) doesn't break startup. Verified 2026-11-02 with a fake key: init shows `platform-core` and `marketing-core` loaded once each (`@inline`), the company's project skills, tools limited to the six read-only ones, no MCP servers.
- [ ] Follow-up questions in the same thread keep context (session resume).
- [ ] Cloudflare lets Bot Framework's requests through (Bot Fight Mode off, or a skip rule).
- [ ] The cost per question in `usage.jsonl` matches the estimate.
