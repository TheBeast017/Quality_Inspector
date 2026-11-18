from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
import torch
from pathlib import Path
import uuid
import time
from datetime import datetime
import logging

from src.inference.engine import InspectionEngine
from src.database import get_db, InspectionRecord, init_db
from src.utils.config import get_app_config as load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Industrial AI Inspection API",
    version="0.1.0",
    description="Automated visual inspection for manufactured components"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine: Optional[InspectionEngine] = None


@app.on_event("startup")
async def startup_event():
    global engine
    config = load_config()
    det_weights = config.get("detection_weights", "runs/detect/train/weights/best.pt")
    seg_weights = config.get("segmentation_weights", "runs/segment/seg_train/weights/best.pt")
    device = config.get("inference_device", "auto")

    logger.info(f"Loading detection model: {det_weights}")
    logger.info(f"Loading segmentation model: {seg_weights}")
    logger.info(f"Device: {device}")

    engine = InspectionEngine(
        detection_weights=det_weights,
        segmentation_weights=seg_weights,
        device=device
    )
    init_db()
    logger.info("API startup complete")


class DefectResponse(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2] normalized
    mask: Optional[List[List[float]]] = None  # polygon points
    area_px: Optional[float] = None
    severity: Optional[str] = None


class InspectionResponse(BaseModel):
    inspection_id: str
    timestamp: str
    image_shape: List[int]
    defects: List[DefectResponse]
    decision: str  # PASS / REJECT
    processing_time_ms: float


@app.post("/inspect", response_model=InspectionResponse)
async def inspect_image(file: UploadFile = File(...)):
    if engine is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    start_time = time.time()
    result = engine.inspect(image)
    processing_time = (time.time() - start_time) * 1000

    # Save to database
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        record = InspectionRecord(
            inspection_id=result["inspection_id"],
            timestamp=datetime.fromisoformat(result["timestamp"]),
            image_shape=str(result["image_shape"]),
            defects_count=len(result["defects"]),
            decision=result["decision"],
            processing_time_ms=processing_time,
            result_json=str(result)
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

    return InspectionResponse(
        inspection_id=result["inspection_id"],
        timestamp=result["timestamp"],
        image_shape=result["image_shape"],
        defects=[
            DefectResponse(
                class_id=d["class_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=d["bbox"],
                mask=d.get("mask"),
                area_px=d.get("area_px"),
                severity=d.get("severity")
            )
            for d in result["defects"]
        ],
        decision=result["decision"],
        processing_time_ms=processing_time
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": engine is not None}


@app.get("/history")
async def get_history(limit: int = 50, offset: int = 0):
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        records = db.query(InspectionRecord).order_by(
            InspectionRecord.timestamp.desc()
        ).offset(offset).limit(limit).all()
        return [
            {
                "inspection_id": r.inspection_id,
                "timestamp": r.timestamp.isoformat(),
                "defects_count": r.defects_count,
                "decision": r.decision,
                "processing_time_ms": r.processing_time_ms
            }
            for r in records
        ]
    finally:
        db.close()


@app.get("/analytics")
async def get_analytics(limit: int = 200):
    """Aggregate defect statistics across past inspections for graph-based analysis."""
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        records = db.query(InspectionRecord).order_by(
            InspectionRecord.timestamp.desc()
        ).limit(limit).all()
    finally:
        db.close()

    CLASS_NAMES = ["crazing", "inclusion", "patches", "pitted_surface", "rolled-in_scale", "scratches"]
    SEVERITY_ORDER = ["minor", "moderate", "major", "critical", "unknown"]

    class_counts = {c: 0 for c in CLASS_NAMES}
    severity_counts = {s: 0 for s in SEVERITY_ORDER}
    conf_buckets = {"0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0}
    decisions = {"PASS": 0, "REJECT": 0}
    total_defects = 0
    total_inspections = len(records)
    processing_times = []

    for r in records:
        decisions[r.decision] = decisions.get(r.decision, 0) + 1
        processing_times.append(r.processing_time_ms or 0)
        try:
            result = eval(r.result_json) if r.result_json else {}
        except Exception:
            result = {}
        for d in result.get("defects", []):
            total_defects += 1
            cls = d.get("class_name", "")
            if cls in class_counts:
                class_counts[cls] += 1
            sev = d.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            conf = (d.get("confidence") or 0) * 100
            if conf < 25:
                conf_buckets["0-25%"] += 1
            elif conf < 50:
                conf_buckets["25-50%"] += 1
            elif conf < 75:
                conf_buckets["50-75%"] += 1
            else:
                conf_buckets["75-100%"] += 1

    return {
        "total_inspections": total_inspections,
        "total_defects": total_defects,
        "defects_by_class": class_counts,
        "defects_by_severity": severity_counts,
        "confidence_distribution": conf_buckets,
        "decisions": decisions,
        "avg_processing_time_ms": round(sum(processing_times) / len(processing_times), 1) if processing_times else 0,
        "max_processing_time_ms": round(max(processing_times), 1) if processing_times else 0,
        "defect_rate": round(total_defects / total_inspections, 2) if total_inspections else 0,
        "reject_rate": round(decisions["REJECT"] / total_inspections * 100, 1) if total_inspections else 0
    }


def _serve_frontend():
    """Serve the bundled frontend (frontend/dist) at / when present."""
    base = os.environ.get("INSPECTION_HOME", os.getcwd())
    dist = os.path.join(base, "frontend", "dist")
    index = os.path.join(dist, "index.html")
    if os.path.isfile(index):
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


_serve_frontend()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)