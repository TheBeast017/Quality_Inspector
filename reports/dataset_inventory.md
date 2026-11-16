# NEU-DET Dataset Inventory Report

**Date**: 2026-11-16  
**Project**: Industrial AI Inspection - Quality Inspection System  
**Dataset**: NEU-DET (Steel Surface Defect Detection)

---

## 1. Dataset Overview

| Property | Value |
|----------|-------|
| **Dataset Name** | NEU-DET |
| **Source Repository** | https://github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection |
| **Paper Reference** | "Deep Learning-based Steel Surface Defect Detection" (Wu et al., 2018) |
| **Total Images** | 1770 |
| **Annotation Format** | Pascal-VOC XML → Converted to YOLO |
| **Native Resolution** | 200 × 200 pixels |
| **Color Space** | RGB (3-channel) |
| **Number of Classes** | 6 |

---

## 2. Class Definitions

| Class ID | Class Name | Description | Total Objects | Percentage |
|----------|------------|-------------|---------------|------------|
| 0 | crazing | Fine crack networks on surface | 678 | 16.4% |
| 1 | inclusion | Foreign material trapped in steel | 1001 | 24.3% |
| 2 | patches | Irregular surface discoloration | 866 | 21.0% |
| 3 | pitted_surface | Small crater-like depressions | 423 | 10.3% |
| 4 | rolled-in_scale | Oxide scale pressed into surface | 620 | 15.0% |
| 5 | scratches | Linear surface abrasions | 538 | 13.0% |
| **Total** | | | **4126** | **100.0%** |

---

## 3. Train/Val/Test Split

Split performed **by image filename** (not by class) to prevent data leakage.

| Split | Images | Annotations | Ratio |
|-------|--------|-------------|-------|
| Train | 1,239 | 2,898 | 70.0% |
| Validation | 265 | 612 | 15.0% |
| Test | 266 | 616 | 15.0% |
| **Total** | **1,770** | **4,126** | **100.0%** |

**Split Seed**: 42 (reproducible)

---

## 4. Class Distribution Per Split

| Split | crazing | inclusion | patches | pitted_surface | rolled-in_scale | scratches | Total |
|-------|---------|-----------|---------|----------------|-----------------|-----------|-------|
| Train | 487 | 709 | 614 | 297 | 435 | 356 | 2,898 |
| Val | 97 | 148 | 125 | 64 | 94 | 84 | 612 |
| Test | 94 | 144 | 127 | 62 | 91 | 98 | 616 |
| **Total** | **678** | **1001** | **866** | **423** | **620** | **538** | **4,126** |

---

## 5. Bounding Box Statistics (Normalized 0–1)

| Class | Count | Mean Width | Mean Height | Mean Area | Mean Aspect Ratio |
|-------|-------|------------|-------------|-----------|-------------------|
| crazing | 678 | 0.923 | 0.917 | 0.847 | 1.01 |
| inclusion | 1001 | 0.762 | 0.753 | 0.574 | 1.01 |
| patches | 866 | 0.781 | 0.776 | 0.606 | 1.01 |
| pitted_surface | 423 | 0.615 | 0.609 | 0.375 | 1.01 |
| rolled-in_scale | 620 | 0.678 | 0.671 | 0.455 | 1.01 |
| scratches | 538 | 0.554 | 0.549 | 0.304 | 1.01 |

**Notes**:
- All defect classes have bounding boxes that cover large portions of the 200×200 images
- Aspect ratios are close to 1.0 (nearly square) for all classes
- Scratches tend to have slightly smaller normalized boxes (more elongated in original aspect)

---

## 6. Image Properties

- **Resolution**: 200 × 200 pixels (all images consistent)
- **Channels**: 3 (RGB)
- **Bit Depth**: 8-bit per channel (0–255)
- **File Format**: JPEG (.jpg)
- **Mean Pixel Intensity**: ~120 (varies by defect type)
- **No corrupted/unreadable images detected**

---

## 7. Directory Structure (Post-Processing)

```
data/processed/neu_det/
├── dataset.yaml              # YOLO configuration
├── images/
│   ├── train/                # 1,239 images
│   ├── val/                  # 265 images
│   └── test/                 # 266 images
└── labels/
    ├── train/                # 1,239 .txt files
    ├── val/                  # 265 .txt files
    └── test/                 # 266 .txt files

reports/dataset_samples/      # 5 rendered samples with bounding boxes
notebooks/01_dataset_exploration.ipynb  # Full exploration notebook
```

---

## 8. YOLO Configuration (`dataset.yaml`)

```yaml
path: C:/Users/Kartikay Tewari/OneDrive/Desktop/Projects/Quality_Inspection/data/processed/neu_det
train: images/train
val: images/val
test: images/test

nc: 6
names: ['crazing', 'inclusion', 'patches', 'pitted_surface', 'rolled-in_scale', 'scratches']

split_ratios: [0.7, 0.15, 0.15]
split_seed: 42
```

---

## 9. Quality Checks Performed

✅ All 1770 images have corresponding XML annotations  
✅ All XML files parse successfully  
✅ No duplicate image filenames  
✅ All bounding boxes within image bounds (after clipping)  
✅ No empty annotation files (every image has ≥1 defect)  
✅ Class name mapping verified against XML source  
✅ Train/Val/Test splits are disjoint (no overlapping filenames)  
✅ Split ratios match specification (70/15/15)  
✅ YOLO label format validated (class_id x_center y_center width height)  
✅ Rendered sample images confirm correct bbox overlay  

---

## 10. Known Issues / Limitations

1. **Class Imbalance**: Inclusion class has 2.4× more samples than pitted_surface. Consider weighted loss or oversampling during training.

2. **Single Defect Per Image**: NEU-DET typically has one defect type per image. Multi-defect scenarios not represented.

3. **Resolution**: 200×200 is relatively low. May need upscaling for detection of fine defects (scratches).

4. **Background Variation**: Limited background diversity (mostly uniform steel surface).

5. **Annotation Precision**: Some bounding boxes appear to cover entire defect region loosely rather than tight fit.

---

## 11. Next Steps

1. **Train YOLOv8 Detection Baseline** (V2)
   - Config: `configs/detection.yaml`
   - Model: YOLOv8n/s/m (start with nano for speed)
   - Target: mAP@0.5 > 0.85 on test split

2. **Train YOLOv8 Segmentation** (V3)
   - Config: `configs/segmentation.yaml`
   - Compare instance segmentation vs bounding box detection

3. **Anomaly Detection Baseline** (V4)
   - Use MVTec AD or normal-only NEU-DET samples
   - Config: `configs/anomaly.yaml` (PatchCore)

4. **Hybrid Detection + Anomaly** (V5)
   - Combine supervised detection with anomaly scoring
   - Research question: Does hybrid outperform supervised alone?

---

## 12. Reproducibility

- **Random Seed**: 42 (used for train/val/test split)
- **Environment**: Python 3.14, PyTorch 2.14.1+cu126
- **Scripts**: `scripts/download_dataset.py`, `scripts/prepare_dataset.py`
- **Config**: `configs/dataset.yaml`
- **Git Commit**: Dataset preparation complete (post-process)