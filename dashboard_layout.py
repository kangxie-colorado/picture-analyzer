"""
Dashboard layout parser for understanding dashboard structure from YAML files
"""
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Panel:
    """Represents a single panel in the dashboard"""
    id: str
    role: str
    source: Optional[str] = None
    row_id: str = ""

    def __repr__(self):
        return f"Panel(id='{self.id}', role='{self.role}', row='{self.row_id}')"


@dataclass
class Row:
    """Represents a row of panels in the dashboard"""
    id: str
    title: str
    intent: str
    panels: List[Panel]
    relationships: List[str]

    def __repr__(self):
        return f"Row(id='{self.id}', title='{self.title}', panels={len(self.panels)})"


@dataclass
class DashboardLayout:
    """Represents the complete dashboard layout"""
    id: str
    human_name: str
    layout_description: List[str]
    analysis_objectives: List[str]
    analysis_tips: List[str]
    rows: List[Row]

    def get_panel(self, panel_id: str) -> Optional[Panel]:
        """Get a panel by its ID"""
        for row in self.rows:
            for panel in row.panels:
                if panel.id == panel_id:
                    return panel
        return None

    def get_row(self, row_id: str) -> Optional[Row]:
        """Get a row by its ID"""
        for row in self.rows:
            if row.id == row_id:
                return row
        return None

    def get_panels_in_row(self, row_id: str) -> List[Panel]:
        """Get all panels in a specific row"""
        row = self.get_row(row_id)
        return row.panels if row else []

    def list_all_panels(self) -> List[Panel]:
        """Get all panels in the dashboard"""
        panels = []
        for row in self.rows:
            panels.extend(row.panels)
        return panels

    def __repr__(self):
        return f"DashboardLayout(id='{self.id}', name='{self.human_name}', rows={len(self.rows)})"


def parse_dashboard_layout(yaml_path: str) -> DashboardLayout:
    """
    Parse a dashboard layout YAML file

    Args:
        yaml_path: Path to the YAML file

    Returns:
        DashboardLayout object
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    dashboard_data = data.get('dashboard_static', {})

    # Parse rows and panels
    rows = []
    for row_data in dashboard_data.get('rows', []):
        panels = []
        for panel_data in row_data.get('panels', []):
            panel = Panel(
                id=panel_data.get('id', ''),
                role=panel_data.get('role', ''),
                source=panel_data.get('source'),
                row_id=row_data.get('id', '')
            )
            panels.append(panel)

        row = Row(
            id=row_data.get('id', ''),
            title=row_data.get('title', ''),
            intent=row_data.get('intent', ''),
            panels=panels,
            relationships=row_data.get('relationships', [])
        )
        rows.append(row)

    # Create dashboard layout
    layout = DashboardLayout(
        id=dashboard_data.get('id', ''),
        human_name=dashboard_data.get('human_name', ''),
        layout_description=dashboard_data.get('layout_description', []),
        analysis_objectives=dashboard_data.get('analysis_objectives', []),
        analysis_tips=dashboard_data.get('analysis_tips', []),
        rows=rows
    )

    return layout


def parse_panel_id(panel_id: str) -> Dict[str, str]:
    """
    Parse a panel ID like 'S1-L-write' or 'S3-L2-value_size'

    Returns:
        dict with 'row', 'position', 'name'
    """
    parts = panel_id.split('-')
    if len(parts) < 2:
        return {'row': '', 'position': '', 'name': panel_id}

    return {
        'row': parts[0],  # e.g., 'S1'
        'position': parts[1],  # e.g., 'L', 'R', 'L2'
        'name': '-'.join(parts[2:]) if len(parts) > 2 else ''  # e.g., 'write', 'value_size'
    }


def get_row_position(row_id: str) -> int:
    """
    Extract row number from row ID like 'S1', 'S2', etc.

    Returns:
        Row number (1-indexed), or 0 if cannot parse
    """
    if row_id.startswith('S') and len(row_id) > 1:
        try:
            return int(row_id[1:])
        except ValueError:
            return 0
    return 0


def get_position_info(position: str) -> Dict[str, any]:
    """
    Parse position string like 'L', 'R', 'L2', 'R3'

    Returns:
        dict with 'side' (left/right), 'index' (0-indexed within that side)
    """
    if not position:
        return {'side': 'left', 'index': 0}

    side = 'left' if position.startswith('L') else 'right'

    # Extract index if present (L2 -> index 1, L -> index 0)
    index_str = position[1:] if len(position) > 1 else ''
    index = (int(index_str) - 1) if index_str.isdigit() else 0

    return {'side': side, 'index': index}
