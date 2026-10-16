export type SceneKey = 'luxury_cinematic' | 'beach_destination' | 'traditional_indian'

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
    tagline: 'The Royal Palace',
    description: 'Grand heritage palace courtyard, sandstone jharokhas, warm chandeliers & royal diyas.',
    ragBadge: 'Visual RAG · 3/4 Regal Anchor',
    ragAngle: '30° Stately Perspective',
  },
  {
    key: 'beach_destination',
    name: 'Goa Coastal Mandap',
    tagline: 'The Sunset Mandap',
    description: 'Scenic beachside sunset, fresh mogra & marigold mandap, elegant coastal festive attire.',
    ragBadge: 'Visual RAG · Candid Sunset Anchor',
    ragAngle: 'Dynamic Tilt & Smile',
  },
  {
    key: 'traditional_indian',
    name: 'Grand Vivah Mandap',
    tagline: 'The Sacred Vivah',
    description: 'Traditional Vedic vivah ceremony, warm havan glow, rich silk & zardozi embroidery.',
    ragBadge: 'Visual RAG · Frontal Vedic Anchor',
    ragAngle: '0° Symmetrical Focus',
  },
]


