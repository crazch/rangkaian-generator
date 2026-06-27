"""Entry point aplikasi FastAPI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# CORS dibuka untuk dev frontend lokal (Vite default port). Sesuaikan saat
# deploy production.
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
