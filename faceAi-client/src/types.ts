export type SceneKey =
  | 'luxury_cinematic'
  | 'beach_destination'
  | 'traditional_indian'
  | 'baraat_celebration'
  | 'sangeet_glamour'
  | 'romantic_vows'

export type AttireStyle = 'groom' | 'bride'

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
  attire?: AttireStyle
  scenes: Record<string, SceneState>
  all_settled: boolean
}

export interface UploadResponse {
  session_id: string
  preview: string
  size: number
  content_type: string
}

export interface IdentityAnchorData {
  scene_key: SceneKey
  anchor_key: string
  title: string
  angle: string
  expression: string
  lighting: string
  vector_tag: string
  status: 'indexed' | 'ready'
  confidence: number
  has_preview: boolean
}

export interface IdentityBankResponse {
  status: string
  method: string
  anchors: IdentityAnchorData[]
}

export interface SceneDefinition {
  key: SceneKey
  name: string
  tagline: string
  description: string
  ragBadge: string
  ragAngle: string
}

export const SCENES: SceneDefinition[] = [
  {
    key: 'luxury_cinematic',
    name: 'Royal Palace Heritage',
    tagline: 'The Royal Balcony',
    description: '3/4 contemplative glance from a carved marble palace balcony at golden sunset.',
    ragBadge: 'Visual RAG · 3/4 Regal Balcony',
    ragAngle: '30° Stately Perspective',
  },
  {
    key: 'beach_destination',
    name: 'Goa Coastal Shoreline',
    tagline: 'The Candid Laugh',
    description: 'Walking casually along the ocean surf, candid radiant laughter in golden twilight.',
    ragBadge: 'Visual RAG · Candid Shoreline Laugh',
    ragAngle: 'Dynamic Tilt & Smile',
  },
  {
    key: 'traditional_indian',
    name: 'Grand Vivah Mandap',
    tagline: 'The Sacred Agni',
    description: 'Intimate close-up with folded hands in Namaste before the glowing havan fire.',
    ragBadge: 'Visual RAG · Sacred Agni Close-up',
    ragAngle: 'Intimate 85mm Focus',
  },
  {
    key: 'baraat_celebration',
    name: 'Baraat Celebration',
    tagline: 'The Baraat Dance',
    description: 'Dynamic celebratory action dancing mid-motion under falling crimson rose petals.',
    ragBadge: 'Visual RAG · Baraat Action Vector',
    ragAngle: 'Dynamic High-Energy Motion',
  },
  {
    key: 'sangeet_glamour',
    name: 'Sangeet Night Luxury',
    tagline: 'The Midnight Sangeet',
    description: 'Over-the-shoulder confident glance, adjusting luxury watch under moody chandeliers.',
    ragBadge: 'Visual RAG · Sangeet Editorial Profile',
    ragAngle: 'Over-the-Shoulder Glance',
  },
  {
    key: 'romantic_vows',
    name: 'The Golden Hour Vows',
    tagline: 'The Eternal Vows',
    description: 'Tender heartfelt gaze with hand on heart before a cascading floral canopy.',
    ragBadge: 'Visual RAG · Tender Vows Anchor',
    ragAngle: 'Heartfelt Emotive Gaze',
  },
]


