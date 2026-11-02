# Team Deployment — Design (draft for decision)

How the AI team setup reaches other people in the company. **Status: proposal.** Nothing here is built yet beyond this plugin repo.

## What has to reach a teammate

| Piece | Where it lives today | Shared how |
| --- | --- | --- |
| Plugins (agents, skills, scripts, workflows) | `ai-team-plugins` (public GitHub) | Claude Code marketplace — done |
| Company project: `CLAUDE.md`, `company.json`, `docs/`, `.claude/rules`, project skills and workflows | local folders only (**not git repos**) | needs a private repo per company project — **decision 1** |
| Credentials | each project's `.secret/` on one machine | never shared — each person gets their own (below) |
| Symlinks (`.claude/scripts`, shared workflows) | absolute paths on one machine | created per machine by a setup script |

## Phase 1 — Claude Code on each teammate's machine

1. **Company project repos (private).** For example `catice-marketing` and `classmat-marketing`. Ignore `.secret/`, `medias/`, `agent-runs/`, `*.local.json`, `.claude/scripts`, and symlinked workflow files.
2. **Commit `.claude/settings.json` declaring the marketplace.** A teammate who trusts the folder is then offered the plugins automatically:
   ```json
   {
     "extraKnownMarketplaces": {
       "ai-team-plugins": { "source": { "source": "github", "repo": "bhurivaj/ai-team-plugins" }, "autoUpdate": true }
     },
     "enabledPlugins": {
       "platform-core@ai-team-plugins": true,
       "marketing-core@ai-team-plugins": true,
       "claude-seo@agricidaniel-claude-seo": true
     }
   }
   ```
   The plugins repo is public, so no git credentials are needed for it. There is no version pinning in this setting. `autoUpdate` follows the default branch, so protect `main` and merge through PRs once more people depend on it.
3. **`setup` script** (to build, in this repo). Run once per machine, per project:
   - Check prerequisites: `claude`, `git`, `gh` auth, `python3`, `uv`, `node`.
   - Create the symlinks into `~/.claude/plugins/marketplaces/ai-team-plugins/…`, which is a stable path across updates.
   - Check that the `.secret/` files named in `company.json` exist, without reading them, and list which are missing.
   - Smoke-test read-only: `wp_rest.py GET ""` returns the company's domain.
4. **Onboarding checklist:**
   - GitHub access to both repos.
   - The person's own credentials, from the table below.
   - First `/mcp` logins (Canva, Flowtone, Meta).
   - First SharePoint device-code sign-in.

### Credentials — per person, least privilege

| System | Give each person | Not this |
| --- | --- | --- |
| WordPress | Their own WP user + Application Password, role matched to the job (Editor for content, Administrator only if needed) | A shared admin password |
| SharePoint / Graph | Their own M365 sign-in (device code). Access comes from SharePoint site membership | A shared token cache — today Classmat borrows Catice's |
| Azure Blob | A **SAS token scoped to their company's containers**, with an expiry date | The account key. The storage account is shared between companies, so the key exposes both |
| Meta / Facebook | Their own Business Manager role on the right Page/ad account | A copied long-lived page token |
| Flowtone, Canva, GA4, GSC | Their own account or invite | Shared logins |

### Guardrails

- Only `marketing-core:publisher` has Bash and can make things public. For people who should draft but never publish, block it with a `permissions.deny` in their user or managed settings, e.g. deny `Agent(marketing-core:publisher)` and `Bash(python3 .claude/scripts/wp_*)`.
- Managed settings can enforce the marketplace and plugins company-wide when there are enough seats to justify it.

## Phase 2 — chat for non-technical staff (options, all to verify)

People who won't run a terminal still need a way in. These are the candidates. Check each for availability and fit before committing, because none has been tested here.

