"""Entry point untuk PyInstaller — jalankan uvicorn dan buka browser."""

from __future__ import annotations

import sys
import time
import threading
import webbrowser

import uvicorn


def _open_browser():
    """Tunggu server siap, lalu buka browser."""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    # Buka browser di background thread
    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()

    print("=" * 50)
    print("  Generator Soal Rangkaian Listrik SMA")
    print("  Buka: http://127.0.0.1:8000")
    print("  Tutup jendela ini untuk menghentikan aplikasi.")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",   # kurangi noise di terminal
    )
