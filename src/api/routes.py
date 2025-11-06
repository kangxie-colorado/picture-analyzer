"""
API route handlers
"""
from flask import Blueprint, request, jsonify, send_file
import anthropic
import os
import base64
from werkzeug.utils import secure_filename
from io import BytesIO

from ..core import parse_dashboard_layout, VisionPanelCropper
from .utils import (
    allowed_file,
    get_image_media_type,
    get_allowed_extensions_str,
    DEFAULT_ANALYSIS_PROMPT
)

# Create blueprint
api = Blueprint('api', __name__)

# Get API key from environment
API_KEY = os.environ.get('ANTHROPIC_API_KEY')


@api.route('/')
def index():
    """API information endpoint"""
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


@api.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(API_KEY)
    })


@api.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image using Claude Vision

    Form data:
        image: Image file (required)
        prompt: Custom analysis prompt (optional)

    Returns:
        JSON with analysis results
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Allowed: {get_allowed_extensions_str()}'
        }), 400

    try:
        image_data = file.read()
        base64_image = base64.standard_b64encode(image_data).decode('utf-8')
        media_type = get_image_media_type(file.filename)

        analysis_prompt = request.form.get('prompt', DEFAULT_ANALYSIS_PROMPT)

        client = anthropic.Anthropic(api_key=API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{
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
                    {"type": "text", "text": analysis_prompt}
                ],
            }],
        )

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


@api.route('/analyze-url', methods=['POST'])
def analyze_image_url():
    """
    Analyze an image from a URL

    JSON body:
        url: Image URL (required)
        prompt: Custom analysis prompt (optional)

    Returns:
        JSON with analysis results
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    image_url = data['url']

    try:
        analysis_prompt = data.get("prompt", DEFAULT_ANALYSIS_PROMPT)

        client = anthropic.Anthropic(api_key=API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "url", "url": image_url},
                    },
                    {"type": "text", "text": analysis_prompt}
                ],
            }],
        )

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


@api.route('/dashboard-layout/<dashboard_name>', methods=['GET'])
def get_dashboard_layout(dashboard_name):
    """
    Get information about a dashboard layout

    Path parameter:
        dashboard_name: Name of the dashboard

    Returns:
        JSON with dashboard structure
    """
    try:
        layout_path = os.path.join('config', 'dashboards', dashboard_name, 'static_pack.yaml')

        if not os.path.exists(layout_path):
            return jsonify({'error': f'Dashboard layout not found: {dashboard_name}'}), 404

        layout = parse_dashboard_layout(layout_path)

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


@api.route('/crop-panel', methods=['POST'])
def crop_panel():
    """
    Crop a specific panel from a dashboard screenshot

    Form data:
        image: Dashboard screenshot (required)
        dashboard_name: Dashboard name (required)
        panel_id: Panel ID to crop (required)
        return_metadata: Return JSON with metadata (default: false)

    Returns:
        Cropped image (PNG) or JSON with metadata
    """
    if not API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

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
        return jsonify({
            'error': f'File type not allowed. Allowed: {get_allowed_extensions_str()}'
        }), 400

    try:
        layout_path = os.path.join('config', 'dashboards', dashboard_name, 'static_pack.yaml')

        if not os.path.exists(layout_path):
            return jsonify({'error': f'Dashboard layout not found: {dashboard_name}'}), 404

        layout = parse_dashboard_layout(layout_path)
        image_data = file.read()

        cropper = VisionPanelCropper(API_KEY)
        cropped_image, metadata = cropper.crop_panel(image_data, layout, panel_id)

        if return_metadata:
            cropped_base64 = base64.standard_b64encode(cropped_image).decode('utf-8')
            return jsonify({
                'success': True,
                'panel_id': panel_id,
                'dashboard': dashboard_name,
                'image': cropped_base64,
                'metadata': metadata
            })
        else:
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
