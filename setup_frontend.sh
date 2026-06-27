#!/usr/bin/env bash
# =============================================================================
# setup_frontend.sh — Generator Soal Rangkaian Listrik SMA
#
# Jalankan SEKALI dari root project (folder yang berisi backend/):
#   bash setup_frontend.sh
# =============================================================================
set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Setup Frontend — Generator Soal Rangkaian  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Scaffold ───────────────────────────────────────────────────────────────
echo "▸ [1/4] Scaffold React + Vite..."
#npm create vite@latest frontend -- --template react
cd frontend

# ── 2. Dependencies ───────────────────────────────────────────────────────────
echo "▸ [2/4] Install dependencies..."
#npm install
#npm install -D tailwindcss @tailwindcss/vite

# ── 3. Tulis semua file ───────────────────────────────────────────────────────
echo "▸ [3/4] Menulis file konfigurasi & source..."
mkdir -p src/api src/hooks src/components

# ── vite.config.js ────────────────────────────────────────────────────────────
cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
EOF

# ── index.html ────────────────────────────────────────────────────────────────
cat > index.html << 'EOF'
<!doctype html>
<html lang="id">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Generator Soal Rangkaian Listrik</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# ── src/index.css ─────────────────────────────────────────────────────────────
cat > src/index.css << 'EOF'
@import "tailwindcss";

:root {
  --ink:     #0f0e0c;
  --paper:   #f5f0e8;
  --cream:   #ede8dc;
  --accent:  #c8401a;
  --accent2: #2a6496;
  --muted:   #7a7468;
  --rule:    #d4cec4;
}

* { box-sizing: border-box; }

body {
  font-family: 'Syne', sans-serif;
  background-color: var(--paper);
  color: var(--ink);
  min-height: 100vh;
}

.mono { font-family: 'Space Mono', monospace; }

.rule {
  border: none;
  border-top: 2px solid var(--ink);
  margin: 0;
}
.rule-thin {
  border: none;
  border-top: 1px solid var(--rule);
}

.badge {
  display: inline-block;
  font-family: 'Space Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 8px;
  border: 1.5px solid currentColor;
}

.btn-primary {
  background: var(--ink);
  color: var(--paper);
  font-family: 'Space Mono', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 12px 28px;
  border: none;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}
.btn-primary:hover { background: #2a2820; }
.btn-primary:active { transform: translateY(1px); }
.btn-primary:disabled {
  background: var(--muted);
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: transparent;
  color: var(--ink);
  font-family: 'Space Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 10px 20px;
  border: 1.5px solid var(--ink);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-secondary:hover {
  background: var(--ink);
  color: var(--paper);
}

.answer-input {
  font-family: 'Space Mono', monospace;
  font-size: 1.1rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--ink);
  padding: 6px 2px;
  width: 120px;
  outline: none;
  color: var(--ink);
  text-align: right;
}
.answer-input:focus { border-bottom-color: var(--accent2); }
.answer-input::placeholder { color: var(--muted); }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.35s ease both; }

@keyframes spin {
  to { transform: rotate(360deg); }
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--rule);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

