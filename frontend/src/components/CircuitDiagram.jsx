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

      <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--rule)]" style={{ background: 'var(--cream)' }}>
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
        className="svg-container flex justify-center items-center p-6 overflow-x-auto"
        style={{ background: 'var(--svg-bg)' }}
        dangerouslySetInnerHTML={{ __html: svg }}
      />

      <div className="px-5 py-4 border-t border-[var(--rule)]" style={{ background: 'var(--cream)' }}>
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