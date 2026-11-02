---
name: brand-voice
description: Load the current client's own brand guideline (colors, typography, tone of voice, audience, logo and imagery rules) before writing copy or specifying visual direction. Use instead of any generic "brand-guidelines" skill — that one is Anthropic's brand, not the client's.
---

# Brand Voice

1. Find the client project's `client.json` (walk up from the current directory). If there is none, stop and say so — never fall back to a generic or Anthropic brand.
2. Read the file named in `client.json` → `brand_doc`, relative to that project root, in full.
3. Also read any copywriting style rule the project keeps under `.claude/rules/` (e.g. `fb-copywriting-human-style.md`) if you are writing social copy.
4. Apply it: palette and fonts exactly as written there, tone of voice, audience, and any do/don't lists. Quote the hex values from the doc; never invent or approximate a color.
5. In your output notes, name the brand doc you used (`client.json` → `brand_doc`), so a reviewer can check it.
