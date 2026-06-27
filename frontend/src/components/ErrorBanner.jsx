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
