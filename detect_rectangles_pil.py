#!/usr/bin/env python3
"""
Automatically detect colored rectangle boundaries using PIL only
"""
from PIL import Image

# Load the image
img = Image.open('screenshots/abase-risk-anal-11041203.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}")

# Define colors to detect (RGB values)
colors = {
    'green': (0, 255, 0),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'red': (255, 0, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
}

def color_distance(c1, c2):
    """Calculate color distance"""
    return sum(abs(a - b) for a, b in zip(c1, c2))

def find_horizontal_colored_lines(img, tolerance=30):
    """
    Scan for horizontal colored lines
    """
    lines = []

    # Scan every 5th row for speed
    for y in range(0, height, 5):
        x = 0
        while x < width:
            pixel = img.getpixel((x, y))[:3]  # Get RGB, ignore alpha if present

            # Check if this matches any target color
            for color_name, color_rgb in colors.items():
                if color_distance(pixel, color_rgb) <= tolerance:
                    # Found colored pixel - trace the line
                    start_x = x
                    while x < width - 1:
                        px = img.getpixel((x, y))[:3]
                        if color_distance(px, color_rgb) <= tolerance:
                            x += 1
                        else:
                            break

                    line_length = x - start_x
                    if line_length > 500:  # Significant line
                        lines.append({
                            'color': color_name,
                            'y': y,
                            'x_start': start_x,
                            'x_end': x - 1,
                            'length': line_length
                        })
                        print(f"{color_name:8s} horizontal line at y={y:4d}, x={start_x:4d}..{x-1:4d} (length={line_length})")
                    break
            x += 1

    return lines

def find_vertical_colored_lines(img, tolerance=30):
    """
    Scan for vertical colored lines
    """
    lines = []

    # Scan every 5th column for speed
    for x in range(0, width, 5):
        y = 0
        while y < height:
            pixel = img.getpixel((x, y))[:3]

            # Check if this matches any target color
            for color_name, color_rgb in colors.items():
                if color_distance(pixel, color_rgb) <= tolerance:
                    # Found colored pixel - trace the line
                    start_y = y
                    while y < height - 1:
                        px = img.getpixel((x, y))[:3]
                        if color_distance(px, color_rgb) <= tolerance:
                            y += 1
                        else:
                            break

                    line_length = y - start_y
                    if line_length > 100:  # Significant line
                        lines.append({
                            'color': color_name,
                            'x': x,
                            'y_start': start_y,
                            'y_end': y - 1,
                            'length': line_length
                        })
                        print(f"{color_name:8s} vertical line at x={x:4d}, y={start_y:4d}..{y-1:4d} (length={line_length})")
                    break
            y += 1

    return lines

# Run the detection
print("\nScanning for horizontal colored lines...")
print("=" * 70)
h_lines = find_horizontal_colored_lines(img)

print(f"\nFound {len(h_lines)} horizontal colored lines")

print("\nScanning for vertical colored lines...")
print("=" * 70)
v_lines = find_vertical_colored_lines(img)

print(f"\nFound {len(v_lines)} vertical colored lines")

# Group lines into rectangles
print("\nGrouping into rectangles...")
print("=" * 70)

def find_rectangles(h_lines, v_lines):
    """Group horizontal and vertical lines into rectangles"""
    rectangles = []

    # Group horizontal lines by color and approximate position
    for color in colors.keys():
        color_h_lines = [l for l in h_lines if l['color'] == color]
        color_v_lines = [l for l in v_lines if l['color'] == color]

        # Sort by y-coordinate
        color_h_lines.sort(key=lambda l: l['y'])
        color_v_lines.sort(key=lambda l: l['x'])

        # Try to find pairs of horizontal lines (top and bottom)
        for i in range(0, len(color_h_lines) - 1, 2):
            top_line = color_h_lines[i]
            bottom_line = color_h_lines[i + 1]

            # Check if they form a rectangle (similar x range)
            if abs(top_line['x_start'] - bottom_line['x_start']) < 50:
                rect = {
                    'color': color,
                    'x': top_line['x_start'],
                    'y': top_line['y'],
                    'width': top_line['length'],
                    'height': bottom_line['y'] - top_line['y']
                }
                rectangles.append(rect)
                print(f"{color:8s} rectangle: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

    return rectangles

rectangles = find_rectangles(h_lines, v_lines)
print(f"\nTotal rectangles found: {len(rectangles)}")
