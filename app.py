from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import os
import base64
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Anthropic client
API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set. Please set it in environment variables.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_media_type(filename):
    """Get the proper media type for the image"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    # Fallback to common types
    ext = filename.rsplit('.', 1)[1].lower()
    media_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')

@app.route('/')
def index():
    return jsonify({
        'service': 'Picture Analyzer API',
        'version': '1.0.0',
        'endpoints': {
            'POST /analyze': 'Analyze an image',
            'POST /analyze-url': 'Analyze an image from URL',
            'GET /health': 'Health check'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'api_key_configured': bool(API_KEY)})

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image

    Form data:
    - image: Image file (required)
    - prompt: Custom analysis prompt (optional)
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    # Check if image file is present
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Read and encode the image
        image_data = file.read()
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')

        # Get media type
        media_type = get_image_media_type(file.filename)

        # Get custom prompt or use default
        custom_prompt = request.form.get('prompt', '')
        if custom_prompt:
            analysis_prompt = custom_prompt
        else:
            analysis_prompt = """Please analyze this image in detail. Provide:
1. A description of what you see in the image
2. Key objects, people, or elements present
3. The setting or context
4. Any notable details, colors, or composition
5. Any text visible in the image
6. The overall mood or purpose of the image"""

        # Call Claude API with vision
        client = anthropic.Anthropic(api_key=API_KEY)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ],
                }
            ],
        )

        # Extract the analysis text
        analysis = message.content[0].text

        return jsonify({
            'success': True,
            'filename': secure_filename(file.filename),
            'analysis': analysis,
            'model': 'claude-3-5-sonnet-20241022',
            'prompt_used': analysis_prompt
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-url', methods=['POST'])
def analyze_image_url():
    """
    Analyze an image from a URL

    JSON body:
    - url: Image URL (required)
    - prompt: Custom analysis prompt (optional)
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    image_url = data['url']

    try:
        # Get custom prompt or use default
        custom_prompt = data.get('prompt', '')
        if custom_prompt:
            analysis_prompt = custom_prompt
        else:
            analysis_prompt = """Please analyze this image in detail. Provide:
1. A description of what you see in the image
2. Key objects, people, or elements present
3. The setting or context
4. Any notable details, colors, or composition
5. Any text visible in the image
6. The overall mood or purpose of the image"""

        # Call Claude API with vision
        client = anthropic.Anthropic(api_key=API_KEY)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": image_url,
                            },
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ],
                }
            ],
        )

        # Extract the analysis text
        analysis = message.content[0].text

        return jsonify({
            'success': True,
            'url': image_url,
            'analysis': analysis,
            'model': 'claude-3-5-sonnet-20241022',
            'prompt_used': analysis_prompt
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
