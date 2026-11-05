# Virtual office for the AI marketing team — design

Status: draft for the owner's approval, 2026-11-05. Replaces the Teams bot (`deploy/teams-bot/`, `docs/team-deployment.md` → "Decided 2026-11-02: Teams bot").

## Intent

The owner wants one place where people can see what each AI agent is doing and hand it work. Today the agents exist only inside a Claude Code session: `marketing-manager` spins them up as subagents and they vanish when the run ends. Nobody else on the team can use them, and nobody can see who is busy.

The answer is a web page drawn as a pixel-art office. Each AI agent is a character at a desk. Each person on the team logs in as their own character, walks up to an agent, and talks to it. The room shows at a glance which agents are working, who is waiting for whom, and how much the team is spending.

Gather.town is the reference for the genre: a top-down, walkable 2D room. The art, layout and code must be original.

## Who uses it

- Phase 1: the owner and the people they add, working on marketing for the two companies, Catice and Classmat.
- People join with their company Microsoft 365 account (see Constraints).

## What the owner decided

1. **No Teams bot.** The virtual office is the only way to use the agents. The Teams bot is retired before it ever ran.
2. **Several people share one office.** Each person is a character, and everyone can walk up to and talk to any agent. The agents are shared.
3. **Agents are the characters.** In Phase 1 these are the six marketing roles in `plugins/marketing-core/agents/`: research-analyst, content-strategist, content-writer, designer, seo-specialist, publisher.
4. **Talking to an agent.** Walk up to the agent and type to it. The conversation is private: other people see a speech-bubble icon over the agent's head, meaning "talking with someone", but never the content.
5. **Busy agents queue.** If the agent is already busy with another person, the newcomer joins a queue. The room shows that people are waiting (for example a count over the agent).
6. **Fire and forget.** After giving the work, the person can walk away. When the work is done, a "!" appears over the agent. Clicking the agent, or walking back to it, opens the result: a short summary first, with the full output behind it. (Owner picked mockup B on 2026-11-05.)
7. **Idle agents sit still** and spend no tokens. Movement and animation are purely client-side. Claude is called only when someone gives an agent work.
8. **A screen on the office wall shows token spend.**
9. **Phases.** Phase 1 is marketing only. Phase 2 adds project work as separate office rooms, one per project.
10. **One floor per company.** The building has a Catice floor and a Classmat floor, and each floor will later be split into rooms by type of work. In Phase 1 each floor is one open-plan space with no rooms yet. The floor you stand on decides which company a job is for. (Owner, 2026-11-05.)
11. **Access is managed inside the office, in a security room.** Rights show up as doors: the door to a floor or department opens for people who are allowed and stays shut for everyone else. If someone without the right is inside, for example because their right was just removed, they are pushed out of the room at once. Someone allowed on both companies' floors can walk into either one straight away. (Owner, 2026-11-05.)
12. **Service keys are entered in the security room too**, per floor: the GA4 service account, WordPress passwords, Flowtone tokens and SAS tokens. (Owner, 2026-11-05.)
13. **Three containers for the agents:** one per floor, plus an executor (see "How it fits together"). (Owner agreed, 2026-11-05.)
14. **Everything runs on Docker** on the company server.
15. Anything else is to be tuned later with the owner.

## Goals

- From the office alone, the owner can ask research-analyst for this month's GA4 numbers and get them, without opening Claude Code.
- Anyone in the office can tell in under a second which agents are free, busy or done, and how many people are waiting.
- Spend is visible all the time, and capped.

## Non-goals (Phase 1)

- Project rooms (Phase 2).
- Voice or video between people. Gather has this; this office does not need it.
- People chatting with each other inside the office. They already have Teams.
- Agents talking to each other on their own, or the office running work on a schedule.
- Editing context, skills or tools from the office. That was the separate "admin UI" idea and stays separate.

## Anti-goals (a failure even if it works)

- Someone can read another person's conversation with an agent.
- An agent publishes, posts or changes anything outside the system without a person approving it first.
- Idle offices cost money: polling Claude, keeping sessions warm, or "ambient" agent chatter.
- Credentials are shared widely, for example every agent container holding every key.
- The art or layout copies Gather.town.

## Constraints carried over from the Teams bot decisions

These were decided on 2026-11-02 and still hold:

