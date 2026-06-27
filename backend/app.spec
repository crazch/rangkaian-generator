# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec untuk Generator Soal Rangkaian Listrik SMA
#
# Cara pakai:
#   cd backend
#   pyinstaller app.spec
#
# Output: dist/GeneratorRangkaian/ (folder) atau dist/GeneratorRangkaian.exe (onefile)

import sys
from pathlib import Path

block_cipher = None

# ---------------------------------------------------------------------------
# Cari lokasi schemdraw & matplotlib untuk data/binaries
# ---------------------------------------------------------------------------
import schemdraw, matplotlib, importlib
schemdraw_dir   = Path(schemdraw.__file__).parent
matplotlib_dir  = Path(matplotlib.__file__).parent

# Folder static hasil build React (npm run build di frontend/)
static_src = Path("../frontend/dist")

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ["main.py"],          # entry point kita (buka browser + jalankan uvicorn)
    pathex=[".", "app"],  # tambah folder app ke sys.path
    binaries=[],
    datas=[
        # schemdraw butuh file font & style di dalam package-nya
        (str(schemdraw_dir), "schemdraw"),
        # matplotlib butuh mpl-data (font, style, dll)
        (str(matplotlib_dir / "mpl-data"), "matplotlib/mpl-data"),
        # frontend build → akan di-serve oleh FastAPI sebagai static
        (str(static_src), "static"),
    ],
    hiddenimports=[
        # FastAPI / Starlette internals
        "fastapi",
        "fastapi.staticfiles",
        "fastapi.responses",
        "starlette.routing",
        "starlette.staticfiles",
        "starlette.responses",
        # uvicorn — butuh semua modul ini saat dipakai programatik
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # schemdraw backend — dia pakai matplotlib backend 'svg' non-interaktif
        "schemdraw",
        "schemdraw.elements",
        "matplotlib",
        "matplotlib.pyplot",
        "matplotlib.backends.backend_svg",
        "matplotlib.backends.backend_agg",
        # pydantic v2
        "pydantic",
        "pydantic.deprecated.class_validators",
        # app sendiri — pastikan semua modul terdaftar
        "app",
        "app.main",
        "app.api",
        "app.api.questions",
        "app.api.schemas",
        "app.models",
        "app.models.circuit_spec",
        "app.models.components",
        "app.patterns",
        "app.patterns.base",
        "app.patterns.registry",
        "app.patterns.series_pattern",
        "app.patterns.parallel_pattern",
        "app.patterns.mixed_basic_pattern",
        "app.patterns.value_generator",
        "app.services",
        "app.services.renderer",
        "app.services.calculator",
        "app.services.describer",
        # stdlib yang kadang luput di-detect
        "email.mime.text",
        "email.mime.multipart",
        "logging.handlers",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Buang paket besar yang tidak dipakai
        "tkinter",
        "PyQt5",
        "PyQt6",
        "wx",
        "IPython",
        "jupyter",
        "notebook",
        "scipy",
        "pandas",
        "sklearn",
        "PIL",       # Pillow tidak dipakai oleh schemdraw path SVG
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# Output: folder (lebih cepat startup, lebih mudah debug)
# Ganti ke EXE onefile kalau mau satu file tunggal (startup lebih lambat ~5dtk)
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # folder mode
    name="GeneratorRangkaian",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                # kompresi (opsional, butuh UPX)
    console=True,            # tampilkan terminal agar user tahu status
    icon=None,               # ganti dengan path .ico/.icns jika ada
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GeneratorRangkaian",
)
