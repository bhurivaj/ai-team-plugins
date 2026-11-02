# marketing-core

Marketing agents, skills and workflows. Requires `platform-core` (scripts, upload/WordPress reference skills, model-selection criteria). Company-specific values come from each project's `company.json` → top level and `marketing` section.

- Agents: `research-analyst`, `content-strategist` (opus), `content-writer`, `seo-specialist`, `designer`, `publisher` (only one with Bash). All sonnet except the strategist — see `platform-core/docs/model-selection.md`.
- Skills: `brand-voice`, `campaign-plan`, `content-creation`, `marketing-manager`, `performance-report`, `wp-publish`, `flowtone-ops`.
- Workflows: `marketing-manager-research.js`, `marketing-manager-draft.js`.

Per-project on purpose: Catice keeps occasion-specific skills (`event-calendar`, `calendar-notice`, `knowledge-article`, `image-alt-text`) and short always-on rules; Classmat keeps its `flowtone-content-format` rule. Promote one here only when a second company needs it, moving its IDs into `company.json`.
