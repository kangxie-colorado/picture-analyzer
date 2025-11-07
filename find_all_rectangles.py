#!/usr/bin/env python3
"""
Find all colored rectangles by scanning for the 4 edges of each
"""
from PIL import Image

img = Image.open('screenshots/abase-risk-anal-11041203.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def color_match(c1, c2, tol=30):
    """Check if two colors match within tolerance"""
    return all(abs(a - b) <= tol for a, b in zip(c1[:3], c2))

# Target colors
COLORS = {
    'green': (0, 255, 0),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'red': (255, 0, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'orange': (255, 165, 0),
}

def find_rectangle_at(img, start_x, start_y, color_rgb, visited):
    """
    Given a starting point of a colored pixel, trace the full rectangle
    """
    # Skip if already visited
    if (start_x, start_y) in visited:
        return None

    # Trace right to find right edge
    x = start_x
    while x < width and color_match(img.getpixel((x, start_y)), color_rgb):
        x += 1
    right_edge = x - 1

    # Trace down to find bottom edge
    y = start_y
    while y < height and color_match(img.getpixel((start_x, y)), color_rgb):
        y += 1
    bottom_edge = y - 1

    # Verify this forms a rectangle by checking if right edge extends down
    # and bottom edge extends right
    if right_edge > start_x + 10 and bottom_edge > start_y + 10:
        # Mark as visited
        for py in range(start_y, min(start_y + 5, bottom_edge + 1)):
            for px in range(start_x, min(start_x + 5, right_edge + 1)):
                visited.add((px, py))

        return {
            'x': start_x,
            'y': start_y,
            'width': right_edge - start_x + 1,
            'height': bottom_edge - start_y + 1
        }

    return None

# Scan for rectangles
rectangles = []
visited = set()

print("Scanning for colored rectangles...")
print("=" * 70)

for color_name, color_rgb in COLORS.items():
    print(f"\nScanning for {color_name} rectangles...")

    # Scan the image at intervals
    for y in range(0, height, 10):
        for x in range(0, width, 10):
            if (x, y) in visited:
                continue

            pixel = img.getpixel((x, y))
            if color_match(pixel, color_rgb):
                rect = find_rectangle_at(img, x, y, color_rgb, visited)
                if rect and rect['width'] > 500 and rect['height'] > 100:
                    rect['color'] = color_name
                    rectangles.append(rect)
                    print(f"  Found: x={rect['x']:4d}, y={rect['y']:4d}, w={rect['width']:4d}, h={rect['height']:4d}")

print(f"\n{'=' * 70}")
print(f"Total rectangles found: {len(rectangles)}")
print("=" * 70)

# Sort by y then x
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\nAll rectangles (sorted by position):")
for i, rect in enumerate(rectangles, 1):
    print(f"{i:2d}. {rect['color']:8s}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")
