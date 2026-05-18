"""
Local Image Captioning using BLIP (offline, CPU-friendly)
Better than ViT-GPT2 for real projects
"""

import os

# Local cache (important for offline use)
os.environ["HF_HOME"] = "../models/cache/huggingface/blip"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "300"

from dotenv import load_dotenv

load_dotenv()

import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration


# Custom error
class CaptionError(Exception):
    pass


class LocalImageCaptioner:
    def __init__(self):
        self.model_id = os.getenv("BLIP_MODEL_ID")

        try:
            # Load processor + model
            self.processor = BlipProcessor.from_pretrained(self.model_id)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_id)
        except Exception as e:
            raise CaptionError(f"Model loading failed: {e}")

        # Device (CPU / GPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Generation config (important for quality)
        self.gen_kwargs = {
            "max_length": 40,
            "num_beams": 3
        }

    def caption(self, image: Image.Image) -> str:
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")

            # preprocess image
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            self.model.eval()
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    **self.gen_kwargs
                )

            caption = self.processor.decode(
                output[0],
                skip_special_tokens=True
            )

            return caption.strip()

        except Exception as e:
            raise CaptionError(f"Caption generation failed: {e}")


# Singleton (important for Streamlit / apps)
_captioner = None


def caption_image(image: Image.Image) -> str:
    global _captioner
    if _captioner is None:
        _captioner = LocalImageCaptioner()
    return _captioner.caption(image)


# ---------------- TEST ----------------
if __name__ == "__main__":
    img = Image.open("../assets/overripe.jpg")
    print(caption_image(img))