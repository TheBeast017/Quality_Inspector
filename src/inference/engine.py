import cv2
import numpy as np
import torch
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

CLASS_NAMES = [
    "crazing", "inclusion", "patches",
    "pitted_surface", "rolled-in_scale", "scratches"
]


class InspectionEngine:
    def __init__(
        self,
        detection_weights: str,
        segmentation_weights: str,
        device: str = "auto"
    ):
        self.device = self._resolve_device(device)
        logger.info(f"Using device: {self.device}")

        self.det_model = YOLO(detection_weights)
        self.det_model.to(self.device)
        self.det_model.fuse()

        self.seg_model = YOLO(segmentation_weights)
        self.seg_model.to(self.device)
        self.seg_model.fuse()

        self.conf_threshold = 0.55
        self.iou_threshold = 0.5
        self.max_det = 300

    def _resolve_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def inspect(self, image: np.ndarray) -> Dict[str, Any]:
        h, w = image.shape[:2]

        det_results = self.det_model(
            image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            max_det=self.max_det,
            verbose=False
        )[0]

        seg_results = self.seg_model(
            image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            max_det=self.max_det,
            verbose=False
        )[0]

        defects = self._merge_results(det_results, seg_results, w, h)
        decision = self._make_decision(defects)

        return {
            "inspection_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "image_shape": [h, w, 3],
            "defects": defects,
            "decision": decision
        }

    def _merge_results(
        self,
        det_results,
        seg_results,
        img_w: int,
        img_h: int
    ) -> List[Dict[str, Any]]:
        defects = []

        if det_results.boxes is not None:
            boxes = det_results.boxes.xyxy.cpu().numpy()
            confs = det_results.boxes.conf.cpu().numpy()
            cls_ids = det_results.boxes.cls.cpu().numpy().astype(int)

            seg_masks = None
            if seg_results.masks is not None:
                seg_masks = seg_results.masks.xy

            for i, (box, conf, cls_id) in enumerate(zip(boxes, confs, cls_ids)):
                x1, y1, x2, y2 = box
                bbox_norm = [x1 / img_w, y1 / img_h, x2 / img_w, y2 / img_h]

                mask_poly = None
                area_px = None
                if seg_masks and i < len(seg_masks):
                    poly = seg_masks[i]
                    if len(poly) > 0:
                        mask_poly = poly.tolist()
                        area_px = cv2.contourArea(poly.astype(np.float32))

                defects.append({
                    "class_id": int(cls_id),
                    "class_name": CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f"class_{cls_id}",
                    "confidence": float(conf),
                    "bbox": bbox_norm,
                    "mask": mask_poly,
                    "area_px": area_px,
                    "severity": self._assess_severity(cls_id, area_px, img_w, img_h)
                })

        return defects

    def _assess_severity(
        self,
        cls_id: int,
        area_px: Optional[float],
        img_w: int,
        img_h: int
    ) -> str:
        if area_px is None:
            return "unknown"

        img_area = img_w * img_h
        rel_area = area_px / img_area

        if rel_area < 0.001:
            return "minor"
        elif rel_area < 0.01:
            return "moderate"
        elif rel_area < 0.05:
            return "major"
        else:
            return "critical"

    def _make_decision(self, defects: List[Dict[str, Any]]) -> str:
        if not defects:
            return "PASS"

        for d in defects:
            if d["severity"] in ("major", "critical"):
                return "REJECT"
            if d["confidence"] > 0.8 and d["severity"] == "moderate":
                return "REJECT"

        return "PASS"