| Option | Fits when | Watch out |
| --- | --- | --- |
| **Claude Code on the web / desktop app** with the company repos | Staff can use a browser and don't need local files | Scripts need secrets in that environment; check how the cloud sandbox handles `.secret/` |
| **Claude in Slack (Claude Tag)** | The team works in Slack | The company is on Microsoft 365, so Teams is the more likely home |
| **Microsoft Teams bot** built on the Claude Agent SDK, hosted (e.g. on Azure), reusing these plugins' skills | Everyone lives in Teams | The most work. It is a small app to build, host and secure |
| **claude.ai Projects + remote MCP connectors** | Q&A and drafting without file/script access | No Bash, so no uploads or WordPress scripts unless those become remote MCP tools |

Recommended order: Phase 1 for the people who run the work now. Pick a Phase 2 front-end only after Phase 1 has run for a while, so it wraps a workflow that already works.

### Decided 2026-11-02: Teams bot, self-hosted

- **Channel:** Microsoft Teams. The company is internal-only on Microsoft 365.
- **Hosting:** the company's own Ubuntu server, not Azure. Requests flow Teams → Cloudflare (proxied DNS) → existing nginx → the bot container (Docker Compose).

```text
Teams user ─► Microsoft Teams / bot registration (free)
                 │ HTTPS POST /api/messages (JWT signed by Bot Framework)
            Cloudflare (proxied DNS, TLS)
                 │
            nginx on Ubuntu  ── proxy_pass ──►  bot container (127.0.0.1 only)
                                                 ├── Teams adapter (Bot Framework SDK)
                                                 ├── Claude Agent SDK + ai-team-plugins
                                                 ├── volumes: company repos, per-conversation workspaces, logs
                                                 └── secrets: Docker secrets / root-only env file (never in git or the image)
```

#### Admin checklist (owner, one-time)

1. **Entra ID app registration**, single-tenant. Gives the bot's app ID and a client secret. Add Graph delegated permissions later, for SharePoint-as-the-user.
2. **Bot registration in the Teams Developer Portal** (Tools → Bot management). No Azure subscription is needed. Set the messaging endpoint to `https://<bot-host>/api/messages`.
3. **Teams app package.** Upload as a custom app for the organisation in the Teams Admin Center and restrict it to a security group, e.g. `AI-Marketing-Users`. A second group, `AI-Marketing-Publishers`, gates publishing.
4. **Anthropic Console.** Create a dedicated workspace and API key for the bot, with a monthly spend limit. Start around $50 for Phase 0.
5. **Cloudflare:**
   - Add a proxied DNS record for the bot host.
   - Set SSL mode to Full (strict), with an origin certificate on nginx.
   - **Bot Fight Mode (classic) blocks Microsoft's calls and cannot be skipped by a WAF rule.** Either turn it off for the zone, or use Super Bot Fight Mode with a skip rule for `/api/messages`.
   - Bot Framework's JWT is validated in the app, so the endpoint stays authenticated without IP allow-listing.
6. **nginx.**
   - Add a server block that proxies `/api/messages` to `127.0.0.1:<port>`.
   - Raise `client_max_body_size` for photo attachments.
   - Keep `proxy_read_timeout` modest, because the bot must answer Teams within seconds and send long results afterwards as proactive messages.
7. **Server.**
   - Docker Engine + Compose plugin.
   - A non-root deploy user.
   - Secrets readable by root/the container only.
   - Outbound internet to Anthropic, Microsoft Graph, Flowtone, Meta and both WordPress sites.

#### Phase 0 scope

- **Build:** a read-only bot that answers from the company docs and playbook in one channel, for the owner only.
- **Prove:** the Agent SDK loads the plugins inside the container; conversation state maps to Teams threads; replies arrive asynchronously; costs are logged per user.
- **Out of scope:** publishing, uploads and Flowtone writes.

## Decisions needed

1. Make each company project a private repo? Under which account or org, and with what names? The bot container needs these repos too.
2. Who will use this first, and which of them should be able to publish?
3. Azure storage: issue per-company SAS tokens now, or keep the account key on the owner's machine only until teammates join?
