#!/usr/bin/env python3
"""
Detect TCE panels - adjusted for vertical separator in middle
"""
from PIL import Image

img = Image.open('screenshots/tce_panels_filled_4colors_taller.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def is_colored(pixel):
    """Check if pixel is a colored block"""
    rgb = pixel[:3]
    return sum(rgb) >= 100  # Must have some brightness

def get_color_at(x, y):
    """Get color at position"""
    return img.getpixel((x, y))[:3]

# Strategy: Look for colored rectangles by scanning specific positions
# We know there are likely 2 columns and 2 rows

print("Scanning for colored rectangles...")
print("=" * 70)

# Scan horizontally at 1/4 width to find left column rectangles
x_left = width // 4
rectangles = []

# Find top rectangle in left column
print(f"\nScanning left column at x={x_left}...")
for y in range(50, height, 10):
    pixel = get_color_at(x_left, y)
    if is_colored(pixel):
        # Found start of a colored region
        y_start = y
        # Find where this color ends
        current_color = pixel
        y_end = y
        for y2 in range(y + 1, height):
            px = get_color_at(x_left, y2)
            if not is_colored(px) or sum(abs(px[i] - current_color[i]) for i in range(3)) > 50:
                y_end = y2 - 1
                break
        else:
            y_end = height - 1

        if y_end - y_start > 100:  # Significant height
            # Now find horizontal extent
            x_start = x_left
            # Scan left to find start
            for x2 in range(x_left, 0, -1):
                px = get_color_at(x2, (y_start + y_end) // 2)
                if not is_colored(px):
                    x_start = x2 + 1
                    break
            else:
                x_start = 0

            # Scan right to find end (stop at middle separator)
            x_end = x_left
            for x2 in range(x_left, width // 2):
                px = get_color_at(x2, (y_start + y_end) // 2)
                if not is_colored(px):
                    x_end = x2 - 1
                    break
            else:
                x_end = width // 2

            rect = {
                'x': x_start,
                'y': y_start,
                'width': x_end - x_start + 1,
                'height': y_end - y_start + 1,
                'color': current_color
            }
            rectangles.append(rect)
            print(f"  Found: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}, color=RGB{rect['color']}")

            # Jump past this rectangle
            y = y_end + 10

# Scan horizontally at 3/4 width to find right column rectangles
x_right = 3 * width // 4
print(f"\nScanning right column at x={x_right}...")
for y in range(50, height, 10):
    pixel = get_color_at(x_right, y)
    if is_colored(pixel):
        # Found start of a colored region
        y_start = y
        # Find where this color ends
        current_color = pixel
        y_end = y
        for y2 in range(y + 1, height):
            px = get_color_at(x_right, y2)
            if not is_colored(px) or sum(abs(px[i] - current_color[i]) for i in range(3)) > 50:
                y_end = y2 - 1
                break
        else:
            y_end = height - 1

        if y_end - y_start > 100:  # Significant height
            # Now find horizontal extent
            # Scan left to find start (from middle separator)
            x_start = x_right
            for x2 in range(x_right, width // 2, -1):
                px = get_color_at(x2, (y_start + y_end) // 2)
                if not is_colored(px):
                    x_start = x2 + 1
                    break
            else:
                x_start = width // 2

            # Scan right to find end
            x_end = x_right
            for x2 in range(x_right, width):
                px = get_color_at(x2, (y_start + y_end) // 2)
                if not is_colored(px):
                    x_end = x2 - 1
                    break
            else:
                x_end = width - 1

            rect = {
                'x': x_start,
                'y': y_start,
                'width': x_end - x_start + 1,
                'height': y_end - y_start + 1,
                'color': current_color
            }
            rectangles.append(rect)
            print(f"  Found: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}, color=RGB{rect['color']}")

            # Jump past this rectangle
            y = y_end + 10

# Sort by position
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\n" + "=" * 70)
print(f"Total rectangles detected: {len(rectangles)}")
print("=" * 70)

# Generate YAML
panel_ids = ['panel-1-left', 'panel-1-right', 'panel-2-left', 'panel-2-right']

print("\nFinal coordinates:\n")
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        print(f"{panel_ids[i]:20s}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

print("\n" + "=" * 70)
print("YAML format:")
print("=" * 70)
print()
print(f"dashboard: tce-resource-overview")
print(f"version: '1.0'")
print(f"image_dimensions:")
print(f"  width: {width}")
print(f"  height: {height}")
print()
print("panels:")
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        print(f"  {panel_ids[i]}:")
        print(f"    x: {rect['x']}")
        print(f"    y: {rect['y']}")
        print(f"    width: {rect['width']}")
        print(f"    height: {rect['height']}")
        print()
