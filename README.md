# Industrial AI Inspection

AI-powered automated visual inspection and defect severity assessment for manufactured components.

## Pipeline

```
Image → Preprocess → Detect Component → Detect Defect (YOLO)
    → Segment Defect → Anomaly Detection → Analyze
    → Severity → PASS/REJECT → Report
```

## Current Status

**Phase: V0 — Environment & Project Foundation**

| Component | Status |
|-----------|--------|
| Python environment | ✅ Created (`.venv/`) |
| CUDA / GPU | ⚠️ RTX 4060 detected but **disabled** (Optimus, kernel driver stopped). See [GPU Setup](#gpu-setup). |
| Project structure | ✅ Created |
| Configuration system | ✅ YAML configs in `configs/` |
| Logging | ✅ Structured logging in `src/utils/logging.py` |
| Git | ⏳ Not initialized yet |

## Quick Start

```cmd
# 1. Clone and enter project
cd C:\Users\Kartikay Tewari\OneDrive\Desktop\Projects\Quality_Inspection

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Install PyTorch with CUDA (if GPU is enabled)
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

# 4. Install remaining dependencies
python -m pip install -r requirements.txt

# 5. Verify installation
python -c "import torch; print('CUDA:', torch.cuda.is_available()); import ultralytics, cv2, fastapi, mlflow; print('OK')"
```

## GPU Setup

The NVIDIA RTX 4060 Laptop GPU is present but currently **disabled** (PnP status "Unknown", kernel driver `nvlddmkm` stopped). This is typical for Optimus laptops where the dGPU powers down when not in use.

**To enable:**
1. Open **Device Manager** as Administrator
2. Find **Display adapters** → NVIDIA GeForce RTX 4060 Laptop GPU
3. Right-click → **Enable device** (or update driver)
4. Or check BIOS for "Discrete GPU only" / "NVIDIA GPU" setting

After enabling, run `nvidia-smi` to verify. Then reinstall PyTorch if needed.

**Note:** Training will run on CPU (~20–50× slower) until GPU is enabled. The project structure and all code are GPU-ready.

## Project Structure

```
Quality_Inspection/
├── configs/
│   ├── dataset.yaml           # Dataset configurations (NEU-DET, GC10-DET, MVTec AD)
│   ├── detection.yaml         # YOLO detection hyperparameters
│   ├── segmentation.yaml      # YOLO segmentation hyperparameters
│   ├── anomaly.yaml           # PatchCore anomaly detection config
│   ├── inspection_rules.yaml  # PASS/REJECT decision rules (configurable)
│   └── app.yaml               # Runtime settings (paths, DB, MLflow)
├── data/
│   ├── raw/                   # Downloaded datasets (not in git)
│   ├── interim/               # Intermediate processing
│   ├── processed/             # Final training splits
│   └── external/              # External data
├── notebooks/                 # Exploration notebooks
├── scripts/                   # Training & evaluation scripts
├── src/
│   ├── utils/                 # Config, logging, helpers
│   ├── data/                  # Dataset loading & preprocessing
│   ├── detection/             # YOLO detection
│   ├── segmentation/          # YOLO segmentation
│   ├── anomaly/               # PatchCore anomaly detection
│   ├── analysis/              # Defect measurement
│   ├── severity/              # Severity assessment
│   ├── decision/              # PASS/REJECT engine
│   ├── inference/             # End-to-end pipeline
│   ├── evaluation/            # Metrics & reporting
│   └── database/              # DB models & queries
├── api/
│   └── main.py                # FastAPI endpoints
├── frontend/                  # React + Vite dashboard
├── tests/                     # Unit tests
├── models/                    # Trained model weights (not in git)
├── experiments/               # MLflow runs (not in git)
├── reports/                   # Generated reports
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Package metadata
├── .env.example               # Environment variable template
├── docker-compose.yml         # Deployment stack
└── README.md                  # This file
```

## Development Roadmap

| Phase | Goal | Exit Criterion |
|-------|------|----------------|
| **V0** | Environment, git, configs, logging | `python -c "import src"` works |
| **V1** | Dataset download, conversion, split | 1800 NEU-DET images ready for YOLO |
| **V2** | YOLO detection baseline | mAP50 reported, confusion matrix |
| **V3** | Segmentation (YOLO-seg) | IoU / Dice per class |
| **V4** | Anomaly detection (PatchCore) | Image & pixel AUROC on MVTec AD |
| **V5** | Defect measurement | Area, bbox, count, mm conversion |
| **V6** | Severity model | Transparent methodology (no fake thresholds) |
| **V7** | PASS/REJECT engine | Configurable YAML rules |
| **V8** | FastAPI + React + PostgreSQL + MLflow | End-to-end upload → result |
| **V9** | Docker Compose single-command run | `docker compose up` works |

## Key Principles

1. **Incremental** — One working milestone at a time. No 20-file dumps.
2. **Configurable** — All hyperparameters and rules in YAML, never hard-coded.
3. **Honest metrics** — Report standard metrics (mAP, IoU, AUROC), not inflated claims.
4. **Engineering validity** — Distinguish CV confidence from engineering certainty. No fake "industry standard" thresholds.
5. **Reproducible** — Every experiment tracked in MLflow with full config.

## License

MIT