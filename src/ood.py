"""Energy-based out-of-distribution detection for classifier logits."""

from __future__ import annotations

import os
from typing import Optional

import torch
from dotenv import load_dotenv


load_dotenv()

UNKNOWN_LABEL = "Model confidence is outside the valid fruit distribution! Try again with a different image.😊"


def energy_score_from_logits(logits: torch.Tensor) -> torch.Tensor:
    """
    Compute energy scores from raw model logits.

    Energy is defined as:
        energy(x) = -logsumexp(logits)

    Higher energy means the sample is less compatible with the known
    in-distribution classes.
    """
    if logits.ndim == 1:
        logits = logits.unsqueeze(0)
    return -torch.logsumexp(logits, dim=1)


def load_ood_threshold(default: Optional[float] = None) -> Optional[float]:
    """Load the calibrated OOD threshold from environment variables."""
    value = (os.getenv("OOD_THRESHOLD") or "").strip()
    if not value:
        return default

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"OOD_THRESHOLD must be numeric, got {value!r}.") from exc


def classify_ood(
    energy_score: float,
    threshold: Optional[float] = None,
) -> dict[str, object]:
    """
    Apply the threshold decision rule.

    If energy_score > threshold, the image is treated as unknown/not fruit.
    When no threshold is configured, OOD detection is reported as disabled.
    """
    resolved_threshold = load_ood_threshold() if threshold is None else threshold
    enabled = resolved_threshold is not None
    is_ood = bool(enabled and energy_score > float(resolved_threshold))

    return {
        "energy_score": float(energy_score),
        "ood_threshold": None if resolved_threshold is None else float(resolved_threshold),
        "ood_enabled": enabled,
        "is_ood": is_ood,
    }


def final_prediction_label(class_label: str, is_ood: bool) -> str:
    """Return the user-facing class label after OOD filtering."""
    return UNKNOWN_LABEL if is_ood else class_label
