import type { AttireStyle, SceneKey, SessionStatus, UploadResponse } from '../types'

export interface ServerConfig {
  model: string | null
  fallback_models: string[]
  model_chain: string[]
  gemini_key_configured: boolean
  fal_key_configured: boolean
  api_key_configured: boolean
}

const rawBase = (import.meta.env.VITE_API_BASE ?? '').trim().replace(/\/+$/, '')
const API_BASE = rawBase ? (rawBase.startsWith('http') ? rawBase : `https://${rawBase}`) : ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new Error('Could not reach the studio service. Check that the backend is running.')
  }

  if (!response.ok) {
    let detail = 'Something went wrong. Please try again.'
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') detail = data.detail
    } catch {
      /* keep default message */
    }
    throw new Error(detail)
  }

  return (await response.json()) as T
}

export function getConfig(): Promise<ServerConfig> {
  return request<ServerConfig>('/api/config')
}

export function uploadReference(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return request<UploadResponse>('/api/upload', { method: 'POST', body: formData })
}

export function confirmConsent(sessionId: string): Promise<{ status: string }> {
  return request(`/api/sessions/${sessionId}/consent`, { method: 'POST' })
}

export function startGeneration(
  sessionId: string,
  scenes: SceneKey[],
  attire: AttireStyle = 'groom',
): Promise<{ status: string }> {
  return request(`/api/sessions/${sessionId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenes, attire }),
  })
}

export function getStatus(sessionId: string): Promise<SessionStatus> {
  return request<SessionStatus>(`/api/sessions/${sessionId}/status`)
}

export function resetSession(sessionId: string): Promise<{ status: string }> {
  return request(`/api/sessions/${sessionId}/reset`, { method: 'POST' })
}

export function referenceUrl(sessionId: string, version = 0): string {
  return `${API_BASE}/api/sessions/${sessionId}/reference?v=${version}`
}

export function portraitUrl(sessionId: string, scene: string, version = 0): string {
  return `${API_BASE}/api/sessions/${sessionId}/portrait/${scene}?v=${version}`
}

export function portraitDownloadUrl(sessionId: string, scene: string): string {
  return `${API_BASE}/api/sessions/${sessionId}/portrait/${scene}?download=1`
}

export function bundleDownloadUrl(sessionId: string): string {
  return `${API_BASE}/api/sessions/${sessionId}/download`
}
