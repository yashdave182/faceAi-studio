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

  if (scene === 'traditional_indian') {
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

  if (scene === 'baraat_celebration') {
    return (
      <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
        <ellipse cx="60" cy="42" rx="22" ry="16" stroke={stroke} strokeWidth="1" />
        <path d="M38 42c0-8 10-14 22-14s22 6 22 14" stroke={stroke} strokeWidth="1" />
        <path d="M44 32l32 20M44 52l32-20" stroke={stroke} strokeWidth="0.75" />
        <circle cx="28" cy="20" r="3" stroke={stroke} strokeWidth="0.75" />
        <circle cx="92" cy="18" r="2.5" stroke={stroke} strokeWidth="0.75" />
        <circle cx="60" cy="14" r="3.5" stroke={stroke} strokeWidth="0.75" />
        <path d="M22 66l12-12M98 66l-12-12" stroke={stroke} strokeWidth="1" />
        <path d="M12 40c4-4 8 0 12-4M96 36c4-4 8 0 12-4" stroke={stroke} strokeWidth="0.75" />
      </svg>
    )
  }

  if (scene === 'sangeet_glamour') {
    return (
      <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
        <path d="M60 8v16M48 24h24M38 34l22-10 22 10" stroke={stroke} strokeWidth="1" />
        <circle cx="60" cy="38" r="5" stroke={stroke} strokeWidth="0.75" />
        <circle cx="44" cy="46" r="3" stroke={stroke} strokeWidth="0.75" />
        <circle cx="76" cy="46" r="3" stroke={stroke} strokeWidth="0.75" />
        <path d="M44 49v10M76 49v10M60 43v22" stroke={stroke} strokeWidth="0.75" />
        <path d="M30 68h60" stroke={stroke} strokeWidth="1" />
        <path d="M22 28l4 4M98 28l-4 4M20 54l5-2M100 54l-5-2" stroke={stroke} strokeWidth="0.75" />
      </svg>
    )
  }

  // romantic_vows
  return (
    <svg viewBox="0 0 120 80" fill="none" className={className} aria-hidden="true">
      <path d="M24 68V34c0-14 16-24 36-24s36 10 36 24v34" stroke={stroke} strokeWidth="1" />
      <path d="M24 68h72" stroke={stroke} strokeWidth="1" />
      <circle cx="52" cy="46" r="12" stroke={stroke} strokeWidth="1" />
      <circle cx="68" cy="46" r="12" stroke={stroke} strokeWidth="1" />
      <path d="M60 38c3-4 8-4 10 0" stroke={stroke} strokeWidth="0.75" />
      <circle cx="36" cy="24" r="3" stroke={stroke} strokeWidth="0.5" />
      <circle cx="84" cy="24" r="3" stroke={stroke} strokeWidth="0.5" />
      <circle cx="60" cy="14" r="3" stroke={stroke} strokeWidth="0.5" />
    </svg>
  )
}
