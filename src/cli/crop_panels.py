#!/usr/bin/env python3
"""
CLI tool for cropping dashboard panels using coordinates
Extracts individual panels from dashboard screenshots
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.panel_cropper import PanelCropper


def main():
    parser = argparse.ArgumentParser(
        description='Crop dashboard panels using coordinate configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Crop all panels from a dashboard
  python -m src.cli.crop_panels screenshots/dashboard.png \\
    -c config/dashboards/my-dashboard/coordinates.yaml

  # Crop specific panel
  python -m src.cli.crop_panels screenshots/dashboard.png \\
    -c config/dashboards/my-dashboard/coordinates.yaml \\
    -p S1-L-write

  # Specify output directory
  python -m src.cli.crop_panels screenshots/dashboard.png \\
    -c config/dashboards/my-dashboard/coordinates.yaml \\
    -o outputs/panels/

  # Verify coordinates without cropping
  python -m src.cli.crop_panels screenshots/dashboard.png \\
    -c config/dashboards/my-dashboard/coordinates.yaml \\
    --verify-only
'''
    )

    parser.add_argument(
        'image',
        help='Path to dashboard screenshot'
    )

    parser.add_argument(
        '-c', '--coordinates',
        dest='coordinates',
        required=True,
        help='Path to coordinates.yaml file'
    )

    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        default='outputs/cropped-panels',
        help='Output directory for cropped panels (default: outputs/cropped-panels)'
    )

    parser.add_argument(
        '-p', '--panel',
        dest='panel_id',
        help='Crop specific panel only (e.g., S1-L-write)'
    )

    parser.add_argument(
        '--pattern',
        dest='filename_pattern',
        default='{dashboard}_{panel_id}.png',
        help='Filename pattern (default: {dashboard}_{panel_id}.png)'
    )

    parser.add_argument(
        '--verify-only',
        dest='verify_only',
        action='store_true',
        help='Only verify coordinates, do not crop'
    )

    parser.add_argument(
        '--list-panels',
        dest='list_panels',
        action='store_true',
        help='List available panel IDs and exit'
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.image):
        print(f"Error: Image not found: {args.image}")
        sys.exit(1)

    if not os.path.exists(args.coordinates):
        print(f"Error: Coordinates file not found: {args.coordinates}")
        sys.exit(1)

    try:
        # Initialize cropper
        print(f"📐 Loading coordinates from: {args.coordinates}")
        cropper = PanelCropper(args.coordinates)

        # List panels and exit if requested
        if args.list_panels:
            panel_ids = cropper.get_panel_ids()
            print(f"\n📋 Available panels ({len(panel_ids)}):")
            for panel_id in panel_ids:
                print(f"  • {panel_id}")
            sys.exit(0)

        # Verify coordinates
        print(f"🔍 Verifying coordinates against: {args.image}")
        verification = cropper.verify_coordinates(args.image)

        # Show verification results
        img_dims = verification['image_dimensions']
        exp_dims = verification['expected_dimensions']

        print(f"\nImage dimensions: {img_dims['width']}x{img_dims['height']}")

        if exp_dims['width'] > 0:
            print(f"Expected dimensions: {exp_dims['width']}x{exp_dims['height']}")

            if not verification['dimensions_match']:
                print("⚠️  WARNING: Image dimensions don't match expected dimensions!")
                print("   Cropping may produce incorrect results.")

        # Check for coordinate issues
        issues_found = False
        for check in verification['panel_checks']:
            if not check['valid']:
                if not issues_found:
                    print("\n❌ Coordinate validation issues:")
                    issues_found = True
                print(f"  • {check['panel_id']}: {', '.join(check['issues'])}")

        if issues_found:
            print("\n⚠️  Some panels have coordinate issues.")
            print("   Cropping may fail or produce incorrect results.")
            response = input("\nContinue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(1)
        else:
            print("✓ All panel coordinates are valid")

        # Exit if verify-only
        if args.verify_only:
            print("\n✓ Verification complete (no cropping performed)")
            sys.exit(0)

        # Crop panels
        print(f"\n✂️  Cropping panels...")

        if args.panel_id:
            # Crop single panel
            print(f"   Panel: {args.panel_id}")
            output_path = os.path.join(
                args.output_dir,
                args.filename_pattern.format(
                    dashboard=cropper.coordinates.get('dashboard', 'dashboard'),
                    panel_id=args.panel_id.lower()
                )
            )

            os.makedirs(args.output_dir, exist_ok=True)

            _, metadata = cropper.crop_panel(args.image, args.panel_id, output_path)

            print(f"\n✅ Panel cropped successfully!")
            print(f"   Output: {output_path}")
            print(f"   Size: {metadata['dimensions']['width']}x{metadata['dimensions']['height']}px")

        else:
            # Crop all panels
            panel_ids = cropper.get_panel_ids()
            print(f"   Panels: {len(panel_ids)}")
            print(f"   Output: {args.output_dir}/")
            print()

            results = cropper.crop_all_panels(
                args.image,
                args.output_dir,
                args.filename_pattern
            )

            # Summary
            success_count = sum(1 for r in results if 'error' not in r)
            error_count = len(results) - success_count

            print(f"\n{'='*60}")
            print(f"✅ Cropping complete!")
            print(f"{'='*60}")
            print(f"   Total panels: {len(results)}")
            print(f"   Successfully cropped: {success_count}")

            if error_count > 0:
                print(f"   Errors: {error_count}")

            print(f"   Output directory: {args.output_dir}")

            # Show errors if any
            if error_count > 0:
                print("\n❌ Errors:")
                for result in results:
                    if 'error' in result:
                        print(f"   • {result['panel_id']}: {result['error']}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