.correct { color: #1a7a3c; border-color: #1a7a3c !important; }
.wrong   { color: var(--accent); border-color: var(--accent) !important; }
EOF

# ── src/main.jsx ──────────────────────────────────────────────────────────────
cat > src/main.jsx << 'EOF'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
EOF

# ── src/api/questions.js ──────────────────────────────────────────────────────
cat > src/api/questions.js << 'EOF'
const BASE = '/api/questions'

export async function generateQuestion({ pattern, difficulty, seed } = {}) {
  const params = new URLSearchParams()
  if (pattern)      params.set('pattern', pattern)
  if (difficulty)   params.set('difficulty', difficulty)
  if (seed != null) params.set('seed', String(seed))

  const res = await fetch(`${BASE}/generate?${params}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function fetchPatterns() {
  const res = await fetch(`${BASE}/patterns`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
EOF

# ── src/hooks/useQuestion.js ──────────────────────────────────────────────────
cat > src/hooks/useQuestion.js << 'EOF'
import { useState, useCallback } from 'react'
import { generateQuestion } from '../api/questions.js'

export function useQuestion() {
  const [question, setQuestion] = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [answers,  setAnswers]  = useState({})
  const [checked,  setChecked]  = useState(false)

  const generate = useCallback(async (opts = {}) => {
    setLoading(true)
    setError(null)
    setAnswers({})
    setChecked(false)
    try {
      const data = await generateQuestion(opts)
      setQuestion(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const setAnswer = useCallback((key, value) => {
    setAnswers(prev => ({ ...prev, [key]: value }))
    setChecked(false)
  }, [])

  const check = useCallback(() => setChecked(true), [])

  return { question, loading, error, generate, answers, setAnswer, checked, check }
}
EOF

# ── src/components/Controls.jsx ───────────────────────────────────────────────
cat > src/components/Controls.jsx << 'EOF'
import { useState } from 'react'

const PATTERNS = [
  { value: '',                label: 'Acak' },
  { value: 'series_simple',   label: 'Seri' },
  { value: 'parallel_simple', label: 'Paralel' },
  { value: 'mixed_basic',     label: 'Campuran' },
]

const DIFFICULTIES = [
  { value: 'mudah',  label: 'Mudah' },
  { value: 'sedang', label: 'Sedang' },
  { value: 'sulit',  label: 'Sulit' },
]

export default function Controls({ onGenerate, loading }) {
  const [pattern,    setPattern]    = useState('')
  const [difficulty, setDifficulty] = useState('sedang')
  const [seedStr,    setSeedStr]    = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const seed = seedStr.trim() !== '' ? parseInt(seedStr, 10) : undefined
    onGenerate({ pattern: pattern || undefined, difficulty, seed })
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-0 border border-[var(--ink)]">

        <div className="bg-[var(--ink)] text-[var(--paper)] px-5 py-3">
          <span className="mono text-xs font-bold tracking-widest uppercase">
            Parameter Soal
          </span>
        </div>

        <div className="divide-y divide-[var(--rule)]">

          <div className="flex items-center px-5 py-4 gap-6">
            <label className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0">
              Pola
            </label>
            <div className="flex flex-wrap gap-2">
              {PATTERNS.map(p => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPattern(p.value)}
                  className={`badge cursor-pointer transition-colors ${
                    pattern === p.value
                      ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                      : 'text-[var(--muted)] hover:text-[var(--ink)]'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center px-5 py-4 gap-6">
            <label className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0">
              Kesulitan
            </label>
            <div className="flex gap-2">
              {DIFFICULTIES.map(d => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDifficulty(d.value)}
                  className={`badge cursor-pointer transition-colors ${
                    difficulty === d.value
                      ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                      : 'text-[var(--muted)] hover:text-[var(--ink)]'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center px-5 py-4 gap-6">
            <label
              htmlFor="seed"
              className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0"
            >
              Seed
            </label>
            <input
              id="seed"
              type="number"
              min="0"
              placeholder="acak"
              value={seedStr}
              onChange={e => setSeedStr(e.target.value)}
              className="answer-input w-28 text-left"
            />
            {seedStr && (
              <button
                type="button"
                onClick={() => setSeedStr('')}
                className="mono text-xs text-[var(--muted)] hover:text-[var(--accent)] underline"
              >
                reset
              </button>
            )}
          </div>

        </div>

        <div className="px-5 py-4 bg-[var(--cream)]">
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading
              ? <span className="flex items-center justify-center gap-3">
                  <span className="spinner" /> Membuat soal...
                </span>
              : '→ Generate Soal'}
          </button>
        </div>

      </div>
    </form>
  )
}
EOF

# ── src/components/CircuitDiagram.jsx ─────────────────────────────────────────
cat > src/components/CircuitDiagram.jsx << 'EOF'
const PATTERN_LABELS = {
  series_simple:   'Seri',
  parallel_simple: 'Paralel',
  mixed_basic:     'Campuran',
}

const DIFF_COLORS = {
  mudah:  '#1a7a3c',
  sedang: '#c8401a',
  sulit:  '#7a1ac8',
}

function collectComponents(node) {
  if (node.value !== undefined) return [node]
  return (node.elements ?? []).flatMap(collectComponents)
}

export default function CircuitDiagram({ spec, svg }) {
  const patternLabel = PATTERN_LABELS[spec.pattern] ?? spec.pattern
  const diffColor    = DIFF_COLORS[spec.difficulty] ?? 'var(--ink)'

  return (
    <div className="border border-[var(--ink)]">

      <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--rule)] bg-[var(--cream)]">
        <div className="flex items-center gap-3">
          <span className="badge" style={{ color: diffColor, borderColor: diffColor }}>
            {spec.difficulty}
          </span>
          <span className="badge text-[var(--muted)]">{patternLabel}</span>
        </div>
        <span className="mono text-xs text-[var(--muted)]">
          seed <span className="text-[var(--ink)] font-bold">{spec.seed}</span>
        </span>
      </div>

      <div
        className="flex justify-center items-center bg-white p-6 overflow-x-auto"
        dangerouslySetInnerHTML={{ __html: svg }}
      />

      <div className="px-5 py-4 border-t border-[var(--rule)] bg-[var(--cream)]">
        <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-3">
          Komponen
        </p>
        <div className="flex flex-wrap gap-x-6 gap-y-1">
          {collectComponents(spec.root).map(c => (
            <span key={c.id} className="mono text-sm">
              <span className="font-bold">{c.label}</span>
              <span className="text-[var(--muted)]"> = {c.value}{c.unit}</span>
            </span>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-[var(--rule)]">
          <span className="mono text-sm">
            <span className="text-[var(--muted)]">Sumber: </span>
            <span className="font-bold">{spec.source.label} = {spec.source.voltage} V</span>
          </span>
        </div>
      </div>

    </div>
  )
}
EOF

# ── src/components/AnswerForm.jsx ─────────────────────────────────────────────
cat > src/components/AnswerForm.jsx << 'EOF'
function evalAnswer(raw, correct) {
  if (raw === undefined || raw === '') return 'empty'
  const num = parseFloat(String(raw).replace(',', '.'))
  if (isNaN(num)) return 'wrong'
  return Math.abs(num - correct) / correct <= 0.02 ? 'correct' : 'wrong'
}

function roundN(n, dec = 4) {
  return parseFloat(n.toFixed(dec))
}

function Field({ label, unit, value, onChange, result, correctValue }) {
  const cls = result === 'correct' ? 'correct' : result === 'wrong' ? 'wrong' : ''
  return (
    <div className="flex items-center gap-4 py-4 border-b border-[var(--rule)] last:border-0">
      <span className="mono text-sm font-bold w-32 shrink-0">{label}</span>
      <div className="flex items-baseline gap-2">
        <input
          type="text"
          inputMode="decimal"
          placeholder="0"
          value={value}
          onChange={e => onChange(e.target.value)}
          className={`answer-input ${cls}`}
        />
        <span className="mono text-xs text-[var(--muted)]">{unit}</span>
      </div>
      {result === 'correct' && <span className="mono text-xs correct">✓ Benar</span>}
      {result === 'wrong'   && <span className="mono text-xs wrong">✗ Jwb: {roundN(correctValue)}</span>}
      {result === 'empty'   && <span className="mono text-xs text-[var(--muted)]">Jwb: {roundN(correctValue)}</span>}
    </div>
  )
}

function ScoreBadge({ answers, solution }) {
  const pairs = [
    ['r_total', solution.total_resistance],
    ['i_total', solution.total_current],
    ...solution.component_results.flatMap(c => [
      [`v_${c.label}`, c.voltage_drop],
      [`i_${c.label}`, c.current],
    ]),
  ]
  const correct = pairs.filter(([k, v]) => evalAnswer(answers[k], v) === 'correct').length
  return (
    <div className="flex items-center gap-2">
      <span className="mono text-sm font-bold">{correct}/{pairs.length}</span>
      <span className="mono text-xs text-[var(--muted)]">benar</span>
    </div>
  )
}

export default function AnswerForm({ solution, answers, setAnswer, checked, onCheck, onNext }) {
  const { total_resistance, total_current, component_results } = solution
  const res = (key, val) => checked ? evalAnswer(answers[key], val) : null

  return (
    <div className="border border-[var(--ink)]">

      <div className="bg-[var(--ink)] text-[var(--paper)] px-5 py-3">
        <span className="mono text-xs font-bold tracking-widest uppercase">Jawab Pertanyaan</span>
      </div>

      <div className="px-5">
        <div className="pt-4 pb-2">
          <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-2">
            Rangkaian Keseluruhan
          </p>
          <Field label="R total" unit="Ω"
            value={answers['r_total'] ?? ''} onChange={v => setAnswer('r_total', v)}
            result={res('r_total', total_resistance)} correctValue={total_resistance} />
          <Field label="I total" unit="A"
            value={answers['i_total'] ?? ''} onChange={v => setAnswer('i_total', v)}
            result={res('i_total', total_current)} correctValue={total_current} />
        </div>

        <hr className="rule-thin my-2" />

        <div className="pt-2 pb-4">
          <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-2">
            Per Komponen
          </p>
          {component_results.map(c => (
            <div key={c.component_id}>
              <Field label={`V ${c.label}`} unit="V"
                value={answers[`v_${c.label}`] ?? ''} onChange={v => setAnswer(`v_${c.label}`, v)}
                result={res(`v_${c.label}`, c.voltage_drop)} correctValue={c.voltage_drop} />
              <Field label={`I ${c.label}`} unit="A"
                value={answers[`i_${c.label}`] ?? ''} onChange={v => setAnswer(`i_${c.label}`, v)}
                result={res(`i_${c.label}`, c.current)} correctValue={c.current} />
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-[var(--ink)] bg-[var(--cream)] px-5 py-4 flex items-center gap-3">
        {!checked
          ? <button className="btn-primary flex-1" onClick={onCheck}>→ Periksa Jawaban</button>
          : <>
              <ScoreBadge answers={answers} solution={solution} />
              <button className="btn-secondary flex-1" onClick={onNext}>Soal Baru →</button>
            </>
        }
      </div>

    </div>
  )
}
EOF

# ── src/components/ErrorBanner.jsx ────────────────────────────────────────────
cat > src/components/ErrorBanner.jsx << 'EOF'
export default function ErrorBanner({ message, onDismiss }) {
  return (
    <div className="border border-[var(--accent)] bg-[#fff5f3] px-5 py-4 flex items-start justify-between gap-4">
      <div>
        <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--accent)] mb-1">Error</p>
        <p className="text-sm">{message}</p>
        <p className="mono text-xs text-[var(--muted)] mt-1">Pastikan backend berjalan di port 8000.</p>
      </div>
      <button onClick={onDismiss} className="mono text-xs text-[var(--muted)] hover:text-[var(--ink)] shrink-0 mt-1">
        ✕ tutup
      </button>
    </div>
  )
}
EOF

# ── src/App.jsx ───────────────────────────────────────────────────────────────
cat > src/App.jsx << 'EOF'
import { useQuestion } from './hooks/useQuestion.js'
import Controls        from './components/Controls.jsx'
import CircuitDiagram  from './components/CircuitDiagram.jsx'
import AnswerForm      from './components/AnswerForm.jsx'
import ErrorBanner     from './components/ErrorBanner.jsx'

export default function App() {
  const { question, loading, error, generate, answers, setAnswer, checked, check } = useQuestion()

  function handleNext() {
    generate({ difficulty: question?.spec?.difficulty })
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--paper)' }}>

      <header className="border-b-2 border-[var(--ink)] px-6 py-5 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight leading-none">Generator Soal</h1>
          <p className="mono text-xs text-[var(--muted)] mt-1 tracking-widest uppercase">
            Rangkaian Listrik · SMA
          </p>
        </div>
        <span className="mono text-xs text-[var(--muted)] hidden sm:block">R · I · V</span>
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

            <details className="border border-[var(--rule)]">
              <summary className="px-5 py-3 mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] cursor-pointer hover:text-[var(--ink)] select-none">
                ▸ Struktur Topologi (petunjuk / konteks LLM)
              </summary>
              <pre className="px-5 py-4 text-xs mono text-[var(--ink)] whitespace-pre-wrap border-t border-[var(--rule)] bg-white overflow-x-auto">
                {question.llm_description}
              </pre>
            </details>
          </div>
        )}

        {!question && !loading && !error && (
          <div className="border border-dashed border-[var(--rule)] flex flex-col items-center justify-center py-20 gap-3 text-center">
            <span className="text-4xl select-none">⚡</span>
            <p className="font-semibold text-lg">Belum ada soal</p>
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
EOF

# Hapus file bawaan Vite yang tidak dipakai
rm -f src/App.css public/vite.svg src/assets/react.svg 2>/dev/null || true

# ── 4. Selesai ────────────────────────────────────────────────────────────────
echo ""
echo "▸ [4/4] Selesai!"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Cara menjalankan:                                  ║"
echo "║                                                      ║"
echo "║  Terminal 1 (backend):                              ║"
echo "║    cd backend                                        ║"
echo "║    uv run uvicorn app.main:app --reload --port 8000 ║"
echo "║                                                      ║"
echo "║  Terminal 2 (frontend):                             ║"
echo "║    cd frontend                                       ║"
echo "║    npm run dev                                       ║"
echo "║                                                      ║"
echo "║  Buka → http://localhost:5173                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""