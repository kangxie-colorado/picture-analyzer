"""
CLI tool for dashboard risk analysis
Analyzes Grafana dashboards for potential risk indicators
"""
import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.risk_analyzer import RiskAnalyzer


def main():
    """Main entry point for risk analysis CLI"""
    parser = argparse.ArgumentParser(
        description='Analyze Grafana dashboard screenshots for risk indicators',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a dashboard with default output
  python -m src.cli.analyze_risk screenshots/dashboard.png abase-risk-analysis

  # Analyze specific panels only
  python -m src.cli.analyze_risk screenshots/dashboard.png abase-risk-analysis \\
    --panels S1-L-read S1-L-write

  # Extract panels to specific directory
  python -m src.cli.analyze_risk screenshots/dashboard.png abase-risk-analysis \\
    --output-dir outputs/risk-analysis

  # Generate analysis context as JSON
  python -m src.cli.analyze_risk screenshots/dashboard.png abase-risk-analysis \\
    --format json --output context.json

Dashboard names should match directory names in config/dashboards/
        """
    )

    parser.add_argument(
        'image',
        help='Path to dashboard screenshot'
    )

    parser.add_argument(
        'dashboard',
        help='Dashboard name (matches config/dashboards/<name>)'
    )

    parser.add_argument(
        '--panels',
        nargs='+',
        help='Specific panel IDs to analyze (default: all panels)'
    )

    parser.add_argument(
        '--output-dir',
        help='Directory to save extracted panel images (default: temp directory)'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Path to save analysis context report'
    )

    parser.add_argument(
        '--format',
        choices=['yaml', 'json'],
        default='yaml',
        help='Output format for analysis report (default: yaml)'
    )

    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='Only extract panels without generating analysis context'
    )

    parser.add_argument(
        '--list-panels',
        action='store_true',
        help='List available panels and exit'
    )

    args = parser.parse_args()

    # Build coordinates path
    coordinates_path = Path('config/dashboards') / args.dashboard / 'coordinates.yaml'

    if not coordinates_path.exists():
        print(f"Error: Coordinates file not found: {coordinates_path}")
        print(f"\nAvailable dashboards:")
        dashboards_dir = Path('config/dashboards')
        if dashboards_dir.exists():
            for dash_dir in dashboards_dir.iterdir():
                if dash_dir.is_dir():
                    coord_file = dash_dir / 'coordinates.yaml'
                    if coord_file.exists():
                        print(f"  - {dash_dir.name}")
        sys.exit(1)

    # Initialize analyzer
    try:
        analyzer = RiskAnalyzer(str(coordinates_path))
    except Exception as e:
        print(f"Error initializing analyzer: {e}")
        sys.exit(1)

    # Handle list panels request
    if args.list_panels:
        print(f"Available panels in '{args.dashboard}':")
        for panel_id in analyzer.cropper.get_panel_ids():
            metadata = analyzer.get_panel_metadata(panel_id)
            desc = metadata.get('description', 'No description')
            print(f"  {panel_id:20s} - {desc}")
        sys.exit(0)

    # Verify image exists
    if not Path(args.image).exists():
        print(f"Error: Image file not found: {args.image}")
        sys.exit(1)

    # Extract panels
    if args.extract_only:
        print(f"Extracting panels from {args.image}...")
        results = analyzer.extract_panels_for_analysis(
            args.image,
            output_dir=args.output_dir,
            panels=args.panels
        )

        print(f"\nExtracted {len(results['panels'])} panels:")
        for panel in results['panels']:
            if 'error' in panel:
                print(f"  ✗ {panel['panel_id']}: {panel['error']}")
            else:
                print(f"  ✓ {panel['panel_id']} → {panel['cropped_image_path']}")

        print(f"\nOutput directory: {results['output_dir']}")
        sys.exit(0)

    # Generate analysis context
    print(f"Generating analysis context for {args.image}...")
    try:
        context = analyzer.generate_analysis_context(
            args.image,
            panel_ids=args.panels
        )

        # Display summary
        print(f"\nDashboard: {context['dashboard_name']}")
        print(f"Total panels: {context['total_panels']}")
        print("\nPanel Summary:")

        for panel in context['panels']:
            if 'error' in panel:
                print(f"  ✗ {panel['panel_id']}: {panel['error']}")
                continue

            print(f"\n  Panel: {panel['panel_id']}")
            print(f"    Type: {panel['type']}")
            print(f"    Description: {panel['description']}")
            print(f"    Image: {panel['image_path']}")
            print(f"    Risk Indicators to Check:")
            for indicator in panel['risk_indicators']:
                print(f"      - {indicator}")

        # Save report if requested
        if args.output:
            analyzer.save_analysis_report(context, args.output, format=args.format)
            print(f"\n✓ Analysis context saved to: {args.output}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
