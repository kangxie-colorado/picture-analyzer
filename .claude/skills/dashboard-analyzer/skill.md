# Dashboard Analyzer Skill

Analyze Grafana dashboard screenshots directly and generate configuration files for risk analysis.

## Purpose

When the user provides a dashboard screenshot, analyze it using vision capabilities to extract precise panel coordinates and dashboard structure. Generate configuration files that enable accurate LLM-based risk analysis.

## Input

- **Image path**: Path to a Grafana dashboard screenshot
- **Dashboard name** (optional): Human-readable name

## Output

Three configuration files in `config/dashboards/<dashboard-id>/`:
1. **coordinates.yaml**: Precise pixel coordinates for each panel
2. **static_pack.yaml**: Dashboard structure and analysis guidance
3. **run_pack.yaml**: Runtime configuration template

## Instructions

When the user asks to analyze a dashboard screenshot, follow these steps:

### Step 1: Load and Examine the Image

Read the image file and carefully examine the dashboard layout:
- Note the overall image dimensions (width x height)
- Identify distinct rows or sections
- Count visible panels
- Observe the layout pattern (grid, side-by-side, etc.)

### Step 2: Extract Precise Panel Coordinates

For EACH panel, measure the bounding box coordinates:

**Measurement Guidelines:**
- **x**: Distance from left edge of image to left edge of panel (pixels)
- **y**: Distance from top edge of image to top edge of panel (pixels)
- **width**: Panel width including title, graph, legend, axes (pixels)
- **height**: Panel height including all components (pixels)

**What to include:**
- Panel title/heading
- Graph/chart area
- Legends (usually on right side)
- Axis labels and scales
- Any panel-specific controls

**What to exclude:**
- Whitespace between panels
- Dashboard header/navigation
- Gaps between rows

**Accuracy target**: ±5 pixels

**Technique:**
- Start from top-left corner of image (0, 0)
- Measure to the visual boundary of each panel
- Include the panel's border/container
- Be systematic: go row by row, left to right

### Step 3: Generate Panel IDs

Create systematic IDs using pattern: `S{row}-{position}-{name}`

**Components:**
- **Row**: S1, S2, S3... (top to bottom)
- **Position**:
  - L = left column
  - R = right column
  - L2 = left column, second in vertical stack
  - R2 = right column, second in vertical stack
- **Name**: Descriptive keyword (lowercase, underscores)
  - Examples: write, read, qps, disk, hotkey, value_size

**Examples:**
- First row, left panel about writes: `S1-L-write`
- First row, right panel about reads: `S1-R-read`
- Second row, left panel about disk: `S2-L-disk`
- Third row, bottom full-width panel: `S3-L2-value_size`

### Step 4: Understand Dashboard Purpose

Analyze what the dashboard monitors:
- What system/service is being monitored?
- What are the key metrics? (capacity, performance, storage, traffic)
- What would be important for risk analysis?
- How do panels relate to each other?

### Step 5: Generate coordinates.yaml

Create the file with this structure:

```yaml
dashboard: <dashboard-id>
version: '1.0'
description: Pixel-based panel coordinates (no LLM required for cropping)
image_dimensions:
  width: <width>
  height: <height>

note: |
  These coordinates were extracted through visual analysis.
  They work for screenshots with the same dashboard layout and resolution.

panels:
  S1-L-write:
    # Panel title or description
    x: <x_coordinate>
    y: <y_coordinate>
    width: <width_pixels>
    height: <height_pixels>

  # ... more panels
```

**Important:**
- Use actual measured coordinates
- Add comments with panel titles
- All values must be integers (pixels)
- Verify coordinates are within image bounds

### Step 6: Generate static_pack.yaml

Create the file with dashboard structure:

```yaml
schema_version: 1

dashboard_static:
  id: "<dashboard-id>"
  human_name: "<Dashboard Human Name>"

  layout_description:
    - "Description of dashboard layout (e.g., '3 rows with varying layouts')"
    - "Description of panel types (e.g., 'Time series graphs with legends')"

  analysis_objectives:
    - "Key monitoring objective 1 (e.g., 'Capacity headroom vs usage')"
    - "Key monitoring objective 2"

  analysis_tips:
    - "Tip for interpreting this dashboard"
    - "Risk analysis guidance (e.g., 'Spikes > 10min are concerning')"

  rows:
    - id: "S1"
      title: "Row title or description of what this row monitors"
      intent: "Purpose of this row (e.g., 'Headroom & per-DC stress detection')"
      panels:
        - id: "S1-L-write"
          role: "panel_role (e.g., 'global_capacity_headroom')"
          source: "left/write"
        - id: "S1-R-write"
          role: "per_dc_capacity_headroom"
          source: "right/write"
      relationships:
        - "How panels in this row relate (e.g., 'Global vs per-DC comparison')"

  identifiers:
    row_id_pattern: "S{n}"
    panel_id_pattern: "S{n}-{position}-{name}"
```

