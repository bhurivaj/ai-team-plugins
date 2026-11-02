# Model Selection Criteria

Which model each agent and each Workflow step runs on. Shared by every client project. Applied 2026-11-02 (marketing-core 0.4.0): agent `model:` frontmatter, and per-step `model` in Catice's portfolio pipeline (Cover = sonnet, Upload Images = haiku; steps with an `agentType` take that agent's model). The main session's model is set by the user (`/model`).

## The four questions

Ask them in order. The first one that says "higher tier" wins.

1. **Can the mistake reach the public or be impossible to undo?** Publishing, scheduling, broadcasting, deleting, or anything a customer sees. If yes, use **Sonnet at minimum**, even when the task looks mechanical. Haiku saves little on a single publish, and a wrong publish costs a lot more.
2. **Does it need judgment across ambiguous or conflicting inputs?** Examples: choosing a strategy, weighing sources that disagree, diagnosing why something failed, or deciding what *not* to do. If yes, use **Opus**.
3. **Is the output Thai prose that someone will read, or is it a long tool chain with silent-failure gotchas?** Silent-failure examples: Flowtone 200-with-no-write, unverified Canva edits. If yes, use **Sonnet**.
4. **Otherwise, is the work mechanical, rule-bound and checked by something downstream?** That something can be a script, a schema, or the next step. If yes, use **Haiku**.

## Tiers

| Tier | Use for | Typical tasks | Don't use for |
| --- | --- | --- | --- |
| **Haiku** | High-volume, deterministic, verifiable work | Fixed-query data pulls (GA4/GSC/Meta numbers into a table); listing and lookups; format conversion (JSON → Gutenberg, CSV → table); tagging against explicit rules (Event vs Sport); link/alt/length checks; read-back verification after a write | Anything public, any Thai copy a reader sees, anything with conflicting inputs |
| **Sonnet** *(default)* | Production work: writing, reviewing, multi-step tool use | Drafting and revising Thai copy; platform variants; SEO review; research synthesis into a brief; reports; Canva editing; WordPress publish/upload; Flowtone writes | Open-ended strategy, or deciding between conflicting sources when the stakes are high |
| **Opus** | Low-volume, high-leverage judgment | Orchestrating (main session); marketing strategy, quarterly plans, budget allocation; choosing the content concept a whole piece is built on; diagnosing a failure across systems; final review of a high-stakes or sensitive piece (e.g. royal observance posts, crisis replies) | Routine drafting or data pulls. It's slower and costs more for no gain there |

## Rules of thumb

- **Volume pushes down, stakes push up.** A step that runs 20 times a month on fixed rules belongs on Haiku. A step that runs once and shapes everything after it belongs on Opus.
- **Escalate on evidence, not by default.** If a Haiku step fails its downstream check twice, move that step up a tier. Don't move the whole agent.
- **Verbatim-copy tasks don't need a bigger model.** Royal titles and fixed contact blocks are copied from source and checked by script, not generated. The model tier doesn't make them safer; the script check does.
- **Never drop below Sonnet for Thai customer-facing copy.** Tone and the de-AI-ify rules are the expensive part to get right.
- **Cost check:** if a pipeline's cost is dominated by an Opus step that runs per item, ask whether that step is really judgment or just drafting.

## Proposed assignment

| Agent / step | Tier | Why (question that decided it) |
| --- | --- | --- |
| Main session (orchestrator) | Opus | Q2: plans, delegates, resolves conflicts |
| `content-strategist` | Opus | Q2: one concept choice shapes the whole piece; runs once per piece |
| `research-analyst` | Sonnet | Q3: synthesis into a brief. Pure fixed-query pulls inside a Workflow can run as a Haiku step |
| `content-writer` | Sonnet | Q3: Thai copy plus Flowtone silent-failure gotchas |
| `seo-specialist` | Sonnet | Q3: review with judgment, output is proposed edits |
| `designer` | Sonnet | Q3: long Canva edit chains with unverified responses |
| `publisher` | Sonnet | Q1: public and irreversible. Mechanical, but never Haiku |
| Workflow verification / read-back steps | Haiku | Q4: compare against a schema or the expected value |
| Workflow tagging / format-conversion steps | Haiku | Q4: explicit rules, checked by the next step |
