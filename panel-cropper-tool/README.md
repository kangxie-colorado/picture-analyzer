# Panel Cropper Tool

A standalone tool for cropping dashboard panels based on coordinate configurations.

## Features

- Crop individual or all panels from dashboard screenshots
- YAML-based coordinate configuration
- Validation and verification of coordinates
- No LLM dependencies - fast and reliable

## Installation

### Requirements

- Python 3.7+
- Pillow (PIL)
- PyYAML

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Crop all panels from a dashboard:

```bash
./crop-panels /path/to/dashboard.png -c /path/to/coordinates.yaml -o output_directory/
```

### Crop Specific Panel

```bash
./crop-panels /path/to/dashboard.png -c coordinates.yaml -p panel-id -o output/
```

### List Available Panels

```bash
./crop-panels /path/to/dashboard.png -c coordinates.yaml --list-panels
```

### Verify Coordinates

```bash
./crop-panels /path/to/dashboard.png -c coordinates.yaml --verify-only
```

## Coordinates File Format

The coordinates file is in YAML format:

```yaml
dashboard: my-dashboard-name
version: '1.0'
image_dimensions:
  width: 1920
  height: 1080

panels:
  panel-1:
    x: 10
    y: 100
    width: 800
    height: 400

  panel-2:
    x: 820
    y: 100
    width: 800
    height: 400
```

### Coordinate Fields

- `x`: Left edge position (pixels)
- `y`: Top edge position (pixels)
- `width`: Panel width (pixels)
- `height`: Panel height (pixels)

## Command-Line Options

```
positional arguments:
  image                 Path to dashboard screenshot

options:
  -c COORDINATES        Path to coordinates.yaml file (required)
  -o OUTPUT_DIR         Output directory for cropped panels
  -p PANEL_ID           Crop specific panel only
  --verify-only         Only verify coordinates, do not crop
  --list-panels         List available panel IDs and exit
```

## Examples

### Example 1: Crop All Panels

```bash
./crop-panels dashboard.png -c coords.yaml -o panels/
```

### Example 2: Crop Specific Panel

```bash
./crop-panels dashboard.png -c coords.yaml -p panel-2
```

## Programmatic Usage

```python
from src.core.panel_cropper import PanelCropper

# Initialize cropper
cropper = PanelCropper('path/to/coordinates.yaml')

# Crop single panel
panel_image, metadata = cropper.crop_panel(
    'dashboard.png',
    'panel-1',
    'output/panel-1.png'
)

# Crop all panels
results = cropper.crop_all_panels('dashboard.png', 'output/')
```
