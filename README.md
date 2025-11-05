# Picture Analyzer API

A Flask-based REST API that uses Claude AI (Anthropic) to analyze images. Upload pictures and get detailed AI-powered analysis.

## Features

- Upload images via HTTP POST for analysis
- Analyze images from URLs
- Supports multiple image formats (PNG, JPG, JPEG, GIF, WEBP)
- Custom analysis prompts
- Powered by Claude 3.5 Sonnet vision model
- CORS enabled for web applications

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
