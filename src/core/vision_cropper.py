"""
AI vision-based panel detection using Claude API
"""
import anthropic
import base64
import json
import re
from typing import Dict, Optional, Tuple

from .layout import DashboardLayout, parse_panel_id, get_row_position, get_position_info
from .image_ops import crop_image


class VisionPanelCropper:
    """Crop panels using Claude Vision API for intelligent detection"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def identify_with_layout(
        self,
        image_data: bytes,
        layout: DashboardLayout,
        panel_id: str
    ) -> Optional[Dict[str, int]]:
        """
        Use Claude Vision with layout context to identify panel boundaries

        Args:
            image_data: Image bytes
            layout: Dashboard layout object
            panel_id: Panel ID to locate (e.g., 'S1-L-write')

        Returns:
            Dict with keys: x, y, width, height (in pixels), or None if not found
        """
        panel = layout.get_panel(panel_id)
        if not panel:
            raise ValueError(f"Panel '{panel_id}' not found in layout")

        parsed = parse_panel_id(panel_id)
        row_num = get_row_position(parsed['row'])
        position_info = get_position_info(parsed['position'])
        row = layout.get_row(parsed['row'])
        row_title = row.title if row else ""

        prompt = self._build_layout_prompt(
            layout, panel_id, row_num, row_title, parsed, position_info
        )

        return self._detect_panel(image_data, prompt)

    def identify_without_layout(
        self,
        image_data: bytes,
        panel_id: str
    ) -> Optional[Dict[str, int]]:
        """
        Use Claude Vision without layout context (pure vision-based)

        Args:
            image_data: Image bytes
            panel_id: Panel ID to locate (e.g., 'S1-L-1')

        Returns:
            Dict with keys: x, y, width, height (in pixels), or None if not found
        """
        parsed = parse_panel_id(panel_id)
        row_num = get_row_position(parsed['row'])
        position_info = get_position_info(parsed['position'])

        prompt = self._build_vision_only_prompt(row_num, position_info)

        return self._detect_panel(image_data, prompt)

    def crop_panel(
        self,
        image_data: bytes,
        layout: Optional[DashboardLayout],
        panel_id: str,
        use_layout: bool = True
    ) -> Tuple[bytes, Dict]:
        """
        Complete pipeline: identify and crop a panel

        Args:
            image_data: Dashboard screenshot bytes
            layout: Dashboard layout object (can be None if use_layout=False)
            panel_id: Panel ID to crop
            use_layout: If True, use layout context; if False, use pure vision

        Returns:
            Tuple of (cropped_image_bytes, metadata_dict)
        """
        # Identify boundaries
        if use_layout:
            boundaries = self.identify_with_layout(image_data, layout, panel_id)
        else:
            boundaries = self.identify_without_layout(image_data, panel_id)

        if not boundaries:
            raise ValueError(f"Could not identify panel '{panel_id}'")

        # Crop the image
        cropped_image = crop_image(image_data, boundaries)

        # Prepare metadata
        if use_layout and layout:
            panel = layout.get_panel(panel_id)
            panel_role = panel.role if panel else 'unknown'
        else:
            panel_role = 'detected_without_layout'

        metadata = {
            'panel_id': panel_id,
            'panel_role': panel_role,
            'boundaries': boundaries,
            'confidence': boundaries.get('confidence', 'unknown'),
            'notes': boundaries.get('notes', ''),
            'used_layout': use_layout
        }

        return cropped_image, metadata

    def _detect_panel(self, image_data: bytes, prompt: str) -> Optional[Dict[str, int]]:
        """Call Claude API to detect panel boundaries"""
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
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
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            result = json.loads(response_text)

            if result.get('found'):
                return {
                    'x': result['x'],
                    'y': result['y'],
                    'width': result['width'],
                    'height': result['height'],
                    'confidence': result.get('confidence', 'unknown'),
                    'notes': result.get('notes', '')
                }
            else:
                raise ValueError(f"Panel not found: {result.get('reason', 'Unknown')}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise ValueError(f"Failed to identify panel: {str(e)}")

    def _build_layout_prompt(self, layout, panel_id, row_num, row_title, parsed, position_info):
        """Build prompt with layout context"""
        dashboard_context = f"""
Dashboard: {layout.human_name}
Total Rows: {len(layout.rows)}
Layout: {' | '.join(layout.layout_description)}
"""

        panel_context = f"""
Target Panel ID: {panel_id}
Row Number: {row_num} (ID: {parsed['row']})
Row Title: {row_title}
Position: {parsed['position']} ({position_info['side']}, index {position_info['index']})
"""

        return f"""Identify the bounding box coordinates of a specific panel in this dashboard.

{dashboard_context}
{panel_context}

Instructions:
1. Locate row {row_num} (title: "{row_title}")
2. Find panel at position {parsed['position']} ({position_info['side']}, index {position_info['index']})
3. Identify precise bounding box (x, y, width, height) in pixels
4. Include graph/chart area and legends, exclude excessive whitespace
5. Respond ONLY with JSON: {{"found": true, "x": N, "y": N, "width": N, "height": N, "confidence": "high|medium|low", "notes": "..."}}

If not found: {{"found": false, "reason": "..."}}"""

    def _build_vision_only_prompt(self, row_num, position_info):
        """Build prompt without layout context"""
        return f"""Identify a specific panel in this dashboard using only visual analysis.

Target: Row {row_num}, {position_info['side']} side, position {position_info['index'] + 1}

Instructions:
1. Visually identify all rows (separated by whitespace or titles)
2. Count from top to find row {row_num}
3. Identify panels on the {position_info['side']} side
4. Select panel at position {position_info['index'] + 1}
5. Identify precise bounding box (x, y, width, height) in pixels
6. Include graph/chart and legends, exclude excessive whitespace
7. Respond ONLY with JSON: {{"found": true, "x": N, "y": N, "width": N, "height": N, "confidence": "high|medium|low", "notes": "..."}}

If not found: {{"found": false, "reason": "..."}}"""
