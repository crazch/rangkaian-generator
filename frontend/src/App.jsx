import { useState, useEffect, useCallback } from 'react'
import { useQuestion } from './hooks/useQuestion.js'
import Controls        from './components/Controls.jsx'
import CircuitDiagram  from './components/CircuitDiagram.jsx'
import AnswerForm      from './components/AnswerForm.jsx'
import ErrorBanner     from './components/ErrorBanner.jsx'

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('dark-mode')
    if (saved !== null) return saved === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('dark-mode', dark)
  }, [dark])

  return [dark, () => setDark(d => !d)]
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback for older browsers
      const el = document.createElement('textarea')
      el.value = text
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`btn-copy ${copied ? 'copied' : ''}`}
    >
      {copied ? '✓ Tersalin' : '⎘ Salin'}
    </button>
  )
}

export default function App() {
  const { question, loading, error, generate, answers, setAnswer, checked, check } = useQuestion()
  const [dark, toggleDark] = useDarkMode()

  function handleNext() {
    generate({ difficulty: question?.spec?.difficulty })
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--paper)', color: 'var(--ink)', transition: 'background 0.2s, color 0.2s' }}>

      <header className="border-b-2 border-[var(--ink)] px-6 py-5 flex items-center justify-between">
        <div>
          <h1 
            className="text-2xl font-black uppercase tracking-wider text-center" 
            style={{ color: 'var(--ink)' }}
          >
            Generator Soal
          </h1>
          <p className="mono text-xs text-[var(--muted)] mt-1 tracking-widest uppercase">
            Rangkaian Listrik
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="mono text-xs text-[var(--muted)] hidden sm:block">V · I · R</span>
          <button
            type="button"
            onClick={toggleDark}
            className="btn-icon"
            title={dark ? 'Mode Terang' : 'Mode Gelap'}
            aria-label={dark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'}
          >
            {dark ? '☀' : '☾'}
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">

        {error && <ErrorBanner message={error} onDismiss={() => generate({})} />}

        <Controls onGenerate={generate} loading={loading} />

        {question && !loading && (
          <div className="fade-in space-y-6">
            <div className="flex items-center gap-4">
              <hr className="flex-1 rule" />
              <span className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)]">Soal</span>
              <hr className="flex-1 rule" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              <CircuitDiagram spec={question.spec} svg={question.svg} />
              <AnswerForm
                solution={question.solution}
                answers={answers}
                setAnswer={setAnswer}
                checked={checked}
                onCheck={check}
                onNext={handleNext}
              />
            </div>

            <details className="border border-[var(--rule)]" style={{ background: 'var(--cream)' }}>
              <summary className="px-5 py-3 mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] cursor-pointer hover:text-[var(--ink)] select-none list-none flex items-center justify-between">
                <span>▸ Struktur Topologi (petunjuk / konteks LLM)</span>
              </summary>
              <div className="border-t border-[var(--rule)]">
                <div className="flex items-center justify-end px-4 py-2 border-b border-[var(--rule)]" style={{ background: 'var(--paper)' }}>
                  <CopyButton text={question.llm_description} />
                </div>
                <pre className="px-5 py-4 text-xs mono whitespace-pre-wrap overflow-x-auto" style={{ color: 'var(--ink)', background: 'var(--paper)' }}>
                  {question.llm_description}
                </pre>
              </div>
            </details>
          </div>
        )}

        {!question && !loading && !error && (
          <div className="border border-dashed border-[var(--rule)] flex flex-col items-center justify-center py-20 gap-3 text-center">
            <span className="text-4xl select-none">⚡</span>
            <p className="font-semibold text-lg" style={{ color: 'var(--ink)' }}>Belum ada soal</p>
            <p className="mono text-xs text-[var(--muted)]">Pilih parameter di atas lalu klik Generate</p>
          </div>
        )}

      </main>

      <footer className="border-t border-[var(--rule)] px-6 py-4 mt-12">
        <p className="mono text-xs text-[var(--muted)] text-center">
          Backend · FastAPI + schemdraw &nbsp;|&nbsp; Frontend · React + Vite + Tailwind
        </p>
      </footer>

    </div>
  )
}