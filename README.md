# Picture Analyzer API

A Flask-based REST API that uses Claude AI (Anthropic) to analyze images and crop dashboard panels. Upload pictures and get detailed AI-powered analysis, or extract specific panels from dashboard screenshots.

## Features

### Image Analysis
- Upload images via HTTP POST for analysis
- Analyze images from URLs
- Custom analysis prompts
- Powered by Claude 3.5 Sonnet vision model

### Dashboard Panel Cropping (NEW!)
- Automatically crop specific panels from dashboard screenshots
- AI-powered panel boundary detection
- YAML-based dashboard layout definitions
- Command-line tool and REST API support
- Supports complex multi-row dashboard layouts

### General
- Supports multiple image formats (PNG, JPG, JPEG, GIF, WEBP)
- CORS enabled for web applications
- Easy to integrate with any programming language

## Setup

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd picture-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. Run the server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Health Check

Check if the API is running and configured properly.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "api_key_configured": true
}
```

### 2. Analyze Image (File Upload)

Upload an image file for analysis.

**Endpoint:** `POST /analyze`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `image` (required): Image file
- `prompt` (optional): Custom analysis prompt

**Example using curl:**
```bash
curl -X POST http://localhost:5000/analyze \
  -F "image=@/path/to/your/image.jpg"
```

**Example with custom prompt:**
```bash
curl -X POST http://localhost:5000/analyze \
  -F "image=@/path/to/your/image.jpg" \
  -F "prompt=Describe the colors and mood of this image"
```

**Response:**
```json
{
  "success": true,
  "filename": "image.jpg",
  "analysis": "Detailed analysis of the image...",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_used": "Please analyze this image..."
}
```

### 3. Analyze Image (URL)

Analyze an image from a public URL.

**Endpoint:** `POST /analyze-url`

**Content-Type:** `application/json`

**Body:**
```json
{
  "url": "https://example.com/image.jpg",
  "prompt": "Optional custom prompt"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/analyze-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.jpg"
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/image.jpg",
  "analysis": "Detailed analysis of the image...",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_used": "Please analyze this image..."
}
```

### 4. Crop Dashboard Panel

Crop a specific panel from a dashboard screenshot using AI-powered boundary detection.

**Endpoint:** `POST /crop-panel`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `image` (required): Dashboard screenshot file
- `dashboard_name` (required): Dashboard name (e.g., 'abase-risk-analysis')
- `panel_id` (required): Panel ID to crop (e.g., 'S1-L-write', 'S2-R-partition')
- `return_metadata` (optional): Return JSON with metadata instead of image (default: false)

**Example using curl:**
```bash
curl -X POST http://localhost:5000/crop-panel \
  -F "image=@dashboard.png" \
  -F "dashboard_name=abase-risk-analysis" \
  -F "panel_id=S1-L-write" \
  --output S1-L-write.png
```

**Example with metadata:**
```bash
curl -X POST http://localhost:5000/crop-panel \
  -F "image=@dashboard.png" \
  -F "dashboard_name=abase-risk-analysis" \
  -F "panel_id=S1-L-write" \
  -F "return_metadata=true"
```

**Response (with return_metadata=true):**
```json
{
  "success": true,
  "panel_id": "S1-L-write",
  "dashboard": "abase-risk-analysis",
  "image": "<base64-encoded PNG>",
  "metadata": {
    "panel_id": "S1-L-write",
    "panel_role": "global_capacity_headroom",
    "boundaries": {
      "x": 50,
      "y": 100,
      "width": 800,
      "height": 400,
      "confidence": "high",
      "notes": "Panel identified in row 1, left side"
    }
  }
}
```

### 5. Get Dashboard Layout

Get information about a dashboard's layout and available panels.

**Endpoint:** `GET /dashboard-layout/<dashboard_name>`

**Example:**
```bash
curl http://localhost:5000/dashboard-layout/abase-risk-analysis
```

**Response:**
```json
{
  "dashboard_id": "cc-risk-analysis/abase-risk-analysis",
  "name": "Abase Risk Analysis",
  "rows": [
    {
      "id": "S1",
      "title": "写/读 RU Quota vs Usage，左边为总，右边为DC",
      "intent": "Headroom & per-DC stress detection (write/read).",
      "panels": [
        {
          "id": "S1-L-write",
          "role": "global_capacity_headroom",
          "source": "left/write"
        },
        {
          "id": "S1-R-write",
          "role": "per_dc_capacity_headroom",
          "source": "right/write"
        }
      ]
    }
  ]
}
```

## Dashboard Panel Cropping

### Overview

The panel cropping feature allows you to automatically extract specific panels from dashboard screenshots. This is useful for:

- Automated monitoring and reporting
- Creating panel-specific alerts
- Extracting metrics for analysis
- Building custom dashboards from existing ones

### How It Works

1. **Define Dashboard Layout**: Create a YAML file describing your dashboard structure (rows and panels)
2. **Take Screenshot**: Capture your dashboard as an image
3. **Crop Panel**: Use the API or CLI to extract specific panels
4. **AI Detection**: Claude Vision identifies panel boundaries automatically

### Dashboard Layout YAML

Dashboard layouts are defined in YAML files under `dashboard-prompts/<dashboard-name>/static_pack.yaml`.

**Example structure:**
```yaml
schema_version: 1

