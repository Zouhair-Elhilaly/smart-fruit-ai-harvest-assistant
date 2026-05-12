"""BLIP image captioning via the Hugging Face InferenceClient (2025/2026 compatible)."""
from __future__ import annotations

import os
from io import BytesIO

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from PIL import Image

load_dotenv()

DEFAULT_BLIP_MODEL_ID = "Salesforce/blip-image-captioning-base"
# Fallback model if the default is not available via hf-inference
FALLBACK_BLIP_MODEL_ID = "nlpconnect/vit-gpt2-image-captioning"


class BLIPCaptionError(RuntimeError):
    """Raised when BLIP caption generation cannot be completed."""


def _get_huggingface_token() -> str:
    token = (
        os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HF_API_TOKEN")
        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        or ""
    ).strip()
    if not token:
        raise BLIPCaptionError(
            "Hugging Face API token is not set. Add HUGGINGFACE_API_KEY or "
            "HF_API_TOKEN to your .env file."
        )
    return token


def caption_image(image: Image.Image, timeout: int = 45) -> str:
    """Return a BLIP caption for a PIL image using the HF InferenceClient."""
    token = _get_huggingface_token()
    model_id = os.getenv("BLIP_MODEL_ID", DEFAULT_BLIP_MODEL_ID).strip()

    # Convert PIL image to bytes (InferenceClient accepts bytes or PIL directly)
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=90)
    image_bytes = buffer.getvalue()

    # Use the official InferenceClient — it targets router.huggingface.co automatically
    client = InferenceClient(
        provider="hf-inference",   # routes to router.huggingface.co/hf-inference
        api_key=token,
        timeout=timeout,
    )

    try:
        result = client.image_to_text(image_bytes, model=model_id)
    except Exception as exc:
        # Try fallback model before giving up
        if model_id != FALLBACK_BLIP_MODEL_ID:
            try:
                result = client.image_to_text(image_bytes, model=FALLBACK_BLIP_MODEL_ID)
            except Exception as exc2:
                raise BLIPCaptionError(
                    f"Both models failed. Primary: {exc} | Fallback: {exc2}"
                ) from exc2
        else:
            raise BLIPCaptionError(f"Hugging Face BLIP request failed: {exc}") from exc

    # result is an ImageToTextOutput object; .generated_text holds the caption
    caption = (result.generated_text or "").strip()
    if not caption:
        raise BLIPCaptionError("Hugging Face BLIP did not return a caption.")
    return caption