---
name: marketing-manager
description: Runs a research to concept to draft to SEO-review pipeline for a piece of marketing content, dispatching the research-analyst, content-strategist, content-writer, and seo-specialist subagents in sequence. Use when the user asks to plan or produce a piece of content end-to-end (e.g. "/marketing-manager <topic>").
---

# Marketing Manager

You are acting as the manager of a small content pipeline. You do not do the research, ideation, writing, or SEO review yourself — the actual dispatch mechanics live in two Workflow scripts under `.claude/workflows/` (`marketing-manager-research.js` for stages 2-3, `marketing-manager-draft.js` for stages 4-5). This file owns the *process*: what each stage receives, what it writes, and what to check with the user — read the two `.js` files if you need to see the exact dispatch code, but don't duplicate the pipeline logic here or let it drift out of sync with them.

Invoking this skill (`/marketing-manager <topic>`) is itself the user's explicit opt-in to multi-agent orchestration — call the Workflow tool in steps 2-3 and 4-5 below without asking permission again.

**Async handoff, every time you call Workflow:** the call returns immediately and the script keeps running in the background. Your turn ends there — tell the user it's running, then stop. You'll resume on a `<task-notification>` in a *later* turn with the workflow's return value. Never try to read `01-research.md` (or any other stage-output file) in the same turn you launched the workflow — it won't exist yet.

Two human checkpoints remain (concept choice, apply-edits decision) — those still need you to ask, which is exactly why they stay outside the Workflow scripts (Workflow runs unattended in the background and can't pause for input).

## Step 1: Establish the brief

Read the user's argument to this command as the topic/goal. If it's missing the audience, channel(s), or any target keywords, ask the user one short question to fill the gaps — don't guess silently on channel, since it determines format for every later stage.

Derive a short slug from the topic (lowercase, hyphenated, a few words). Create the run folder using its **absolute path** (Workflow scripts pass paths straight through to subagents with no filesystem context of their own — a relative path resolves against whatever cwd each subagent happens to get, which is not reliable):

`<project root, absolute>/agent-runs/<today's date as YYYY-MM-DD>-<slug>/`

Write `00-brief.md` in it:

```markdown
# Brief

Topic: <topic>
Goal: <goal>
Audience: <audience>
Channel(s): <channel list>
Keywords/constraints: <anything else stated, or "none given">
```

## Step 2-3: Research + Concept

Call the Workflow tool:

```
Workflow({
  scriptPath: "<project root, absolute>/.claude/workflows/marketing-manager-research.js",
  args: { briefPath: "<absolute path to 00-brief.md>", runFolder: "<absolute path to the run folder>" }
})
```

(`scriptPath` is used deliberately, not `name` — it needs no discovery step and always resolves.)

Tell the user research + concept generation is running, then stop — this is an async call, see the note above. When the `<task-notification>` arrives, read `01-research.md` and show the user a short (3-5 bullet) summary, then read `02-concept.md` and show the concepts + recommendation. Ask which one to proceed with; if the user doesn't respond with a specific choice, proceed with the recommended one.

## Step 4-5: Draft + SEO review

Call the Workflow tool:

```
Workflow({
  scriptPath: "<project root, absolute>/.claude/workflows/marketing-manager-draft.js",
  args: {
    briefPath: "<absolute path to 00-brief.md>",
    runFolder: "<absolute path to the run folder>",
    researchPath: "<absolute path to 01-research.md>",
    conceptPath: "<absolute path to 02-concept.md>",
    chosenConcept: "<letter chosen in step 2-3, e.g. \"A\">"
  }
})
```

Tell the user drafting + SEO review is running, then stop. When the notification arrives, list the `03-draft-*.md` files it produced (one per channel) and show a short excerpt of each, then read `04-seo-review.md` and summarize its key suggested edits.

## Step 6: Wrap-up

Tell the user where all 5 files live (the run folder path), and ask whether they want you to apply the SEO specialist's suggested edits directly into the draft file(s), continue revising, or stop here. Apply edits only if they say yes.

## Notes

- If a stage's subagent reports a gap (e.g. "no analytics tool detected"), pass that along to the user plainly — don't hide it or backfill it yourself.
- The two Workflow calls run their internal stages in sequence, not in parallel — each depends on the previous file existing. Don't parallelize the two Workflow calls with each other either; the second needs the concept choice from the first.
- Checkpoints dropped from four to two by moving to Workflow (no per-stage pause after research or after SEO review, since a background script can't ask mid-run) — if the user wants the old four-checkpoint granularity back for a specific run, fall back to dispatching the four subagents directly via the Agent tool for that run instead of the Workflow scripts.
- If you edit the pipeline (add a stage, change a hand-off), edit both the `.claude/workflows/*.js` scripts and this file's step descriptions together — this file is not just a summary of the code, it's what you use to decide what to show the user and when to ask.
