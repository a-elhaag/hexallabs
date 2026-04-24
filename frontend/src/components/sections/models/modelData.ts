export type SpeedTier = 'Fast' | 'Medium' | 'Thorough'
export type ContextSize = 'Short' | 'Standard' | 'Long' | 'Extended'

export interface ModelData {
  id: string
  whitelabel: string
  realName: string
  provider: 'Anthropic' | 'Azure AI Foundry'
  role: string
  roleColor: string
  speedTier: SpeedTier
  contextSize: ContextSize
  contextWindow: string
  strengths: string[]
  bestFor: string[]
}

export const MODELS: ModelData[] = [
  {
    id: 'apex',
    whitelabel: 'Apex',
    realName: 'claude-opus-4-7',
    provider: 'Anthropic',
    role: 'Chairman',
    roleColor: '#6290c3',
    speedTier: 'Thorough',
    contextSize: 'Long',
    contextWindow: '200k',
    strengths: ['Synthesis', 'Reasoning', 'Nuance'],
    bestFor: ['Complex queries', 'Final answers', 'Council synthesis'],
  },
  {
    id: 'pulse',
    whitelabel: 'Pulse',
    realName: 'claude-sonnet-4-6',
    provider: 'Anthropic',
    role: 'Reasoning',
    roleColor: '#9b72cf',
    speedTier: 'Medium',
    contextSize: 'Long',
    contextWindow: '200k',
    strengths: ['Speed', 'Accuracy', 'Coding'],
    bestFor: ['Balanced tasks', 'Code', 'Analysis'],
  },
  {
    id: 'swift',
    whitelabel: 'Swift',
    realName: 'GPT-4o mini',
    provider: 'Azure AI Foundry',
    role: 'Fast Organizer',
    roleColor: '#5ba08a',
    speedTier: 'Fast',
    contextSize: 'Standard',
    contextWindow: '128k',
    strengths: ['Speed', 'Organization', 'Conciseness'],
    bestFor: ['Quick drafts', 'Summaries', 'Triage'],
  },
  {
    id: 'prism',
    whitelabel: 'Prism',
    realName: 'o4-mini',
    provider: 'Azure AI Foundry',
    role: 'Reasoning',
    roleColor: '#9b72cf',
    speedTier: 'Medium',
    contextSize: 'Standard',
    contextWindow: '128k',
    strengths: ['Logic', 'Math', 'Step-by-step'],
    bestFor: ['Math problems', 'Logical reasoning', 'Chain-of-thought'],
  },
  {
    id: 'depth',
    whitelabel: 'Depth',
    realName: 'GPT-4.1',
    provider: 'Azure AI Foundry',
    role: 'Deep Analysis',
    roleColor: '#6290c3',
    speedTier: 'Thorough',
    contextSize: 'Standard',
    contextWindow: '128k',
    strengths: ['Depth', 'Research', 'Detail'],
    bestFor: ['Research', 'Deep dives', 'Technical writing'],
  },
  {
    id: 'atlas',
    whitelabel: 'Atlas',
    realName: 'Llama 4 Scout',
    provider: 'Azure AI Foundry',
    role: 'Open-Source',
    roleColor: '#c09050',
    speedTier: 'Medium',
    contextSize: 'Standard',
    contextWindow: '64k',
    strengths: ['Open weights', 'Diversity', 'Balance'],
    bestFor: ['Diverse perspectives', 'Open-source tasks', 'General use'],
  },
  {
    id: 'horizon',
    whitelabel: 'Horizon',
    realName: 'Phi-4',
    provider: 'Azure AI Foundry',
    role: 'Long Context',
    roleColor: '#5b9062',
    speedTier: 'Thorough',
    contextSize: 'Extended',
    contextWindow: '1M+',
    strengths: ['Long docs', 'Coherence', 'Retention'],
    bestFor: ['Long documents', 'Books', 'Large codebases'],
  },
  {
    id: 'spark',
    whitelabel: 'Spark',
    realName: 'GPT-4.1 nano',
    provider: 'Azure AI Foundry',
    role: 'Utility',
    roleColor: '#a89080',
    speedTier: 'Fast',
    contextSize: 'Short',
    contextWindow: '32k',
    strengths: ['Cost', 'Speed', 'Utility'],
    bestFor: ['Prompt Forge', 'Prompt Lens', 'Quick ops'],
  },
]
