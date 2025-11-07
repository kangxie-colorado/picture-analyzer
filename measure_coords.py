#!/usr/bin/env python3
"""
Helper script to calculate corrected coordinates with 1.5x scaling
"""

# My visual measurements (at 2/3 scale)
visual_coords = {
    "S1-L-read": {"x": 38, "y": 81, "width": 602, "height": 161},
    "S1-R-read": {"x": 643, "y": 81, "width": 611, "height": 161},
    "S1-L-write": {"x": 38, "y": 244, "width": 602, "height": 149},
    "S1-R-write": {"x": 643, "y": 244, "width": 611, "height": 149},
    "S2-L-disk": {"x": 38, "y": 395, "width": 602, "height": 196},
    "S2-R-partition": {"x": 643, "y": 395, "width": 611, "height": 196},
    "S3-L-qps_vs_quota": {"x": 38, "y": 593, "width": 602, "height": 169},
    "S3-R-hotkey": {"x": 643, "y": 593, "width": 611, "height": 169},
    "S3-L2-value_size": {"x": 38, "y": 764, "width": 602, "height": 162},
}

print("Corrected coordinates (multiplied by 1.5):")
print("=" * 60)

for panel_id, coords in visual_coords.items():
    actual_x = int(coords["x"] * 1.5)
    actual_y = int(coords["y"] * 1.5)
    actual_width = int(coords["width"] * 1.5)
    actual_height = int(coords["height"] * 1.5)

    print(f"\n{panel_id}:")
    print(f"  x: {actual_x}")
    print(f"  y: {actual_y}")
    print(f"  width: {actual_width}")
    print(f"  height: {actual_height}")
    print(f"  right edge: {actual_x + actual_width}")
    print(f"  bottom edge: {actual_y + actual_height}")
