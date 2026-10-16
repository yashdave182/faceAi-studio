import { SCENES, type SceneKey } from '../types'
import { SceneIllustration } from './SceneIllustration'

interface Props {
  previewUrl: string | null
  selected: SceneKey[]
  onToggle: (key: SceneKey) => void
  onGenerate: () => void
  busy: boolean
  error: string | null
}

export function SceneSelectScreen({ previewUrl, selected, onToggle, onGenerate, busy, error }: Props) {
  return (
    <section className="fade-up mx-auto max-w-5xl px-6 pt-14 pb-24 sm:px-10">
      <div className="flex flex-wrap items-center gap-6 border-b border-beige pb-8">
        {previewUrl && (
          <img
            src={previewUrl}
            alt="Your reference photograph"
            className="h-20 w-20 border border-beige object-cover"
          />
        )}
        <div>
          <p className="text-[11px] tracking-[0.28em] text-stone uppercase">Step two · Choose your scenes</p>
          <h1 className="mt-2 font-serif text-3xl font-medium text-charcoal sm:text-4xl">
            Where should this story take place?
          </h1>
        </div>
      </div>

      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {SCENES.map((scene) => {
          const isSelected = selected.includes(scene.key)
          return (
            <button
              key={scene.key}
              type="button"
              aria-pressed={isSelected}
              onClick={() => onToggle(scene.key)}
              className={`group border p-6 text-left transition-all duration-200 ${
                isSelected
                  ? 'border-olive bg-white'
                  : 'border-beige bg-white/40 hover:border-stone'
              }`}
            >
              <div className="flex h-28 items-center justify-center border-b border-beige pb-5 text-olive">
                <SceneIllustration scene={scene.key} className="h-20 w-auto" />
              </div>
              <div className="pt-5">
                <p className="text-[10px] tracking-[0.24em] text-stone uppercase">{scene.tagline}</p>
                <h2 className="mt-2 font-serif text-2xl font-medium text-charcoal">{scene.name}</h2>
                <p className="mt-2 text-sm leading-relaxed text-stone">{scene.description}</p>
              </div>
              <div className="mt-5 flex items-center gap-2 text-xs tracking-[0.18em] uppercase">
                <span
                  className={`inline-block h-2 w-2 rounded-full transition-colors ${
                    isSelected ? 'bg-olive' : 'bg-beige'
                  }`}
                />
                <span className={isSelected ? 'text-olive' : 'text-stone'}>
                  {isSelected ? 'Selected' : 'Not selected'}
                </span>
              </div>
            </button>
          )
        })}
      </div>

      {error && (
        <p role="alert" className="mt-8 border-l-2 border-charcoal/40 pl-4 text-sm text-charcoal">
          {error}
        </p>
      )}

      <div className="mt-12 flex flex-wrap items-center gap-6 border-t border-beige pt-8">
        <button
          type="button"
          onClick={onGenerate}
          disabled={selected.length === 0 || busy}
          className="bg-charcoal px-10 py-3.5 text-sm tracking-[0.14em] text-ivory uppercase transition-colors duration-200 hover:bg-olive disabled:cursor-not-allowed disabled:bg-beige disabled:text-stone"
        >
          {busy ? 'Starting…' : 'Generate portraits'}
        </button>
        <p className="text-xs text-stone">
          All three scenes are selected by default. Deselect any you don't need.
        </p>
      </div>
    </section>
  )
}
