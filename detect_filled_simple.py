#!/usr/bin/env python3
"""
Simple rectangle detection by finding color boundaries
"""
from PIL import Image

img = Image.open('screenshots/abase-risk-anal-11041203_filled_v5.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def is_colored(pixel):
    """Check if pixel is a colored block (not background)"""
    rgb = pixel[:3]
    # Not too dark (background)
    if sum(rgb) < 100:
        return False
    # Not too light (UI elements)
    if sum(rgb) > 700:
        return False
    return True

def colors_match(c1, c2, tol=20):
    """Check if two colors match"""
    return all(abs(c1[i] - c2[i]) <= tol for i in range(3))

# Find horizontal bands by scanning rows
print("Finding horizontal color bands...")
bands = []
current_band = None

for y in range(80, height):  # Skip top UI
    # Sample middle of the image to determine row color
    mid_pixel = img.getpixel((width // 2, y))[:3]

    if is_colored(mid_pixel):
        if current_band is None:
            # Start new band
            current_band = {'y_start': y, 'color': mid_pixel}
        elif not colors_match(current_band['color'], mid_pixel):
            # Color changed - end current band and start new one
            current_band['y_end'] = y - 1
            current_band['height'] = current_band['y_end'] - current_band['y_start'] + 1
            if current_band['height'] > 100:
                bands.append(current_band)
            current_band = {'y_start': y, 'color': mid_pixel}
    else:
        # Non-colored row - end current band if any
        if current_band is not None:
            current_band['y_end'] = y - 1
            current_band['height'] = current_band['y_end'] - current_band['y_start'] + 1
            if current_band['height'] > 100:
                bands.append(current_band)
            current_band = None

# Don't forget last band
if current_band is not None:
    current_band['y_end'] = height - 1
    current_band['height'] = current_band['y_end'] - current_band['y_start'] + 1
    if current_band['height'] > 100:
        bands.append(current_band)

print(f"Found {len(bands)} horizontal bands\n")

# For each band, find vertical splits (left/right rectangles)
rectangles = []

for band_idx, band in enumerate(bands):
    print(f"Band {band_idx + 1}: y={band['y_start']}-{band['y_end']}, height={band['height']}")

    # Scan across the band to find vertical color changes
    y_mid = (band['y_start'] + band['y_end']) // 2

    regions = []
    current_region = None

    for x in range(40, width):
        pixel = img.getpixel((x, y_mid))[:3]

        if is_colored(pixel):
            if current_region is None:
                # Start new region
                current_region = {'x_start': x, 'color': pixel}
            elif not colors_match(current_region['color'], pixel):
                # Color changed - end current region
                current_region['x_end'] = x - 1
                current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
                if current_region['width'] > 300:
                    regions.append(current_region)
                current_region = {'x_start': x, 'color': pixel}
        else:
            # Non-colored pixel
            if current_region is not None:
                current_region['x_end'] = x - 1
                current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
                if current_region['width'] > 300:
                    regions.append(current_region)
                current_region = None

    # Don't forget last region
    if current_region is not None:
        current_region['x_end'] = width - 1
        current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
        if current_region['width'] > 300:
            regions.append(current_region)

    # Create rectangles from regions
    for region in regions:
        rect = {
            'x': region['x_start'],
            'y': band['y_start'],
            'width': region['width'],
            'height': band['height'],
            'color_rgb': region['color']
        }
        rectangles.append(rect)
        print(f"  Region: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

# Sort by position
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\n" + "=" * 70)
print(f"Total rectangles: {len(rectangles)}")
print("=" * 70)

# Assign panel IDs
panel_ids = [
    'S1-L-read', 'S1-R-read',
    'S1-L-write', 'S1-R-write',
    'S2-L-disk', 'S2-R-partition',
    'S3-L-qps_vs_quota', 'S3-R-hotkey',
    'S3-L2-value_size'
]

print("\nFinal coordinates:\n")
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        panel_id = panel_ids[i]
        print(f"{panel_id:20s}: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}")

print("\n" + "=" * 70)
print("YAML format:")
print("=" * 70)
print()
for i, rect in enumerate(rectangles):
    if i < len(panel_ids):
        print(f"  {panel_ids[i]}:")
        print(f"    x: {rect['x']}")
        print(f"    y: {rect['y']}")
        print(f"    width: {rect['width']}")
        print(f"    height: {rect['height']}")
        print()
