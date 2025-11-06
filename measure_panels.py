#!/usr/bin/env python3
"""
Interactive tool to help measure panel coordinates precisely
"""
from PIL import Image, ImageDraw
import sys


def visualize_coordinates(image_path: str, coords_dict: dict):
    """Draw rectangles on image to visualize panel boundaries"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    colors = [
        'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
        'orange', 'purple', 'pink'
    ]

    for i, (panel_id, coords) in enumerate(coords_dict.items()):
        x = coords['x']
        y = coords['y']
        w = coords['width']
        h = coords['height']

        color = colors[i % len(colors)]

        # Draw rectangle
        draw.rectangle(
            [x, y, x + w, y + h],
            outline=color,
            width=3
        )

        # Draw label
        draw.text((x + 5, y + 5), panel_id, fill=color)

    output_path = 'outputs/coordinates_visualization.png'
    img.save(output_path)
    print(f"Saved visualization to: {output_path}")


if __name__ == '__main__':
    # Current coordinates
    coords = {
        'S1-L-write': {'x': 27, 'y': 85, 'width': 627, 'height': 156},
        'S1-R-write': {'x': 654, 'y': 85, 'width': 627, 'height': 156},
        'S1-L-read': {'x': 27, 'y': 247, 'width': 627, 'height': 153},
        'S1-R-read': {'x': 654, 'y': 247, 'width': 627, 'height': 153},
        'S2-L-disk': {'x': 27, 'y': 413, 'width': 627, 'height': 175},
        'S2-R-partition': {'x': 654, 'y': 413, 'width': 627, 'height': 175},
        'S3-L-qps_vs_quota': {'x': 27, 'y': 602, 'width': 627, 'height': 160},
        'S3-R-hotkey': {'x': 654, 'y': 602, 'width': 627, 'height': 160},
        'S3-L2-value_size': {'x': 27, 'y': 777, 'width': 1254, 'height': 145},
    }

    image_path = sys.argv[1] if len(sys.argv) > 1 else 'screenshots/abase-risk-anal-11041203.png'
    visualize_coordinates(image_path, coords)
