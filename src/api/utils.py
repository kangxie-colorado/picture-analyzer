"""
API utility functions
"""
import mimetypes


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DEFAULT_ANALYSIS_PROMPT = """Please analyze this image in detail. Provide:
1. A description of what you see
2. Key objects, people, or elements present
3. The setting or context
4. Notable details, colors, or composition
5. Any text visible
6. The overall mood or purpose"""


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_image_media_type(filename: str) -> str:
    """Get the proper media type for an image file"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type

    # Fallback to common types
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    media_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')


def get_allowed_extensions_str() -> str:
    """Get comma-separated string of allowed extensions"""
    return ', '.join(sorted(ALLOWED_EXTENSIONS))
