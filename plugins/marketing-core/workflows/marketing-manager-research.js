export const meta = {
  name: 'marketing-manager-research',
  description: 'Research a content brief and generate content concepts (stages 1-2 of the marketing-manager pipeline)',
  phases: [
    { title: 'Research' },
    { title: 'Concept' },
  ],
}

// args: { briefPath: absolute path to 00-brief.md, runFolder: absolute path to the run folder }
const briefPath = args.briefPath
const runFolder = args.runFolder
const researchPath = `${runFolder}/01-research.md`
const conceptPath = `${runFolder}/02-concept.md`

phase('Research')
await agent(
  `Read the brief file at ${briefPath} in full, then follow your own instructions to research this topic and write your findings to ${researchPath}.`,
  { label: 'research-analyst', agentType: 'marketing-core:research-analyst', phase: 'Research' }
)

phase('Concept')
await agent(
  `Read the brief file at ${briefPath} and the research file at ${researchPath} in full, then follow your own instructions to generate content concepts and write them to ${conceptPath}.`,
  { label: 'content-strategist', agentType: 'marketing-core:content-strategist', phase: 'Concept' }
)

return { briefPath, runFolder, researchPath, conceptPath }
