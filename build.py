#!/usr/bin/env python3
"""
Script build otomatis untuk Generator Soal Rangkaian Listrik SMA.

Jalankan dari root folder project:
    python build.py

Yang dilakukan:
  1. npm run build  (di folder frontend/)
  2. pyinstaller app.spec  (di folder backend/)
  3. Tampilkan lokasi output
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = BACKEND / "dist" / "GeneratorRangkaian"


def run(cmd: list[str], cwd: Path, label: str) -> None:
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"\n❌  Gagal: {label}")
        sys.exit(result.returncode)
    print(f"✅  Selesai: {label}")


def check_tools() -> None:
    """Pastikan npm dan pyinstaller tersedia."""
    missing = []
    for tool in ["npm", "pyinstaller"]:
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        print(f"❌  Tool berikut tidak ditemukan: {', '.join(missing)}")
        print("    Install dulu:")
        if "npm" in missing:
            print("      npm  → https://nodejs.org")
        if "pyinstaller" in missing:
            print("      pyinstaller → pip install pyinstaller")
        sys.exit(1)


def main() -> None:
    print("\n🔧  Build Generator Soal Rangkaian Listrik SMA")
    print(f"    Root   : {ROOT}")
    print(f"    Output : {DIST}")

    check_tools()

    # 1. Install npm deps jika belum ada
    if not (FRONTEND / "node_modules").exists():
        run(["npm", "install"], cwd=FRONTEND, label="npm install (pertama kali)")

    # 2. Build React
    run(["npm", "run", "build"], cwd=FRONTEND, label="Build React frontend")

    # 3. Pastikan pyproject deps terinstall
    if shutil.which("uv"):
        run(["uv", "sync"], cwd=BACKEND, label="uv sync (Python deps)")
    else:
        print("  ℹ️  uv tidak ditemukan, asumsikan deps sudah terinstall.")

    # 4. PyInstaller
    run(
        ["pyinstaller", "app.spec", "--noconfirm"],
        cwd=BACKEND,
        label="PyInstaller bundle",
    )

    # 5. Ringkasan
    if DIST.exists():
        size_mb = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file()) / 1e6
        print(f"\n{'='*55}")
        print(f"  ✅  Build berhasil!")
        print(f"  📁  Output  : {DIST}")
        print(f"  📦  Ukuran  : {size_mb:.0f} MB")
        print(f"\n  Cara distribusi:")
        print(f"  → ZIP seluruh folder  {DIST.name}/")
        print(f"  → Teman extract & jalankan  GeneratorRangkaian.exe")
        print(f"{'='*55}\n")
    else:
        print("\n⚠️   Folder output tidak ditemukan — cek log PyInstaller di atas.")


if __name__ == "__main__":
    main()
