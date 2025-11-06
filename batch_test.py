#!/usr/bin/env python3
"""
Batch test script to process all screenshots and crop all panels
Tests both with-prompt (using layout) and without-prompt (pure vision) modes
"""
import os
import sys
import glob
from pathlib import Path
from dashboard_layout import parse_dashboard_layout
from panel_cropper import PanelCropper


def get_dashboard_name_from_screenshot(screenshot_path: str) -> str:
    """
    Try to determine dashboard name from screenshot filename
    Default to 'abase-risk-analysis' if not clear
    """
    basename = os.path.basename(screenshot_path).lower()

    # Check for known dashboard names
    if 'abase' in basename or 'risk' in basename:
        return 'abase-risk-analysis'

    # Add more dashboard detection logic here as needed

    # Default
    return 'abase-risk-analysis'


def sanitize_filename(name: str) -> str:
    """Sanitize filename for safe filesystem usage"""
    # Replace path separators and other unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        name = name.replace(char, '-')
    return name


def process_screenshot(
    screenshot_path: str,
    dashboard_name: str,
    layout_path: str,
    cropper: PanelCropper,
    output_dir: str
):
    """
    Process a single screenshot and crop all panels in both modes

    Args:
        screenshot_path: Path to screenshot file
        dashboard_name: Name of the dashboard
        layout_path: Path to layout YAML file
        cropper: PanelCropper instance
        output_dir: Output directory
    """
    print(f"\n{'='*80}")
    print(f"Processing: {screenshot_path}")
    print(f"Dashboard: {dashboard_name}")
    print(f"{'='*80}")

    # Read screenshot
    try:
        with open(screenshot_path, 'rb') as f:
            image_data = f.read()
        print(f"✓ Loaded screenshot ({len(image_data)} bytes)")
    except Exception as e:
        print(f"✗ Error reading screenshot: {e}")
        return

    # Parse layout
    try:
        layout = parse_dashboard_layout(layout_path)
        print(f"✓ Loaded layout: {layout.human_name} ({len(layout.list_all_panels())} panels)")
    except Exception as e:
        print(f"✗ Error parsing layout: {e}")
        return

    # Get screenshot base name
    screenshot_basename = os.path.basename(screenshot_path)
    screenshot_name = os.path.splitext(screenshot_basename)[0]
    screenshot_name = sanitize_filename(screenshot_name)

    # Get all panels
    panels = layout.list_all_panels()

    print(f"\nCropping {len(panels)} panels in both modes...\n")

    success_count = {'with-prompt': 0, 'without-prompt': 0}
    error_count = {'with-prompt': 0, 'without-prompt': 0}

    # Process each panel
    for i, panel in enumerate(panels, 1):
        panel_id = panel.id
        print(f"[{i}/{len(panels)}] Panel: {panel_id}")

        # Mode 1: With prompt (using layout)
        try:
            print(f"  → with-prompt... ", end='', flush=True)
            cropped_image, metadata = cropper.crop_panel_by_id(
                image_data,
                layout,
                panel_id,
                use_layout=True
            )

            # Generate output filename
            output_filename = f"{screenshot_name}.with-prompt.{panel_id.lower()}.png"
            output_path = os.path.join(output_dir, output_filename)

            # Save
            with open(output_path, 'wb') as f:
                f.write(cropped_image)

            confidence = metadata.get('confidence', 'unknown')
            print(f"✓ ({confidence} confidence)")
            success_count['with-prompt'] += 1

        except Exception as e:
            print(f"✗ Error: {str(e)[:60]}")
            error_count['with-prompt'] += 1

        # Mode 2: Without prompt (pure vision)
        try:
            print(f"  → without-prompt... ", end='', flush=True)
            cropped_image, metadata = cropper.crop_panel_by_id(
                image_data,
                None,  # No layout
                panel_id,
                use_layout=False
            )

            # Generate output filename
            output_filename = f"{screenshot_name}.without-prompt.{panel_id.lower()}.png"
            output_path = os.path.join(output_dir, output_filename)

            # Save
            with open(output_path, 'wb') as f:
                f.write(cropped_image)

            confidence = metadata.get('confidence', 'unknown')
            print(f"✓ ({confidence} confidence)")
            success_count['without-prompt'] += 1

        except Exception as e:
            print(f"✗ Error: {str(e)[:60]}")
            error_count['without-prompt'] += 1

    # Summary
    print(f"\n{'─'*80}")
    print(f"Summary for {screenshot_basename}:")
    print(f"  With prompt:    {success_count['with-prompt']}/{len(panels)} successful, {error_count['with-prompt']} errors")
    print(f"  Without prompt: {success_count['without-prompt']}/{len(panels)} successful, {error_count['without-prompt']} errors")
    print(f"{'─'*80}")


def main():
    # Configuration
    screenshots_dir = 'screenshots'
    output_dir = 'outputs'
    dashboards_config = {
        'abase-risk-analysis': 'dashboard-prompts/abase-risk-analysis/static_pack.yaml'
    }

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Please set environment variable.")
        sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Initialize cropper
    cropper = PanelCropper(api_key)
    print(f"✓ Initialized PanelCropper")

    # Find all screenshots
    screenshot_patterns = ['*.png', '*.jpg', '*.jpeg']
    screenshots = []
    for pattern in screenshot_patterns:
        screenshots.extend(glob.glob(os.path.join(screenshots_dir, pattern)))

    if not screenshots:
        print(f"\nNo screenshots found in {screenshots_dir}/")
        print(f"Please add screenshot images to the {screenshots_dir}/ directory")
        sys.exit(0)

    print(f"\nFound {len(screenshots)} screenshot(s):")
    for s in screenshots:
        print(f"  - {s}")

    # Process each screenshot
    total_success = {'with-prompt': 0, 'without-prompt': 0}
    total_errors = {'with-prompt': 0, 'without-prompt': 0}

    for screenshot_path in screenshots:
        # Determine dashboard name
        dashboard_name = get_dashboard_name_from_screenshot(screenshot_path)

        # Get layout path
        if dashboard_name not in dashboards_config:
            print(f"\nSkipping {screenshot_path}: Unknown dashboard '{dashboard_name}'")
            continue

        layout_path = dashboards_config[dashboard_name]

        if not os.path.exists(layout_path):
            print(f"\nSkipping {screenshot_path}: Layout not found at {layout_path}")
            continue

        # Process
        process_screenshot(
            screenshot_path,
            dashboard_name,
            layout_path,
            cropper,
            output_dir
        )

    # Final summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Processed {len(screenshots)} screenshot(s)")
    print(f"Outputs saved to: {output_dir}/")
    print(f"\nCheck the outputs directory for all cropped panels!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
