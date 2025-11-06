"""
Fast coordinate-based panel cropping (no LLM required)
"""
import yaml
from typing import Dict, Optional
from pathlib import Path

from .image_ops import crop_image


class CoordinatePanelCropper:
    """Crop panels using pre-defined pixel coordinates"""

    def __init__(self, dashboard_name: str, config_dir: str = "config/dashboards"):
        self.dashboard_name = dashboard_name
        self.config_dir = config_dir
        self.coordinates = self._load_coordinates()

    def _load_coordinates(self) -> Dict:
        """Load coordinate configuration from YAML file"""
        config_path = Path(self.config_dir) / self.dashboard_name / "coordinates.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Coordinates file not found: {config_path}\n"
                f"Run 'analyze-layout' command to generate it."
            )

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def get_panel_coordinates(self, panel_id: str) -> Optional[Dict[str, int]]:
        """Get coordinates for a specific panel"""
        panels = self.coordinates.get('panels', {})
        return panels.get(panel_id)

    def list_panels(self) -> Dict[str, Dict[str, int]]:
        """List all available panels and their coordinates"""
        return self.coordinates.get('panels', {})

    def crop_panel(self, image_data: bytes, panel_id: str) -> tuple[bytes, Dict]:
        """
        Crop a panel using pre-defined coordinates

        Args:
            image_data: Dashboard screenshot bytes
            panel_id: Panel ID to crop

        Returns:
            Tuple of (cropped_image_bytes, metadata_dict)
        """
        coords = self.get_panel_coordinates(panel_id)

        if not coords:
            available = ', '.join(self.list_panels().keys())
            raise ValueError(
                f"Panel '{panel_id}' not found in configuration.\n"
                f"Available panels: {available}"
            )

        # Crop the image
        cropped_image = crop_image(image_data, coords)

        # Metadata
        metadata = {
            'panel_id': panel_id,
            'method': 'coordinate_based',
            'boundaries': coords,
            'dashboard': self.dashboard_name
        }

        return cropped_image, metadata

    def crop_all_panels(self, image_data: bytes) -> Dict[str, tuple[bytes, Dict]]:
        """
        Crop all panels from a screenshot

        Args:
            image_data: Dashboard screenshot bytes

        Returns:
            Dict mapping panel_id to (cropped_image_bytes, metadata)
        """
        results = {}

        for panel_id in self.list_panels().keys():
            try:
                cropped, metadata = self.crop_panel(image_data, panel_id)
                results[panel_id] = (cropped, metadata)
            except Exception as e:
                results[panel_id] = (None, {'error': str(e)})

        return results
