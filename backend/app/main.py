"""Entry point aplikasi FastAPI — termasuk serving frontend statis."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import questions_router

app = FastAPI(
    title="Generator Soal Rangkaian Listrik SMA",
    description=(
        "API untuk men-generate soal fisika rangkaian listrik level SMA, "
        "lengkap dengan gambar SVG presisi, jawaban matematis, dan deskripsi "
        "teks struktural — semuanya diturunkan dari satu CircuitSpec yang sama."
    ),
    version="0.1.0",
)

# CORS — hanya diperlukan saat dev (Vite dev server terpisah).
# Saat production (PyInstaller), frontend di-serve dari FastAPI langsung
# sehingga tidak ada cross-origin request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static file serving — aktif hanya jika folder `static` tersedia
# (i.e. saat distribusi PyInstaller, bukan saat dev dengan Vite terpisah).
# ---------------------------------------------------------------------------
def _find_static_dir() -> Path | None:
    """Cari folder static di beberapa lokasi yang mungkin."""
    candidates = [
        # PyInstaller: _MEIPASS adalah folder temp tempat file di-extract
        Path(getattr(sys, "_MEIPASS", "")) / "static",
        # Dev: jalankan dari root repo
        Path(__file__).parent.parent.parent / "frontend" / "dist",
        # Fallback: folder static di samping executable
        Path(sys.executable).parent / "static",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return None


_static_dir = _find_static_dir()

if _static_dir:
    # Mount assets (JS, CSS, gambar) di /assets
    assets_dir = _static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Semua route non-API → kembalikan index.html (SPA routing)
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        index = _static_dir / "index.html"
        return FileResponse(str(index))
