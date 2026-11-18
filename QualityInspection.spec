# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['api.main', 'uvicorn', 'uvicorn.config', 'uvicorn.server', 'uvicorn.lifespan.on', 'fastapi', 'fastapi.applications', 'fastapi.routing', 'fastapi.middleware.cors', 'starlette.applications', 'starlette.routing', 'starlette.middleware.cors', 'starlette.responses', 'starlette.formparsers', 'ultralytics', 'ultralytics.models', 'ultralytics.models.yolo', 'torch', 'torch.nn', 'torch.nn.modules', 'torch.cuda', 'cv2', 'numpy', 'PIL', 'yaml', 'sqlalchemy', 'alembic', 'pydantic', 'pydantic_settings', 'scipy', 'sklearn', 'psutil', 'bottle', 'websocket', 'triton', 'tokenizers']
hiddenimports += collect_submodules('ultralytics')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('cv2')


a = Analysis(
    ['C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/runs/detect/train/weights/best.pt', 'runs/detect/train/weights'), ('C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/runs/segment/seg_train/weights/best.pt', 'runs/segment/seg_train/weights'), ('C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/configs', 'configs'), ('C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/frontend/dist', 'frontend/dist')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QualityInspection',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QualityInspection',
)
