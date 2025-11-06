# Testing Guide

This guide explains how to test the panel cropping functionality with your dashboard screenshots.

## Overview

The test compares two cropping modes:
- **with-prompt**: Uses the dashboard layout YAML file to guide panel detection
- **without-prompt**: Uses pure AI vision without layout context

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Add screenshots:**
   Place your dashboard screenshots in the `screenshots/` directory:
   ```bash
   # Copy your screenshots
   cp /path/to/your/screenshots/*.png screenshots/
   ```

## Running Tests

### Batch Test All Screenshots

Process all screenshots and crop all panels in both modes:

```bash
python batch_test.py
```

This will:
1. Find all images in `screenshots/`
2. For each screenshot, crop all defined panels
3. Save outputs to `outputs/` with naming convention:
   - `{screenshot-name}.with-prompt.{panel-id}.png`
   - `{screenshot-name}.without-prompt.{panel-id}.png`

### Example Output

For screenshot `abase-risk-anal-11041203.png`, you'll get:

```
outputs/
├── abase-risk-anal-11041203.png.with-prompt.s1-l-write.png
├── abase-risk-anal-11041203.png.without-prompt.s1-l-write.png
├── abase-risk-anal-11041203.png.with-prompt.s1-r-write.png
├── abase-risk-anal-11041203.png.without-prompt.s1-r-write.png
├── abase-risk-anal-11041203.png.with-prompt.s1-l-read.png
├── abase-risk-anal-11041203.png.without-prompt.s1-l-read.png
└── ... (18 files total - 9 panels × 2 modes)
```

## Expected Panels

For the **abase-risk-analysis** dashboard, the following panels will be cropped:

### Row 1 (S1): RU Quota vs Usage
- `S1-L-write` - Global write capacity
- `S1-R-write` - Per-DC write capacity
- `S1-L-read` - Global read capacity
- `S1-R-read` - Per-DC read capacity

### Row 2 (S2): Storage Usage
- `S2-L-disk` - Table and subtable storage
- `S2-R-partition` - Partition capacity max

### Row 3 (S3): Traffic & Hotkeys
- `S3-L-qps_vs_quota` - QPS vs quota alignment
- `S3-R-hotkey` - Hotkey activity
- `S3-L2-value_size` - Value size characteristics

**Total: 9 panels per screenshot**

## Testing Individual Screenshots

You can also test individual screenshots using the CLI tool:

```bash
# With layout context
python crop_cli.py screenshots/dashboard.png abase-risk-analysis S1-L-write

# List all available panels
python crop_cli.py screenshots/dashboard.png abase-risk-analysis --list-panels
```

## Interpreting Results

### Success Indicators
- ✓ High confidence detections
- Properly cropped panels with clear boundaries
- Legends and titles included

### Things to Check
1. **Boundary accuracy**: Are panels cropped precisely?
2. **Legend inclusion**: Are legends included in the crop?
3. **Whitespace**: Is excessive whitespace avoided?
4. **Mode comparison**: How do with-prompt and without-prompt compare?

### Expected Differences

**With-prompt mode:**
- Uses dashboard structure information
- Knows panel titles and roles
- More context-aware
- Generally more accurate

**Without-prompt mode:**
- Pure visual detection
- No prior knowledge of layout
- Tests raw vision capabilities
- May be less precise

## Troubleshooting

### No screenshots found
```
No screenshots found in screenshots/
```
**Solution:** Add PNG or JPG files to the `screenshots/` directory

### API key not set
```
Error: ANTHROPIC_API_KEY not set
```
**Solution:** Export your API key:
```bash
export ANTHROPIC_API_KEY=sk-...
```

### Panel not found
```
✗ Error: Panel not found
```
**Possible causes:**
- Screenshot doesn't match the dashboard layout
- Panel is obscured or not visible
- Image quality is too low

## Directory Structure

```
picture-analyzer/
├── screenshots/          # Input: Your dashboard screenshots
│   └── *.png
├── outputs/             # Output: Cropped panels
│   └── *.with-prompt.*.png
│   └── *.without-prompt.*.png
├── dashboard-prompts/   # Dashboard layout definitions
│   └── abase-risk-analysis/
│       └── static_pack.yaml
└── batch_test.py        # Test script
```

## Notes

- The `outputs/` directory is git-ignored
- Processing time: ~2-5 seconds per panel (per mode)
- For a 9-panel dashboard: ~3-5 minutes total per screenshot
- API costs: Approximately $0.01-0.10 per panel depending on image size
