"""
Image manipulation operations for panel cropping
"""
from PIL import Image
from io import BytesIO
from typing import Dict


def crop_image(image_data: bytes, boundaries: Dict[str, int]) -> bytes:
    """
    Crop an image based on bounding box coordinates

    Args:
        image_data: Original image bytes
        boundaries: Dict with x, y, width, height

    Returns:
        Cropped image bytes (PNG format)
    """
    # Open image
    image = Image.open(BytesIO(image_data))

    # Extract coordinates
    left = boundaries['x']
    top = boundaries['y']
    right = left + boundaries['width']
    bottom = top + boundaries['height']

    # Ensure coordinates are within image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)

    # Crop
    cropped = image.crop((left, top, right, bottom))

    # Convert to bytes
    output = BytesIO()
    cropped.save(output, format='PNG')
    return output.getvalue()


def load_image(image_path: str) -> bytes:
    """Load image file as bytes"""
    with open(image_path, 'rb') as f:
        return f.read()


def get_image_dimensions(image_data: bytes) -> tuple[int, int]:
    """Get image dimensions (width, height)"""
    image = Image.open(BytesIO(image_data))
    return image.width, image.height


def save_image(image_data: bytes, output_path: str):
    """Save image bytes to file"""
    with open(output_path, 'wb') as f:
        f.write(image_data)
