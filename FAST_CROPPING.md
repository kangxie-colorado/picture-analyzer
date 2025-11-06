# Fast Panel Cropping (No LLM Required)

This guide explains how to use the fast, coordinate-based panel cropping system that **requires NO API calls or LLM processing**.

## Overview

Instead of using AI vision to identify panels every time (slow and expensive), this system uses pre-defined pixel coordinates stored in a configuration file. This makes cropping:

- **Instant**: No API calls, just simple pixel math
- **Free**: No API costs
- **Consistent**: Same coordinates every time
- **Reliable**: No AI variability

## Quick Start

```bash
# Crop all panels from all screenshots (FAST!)
python crop_fast.py --batch

# Crop all panels from one screenshot
python crop_fast.py screenshot.png

# Crop a single panel
python crop_fast.py screenshot.png -p S1-L-write

# List available panels
python crop_fast.py --list
```

## How It Works

### 1. Coordinate Configuration File

Panel coordinates are stored in `dashboard-prompts/{dashboard}/coordinates.yaml`:

```yaml
dashboard: abase-risk-analysis
version: '1.0'
description: Pixel-based panel coordinates

panels:
  S1-L-write:
    x: 27
    y: 98
    width: 627
    height: 145
  # ... more panels
```

### 2. Fast Cropping Script

`crop_fast.py` reads the coordinates and crops panels instantly:

1. Load coordinates from YAML
2. Open screenshot image
3. Crop using simple PIL/Pillow operations
4. Save cropped panels

**No API calls. No LLM. Just pixels.**

## Performance

### Speed Comparison

| Method | Time per Panel | Cost per Panel |
|--------|---------------|----------------|
| **Fast (coordinates)** | **~0.1 seconds** | **$0.00** |
| LLM Vision (with layout) | ~3-5 seconds | ~$0.01-0.05 |
| LLM Vision (without layout) | ~3-5 seconds | ~$0.01-0.05 |

### Batch Processing

For 4 screenshots × 9 panels = 36 total panels:

- **Fast method**: ~4 seconds, $0.00
- **LLM method**: ~3-5 minutes, ~$0.36-1.80

## Usage Guide

### Batch Process All Screenshots

```bash
python crop_fast.py --batch
```

Output structure:
```
outputs/
├── screenshot1.s1-l-write.png
├── screenshot1.s1-r-write.png
├── screenshot1.s1-l-read.png
... (36 files for 4 screenshots)
```

### Single Screenshot

```bash
python crop_fast.py screenshots/abase-risk-anal-11041203.png
```

### Single Panel

```bash
python crop_fast.py screenshots/dashboard.png -p S1-L-write -o my_output/
```

### List Available Panels

```bash
python crop_fast.py --list
```

Output:
```
Available panels in abase-risk-analysis:

  S1-L-write           @  (  27,   98,  627x 145)
  S1-R-write           @  ( 654,   98,  627x 145)
  S1-L-read            @  (  27,  246,  627x 155)
  S1-R-read            @  ( 654,  246,  627x 155)
  S2-L-disk            @  (  27,  420,  627x 168)
  S2-R-partition       @  ( 654,  420,  627x 168)
  S3-L-qps_vs_quota    @  (  27,  617,  627x 148)
  S3-R-hotkey          @  ( 654,  617,  627x 148)
  S3-L2-value_size     @  (  27,  770, 1254x 150)
```

## Creating Coordinate Files

### Option 1: Use Provided Coordinates

The repository includes pre-measured coordinates for `abase-risk-analysis` dashboard:
- File: `dashboard-prompts/abase-risk-analysis/coordinates.yaml`
- Based on 1920x1460 pixel screenshots
- Tested with 4 different screenshots

### Option 2: Analyze Once with LLM

If you need custom coordinates for a different dashboard layout:

```bash
export ANTHROPIC_API_KEY=your_key
python analyze_layout.py screenshots/your-dashboard.png my-dashboard-name
```

This runs **one LLM call** to analyze the screenshot and generates the coordinates file.

### Option 3: Manual Measurement

Create coordinates manually by:

1. Open screenshot in image editor
2. Measure panel positions (x, y, width, height)
3. Create YAML file with coordinates
4. Test and adjust as needed

Helper script:
```bash
python measure_panels.py screenshots/dashboard.png
```

This creates a visualization showing where your coordinates land.

## Requirements

The coordinate file should work for:
- ✅ All screenshots of the **same dashboard layout**
- ✅ Screenshots with the **same resolution**
- ⚠️ May need adjustment for different resolutions
- ❌ Won't work for completely different dashboard layouts

## Adjusting Coordinates

If coordinates don't align perfectly:

1. **Visualize current coordinates:**
   ```bash
   python measure_panels.py screenshots/your-screenshot.png
   ```
   This creates `outputs/coordinates_visualization.png`

2. **Adjust coordinates in YAML:**
   Edit `dashboard-prompts/{dashboard}/coordinates.yaml`

3. **Test again:**
   ```bash
   python crop_fast.py screenshots/your-screenshot.png -p S1-L-write
   ```

4. **Iterate until perfect**

### Common Adjustments

- **Panel too high/low**: Adjust `y` coordinate
- **Panel too left/right**: Adjust `x` coordinate
- **Panel too small**: Increase `width` or `height`
- **Cutting off content**: Increase `width` and `height`
- **Too much whitespace**: Decrease `width` and `height`

## Multi-Dashboard Support

To support multiple dashboards:

1. Create coordinates file for each:
   ```
   dashboard-prompts/
   ├── dashboard-1/
   │   └── coordinates.yaml
   ├── dashboard-2/
   │   └── coordinates.yaml
   ```

2. Specify dashboard when cropping:
   ```bash
   python crop_fast.py screenshot.png -d dashboard-2
   ```

## Comparison with LLM Methods

### Use Fast Cropping When:
- ✅ You have many screenshots of the same dashboard
- ✅ Dashboard layout is consistent
- ✅ You want instant results
- ✅ You want to minimize costs
- ✅ Running automated/scheduled jobs

### Use LLM Cropping When:
- ⚠️ Every screenshot has a different layout
- ⚠️ Dashboard structure varies
- ⚠️ You need adaptive/smart detection
- ⚠️ One-time analysis is acceptable

## Examples

### Example 1: Daily Monitoring

```bash
#!/bin/bash
# Daily screenshot cropping job

# Take screenshot
./take_dashboard_screenshot.sh > screenshots/dashboard-$(date +%Y%m%d).png

# Crop all panels (instant, no API cost)
python crop_fast.py --batch

# Process panels for analysis
python analyze_panels.py outputs/*.png
```

### Example 2: Specific Panel Extraction

```python
import subprocess
import os

# Crop specific panels you care about
panels_of_interest = ['S1-L-write', 'S2-R-partition', 'S3-L-qps_vs_quota']

for screenshot in os.listdir('screenshots/'):
    for panel in panels_of_interest:
        subprocess.run([
            'python', 'crop_fast.py',
            f'screenshots/{screenshot}',
            '-p', panel,
            '-o', f'outputs/{panel}/'
        ])
```

## Troubleshooting

### Coordinates don't match panels

1. Check screenshot resolution matches expected (1920x1460)
2. Verify dashboard layout hasn't changed
3. Run visualization to see where boxes land
4. Adjust coordinates in YAML file

### Wrong panels cropped

1. Check panel IDs in YAML file
2. Verify panel ID mapping matches your dashboard
3. Run `--list` to see available panels

### Cropped panels look cut off

1. Increase `width` or `height` in coordinates
2. Adjust `x` or `y` to shift position
3. Visualize to see alignment

## See Also

- `TESTING.md` - LLM-based cropping with/without prompts
- `README.md` - Full API documentation
- `crop_cli.py` - LLM-based CLI tool
- `batch_test.py` - LLM batch processing

## Summary

**Fast coordinate-based cropping is ideal for production use when you have consistent dashboard layouts.**

- No API keys required
- Instant processing
- Zero cost
- Reliable and consistent
- Perfect for automation

Just set up coordinates once, then crop thousands of screenshots instantly!
