import { SCENES, type SceneKey, type SceneState } from '../types'

interface Props {
  selected: SceneKey[]
  scenes: Record<string, SceneState>
  onRetry: (key: SceneKey) => void
  onViewResults: () => void
}

const STATUS_LABEL: Record<string, string> = {
  idle: 'Queued',
  pending: 'Queued',
  generating: 'Generating portrait…',
  completed: 'Completed',
  failed: 'Failed',
}

export function GenerationScreen({ selected, scenes, onRetry, onViewResults }: Props) {
  const activeScenes = SCENES.filter((scene) => selected.includes(scene.key))
  const settled = activeScenes.filter((scene) => {
    const status = scenes[scene.key]?.status ?? 'idle'
    return status === 'completed' || status === 'failed'
  }).length

  return (
    <section className="fade-up mx-auto max-w-3xl px-6 pt-16 pb-24 sm:px-10">
      <p className="text-[11px] tracking-[0.28em] text-stone uppercase">Step three · Generation</p>
      <h1 className="mt-4 font-serif text-4xl font-medium text-charcoal sm:text-5xl">
        Composing your portraits.
      </h1>
      <p className="mt-4 max-w-lg text-sm leading-relaxed text-stone">
        Each scene is generated separately from the same reference photograph. This can take up to
        a minute or two per portrait — you can leave this page open.
      </p>

      <div className="mt-10 flex max-w-xs gap-1.5" aria-hidden="true">
        {activeScenes.map((scene) => {
          const status = scenes[scene.key]?.status ?? 'idle'
          const done = status === 'completed'
          const failed = status === 'failed'
          return (
            <span
              key={scene.key}
              className={`h-px flex-1 transition-colors duration-500 ${
                failed ? 'bg-charcoal/30' : done ? 'bg-olive' : 'bg-beige slow-pulse'
              }`}
            />
          )
        })}
      </div>
      <p className="mt-3 text-xs text-stone">
        {settled} of {activeScenes.length} scenes finished
      </p>

      <ul className="mt-12 divide-y divide-beige border-y border-beige">
        {activeScenes.map((scene) => {
          const sceneState = scenes[scene.key]
          const status = sceneState?.status ?? 'idle'
          return (
            <li key={scene.key} className="flex flex-wrap items-center justify-between gap-4 py-5">
              <div>
                <p className="font-serif text-xl text-charcoal">{scene.name}</p>
                {status === 'failed' && sceneState?.error && (
                  <p className="mt-1 max-w-md text-xs leading-relaxed text-stone">{sceneState.error}</p>
                )}
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`text-xs tracking-[0.14em] uppercase ${
                    status === 'completed'
                      ? 'text-olive'
                      : status === 'failed'
                        ? 'text-charcoal'
                        : 'text-stone'
                  }`}
                >
                  {STATUS_LABEL[status] ?? status}
                </span>
                {(status === 'pending' || status === 'generating') && (
                  <span className="slow-pulse inline-block h-1.5 w-1.5 rounded-full bg-olive" />
                )}
                {status === 'failed' && (
                  <button
                    type="button"
                    onClick={() => onRetry(scene.key)}
                    className="border border-beige px-4 py-1.5 text-xs tracking-[0.14em] text-charcoal uppercase transition-colors hover:border-olive hover:text-olive"
                  >
                    Retry
                  </button>
                )}
              </div>
            </li>
          )
        })}
      </ul>

      <div className="mt-10">
        <button
          type="button"
          onClick={onViewResults}
          disabled={settled === 0}
          className="text-sm text-stone underline underline-offset-4 transition-colors hover:text-charcoal disabled:opacity-50"
        >
          {settled === activeScenes.length
            ? 'View results'
            : `View available results (${settled})`}
        </button>
      </div>
    </section>
  )
}