- **Hosting:** the company Ubuntu server, Docker Compose, behind the existing nginx and Cloudflare proxied DNS. Not Azure. Ports bind to `127.0.0.1` only.
- **Claude:** the Claude Agent SDK with an API key from a dedicated Anthropic Console workspace that has a monthly spend limit. Subscription logins are not allowed for this use. The default model is `claude-sonnet-5-5`; per-role models follow each agent's `model:` frontmatter and `plugins/platform-core/docs/model-selection.md`.
- **Plugins are baked into the image** and pinned by rebuild, not pulled from `main` at runtime (decided 2026-11-02).
- **Company folders** are mounted read-only without `.secret/` or `medias/`.
- **Per-request budget cap** (`max_budget_usd`) and `permission_mode="dontAsk"` with an explicit tool allowlist per role.
- **Secrets** never go in git or the image. Azure storage is shared by both companies, so use SAS tokens scoped per company, never the account key.

New constraints:

- **Login uses Entra ID (OIDC)**, single tenant. There are no local passwords. *(My call.)*
- **Entra decides who you are, and the office decides where you may go.** Anyone in one Entra group (`AI-Office-Users`) can log in and lands in the lobby. Which floors and rooms they may enter is set in the security room (decision 11), not in Entra.
- **The office is a public web page**, so it sits behind Cloudflare Access as well as the app's own Entra login. nginx must pass WebSocket upgrades.

## How it fits together

```text
Browser (pixel office, canvas; one floor per company)
   │  HTTPS + WebSocket (Cloudflare Access → nginx)
Office server container
   ├─ Entra login, session cookie
   ├─ room state: who is where, agent status, queues   ──► broadcast to everyone in the room
   ├─ conversations: per (person, agent), private
   ├─ job queue per agent (FIFO)
   └─ spend ledger (usage.jsonl or a small DB)
        │  one job at a time per agent
Agent containers, one per floor (agents-catice, agents-classmat)
   ├─ Claude Agent SDK + ai-team-plugins (baked in)
   ├─ per-run tool allowlist and MCP servers for the role
   └─ that company's read-only credentials
Executor container
   └─ write credentials per company; runs approved actions only
```

- **One agent container per floor (company)**, running all six roles. It mounts only its own company folder and holds only that company's **read-only** credentials, such as GA4 viewer and Search Console. Roles differ by tool allowlist and MCP config per run.
- **One executor container** holds the credentials that write: WordPress, Flowtone writes, posting and storage SAS tokens, per company. It runs only actions a person has approved, and never calls Claude. Since agents only propose writes, no agent container ever holds a write credential.
- **The office server never calls Claude itself.** It keeps state and dispatches jobs.
- **Reuse from the Teams bot:**
  - `agent_options`: tool allowlist, `dontAsk`, budget cap, strict MCP config
  - per-run cost logging from `ResultMessage`, including the `ResultError` handling
  - `SessionStore`
  - the writable-`/data` Dockerfile fix

  The Teams adapter code goes.

## Behaviour details

**Agent states, shown above the agent's head:**
- *idle*: sitting still
- *talking*: speech-bubble icon
- *done*: "!", shown only to the person whose job finished. Everyone else sees idle or talking.
- *queue*: a small count of waiting people

**Conversations:**
- Each (person, agent) pair keeps its own Claude session, so a follow-up resumes context.
- Only that person can read it.
- The office keeps the conversation history so the person can reopen past results.

**The queue:**
- Each agent runs one job at a time.
- A message to a busy agent becomes a queued job. The person sees their position and can leave.
- The queue is first-in, first-out.

**Results:**
- When a job finishes, the person gets the "!".
- Clicking shows a summary card first: the agent's final answer, trimmed. The full output sits behind it.
- In Phase 1, results are text (Markdown) plus links, such as Canva export URLs. Uploading attachments and downloading files come later. *(My call.)*
- **Handing work between agents:** a result card has a "send to…" button that queues a new job for another agent, with the result attached as context. Agents never hand off to each other on their own. *(My call.)*

**Spend wall:**
- This month's spend against the monthly cap, broken down by agent and by person.
- Spend shows in USD from `total_cost_usd`. Token counts are secondary.
- The office enforces its own monthly cap, set below the Anthropic Console limit. At the cap it refuses new jobs with a clear message, and the Console limit stays as a backstop. Per-person caps can come later. *(My call.)*

