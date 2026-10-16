import type { SceneKey } from '../types'

interface Props {
  scene: SceneKey
  className?: string
}

export function SceneIllustration({ scene, className }: Props) {
  const stroke = 'currentColor'

  if (scene === 'luxury_cinematic') {
    return (
      <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
        <path d="M18 68V32c0-12 8-22 18-22s18 10 18 22v36" stroke={stroke} strokeWidth="1" />
        <path d="M42 10v58M18 68h48" stroke={stroke} strokeWidth="1" />
        <path d="M66 68V38c0-8 6-14 13-14s13 6 13 14v30" stroke={stroke} strokeWidth="1" />
        <path d="M79 24v44" stroke={stroke} strokeWidth="1" />
        <path d="M6 68h108" stroke={stroke} strokeWidth="1" />
        <circle cx="36" cy="50" r="7" stroke={stroke} strokeWidth="1" />
        <path d="M29 46c2 2 5 3 7 3s5-1 7-3" stroke={stroke} strokeWidth="0.75" />
        <path d="M99 68V26l6-8 6 8v42" stroke={stroke} strokeWidth="1" />
      </svg>
    )
  }

  if (scene === 'beach_destination') {
    return (
      <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
        <circle cx="88" cy="22" r="9" stroke={stroke} strokeWidth="1" />
        <path d="M88 5v5M88 34v5M105 22h-5M76 22h-5M100 10l-3.5 3.5M79.5 30.5 76 34M100 34l-3.5-3.5M79.5 13.5 76 10" stroke={stroke} strokeWidth="1" />
        <path d="M4 56c10-6 18-6 28 0s18 6 28 0 18-6 28 0 18 6 28 0" stroke={stroke} strokeWidth="1" />
        <path d="M4 64c10-6 18-6 28 0s18 6 28 0 18-6 28 0 18 6 28 0" stroke={stroke} strokeWidth="1" />
        <path d="M22 52c0-10 6-18 14-22 8 4 14 12 14 22" stroke={stroke} strokeWidth="1" />
        <path d="M30 52c0-7 3-13 6-16 3 3 6 9 6 16" stroke={stroke} strokeWidth="0.75" />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
      <path d="M60 12v56" stroke={stroke} strokeWidth="1" />
      <path d="M60 20c-8-10-22-12-30-8 2 10 12 18 30 16" stroke={stroke} strokeWidth="1" />
      <path d="M60 20c8-10 22-12 30-8-2 10-12 18-30 16" stroke={stroke} strokeWidth="1" />
      <path d="M60 32c-6-8-18-10-24-6 2 8 10 14 24 12" stroke={stroke} strokeWidth="1" />
      <path d="M60 32c6-8 18-10 24-6-2 8-10 14-24 12" stroke={stroke} strokeWidth="1" />
      <ellipse cx="60" cy="53" rx="9" ry="11" stroke={stroke} strokeWidth="1" />
      <path d="M55 49h2.5M62.5 49H65" stroke={stroke} strokeWidth="0.75" />
      <path d="M26 68c8-4 16-4 24 0M70 68c8-4 16-4 24 0" stroke={stroke} strokeWidth="0.75" />
      <circle cx="60" cy="53" r="14" stroke={stroke} strokeWidth="0.5" strokeDasharray="2 4" />
    </svg>
  )
}
