"""
Configuration loader for the Industrial AI Inspection project.

Loads YAML configs from configs/ and environment variables from .env.
Single entry point for all configuration.
"""

from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv


# Load .env at module import time
load_dotenv()

_CONFIG_CACHE: dict[str, Any] = {}
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # .../Quality_Inspection


def _resolve_path(path_str: str) -> Path:
    """Resolve a path that may contain ${ENV_VAR} placeholders."""
    import os
    # Replace ${VAR} with environment variable
    expanded = os.path.expandvars(path_str)
    return (_PROJECT_ROOT / expanded).resolve()


def load_config(name: str) -> dict:
    """
    Load a YAML config file from configs/.
    Caches results for subsequent calls.
    """
    if name in _CONFIG_CACHE:
        return _CONFIG_CACHE[name]

    config_path = _PROJECT_ROOT / "configs" / f"{name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Recursively resolve ${ENV_VAR} in strings
    def resolve(obj):
        if isinstance(obj, str):
            return os.path.expandvars(obj)
        if isinstance(obj, dict):
            return {k: resolve(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [resolve(v) for v in obj]
        return obj

    import os
    data = resolve(data)
    _CONFIG_CACHE[name] = data
    return data


def get_dataset_config(dataset_name: str = "neu_det") -> dict:
    """Get a specific dataset configuration from dataset.yaml."""
    all_datasets = load_config("dataset")
    if dataset_name not in all_datasets:
        raise KeyError(f"Dataset '{dataset_name}' not found in configs/dataset.yaml")
    return all_datasets[dataset_name]


def get_app_config() -> dict:
    """Get application runtime configuration."""
    return load_config("app")


def get_detection_config() -> dict:
    """Get detection (YOLO) configuration."""
    return load_config("detection")


def get_segmentation_config() -> dict:
    """Get segmentation configuration."""
    return load_config("segmentation")


def get_anomaly_config() -> dict:
    """Get anomaly detection configuration."""
    return load_config("anomaly")


def get_inspection_rules() -> dict:
    """Get PASS/REJECT decision rules."""
    return load_config("inspection_rules")


def clear_cache() -> None:
    """Clear the config cache (useful for tests)."""
    _CONFIG_CACHE.clear()