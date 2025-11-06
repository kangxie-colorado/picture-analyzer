"""
Flask API application
"""
from flask import Flask
from flask_cors import CORS
import os

from .routes import api


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)

    # Configuration
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(api)

    # Check API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("WARNING: ANTHROPIC_API_KEY not set in environment variables")

    return app


def run_server(host='0.0.0.0', port=None, debug=False):
    """Run the Flask development server"""
    app = create_app()
    port = port or int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    run_server(debug=debug_mode)
