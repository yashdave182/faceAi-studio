import { useState } from 'react'
import {
  bundleDownloadUrl,
  portraitDownloadUrl,
  portraitUrl,
  referenceUrl,
} from '../lib/api'
import { SCENES, type AttireStyle, type SceneKey, type SceneState } from '../types'
import { Lightbox } from './Lightbox'

interface Props {
  sessionId: string
  selected: SceneKey[]
  scenes: Record<string, SceneState>
  previewUrl: string | null
  attire: AttireStyle
  onRegenerate: (key: SceneKey, attire?: AttireStyle) => void
  onRegenerateAll: (attire?: AttireStyle) => void
  onStartOver: () => void
}

export function ResultsScreen({
  sessionId,
  selected,
  scenes,
  previewUrl,
  attire,
  onRegenerate,
  onRegenerateAll,
  onStartOver,
}: Props) {
  const [lightbox, setLightbox] = useState<SceneKey | 'reference' | null>(null)

  const activeScenes = SCENES.filter((scene) => selected.includes(scene.key))
  const completedCount = activeScenes.filter(
    (scene) => scenes[scene.key]?.status === 'completed',
  ).length

  const lightboxContent =
    lightbox === 'reference'
      ? {
          src: previewUrl ?? referenceUrl(sessionId),
          caption: 'Reference photograph',
          downloadUrl: referenceUrl(sessionId) + '&download=1',
        }
      : lightbox
        ? {
            src: portraitUrl(sessionId, lightbox, scenes[lightbox]?.version ?? 0),
            caption: SCENES.find((s) => s.key === lightbox)?.name ?? '',
            downloadUrl: portraitDownloadUrl(sessionId, lightbox),
          }
        : null

  return (
    <section className="fade-up mx-auto max-w-6xl px-6 pt-14 pb-24 sm:px-10">
      <div className="flex flex-wrap items-end justify-between gap-6 border-b border-beige pb-8">
        <div>
          <p className="text-[11px] tracking-[0.28em] text-stone uppercase">Step four · Results</p>
          <h1 className="mt-3 font-serif text-4xl font-medium text-charcoal sm:text-5xl">
            Your Indian wedding portraits.
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-stone">
            AI-generated Indian wedding portraits preserving your identity.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 border border-beige bg-white/70 px-3.5 py-1.5 text-xs text-charcoal">
              <span>{attire === 'groom' ? '🤵' : '👰'}</span>
              <span className="font-medium">
                {attire === 'groom' ? "Groom (Men's Attire)" : "Bride (Women's Attire)"}
              </span>
            </span>
            <button
              type="button"
              onClick={() => onRegenerateAll(attire === 'groom' ? 'bride' : 'groom')}
              className="border border-beige bg-white/40 px-3.5 py-1.5 text-xs tracking-[0.1em] text-stone uppercase transition-colors hover:border-olive hover:text-olive"
            >
              Switch to {attire === 'groom' ? "Bride (Women's)" : "Groom (Men's)"} & Regenerate
            </button>
          </div>
        </div>

        {previewUrl && (
          <button
            type="button"
            onClick={() => setLightbox('reference')}
            className="group flex items-center gap-3 border border-beige bg-white/50 p-3 pr-5 text-left transition-colors hover:border-stone"
          >
            <img
              src={previewUrl}
              alt="Reference photograph used for all portraits"
              className="h-14 w-14 object-cover"
            />
            <span className="text-xs leading-snug text-stone">
              Reference
              <br />
              photograph
            </span>
          </button>
        )}
      </div>

      <div className="mt-12 grid gap-8 md:grid-cols-3">
        {activeScenes.map((scene) => {
          const sceneState = scenes[scene.key]
          const status = sceneState?.status ?? 'idle'
          const generating = status === 'pending' || status === 'generating'

          return (
            <article key={scene.key} className="group flex flex-col">
              <div className="relative aspect-[3/4] overflow-hidden border border-beige bg-white/40">
                {status === 'completed' ? (
                  <button
                    type="button"
                    onClick={() => setLightbox(scene.key)}
                    className="block h-full w-full cursor-zoom-in"
                    aria-label={`Open ${scene.name} portrait at a larger size`}
                  >
                    <img
                      src={portraitUrl(sessionId, scene.key, sceneState?.version ?? 0)}
                      alt={`${scene.name} wedding portrait`}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
                    />
                  </button>
                ) : generating ? (
                  <div className="flex h-full flex-col items-center justify-center gap-3">
                    <span className="slow-pulse h-1.5 w-10 bg-olive" />
                    <p className="text-xs tracking-[0.18em] text-stone uppercase">
                      {status === 'generating' ? 'Generating…' : 'Queued'}
                    </p>
                  </div>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center gap-4 px-6 text-center">
                    <p className="font-serif text-xl text-charcoal">Generation failed</p>
                    {sceneState?.error && (
                      <p className="text-xs leading-relaxed text-stone">{sceneState.error}</p>
                    )}
                    <button
                      type="button"
                      onClick={() => onRegenerate(scene.key)}
                      className="border border-beige px-5 py-2 text-xs tracking-[0.14em] uppercase transition-colors hover:border-olive hover:text-olive"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>

              <div className="mt-4 flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-serif text-xl text-charcoal">{scene.name}</h2>
                  <p className="mt-1 text-xs tracking-[0.14em] text-stone uppercase">
                    {status === 'completed'
                      ? 'Completed'
                      : status === 'failed'
                        ? 'Not generated'
                        : 'In progress'}
                  </p>
                </div>
                {status === 'completed' && (
                  <div className="flex shrink-0 items-center gap-4 pt-1">
                    <a
                      href={portraitDownloadUrl(sessionId, scene.key)}
                      download
                      className="text-xs tracking-[0.14em] text-olive uppercase underline underline-offset-4 hover:text-olive-dark"
                    >
                      Download
                    </a>
                    <button
                      type="button"
                      onClick={() => onRegenerate(scene.key)}
                      className="text-xs tracking-[0.14em] text-stone uppercase underline underline-offset-4 hover:text-charcoal"
                    >
                      Regenerate
                    </button>
                  </div>
                )}
              </div>
            </article>
          )
        })}
      </div>

      <div className="mt-14 flex flex-wrap items-center justify-between gap-6 border-t border-beige pt-8">
        <div className="flex flex-wrap items-center gap-6">
          <button
            type="button"
            onClick={() => onRegenerateAll()}
            className="bg-charcoal px-10 py-3.5 text-sm tracking-[0.14em] text-ivory uppercase transition-colors duration-200 hover:bg-olive"
          >
            Generate another set
          </button>
          <button
            type="button"
            onClick={onStartOver}
            className="border border-beige px-10 py-3.5 text-sm tracking-[0.14em] text-charcoal uppercase transition-colors duration-200 hover:border-stone"
          >
            Start over
          </button>
        </div>

        {completedCount > 0 && (
          <a
            href={bundleDownloadUrl(sessionId)}
            download
            className="text-xs tracking-[0.14em] text-stone uppercase underline underline-offset-4 hover:text-charcoal"
          >
            Download all ({completedCount}) as ZIP
          </a>
        )}
      </div>

      {lightboxContent && (
        <Lightbox
          src={lightboxContent.src}
          caption={lightboxContent.caption}
          downloadUrl={lightboxContent.downloadUrl}
          onClose={() => setLightbox(null)}
        />
      )}
    </section>
  )
}
