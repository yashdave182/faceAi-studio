import { useEffect, useMemo, useRef, useState } from 'react'
import { GenerationScreen } from './components/GenerationScreen'
import { Header } from './components/Header'
import { ResultsScreen } from './components/ResultsScreen'
import { SceneSelectScreen } from './components/SceneSelectScreen'
import { UploadScreen } from './components/UploadScreen'
import { getConfig, getStatus, resetSession, startGeneration } from './lib/api'
import { SCENES, type AttireStyle, type SceneKey, type SceneState } from './types'

type Step = 'upload' | 'scenes' | 'generation' | 'results'

const ALL_SCENES: SceneKey[] = SCENES.map((scene) => scene.key)

export function App() {
  const [step, setStep] = useState<Step>('upload')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [attire, setAttire] = useState<AttireStyle>('groom')
  const [selected, setSelected] = useState<SceneKey[]>([...ALL_SCENES])
  const [sceneStates, setSceneStates] = useState<Record<string, SceneState>>({})
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const previewUrlRef = useRef<string | null>(null)

  useEffect(() => {
    previewUrlRef.current = previewUrl
  }, [previewUrl])

  useEffect(() => {
    getConfig()
      .then((config) => {
        if (!config.api_key_configured) {
          setNotice(
            'Heads up: the studio service has no image provider key configured yet, so generation cannot start. Add FAL_KEY (recommended) or GEMINI_API_KEY to the backend environment.',
          )
        }
      })
      .catch(() => {
        /* config check is best-effort */
      })
  }, [])

  const anyInProgress = useMemo(
    () =>
      Object.values(sceneStates).some(
        (scene) => scene.status === 'pending' || scene.status === 'generating',
      ),
    [sceneStates],
  )

  useEffect(() => {
    if (!sessionId || !anyInProgress) return
    let cancelled = false

    async function poll() {
      try {
        const status = await getStatus(sessionId!)
        if (cancelled) return
        setSceneStates((previous) => ({ ...previous, ...status.scenes }))
      } catch {
        /* transient polling errors are ignored */
      }
    }

    void poll()
    const timer = window.setInterval(poll, 2500)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [sessionId, anyInProgress])

  useEffect(() => {
    if (step !== 'generation' || selected.length === 0) return
    const settled = selected.every((key) => {
      const status = sceneStates[key]?.status
      return status === 'completed' || status === 'failed'
    })
    const started = selected.some((key) => {
      const status = sceneStates[key]?.status
      return status && status !== 'idle'
    })
    if (settled && started) setStep('results')
  }, [step, selected, sceneStates])

  function handleUploaded(newSessionId: string, newPreviewUrl: string, newAttire: AttireStyle) {
    setSessionId(newSessionId)
    setPreviewUrl(newPreviewUrl)
    setAttire(newAttire)
    setNotice(null)
    setStep('scenes')
  }

  function handleToggleScene(key: SceneKey) {
    setSelected((previous) =>
      previous.includes(key) ? previous.filter((item) => item !== key) : [...previous, key],
    )
  }

  async function runGeneration(
    scenes: SceneKey[],
    nextStep: Step,
    overrideAttire?: AttireStyle,
  ) {
    if (!sessionId) return
    const activeAttire = overrideAttire ?? attire
    if (overrideAttire && overrideAttire !== attire) {
      setAttire(overrideAttire)
    }
    setBusy(true)
    setNotice(null)
    try {
      await startGeneration(sessionId, scenes, activeAttire)
      setSceneStates((previous) => {
        const updated = { ...previous }
        for (const key of scenes) {
          const existing = previous[key]
          updated[key] = {
            status: 'pending',
            error: null,
            version: existing?.version ?? 0,
          }
        }
        return updated
      })
      setStep(nextStep)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Generation could not be started.')
    } finally {
      setBusy(false)
    }
  }

  async function handleGenerate() {
    await runGeneration(selected, 'generation')
  }

  async function handleRegenerate(keys: SceneKey[], overrideAttire?: AttireStyle) {
    await runGeneration(keys, step === 'results' ? 'results' : 'generation', overrideAttire)
  }

  async function handleRegenerateAll(overrideAttire?: AttireStyle) {
    await runGeneration(selected, 'generation', overrideAttire)
  }

  async function handleStartOver() {
    if (sessionId) {
      void resetSession(sessionId).catch(() => undefined)
    }
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current)
    setSessionId(null)
    setPreviewUrl(null)
    setAttire('groom')
    setSelected([...ALL_SCENES])
    setSceneStates({})
    setNotice(null)
    setBusy(false)
    setStep('upload')
  }

  return (
    <div className="flex min-h-svh flex-col">
      <Header />

      {notice && (
        <div className="border-b border-beige bg-white/60">
          <p className="mx-auto max-w-5xl px-6 py-3 text-xs leading-relaxed text-stone sm:px-10">
            {notice}
          </p>
        </div>
      )}

      <main className="flex-1">
        {step === 'upload' && (
          <UploadScreen initialAttire={attire} onUploaded={handleUploaded} />
        )}

        {step === 'scenes' && (
          <SceneSelectScreen
            selected={selected}
            attire={attire}
            onSelectAttire={setAttire}
            onToggle={handleToggleScene}
            onGenerate={handleGenerate}
            busy={busy}
            error={notice}
          />
        )}

        {step === 'generation' && (
          <GenerationScreen
            selected={selected}
            scenes={sceneStates}
            onRetry={(key) => void handleRegenerate([key])}
            onViewResults={() => setStep('results')}
          />
        )}

        {step === 'results' && sessionId && (
          <ResultsScreen
            sessionId={sessionId}
            selected={selected}
            scenes={sceneStates}
            attire={attire}
            onRegenerate={(key, newAttire) => void handleRegenerate([key], newAttire)}
            onRegenerateAll={(newAttire) => void handleRegenerateAll(newAttire)}
            onStartOver={() => void handleStartOver()}
          />
        )}
      </main>

      <footer className="border-t border-beige">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-6 sm:px-10">
          <p className="text-[11px] leading-relaxed text-stone">
            Portraits are AI-generated and likeness may vary. Images exist only for this session and
            are deleted when you start over.
          </p>
          <p className="text-[11px] tracking-[0.18em] text-stone uppercase">
            Lovers AI · Face Consistency Demo
          </p>
        </div>
      </footer>
    </div>
  )
}
