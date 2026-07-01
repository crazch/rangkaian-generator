const PATTERN_LABELS = {
  series_simple:      'Seri',
  parallel_simple:    'Paralel',
  mixed_basic:        'Campuran',
  wheatstone_bridge:  'Jembatan Wheatstone',
  multi_level:        'Bertingkat',
  multi_emf:          'Multi-Sumber',
}

const DIFF_COLORS = {
  mudah:  '#1a7a3c',
  sedang: '#c8401a',
  sulit:  '#7a1ac8',
}

const POLARITY_LABELS = {
  aiding:   'searah',
  opposing: 'berlawanan',
}

function collectComponents(node) {
  if (node.value !== undefined) return [node]
  return (node.elements ?? []).flatMap(collectComponents)
}

function SourceRow({ label, value }) {
  return (
    <span className="mono text-sm">
      <span className="text-[var(--muted)]">{label}: </span>
      <span className="font-bold">{value}</span>
    </span>
  )
}

export default function CircuitDiagram({ spec, svg }) {
  const patternLabel = PATTERN_LABELS[spec.pattern] ?? spec.pattern
  const diffColor    = DIFF_COLORS[spec.difficulty] ?? 'var(--ink)'
  const galvanometer = spec.topology_meta?.galvanometer
  const hasExtraSources = spec.extra_sources && spec.extra_sources.length > 0

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
          {galvanometer && (
            <span className="mono text-sm">
              <span className="font-bold">{galvanometer.label}</span>
              <span className="text-[var(--muted)]"> = {galvanometer.value}{galvanometer.unit ?? 'Ω'}</span>
              <span className="badge ml-1" style={{ fontSize: '0.6rem' }}>galvanometer</span>
            </span>
          )}
        </div>

        <div className="mt-3 pt-3 border-t border-[var(--rule)] flex flex-col gap-1">
          <SourceRow label="Sumber" value={`${spec.source.label} = ${spec.source.voltage} V`} />
          {hasExtraSources && spec.extra_sources.map((s, i) => (
            <SourceRow
              key={i}
              label="Sumber"
              value={
                `${s.label} = ${s.voltage} V` +
                (s.polarity ? ` (${POLARITY_LABELS[s.polarity] ?? s.polarity} dengan ${spec.source.label})` : '')
              }
            />
          ))}
        </div>
      </div>

    </div>
  )
}