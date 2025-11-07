#!/usr/bin/env python3
"""
Debug: check what pixels look like in the TCE image
"""
from PIL import Image

img = Image.open('screenshots/tce_panels_filled_4colors_taller.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

# Sample pixels at various positions
print("Sampling pixels at various positions:")
print("=" * 70)

positions = [
    (100, 100, "Top-left area"),
    (width // 4, height // 4, "1/4 width, 1/4 height"),
    (width // 2, height // 4, "Mid width, 1/4 height"),
    (3 * width // 4, height // 4, "3/4 width, 1/4 height"),
    (width // 4, 3 * height // 4, "1/4 width, 3/4 height"),
    (width // 2, 3 * height // 4, "Mid width, 3/4 height"),
    (3 * width // 4, 3 * height // 4, "3/4 width, 3/4 height"),
]

for x, y, label in positions:
    pixel = img.getpixel((x, y))
    print(f"{label:30s} ({x:4d}, {y:3d}): RGB{pixel[:3]}, sum={sum(pixel[:3])}")

# Sample a vertical line in the middle
print("\n" + "=" * 70)
print("Vertical scan at x=width//2:")
print("=" * 70)
for y in range(50, min(height, 800), 50):
    pixel = img.getpixel((width // 2, y))[:3]
    print(f"y={y:3d}: RGB{pixel}, sum={sum(pixel)}")
