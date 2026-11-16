#!/usr/bin/env python
"""
Prepare NEU-DET dataset for YOLO training.

Converts Pascal-VOC XML annotations to YOLO format (one .txt per image).
Creates train/val/test splits by image filename (never by class).
Generates dataset.yaml for YOLO.
"""

import argparse
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path so scripts work when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import get_dataset_config
from src.utils.helpers import set_seed
from src.utils.logging import get_logger

logger = get_logger(__name__)

# NEU-DET has 6 classes. XML annotations use these exact names:
CLASS_NAMES = ["crazing", "inclusion", "patches", "pitted_surface", "rolled-in_scale", "scratches"]

# Map XML class names to our canonical class IDs (handles aliases)
CLASS_TO_ID = {
    "crazing": 0,
    "inclusion": 1,
    "patches": 2,
    "pitted_surface": 3,
    "pitted": 3,          # alias
    "rolled-in_scale": 4,
    "rolled_in_scale": 4, # alias (underscore)
    "scratches": 5,
    "scratch": 5,         # alias (singular)
}


def parse_voc_xml(xml_path: Path) -> list[dict]:
    """Parse a Pascal-VOC XML annotation file to YOLO format."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    if size is None:
        raise ValueError(f"No <size> element in {xml_path}")
    img_width = int(size.find("width").text)
    img_height = int(size.find("height").text)

    objects = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip().lower()
        if name not in CLASS_TO_ID:
            logger.warning(f"Unknown class '{name}' in {xml_path}, skipping")
            continue
        class_id = CLASS_TO_ID[name]

        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)

        if xmax <= xmin or ymax <= ymin:
            logger.warning(f"Invalid bbox in {xml_path}: ({xmin},{ymin},{xmax},{ymax})")
            continue
        if xmax > img_width or ymax > img_height:
            logger.warning(f"BBox exceeds image size in {xml_path}")
            continue

        x_center = (xmin + xmax) / 2.0 / img_width
        y_center = (ymin + ymax) / 2.0 / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height

        objects.append({
            "class_id": class_id,
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height,
        })

    return objects


def write_yolo_label(objects: list[dict], output_path: Path) -> None:
    """Write YOLO format label file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for obj in objects:
            f.write(
                f"{obj['class_id']} "
                f"{obj['x_center']:.6f} {obj['y_center']:.6f} "
                f"{obj['width']:.6f} {obj['height']:.6f}\n"
            )


def split_filenames(filenames: list[str], ratios: list[float], seed: int) -> dict[str, list[str]]:
    """Split filenames into train/val/test by the given ratios."""
    assert abs(sum(ratios) - 1.0) < 1e-6, "Ratios must sum to 1.0"
    assert len(ratios) == 3, "Expected 3 ratios (train, val, test)"

    random.seed(seed)
    shuffled = filenames[:]
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])

    return {
        "train": shuffled[:n_train],
        "val": shuffled[n_train:n_train + n_val],
        "test": shuffled[n_train + n_val:],
    }


def copy_images(filenames: list[str], src_dir: Path, dst_dir: Path) -> None:
    """Copy image files to split directory."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for fname in filenames:
        src = src_dir / fname
        dst = dst_dir / fname
        if src.exists():
            shutil.copy2(src, dst)
        else:
            logger.warning(f"Image not found: {src}")


def generate_yaml_config(
    processed_dir: Path,
    class_names: list[str],
    ratios: list[float],
    seed: int,
) -> Path:
    """Generate dataset.yaml for YOLO."""
    yaml_path = processed_dir / "dataset.yaml"
    content = f"""# NEU-DET dataset configuration for YOLO
path: {processed_dir.as_posix()}
train: images/train
val: images/val
test: images/test

nc: {len(class_names)}
names: {class_names}

