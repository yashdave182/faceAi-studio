import { SCENES, type AttireStyle, type SceneKey } from '../types'
import { BrideIcon, GroomIcon } from './AttireIcons'
import { SceneIllustration } from './SceneIllustration'

interface Props {
  sessionId?: string | null
  selected: SceneKey[]
  attire: AttireStyle
  onSelectAttire: (attire: AttireStyle) => void
  onToggle: (key: SceneKey) => void
  onGenerate: () => void
  busy: boolean
  error: string | null
}

export function SceneSelectScreen({
  selected,
  attire,
  onSelectAttire,
  onToggle,
  onGenerate,
  busy,
  error,
}: Props) {
  return (
    <section className="fade-up mx-auto max-w-5xl px-6 pt-14 pb-24 sm:px-10">
      <div className="border-b border-beige pb-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-[11px] tracking-[0.28em] text-stone uppercase">Step two · Choose your scenes</p>
          <span className="inline-flex items-center gap-1.5 border border-olive/30 bg-olive/5 px-2.5 py-1 text-[10px] font-medium tracking-[0.16em] text-olive uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-olive animate-pulse" />
            Visual RAG Active
          </span>
        </div>
        <h1 className="mt-2 font-serif text-3xl font-medium text-charcoal sm:text-4xl">
          Where should this Indian wedding story take place?
        </h1>
      </div>

      {/* Visual RAG Identity Matrix Dashboard */}
      <div className="mt-8 border border-beige bg-white/70 p-6 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-beige/60 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs">⚡</span>
              <p className="text-[10px] font-semibold tracking-[0.24em] text-olive uppercase">
                Visual RAG · Canonical Identity Matrix
              </p>
            </div>
            <h2 className="mt-1 font-serif text-2xl font-medium text-charcoal">
              Multi-View Canonical Bootstrapping
            </h2>
            <p className="mt-1 max-w-2xl text-xs text-stone">
              To eliminate single-angle facial distortion and stiff passport poses, our Visual RAG engine maps your photograph into 6 distinct canonical 3D perspectives and natural emotional expressions. Each scene dynamically conditions pose, lighting, and facial geometry.
            </p>
          </div>
          <div className="rounded border border-olive/20 bg-ivory px-3 py-2 text-right">
            <p className="text-[10px] tracking-[0.18em] text-stone uppercase">RAG Vector Bank</p>
            <p className="text-xs font-semibold text-charcoal">6 Multi-View Anchors Ready</p>
          </div>
        </div>

        {/* 6 Canonical Anchors Grid */}
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 01</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">30° Regal</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Contemplative Stately</h3>
            <p className="mt-0.5 text-[11px] text-stone">3/4 turned glance · Balustrade lean</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Royal Palace Heritage
            </div>
          </div>

          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 02</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">Candid Motion</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Joyful Beach Laugh</h3>
            <p className="mt-0.5 text-[11px] text-stone">Mid-stride walking · Authentic eye crinkles</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Goa Coastal Mandap
            </div>
          </div>

          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 03</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">0° Intimate</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Sacred Namaste Pose</h3>
            <p className="mt-0.5 text-[11px] text-stone">85mm close-up · Reverent serene smile</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Sacred Agni Vivah
            </div>
          </div>

          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 04</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">High Action</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Baraat Celebration</h3>
            <p className="mt-0.5 text-[11px] text-stone">Dancing mid-motion · Exuberant joy</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Baraat Euphoria
            </div>
          </div>

          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 05</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">45° Profile</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Sangeet Chiaroscuro</h3>
            <p className="mt-0.5 text-[11px] text-stone">Over-the-shoulder · Confident smirk</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Sangeet Midnight
            </div>
          </div>

          <div className="border border-beige/80 bg-ivory/60 p-3.5 transition-colors hover:border-olive/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] tracking-[0.18em] text-stone uppercase">Anchor 06</span>
              <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium text-olive uppercase">Golden Hour</span>
            </div>
            <h3 className="mt-1.5 font-serif text-sm font-medium text-charcoal">Heartfelt Vows</h3>
            <p className="mt-0.5 text-[11px] text-stone">Hand on chest · Tender romantic gaze</p>
            <div className="mt-2 border-t border-beige/40 pt-1.5 text-[10px] text-stone">
              <span className="text-charcoal font-medium">Scene:</span> Golden Hour Vows
            </div>
          </div>
        </div>
      </div>

      {/* Wedding Role & Attire Selection */}
      <div className="mt-8 border border-beige bg-white/70 p-6 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] tracking-[0.24em] text-stone uppercase">Wedding Role & Attire</p>
            <h2 className="mt-1 font-serif text-2xl font-medium text-charcoal">Who is this portrait for?</h2>
            <p className="mt-1 text-xs text-stone">
              Select your role so the AI creates authentic Indian groom or bridal wedding attire.
            </p>
          </div>
          <div className="flex border border-beige bg-ivory p-1">
            <button
              type="button"
              onClick={() => onSelectAttire('groom')}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs tracking-[0.14em] uppercase transition-all ${
                attire === 'groom'
                  ? 'bg-charcoal font-medium text-ivory shadow-sm'
                  : 'text-stone hover:text-charcoal'
              }`}
            >
              <GroomIcon className="h-4 w-4" />
              <span>Groom (Men's Attire)</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectAttire('bride')}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs tracking-[0.14em] uppercase transition-all ${
                attire === 'bride'
                  ? 'bg-charcoal font-medium text-ivory shadow-sm'
                  : 'text-stone hover:text-charcoal'
              }`}
            >
              <BrideIcon className="h-4 w-4" />
              <span>Bride (Women's Attire)</span>
            </button>
          </div>
        </div>

        <div className="mt-4 border-t border-beige/60 pt-3 text-[11px] text-stone">
          {attire === 'groom' ? (
            <p>
              ✨ <strong className="text-charcoal">Groom Styling:</strong> Royal embroidered silk sherwani, safa pagdi (turban), layered pearl kantha mala, and tailored bandhgala for an authentic masculine silhouette.
            </p>
          ) : (
            <p>
              ✨ <strong className="text-charcoal">Bride Styling:</strong> Opulent red & pastel bridal lehengas with antique gold zardozi, sheer dupatta veil, uncut polki kundan jewelry sets, and maang tikka.
            </p>
          )}
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
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <p className="text-[10px] tracking-[0.24em] text-stone uppercase">{scene.tagline}</p>
                  <span className="rounded bg-olive/10 px-1.5 py-0.5 text-[9px] font-medium tracking-[0.1em] text-olive uppercase">
                    {scene.ragAngle}
                  </span>
                </div>
                <h2 className="mt-2 font-serif text-2xl font-medium text-charcoal">{scene.name}</h2>
                <p className="mt-2 text-sm leading-relaxed text-stone">{scene.description}</p>
                
                {/* Visual RAG Badge */}
                <div className="mt-3 flex items-center gap-1.5 text-[10px] font-medium text-olive">
                  <span>⚡</span>
                  <span>{scene.ragBadge}</span>
                </div>
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
          All 6 cinematic scenes are selected by default. Deselect any you don't need.
        </p>
      </div>
    </section>
  )
}