dashboard_static:
  id: "my-dashboard"
  human_name: "My Dashboard"

  layout_description:
    - "This dashboard has 3 rows"
    - "Each row contains multiple panels"

  rows:
    - id: "S1"
      title: "First Row Title"
      intent: "Purpose of this row"
      panels:
        - id: "S1-L-write"
          role: "metric_name"
          source: "left/write"
        - id: "S1-R-read"
          role: "metric_name"
          source: "right/read"

    - id: "S2"
      title: "Second Row Title"
      intent: "Purpose of this row"
      panels:
        - id: "S2-L-disk"
          role: "storage_metrics"
```

### Panel ID Convention

Panel IDs follow the pattern: `{row}-{position}-{name}`

- **Row**: S1, S2, S3, etc.
- **Position**: L (left), R (right), L2 (left, 2nd), etc.
- **Name**: Descriptive name (optional)

**Examples:**
- `S1-L-write` - Row 1, Left panel, write metrics
- `S2-R-partition` - Row 2, Right panel, partition data
- `S3-L2-value_size` - Row 3, Left 2nd panel, value size

### Command-Line Tool

Use the `crop_cli.py` script for local panel cropping:

**Basic usage:**
```bash
python crop_cli.py screenshot.png abase-risk-analysis S1-L-write
```

**With custom output:**
```bash
python crop_cli.py screenshot.png abase-risk-analysis S1-L-write -o output.png
```

**List available panels:**
```bash
python crop_cli.py screenshot.png abase-risk-analysis --list-panels
```

**With API key:**
```bash
python crop_cli.py screenshot.png abase-risk-analysis S1-L-write --api-key sk-xxx
```

Or set environment variable:
```bash
export ANTHROPIC_API_KEY=sk-xxx
python crop_cli.py screenshot.png abase-risk-analysis S1-L-write
```

## Usage Examples

### Python

```python
import requests

# Analyze a local file
with open('my_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/analyze',
        files={'image': f}
    )
    result = response.json()
    print(result['analysis'])

# Analyze from URL
response = requests.post(
    'http://localhost:5000/analyze-url',
    json={'url': 'https://example.com/image.jpg'}
)
result = response.json()
print(result['analysis'])

# Crop a panel from dashboard
with open('dashboard.png', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/crop-panel',
        files={'image': f},
        data={
            'dashboard_name': 'abase-risk-analysis',
            'panel_id': 'S1-L-write'
        }
    )
    # Save the cropped image
    with open('S1-L-write.png', 'wb') as out:
        out.write(response.content)

# Crop panel with metadata
with open('dashboard.png', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/crop-panel',
        files={'image': f},
        data={
            'dashboard_name': 'abase-risk-analysis',
            'panel_id': 'S1-L-write',
            'return_metadata': 'true'
        }
    )
    result = response.json()
    print(f"Confidence: {result['metadata']['confidence']}")
    print(f"Boundaries: {result['metadata']['boundaries']}")
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// Analyze a local file
const form = new FormData();
form.append('image', fs.createReadStream('my_image.jpg'));

axios.post('http://localhost:5000/analyze', form, {
    headers: form.getHeaders()
})
.then(response => {
    console.log(response.data.analysis);
})
.catch(error => {
    console.error('Error:', error.response.data);
});

// Analyze from URL
axios.post('http://localhost:5000/analyze-url', {
    url: 'https://example.com/image.jpg'
})
.then(response => {
    console.log(response.data.analysis);
})
.catch(error => {
    console.error('Error:', error.response.data);
});
```

### JavaScript (Browser/Fetch)

```javascript
// Analyze a file from file input
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('image', file);

fetch('http://localhost:5000/analyze', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log(data.analysis);
})
.catch(error => {
    console.error('Error:', error);
});
```

### HTML Form Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Picture Analyzer</title>
</head>
<body>
    <h1>Picture Analyzer</h1>

    <form id="uploadForm">
        <input type="file" id="imageFile" accept="image/*" required>
        <textarea id="customPrompt" placeholder="Optional: Custom analysis prompt"></textarea>
        <button type="submit">Analyze Image</button>
    </form>

    <div id="result"></div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();
            const fileInput = document.getElementById('imageFile');
            const promptInput = document.getElementById('customPrompt');

            formData.append('image', fileInput.files[0]);
            if (promptInput.value) {
                formData.append('prompt', promptInput.value);
            }

            try {
                const response = await fetch('http://localhost:5000/analyze', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                document.getElementById('result').innerHTML =
                    `<h2>Analysis:</h2><p>${data.analysis}</p>`;
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('result').innerHTML =
                    `<p style="color: red;">Error: ${error.message}</p>`;
            }
        });
    </script>
</body>
</html>
```

## Configuration

Configure the API using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) | - |
| `PORT` | Port to run the server on | 5000 |
| `DEBUG` | Enable Flask debug mode | False |

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- WebP (.webp)

Maximum file size: 16MB

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid request (missing file, unsupported format, etc.)
- `500 Internal Server Error`: Server-side error or API key issues

Example error response:
```json
{
  "error": "No image file provided"
}
```

## Security Considerations

- Never commit your `.env` file or API keys to version control
- Use HTTPS in production
- Implement rate limiting for production use
- Consider adding authentication for public deployments
- The `uploads/` directory is in `.gitignore` to avoid committing user images

## License

MIT License

## Support

For issues or questions, please open an issue on the repository.
