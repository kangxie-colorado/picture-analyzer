#!/usr/bin/env python3
"""
Fast panel cropping CLI using pre-defined coordinates
"""
import argparse
import sys
import glob
from pathlib import Path

from ..core import CoordinatePanelCropper, load_image, save_image


def crop_single_panel(image_path: str, dashboard: str, panel_id: str, output_path: str):
    """Crop a single panel from an image"""
    cropper = CoordinatePanelCropper(dashboard)
    image_data = load_image(image_path)
    cropped, metadata = cropper.crop_panel(image_data, panel_id)

    save_image(cropped, output_path)
    print(f"✓ Cropped {panel_id} → {output_path}")

    return metadata


def crop_all_panels(image_path: str, dashboard: str, output_dir: str):
    """Crop all panels from an image"""
    cropper = CoordinatePanelCropper(dashboard)
    image_data = load_image(image_path)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    screenshot_name = Path(image_path).stem
    panels = cropper.list_panels()

    print(f"\nProcessing: {image_path}")
    print(f"Panels to crop: {len(panels)}")
    print(f"Output: {output_dir}/\n")

    success_count = 0

    for i, panel_id in enumerate(panels.keys(), 1):
        output_filename = f"{screenshot_name}.{panel_id.lower()}.png"
        output_path = Path(output_dir) / output_filename

        try:
            cropped, _ = cropper.crop_panel(image_data, panel_id)
            save_image(cropped, str(output_path))
            print(f"  [{i}/{len(panels)}] ✓ {panel_id:20} → {output_filename}")
            success_count += 1
        except Exception as e:
            print(f"  [{i}/{len(panels)}] ✗ {panel_id:20} → Error: {str(e)[:40]}")

    print(f"\n✓ Cropped {success_count}/{len(panels)} panels\n")

    return success_count


def batch_process(screenshots_dir: str, dashboard: str, output_dir: str):
    """Process all screenshots in a directory"""
    patterns = [f'{screenshots_dir}/*.png', f'{screenshots_dir}/*.jpg']
    screenshots = []
    for pattern in patterns:
        screenshots.extend(glob.glob(pattern))

    if not screenshots:
        print(f"No screenshots found in {screenshots_dir}/")
        return

    print(f"{'='*70}")
    print(f"Fast Panel Cropping (No LLM)")
    print(f"{'='*70}")
    print(f"Dashboard: {dashboard}")
    print(f"Screenshots: {len(screenshots)}\n")

    total_success = 0
    total_panels = 0

    for screenshot in screenshots:
        success = crop_all_panels(screenshot, dashboard, output_dir)
        cropper = CoordinatePanelCropper(dashboard)
        total_panels += len(cropper.list_panels())
        total_success += success

    print(f"{'='*70}")
    print(f"Batch Complete")
    print(f"{'='*70}")
    print(f"Screenshots: {len(screenshots)}")
    print(f"Panels cropped: {total_success}/{total_panels}")
    print(f"Output: {output_dir}/")


def list_panels(dashboard: str):
    """List all available panels"""
    cropper = CoordinatePanelCropper(dashboard)
    panels = cropper.list_panels()

    print(f"Available panels in {dashboard}:\n")
    for panel_id, coords in panels.items():
        print(f"  {panel_id:20} @ ({coords['x']:4}, {coords['y']:4}, "
              f"{coords['width']:4}x{coords['height']:4})")


def main():
    parser = argparse.ArgumentParser(
        description='Fast panel cropping using coordinates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s screenshot.png                    # Crop all panels
  %(prog)s screenshot.png -p S1-L-write      # Crop one panel
  %(prog)s --batch                           # Process all screenshots
  %(prog)s --list                            # List available panels
        """
    )

    parser.add_argument('image', nargs='?', help='Screenshot image path')
    parser.add_argument('-d', '--dashboard', default='abase-risk-analysis',
                        help='Dashboard name (default: abase-risk-analysis)')
    parser.add_argument('-o', '--output', default='outputs',
                        help='Output directory (default: outputs/)')
    parser.add_argument('-p', '--panel', help='Crop only this panel ID')
    parser.add_argument('--batch', action='store_true',
                        help='Process all screenshots in screenshots/')
    parser.add_argument('--list', action='store_true',
                        help='List available panels')

    args = parser.parse_args()

    try:
        if args.list:
            list_panels(args.dashboard)
        elif args.batch:
            batch_process('screenshots', args.dashboard, args.output)
        elif args.image:
            if args.panel:
                screenshot_name = Path(args.image).stem
                output_filename = f"{screenshot_name}.{args.panel.lower()}.png"
                output_path = Path(args.output) / output_filename
                Path(args.output).mkdir(parents=True, exist_ok=True)
                crop_single_panel(args.image, args.dashboard, args.panel, str(output_path))
            else:
                crop_all_panels(args.image, args.dashboard, args.output)
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