**Actions with outside effects** (publish, schedule, Flowtone writes, Canva edits):
- The agent never holds the real write tools. Instead it calls a "propose action" tool that records the exact call (tool name and arguments) plus a one-line reason, and the run ends.
- A person with publish rights sees the proposed action and the reason in an approval list on the office wall. They do not see the conversation it came from, so conversations stay private.
- On approval, the role container executes that exact recorded call. This is not a new LLM run, so it costs nothing and cannot drift from what was approved. On rejection, the requester is told.
- While an action waits for approval, the agent is free for the next person in its queue.
- In Phase 1 only the owner has publish rights.

*(All my calls.)*

## Security room and doors

- **The security room** is a room in the office. Only admins can enter it; in Phase 1 that is the owner. It shows people × floors (and later rooms), and toggling a cell grants or removes access.
- **Doors are enforced by the server, not drawn.** The office server holds the access list and checks it on every move into a floor or room, every message to an agent, every result and every spend view. A browser that draws its own way through a door still gets refused.
- **Removing access takes effect at once:**
  - the person's character is moved out to the lobby
  - their open chat on that floor closes
  - their queued jobs there are cancelled
  - a job already running finishes, but its result is held until access returns
- **Granting access takes effect at once.** The door opens without logging in again.
- Every change in the security room is logged, with who changed what and when.

### Service keys

The security room is also where admins enter each floor's service keys (decision 12). That makes key storage the most sensitive part of the system, so *(all my calls)*:

- **Separate secrets store.** A small dedicated secrets container holds the keys, not the office server.
  - The office server can **write** keys into it but can never read them back.
  - Each agent container can read only its own floor's read-only keys.
  - The executor can read the write keys.
  - Each caller has its own token.
  - Taking over the office server lets someone overwrite keys, but not read them.
- **Write-only in the UI.** A key field accepts a typed value or an uploaded file, such as a service-account JSON. Afterwards it shows only "set on <date> by <name>", never the value. Changing a key means replacing it.
- **Every key is labelled with its floor and its kind (read or write).** The kind decides which container receives it, so a write key can never reach an agent container.
- **Encrypted at rest.** The encryption key is a root-only file on the host, outside the database and outside any backup of the data volume.
- **A fresh Entra sign-in with MFA** is required before the security room accepts a change.
- **"Test" button per key.** The receiving container tries the key, for example with a GA4 metadata call, and reports OK or the error. The value is not echoed back.
- **Migration.** Today's keys live in each company's `.secret/` folder on the owner's Mac. The owner enters them once through the security room, and they are never copied as files to the server.
- **Phase 1 has two floors and no rooms.** Doors sit at the floor entrances: the lift or stairs from the lobby. Department rooms and their doors come in Phase 2.

## Phase 1 milestones (suggested order)

1. **Office shell.**
   - Entra login, the lobby and two floors.
   - The people's characters walk with live presence, and the agents sit idle.
   - The security room works, with doors enforced by the server.
   - No Claude yet.
2. **Service keys in the security room** (secrets store, write-only fields, test button). Then **one agent end to end.** research-analyst runs in its own container with the GA4 MCP server and read-only credentials, plus conversation, queue, "!", result card and the spend wall. This proves the owner's first scenario.
3. **The read-mostly roles:**
   - content-strategist
   - seo-specialist
   - content-writer, drafting text without Flowtone writes
4. **Approval flow,** then the roles that write outside: content-writer's Flowtone writes, designer (Canva), publisher.

## Left to the builder

- The frontend stack and rendering, e.g. a canvas game library vs plain canvas, and the tile and sprite pipeline. The pixel art must be original.
- The backend framework. Python is suggested, to reuse the Agent SDK code.
- How the office server talks to agent containers: an HTTP job API, a queue such as Redis, or similar.
- Storage for conversations, queues and spend. SQLite on a volume is likely enough.
- Room layout, character movement, how "walk up to" is detected, and the chat panel design.
- How each MCP server is packaged per role. The company `.mcp.json` today mixes stdio servers (uvx/npx) with OAuth-based HTTP servers (Canva, Meta Ads), and the OAuth ones need a headless auth story.

## Open questions

None blocking. The builder check (2026-11-05) raised six; the owner answered the company question with floors, and the rest are marked *(My call)* above.
