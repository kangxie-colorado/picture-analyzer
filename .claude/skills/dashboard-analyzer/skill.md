# Dashboard Analyzer Skill

Analyze Grafana dashboard screenshots and generate configuration files for risk analysis.

## Purpose

This skill extracts precise panel coordinates and dashboard structure from screenshots to enable accurate LLM-based risk analysis. The generated configuration files provide context and coordinates that help the LLM understand what it's analyzing.

## Input

- **Image path**: Path to a Grafana dashboard screenshot (any dimensions)
- **Dashboard name** (optional): Human-readable name for the dashboard

## Output

Three configuration files in `config/dashboards/<dashboard-id>/`:

1. **coordinates.yaml**: Precise pixel coordinates for each panel
2. **static_pack.yaml**: Dashboard structure, layout, and analysis guidance
3. **run_pack.yaml**: Runtime configuration template for analysis

## Instructions

When the user asks to analyze a dashboard, follow these steps:

### Step 1: Analyze Image with Claude Vision API

Use Claude Vision API to analyze the dashboard screenshot and extract:

1. **Image dimensions** (width x height in pixels)
2. **Panel coordinates** - PRECISE bounding boxes (x, y, width, height) for each panel
   - x: left edge position (pixels from left)
   - y: top edge position (pixels from top)
   - width: panel width in pixels
   - height: panel height in pixels
   - Include title, graph area, legends, and axes
   - Exclude excessive whitespace between panels
   - Accuracy target: ±5 pixels

3. **Dashboard structure**:
   - Number of rows/sections
   - Panel arrangement in each row
   - Visual layout pattern

4. **Panel metadata**:
   - Panel titles (visible text)
   - What each panel measures
   - Panel role/purpose

5. **Analysis context**:
   - Dashboard monitoring purpose
   - Key metrics being tracked
   - Risk analysis considerations

### Step 2: Generate Panel IDs

Use systematic naming: `S{row}-{position}-{name}`
- Row: S1, S2, S3... (top to bottom)
- Position: L (left), R (right), L2 (left second), R2, etc.
- Name: descriptive keyword (write, read, qps, disk, etc.)

Examples: `S1-L-write`, `S1-R-read`, `S2-L-disk`, `S3-L2-value_size`

### Step 3: Generate coordinates.yaml

Format:
```yaml
dashboard: dashboard-id
version: '1.0'
description: Pixel-based panel coordinates (no LLM required for cropping)
image_dimensions:
  width: <image_width>
  height: <image_height>

note: |
  These coordinates were extracted using AI vision analysis.
  They should work for all screenshots with the same dashboard layout and resolution.

panels:
  S1-L-write:
    # Panel title or description
    x: 30
    y: 250
    width: 615
    height: 153
  # ... more panels
```

### Step 4: Generate static_pack.yaml

Format:
```yaml
schema_version: 1

dashboard_static:
  id: "dashboard-id"
  human_name: "Dashboard Human Name"

  layout_description:
    - "Description of dashboard layout"
    - "Panel arrangement details"

  analysis_objectives:
    - "Key objective 1"
    - "Key objective 2"

  analysis_tips:
    - "Tip for interpreting this dashboard"
    - "Risk analysis guidance"

  rows:
    - id: "S1"
      title: "Row title or description"
      intent: "What this row monitors"
      panels:
        - id: "S1-L-write"
          role: "panel_role_description"
          source: "left/write"
        # ... more panels
      relationships:
        - "How panels relate to each other"

  identifiers:
    row_id_pattern: "S{n}"
    panel_id_pattern: "S{n}-{position}-{name}"
```

### Step 5: Generate run_pack.yaml (JSON format)

Format:
```json
{
  "schema_version": 1,
  "_about_run_pack": "Runtime parameters for dashboard analysis...",
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
      "format": "Return response content as structured JSON object",
      "verbosity": "Include resource identities in response",
      "json_schema": {
        "summary": "string - 1-2 paragraph summary",
        "findings": "array of strings - key findings",
        "risks": "array of risk objects with title, severity, description, location, bounding_box",
        "correlations": "array of strings - metric relationships",
        "next_steps": "array of strings - recommended actions",
        "title": "string - short descriptive title",
        "dashboard_understanding": "object - AI's understanding of dashboard"
      }
    }
  }
}
```

