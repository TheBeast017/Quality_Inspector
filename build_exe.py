"""Build a standalone PyInstaller .exe for offline deployment.

Usage:
    pip install pyinstaller
    python build_exe.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DETECT_WEIGHTS = ROOT / "runs" / "detect" / "train" / "weights" / "best.pt"
SEG_WEIGHTS = ROOT / "runs" / "segment" / "seg_train" / "weights" / "best.pt"
HIDDEN_IMPORTS = [
    "uvicorn", "uvicorn.config", "uvicorn.server", "uvicorn.lifespan.on",
    "fastapi", "fastapi.applications", "fastapi.routing", "fastapi.middleware.cors",
    "starlette.applications", "starlette.routing", "starlette.middleware.cors",
    "starlette.responses", "starlette.formparsers",
    "ultralytics", "ultralytics.models", "ultralytics.models.yolo",
    "torch", "torch.nn", "torch.nn.modules", "torch.cuda",
    "cv2", "numpy", "PIL", "yaml", "sqlalchemy", "alembic",
    "pydantic", "pydantic_settings", "scipy", "sklearn",
    "psutil", "bottle", "websocket", "triton", "tokenizers",
]


def check_weights():
    missing = []
    for w in (DETECT_WEIGHTS, SEG_WEIGHTS):
        if not w.exists():
            missing.append(str(w))
    if missing:
        print("MISSING WEIGHTS:")
        for m in missing:
            print("  ", m)
        sys.exit(1)
    print(f"Found weights: {DETECT_WEIGHTS.name} ({DETECT_WEIGHTS.stat().st_size/1e6:.0f} MB)")
    print(f"Found weights: {SEG_WEIGHTS.name} ({SEG_WEIGHTS.stat().st_size/1e6:.0f} MB)")


def write_launcher():
    """Write a tiny launcher so the bundled app knows its own directory."""
    launcher = ROOT / "launcher.py"
    launcher.write_text('''
import os, sys
os.environ.setdefault("INSPECTION_HOME", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ["INSPECTION_HOME"])
import api.main  # noqa: F401
''')
    return launcher


def main():
    check_weights()
    launcher = write_launcher()

    hidden = ",".join(HIDDEN_IMPORTS)
    def add_data(source, dest):
        return f"--add-data={source}:{dest}"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--noconsole",
        "--name", "QualityInspection",
        add_data(str(DETECT_WEIGHTS), "runs/detect/train/weights"),
        add_data(str(SEG_WEIGHTS), "runs/segment/seg_train/weights"),
        add_data(str(ROOT / "configs"), "configs"),
        add_data(str(ROOT / "frontend" / "dist"), "frontend/dist"),
        "--hidden-import", "api.main",
        *sum([["--hidden-import", h] for h in HIDDEN_IMPORTS], []),
        "--collect-submodules", "ultralytics",
        "--collect-submodules", "torch",
        "--collect-submodules", "cv2",
        str(launcher),
    ]
    print("Running:", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("PyInstaller FAILED")
        sys.exit(r.returncode)

    print("\nDone. Build output: dist/QualityInspection/")


if __name__ == "__main__":
    main()