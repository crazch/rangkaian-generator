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

function Row({ label, hint, children }) {
  return (
    <div className="flex items-start px-5 py-4 gap-6 border-b border-[var(--rule)] last:border-0">
      <div className="w-36 shrink-0 pt-0.5">
        <p className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)]">{label}</p>
        {hint && <p className="mono text-[10px] text-[var(--muted)] mt-0.5 leading-tight">{hint}</p>}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  )
}

function NumberInput({ value, onChange, placeholder, min, max, step = 1 }) {
  return (
    <input
      type="number"
      min={min}
      max={max}
      step={step}
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value === '' ? '' : e.target.value)}
      className="answer-input w-24 text-left"
      style={{ fontSize: '0.85rem' }}
    />
  )
}

function Toggle({ value, onChange, labelOn = 'Ya', labelOff = 'Tidak', labelNull = 'Acak' }) {
  const options = [
    { v: null,  label: labelNull },
    { v: true,  label: labelOn },
    { v: false, label: labelOff },
  ]
  return (
    <div className="flex gap-2">
      {options.map(o => (
        <button
          key={String(o.v)}
          type="button"
          onClick={() => onChange(o.v)}
          className={`badge cursor-pointer transition-colors ${
            value === o.v
              ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
              : 'text-[var(--muted)] hover:text-[var(--ink)]'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

const UNIT_OPTIONS = [
  { value: 'base', label: 'Ω / A / V' },
  { value: 'kilo', label: 'kΩ / mA / V' },
  { value: 'auto', label: 'Auto' },
]

export default function Controls({ onGenerate, loading }) {
  const [pattern,    setPattern]    = useState('')
  const [difficulty, setDifficulty] = useState('sedang')
  const [seedStr,    setSeedStr]    = useState('')
  const [showAdv,    setShowAdv]    = useState(false)

  // Advanced Layer 1
  const [nComponents,    setNComponents]    = useState('')
  const [rMin,           setRMin]           = useState('')
  const [rMax,           setRMax]           = useState('')
  const [forceIdentical, setForceIdentical] = useState(null)   // null | true | false

  // Advanced Layer 2
  const [internalR,  setInternalR]  = useState('')
  const [showPower,  setShowPower]  = useState(false)
  const [unitPrefix, setUnitPrefix] = useState('base')

  function resetAdvanced() {
    setNComponents(''); setRMin(''); setRMax('')
    setForceIdentical(null); setInternalR('')
    setShowPower(false); setUnitPrefix('base')
  }

  function hasAdvanced() {
    return nComponents !== '' || rMin !== '' || rMax !== '' ||
      forceIdentical !== null || internalR !== '' ||
      showPower || unitPrefix !== 'base'
  }

  function handleSubmit(e) {
    e.preventDefault()
    const seed = seedStr.trim() !== '' ? parseInt(seedStr, 10) : undefined

    const opts = {
      pattern: pattern || undefined,
      difficulty,
      seed,
    }

    if (hasAdvanced()) {
      if (nComponents !== '')   opts.n_components = parseInt(nComponents, 10)
      if (rMin !== '')          opts.r_min = parseFloat(rMin)
      if (rMax !== '')          opts.r_max = parseFloat(rMax)
      if (forceIdentical !== null) opts.force_identical = forceIdentical
      if (internalR !== '')     opts.internal_resistance = parseFloat(internalR)
      if (showPower)            opts.show_power = true
      if (unitPrefix !== 'base') opts.unit_prefix = unitPrefix
    }

    onGenerate(opts)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-0 border border-[var(--ink)]">

        {/* Header */}
        <div className="px-5 py-3" style={{ background: 'var(--ink)' }}>
          <span className="mono text-xs font-bold tracking-widest uppercase" style={{ color: 'var(--paper)' }}>
            Parameter Soal
          </span>
        </div>

        {/* Basic params */}
        <div className="divide-y divide-[var(--rule)]">

          <div className="flex items-center px-5 py-4 gap-6">
            <label className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0">Pola</label>
            <div className="flex flex-wrap gap-2">
              {PATTERNS.map(p => (
                <button key={p.value} type="button" onClick={() => setPattern(p.value)}
                  className={`badge cursor-pointer transition-colors ${
                    pattern === p.value
                      ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                      : 'text-[var(--muted)] hover:text-[var(--ink)]'
                  }`}>{p.label}</button>
              ))}
            </div>
          </div>

          <div className="flex items-center px-5 py-4 gap-6">
            <label className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0">Kesulitan</label>
            <div className="flex gap-2">
              {DIFFICULTIES.map(d => (
                <button key={d.value} type="button" onClick={() => setDifficulty(d.value)}
                  className={`badge cursor-pointer transition-colors ${
                    difficulty === d.value
                      ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                      : 'text-[var(--muted)] hover:text-[var(--ink)]'
                  }`}>{d.label}</button>
              ))}
            </div>
          </div>

          <div className="flex items-center px-5 py-4 gap-6">
            <label htmlFor="seed" className="mono text-xs font-bold tracking-wide uppercase text-[var(--muted)] w-24 shrink-0">Seed</label>
            <input id="seed" type="number" min="0" placeholder="acak" value={seedStr}
              onChange={e => setSeedStr(e.target.value)} className="answer-input w-28 text-left" />
            {seedStr && (
              <button type="button" onClick={() => setSeedStr('')}
                className="mono text-xs text-[var(--muted)] hover:text-[var(--accent)] underline">reset</button>
            )}
          </div>

        </div>

        {/* Advanced toggle */}
        <button
          type="button"
          onClick={() => setShowAdv(v => !v)}
          className="flex items-center justify-between px-5 py-3 border-t border-[var(--rule)] hover:text-[var(--ink)] transition-colors"
          style={{ background: 'var(--cream)', color: 'var(--muted)' }}
        >
          <span className="mono text-xs font-bold tracking-widest uppercase flex items-center gap-2">
            <span>{showAdv ? '▾' : '▸'}</span>
            Advanced
            {hasAdvanced() && (
              <span className="badge" style={{ color: 'var(--accent)', borderColor: 'var(--accent)', fontSize: '0.6rem' }}>
                aktif
              </span>
            )}
          </span>
          {showAdv && hasAdvanced() && (
            <span
              onClick={e => { e.stopPropagation(); resetAdvanced() }}
              className="mono text-[10px] underline hover:text-[var(--accent)] cursor-pointer"
            >
              reset semua
            </span>
          )}
        </button>

        {showAdv && (
          <div className="border-t border-[var(--rule)] divide-y divide-[var(--rule)]" style={{ background: 'var(--paper)' }}>

            {/* Separator label Layer 1 */}
            <div className="px-5 py-2">
              <span className="mono text-[10px] font-bold tracking-widest uppercase text-[var(--muted)]">
                ── Struktur Komponen
              </span>
            </div>

            <Row label="Jml. Komponen" hint="Override range otomatis">
              <div className="flex items-center gap-3">
                <NumberInput value={nComponents} onChange={setNComponents} placeholder="auto" min={2} max={8} />
                {nComponents !== '' && (
                  <button type="button" onClick={() => setNComponents('')}
                    className="mono text-xs text-[var(--muted)] hover:text-[var(--accent)] underline">reset</button>
                )}
              </div>
            </Row>

            <Row label="Range R" hint="Filter pool nilai (Ω)">
              <div className="flex items-center gap-2">
                <NumberInput value={rMin} onChange={setRMin} placeholder="min" min={1} step={1} />
                <span className="mono text-xs text-[var(--muted)]">–</span>
                <NumberInput value={rMax} onChange={setRMax} placeholder="max" min={1} step={1} />
                <span className="mono text-xs text-[var(--muted)]">Ω</span>
                {(rMin !== '' || rMax !== '') && (
                  <button type="button" onClick={() => { setRMin(''); setRMax('') }}
                    className="mono text-xs text-[var(--muted)] hover:text-[var(--accent)] underline ml-1">reset</button>
                )}
              </div>
            </Row>

            <Row label="Identik" hint="Paksa/larang dua R bernilai sama">
              <Toggle value={forceIdentical} onChange={setForceIdentical}
                labelOn="Paksa" labelOff="Larang" labelNull="Acak" />
            </Row>

            {/* Separator label Layer 2 */}
            <div className="px-5 py-2">
              <span className="mono text-[10px] font-bold tracking-widest uppercase text-[var(--muted)]">
                ── Sumber & Output
              </span>
            </div>

            <Row label="R dalam" hint="Hambatan dalam sumber (Ω)">
              <div className="flex items-center gap-3">
                <NumberInput value={internalR} onChange={setInternalR} placeholder="0 (ideal)" min={0} step={0.1} />
                <span className="mono text-xs text-[var(--muted)]">Ω</span>
                {internalR !== '' && (
                  <button type="button" onClick={() => setInternalR('')}
                    className="mono text-xs text-[var(--muted)] hover:text-[var(--accent)] underline">reset</button>
                )}
              </div>
            </Row>

            <Row label="Tampil Daya" hint="Tampilkan P = V·I per komponen">
              <button
                type="button"
                onClick={() => setShowPower(v => !v)}
                className={`badge cursor-pointer transition-colors ${
                  showPower
                    ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                    : 'text-[var(--muted)] hover:text-[var(--ink)]'
                }`}
              >
                {showPower ? 'Aktif' : 'Nonaktif'}
              </button>
            </Row>

            <Row label="Satuan" hint="Prefix output nilai">
              <div className="flex gap-2">
                {UNIT_OPTIONS.map(u => (
                  <button key={u.value} type="button" onClick={() => setUnitPrefix(u.value)}
                    className={`badge cursor-pointer transition-colors ${
                      unitPrefix === u.value
                        ? 'bg-[var(--ink)] text-[var(--paper)] border-[var(--ink)]'
                        : 'text-[var(--muted)] hover:text-[var(--ink)]'
                    }`}>{u.label}</button>
                ))}
              </div>
            </Row>

          </div>
        )}

        {/* Submit */}
        <div className="px-5 py-4 border-t border-[var(--rule)]" style={{ background: 'var(--cream)' }}>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading
              ? <span className="flex items-center justify-center gap-3"><span className="spinner" /> Membuat soal...</span>
              : '→ Generate Soal'}
          </button>
        </div>

      </div>
    </form>
  )
}