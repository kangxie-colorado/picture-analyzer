# Picture Analyzer

AI-powered dashboard panel cropping tool with both fast coordinate-based and adaptive vision-based modes.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Fast cropping (no LLM, instant)
./crop-fast --batch

# Start API server
./run-api
```

## Features

- **Fast Cropping**: Pre-defined coordinates, ~0.1s per panel, $0.00 cost
- **Vision Cropping**: AI-powered adaptive detection, ~4s per panel
- **REST API**: HTTP interface for integration
- **Batch Processing**: Process multiple screenshots at once
- **Multiple Dashboards**: Support for different layouts

## Project Structure

```
picture-analyzer/
├── src/                    # Source code
│   ├── core/              # Core business logic
│   ├── api/               # REST API server
│   └── cli/               # Command-line tools
├── config/                # Configuration
│   └── dashboards/        # Dashboard definitions
├── docs/                  # Documentation
│   ├── README.md          # Full user guide
│   ├── FAST_CROPPING.md   # Fast cropping guide
│   └── TESTING.md         # Testing guide
├── screenshots/           # Input screenshots
├── outputs/               # Cropped panels
├── crop-fast              # Fast cropping CLI
├── run-api                # API server launcher
├── requirements.txt       # Python dependencies
└── CLAUDE.md              # Architecture & principles
```

## Documentation

- **[User Guide](docs/README.md)** - Complete usage documentation
- **[Fast Cropping](docs/FAST_CROPPING.md)** - Coordinate-based cropping guide
- **[Testing Guide](docs/TESTING.md)** - Testing and comparison methods
- **[Architecture](CLAUDE.md)** - Development principles and structure

## Usage Examples

### Fast Coordinate-Based Cropping

```bash
# Crop all panels from all screenshots
./crop-fast --batch

# Crop one screenshot
./crop-fast screenshots/dashboard.png

# Crop specific panel
./crop-fast screenshots/dashboard.png -p S1-L-write

# List available panels
./crop-fast --list
```

### REST API

```bash
# Start server
./run-api

# Health check
curl http://localhost:5000/health

# Crop panel
curl -X POST http://localhost:5000/crop-panel \
  -F "image=@dashboard.png" \
  -F "dashboard_name=abase-risk-analysis" \
  -F "panel_id=S1-L-write" \
  --output panel.png
```

### Python API

```python
from src.core import CoordinatePanelCropper, load_image, save_image

# Initialize cropper
cropper = CoordinatePanelCropper('abase-risk-analysis')

# Load and crop
image_data = load_image('screenshots/dashboard.png')
cropped, metadata = cropper.crop_panel(image_data, 'S1-L-write')

# Save result
save_image(cropped, 'output.png')
```

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies
- Anthropic API key (only for vision-based cropping or initial setup)

## Installation

```bash
# Clone repository
git clone <repository-url>
cd picture-analyzer

# Install dependencies
pip install -r requirements.txt

# Set API key (optional, only for vision features)
export ANTHROPIC_API_KEY=your_key_here
```

## Configuration

### Adding a New Dashboard

1. Take a reference screenshot
2. Generate coordinates:
   ```bash
   python -m src.cli.analyze_layout screenshot.png my-dashboard
   ```
3. Coordinates saved to `config/dashboards/my-dashboard/coordinates.yaml`
4. Use with `./crop-fast -d my-dashboard`

### Environment Variables

- `ANTHROPIC_API_KEY`: API key for vision features (optional)
- `PORT`: API server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False)

## Development

See [CLAUDE.md](CLAUDE.md) for:
- Architecture principles
- Development guidelines
- Adding new features
- File organization rules
- Dependency management

## License

MIT License

## Support

For issues or questions, open an issue on the repository.
