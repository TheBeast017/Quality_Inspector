"""
Helper utilities for the Industrial AI Inspection project.

Small pure functions used across data, inference, and evaluation modules.
"""

import random
from pathlib import Path
from typing import Optional
import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_device(device: str = "auto") -> torch.device:
    """
    Resolve device string to torch.device.

    Args:
        device: "auto", "cuda", "cpu", or "cuda:N"

    Returns:
        torch.device
    """
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


def resolve_project_path(relative_path: str) -> Path:
    """Resolve a path relative to the project root."""
    project_root = Path(__file__).resolve().parents[3]  # .../Quality_Inspection
    return (project_root / relative_path).resolve()


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_image(image_path: str) -> np.ndarray:
    """
    Load an image as RGB numpy array.

    Args:
        image_path: Path to image file.

    Returns:
        HxWx3 numpy array in RGB order, dtype uint8.
    """
    import cv2
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def save_image(image: np.ndarray, output_path: str) -> None:
    """Save RGB numpy array as image file."""
    import cv2
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), bgr)


def get_class_names(config_name: str = "neu_det") -> list[str]:
    """Get class names from dataset config."""
    from src.utils.config import get_dataset_config
    return get_dataset_config(config_name).get("classes", [])


def format_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"