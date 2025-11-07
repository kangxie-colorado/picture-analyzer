"""
Risk analysis module - Analyze dashboard panels for risk indicators
Uses panel cropping and vision analysis to identify potential issues
"""
import yaml
from PIL import Image
from typing import Dict, List, Optional
from pathlib import Path
from .panel_cropper import PanelCropper


class RiskAnalyzer:
    """Analyze dashboard panels for risk indicators"""

    def __init__(self, coordinates_path: str):
        """
        Initialize risk analyzer with coordinates file

        Args:
            coordinates_path: Path to coordinates.yaml file
        """
        self.cropper = PanelCropper(coordinates_path)
        self.coordinates_path = coordinates_path
        self.dashboard_name = self.cropper.coordinates.get('dashboard', 'unknown')

    def get_panel_metadata(self, panel_id: str) -> Dict:
        """
        Get metadata about a specific panel

        Args:
            panel_id: Panel identifier (e.g., 'S1-L-read')

        Returns:
            Dict containing panel metadata including description
        """
        panels = self.cropper.coordinates.get('panels', {})
        if panel_id not in panels:
            return {'panel_id': panel_id, 'error': 'Panel not found'}

        panel_data = panels[panel_id]

        # Extract comment/description if present
        description = None
        if isinstance(panel_data, dict):
            # Look for comment marker in raw YAML
            with open(self.coordinates_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find panel section and extract comment
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if f'{panel_id}:' in line:
                        # Check next line for comment
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line.startswith('#'):
                                description = next_line.lstrip('#').strip()
                        break

        return {
            'panel_id': panel_id,
            'description': description,
            'coordinates': {
                'x': panel_data.get('x', 0),
                'y': panel_data.get('y', 0),
                'width': panel_data.get('width', 0),
                'height': panel_data.get('height', 0)
            }
        }

    def extract_panels_for_analysis(
        self,
        image_path: str,
        output_dir: str = None,
        panels: Optional[List[str]] = None
    ) -> Dict:
        """
        Extract panels from dashboard for analysis

        Args:
            image_path: Path to dashboard screenshot
            output_dir: Optional directory to save cropped panels
            panels: Optional list of specific panel IDs to extract (default: all)

        Returns:
            Dict with extraction results and panel metadata
        """
        import os
        import tempfile

        # Use temp directory if no output specified
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='risk_analysis_')

        os.makedirs(output_dir, exist_ok=True)

        # Get panel IDs to process
        panel_ids = panels if panels else self.cropper.get_panel_ids()

        results = {
            'dashboard': self.dashboard_name,
            'source_image': image_path,
            'output_dir': output_dir,
            'panels': []
        }

        # Extract each panel
        for panel_id in panel_ids:
            try:
                # Get panel metadata
                metadata = self.get_panel_metadata(panel_id)

                # Crop panel
                output_path = os.path.join(
                    output_dir,
                    f"{self.dashboard_name}_{panel_id.lower()}.png"
                )

                panel_image, crop_metadata = self.cropper.crop_panel(
                    image_path,
                    panel_id,
                    output_path
                )

                # Combine metadata
                panel_info = {
                    **metadata,
                    'cropped_image_path': output_path,
                    'dimensions': crop_metadata['dimensions']
                }

                results['panels'].append(panel_info)

            except Exception as e:
                results['panels'].append({
                    'panel_id': panel_id,
                    'error': str(e)
                })

        return results

    def generate_analysis_context(
        self,
        image_path: str,
        panel_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate context information for LLM-based risk analysis

        Args:
            image_path: Path to dashboard screenshot
            panel_ids: Optional list of specific panel IDs to analyze

        Returns:
            Dict containing analysis context and panel information
        """
        # Extract panels
        extraction_results = self.extract_panels_for_analysis(
            image_path,
            panels=panel_ids
        )

        # Build analysis context
        context = {
            'dashboard_name': self.dashboard_name,
            'image_path': image_path,
            'total_panels': len(extraction_results['panels']),
            'panels': []
        }

        # Add panel-specific context
        for panel_info in extraction_results['panels']:
            if 'error' in panel_info:
                context['panels'].append(panel_info)
                continue

            # Categorize panel by type (read, write, disk, qps, hotkey, etc.)
            panel_id = panel_info['panel_id']
            panel_type = self._categorize_panel(panel_id, panel_info.get('description', ''))

            context['panels'].append({
                'panel_id': panel_id,
                'description': panel_info.get('description', 'No description'),
                'type': panel_type,
                'image_path': panel_info.get('cropped_image_path'),
                'risk_indicators': self._get_risk_indicators_for_type(panel_type)
            })

        return context

    def _categorize_panel(self, panel_id: str, description: str) -> str:
        """Categorize panel by its type based on ID and description"""
        panel_id_lower = panel_id.lower()
        desc_lower = description.lower() if description else ''

        if 'read' in panel_id_lower or '读' in desc_lower:
            return 'read_capacity'
        elif 'write' in panel_id_lower or '写' in desc_lower:
            return 'write_capacity'
        elif 'disk' in panel_id_lower or 'storage' in desc_lower:
            return 'storage'
        elif 'partition' in desc_lower:
            return 'partition'
        elif 'qps' in panel_id_lower or 'qps' in desc_lower:
            return 'qps_quota'
        elif 'hotkey' in panel_id_lower or '热key' in desc_lower:
            return 'hotkey'
        elif 'value_size' in panel_id_lower or 'value size' in desc_lower:
            return 'value_size'
        else:
            return 'other'

    def _get_risk_indicators_for_type(self, panel_type: str) -> List[str]:
        """Get relevant risk indicators for a panel type"""
        indicators = {
            'read_capacity': [
                'Current usage approaching quota/limit',
                'Sudden spikes or unusual patterns',
                'Consistent near-limit operation',
                'Cross-DC imbalances'
            ],
            'write_capacity': [
                'Current usage approaching quota/limit',
                'Write throttling indicators',
                'Sustained high write rates',
                'DC-level imbalances'
            ],
            'storage': [
                'Disk usage above 80%',
                'Rapid growth trends',
                'Top tables consuming excessive space',
                'Low remaining capacity'
            ],
            'partition': [
                'Partitions near capacity limits',
                'Uneven distribution across partitions',
                'Individual partition saturation'
            ],
            'qps_quota': [
                'QPS approaching or exceeding quota',
                'Quota violations',
                'Traffic concentration on specific shards'
            ],
            'hotkey': [
                'Presence of hot keys',
                'High RU consumption by specific keys',
                'Uneven access patterns'
            ],
            'value_size': [
                'Large value sizes indicating inefficient data structure',
                'Values approaching size limits',
                'Anomalous size patterns per DC'
            ]
        }

        return indicators.get(panel_type, [
            'Unusual patterns or anomalies',
            'Values approaching limits',
            'Sudden changes or spikes'
        ])

    def save_analysis_report(
        self,
        analysis_results: Dict,
        output_path: str,
        format: str = 'yaml'
    ):
        """
        Save analysis results to file

        Args:
            analysis_results: Analysis results dictionary
            output_path: Path to save report
            format: Output format ('yaml' or 'json')
        """
        import json

        if format == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    analysis_results,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False
                )
        elif format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
