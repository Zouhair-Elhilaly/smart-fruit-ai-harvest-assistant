"""Image preprocessing utilities for model inference."""

from typing import Union

import torch
from PIL import Image
from torchvision import transforms


IMAGE_SIZE = (224, 224)

preprocess_transform = transforms.Compose(
    [
        transforms.Resize(IMAGE_SIZE),
        # ToTensor converts HWC images to CHW tensors and scales pixels to [0, 1].
        transforms.ToTensor(),
    ]
)


def preprocess_image(image: Union[Image.Image, str]) -> torch.Tensor:
    """
    Resize, normalize, and batch an input image.

    Steps:
        1. Convert image to RGB.
        2. Resize to 224x224.
        3. Divide pixel values by 255 using transforms.ToTensor().
        4. Expand dimensions from [C, H, W] to [1, C, H, W].
    """
    if isinstance(image, str):
        image = Image.open(image)

    if not isinstance(image, Image.Image):
        raise TypeError("Input must be a PIL image or a valid image path.")

    image = image.convert("RGB")
    image_tensor = preprocess_transform(image)
    return image_tensor.unsqueeze(0)
