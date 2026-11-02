# ai-team-plugins

Public Claude Code marketplace for the company AI teams. One repo, several plugins, one CI.

| Plugin | What it holds | Used by |
| --- | --- | --- |
| `platform-core` | `company.json` loader and the Azure Blob / SharePoint / WordPress scripts; skills `asset-upload`, `msgraph`, `wordpress-woocommerce`; `docs/model-selection.md` | every department |
| `marketing-core` | 6 marketing agents, marketing skills (`brand-voice`, `flowtone-ops`, `wp-publish`, `campaign-plan`, …), the `marketing-manager` workflows. Declares `dependencies: ["platform-core"]` | marketing projects (Catice, Classmat) |
| `accounting-core`, `projects-core` | not created yet — add under `plugins/` when that work starts (accounting will plug into the existing `ai_team/odoo_team`) | |

Plugin agents and skills are namespaced `<plugin>:<name>` (e.g. `marketing-core:publisher`, `platform-core:asset-upload`).

## company.json (lives in each company project, never in this repo)

One file per company project. Top level is company-wide; each department adds its own section.

```jsonc
{
  "company": "catice", "prefix": "ci",            // prefix scopes Azure containers (ci-images, …)
  "name_th": "…", "name_en": "…", "domain": "catice.co",
  "reference_ids_doc": "docs/reference-ids.md",
  "wordpress":  { "site_alias": "production", "credentials": ".secret/…/wp-sites.json", "seo_plugin": "yoast|aioseo" },
  "azure":      { "credentials": ".secret/ms_azure_credentials.json", "containers": { "images": "ci-images", "public": "ci-public" } },
  "sharepoint": { "token_cache": ".secret/msgraph_token_cache.json" },
  "marketing":  { "sharepoint_site": "…", "brand_doc": "…", "playbook_doc": "…", "flowtone_connector": "flowtone-catice", "canva": { … } },
  "accounting": { /* reserved — e.g. odoo_url, odoo_db, sharepoint_site; define when accounting-core is built */ }
}
```

Paths are relative to the company project root. Scripts find the file by walking up from the current directory, so **run them from inside the company project**.

## Install in a company project

```bash
claude plugin marketplace add bhurivaj/ai-team-plugins          # public: no git credentials needed
claude plugin install platform-core@ai-team-plugins  --scope project
claude plugin install marketing-core@ai-team-plugins --scope project
ln -sfn ~/.claude/plugins/marketplaces/ai-team-plugins/plugins/platform-core/scripts .claude/scripts
```

Workflows that a project uses are symlinked per file into its `.claude/workflows/` the same way (target `…/plugins/<plugin>/workflows/<file>.js`).

## Changing something

1. Edit here, run `python3 -m unittest discover -s tests` and `bash tests/secret_scan.sh`.
2. Agents/skills changed → bump that plugin's `version` in `plugins/<name>/.claude-plugin/plugin.json`.
3. Commit and push. CI runs the tests and the secret scan.
4. In each company project: `claude plugin marketplace update ai-team-plugins && claude plugin update <plugin>@ai-team-plugins --scope project`, then start a new session. Agents and skills load from a versioned cache copy; scripts and workflows are symlinked to the marketplace clone, so they change as soon as the marketplace is updated.

Never commit `company.json`, `.secret/`, or anything credential-shaped — `.gitignore` and CI both block it. See `docs/team-deployment.md` for rolling this out to teammates.
