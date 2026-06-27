# Generator Soal Rangkaian Listrik SMA

Generator soal fisika rangkaian listrik (level SMA) dengan gambar presisi
(bukan dari LLM), topologi yang bisa di-random, dan arsitektur yang scalable
ke jenis soal baru (RC/RL, pola non-standar, dll).

## Status

🚧 **Fondasi backend** — model data, dua pola topologi dasar (seri & paralel
sederhana), tiga service inti (render/calculate/describe), dan satu endpoint
generate sudah berjalan dan teruji. Frontend React **belum dibuat**.

## Arsitektur Kunci

Satu `CircuitSpec` (lihat `app/models/circuit_spec.py`) adalah **single
source of truth** untuk setiap soal. Dia dibuat sekali oleh modul pola
(`app/patterns/`), lalu dipakai ulang oleh tiga service independen:

```
                    ┌─────────────────┐
                    │   CircuitSpec   │  ← dibuat sekali oleh pattern generator
                    └────────┬────────┘
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
   services/renderer  services/calculator  services/describer
   (SVG via schemdraw) (R_total, I, V)      (teks struktural utk LLM)
```

Topologi direpresentasikan sebagai **Branch rekursif** (seri/paralel
bersarang), bukan graph bebas — cukup ekspresif untuk semua pola SMA standar
tanpa perlu circuit solver / node analysis.

## Struktur Folder Lama
```
backend/
├── app/
│   ├── main.py                  # entry point FastAPI
│   ├── models/
│   │   ├── components.py        # Component, VoltageSource
│   │   └── circuit_spec.py      # Branch (rekursif), CircuitSpec
│   ├── patterns/                # modul pola topologi (scalable)
│   │   ├── base.py              # interface PatternGenerator
│   │   ├── series_pattern.py    # pola SERIES_SIMPLE
│   │   ├── parallel_pattern.py  # pola PARALLEL_SIMPLE
│   │   └── registry.py          # titik pendaftaran semua pola
│   ├── services/                # tiga konsumen CircuitSpec
│   │   ├── renderer.py          # CircuitSpec -> SVG (schemdraw)
│   │   ├── calculator.py        # CircuitSpec -> jawaban matematis
│   │   └── describer.py         # CircuitSpec -> teks untuk LLM
│   └── api/
│       ├── schemas.py           # request/response model API
│       └── questions.py         # endpoint /api/questions/*
└── tests/                       # pytest, 14 test, semua lulus
```

## Struktur Folder Baru

```
├── NOTES.md
├── README.md
├── backend
│   ├── app
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-313.pyc
│   │   │   └── main.cpython-313.pyc
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-313.pyc
│   │   │   │   ├── questions.cpython-313.pyc
│   │   │   │   └── schemas.cpython-313.pyc
│   │   │   ├── questions.py
│   │   │   └── schemas.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-313.pyc
│   │   │   │   ├── circuit_spec.cpython-313.pyc
│   │   │   │   └── components.cpython-313.pyc
│   │   │   ├── circuit_spec.py
│   │   │   └── components.py
│   │   ├── patterns
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-313.pyc
│   │   │   │   ├── base.cpython-313.pyc
│   │   │   │   ├── mixed_basic_pattern.cpython-313.pyc
│   │   │   │   ├── parallel_pattern.cpython-313.pyc
│   │   │   │   ├── registry.cpython-313.pyc
│   │   │   │   ├── series_pattern.cpython-313.pyc
│   │   │   │   └── value_generator.cpython-313.pyc
│   │   │   ├── base.py
│   │   │   ├── mixed_basic_pattern.py
│   │   │   ├── parallel_pattern.py
│   │   │   ├── registry.py
│   │   │   ├── series_pattern.py
│   │   │   └── value_generator.py
│   │   └── services
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-313.pyc
│   │       │   ├── calculator.cpython-313.pyc
│   │       │   ├── describer.cpython-313.pyc
│   │       │   └── renderer.cpython-313.pyc
│   │       ├── calculator.py
│   │       ├── describer.py
│   │       └── renderer.py
│   ├── main.py
│   ├── pyproject.toml
│   ├── tests
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-313.pyc
│   │   │   ├── test_api.cpython-313-pytest-9.1.1.pyc
│   │   │   ├── test_calculator.cpython-313-pytest-9.1.1.pyc
│   │   │   ├── test_circuit_spec.cpython-313-pytest-9.1.1.pyc
│   │   │   └── test_renderer.cpython-313-pytest-9.1.1.pyc
│   │   ├── test_api.py
│   │   ├── test_calculator.py
│   │   ├── test_circuit_spec.py
│   │   ├── test_mixed_basic.py
│   │   └── test_renderer.py
│   └── uv.lock
├── frontend
│   ├── README.md
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src
│   │   ├── App.jsx
│   │   ├── api
│   │   │   └── questions.js
│   │   ├── assets
│   │   │   ├── hero.png
│   │   │   └── vite.svg
│   │   ├── components
│   │   │   ├── AnswerForm.jsx
│   │   │   ├── CircuitDiagram.jsx
│   │   │   ├── Controls.jsx
│   │   │   └── ErrorBanner.jsx
│   │   ├── hooks
│   │   │   └── useQuestion.js
│   │   ├── index.css
│   │   └── main.jsx
│   └── vite.config.js
```

## Menjalankan

```bash
cd backend
uv sync                                          # install dependensi
uv run uvicorn app.main:app --reload --port 8000 # jalankan server dev
```

Buka `http://127.0.0.1:8000/docs` untuk Swagger UI interaktif.

### Test

```bash
uv run pytest tests/ -v
```

## Endpoint Tersedia

- `GET /health` — health check
- `GET /api/questions/patterns` — daftar pola yang sudah punya generator
- `GET /api/questions/generate?pattern=...&difficulty=...&seed=...` —
  generate satu soal lengkap (spec + SVG + jawaban + deskripsi teks LLM).
  Semua parameter opsional; jika `pattern` tidak diisi, dipilih random.

## Menambah Pola Topologi Baru

1. Buat file baru di `app/patterns/`, implementasikan `PatternGenerator`
   (lihat `series_pattern.py` sebagai contoh paling sederhana).
2. Tambahkan anggota baru ke enum `PatternType` di `app/models/circuit_spec.py`.
3. Daftarkan instance generator ke `PATTERN_REGISTRY` di `app/patterns/registry.py`.

Tidak ada kode lain (renderer, calculator, describer, endpoint) yang perlu
diubah — semuanya bekerja generik di atas struktur `CircuitSpec`.

## Menambah Jenis Komponen Baru (misal Kapasitor untuk fase RC)

1. Tambah anggota baru ke enum `ComponentType` di `app/models/components.py`.
2. Tambah field opsional di `Component` jika perlu (misal `reactance`).
3. Sesuaikan rumus di `services/calculator.py` jika rumus seri/paralelnya
   berbeda untuk jenis komponen baru tersebut.

Struktur `Branch` (rekursif seri/paralel) tidak perlu diubah.

## Catatan Implementasi Renderer

Layout cabang paralel di `services/renderer.py` digambar dengan menumpuk
cabang secara vertikal dan menyatukan node kiri/kanan lewat kabel eksplisit
(`Line().toy(...)`) — bukan hanya `push()/pop()` schemdraw, karena
percobaan awal menunjukkan itu tidak otomatis menyatukan titik akhir
cabang dengan benar. Rekursi mendukung nesting penuh (paralel di dalam
seri, dan sebaliknya) dan sudah diverifikasi secara visual.
