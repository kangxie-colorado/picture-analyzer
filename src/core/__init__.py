"""
Core functionality for panel detection and cropping
"""
from .layout import (
    DashboardLayout,
    Panel,
    Row,
    parse_dashboard_layout,
    parse_panel_id,
    get_row_position,
    get_position_info
)
from .vision_cropper import VisionPanelCropper
from .coordinate_cropper import CoordinatePanelCropper
from .image_ops import crop_image, load_image, save_image, get_image_dimensions

__all__ = [
    'DashboardLayout',
    'Panel',
    'Row',
    'parse_dashboard_layout',
    'parse_panel_id',
    'get_row_position',
    'get_position_info',
    'VisionPanelCropper',
    'CoordinatePanelCropper',
    'crop_image',
    'load_image',
    'save_image',
    'get_image_dimensions',
]
