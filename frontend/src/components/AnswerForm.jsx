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
    <div className="flex items-center gap-4 py-3 border-b border-[var(--rule)] last:border-0">
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
      {result === 'wrong'   && <span className="mono text-xs wrong">✗ {roundN(correctValue)}</span>}
      {result === 'empty'   && <span className="mono text-xs text-[var(--muted)]">{roundN(correctValue)}</span>}
    </div>
  )
}

// Baris read-only untuk nilai yang tidak diisi user (daya, hambatan dalam)
function InfoRow({ label, value, unit }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-[var(--rule)] last:border-0">
      <span className="mono text-sm font-bold w-32 shrink-0" style={{ color: 'var(--muted)' }}>{label}</span>
      <span className="mono text-sm" style={{ color: 'var(--ink)' }}>
        {roundN(value)} <span className="text-xs" style={{ color: 'var(--muted)' }}>{unit}</span>
      </span>
    </div>
  )
}

function ScoreBadge({ answers, solution, isMultiEmf }) {
  const pairs = [
    ['r_total', solution.total_resistance],
    ['i_total', solution.total_current],
    ...(isMultiEmf ? [['v_eff', solution.source_voltage]] : []),
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

const POLARITY_LABELS = {
  aiding:   'searah (aiding)',
  opposing: 'berlawanan (opposing)',
}

export default function AnswerForm({ spec, solution, answers, setAnswer, checked, onCheck, onNext, showPower }) {
  const { total_resistance, total_current, source_voltage, component_results } = solution
  const hasInternalR = solution.internal_resistance > 0
  const res = (key, val) => checked ? evalAnswer(answers[key], val) : null

  const extraSources = spec?.extra_sources ?? []
  const isMultiEmf = extraSources.length > 0

  return (
    <div className="border border-[var(--ink)]">

      <div className="px-5 py-3" style={{ background: 'var(--ink)' }}>
        <span className="mono text-xs font-bold tracking-widest uppercase" style={{ color: 'var(--paper)' }}>
          Jawab Pertanyaan
        </span>
      </div>

      <div className="px-5">

        {isMultiEmf && (
          <div className="pt-4 pb-2">
            <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-2">
              Sumber Tegangan
            </p>
            <InfoRow label={spec.source.label} value={spec.source.voltage} unit="V" />
            {extraSources.map((s, i) => (
              <InfoRow
                key={i}
                label={`${s.label}${s.polarity ? ` (${POLARITY_LABELS[s.polarity] ?? s.polarity})` : ''}`}
                value={s.voltage}
                unit="V"
              />
            ))}
            <Field label="V efektif" unit="V"
              value={answers['v_eff'] ?? ''} onChange={v => setAnswer('v_eff', v)}
              result={res('v_eff', source_voltage)} correctValue={source_voltage} />
          </div>
        )}

        {isMultiEmf && <hr className="rule-thin my-2" />}

        {/* Rangkaian keseluruhan */}
        <div className="pt-4 pb-2">
          <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-2">
            Rangkaian Keseluruhan
          </p>

          {hasInternalR && (
            <InfoRow
              label="r dalam"
              value={solution.internal_resistance ?? 0}
              unit="Ω"
            />
          )}

          <Field label="R total" unit="Ω"
            value={answers['r_total'] ?? ''} onChange={v => setAnswer('r_total', v)}
            result={res('r_total', total_resistance)} correctValue={total_resistance} />
          <Field label="I total" unit="A"
            value={answers['i_total'] ?? ''} onChange={v => setAnswer('i_total', v)}
            result={res('i_total', total_current)} correctValue={total_current} />

          {showPower && (
            <InfoRow label="P total" value={source_voltage * total_current} unit="W" />
          )}
        </div>

        <hr className="rule-thin my-2" />

        {/* Per komponen */}
        <div className="pt-2 pb-4">
          <p className="mono text-xs font-bold tracking-widest uppercase text-[var(--muted)] mb-2">
            Per Komponen
          </p>
          {component_results.map(c => (
            <div key={c.component_id} className="mb-1">
              <Field label={`V ${c.label}`} unit="V"
                value={answers[`v_${c.label}`] ?? ''} onChange={v => setAnswer(`v_${c.label}`, v)}
                result={res(`v_${c.label}`, c.voltage_drop)} correctValue={c.voltage_drop} />
              <Field label={`I ${c.label}`} unit="A"
                value={answers[`i_${c.label}`] ?? ''} onChange={v => setAnswer(`i_${c.label}`, v)}
                result={res(`i_${c.label}`, c.current)} correctValue={c.current} />
              {showPower && (
                <InfoRow label={`P ${c.label}`} value={c.power} unit="W" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-[var(--ink)] px-5 py-4 flex items-center gap-3" style={{ background: 'var(--cream)' }}>
        {!checked
          ? <button className="btn-primary flex-1" onClick={onCheck}>→ Periksa Jawaban</button>
          : <>
              <ScoreBadge answers={answers} solution={solution} isMultiEmf={isMultiEmf} />
              <button className="btn-secondary flex-1" onClick={onNext}>Soal Baru →</button>
            </>
        }
      </div>

    </div>
  )
}