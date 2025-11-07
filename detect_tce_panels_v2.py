#!/usr/bin/env python3
"""
Detect filled rectangles from tce_panels_filled_4colors_taller.png
"""
from PIL import Image

img = Image.open('screenshots/tce_panels_filled_4colors_taller.png')
width, height = img.size
print(f"Image dimensions: {width}x{height}\n")

def is_colored(pixel):
    """Check if pixel is a colored block (not background)"""
    rgb = pixel[:3]
    # Not too dark (background)
    if sum(rgb) < 50:
        return False
    # Not too light (UI elements) - but be more permissive
    if sum(rgb) > 750:
        return False
    return True

def colors_match(c1, c2, tol=30):
    """Check if two colors match"""
    return all(abs(c1[i] - c2[i]) <= tol for i in range(3))

# Find horizontal bands by scanning rows
print("Finding horizontal color bands...")
bands = []
current_band = None

for y in range(50, height):  # Start from y=50
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
            if current_band['height'] > 50:  # Lower threshold
                bands.append(current_band)
                print(f"  Found band: y={current_band['y_start']}-{current_band['y_end']}, color=RGB{current_band['color']}")
            current_band = {'y_start': y, 'color': mid_pixel}
    else:
        # Non-colored row - end current band if any
        if current_band is not None:
            current_band['y_end'] = y - 1
            current_band['height'] = current_band['y_end'] - current_band['y_start'] + 1
            if current_band['height'] > 50:
                bands.append(current_band)
                print(f"  Found band: y={current_band['y_start']}-{current_band['y_end']}, color=RGB{current_band['color']}")
            current_band = None

# Don't forget last band
if current_band is not None:
    current_band['y_end'] = height - 1
    current_band['height'] = current_band['y_end'] - current_band['y_start'] + 1
    if current_band['height'] > 50:
        bands.append(current_band)
        print(f"  Found band: y={current_band['y_start']}-{current_band['y_end']}, color=RGB{current_band['color']}")

print(f"\nTotal bands found: {len(bands)}\n")

# For each band, find vertical splits (left/right rectangles)
rectangles = []

for band_idx, band in enumerate(bands):
    print(f"Analyzing Band {band_idx + 1}: y={band['y_start']}-{band['y_end']}, height={band['height']}")

    # Scan across the band to find vertical color changes
    y_mid = (band['y_start'] + band['y_end']) // 2

    regions = []
    current_region = None

    for x in range(20, width):
        pixel = img.getpixel((x, y_mid))[:3]

        if is_colored(pixel):
            if current_region is None:
                # Start new region
                current_region = {'x_start': x, 'color': pixel}
            elif not colors_match(current_region['color'], pixel):
                # Color changed - end current region
                current_region['x_end'] = x - 1
                current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
                if current_region['width'] > 200:  # Lower threshold
                    regions.append(current_region)
                current_region = {'x_start': x, 'color': pixel}
        else:
            # Non-colored pixel
            if current_region is not None:
                current_region['x_end'] = x - 1
                current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
                if current_region['width'] > 200:
                    regions.append(current_region)
                current_region = None

    # Don't forget last region
    if current_region is not None:
        current_region['x_end'] = width - 1
        current_region['width'] = current_region['x_end'] - current_region['x_start'] + 1
        if current_region['width'] > 200:
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
        print(f"  Region: x={rect['x']:4d}, y={rect['y']:4d}, width={rect['width']:4d}, height={rect['height']:4d}, color=RGB{rect['color_rgb']}")

# Sort by position
rectangles.sort(key=lambda r: (r['y'], r['x']))

print("\n" + "=" * 70)
print(f"Total rectangles detected: {len(rectangles)}")
print("=" * 70)

# Assign panel IDs
panel_ids = ['panel-1-left', 'panel-1-right', 'panel-2-left', 'panel-2-right']

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
