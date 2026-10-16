import { useEffect } from 'react'

interface Props {
  src: string
  caption: string
  downloadUrl?: string
  onClose: () => void
}

export function Lightbox({ src, caption, downloadUrl, onClose }: Props) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [onClose])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`${caption} — enlarged view`}
      onClick={onClose}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-charcoal/90 p-6"
    >
      <img
        src={src}
        alt={caption}
        onClick={(event) => event.stopPropagation()}
        className="max-h-[80vh] max-w-full object-contain shadow-2xl"
      />
      <div
        onClick={(event) => event.stopPropagation()}
        className="mt-6 flex items-center gap-8 text-ivory"
      >
        <span className="font-serif text-xl italic">{caption}</span>
        {downloadUrl && (
          <a
            href={downloadUrl}
            download
            className="text-xs tracking-[0.18em] uppercase underline underline-offset-4 hover:text-beige"
          >
            Download
          </a>
        )}
        <button
          type="button"
          onClick={onClose}
          className="text-xs tracking-[0.18em] uppercase underline underline-offset-4 hover:text-beige"
        >
          Close
        </button>
      </div>
    </div>
  )
}
