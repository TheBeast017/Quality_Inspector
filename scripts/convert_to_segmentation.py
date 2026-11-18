#!/usr/bin/env python
"""
Convert NEU-DET detection labels (YOLO box) to segmentation labels (YOLO polygon).

NEU-DET provides only bounding box annotations. For YOLO-seg training we need
polygon annotations. Since no pixel-level masks exist, we derive 4-point
rectangular polygons from the bounding boxes. This is a known limitation:
the segmentation model will learn to output rectangular masks that match
the boxes, not the true defect shape.

For true segmentation quality, MVTec AD (pixel-level masks) is needed (V4).
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logging import get_logger

logger = get_logger(__name__)


def box_to_polygon(line: str) -> str:
    """Convert a YOLO detection line to a YOLO-seg polygon line.

    Detection format: class_id xc yc w h
    Segmentation format: class_id x1 y1 x2 y2 x3 y3 x4 y4
    """
    parts = line.strip().split()
    if len(parts) != 5:
        return line  # already polygon or invalid

    class_id = int(parts[0])
    xc = float(parts[1])
    yc = float(parts[2])
    w = float(parts[3])
    h = float(parts[4])

    # Rectangle corners (clockwise from top-left)
    x1 = xc - w / 2
    y1 = yc - h / 2
    x2 = xc + w / 2
    y2 = yc - h / 2
    x3 = xc + w / 2
    y3 = yc + h / 2
    x4 = xc - w / 2
    y4 = yc + h / 2

    return f"{class_id} {x1:.6f} {y1:.6f} {x2:.6f} {y2:.6f} {x3:.6f} {y3:.6f} {x4:.6f} {y4:.6f}"


def main():
    parser = argparse.ArgumentParser(description="Convert detection labels to segmentation polygons")
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=Path("data/processed/neu_det/labels"),
        help="Source directory with detection labels (train/val/test)",
    )
    parser.add_argument(
        "--dst-dir",
        type=Path,
        default=Path("data/processed/neu_det_seg/labels"),
        help="Output directory for segmentation labels",
    )
    args = parser.parse_args()

    for split in ["train", "val", "test"]:
        src_split = args.src_dir / split
        dst_split = args.dst_dir / split
        dst_split.mkdir(parents=True, exist_ok=True)

        n_files = 0
        n_objects = 0
        for src_file in src_split.glob("*.txt"):
            dst_file = dst_split / src_file.name
            with open(src_file) as fin, open(dst_file, "w") as fout:
                for line in fin:
                    if not line.strip():
                        continue
                    n_objects += 1
                    fout.write(box_to_polygon(line) + "\n")
            n_files += 1

        logger.info(f"{split}: {n_files} files, {n_objects} objects converted")

    # Copy images
    img_src = Path("data/processed/neu_det/images")
    img_dst = Path("data/processed/neu_det_seg/images")
    for split in ["train", "val", "test"]:
        dst = img_dst / split
        dst.mkdir(parents=True, exist_ok=True)
        for img_file in (img_src / split).glob("*.jpg"):
            shutil.copy2(img_file, dst / img_file.name)
        logger.info(f"Copied {split} images")

    # Generate dataset.yaml for segmentation
    yaml_path = Path("data/processed/neu_det_seg/dataset.yaml")
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(
        "# NEU-DET segmentation dataset (polygons derived from bounding boxes)\n"
        f"path: {yaml_path.parent.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "\n"
        "nc: 6\n"
        "names: ['crazing', 'inclusion', 'patches', 'pitted_surface', 'rolled-in_scale', 'scratches']\n"
    )
    logger.info(f"Generated segmentation dataset.yaml: {yaml_path}")
    logger.info("Segmentation dataset ready at data/processed/neu_det_seg/")


if __name__ == "__main__":
    main()