### Step 6: Self-Validation

After generating files, validate:

1. **Coordinates validation**:
   - All coordinates are within image bounds (0 ≤ x, x+width ≤ image_width)
   - All coordinates are within image bounds (0 ≤ y, y+height ≤ image_height)
   - No negative values
   - Panel sizes are reasonable (width > 50, height > 50)
   - No overlapping panels (warn if detected)

2. **Structure validation**:
   - All panel IDs in rows exist in coordinates
   - Row IDs follow pattern S1, S2, S3...
   - Panel IDs follow pattern S{n}-{pos}-{name}
   - At least one row exists
   - At least one panel exists

3. **Completeness check**:
   - All three files generated successfully
   - All required fields present
   - YAML/JSON is valid and parseable

4. **Visual verification prompt**:
   - Show summary of panels detected
   - Show image dimensions
   - Recommend: "Visually verify coordinates by overlaying them on the image"

### Step 7: Output Summary

Provide clear summary:
```
✓ Analysis complete for: <dashboard_name>
  Image: <width>x<height> pixels
  Panels detected: <count>
  Rows detected: <count>

Generated files:
  1. config/dashboards/<id>/coordinates.yaml
  2. config/dashboards/<id>/static_pack.yaml
  3. config/dashboards/<id>/run_pack.yaml

Validation results:
  ✓ Coordinates within bounds
  ✓ No negative values
  ✓ Structure is valid
  ⚠ Recommend visual verification

Panel summary:
  - S1-L-write: [title] (x,y,w,h)
  - S1-R-write: [title] (x,y,w,h)
  ...

Next steps:
  1. Review generated files
  2. Visually verify coordinates (optional)
  3. Use for risk analysis: <example command>
```

## Self-Testing Capabilities

The skill includes validation for:

### 1. Coordinate Accuracy
- Bounds checking (within image dimensions)
- No negative values
- Reasonable panel sizes (not too small)
- Overlap detection

### 2. Structural Validity
- YAML/JSON syntax correctness
- Required fields present
- ID pattern consistency
- Cross-reference integrity (all panel IDs exist)

### 3. Dimension Flexibility
- NO hardcoded dimensions
- Works with any image size
- Coordinates are absolute pixels (not percentages)
- Validation adapts to actual image dimensions

### 4. Visual Verification Helper
After generation, optionally create a visual verification image showing:
- Original screenshot with bounding boxes overlaid
- Panel IDs labeled on each box
- Saved as: `config/dashboards/<id>/verification.png`

## Handling Edge Cases

1. **Overlapping panels**: Warn user, suggest manual review
2. **Missing panel titles**: Use generic descriptions, mark for review
3. **Unusual layouts**: Still extract structure, add notes
4. **Very small panels**: Warn if width or height < 50px
5. **Out of bounds**: Error if coordinates extend beyond image

## Usage in Claude Shell

User can invoke this skill by saying:

```
Analyze dashboard screenshots/abase-risk-anal-11041203.png
```

Or:

```
Use dashboard-analyzer skill on screenshots/my-dashboard.png
```

Or:

```
Generate dashboard config for screenshots/dashboard.png with name "My Monitoring Dashboard"
```

## Implementation Notes

- Use Claude Vision API (claude-3-5-sonnet-20241022) for image analysis
- Requires ANTHROPIC_API_KEY environment variable
- All coordinates in pixels (not normalized)
- Supports any image dimensions (tested: 1920x1460, 1280x720, etc.)
- Output follows existing config format for compatibility

## Validation Command

After generation, user can validate with:
```bash
python -m src.utils.validate_dashboard config/dashboards/<id>
```

(Note: Create this validation utility if it doesn't exist)
