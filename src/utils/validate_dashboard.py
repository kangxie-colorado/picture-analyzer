#!/usr/bin/env python3
"""
Validate dashboard configuration files
Checks coordinates, structure, and consistency
"""
import os
import sys
import yaml
import json
import re
from pathlib import Path


def validate_coordinates(config_dir: str) -> tuple:
    """Validate coordinates.yaml"""
    errors = []
    warnings = []
    info = []

    coord_path = os.path.join(config_dir, 'coordinates.yaml')

    if not os.path.exists(coord_path):
        errors.append("coordinates.yaml not found")
        return errors, warnings, info

    try:
        with open(coord_path, 'r') as f:
            coords = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Failed to parse coordinates.yaml: {e}")
        return errors, warnings, info

    # Check required fields
    if 'dashboard' not in coords:
        errors.append("Missing 'dashboard' field")

    if 'image_dimensions' not in coords:
        warnings.append("Missing 'image_dimensions' field")
        width, height = 10000, 10000  # fallback
    else:
        width = coords['image_dimensions'].get('width', 10000)
        height = coords['image_dimensions'].get('height', 10000)
        info.append(f"Image dimensions: {width}x{height}")

    # Validate each panel
    panels = coords.get('panels', {})
    if not panels:
        errors.append("No panels defined")
        return errors, warnings, info

    info.append(f"Panels defined: {len(panels)}")

    for panel_id, panel_coords in panels.items():
        # Check ID pattern
        if not re.match(r'S\d+-[LR]\d*-\w+', panel_id):
            warnings.append(f"{panel_id}: Doesn't match ID pattern")

        # Check required coordinate fields
        required = ['x', 'y', 'width', 'height']
        for field in required:
            if field not in panel_coords:
                errors.append(f"{panel_id}: Missing '{field}' coordinate")
                continue

        x = panel_coords.get('x', 0)
        y = panel_coords.get('y', 0)
        w = panel_coords.get('width', 0)
        h = panel_coords.get('height', 0)

        # Validate values
        if x < 0 or y < 0:
            errors.append(f"{panel_id}: Negative coordinates ({x}, {y})")

        if w <= 0 or h <= 0:
            errors.append(f"{panel_id}: Invalid size ({w}x{h})")

        if x + w > width:
            errors.append(f"{panel_id}: Extends beyond image width ({x}+{w} > {width})")

        if y + h > height:
            errors.append(f"{panel_id}: Extends beyond image height ({y}+{h} > {height})")

        if w < 50 or h < 50:
            warnings.append(f"{panel_id}: Very small panel ({w}x{h})")

    # Check for overlaps
    panel_list = [(pid, p) for pid, p in panels.items()]
    for i, (id1, p1) in enumerate(panel_list):
        for id2, p2 in panel_list[i+1:]:
            if panels_overlap(p1, p2):
                warnings.append(f"Panels {id1} and {id2} overlap")

    return errors, warnings, info


def validate_static_pack(config_dir: str, panel_ids: set) -> tuple:
    """Validate static_pack.yaml"""
    errors = []
    warnings = []
    info = []

    static_path = os.path.join(config_dir, 'static_pack.yaml')

    if not os.path.exists(static_path):
        errors.append("static_pack.yaml not found")
        return errors, warnings, info

    try:
        with open(static_path, 'r') as f:
            static = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Failed to parse static_pack.yaml: {e}")
        return errors, warnings, info

    # Check structure
    if 'dashboard_static' not in static:
        errors.append("Missing 'dashboard_static' root key")
        return errors, warnings, info

    dashboard = static['dashboard_static']

    # Check required fields
    required_fields = ['id', 'human_name', 'rows']
    for field in required_fields:
        if field not in dashboard:
            errors.append(f"Missing required field: {field}")

    # Validate rows
    rows = dashboard.get('rows', [])
    if not rows:
        errors.append("No rows defined")
        return errors, warnings, info

    info.append(f"Rows defined: {len(rows)}")

    # Collect panel IDs from rows
    row_panel_ids = set()

    for i, row in enumerate(rows):
        row_id = row.get('id', f'row_{i}')

        # Check row ID pattern
        if not re.match(r'S\d+', row_id):
            warnings.append(f"{row_id}: Doesn't match row ID pattern")

        # Check row fields
        if 'title' not in row:
            warnings.append(f"{row_id}: Missing title")

        if 'panels' not in row:
            errors.append(f"{row_id}: No panels defined")
            continue

        # Check each panel in row
        for panel in row['panels']:
            if 'id' not in panel:
                errors.append(f"{row_id}: Panel missing ID")
                continue

            panel_id = panel['id']
            row_panel_ids.add(panel_id)

            # Check if panel exists in coordinates
            if panel_ids and panel_id not in panel_ids:
                errors.append(
                    f"{panel_id}: Defined in static_pack but not in coordinates"
                )

    # Check for panels in coordinates but not in static_pack
    if panel_ids:
        missing = panel_ids - row_panel_ids
        if missing:
            warnings.append(
                f"Panels in coordinates but not in static_pack: {', '.join(missing)}"
            )

    return errors, warnings, info


