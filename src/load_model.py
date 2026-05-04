"""Utilities for loading the trained PyTorch image classification model."""

from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn as nn
from torchvision import models


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "checkpoints" / "best_model.pth"

# Keep this order aligned with the order used during training.
# PyTorch ImageFolder usually sorts class folders alphabetically.
DEFAULT_CLASS_NAMES = ["overripe", "ripe", "unripe"]


def _get_device() -> torch.device:
    """Return the best available device for inference."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_checkpoint(model_path: Path):
    """Load a checkpoint while staying compatible with multiple PyTorch versions."""
    try:
        return torch.load(model_path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(model_path, map_location="cpu")


def _extract_state_dict(checkpoint):
    """Support common checkpoint formats: full module, wrapped dict, or raw state dict."""
    if isinstance(checkpoint, nn.Module):
        return checkpoint, None

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        return checkpoint["model_state_dict"], checkpoint

    if isinstance(checkpoint, dict):
        return checkpoint, None

    raise ValueError("Unsupported model checkpoint format.")


def _build_resnet50(num_classes: int, state_dict: dict) -> nn.Module:
    """Create the ResNet50 architecture expected by the saved checkpoint."""
    model = models.resnet50(weights=None)
    in_features = model.fc.in_features

    if "fc.1.weight" in state_dict:
        model.fc = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, num_classes),
        )
    else:
        model.fc = nn.Linear(in_features, num_classes)

    return model


def load_model(
    model_path: Path = MODEL_PATH,
    class_names: List[str] = None,
) -> Tuple[nn.Module, List[str], torch.device]:
    """
    Load the trained model from models/model.pth.

    Returns:
        A tuple containing the PyTorch model, class names, and inference device.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at '{model_path}'. "
            "Place your trained PyTorch checkpoint at models/model.pth."
        )

    checkpoint = _load_checkpoint(model_path)
    loaded_object, metadata = _extract_state_dict(checkpoint)

    if isinstance(loaded_object, nn.Module):
        model = loaded_object
        final_class_names = class_names or DEFAULT_CLASS_NAMES
    else:
        final_class_names = (
            class_names
            or (metadata or {}).get("class_names")
            or DEFAULT_CLASS_NAMES
        )
        model = _build_resnet50(num_classes=len(final_class_names), state_dict=loaded_object)
        model.load_state_dict(loaded_object)

    device = _get_device()
    model.to(device)
    model.eval()

    return model, final_class_names, device
