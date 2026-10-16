export type SceneKey = 'luxury_cinematic' | 'beach_destination' | 'traditional_indian'

export type SceneStatus = 'idle' | 'pending' | 'generating' | 'completed' | 'failed'

export interface SceneState {
  status: SceneStatus
  error: string | null
  version: number
}

export interface SessionStatus {
  session_id: string
  consent_confirmed: boolean
  has_reference: boolean
  scenes: Record<string, SceneState>
  all_settled: boolean
}

export interface UploadResponse {
  session_id: string
  preview: string
  size: number
  content_type: string
}

export interface SceneDefinition {
  key: SceneKey
  name: string
  tagline: string
  description: string
}

export const SCENES: SceneDefinition[] = [
  {
    key: 'luxury_cinematic',
    name: 'Luxury Cinematic',
    tagline: 'The grand venue',
    description: 'Elegant venue, sophisticated styling, dramatic cinematic lighting.',
  },
  {
    key: 'beach_destination',
    name: 'Beach / Destination',
    tagline: 'The shoreline vow',
    description: 'Oceanfront wedding, natural sunlight, destination wedding styling.',
  },
  {
    key: 'traditional_indian',
    name: 'Traditional Indian',
    tagline: 'The timeless ceremony',
    description: 'Culturally appropriate wedding attire, traditional jewellery, detailed décor.',
  },
]
