"""Prediction logic for image classification."""

from typing import Dict, List, Optional

import torch
import torch.nn as nn
from PIL import Image

from src.load_model import load_model
from src.ood import classify_ood, energy_score_from_logits, final_prediction_label
from src.preprocess import preprocess_image


def predict_image(
    image: Image.Image,
    model: Optional[nn.Module] = None,
    class_names: Optional[List[str]] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, object]:
    """
    Predict the class label and confidence score for a single image.

    Args:
        image: PIL image to classify.
        model: Optional loaded PyTorch model. If not provided, it is loaded automatically.
        class_names: Optional class labels. If not provided, labels are loaded with the model.
        device: Optional inference device.

    Returns:
        Dictionary with class_index, class_label, confidence, probabilities,
        logits, energy_score, OOD metadata, and final_label.
    """
    if model is None or class_names is None or device is None:
        model, class_names, device = load_model()

    input_tensor = preprocess_image(image).to(device)

    with torch.inference_mode():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted_index = torch.max(probabilities, dim=1)
        energy = energy_score_from_logits(logits)

    predicted_index_value = int(predicted_index.item())
    confidence_value = float(confidence.item())
    class_label = class_names[predicted_index_value]
    energy_value = float(energy.item())
    ood_result = classify_ood(energy_value)

    return {
        "class_index": predicted_index_value,
        "class_label": class_label,
        "final_label": final_prediction_label(class_label, bool(ood_result["is_ood"])),
        "confidence": confidence_value,
        "probabilities": probabilities.squeeze(0).detach().cpu().tolist(),
        "logits": logits.squeeze(0).detach().cpu().tolist(),
        **ood_result,
    }
