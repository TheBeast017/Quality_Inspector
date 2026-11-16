#!/usr/bin/env python
"""
Download NEU-DET dataset.

NEU-DET: 1000 images of 4 steel surface defect classes (crazing, inclusion, patches, pitted).
Source: https://github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection
Paper: "Deep Learning-based Steel Surface Defect Detection" (Wu et al., 2018)

Annotations are Pascal-VOC XML format.
Native resolution: 200x200 pixels.
"""

import argparse
import hashlib
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# Add project root to path so scripts work when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logging import get_logger

logger = get_logger(__name__)

# NEU-DET dataset URLs (from siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection)
DATASET_URLS = {
    "neu_det": {
        "url": "https://github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection/archive/refs/heads/master.zip",
        "filename": "NEU-DET-Steel-Surface-Defect-Detection-master.zip",
        "sha256": None,
        "extract_dir": "NEU-DET-Steel-Surface-Defect-Detection-master",
    }
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, desc: str = "") -> None:
    """Download a file with progress logging."""
    logger.info(f"Downloading {desc} from {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    def reporthook(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            if block_num % 50 == 0:
                logger.debug(f"  {percent}% ({block_num * block_size // 1024} KB / {total_size // 1024} KB)")

    try:
        urlretrieve(url, dest, reporthook)
        logger.info(f"Downloaded to {dest} ({dest.stat().st_size // 1024} KB)")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


def extract_archive(archive_path: Path, extract_to: Path) -> Path:
    """Extract zip or tar.gz archive."""
    logger.info(f"Extracting {archive_path.name} to {extract_to}")
    extract_to.mkdir(parents=True, exist_ok=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_to)
    elif archive_path.suffix in (".tar", ".gz", ".tgz"):
        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

    logger.info("Extraction complete")
    return extract_to


def verify_structure(raw_dir: Path) -> bool:
    """Verify the extracted dataset has expected structure."""
    images_dir = raw_dir / "IMAGES"
    annotations_dir = raw_dir / "ANNOTATIONS"

    if not images_dir.exists():
        logger.error(f"Missing IMAGES directory: {images_dir}")
        return False
    if not annotations_dir.exists():
        logger.error(f"Missing ANNOTATIONS directory: {annotations_dir}")
        return False

    img_count = len(list(images_dir.glob("*.jpg")))
    ann_count = len(list(annotations_dir.glob("*.xml")))

    logger.info(f"Found {img_count} images, {ann_count} annotations")

    if img_count != 1000:
        logger.warning(f"Expected 1000 images, got {img_count}")
    if ann_count != 1000:
        logger.warning(f"Expected 1000 annotations, got {ann_count}")

    return img_count > 0 and ann_count > 0


def main():
    parser = argparse.ArgumentParser(description="Download NEU-DET dataset")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/neu_det"),
        help="Directory to store raw dataset (default: data/raw/neu_det)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if dataset exists",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing dataset structure",
    )
    args = parser.parse_args()

    raw_dir = args.raw_dir.resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)

    if args.verify_only:
        if verify_structure(raw_dir):
            logger.info("Dataset structure verified OK")
            sys.exit(0)
        else:
            logger.error("Dataset structure verification failed")
            sys.exit(1)

    dataset_info = DATASET_URLS["neu_det"]
    archive_path = raw_dir / dataset_info["filename"]
    extract_dir = raw_dir / dataset_info["extract_dir"]

    if not args.force and extract_dir.exists() and verify_structure(extract_dir):
        logger.info("Dataset already exists and structure is valid. Use --force to re-download.")
        return

    download_file(dataset_info["url"], archive_path, "NEU-DET")

    if dataset_info["sha256"]:
        actual = compute_sha256(archive_path)
        if actual != dataset_info["sha256"]:
            logger.error(f"Checksum mismatch! Expected {dataset_info['sha256']}, got {actual}")
            sys.exit(1)
        logger.info("Checksum verified")
    else:
        actual = compute_sha256(archive_path)
        logger.info(f"SHA256 (record for future): {actual}")

    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_archive(archive_path, extract_dir)

    # The archive extracts with a nested directory structure:
    # NEU-DET-Steel-Surface-Defect-Detection-master/
    #   NEU-DET-Steel-Surface-Defect-Detection-master/
    #       IMAGES/, ANNOTATIONS/, etc.
    # Find the actual dataset directory
    inner_dirs = list(extract_dir.iterdir())
    actual_extract_dir = extract_dir
    if len(inner_dirs) == 1 and inner_dirs[0].is_dir() and (inner_dirs[0] / "IMAGES").exists():
        actual_extract_dir = inner_dirs[0]
        logger.info(f"Found nested dataset directory: {actual_extract_dir}")

    if not verify_structure(actual_extract_dir):
        logger.error("Extracted dataset structure is invalid")
        sys.exit(1)

    logger.info(f"NEU-DET dataset ready at {actual_extract_dir}")


if __name__ == "__main__":
    main()