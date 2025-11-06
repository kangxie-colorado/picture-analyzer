"""
Panel cropper using Claude Vision API to identify and crop dashboard panels
"""
import anthropic
import base64
import json
import re
from PIL import Image
from io import BytesIO
from typing import Dict, Tuple, Optional
from dashboard_layout import DashboardLayout, parse_panel_id, get_row_position, get_position_info


class PanelCropper:
    """Crop panels from dashboard screenshots using AI vision"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def identify_panel_boundaries(
        self,
        image_data: bytes,
        layout: DashboardLayout,
        panel_id: str
    ) -> Optional[Dict[str, int]]:
        """
        Use Claude Vision to identify the bounding box of a specific panel

        Args:
            image_data: Image bytes
            layout: Dashboard layout object
            panel_id: Panel ID to locate (e.g., 'S1-L-write')

        Returns:
            Dict with keys: x, y, width, height (in pixels), or None if not found
        """
        # Get panel info
        panel = layout.get_panel(panel_id)
        if not panel:
            raise ValueError(f"Panel '{panel_id}' not found in layout")

        # Parse panel ID for context
        parsed = parse_panel_id(panel_id)
        row_num = get_row_position(parsed['row'])
        position_info = get_position_info(parsed['position'])

        # Get row info
        row = layout.get_row(parsed['row'])
        row_title = row.title if row else ""

        # Build context about the dashboard
        dashboard_context = f"""
Dashboard: {layout.human_name}
Total Rows: {len(layout.rows)}
Layout: {' | '.join(layout.layout_description)}
"""

        # Build context about the target panel
        panel_context = f"""
Target Panel ID: {panel_id}
Row Number: {row_num} (ID: {parsed['row']})
Row Title: {row_title}
Position: {parsed['position']} ({position_info['side']}, index {position_info['index']})
Panel Role: {panel.role}
"""

        # Encode image
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')

        # Create the prompt
        prompt = f"""I need you to identify the bounding box coordinates of a specific panel in this dashboard screenshot.

{dashboard_context}

{panel_context}

Instructions:
1. Locate row {row_num} (the row with title: "{row_title}")
2. Within that row, find the panel at position {parsed['position']} ({position_info['side']} side, index {position_info['index']})
3. Identify the precise bounding box (x, y, width, height) of this panel in pixels
4. The bounding box should include the graph/chart area and any legends, but not excessive whitespace
5. Respond ONLY with a JSON object in this exact format:

{{
  "found": true,
  "x": <left coordinate in pixels>,
  "y": <top coordinate in pixels>,
  "width": <width in pixels>,
  "height": <height in pixels>,
  "confidence": "<high|medium|low>",
  "notes": "<brief description of what you found>"
}}

If you cannot confidently identify the panel, respond with:
{{
  "found": false,
  "reason": "<explanation>"
}}

IMPORTANT: Respond with ONLY the JSON object, no other text."""

        # Call Claude API
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

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON from response (in case there's extra text)
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
                raise ValueError(f"Panel not found: {result.get('reason', 'Unknown reason')}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise ValueError(f"Failed to identify panel boundaries: {str(e)}")

    def crop_panel(
        self,
        image_data: bytes,
        boundaries: Dict[str, int]
    ) -> bytes:
        """
        Crop an image based on bounding box coordinates

        Args:
            image_data: Original image bytes
            boundaries: Dict with x, y, width, height

        Returns:
            Cropped image bytes (PNG format)
        """
        # Open image
        image = Image.open(BytesIO(image_data))

        # Extract coordinates
        left = boundaries['x']
        top = boundaries['y']
        right = left + boundaries['width']
        bottom = top + boundaries['height']

        # Ensure coordinates are within image bounds
        left = max(0, left)
        top = max(0, top)
        right = min(image.width, right)
        bottom = min(image.height, bottom)

        # Crop
        cropped = image.crop((left, top, right, bottom))

        # Convert to bytes
        output = BytesIO()
        cropped.save(output, format='PNG')
        return output.getvalue()

    def identify_panel_boundaries_without_layout(
        self,
        image_data: bytes,
        panel_id: str
    ) -> Optional[Dict[str, int]]:
        """
        Use Claude Vision to identify panel boundaries WITHOUT layout context
        (pure vision-based detection)

        Args:
            image_data: Image bytes
            panel_id: Panel ID to locate (e.g., 'S1-L-1', 'S2-R-2')

        Returns:
            Dict with keys: x, y, width, height (in pixels), or None if not found
        """
        # Parse panel ID for basic context
        parsed = parse_panel_id(panel_id)
        row_num = get_row_position(parsed['row'])
        position_info = get_position_info(parsed['position'])

        # Encode image
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')

        # Create a minimal prompt without layout context
        prompt = f"""I need you to identify a specific panel in this dashboard screenshot using only visual analysis.

Target: Row {row_num}, {position_info['side']} side, position {position_info['index'] + 1}

Instructions:
1. Visually identify all rows in the dashboard (rows are typically separated by whitespace or titles)
2. Count from the top to find row {row_num}
3. Within that row, identify panels on the {position_info['side']} side
4. Select the panel at position {position_info['index'] + 1} (counting from top to bottom or left to right)
5. Identify the precise bounding box (x, y, width, height) of this panel in pixels
6. Include the graph/chart area and any legends, but not excessive whitespace
7. Respond ONLY with a JSON object in this exact format:

{{
  "found": true,
  "x": <left coordinate in pixels>,
  "y": <top coordinate in pixels>,
  "width": <width in pixels>,
  "height": <height in pixels>,
  "confidence": "<high|medium|low>",
  "notes": "<brief description of what you found>"
}}

If you cannot confidently identify the panel, respond with:
{{
  "found": false,
  "reason": "<explanation>"
}}

IMPORTANT: Respond with ONLY the JSON object, no other text."""

        # Call Claude API
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

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON from response (in case there's extra text)
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
                raise ValueError(f"Panel not found: {result.get('reason', 'Unknown reason')}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise ValueError(f"Failed to identify panel boundaries: {str(e)}")

    def crop_panel_by_id(
        self,
        image_data: bytes,
        layout: DashboardLayout,
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
            boundaries = self.identify_panel_boundaries(image_data, layout, panel_id)
        else:
            boundaries = self.identify_panel_boundaries_without_layout(image_data, panel_id)

        if not boundaries:
            raise ValueError(f"Could not identify panel '{panel_id}'")

        # Crop the image
        cropped_image = self.crop_panel(image_data, boundaries)

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
