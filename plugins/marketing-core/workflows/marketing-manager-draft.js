export const meta = {
  name: 'marketing-manager-draft',
  description: 'Write channel drafts from a chosen concept and run an SEO review (stages 3-4 of the marketing-manager pipeline)',
  phases: [
    { title: 'Draft' },
    { title: 'SEO Review' },
  ],
}

// args: { briefPath, runFolder, researchPath, conceptPath: absolute paths; chosenConcept: e.g. "A" }
const briefPath = args.briefPath
const runFolder = args.runFolder
const researchPath = args.researchPath
const conceptPath = args.conceptPath
const chosenConcept = args.chosenConcept
const seoReviewPath = `${runFolder}/04-seo-review.md`

phase('Draft')
await agent(
  `Read the brief file at ${briefPath}, the research file at ${researchPath}, and the concept file at ${conceptPath} in full. Concept ${chosenConcept} was chosen. Follow your own instructions to write one full draft file per channel in ${runFolder}.`,
  { label: 'content-writer', agentType: 'marketing-core:content-writer', phase: 'Draft' }
)

phase('SEO Review')
await agent(
  `Find every 03-draft-*.md file in ${runFolder} (use Glob) and read them along with the research file at ${researchPath}. Follow your own instructions to review them for on-page/keyword SEO and write your review to ${seoReviewPath}.`,
  { label: 'seo-specialist', agentType: 'marketing-core:seo-specialist', phase: 'SEO Review' }
)

return { runFolder, seoReviewPath }