**Panel Role Suggestions:**
- `global_capacity_headroom` - Overall capacity metrics
- `per_dc_capacity_headroom` - Per-datacenter capacity
- `table_and_subtable_storage` - Storage breakdown
- `partition_capacity_max` - Partition-level capacity
- `qps_vs_quota_alignment` - Traffic vs limits
- `hotkey_activity_topN` - Hotspot detection
- `value_size_characteristics` - Object size analysis

### Step 7: Generate run_pack.yaml (JSON format)

Create the runtime configuration template:

```json
{
  "schema_version": 1,
  "_about_run_pack": "Runtime parameters for dashboard analysis. Template variables ({{var-*}}) should be replaced with actual values from Grafana URL parameters.",
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
      "verbosity": "Include resource identities in the response",
      "json_schema": {
        "summary": "string - 1-2 paragraph summary in Chinese",
        "findings": "array of strings - key findings from dashboard analysis",
        "risks": "array of risk objects - each with: title (string, preferably in English), severity (critical|high|medium|low), description (string), location (string, e.g. 'S2 row, right panel'), bounding_box (optional object with normalized coordinates {x, y, width, height} in 0-1 range)",
        "correlations": "array of strings - relationships between metrics",
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
```

### Step 8: Self-Validation

After generating files, validate them:

**1. Coordinate Bounds Check:**
```
For each panel:
  ✓ 0 ≤ x < image_width
  ✓ 0 ≤ y < image_height
  ✓ x + width ≤ image_width
  ✓ y + height ≤ image_height
  ✓ width > 50, height > 50
```

**2. Structure Check:**
```
✓ All panel IDs in rows exist in coordinates
✓ Row IDs follow pattern: S1, S2, S3...
✓ Panel IDs follow pattern: S{n}-{pos}-{name}
✓ No duplicate panel IDs
```

**3. Completeness:**
```
✓ All visible panels accounted for
✓ All three files generated
✓ Required fields present
```

Report any issues found during validation.

### Step 9: Write Files to Disk

Use the Write tool to create each file:
- `config/dashboards/<dashboard-id>/coordinates.yaml`
- `config/dashboards/<dashboard-id>/static_pack.yaml`
- `config/dashboards/<dashboard-id>/run_pack.yaml`

Create the directory first if it doesn't exist.

### Step 10: Provide Summary

Show clear summary:

```
✅ Dashboard Analysis Complete

Dashboard: <name>
Dashboard ID: <id>
Image: <width>x<height> pixels
Panels detected: <count>
Rows detected: <count>

Generated files:
  1. config/dashboards/<id>/coordinates.yaml
  2. config/dashboards/<id>/static_pack.yaml
  3. config/dashboards/<id>/run_pack.yaml

Validation results:
  ✓ All coordinates within bounds
  ✓ No negative values
  ✓ Structure is valid
  [any warnings]

Panel summary:
  S1-L-write: <title> (x, y, w×h)
  S1-R-write: <title> (x, y, w×h)
  ...

Row summary:
  S1: <title> - <panel_count> panels
  S2: <title> - <panel_count> panels
  ...

Next steps:
  1. Review generated files
  2. Optionally validate: python -m src.utils.validate_dashboard config/dashboards/<id>
  3. Use for risk analysis
```

## Important Notes

- Measure coordinates carefully - accuracy matters for downstream use
- Include ALL visible panels, even small ones
- Panel IDs should be systematic and meaningful
- Analysis objectives should be specific to what you observe
- When in doubt about coordinates, be conservative (slightly larger is better than clipping content)
- Document any assumptions or uncertainties in comments

## Common Dashboard Patterns

**2x2 Grid (Row 1):**
```
S1-L-top, S1-R-top
S1-L-bottom, S1-R-bottom
```

**Side-by-side (Row 2):**
```
S2-L-panel, S2-R-panel
```

**3-panel with full-width bottom:**
```
S3-L-panel, S3-R-panel
S3-L2-fullwidth
```

## Edge Cases

- **Overlapping panels**: Measure to actual visible boundaries, note in comments
- **Nested panels**: Treat as single panel with outer boundary
- **Very small panels**: Include if > 50x50px, note if smaller
- **Partial panels**: Include only if majority is visible
- **Dashboard header**: Exclude from panel coordinates

## Validation Command

User can validate generated files with:
```bash
python -m src.utils.validate_dashboard config/dashboards/<dashboard-id>
```

This checks syntax, bounds, structure, and cross-references.
