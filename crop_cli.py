#!/usr/bin/env python3
"""
Command-line tool for cropping dashboard panels
"""
import argparse
import os
import sys
from dashboard_layout import parse_dashboard_layout
from panel_cropper import PanelCropper


def main():
    parser = argparse.ArgumentParser(
        description='Crop specific panels from dashboard screenshots using AI vision'
    )
    parser.add_argument(
        'image',
        help='Path to dashboard screenshot'
    )
    parser.add_argument(
        'dashboard',
        help='Dashboard name (e.g., abase-risk-analysis)'
    )
    parser.add_argument(
        'panel_id',
        help='Panel ID to crop (e.g., S1-L-write, S2-R-partition)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: <panel_id>.png)',
        default=None
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)',
        default=None
    )
    parser.add_argument(
        '--list-panels',
        action='store_true',
        help='List all available panels in the dashboard'
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Use --api-key or set environment variable.", file=sys.stderr)
        sys.exit(1)

    # Build layout path
    layout_path = os.path.join(
        'dashboard-prompts',
        args.dashboard,
        'static_pack.yaml'
    )

    if not os.path.exists(layout_path):
        print(f"Error: Dashboard layout not found: {layout_path}", file=sys.stderr)
        sys.exit(1)

    # Parse layout
    try:
        layout = parse_dashboard_layout(layout_path)
        print(f"Loaded dashboard: {layout.human_name}")
    except Exception as e:
        print(f"Error parsing dashboard layout: {e}", file=sys.stderr)
        sys.exit(1)

    # List panels if requested
    if args.list_panels:
        print(f"\nAvailable panels in {layout.human_name}:")
        print("=" * 60)
        for row in layout.rows:
            print(f"\nRow {row.id}: {row.title}")
            print(f"  Intent: {row.intent}")
            print(f"  Panels:")
            for panel in row.panels:
                print(f"    - {panel.id:20} | Role: {panel.role}")
        sys.exit(0)

    # Check if image exists
    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Read image
    try:
        with open(args.image, 'rb') as f:
            image_data = f.read()
        print(f"Loaded image: {args.image} ({len(image_data)} bytes)")
    except Exception as e:
        print(f"Error reading image: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize cropper
    cropper = PanelCropper(api_key)

    # Crop panel
    print(f"Identifying panel: {args.panel_id}...")
    try:
        cropped_image, metadata = cropper.crop_panel_by_id(image_data, layout, args.panel_id)
        print(f"✓ Panel identified with {metadata['confidence']} confidence")
        print(f"  Boundaries: x={metadata['boundaries']['x']}, y={metadata['boundaries']['y']}, "
              f"w={metadata['boundaries']['width']}, h={metadata['boundaries']['height']}")
        if metadata.get('notes'):
            print(f"  Notes: {metadata['notes']}")

    except Exception as e:
        print(f"Error cropping panel: {e}", file=sys.stderr)
        sys.exit(1)

    # Save output
    output_path = args.output or f"{args.panel_id}.png"
    try:
        with open(output_path, 'wb') as f:
            f.write(cropped_image)
        print(f"\n✓ Cropped panel saved to: {output_path}")
    except Exception as e:
        print(f"Error saving output: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
