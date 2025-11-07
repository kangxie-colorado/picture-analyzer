"""
Dashboard structure analyzer using Claude Vision API
Extracts panel coordinates and dashboard metadata from screenshots
"""
import anthropic
import base64
import json
import yaml
import re
from typing import Dict, List, Tuple, Optional
from PIL import Image
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Validation result for generated configs"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class DashboardAnalyzer:
    """Analyze dashboard screenshots to extract structure and coordinates"""

    def __init__(self, api_key: str):
        """Initialize analyzer with Anthropic API key"""
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze_dashboard(
        self,
        image_path: str,
        dashboard_name: Optional[str] = None
    ) -> Dict:
        """
        Analyze dashboard screenshot and extract complete structure

        Args:
            image_path: Path to dashboard screenshot
            dashboard_name: Optional dashboard name

        Returns:
            Dict with analysis results including panels, rows, and metadata
        """
        # Load image and get dimensions
        img = Image.open(image_path)
        width, height = img.width, img.height

        # Read image data
        with open(image_path, 'rb') as f:
            image_data = f.read()

        print(f"📊 Analyzing dashboard: {width}x{height} pixels")

        # Extract structure using Claude Vision API
        analysis_result = self._call_vision_api(
            image_data, width, height, dashboard_name
        )

        # Add image dimensions to result
        analysis_result['image_dimensions'] = {
            'width': width,
            'height': height
        }

        return analysis_result

    def _call_vision_api(
        self,
        image_data: bytes,
        width: int,
        height: int,
        dashboard_name: Optional[str] = None
    ) -> Dict:
        """Call Claude Vision API to extract dashboard information"""

        prompt = self._build_prompt(width, height, dashboard_name)
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')

        print("🤖 Calling Claude Vision API...")

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        try:
            result = json.loads(response_text)
            print("✓ Successfully extracted dashboard structure")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse API response: {str(e)}\n"
                f"Response preview: {response_text[:500]}"
            )

    def _build_prompt(
        self,
        width: int,
        height: int,
        dashboard_name: Optional[str] = None
    ) -> str:
        """Build analysis prompt for Claude Vision API"""

        name_hint = f" (name: {dashboard_name})" if dashboard_name else ""

        return f"""Analyze this Grafana dashboard screenshot{name_hint} and extract complete structural information.

Image dimensions: {width}x{height} pixels

Extract:

1. **Panel coordinates** - PRECISE bounding boxes (x, y, width, height in pixels)
   - x, y: top-left corner position
   - width, height: panel dimensions
   - Include title, graph, legends, axes
   - Exclude whitespace between panels
   - Target accuracy: ±5 pixels

2. **Dashboard structure**:
   - Number of rows/sections
   - Panel arrangement per row
   - Layout pattern

3. **Panel information**:
   - Titles (visible text)
   - What each panel shows
   - Row position

4. **Analysis context**:
   - Monitoring purpose
   - Key metrics
   - Risk analysis relevance

**Panel ID pattern**: `S{{row}}-{{pos}}-{{name}}`
- Row: S1, S2, S3... (top to bottom)
- Position: L, R, L2, R2... (left/right, 2nd=second in same column)
- Name: keyword (write, read, qps, disk)

Examples: "S1-L-write", "S1-R-read", "S2-L-disk", "S3-L2-value_size"

**Return JSON**:
{{{{
  "dashboard_name": "Detected name",
  "dashboard_id": "kebab-case-id",
  "total_rows": 3,
  "total_panels": 9,
  "layout_pattern": "Layout description",
  "panels": [
    {{{{
      "id": "S1-L-write",
      "x": 30,
      "y": 250,
      "width": 615,
      "height": 153,
      "title": "Panel title",
      "description": "What this shows",
      "row_number": 1,
      "position": "left",
      "role": "global_capacity_headroom"
    }}}}
  ],
  "rows": [
    {{{{
      "id": "S1",
      "title": "Row title or description",
      "intent": "What this row monitors",
      "panel_count": 4,
      "panel_ids": ["S1-L-write", "S1-R-write", "S1-L-read", "S1-R-read"]
    }}}}
  ],
  "layout_description": ["Layout point 1", "Layout point 2"],
  "analysis_objectives": ["Objective 1", "Objective 2"],
  "analysis_tips": ["Tip 1", "Tip 2"]
}}}}

CRITICAL:
- Coordinates must be PRECISE (measure carefully)
- Include ALL visible panels
- Panel IDs must be systematic
- Return ONLY valid JSON"""

    def validate_analysis(
        self,
        analysis: Dict
    ) -> ValidationResult:
        """Validate analysis results for correctness and completeness"""

        errors = []
        warnings = []
        info = []

        width = analysis.get('image_dimensions', {}).get('width', 0)
        height = analysis.get('image_dimensions', {}).get('height', 0)

        # Validate coordinates
        for panel in analysis.get('panels', []):
            panel_id = panel.get('id', 'unknown')
            x, y = panel.get('x', 0), panel.get('y', 0)
            w, h = panel.get('width', 0), panel.get('height', 0)

            # Check bounds
            if x < 0 or y < 0:
                errors.append(f"{panel_id}: Negative coordinates ({x}, {y})")

            if x + w > width:
                errors.append(f"{panel_id}: Extends beyond image width")

            if y + h > height:
                errors.append(f"{panel_id}: Extends beyond image height")

            # Check reasonable sizes
            if w < 50 or h < 50:
                warnings.append(f"{panel_id}: Very small panel ({w}x{h})")

        # Check for overlaps
        panels = analysis.get('panels', [])
        for i, p1 in enumerate(panels):
            for p2 in panels[i+1:]:
                if self._panels_overlap(p1, p2):
                    warnings.append(
                        f"Panels {p1['id']} and {p2['id']} overlap"
                    )

        # Validate structure
        if not analysis.get('rows'):
            errors.append("No rows defined")

        if not analysis.get('panels'):
            errors.append("No panels detected")

        # Check ID patterns
        for panel in analysis.get('panels', []):
            if not re.match(r'S\d+-[LR]\d*-\w+', panel.get('id', '')):
                warnings.append(
                    f"Panel ID {panel.get('id')} doesn't match pattern"
                )

        # Info messages
        info.append(f"Image dimensions: {width}x{height}")
        info.append(f"Panels detected: {len(panels)}")
        info.append(f"Rows detected: {len(analysis.get('rows', []))}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def _panels_overlap(self, p1: Dict, p2: Dict) -> bool:
        """Check if two panels overlap"""
        x1, y1 = p1['x'], p1['y']
        w1, h1 = p1['width'], p1['height']
        x2, y2 = p2['x'], p2['y']
        w2, h2 = p2['width'], p2['height']

        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or
                    y1 + h1 <= y2 or y2 + h2 <= y1)

    def export_coordinates_yaml(self, analysis: Dict, output_path: str):
        """Export coordinates to YAML format"""

        dashboard_id = analysis.get('dashboard_id', 'unknown')
        dims = analysis.get('image_dimensions', {})

        lines = [
            f"dashboard: {dashboard_id}",
            "version: '1.0'",
            "description: Pixel-based panel coordinates (no LLM required for cropping)",
            "image_dimensions:",
            f"  width: {dims.get('width', 0)}",
            f"  height: {dims.get('height', 0)}",
            "",
            "note: |",
            "  These coordinates were extracted using AI vision analysis.",
            "  They should work for all screenshots with the same dashboard layout and resolution.",
            "",
            "panels:"
        ]

        for panel in analysis.get('panels', []):
            lines.append(f"  {panel['id']}:")
            title = panel.get('title', '')
            if title:
                lines.append(f"    # {title}")
            lines.append(f"    x: {panel['x']}")
            lines.append(f"    y: {panel['y']}")
            lines.append(f"    width: {panel['width']}")
            lines.append(f"    height: {panel['height']}")
            lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✓ Saved: {output_path}")

    def export_static_pack_yaml(self, analysis: Dict, output_path: str):
        """Export dashboard structure to static_pack.yaml"""

        # Build rows with panels
        rows = []
        for row in analysis.get('rows', []):
            panels = []
            for panel_id in row.get('panel_ids', []):
                # Find panel details
                panel_data = next(
                    (p for p in analysis.get('panels', [])
                     if p['id'] == panel_id),
                    None
                )

                panel_entry = {'id': panel_id}
                if panel_data:
                    panel_entry['role'] = panel_data.get('role', 'monitoring')
                    if panel_data.get('position'):
                        panel_entry['source'] = panel_data['position']

                panels.append(panel_entry)

            rows.append({
                'id': row['id'],
                'title': row['title'],
                'intent': row['intent'],
                'panels': panels,
                'relationships': []
            })

        static_pack = {
            'schema_version': 1,
            'dashboard_static': {
                'id': analysis.get('dashboard_id', 'unknown'),
                'human_name': analysis.get('dashboard_name', 'Unknown'),
                'layout_description': analysis.get('layout_description', []),
                'analysis_objectives': analysis.get('analysis_objectives', []),
                'analysis_tips': analysis.get('analysis_tips', []),
                'rows': rows,
                'identifiers': {
                    'row_id_pattern': 'S{n}',
                    'panel_id_pattern': 'S{n}-{position}-{name}'
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(static_pack, f, default_flow_style=False,
                     allow_unicode=True, sort_keys=False)

        print(f"✓ Saved: {output_path}")

    def export_run_pack_json(self, analysis: Dict, output_path: str):
        """Export runtime configuration template"""

        run_pack = {
            "schema_version": 1,
            "_about_run_pack": "Runtime parameters for dashboard analysis. Template placeholders ({{var-*}}) should be replaced with actual values from Grafana URL parameters.",
            "run_pack": {
                "time_window": {
                    "start": "{{var-time_start_iso8601}}",
                    "end": "{{var-time_end_iso8601}}",
                    "tz": "{{var-timezone}}"
                },
                "scope": {
                    "cluster": "{{var-cluster}}",
                    "namespace": "{{var-namespace}}",
                    "table": "{{var-table}}",
                    "region_selector": "{{var-region}}"
                },
                "controls": {
                    "downsampling": "{{var-downsampling}}",
                    "topN": "{{var-topN}}"
                },
                "output_format": {
                    "language": "用中文回答 (Answer in Chinese)",
                    "format": "Return response content as structured JSON object (not markdown string)",
                    "verbosity": "Make sure the response contains the resource identities",
                    "json_schema": {
                        "summary": "string - 1-2 paragraph summary in Chinese",
                        "findings": "array of strings - key findings",
                        "risks": "array of risk objects - title, severity, description, location, bounding_box",
                        "correlations": "array of strings - metric relationships",
                        "next_steps": "array of strings - recommended actions",
                        "title": "string - short descriptive title (max 10 words)",
                        "dashboard_understanding": {
                            "purpose": "AI's understanding of dashboard purpose",
                            "summary": "Dashboard summary",
                            "rows": "Description of rows and panels"
                        }
                    }
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(run_pack, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved: {output_path}")
