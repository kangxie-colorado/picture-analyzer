#!/usr/bin/env python3
"""
Scale TCE coordinates from filled image to actual screenshot
"""

# Original dimensions (filled blocks)
orig_width = 2047
orig_height = 963

# Target dimensions (actual screenshot)
target_width = 3332
target_height = 1568

# Calculate scale factors
scale_x = target_width / orig_width
scale_y = target_height / orig_height

print(f"Original dimensions: {orig_width}x{orig_height}")
print(f"Target dimensions: {target_width}x{target_height}")
print(f"Scale factors: x={scale_x:.4f}, y={scale_y:.4f}\n")

# Original coordinates
panels = {
    'panel-1-left': {'x': 32, 'y': 120, 'width': 970, 'height': 395},
    'panel-1-right': {'x': 1045, 'y': 120, 'width': 971, 'height': 395},
    'panel-2-left': {'x': 32, 'y': 540, 'width': 970, 'height': 397},
    'panel-2-right': {'x': 1045, 'y': 540, 'width': 971, 'height': 397},
}

print("Scaled coordinates:")
print("=" * 70)

scaled_panels = {}
for panel_id, coords in panels.items():
    scaled = {
        'x': int(coords['x'] * scale_x),
        'y': int(coords['y'] * scale_y),
        'width': int(coords['width'] * scale_x),
        'height': int(coords['height'] * scale_y)
    }
    scaled_panels[panel_id] = scaled
    print(f"{panel_id:20s}: x={scaled['x']:4d}, y={scaled['y']:4d}, width={scaled['width']:4d}, height={scaled['height']:4d}")

print("\n" + "=" * 70)
print("YAML format:")
print("=" * 70)
print()
print(f"dashboard: tce-resource-overview")
print(f"version: '1.0'")
print(f"image_dimensions:")
print(f"  width: {target_width}")
print(f"  height: {target_height}")
print()
print("panels:")
for panel_id, coords in scaled_panels.items():
    print(f"  {panel_id}:")
    print(f"    x: {coords['x']}")
    print(f"    y: {coords['y']}")
    print(f"    width: {coords['width']}")
    print(f"    height: {coords['height']}")
    print()
