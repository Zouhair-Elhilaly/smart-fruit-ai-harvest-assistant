# import os
# from pathlib import Path

# IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}

# def is_image(file_path):
#     return file_path.suffix.lower() in IMAGE_EXTENSIONS

# def human_readable_size(size_bytes):
#     if size_bytes == 0:
#         return "0 B"
#     units = ["B", "KB", "MB", "GB", "TB"]
#     i = 0
#     while size_bytes >= 1024 and i < len(units) - 1:
#         size_bytes /= 1024
#         i += 1
#     return f"{size_bytes:.2f} {units[i]}"

# def analyze_dataset(dataset_path="dataset"):
#     dataset_dir = Path(dataset_path)
#     if not dataset_dir.exists():
#         print(f"Dataset folder '{dataset_path}' does not exist.")
#         return

#     total_images = 0
#     total_size = 0

#     subset_stats = {}

#     for subset_dir in sorted([d for d in dataset_dir.iterdir() if d.is_dir()]):
#         subset_name = subset_dir.name
#         subset_images = 0
#         subset_size = 0
#         class_stats = {}

#         for class_dir in sorted([d for d in subset_dir.iterdir() if d.is_dir()]):
#             class_name = class_dir.name
#             class_images = 0
#             class_size = 0

#             for img_path in sorted(class_dir.iterdir()):
#                 if img_path.is_file() and is_image(img_path):
#                     size = img_path.stat().st_size
#                     class_images += 1
#                     class_size += size

#             class_stats[class_name] = {"count": class_images, "size": class_size}
#             subset_images += class_images
#             subset_size += class_size

#         subset_stats[subset_name] = {
#             "count": subset_images,
#             "size": subset_size,
#             "classes": class_stats
#         }
#         total_images += subset_images
#         total_size += subset_size

#     print(f"Dataset: {dataset_dir.resolve()}")
#     print(f"Total images: {total_images}")
#     print(f"Total size: {human_readable_size(total_size)}")
#     print()

#     for subset_name, stats in sorted(subset_stats.items()):
#         print(f"{subset_name}:")
#         print(f"  Total images: {stats['count']}")
#         print(f"  Total size: {human_readable_size(stats['size'])}")
#         for class_name, cls in sorted(stats['classes'].items()):
#             print(f"    {class_name}: {cls['count']} images, {human_readable_size(cls['size'])}")
#         print()

# if __name__ == "__main__":
#     analyze_dataset()

import chroma


