#!/usr/bin/env python3
"""
Automatically detect colored rectangle boundaries in dashboard screenshot
"""
from PIL import Image
import numpy as np

# Load the image
img = Image.open('screenshots/abase-risk-anal-11041203.png')
img_array = np.array(img)

height, width, _ = img_array.shape
print(f"Image dimensions: {width}x{height}")

# Define colors to detect (RGB values for the colored rectangles)
colors = {
    'green': (0, 255, 0),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'red': (255, 0, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'orange': (255, 165, 0),
}

def find_colored_rectangles(img_array, tolerance=30):
    """
    Find bounding boxes of colored rectangles in the image
    """
    rectangles = []

    # Scan for horizontal lines (top and bottom edges)
    for y in range(height):
        for x in range(width):
            pixel = img_array[y, x, :3]

            # Check if pixel matches any target color
            for color_name, color_rgb in colors.items():
                diff = np.abs(pixel.astype(int) - np.array(color_rgb))
                if np.all(diff <= tolerance):
                    # Found a colored pixel - trace the rectangle
                    rect = trace_rectangle(img_array, x, y, color_rgb, tolerance)
                    if rect:
                        rectangles.append({
                            'color': color_name,
                            'coords': rect
                        })
                    break

    return rectangles

def trace_rectangle(img_array, start_x, start_y, color, tolerance):
    """
    Trace a rectangle starting from a colored pixel
    """
    # Simple implementation - scan right and down to find bounds
    min_x, max_x = start_x, start_x
    min_y, max_y = start_y, start_y

    # Scan horizontally to find right edge
    x = start_x
    while x < width - 1:
        pixel = img_array[start_y, x, :3]
        diff = np.abs(pixel.astype(int) - np.array(color))
        if np.all(diff <= tolerance):
            max_x = x
            x += 1
        else:
            break

    # Scan vertically to find bottom edge
    y = start_y
    while y < height - 1:
        pixel = img_array[y, start_x, :3]
        diff = np.abs(pixel.astype(int) - np.array(color))
        if np.all(diff <= tolerance):
            max_y = y
            y += 1
        else:
            break

    # If we found a significant line, return it
    if max_x - min_x > 100 or max_y - min_y > 100:
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x + 1,
            'height': max_y - min_y + 1
        }

    return None

# Alternative approach: Scan for rectangle edges more systematically
def find_rectangles_by_edges(img_array):
    """
    Find rectangles by detecting horizontal and vertical colored lines
    """
    results = []

    # Scan for horizontal lines (more reliable)
    for y in range(0, height, 2):  # Skip every other row for speed
        row = img_array[y, :, :3]

        # Look for continuous colored segments
        x = 0
        while x < width:
            pixel = row[x]

            # Check if this is a bright colored pixel
            for color_name, color_rgb in colors.items():
                diff = np.abs(pixel.astype(int) - np.array(color_rgb))
                if np.all(diff <= 30):
                    # Found start of colored line - trace it
                    start_x = x
                    while x < width:
                        pixel = row[x]
                        diff = np.abs(pixel.astype(int) - np.array(color_rgb))
                        if np.all(diff <= 30):
                            x += 1
                        else:
                            break

                    line_length = x - start_x
                    if line_length > 500:  # Significant horizontal line
                        print(f"Found {color_name} horizontal line at y={y}, x={start_x}..{x} (length={line_length})")
                        results.append({
                            'color': color_name,
                            'type': 'horizontal',
                            'y': y,
                            'x_start': start_x,
                            'x_end': x,
                            'length': line_length
                        })
                    break
            x += 1

    return results

# Run the detection
print("\nScanning for colored rectangle edges...")
print("=" * 60)
edges = find_rectangles_by_edges(img_array)

print(f"\nFound {len(edges)} colored lines")

# Group by approximate y-coordinate to find rectangles
print("\nGrouping lines into rectangles...")
