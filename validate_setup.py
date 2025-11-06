#!/usr/bin/env python3
"""
Validation script to test setup without requiring API calls
"""
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")

    required = ['flask', 'anthropic', 'PIL', 'yaml']
    missing = []

    for module in required:
        try:
            if module == 'PIL':
                __import__('PIL')
            else:
                __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} (missing)")
            missing.append(module)

    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        return False

    print("  All dependencies installed!\n")
    return True


def check_layout_files():
    """Check if dashboard layout files exist and can be parsed"""
    print("Checking dashboard layouts...")

    from dashboard_layout import parse_dashboard_layout

    layout_path = 'dashboard-prompts/abase-risk-analysis/static_pack.yaml'

    if not os.path.exists(layout_path):
        print(f"  ✗ Layout not found: {layout_path}")
        return False

    try:
        layout = parse_dashboard_layout(layout_path)
        print(f"  ✓ Parsed: {layout.human_name}")
        print(f"  ✓ Rows: {len(layout.rows)}")
        print(f"  ✓ Panels: {len(layout.list_all_panels())}")

        # Show panel details
        print("\n  Panels by row:")
        for row in layout.rows:
            print(f"    {row.id}: {len(row.panels)} panels")
            for panel in row.panels:
                print(f"      - {panel.id}")

        print()
        return True

    except Exception as e:
        print(f"  ✗ Error parsing layout: {e}")
        return False


def check_scripts():
    """Check if all scripts are present and syntactically valid"""
    print("Checking scripts...")

    scripts = [
        'app.py',
        'dashboard_layout.py',
        'panel_cropper.py',
        'crop_cli.py',
        'batch_test.py'
    ]

    for script in scripts:
        if not os.path.exists(script):
            print(f"  ✗ {script} (missing)")
            return False

        try:
            with open(script, 'r') as f:
                compile(f.read(), script, 'exec')
            print(f"  ✓ {script}")
        except SyntaxError as e:
            print(f"  ✗ {script} (syntax error: {e})")
            return False

    print()
    return True


def check_directories():
    """Check if required directories exist"""
    print("Checking directories...")

    dirs = ['screenshots', 'outputs', 'dashboard-prompts']

    for d in dirs:
        if os.path.exists(d):
            print(f"  ✓ {d}/")
        else:
            print(f"  ✗ {d}/ (missing)")
            return False

    print()
    return True


def check_screenshots():
    """Check for available screenshots"""
    print("Checking screenshots...")

    import glob

    patterns = ['screenshots/*.png', 'screenshots/*.jpg', 'screenshots/*.jpeg']
    screenshots = []

    for pattern in patterns:
        screenshots.extend(glob.glob(pattern))

    if not screenshots:
        print("  ⚠ No screenshots found in screenshots/")
        print("  → Add screenshots to test the cropping functionality")
        return True

    print(f"  ✓ Found {len(screenshots)} screenshot(s):")
    for s in screenshots:
        print(f"    - {os.path.basename(s)}")

    print()
    return True


def main():
    print("="*60)
    print("Picture Analyzer - Setup Validation")
    print("="*60)
    print()

    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Scripts", check_scripts),
        ("Layout Files", check_layout_files),
        ("Screenshots", check_screenshots),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error during {name} check: {e}\n")
            results.append((name, False))

    print("="*60)
    print("Summary")
    print("="*60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")
        if not result:
            all_passed = False

    print()

    if all_passed:
        print("✓ All checks passed!")
        print("\nReady to run:")
        print("  1. Add screenshots to screenshots/ directory")
        print("  2. Set ANTHROPIC_API_KEY environment variable")
        print("  3. Run: python batch_test.py")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
