"""
Calibrate energy-based OOD threshold and save it to .env

energy(x) = -logsumexp(logits)
threshold = percentile of validation energies
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch
from dotenv import load_dotenv
from PIL import Image
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T


# ---------------- PROJECT ROOT ----------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------- LOAD YOUR MODEL ----------------
from src.load_model import load_model
from src.ood import energy_score_from_logits


# ---------------- ENV ----------------
load_dotenv(PROJECT_ROOT / ".env")


VAL_DIR = os.getenv("OOD_VAL_DIR", "")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))

MEAN = eval(os.getenv("MEAN", "[0.485, 0.456, 0.406]"))
STD = eval(os.getenv("STD", "[0.229, 0.224, 0.225]"))
IMG_SIZE = int(os.getenv("IMG_SIZE", "224"))


# ---------------- TRANSFORM (same as training) ----------------
val_test_transforms = T.Compose([
    T.Resize((256, 256)),
    T.CenterCrop(IMG_SIZE),
    T.ToTensor(),
    T.Normalize(mean=MEAN, std=STD),
])


# ---------------- DATASET ----------------
class ImageFolderDataset(Dataset):
    def __init__(self, root: str, transform=None):
        self.root = Path(root)
        self.transform = transform

        self.images = [
            p for p in self.root.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]

        if len(self.images) == 0:
            raise ValueError(f"No images found in {root}")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        img = Image.open(img_path).convert("RGB")

        if self.transform:
            img = self.transform(img)

        return img


# ---------------- SAVE TO .ENV ----------------
def save_to_env(env_path: Path, key: str, value: str) -> None:
    lines = []

    if env_path.exists():
        lines = env_path.read_text().splitlines()

    updated = False
    new_lines = []

    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n")


# ---------------- ENERGY COMPUTATION ----------------
@torch.inference_mode()
def compute_energies(model, loader, device):
    model.eval()
    energies = []

    for i, batch in enumerate(loader):
        batch = batch.to(device)

        logits = model(batch)
        energy = energy_score_from_logits(logits)

        energies.extend(energy.cpu().numpy())

        print(f"[INFO] Batch {i+1}/{len(loader)} processed")

    return np.array(energies)


# ---------------- ARGUMENTS ----------------
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val-dir", type=str, default=VAL_DIR)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--percentile", type=float, default=95.0)
    return parser.parse_args()


# ---------------- MAIN ----------------
def main():
    args = parse_args()

    if not args.val_dir:
        raise ValueError("OOD_VAL_DIR is not set in .env")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"[INFO] Device: {device}")

    # ---------------- LOAD MODEL ----------------
    model, _, _ = load_model()
    model = model.to(device)

    # ---------------- DATASET ----------------
    dataset = ImageFolderDataset(args.val_dir, transform=val_test_transforms)

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    print(f"[INFO] Validation images: {len(dataset)}")

    # ---------------- ENERGY SCORES ----------------
    energies = compute_energies(model, loader, device)

    # ---------------- THRESHOLD ----------------
    threshold = float(np.percentile(energies, args.percentile))

    print("\n========== RESULTS ==========")
    print(f"Min energy   : {energies.min():.6f}")
    print(f"Mean energy  : {energies.mean():.6f}")
    print(f"Max energy   : {energies.max():.6f}")
    print(f"Threshold ({args.percentile}th percentile): {threshold:.6f}")

    # ---------------- SAVE TO .ENV ----------------
    env_path = PROJECT_ROOT / ".env"

    save_to_env(env_path, "OOD_THRESHOLD", f"{threshold:.6f}")
    save_to_env(env_path, "OOD_THRESHOLD_PERCENTILE", str(args.percentile))

    print(f"\n[INFO] Saved threshold to {env_path}")


if __name__ == "__main__":
    main()