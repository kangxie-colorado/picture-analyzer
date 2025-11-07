#!/usr/bin/env python3
"""
Improved filled rectangle detection using flood fill approach
"""
from PIL import Image

img = Image.open('screenshots/abase-risk-anal-11041203_filled_v5.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def flood_fill_bounds(img, start_x, start_y, target_color, visited, tolerance=10):
    """Use flood fill to find the bounds of a colored region"""
    stack = [(start_x, start_y)]
    min_x, max_x = start_x, start_x
    min_y, max_y = start_y, start_y
    pixel_count = 0

    while stack:
        x, y = stack.pop()

        # Skip if out of bounds or already visited
        if x < 0 or x >= width or y < 0 or y >= height:
            continue
        if (x, y) in visited:
            continue

        # Check if pixel matches target color
        pixel = img.getpixel((x, y))[:3]
        if not all(abs(pixel[i] - target_color[i]) <= tolerance for i in range(3)):
            continue

        # Mark as visited and update bounds
        visited.add((x, y))
        pixel_count += 1
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

        # Add neighbors to stack (check every 5 pixels for speed)
        for dx, dy in [(5, 0), (-5, 0), (0, 5), (0, -5)]:
            stack.append((x + dx, y + dy))

    if pixel_count > 10000:  # Significant region
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x + 1,
            'height': max_y - min_y + 1,
            'pixel_count': pixel_count
        }
    return None

# Scan for filled regions
print("Scanning for filled colored regions...")
print("=" * 70)

rectangles = []
visited_global = set()

# Scan at regular intervals to find starting points of each colored region
for y in range(100, height, 50):  # Start from y=100 to skip header
    for x in range(50, width, 50):
        if (x, y) in visited_global:
            continue

        pixel = img.getpixel((x, y))[:3]

        # Skip very dark pixels (background) - sum of RGB < 100
        if sum(pixel) < 100:
            continue

        # Skip very light pixels (might be text/UI)
        if sum(pixel) > 650:
            continue

        # Try flood fill from this point
        rect = flood_fill_bounds(img, x, y, pixel, visited_global)
        if rect and rect['width'] > 300 and rect['height'] > 100:
            rect['color_rgb'] = pixel
            rectangles.append(rect)
            print(f"Found region RGB{pixel}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}, pixels={rect['pixel_count']}")

# Sort by position (top to bottom, left to right)
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\n" + "=" * 70)
print(f"Total rectangles detected: {len(rectangles)}")
print("=" * 70)

# Map to panel IDs
panel_ids = [
    'S1-L-read', 'S1-R-read',
    'S1-L-write', 'S1-R-write',
    'S2-L-disk', 'S2-R-partition',
    'S3-L-qps_vs_quota', 'S3-R-hotkey',
    'S3-L2-value_size'
]

print("\nDetected panel coordinates:\n")
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        panel_id = panel_ids[i]
        print(f"{panel_id:20s}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

# Generate YAML
print("\n" + "=" * 70)
print("YAML coordinates:")
print("=" * 70)
print()
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        panel_id = panel_ids[i]
        print(f"  {panel_id}:")
        print(f"    x: {rect['x']}")
        print(f"    y: {rect['y']}")
        print(f"    width: {rect['width']}")
        print(f"    height: {rect['height']}")
        print()
