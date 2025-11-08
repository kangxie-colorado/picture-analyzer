"""
Panel cropping module - Extract individual panels from dashboard screenshots
Uses coordinates from coordinates.yaml to crop precise panel boundaries
"""
import yaml
from PIL import Image
from typing import Dict, List, Tuple
from pathlib import Path


class PanelCropper:
    """Crop dashboard panels using coordinate-based boundaries"""

    def __init__(self, coordinates_path: str):
        """
        Initialize cropper with coordinates file

        Args:
            coordinates_path: Path to coordinates.yaml file
        """
        self.coordinates_path = coordinates_path
        self.coordinates = self._load_coordinates()

    def _load_coordinates(self) -> Dict:
        """Load and parse coordinates.yaml"""
        with open(self.coordinates_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if 'panels' not in data:
            raise ValueError(f"No 'panels' section found in {self.coordinates_path}")

        return data

    def get_panel_ids(self) -> List[str]:
        """Get list of all panel IDs"""
        return list(self.coordinates['panels'].keys())

    def get_image_dimensions(self) -> Tuple[int, int]:
        """Get expected image dimensions (width, height)"""
        dims = self.coordinates.get('image_dimensions', {})
        return dims.get('width', 0), dims.get('height', 0)

    def crop_panel(
        self,
        image_path: str,
        panel_id: str,
        output_path: str = None
    ) -> Tuple[Image.Image, Dict]:
        """
        Crop a single panel from dashboard image

        Args:
            image_path: Path to dashboard screenshot
            panel_id: Panel ID to crop (e.g., 'S1-L-write')
            output_path: Optional path to save cropped image

        Returns:
            Tuple of (PIL Image, metadata dict)
        """
        # Load dashboard image
        dashboard = Image.open(image_path)

        # Get panel coordinates
        panels = self.coordinates.get('panels', {})
        if panel_id not in panels:
            available = ', '.join(panels.keys())
            raise ValueError(
                f"Panel '{panel_id}' not found. "
                f"Available panels: {available}"
            )

        coords = panels[panel_id]
        x = coords['x']
        y = coords['y']
        width = coords['width']
        height = coords['height']

        # Crop panel (PIL uses: left, upper, right, lower)
        box = (x, y, x + width, y + height)
        panel_image = dashboard.crop(box)

        # Build metadata
        metadata = {
            'panel_id': panel_id,
            'source_image': image_path,
            'coordinates': {
                'x': x,
                'y': y,
                'width': width,
                'height': height
            },
            'dimensions': {
                'width': panel_image.width,
                'height': panel_image.height
            }
        }

        # Save if output path provided
        if output_path:
            panel_image.save(output_path)
            metadata['output_path'] = output_path

        return panel_image, metadata

    def crop_all_panels(
        self,
        image_path: str,
        output_dir: str,
        filename_pattern: str = "{dashboard}_{panel_id}.png"
    ) -> List[Dict]:
        """
        Crop all panels from dashboard image

        Args:
            image_path: Path to dashboard screenshot
            output_dir: Directory to save cropped panels
            filename_pattern: Filename pattern with {dashboard} and {panel_id} placeholders

        Returns:
            List of metadata dicts for each cropped panel
        """
        import os

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get dashboard name
        dashboard_name = self.coordinates.get('dashboard', 'dashboard')

        results = []

        # Crop each panel
        for panel_id in self.get_panel_ids():
            # Build output filename
            filename = filename_pattern.format(
                dashboard=dashboard_name,
                panel_id=panel_id.lower()
            )
            output_path = os.path.join(output_dir, filename)

            # Crop panel
            try:
                _, metadata = self.crop_panel(image_path, panel_id, output_path)
                results.append(metadata)
                print(f"  ✓ {panel_id} → {filename}")
            except Exception as e:
                print(f"  ✗ {panel_id}: {str(e)}")
                results.append({
                    'panel_id': panel_id,
                    'error': str(e)
                })

        return results

    def verify_coordinates(self, image_path: str) -> Dict:
        """
        Verify that coordinates are valid for the given image

        Args:
            image_path: Path to dashboard screenshot

        Returns:
            Dict with verification results
        """
        dashboard = Image.open(image_path)
        img_width, img_height = dashboard.size

        # Expected dimensions from coordinates
        expected_width, expected_height = self.get_image_dimensions()

        results = {
            'image_dimensions': {'width': img_width, 'height': img_height},
            'expected_dimensions': {'width': expected_width, 'height': expected_height},
            'dimensions_match': (img_width == expected_width and img_height == expected_height),
            'panel_checks': []
        }

        # Check each panel
        panels = self.coordinates.get('panels', {})
        for panel_id, coords in panels.items():
            x = coords['x']
            y = coords['y']
            width = coords['width']
            height = coords['height']

            issues = []

            if x < 0 or y < 0:
                issues.append("Negative coordinates")

            if x + width > img_width:
                issues.append(f"Extends beyond image width ({x + width} > {img_width})")

            if y + height > img_height:
                issues.append(f"Extends beyond image height ({y + height} > {img_height})")

            results['panel_checks'].append({
                'panel_id': panel_id,
                'valid': len(issues) == 0,
                'issues': issues
            })

        return results
