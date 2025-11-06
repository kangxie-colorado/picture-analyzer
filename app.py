from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import anthropic
import os
import base64
from werkzeug.utils import secure_filename
import mimetypes
from io import BytesIO
from dashboard_layout import parse_dashboard_layout, DashboardLayout
from panel_cropper import PanelCropper

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
        'version': '2.0.0',
        'endpoints': {
            'POST /analyze': 'Analyze an image',
            'POST /analyze-url': 'Analyze an image from URL',
            'POST /crop-panel': 'Crop a specific panel from a dashboard screenshot',
            'GET /dashboard-layout/<dashboard_name>': 'Get dashboard layout info',
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

@app.route('/dashboard-layout/<dashboard_name>', methods=['GET'])
def get_dashboard_layout(dashboard_name):
    """
    Get information about a dashboard layout

    Path parameter:
    - dashboard_name: Name of the dashboard (e.g., 'abase-risk-analysis')
    """
    try:
        # Build path to layout YAML
        layout_path = os.path.join(
            'dashboard-prompts',
            dashboard_name,
            'static_pack.yaml'
        )

        if not os.path.exists(layout_path):
            return jsonify({'error': f'Dashboard layout not found: {dashboard_name}'}), 404

        # Parse layout
        layout = parse_dashboard_layout(layout_path)

        # Build response
        response = {
            'dashboard_id': layout.id,
            'name': layout.human_name,
            'rows': []
        }

        for row in layout.rows:
            row_data = {
                'id': row.id,
                'title': row.title,
                'intent': row.intent,
                'panels': [
                    {
                        'id': panel.id,
                        'role': panel.role,
                        'source': panel.source
                    }
                    for panel in row.panels
                ]
            }
            response['rows'].append(row_data)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crop-panel', methods=['POST'])
def crop_panel():
    """
    Crop a specific panel from a dashboard screenshot

    Form data:
    - image: Dashboard screenshot (required)
    - dashboard_name: Dashboard name (e.g., 'abase-risk-analysis') (required)
    - panel_id: Panel ID to crop (e.g., 'S1-L-write') (required)
    - return_metadata: Whether to return metadata as JSON (default: false)
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    # Check required fields
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    if 'dashboard_name' not in request.form:
        return jsonify({'error': 'No dashboard_name provided'}), 400

    if 'panel_id' not in request.form:
        return jsonify({'error': 'No panel_id provided'}), 400

    file = request.files['image']
    dashboard_name = request.form['dashboard_name']
    panel_id = request.form['panel_id']
    return_metadata = request.form.get('return_metadata', 'false').lower() == 'true'

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Load dashboard layout
        layout_path = os.path.join(
            'dashboard-prompts',
            dashboard_name,
            'static_pack.yaml'
        )

        if not os.path.exists(layout_path):
            return jsonify({'error': f'Dashboard layout not found: {dashboard_name}'}), 404

        layout = parse_dashboard_layout(layout_path)

        # Read image
        image_data = file.read()

        # Initialize cropper
        cropper = PanelCropper(API_KEY)

        # Crop the panel
        cropped_image, metadata = cropper.crop_panel_by_id(image_data, layout, panel_id)

        # Return based on preference
        if return_metadata:
            # Return JSON with base64-encoded image
            cropped_base64 = base64.standard_b64encode(cropped_image).decode('utf-8')
            return jsonify({
                'success': True,
                'panel_id': panel_id,
                'dashboard': dashboard_name,
                'image': cropped_base64,
                'metadata': metadata
            })
        else:
            # Return the image directly
            return send_file(
                BytesIO(cropped_image),
                mimetype='image/png',
                as_attachment=True,
                download_name=f'{panel_id}.png'
            )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
