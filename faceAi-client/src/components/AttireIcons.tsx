interface IconProps {
  className?: string
}

export function GroomIcon({ className = 'h-5 w-5' }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* Head */}
      <circle cx="12" cy="7" r="4" />
      {/* Royal pagdi/safa accent line */}
      <path d="M9 5c1.5-1 4.5-1 6 0" />
      {/* Shoulders and tailored jacket */}
      <path d="M4 21v-2a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v2" />
      {/* Tuxedo/Sherwani lapel & bow tie */}
      <path d="M9.5 13l2.5 3 2.5-3" />
      <path d="M10.5 14.5h3" />
    </svg>
  )
}

export function BrideIcon({ className = 'h-5 w-5' }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* Head */}
      <circle cx="12" cy="7" r="4" />
      {/* Delicate veil flowing behind head */}
      <path d="M7 6c-1.5 2-2 6-1 11" strokeDasharray="1 1.5" />
      <path d="M17 6c1.5 2 2 6 1 11" strokeDasharray="1 1.5" />
      {/* Maang tikka hairline accent */}
      <path d="M12 2.5v1.5" />
      {/* Bridal lehenga/gown neckline and shoulders */}
      <path d="M5 21v-2a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v2" />
      {/* Bridal necklace / sweetheart curve */}
      <path d="M9 13.5c1 1.5 2 2 3 2s2-.5 3-2" />
    </svg>
  )
}
