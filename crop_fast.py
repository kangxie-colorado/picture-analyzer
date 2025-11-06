#!/usr/bin/env python3
"""
Fast panel cropping using pre-defined pixel coordinates (NO LLM CALLS)

This script uses the coordinate configuration file to crop panels instantly
without any API calls or LLM processing.
"""
import os
import sys
import yaml
import glob
from PIL import Image
from pathlib import Path


def load_coordinates(dashboard_name: str) -> dict:
    """Load pre-defined panel coordinates from YAML config"""
    config_path = f"dashboard-prompts/{dashboard_name}/coordinates.yaml"

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Coordinates file not found: {config_path}\n"
            f"Run 'python analyze_layout.py <screenshot>' to generate it."
        )

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def crop_panel(image_path: str, panel_id: str, coordinates: dict, output_path: str):
    """
    Crop a single panel using pixel coordinates

    Args:
        image_path: Path to screenshot
        panel_id: Panel ID (e.g., 'S1-L-write')
        coordinates: Dictionary with x, y, width, height
        output_path: Where to save cropped image
    """
    # Open image
    img = Image.open(image_path)

    # Extract coordinates
    x = coordinates['x']
    y = coordinates['y']
    width = coordinates['width']
    height = coordinates['height']

    # Calculate crop box
    left = x
    top = y
    right = x + width
    bottom = y + height

    # Ensure within bounds
    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)

    # Crop
    cropped = img.crop((left, top, right, bottom))

    # Save
    cropped.save(output_path, 'PNG')

    return {
        'x': left,
        'y': top,
        'width': right - left,
        'height': bottom - top
    }


def crop_all_panels(image_path: str, dashboard_name: str, output_dir: str):
    """
    Crop all panels from a screenshot

    Args:
        image_path: Path to screenshot
        dashboard_name: Name of dashboard
        output_dir: Directory to save cropped panels
    """
    # Load coordinates
    config = load_coordinates(dashboard_name)
    panels = config['panels']

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get screenshot basename
    screenshot_name = Path(image_path).stem

    print(f"\nProcessing: {image_path}")
    print(f"Dashboard: {dashboard_name}")
    print(f"Panels to crop: {len(panels)}")
    print(f"Output directory: {output_dir}/")
    print()

    results = []

    # Crop each panel
    for i, (panel_id, coords) in enumerate(panels.items(), 1):
        output_filename = f"{screenshot_name}.{panel_id.lower()}.png"
        output_path = os.path.join(output_dir, output_filename)

        try:
            actual_coords = crop_panel(image_path, panel_id, coords, output_path)
            print(f"  [{i}/{len(panels)}] ✓ {panel_id:20} → {output_filename}")

            results.append({
                'panel_id': panel_id,
                'status': 'success',
                'output': output_path,
                'coordinates': actual_coords
            })

        except Exception as e:
            print(f"  [{i}/{len(panels)}] ✗ {panel_id:20} → Error: {e}")
            results.append({
                'panel_id': panel_id,
                'status': 'error',
                'error': str(e)
            })

    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n✓ Cropped {success_count}/{len(panels)} panels successfully")

    return results


def batch_process(screenshots_dir: str, dashboard_name: str, output_dir: str):
    """Process all screenshots in a directory"""
    # Find screenshots
    patterns = [f'{screenshots_dir}/*.png', f'{screenshots_dir}/*.jpg', f'{screenshots_dir}/*.jpeg']
    screenshots = []
    for pattern in patterns:
        screenshots.extend(glob.glob(pattern))

    if not screenshots:
        print(f"No screenshots found in {screenshots_dir}/")
        return

    print(f"{'='*70}")
    print(f"Fast Panel Cropping (No LLM)")
    print(f"{'='*70}")
    print(f"Dashboard: {dashboard_name}")
    print(f"Screenshots: {len(screenshots)}")
    print()

    total_panels = 0
    total_success = 0

    for screenshot in screenshots:
        results = crop_all_panels(screenshot, dashboard_name, output_dir)
        total_panels += len(results)
        total_success += sum(1 for r in results if r['status'] == 'success')

    print(f"\n{'='*70}")
    print(f"Batch Complete")
    print(f"{'='*70}")
    print(f"Screenshots processed: {len(screenshots)}")
    print(f"Total panels cropped: {total_success}/{total_panels}")
    print(f"Outputs saved to: {output_dir}/")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Fast panel cropping using pre-defined coordinates (no LLM)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crop all panels from one screenshot
  python crop_fast.py screenshot.png

  # Batch process all screenshots
  python crop_fast.py --batch

  # Specify custom output directory
  python crop_fast.py screenshot.png -o my_outputs/

  # Use different dashboard configuration
  python crop_fast.py screenshot.png -d my-dashboard
        """
    )

    parser.add_argument(
        'image',
        nargs='?',
        help='Screenshot image path'
    )
    parser.add_argument(
        '-d', '--dashboard',
        default='abase-risk-analysis',
        help='Dashboard name (default: abase-risk-analysis)'
    )
    parser.add_argument(
        '-o', '--output',
        default='outputs',
        help='Output directory (default: outputs/)'
    )
    parser.add_argument(
        '-p', '--panel',
        help='Crop only this panel ID (e.g., S1-L-write)'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process all screenshots in screenshots/ directory'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available panels from coordinates file'
    )

    args = parser.parse_args()

    # List panels
    if args.list:
        try:
            config = load_coordinates(args.dashboard)
            print(f"Available panels in {args.dashboard}:")
            print()
            for panel_id, coords in config['panels'].items():
                print(f"  {panel_id:20} @ ({coords['x']:4}, {coords['y']:4}, {coords['width']:4}x{coords['height']:4})")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    # Batch mode
    if args.batch:
        try:
            batch_process('screenshots', args.dashboard, args.output)
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        return

    # Single image mode
    if not args.image:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.image):
        print(f"Error: Image not found: {args.image}")
        sys.exit(1)

    try:
        if args.panel:
            # Crop single panel
            config = load_coordinates(args.dashboard)
            if args.panel not in config['panels']:
                print(f"Error: Panel '{args.panel}' not found in configuration")
                print(f"Available panels: {', '.join(config['panels'].keys())}")
                sys.exit(1)

            coords = config['panels'][args.panel]
            screenshot_name = Path(args.image).stem
            output_filename = f"{screenshot_name}.{args.panel.lower()}.png"
            output_path = os.path.join(args.output, output_filename)

            os.makedirs(args.output, exist_ok=True)
            crop_panel(args.image, args.panel, coords, output_path)
            print(f"✓ Cropped {args.panel} → {output_path}")
        else:
            # Crop all panels
            crop_all_panels(args.image, args.dashboard, args.output)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
