#!/usr/bin/env python3
"""
One-time layout analysis script
Uses Claude Vision API once to identify all panel coordinates in a dashboard screenshot
Saves coordinates to a reusable configuration file
"""
import os
import sys
import json
import base64
import anthropic
import yaml
from PIL import Image


def analyze_dashboard_layout(screenshot_path: str, api_key: str, dashboard_name: str) -> dict:
    """
    Use Claude Vision to analyze dashboard and extract all panel coordinates

    Returns a dictionary mapping panel IDs to their pixel coordinates
    """
    # Read and encode image
    with open(screenshot_path, 'rb') as f:
        image_data = f.read()

    base64_image = base64.standard_b64encode(image_data).decode('utf-8')

    # Get image dimensions
    img = Image.open(screenshot_path)
    width, height = img.width, img.height

    # Create detailed prompt
    prompt = f"""Analyze this dashboard screenshot and identify the precise bounding box coordinates for each panel.

This dashboard has the following structure:
- Row 1 (S1): 4 panels in a 2x2 grid - read/write quota vs usage
- Row 2 (S2): 2 panels side by side - disk usage and storage capacity
- Row 3 (S3): 3 panels - QPS quota (top-left), hotkey (top-right), value size (bottom full-width)

Image dimensions: {width}x{height} pixels

For EACH of the 9 panels, identify:
1. The exact bounding box (x, y, width, height) in pixels
2. Include the panel title, graph area, legend, and axis labels
3. Exclude excessive whitespace between panels

Respond with a JSON object mapping panel IDs to coordinates:

{{
  "S1-L-write": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S1-R-write": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S1-L-read": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S1-R-read": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S2-L-disk": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S2-R-partition": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S3-L-qps_vs_quota": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S3-R-hotkey": {{"x": ..., "y": ..., "width": ..., "height": ...}},
  "S3-L2-value_size": {{"x": ..., "y": ..., "width": ..., "height": ...}}
}}

Panel ID Mapping:
- S1-L-write: Row 1, left column, top panel (读总计/Read Total)
- S1-R-write: Row 1, right column, top panel (读/DC, Read per DC)
- S1-L-read: Row 1, left column, bottom panel (写总计/Write Total)
- S1-R-read: Row 1, right column, bottom panel (写/DC, Write per DC)
- S2-L-disk: Row 2, left panel (Disk Usage)
- S2-R-partition: Row 2, right panel (Storage Capacity)
- S3-L-qps_vs_quota: Row 3, left panel (QPS vs Quota)
- S3-R-hotkey: Row 3, right panel (热key RU top3)
- S3-L2-value_size: Row 3, bottom panel (Single Value Size per DC)

IMPORTANT: Return ONLY the JSON object, no other text."""

    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)

    print(f"Analyzing {screenshot_path}...")
    print(f"Image size: {width}x{height}")
    print("Calling Claude Vision API...")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # Parse response
    response_text = message.content[0].text.strip()

    # Extract JSON
    import re
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)

    coordinates = json.loads(response_text)

    print(f"✓ Successfully extracted coordinates for {len(coordinates)} panels")

    return coordinates


def save_layout_config(coordinates: dict, dashboard_name: str, output_path: str):
    """Save coordinates to a configuration file"""

    config = {
        'dashboard': dashboard_name,
        'version': '1.0',
        'description': 'Pixel-based panel coordinates (no LLM required for cropping)',
        'panels': coordinates
    }

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"✓ Saved layout configuration to: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_layout.py <screenshot_path> [dashboard_name]")
        print("Example: python analyze_layout.py screenshots/abase-risk-anal-11041203.png abase-risk-analysis")
        sys.exit(1)

    screenshot_path = sys.argv[1]
    dashboard_name = sys.argv[2] if len(sys.argv) > 2 else 'abase-risk-analysis'

    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot not found: {screenshot_path}")
        sys.exit(1)

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Analyze layout
    try:
        coordinates = analyze_dashboard_layout(screenshot_path, api_key, dashboard_name)

        # Display results
        print("\nExtracted coordinates:")
        for panel_id, coords in coordinates.items():
            print(f"  {panel_id}: x={coords['x']}, y={coords['y']}, w={coords['width']}, h={coords['height']}")

        # Save to config file
        output_path = f"dashboard-prompts/{dashboard_name}/coordinates.yaml"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        save_layout_config(coordinates, dashboard_name, output_path)

        print(f"\n✓ Layout analysis complete!")
        print(f"  Config saved to: {output_path}")
        print(f"\nYou can now use coordinate-based cropping without LLM calls.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
