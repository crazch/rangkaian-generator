const BASE = '/api/questions'

export async function generateQuestion({
  pattern,
  difficulty,
  seed,
  // Advanced Layer 1
  n_components,
  r_min,
  r_max,
  force_identical,
  // Advanced Layer 2
  internal_resistance,
  show_power,
  unit_prefix,
} = {}) {
  const params = new URLSearchParams()

  if (pattern)      params.set('pattern', pattern)
  if (difficulty)   params.set('difficulty', difficulty)
  if (seed != null) params.set('seed', String(seed))

  // Advanced — hanya kirim jika ada isinya
  if (n_components != null)         params.set('n_components', String(n_components))
  if (r_min != null)                params.set('r_min', String(r_min))
  if (r_max != null)                params.set('r_max', String(r_max))
  if (force_identical != null)      params.set('force_identical', String(force_identical))
  if (internal_resistance != null)  params.set('internal_resistance', String(internal_resistance))
  if (show_power)                   params.set('show_power', 'true')
  if (unit_prefix)                  params.set('unit_prefix', unit_prefix)

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