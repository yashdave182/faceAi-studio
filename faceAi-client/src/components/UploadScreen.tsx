import { useEffect, useRef, useState } from 'react'
import { confirmConsent, uploadReference } from '../lib/api'
import type { AttireStyle } from '../types'

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
const MAX_BYTES = 10 * 1024 * 1024

interface Props {
  initialAttire?: AttireStyle
  onUploaded: (sessionId: string, previewUrl: string, attire: AttireStyle) => void
}

export function UploadScreen({ initialAttire, onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [attire, setAttire] = useState<AttireStyle>(initialAttire ?? 'groom')
  const [consent, setConsent] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  function acceptFile(candidate: File | undefined) {
    if (!candidate) return
    setError(null)

    if (!ALLOWED_TYPES.includes(candidate.type)) {
      setError('That file type is not supported. Please use a JPG, PNG or WebP photograph.')
      return
    }
    if (candidate.size > MAX_BYTES) {
      setError('That photograph is larger than 10 MB. Please choose a smaller file.')
      return
    }
    if (candidate.size === 0) {
      setError('That file appears to be empty. Please choose another photograph.')
      return
    }

    setFile(candidate)
    setPreviewUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous)
      return URL.createObjectURL(candidate)
    })
  }

  async function handleContinue() {
    if (!file || !consent || busy) return
    setBusy(true)
    setError(null)
    try {
      const session = await uploadReference(file)
      await confirmConsent(session.session_id)
      onUploaded(session.session_id, previewUrl!, attire)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The photograph could not be processed.')
      setBusy(false)
    }
  }

  return (
    <section className="fade-up mx-auto max-w-3xl px-6 pt-16 pb-24 sm:px-10">
      <div className="max-w-xl">
        <p className="mb-6 text-[11px] tracking-[0.28em] text-stone uppercase">Step one · Reference photograph</p>
        <h1 className="font-serif text-5xl leading-[1.05] font-medium text-charcoal sm:text-6xl">
          One face. Three wedding stories.
        </h1>
        <p className="mt-6 max-w-md text-base leading-relaxed text-stone">
          Explore three wedding aesthetics using one reference photograph. The same photograph is
          used for every portrait.
        </p>
      </div>

      <div className="mt-14">
        <label
          htmlFor="reference-photo"
          onDragOver={(event) => {
            event.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragOver(false)
            acceptFile(event.dataTransfer.files?.[0])
          }}
          className={`block cursor-pointer border border-dashed transition-colors duration-200 ${
            dragOver ? 'border-olive bg-white/70' : 'border-beige bg-white/40 hover:border-stone'
          }`}
        >
          <input
            ref={inputRef}
            id="reference-photo"
            type="file"
            accept={ALLOWED_TYPES.join(',')}
            className="sr-only"
            onChange={(event) => acceptFile(event.target.files?.[0])}
          />

          {previewUrl ? (
            <div className="flex flex-col items-center gap-5 px-8 py-10">
              <img
                src={previewUrl}
                alt="Preview of the uploaded reference photograph"
                className="max-h-72 w-auto max-w-full object-contain shadow-sm"
              />
              <span className="text-sm text-stone underline underline-offset-4">
                Replace photograph
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 px-8 py-20 text-center">
              <svg
                viewBox="0 0 40 40"
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                className="h-9 w-9 text-olive"
                aria-hidden="true"
              >
                <path d="M20 27V13" />
                <path d="M14 19l6-6 6 6" />
                <path d="M8 26v5a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-5" />
              </svg>
              <p className="font-serif text-2xl text-charcoal">
                Drop a photograph here, or browse
              </p>
              <p className="text-sm text-stone">JPG, PNG or WebP · up to 10 MB</p>
            </div>
          )}
        </label>

        {error && (
          <p role="alert" className="mt-4 border-l-2 border-charcoal/40 pl-4 text-sm text-charcoal">
            {error}
          </p>
        )}

        {/* Gender / Attire Selection */}
        <div className="mt-8 border border-beige bg-white/70 p-6 sm:p-7">
          <p className="text-[10px] tracking-[0.24em] text-stone uppercase">Required · Person In Photograph</p>
          <h2 className="mt-1 font-serif text-2xl font-medium text-charcoal">
            Is the person in this photograph Male or Female?
          </h2>
          <p className="mt-1 text-xs text-stone">
            Select the gender so our AI generates authentic, tailored Indian groom or bridal wedding attire.
          </p>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setAttire('groom')}
              className={`flex flex-col items-center justify-center gap-2.5 border p-5 text-center transition-all ${
                attire === 'groom'
                  ? 'border-olive bg-white ring-2 ring-olive/20'
                  : 'border-beige bg-white/40 hover:border-stone'
              }`}
            >
              <span className="text-3xl">🤵</span>
              <div>
                <p className="font-serif text-lg font-medium text-charcoal">Male (Groom)</p>
                <p className="text-[11px] text-stone">Royal Sherwani, Safa & Bandhgala</p>
              </div>
              <span
                className={`mt-1 inline-flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase ${
                  attire === 'groom' ? 'font-medium text-olive' : 'text-stone'
                }`}
              >
                <span
                  className={`h-2 w-2 rounded-full ${attire === 'groom' ? 'bg-olive' : 'bg-beige'}`}
                />
                {attire === 'groom' ? 'Selected' : 'Select Male'}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setAttire('bride')}
              className={`flex flex-col items-center justify-center gap-2.5 border p-5 text-center transition-all ${
                attire === 'bride'
                  ? 'border-olive bg-white ring-2 ring-olive/20'
                  : 'border-beige bg-white/40 hover:border-stone'
              }`}
            >
              <span className="text-3xl">👰</span>
              <div>
                <p className="font-serif text-lg font-medium text-charcoal">Female (Bride)</p>
                <p className="text-[11px] text-stone">Bridal Lehenga, Kundan & Dupatta</p>
              </div>
              <span
                className={`mt-1 inline-flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase ${
                  attire === 'bride' ? 'font-medium text-olive' : 'text-stone'
                }`}
              >
                <span
                  className={`h-2 w-2 rounded-full ${attire === 'bride' ? 'bg-olive' : 'bg-beige'}`}
                />
                {attire === 'bride' ? 'Selected' : 'Select Female'}
              </span>
            </button>
          </div>
        </div>

        <div className="mt-10 border-t border-beige pt-8">
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
              className="mt-0.5 h-4 w-4 accent-olive"
            />
            <span className="max-w-xl text-sm leading-relaxed text-stone">
              I confirm that the person in this photograph is a consenting adult and has agreed to
              its use for generating wedding portraits.
            </span>
          </label>

          <div className="mt-8 flex flex-wrap items-center gap-6">
            <button
              type="button"
              onClick={handleContinue}
              disabled={!file || !consent || busy}
              className="bg-charcoal px-10 py-3.5 text-sm tracking-[0.14em] text-ivory uppercase transition-colors duration-200 hover:bg-olive disabled:cursor-not-allowed disabled:bg-beige disabled:text-stone"
            >
              {busy ? 'Preparing…' : 'Continue'}
            </button>
            <p className="text-xs text-stone">
              Your photograph is processed on our server and removed when you start over.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