split_ratios: {ratios}
split_seed: {seed}
"""
    yaml_path.write_text(content)
    logger.info(f"Generated YOLO config: {yaml_path}")
    return yaml_path


def render_sample_image(
    images_dir: Path,
    labels_dir: Path,
    output_dir: Path,
    num_samples: int = 5,
) -> None:
    """Render sample images with bounding boxes overlaid."""
    import cv2

    output_dir.mkdir(parents=True, exist_ok=True)
    image_files = list(images_dir.glob("*.jpg"))[:num_samples]
    colors = [
        (255, 0, 0),      # crazing - blue
        (0, 255, 0),      # inclusion - green
        (0, 0, 255),      # patches - red
        (255, 0, 255),    # pitted_surface - magenta
        (255, 255, 0),    # rolled-in_scale - cyan
        (0, 255, 255),    # scratches - yellow
    ]

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]

        label_path = labels_dir / (img_path.stem + ".txt")
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    class_id, xc, yc, bw, bh = map(float, parts)
                    class_id = int(class_id)

                    x_center = xc * w
                    y_center = yc * h
                    box_w = bw * w
                    box_h = bh * h
                    x1 = int(x_center - box_w / 2)
                    y1 = int(y_center - box_h / 2)
                    x2 = int(x_center + box_w / 2)
                    y2 = int(y_center + box_h / 2)

                    color = colors[class_id % len(colors)]
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        img, CLASS_NAMES[class_id], (x1, max(y1 - 5, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
                    )

        out_path = output_dir / f"sample_{img_path.name}"
        cv2.imwrite(str(out_path), img)
        logger.info(f"Saved sample: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Prepare NEU-DET for YOLO training")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/neu_det/NEU-DET-Steel-Surface-Defect-Detection-master/NEU-DET-Steel-Surface-Defect-Detection-master"),
        help="Raw dataset directory",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/neu_det"),
        help="Output directory for processed data",
    )
    parser.add_argument(
        "--split-ratios",
        type=float,
        nargs=3,
        default=[0.7, 0.15, 0.15],
        help="Train/val/test split ratios",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for splitting",
    )
    parser.add_argument(
        "--render-samples",
        type=int,
        default=5,
        help="Number of sample images to render",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing processed directory",
    )
    args = parser.parse_args()

    set_seed(args.seed)

    raw_dir = args.raw_dir.resolve()
    processed_dir = args.processed_dir.resolve()

    if not raw_dir.exists():
        logger.error(f"Raw directory not found: {raw_dir}. Run download_dataset.py first.")
        sys.exit(1)

    images_raw = raw_dir / "IMAGES"
    annotations_raw = raw_dir / "ANNOTATIONS"

    if not images_raw.exists() or not annotations_raw.exists():
        logger.error(f"Expected IMAGES/ and ANNOTATIONS/ in {raw_dir}")
        sys.exit(1)

    if args.force and processed_dir.exists():
        shutil.rmtree(processed_dir)

    images_out = processed_dir / "images"
    labels_out = processed_dir / "labels"

    for split in ["train", "val", "test"]:
        (images_out / split).mkdir(parents=True, exist_ok=True)
        (labels_out / split).mkdir(parents=True, exist_ok=True)

    all_images = sorted(images_raw.glob("*.jpg"))
    filenames = [f.name for f in all_images]
    logger.info(f"Found {len(filenames)} images")

    splits = split_filenames(filenames, args.split_ratios, args.seed)
    for split_name, split_files in splits.items():
        logger.info(f"  {split_name}: {len(split_files)} images")

    total_objects = 0
    class_counts = {name: 0 for name in CLASS_NAMES}

    for split_name, split_files in splits.items():
        img_split_dir = images_out / split_name
        lbl_split_dir = labels_out / split_name

        copy_images(split_files, images_raw, img_split_dir)

        for fname in split_files:
            xml_path = annotations_raw / (Path(fname).stem + ".xml")
            if not xml_path.exists():
                logger.warning(f"Missing annotation for {fname}")
                continue

            objects = parse_voc_xml(xml_path)
            total_objects += len(objects)
            for obj in objects:
                class_counts[CLASS_NAMES[obj["class_id"]]] += 1

            label_path = lbl_split_dir / (Path(fname).stem + ".txt")
            write_yolo_label(objects, label_path)

    logger.info(f"Total objects: {total_objects}")
    for name, count in class_counts.items():
        logger.info(f"  {name}: {count}")

    generate_yaml_config(processed_dir, CLASS_NAMES, args.split_ratios, args.seed)

    if args.render_samples > 0:
        render_dir = Path("reports") / "dataset_samples"
        render_sample_image(
            images_out / "train",
            labels_out / "train",
            render_dir,
            args.render_samples,
        )

    logger.info(f"Dataset preparation complete. Output: {processed_dir}")


if __name__ == "__main__":
    main()