"""
Local Image Captioning using ViT-GPT2 (no API, fully offline)
"""

from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from PIL import Image


class CaptionError(Exception):
    pass


class LocalImageCaptioner:
    def __init__(self):
        self.model_id = "nlpconnect/vit-gpt2-image-captioning"

        try:
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_id)
            self.processor = ViTImageProcessor.from_pretrained(self.model_id)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        except Exception as e:
            raise CaptionError(f"Model loading failed: {e}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.gen_kwargs = {
            "max_length": 16,
            "num_beams": 4
        }

    def caption(self, image: Image.Image) -> str:
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")

            pixel_values = self.processor(
                images=[image],
                return_tensors="pt"
            ).pixel_values.to(self.device)

            output_ids = self.model.generate(pixel_values, **self.gen_kwargs)

            caption = self.tokenizer.decode(
                output_ids[0],
                skip_special_tokens=True
            )

            return caption.strip()

        except Exception as e:
            raise CaptionError(f"Caption generation failed: {e}")


# singleton (important for Streamlit performance)
_captioner = None

def caption_image(image: Image.Image) -> str:
    global _captioner
    if _captioner is None:
        _captioner = LocalImageCaptioner()
    return _captioner.caption(image)