def validate_run_pack(config_dir: str) -> tuple:
    """Validate run_pack.yaml (JSON format)"""
    errors = []
    warnings = []
    info = []

    run_path = os.path.join(config_dir, 'run_pack.yaml')

    if not os.path.exists(run_path):
        errors.append("run_pack.yaml not found")
        return errors, warnings, info

    try:
        with open(run_path, 'r') as f:
            run_pack = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse run_pack.yaml: {e}")
        return errors, warnings, info

    # Check structure
    if 'run_pack' not in run_pack:
        errors.append("Missing 'run_pack' root key")
        return errors, warnings, info

    # Check required sections
    required_sections = ['time_window', 'scope', 'output_format']
    for section in required_sections:
        if section not in run_pack['run_pack']:
            warnings.append(f"Missing section: {section}")

    info.append("run_pack.yaml structure is valid")

    return errors, warnings, info


def panels_overlap(p1: dict, p2: dict) -> bool:
    """Check if two panels overlap"""
    x1, y1 = p1.get('x', 0), p1.get('y', 0)
    w1, h1 = p1.get('width', 0), p1.get('height', 0)
    x2, y2 = p2.get('x', 0), p2.get('y', 0)
    w2, h2 = p2.get('width', 0), p2.get('height', 0)

    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or
                y1 + h1 <= y2 or y2 + h2 <= y1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.validate_dashboard <config_dir>")
        print("Example: python -m src.utils.validate_dashboard config/dashboards/abase-risk-analysis")
        sys.exit(1)

    config_dir = sys.argv[1]

    if not os.path.isdir(config_dir):
        print(f"Error: Directory not found: {config_dir}")
        sys.exit(1)

    print(f"🔍 Validating dashboard configuration: {config_dir}\n")

    all_errors = []
    all_warnings = []
    all_info = []

    # Validate coordinates
    print("📍 Validating coordinates.yaml...")
    errors, warnings, info = validate_coordinates(config_dir)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    all_info.extend(info)

    # Get panel IDs for cross-validation
    try:
        with open(os.path.join(config_dir, 'coordinates.yaml'), 'r') as f:
            coords = yaml.safe_load(f)
            panel_ids = set(coords.get('panels', {}).keys())
    except:
        panel_ids = set()

    # Validate static_pack
    print("📋 Validating static_pack.yaml...")
    errors, warnings, info = validate_static_pack(config_dir, panel_ids)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    all_info.extend(info)

    # Validate run_pack
    print("⚙️  Validating run_pack.yaml...")
    errors, warnings, info = validate_run_pack(config_dir)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    all_info.extend(info)

    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    if all_info:
        print("\n📊 Information:")
        for msg in all_info:
            print(f"  ℹ️  {msg}")

    if all_warnings:
        print(f"\n⚠️  Warnings ({len(all_warnings)}):")
        for msg in all_warnings:
            print(f"  ⚠️  {msg}")

    if all_errors:
        print(f"\n❌ Errors ({len(all_errors)}):")
        for msg in all_errors:
            print(f"  ❌ {msg}")
        print("\n❌ Validation FAILED")
        sys.exit(1)
    else:
        if all_warnings:
            print("\n✅ Validation PASSED (with warnings)")
        else:
            print("\n✅ Validation PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
