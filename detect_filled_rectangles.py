#!/usr/bin/env python3
"""
Detect filled rectangle coordinates from the filled blocks image
"""
from PIL import Image
from collections import defaultdict

# Load the filled blocks image
img = Image.open('screenshots/abase-risk-anal-11041203_filled_v5.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def get_unique_colors(img, sample_interval=50):
    """Sample the image to find unique colors"""
    colors = set()
    for y in range(0, height, sample_interval):
        for x in range(0, width, sample_interval):
            pixel = img.getpixel((x, y))
            colors.add(pixel[:3] if len(pixel) >= 3 else pixel)
    return colors

def find_rectangle_bounds(img, target_color, tolerance=10):
    """Find the bounding box of all pixels matching the target color"""
    min_x, max_x = width, 0
    min_y, max_y = height, 0
    found = False

    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))[:3]

            # Check if pixel matches target color
            if all(abs(pixel[i] - target_color[i]) <= tolerance for i in range(3)):
                found = True
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if found and (max_x - min_x > 100) and (max_y - min_y > 100):
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x + 1,
            'height': max_y - min_y + 1
        }
    return None

# Get unique colors
print("Sampling unique colors...")
colors = get_unique_colors(img)
print(f"Found {len(colors)} unique color regions\n")

# Filter out very dark colors (likely background) and very similar colors
filtered_colors = []
for color in colors:
    # Skip very dark colors (background)
    if sum(color) < 50:
        continue
    # Skip if too similar to existing colors
    is_unique = True
    for existing in filtered_colors:
        if all(abs(color[i] - existing[i]) < 30 for i in range(3)):
            is_unique = False
            break
    if is_unique:
        filtered_colors.append(color)

print(f"Analyzing {len(filtered_colors)} distinct colored regions...")
print("=" * 70)

# Detect rectangles for each color
rectangles = []
for color in sorted(filtered_colors, key=lambda c: (c[1], c[0], c[2])):  # Sort by color
    print(f"\nScanning for color RGB{color}...")
    rect = find_rectangle_bounds(img, color)
    if rect:
        rect['color_rgb'] = color
        rectangles.append(rect)
        print(f"  Found rectangle: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

# Sort rectangles by position (top to bottom, left to right)
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\n" + "=" * 70)
print(f"Total rectangles detected: {len(rectangles)}")
print("=" * 70)

# Assign panel IDs based on position
panel_ids = [
    'S1-L-read', 'S1-R-read',
    'S1-L-write', 'S1-R-write',
    'S2-L-disk', 'S2-R-partition',
    'S3-L-qps_vs_quota', 'S3-R-hotkey',
    'S3-L2-value_size'
]

print("\nDetected coordinates:\n")
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        panel_id = panel_ids[i]
        print(f"{panel_id:20s}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")
    else:
        print(f"Unknown panel {i+1:2d}     : x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

# Generate YAML output
print("\n" + "=" * 70)
print("YAML format for coordinates.yaml:")
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
