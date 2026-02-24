"""
PreViz - Interactive Film Production Planning Tool
Educational Technology for Digital Media Arts
Developed by: Eduardo Carmona
Version: 4.0 (Phase 1 Update)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime
import copy

# Page Configuration
st.set_page_config(
    page_title="PreViz 4.0 - Film Production Planning",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .version-badge {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
    /* Icon palette grid */
    .icon-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        margin: 8px 0 12px 0;
    }
    .icon-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 8px 4px 6px 4px;
        cursor: pointer;
        transition: all 0.15s ease;
        text-decoration: none;
        min-height: 68px;
    }
    .icon-card:hover {
        background: #e8f4fd;
        border-color: #2196F3;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(33,150,243,0.18);
    }
    .icon-card.selected {
        background: #1976D2;
        border-color: #1565C0;
        box-shadow: 0 4px 12px rgba(25,118,210,0.35);
    }
    .icon-card.selected .icon-emoji {
        filter: grayscale(0);
    }
    .icon-card.selected .icon-label {
        color: white;
    }
    .icon-emoji {
        font-size: 1.7rem;
        line-height: 1;
        margin-bottom: 4px;
    }
    .icon-label {
        font-size: 0.58rem;
        font-weight: 600;
        color: #444;
        text-align: center;
        line-height: 1.2;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .palette-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 10px 0 6px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scene_elements' not in st.session_state:
    st.session_state.scene_elements = {
        'cameras': [],
        'lights': [],
        'actors': [],
        'set_pieces': [],
        'props': [],
        'vehicles': [],
        'screens': [],
        'green_screens': []
    }

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Perspective"

if 'scene_name' not in st.session_state:
    st.session_state.scene_name = "Untitled Scene"

if 'clipboard' not in st.session_state:
    st.session_state.clipboard = None

if 'selected_element' not in st.session_state:
    st.session_state.selected_element = None

# Camera height presets
CAMERA_HEIGHT_PRESETS = {
    "Eye Level (5 ft)": 5.0,
    "Shoulder Level (4.5 ft)": 4.5,
    "Chest Level (4 ft)": 4.0,
    "Waist Level (3 ft)": 3.0,
    "Low Angle (2 ft)": 2.0,
    "Ground Level (0.5 ft)": 0.5,
    "High Angle (7 ft)": 7.0,
    "Overhead (9 ft)": 9.0,
    "Crane Height (12 ft)": 12.0
}

# Field of View presets (based on focal length)
FOV_PRESETS = {
    "16mm (Ultra Wide)": 107,
    "24mm (Wide)": 84,
    "35mm (Standard Wide)": 63,
    "50mm (Normal)": 47,
    "85mm (Portrait)": 29,
    "135mm (Telephoto)": 18,
    "200mm (Super Telephoto)": 12
}

# Helper Functions
def angle_to_radians(angle_deg):
    """Convert degrees to radians"""
    return np.radians(angle_deg)

def rotate_point(x, y, angle_deg):
    """Rotate a point around origin by angle in degrees"""
    angle_rad = angle_to_radians(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x, new_y

def create_camera_frustum(x, y, z, rotation, fov=60, name="Camera"):
    """Create enhanced camera frustum with rotation and FOV"""
    cone_length = 4
    cone_width = np.tan(np.radians(fov/2)) * cone_length
    
    # Base cone points (before rotation)
    points = [
        (0, 0),  # apex
        (-cone_width, cone_length),  # left far
        (cone_width, cone_length),   # right far
    ]
    
    # Rotate all points
    rotated_points = [rotate_point(px, py, rotation) for px, py in points]
    
    # Add world position
    world_points = [(x + px, y + py, z) for px, py, _ in rotated_points]
    
    return world_points

def create_light_coverage(x, y, z, rotation, intensity, light_type):
    """Create light coverage visualization based on type"""
    if light_type in ["Key Light", "Fill Light", "Back Light"]:
        beam_length = intensity / 15
    elif light_type == "LED Panel":
        beam_length = intensity / 25
    elif light_type == "Practical":
        beam_length = intensity / 40
    else:  # Natural Light
        beam_length = intensity / 10
    
    # Direction vector (rotated)
    dx, dy = rotate_point(0, beam_length, rotation)
    
    return [x, y, z, x + dx, y + dy, z]

def duplicate_element(element_type, element_data):
    """Duplicate an element with offset position"""
    new_element = copy.deepcopy(element_data)
    new_element['x'] += 1.0  # Offset by 1 foot
    new_element['y'] += 1.0
    
    # Rename
    original_name = new_element['name']
    if 'Copy' in original_name:
        # Find number in "Copy N" and increment
        try:
            parts = original_name.rsplit('Copy', 1)
            if len(parts) == 2 and parts[1].strip().isdigit():
                num = int(parts[1].strip()) + 1
                new_element['name'] = f"{parts[0]}Copy {num}"
            else:
                new_element['name'] = f"{original_name} Copy 2"
        except:
            new_element['name'] = f"{original_name} Copy"
    else:
        new_element['name'] = f"{original_name} Copy"
    
    return new_element

def generate_3d_scene(view_mode="Perspective"):
    """Generate enhanced 3D visualization"""
    fig = go.Figure()
    
    stage_size = 20
    
    # Draw stage floor grid
    grid_lines_x = []
    grid_lines_y = []
    for i in range(-stage_size//2, stage_size//2 + 1, 2):
        grid_lines_x.extend([i, i, None])
        grid_lines_y.extend([-stage_size//2, stage_size//2, None])
        grid_lines_x.extend([-stage_size//2, stage_size//2, None])
        grid_lines_y.extend([i, i, None])
    
    fig.add_trace(go.Scatter3d(
        x=grid_lines_x,
        y=grid_lines_y,
        z=[0] * len(grid_lines_x),
        mode='lines',
        line=dict(color='lightgray', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add cameras (with enhanced visualization)
    for cam in st.session_state.scene_elements['cameras']:
        # Camera body
        fig.add_trace(go.Scatter3d(
            x=[cam['x']],
            y=[cam['y']],
            z=[cam['z']],
            mode='markers+text',
            marker=dict(size=12, color='blue', symbol='diamond'),
            text=[cam['name']],
            textposition='top center',
            name=cam['name'],
            hovertemplate=f"<b>{cam['name']}</b><br>" +
                         f"Position: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f})<br>" +
                         f"Rotation: {cam['rotation']}Â°<br>" +
                         f"Focal Length: {cam['focal_length']}mm<br>" +
                         f"FOV: {cam['fov']}Â°<extra></extra>"
        ))
        
        # Camera viewing frustum
        frustum = create_camera_frustum(cam['x'], cam['y'], cam['z'], 
                                       cam['rotation'], cam['fov'])
        
        # Draw frustum edges
        fig.add_trace(go.Scatter3d(
            x=[frustum[0][0], frustum[1][0]],
            y=[frustum[0][1], frustum[1][1]],
            z=[frustum[0][2], frustum[1][2]],
            mode='lines',
            line=dict(color='blue', width=3, dash='dash'),
            showlegend=False,
            hoverinfo='skip',
            opacity=0.6
        ))
        fig.add_trace(go.Scatter3d(
            x=[frustum[0][0], frustum[2][0]],
            y=[frustum[0][1], frustum[2][1]],
            z=[frustum[0][2], frustum[2][2]],
            mode='lines',
            line=dict(color='blue', width=3, dash='dash'),
            showlegend=False,
            hoverinfo='skip',
            opacity=0.6
        ))
    
    # Add lights (with enhanced types and visualization)
    for light in st.session_state.scene_elements['lights']:
        # Light color based on type
        if light['type'] == "Key Light":
            color = 'yellow'
        elif light['type'] == "Fill Light":
            color = 'lightyellow'
        elif light['type'] == "Back Light":
            color = 'orange'
        elif light['type'] == "LED Panel":
            color = 'white'
        elif light['type'] == "Practical":
            color = 'gold'
        else:  # Natural Light
            color = 'lightblue'
        
        # Light fixture
        fig.add_trace(go.Scatter3d(
            x=[light['x']],
            y=[light['y']],
            z=[light['z']],
            mode='markers+text',
            marker=dict(size=10, color=color, symbol='diamond'),
            text=[light['name']],
            textposition='top center',
            name=light['name'],
            hovertemplate=f"<b>{light['name']}</b><br>" +
                         f"Type: {light['type']}<br>" +
                         f"Position: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f})<br>" +
                         f"Rotation: {light['rotation']}Â°<br>" +
                         f"Intensity: {light['intensity']}%<extra></extra>"
        ))
        
        # Light beam/coverage
        beam = create_light_coverage(light['x'], light['y'], light['z'], 
                                     light['rotation'], light['intensity'], 
                                     light['type'])
        fig.add_trace(go.Scatter3d(
            x=[beam[0], beam[3]],
            y=[beam[1], beam[4]],
            z=[beam[2], beam[5]],
            mode='lines',
            line=dict(color=color, width=4),
            showlegend=False,
            hoverinfo='skip',
            opacity=0.5
        ))
    
    # Add actors
    for actor in st.session_state.scene_elements['actors']:
        fig.add_trace(go.Scatter3d(
            x=[actor['x']],
            y=[actor['y']],
            z=[0],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='circle'),
            text=[actor['name']],
            textposition='top center',
            name=actor['name'],
            hovertemplate=f"<b>{actor['name']}</b><br>" +
                         f"Position: ({actor['x']:.1f}, {actor['y']:.1f})<br>" +
                         f"Notes: {actor['notes']}<extra></extra>"
        ))
    
    # Add set pieces
    for piece in st.session_state.scene_elements['set_pieces']:
        # Different colors for different types
        color_map = {
            'Table': 'brown',
            'Chair': 'saddlebrown',
            'Sofa': 'tan',
            'Desk': 'sienna',
            'Wall': 'gray',
            'Door': 'darkgray',
            'Window': 'lightblue'
        }
        color = color_map.get(piece['type'], 'green')
        
        fig.add_trace(go.Scatter3d(
            x=[piece['x']],
            y=[piece['y']],
            z=[0],
            mode='markers+text',
            marker=dict(size=12, color=color, symbol='square'),
            text=[piece['name']],
            textposition='top center',
            name=piece['name'],
            hovertemplate=f"<b>{piece['name']}</b><br>" +
                         f"Type: {piece['type']}<br>" +
                         f"Position: ({piece['x']:.1f}, {piece['y']:.1f})<extra></extra>"
        ))
    
    # Add props
    for prop in st.session_state.scene_elements.get('props', []):
        prop_color_map = {
            'Weapon': 'darkred',
            'Phone': 'purple',
            'Bag / Briefcase': 'saddlebrown',
            'Food / Drink': 'orange',
            'Book / Document': 'khaki',
            'Electronics': 'steelblue',
            'Tool': 'dimgray',
            'Other': 'olive'
        }
        color = prop_color_map.get(prop.get('type', 'Other'), 'olive')
        
        fig.add_trace(go.Scatter3d(
            x=[prop['x']],
            y=[prop['y']],
            z=[0.5],
            mode='markers+text',
            marker=dict(size=8, color=color, symbol='cross'),
            text=[f"🎭 {prop['name']}"],
            textposition='top center',
            name=prop['name'],
            hovertemplate=f"<b>{prop['name']}</b><br>" +
                         f"Type: {prop.get('type', 'Prop')}<br>" +
                         f"Position: ({prop['x']:.1f}, {prop['y']:.1f})<br>" +
                         f"Notes: {prop.get('notes', '')}<extra></extra>"
        ))
    
    # Add vehicles
    for vehicle in st.session_state.scene_elements['vehicles']:
        fig.add_trace(go.Scatter3d(
            x=[vehicle['x']],
            y=[vehicle['y']],
            z=[0],
            mode='markers+text',
            marker=dict(size=18, color='darkblue', symbol='square'),
            text=[vehicle['name']],
            textposition='top center',
            name=vehicle['name'],
            hovertemplate=f"<b>{vehicle['name']}</b><br>" +
                         f"Type: {vehicle['type']}<br>" +
                         f"Rotation: {vehicle['rotation']}Â°<br>" +
                         f"Position: ({vehicle['x']:.1f}, {vehicle['y']:.1f})<extra></extra>"
        ))
    
    # Add screens/monitors
    for screen in st.session_state.scene_elements['screens']:
        fig.add_trace(go.Scatter3d(
            x=[screen['x']],
            y=[screen['y']],
            z=[screen['z']],
            mode='markers+text',
            marker=dict(size=14, color='black', symbol='square'),
            text=[screen['name']],
            textposition='top center',
            name=screen['name'],
            hovertemplate=f"<b>{screen['name']}</b><br>" +
                         f"Size: {screen['size']}<br>" +
                         f"Height: {screen['z']} ft<br>" +
                         f"Position: ({screen['x']:.1f}, {screen['y']:.1f})<extra></extra>"
        ))
    
    # Add green screens
    for gs in st.session_state.scene_elements['green_screens']:
        # Draw as a vertical surface
        width = 8
        height = 8
        
        # Rotate points based on rotation
        corners = [
            (-width/2, 0), (width/2, 0),
            (width/2, 0), (width/2, 0),
            (-width/2, 0), (-width/2, 0)
        ]
        
        rotated = [rotate_point(px, py, gs['rotation']) for px, py in corners]
        
        fig.add_trace(go.Scatter3d(
            x=[gs['x'] + rotated[0][0], gs['x'] + rotated[1][0]],
            y=[gs['y'] + rotated[0][1], gs['y'] + rotated[1][1]],
            z=[0, height],
            mode='lines',
            line=dict(color='green', width=10),
            showlegend=False,
            hoverinfo='skip',
            opacity=0.6
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[gs['x']],
            y=[gs['y']],
            z=[height/2],
            mode='text',
            text=[gs['name']],
            textposition='middle center',
            name=gs['name'],
            hovertemplate=f"<b>{gs['name']}</b><br>" +
                         f"Size: {gs['size']}<br>" +
                         f"Rotation: {gs['rotation']}Â°<extra></extra>"
        ))
    
    # Set camera view
    if view_mode == "Top-Down":
        camera = dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))
    elif view_mode == "Side View":
        camera = dict(eye=dict(x=2.5, y=0, z=0.5), up=dict(x=0, y=0, z=1))
    else:
        camera = dict(eye=dict(x=1.5, y=-1.5, z=1.5), up=dict(x=0, y=0, z=1))
    
    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-stage_size//2, stage_size//2], title="X (feet)"),
            yaxis=dict(range=[-stage_size//2, stage_size//2], title="Y (feet)"),
            zaxis=dict(range=[0, 15], title="Z (feet)"),
            aspectmode='cube',
            camera=camera,
            bgcolor='rgb(245,242,235)'
        ),
        height=650,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(
            text=f"\u1F3AC  {st.session_state.scene_name}  \u00B7  {view_mode} View",
            font=dict(size=15, color='#333'),
            x=0.01
        ),
        showlegend=True,
        legend=dict(
            x=0.01, y=0.99,
            xanchor='left', yanchor='top',
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#ccc',
            borderwidth=1,
            font=dict(size=11),
            itemsizing='constant',
            itemwidth=30
        ),
        paper_bgcolor='white',
    )
    
    return fig

def export_setup_report():
    """Generate comprehensive setup report"""
    report = f"""
PRODUCTION SETUP REPORT
=====================================
Scene: {st.session_state.scene_name}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
=====================================

CAMERAS ({len(st.session_state.scene_elements['cameras'])})
-------------------------------------
"""
    for i, cam in enumerate(st.session_state.scene_elements['cameras'], 1):
        report += f"""
{i}. {cam['name']}
   Position: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) feet
   Rotation: {cam['rotation']}Â°
   Focal Length: {cam['focal_length']}mm
   Field of View: {cam['fov']}Â°
"""
    
    report += f"""
LIGHTING ({len(st.session_state.scene_elements['lights'])})
-------------------------------------
"""
    for i, light in enumerate(st.session_state.scene_elements['lights'], 1):
        report += f"""
{i}. {light['name']}
   Type: {light['type']}
   Position: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) feet
   Rotation: {light['rotation']}Â°
   Intensity: {light['intensity']}%
"""
    
    report += f"""
TALENT ({len(st.session_state.scene_elements['actors'])})
-------------------------------------
"""
    for i, actor in enumerate(st.session_state.scene_elements['actors'], 1):
        report += f"""
{i}. {actor['name']}
   Position: ({actor['x']:.1f}, {actor['y']:.1f}) feet
   Notes: {actor['notes']}
"""
    
    if st.session_state.scene_elements['set_pieces']:
        report += f"""
SET PIECES ({len(st.session_state.scene_elements['set_pieces'])})
-------------------------------------
"""
        for i, piece in enumerate(st.session_state.scene_elements['set_pieces'], 1):
            report += f"""
{i}. {piece['name']} ({piece['type']})
   Position: ({piece['x']:.1f}, {piece['y']:.1f}) feet
"""
    
    if st.session_state.scene_elements['vehicles']:
        report += f"""
VEHICLES ({len(st.session_state.scene_elements['vehicles'])})
-------------------------------------
"""
        for i, veh in enumerate(st.session_state.scene_elements['vehicles'], 1):
            report += f"""
{i}. {veh['name']} ({veh['type']})
   Position: ({veh['x']:.1f}, {veh['y']:.1f}) feet
   Rotation: {veh['rotation']}Â°
"""
    
    if st.session_state.scene_elements['screens']:
        report += f"""
SCREENS/MONITORS ({len(st.session_state.scene_elements['screens'])})
-------------------------------------
"""
        for i, scr in enumerate(st.session_state.scene_elements['screens'], 1):
            report += f"""
{i}. {scr['name']} ({scr['size']})
   Position: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f}) feet
"""
    
    if st.session_state.scene_elements['green_screens']:
        report += f"""
GREEN SCREENS ({len(st.session_state.scene_elements['green_screens'])})
-------------------------------------
"""
        for i, gs in enumerate(st.session_state.scene_elements['green_screens'], 1):
            report += f"""
{i}. {gs['name']} ({gs['size']})
   Position: ({gs['x']:.1f}, {gs['y']:.1f}) feet
   Rotation: {gs['rotation']}Â°
"""
    
    report += """
=====================================
Equipment Checklist:
"""
    report += f"  â˜ {len(st.session_state.scene_elements['cameras'])} Camera(s)\n"
    report += f"  â˜ {len(st.session_state.scene_elements['lights'])} Light(s)\n"
    if st.session_state.scene_elements['screens']:
        report += f"  â˜ {len(st.session_state.scene_elements['screens'])} Monitor(s)\n"
    if st.session_state.scene_elements['green_screens']:
        report += f"  â˜ {len(st.session_state.scene_elements['green_screens'])} Green Screen(s)\n"
    
    return report

def export_scene_json():
    """Export scene as JSON"""
    scene_data = {
        'scene_name': st.session_state.scene_name,
        'created': datetime.now().isoformat(),
        'elements': st.session_state.scene_elements,
        'version': '4.0'
    }
    return json.dumps(scene_data, indent=2)

# Main Application
def main():
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header">ðŸŽ¬ PreViz 3.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Interactive Film Production Planning Tool</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="version-badge">v4.0</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Scene Setup")
        
        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name
        
        st.divider()
        
        # === VISUAL ICON PALETTE ===
        st.markdown('<div class="palette-title">🎬 Add to Scene</div>', unsafe_allow_html=True)
        
        # Define icon palette — maps display to internal element_type string
        ICONS = [
            ("🎥", "Camera",        "Camera"),
            ("📷", "Action Cam",    "Camera"),
            ("🚁", "Drone",         "Camera"),
            ("💡", "Key Light",     "Light"),
            ("🔦", "LED Panel",     "Light"),
            ("🌤️", "Natural Light", "Light"),
            ("🧍", "Actor",         "Actor"),
            ("🎬", "Director",      "Actor"),
            ("🪑", "Dir. Chair",    "Set Piece"),
            ("🚪", "Door/Wall",     "Set Piece"),
            ("🪟", "Window",        "Set Piece"),
            ("🛋️", "Furniture",    "Set Piece"),
            ("🔫", "Weapon",        "Props"),
            ("📱", "Phone",         "Props"),
            ("🎒", "Bag",           "Props"),
            ("🍽️", "Food/Drink",   "Props"),
            ("📄", "Document",      "Props"),
            ("🚗", "Vehicle",       "Vehicle"),
            ("🚌", "Star Trailer",  "Vehicle"),
            ("🖥️", "Screen",       "Screen/Monitor"),
            ("📽️", "Projector",    "Screen/Monitor"),
            ("🟢", "Green Screen",  "Green Screen"),
        ]
        
        # Build icon grid HTML
        grid_html = '<div class="icon-grid">'
        for emoji, label, etype in ICONS:
            selected_cls = " selected" if st.session_state.selected_element == f"{label}|{etype}" else ""
            grid_html += f'''<div class="icon-card{selected_cls}">
                <div class="icon-emoji">{emoji}</div>
                <div class="icon-label">{label}</div>
            </div>'''
        grid_html += '</div>'
        
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # Functional selectbox hidden below — synced with icon clicks via label
        icon_labels = ["── Select ──"] + [f"{e} {l}" for e, l, _ in ICONS]
        icon_map = {f"{e} {l}": t for e, l, t in ICONS}
        
        chosen = st.selectbox(
            "Or pick from list:",
            icon_labels,
            label_visibility="collapsed"
        )
        element_type = icon_map.get(chosen, None)
        
        if element_type is None and chosen != "── Select ──":
            element_type = chosen
        
        if element_type == "Camera":
            st.subheader("ðŸ“· Add Camera")
            with st.form("camera_form"):
                cam_name = st.text_input("Camera Name", 
                    value=f"Camera {chr(65 + len(st.session_state.scene_elements['cameras']))}")  # A, B, C...
                
                col1, col2 = st.columns(2)
                with col1:
                    cam_x = st.number_input("X Position", value=0.0, step=0.5)
                    cam_y = st.number_input("Y Position", value=-5.0, step=0.5)
                with col2:
                    # Height preset selector
                    height_preset = st.selectbox("Height Preset", list(CAMERA_HEIGHT_PRESETS.keys()))
                    cam_z = st.number_input("Height (Z)", 
                        value=CAMERA_HEIGHT_PRESETS[height_preset], step=0.5, min_value=0.0)
                
                cam_rotation = st.slider("Rotation (degrees)", 0, 359, 0)
                
                # Focal length with FOV calculation
                focal_preset = st.selectbox("Focal Length Preset", list(FOV_PRESETS.keys()))
                cam_focal = int(focal_preset.split('mm')[0])
                cam_fov = FOV_PRESETS[focal_preset]
                
                st.caption(f"Field of View: {cam_fov}Â°")
                
                if st.form_submit_button("Add Camera"):
                    st.session_state.scene_elements['cameras'].append({
                        'name': cam_name,
                        'x': cam_x,
                        'y': cam_y,
                        'z': cam_z,
                        'rotation': cam_rotation,
                        'focal_length': cam_focal,
                        'fov': cam_fov
                    })
                    st.success(f"Added {cam_name}")
                    st.rerun()
        
        elif element_type == "Light":
            st.subheader("ðŸ’¡ Add Light")
            with st.form("light_form"):
                light_name = st.text_input("Light Name", 
                    value=f"Light {len(st.session_state.scene_elements['lights'])+1}")
                light_type = st.selectbox("Type", 
                    ["Key Light", "Fill Light", "Back Light", "LED Panel", "Practical", "Natural Light"])
                
                col1, col2 = st.columns(2)
                with col1:
                    light_x = st.number_input("X Position", value=3.0, step=0.5)
                    light_y = st.number_input("Y Position", value=0.0, step=0.5)
                    light_z = st.number_input("Height (Z)", value=7.0, step=0.5, min_value=0.0)
                with col2:
                    light_rotation = st.slider("Rotation", 0, 359, 0, key="light_rot")
                    light_intensity = st.slider("Intensity (%)", 0, 100, 80, key="light_int")
                
                if st.form_submit_button("Add Light"):
                    st.session_state.scene_elements['lights'].append({
                        'name': light_name,
                        'type': light_type,
                        'x': light_x,
                        'y': light_y,
                        'z': light_z,
                        'rotation': light_rotation,
                        'intensity': light_intensity
                    })
                    st.success(f"Added {light_name}")
                    st.rerun()
        
        elif element_type == "Actor":
            st.subheader("ðŸŽ­ Add Actor")
            with st.form("actor_form"):
                actor_name = st.text_input("Actor/Character Name", 
                    value=f"Actor {len(st.session_state.scene_elements['actors'])+1}")
                col1, col2 = st.columns(2)
                with col1:
                    actor_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    actor_y = st.number_input("Y Position", value=0.0, step=0.5)
                
                actor_notes = st.text_area("Blocking Notes", 
                    placeholder="e.g., Standing, sitting, walking towards...")
                
                if st.form_submit_button("Add Actor"):
                    st.session_state.scene_elements['actors'].append({
                        'name': actor_name,
                        'x': actor_x,
                        'y': actor_y,
                        'notes': actor_notes
                    })
                    st.success(f"Added {actor_name}")
                    st.rerun()
        
        elif element_type == "Set Piece":
            st.subheader("ðŸª‘ Add Set Piece")
            with st.form("setpiece_form"):
                piece_name = st.text_input("Name", value="Furniture")
                piece_type = st.selectbox("Type", 
                    ["Table", "Chair", "Sofa", "Desk", "Wall", "Door", "Window"])
                
                col1, col2 = st.columns(2)
                with col1:
                    piece_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    piece_y = st.number_input("Y Position", value=0.0, step=0.5)
                
                if st.form_submit_button("Add Set Piece"):
                    st.session_state.scene_elements['set_pieces'].append({
                        'name': piece_name,
                        'type': piece_type,
                        'x': piece_x,
                        'y': piece_y
                    })
                    st.success(f"Added {piece_name}")
                    st.rerun()
        
        elif element_type == "Props":
            st.subheader("🎭 Add Prop")
            with st.form("props_form"):
                prop_name = st.text_input("Prop Name", value="Prop")
                prop_type = st.selectbox("Category", 
                    ["Weapon", "Phone", "Bag / Briefcase", "Food / Drink", 
                     "Book / Document", "Electronics", "Tool", "Other"])
                
                col1, col2 = st.columns(2)
                with col1:
                    prop_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    prop_y = st.number_input("Y Position", value=0.0, step=0.5)
                
                prop_notes = st.text_input("Notes", placeholder="e.g., Hero prop, breakaway")
                
                if st.form_submit_button("Add Prop"):
                    if 'props' not in st.session_state.scene_elements:
                        st.session_state.scene_elements['props'] = []
                    st.session_state.scene_elements['props'].append({
                        'name': prop_name,
                        'type': prop_type,
                        'x': prop_x,
                        'y': prop_y,
                        'notes': prop_notes
                    })
                    st.success(f"Added {prop_name}")
                    st.rerun()
        
        elif element_type == "Vehicle":
            st.subheader("ðŸš— Add Vehicle")
            with st.form("vehicle_form"):
                veh_name = st.text_input("Name", value="Car")
                veh_type = st.selectbox("Type", ["Car", "Van", "Truck", "Motorcycle", "Bicycle"])
                
                col1, col2 = st.columns(2)
                with col1:
                    veh_x = st.number_input("X Position", value=0.0, step=0.5)
                    veh_y = st.number_input("Y Position", value=0.0, step=0.5)
                with col2:
                    veh_rotation = st.slider("Rotation", 0, 359, 0, key="veh_rot")
                
                if st.form_submit_button("Add Vehicle"):
                    st.session_state.scene_elements['vehicles'].append({
                        'name': veh_name,
                        'type': veh_type,
                        'x': veh_x,
                        'y': veh_y,
                        'rotation': veh_rotation
                    })
                    st.success(f"Added {veh_name}")
                    st.rerun()
        
        elif element_type == "Screen/Monitor":
            st.subheader("ðŸ–¥ï¸ Add Screen")
            with st.form("screen_form"):
                scr_name = st.text_input("Name", value="Monitor")
                scr_size = st.selectbox("Size", 
                    ["24\" Monitor", "32\" Monitor", "55\" TV", "75\" TV", "Projector Screen"])
                
                col1, col2 = st.columns(2)
                with col1:
                    scr_x = st.number_input("X Position", value=0.0, step=0.5)
                    scr_y = st.number_input("Y Position", value=0.0, step=0.5)
                with col2:
                    scr_z = st.number_input("Height", value=3.0, step=0.5, min_value=0.0)
                
                if st.form_submit_button("Add Screen"):
                    st.session_state.scene_elements['screens'].append({
                        'name': scr_name,
                        'size': scr_size,
                        'x': scr_x,
                        'y': scr_y,
                        'z': scr_z
                    })
                    st.success(f"Added {scr_name}")
                    st.rerun()
        
        elif element_type == "Green Screen":
            st.subheader("ðŸŸ¢ Add Green Screen")
            with st.form("greenscreen_form"):
                gs_name = st.text_input("Name", value="Green Screen")
                gs_size = st.selectbox("Size", ["6x8 ft", "8x10 ft", "10x12 ft", "12x20 ft"])
                
                col1, col2 = st.columns(2)
                with col1:
                    gs_x = st.number_input("X Position", value=0.0, step=0.5)
                    gs_y = st.number_input("Y Position", value=5.0, step=0.5)
                with col2:
                    gs_rotation = st.slider("Rotation", 0, 359, 0, key="gs_rot")
                
                if st.form_submit_button("Add Green Screen"):
                    st.session_state.scene_elements['green_screens'].append({
                        'name': gs_name,
                        'size': gs_size,
                        'x': gs_x,
                        'y': gs_y,
                        'rotation': gs_rotation
                    })
                    st.success(f"Added {gs_name}")
                    st.rerun()
        
        st.divider()
        
        # Templates
        st.subheader("ðŸ“‹ Quick Templates")
        if st.button("Three-Point Lighting"):
            st.session_state.scene_elements['lights'] = [
                {'name': 'Key Light', 'type': 'Key Light', 'x': 3, 'y': 3, 'z': 6, 
                 'rotation': 225, 'intensity': 100},
                {'name': 'Fill Light', 'type': 'Fill Light', 'x': -3, 'y': 3, 'z': 5, 
                 'rotation': 135, 'intensity': 50},
                {'name': 'Back Light', 'type': 'Back Light', 'x': 0, 'y': -3, 'z': 7, 
                 'rotation': 0, 'intensity': 70}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Subject', 'x': 0, 'y': 0, 'notes': 'Center frame'}
            ]
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Main Camera', 'x': 0, 'y': -8, 'z': 5, 'rotation': 0, 
                 'focal_length': 50, 'fov': 47}
            ]
            st.rerun()
        
        if st.button("Multi-Camera Interview"):
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Camera A (Wide)', 'x': 0, 'y': -8, 'z': 5, 'rotation': 0, 
                 'focal_length': 35, 'fov': 63},
                {'name': 'Camera B (Close)', 'x': -3, 'y': -7, 'z': 4.5, 'rotation': 15, 
                 'focal_length': 85, 'fov': 29},
                {'name': 'Camera C (Over Shoulder)', 'x': 2, 'y': -2, 'z': 4, 'rotation': 180, 
                 'focal_length': 50, 'fov': 47}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Interviewee', 'x': 0, 'y': 0, 'notes': 'Seated, looking camera left'}
            ]
            st.session_state.scene_elements['set_pieces'] = [
                {'name': 'Interview Chair', 'type': 'Chair', 'x': 0, 'y': 0}
            ]
            st.rerun()
        
        if st.button("Green Screen Setup"):
            st.session_state.scene_elements['green_screens'] = [
                {'name': 'Main Green Screen', 'size': '12x20 ft', 'x': 0, 'y': 8, 'rotation': 0}
            ]
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Main Camera', 'x': 0, 'y': -6, 'z': 5, 'rotation': 0, 
                 'focal_length': 50, 'fov': 47}
            ]
            st.session_state.scene_elements['lights'] = [
                {'name': 'Subject Key', 'type': 'Key Light', 'x': 3, 'y': -2, 'z': 6, 
                 'rotation': 200, 'intensity': 100},
                {'name': 'Subject Fill', 'type': 'Fill Light', 'x': -3, 'y': -2, 'z': 5, 
                 'rotation': 160, 'intensity': 60},
                {'name': 'Green Screen Light L', 'type': 'LED Panel', 'x': -4, 'y': 6, 'z': 4, 
                 'rotation': 90, 'intensity': 80},
                {'name': 'Green Screen Light R', 'type': 'LED Panel', 'x': 4, 'y': 6, 'z': 4, 
                 'rotation': 90, 'intensity': 80}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Subject', 'x': 0, 'y': 2, 'notes': 'Standing 6 ft from green screen'}
            ]
            st.rerun()
        
        st.divider()
        
        # Clear scene
        if st.button("ðŸ—‘ï¸ Clear All Elements", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [], 'lights': [], 'actors': [],
                'set_pieces': [], 'props': [], 'vehicles': [], 'screens': [], 'green_screens': []
            }
            st.rerun()
        
        st.divider()
        
        # Scene Summary in sidebar
        st.subheader("📊 Scene Summary")
        elems = st.session_state.scene_elements
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("🎥 Cameras", len(elems['cameras']))
            st.metric("🎭 Actors", len(elems['actors']))
            st.metric("🎭 Props", len(elems.get('props', [])))
        with col_b:
            st.metric("💡 Lights", len(elems['lights']))
            st.metric("🪑 Set Pieces", len(elems['set_pieces']))
            st.metric("🚗 Vehicles", len(elems['vehicles']))
        
        st.divider()
        
        # Export in sidebar
        st.subheader("📤 Export")
        if st.button("📄 Setup Report"):
            report = export_setup_report()
            st.download_button(
                label="⬇️ Download Report",
                data=report,
                file_name=f"previz_{st.session_state.scene_name.replace(' ', '_')}.txt",
                mime="text/plain",
                key="dl_report"
            )
        if st.button("💾 Save Scene (JSON)"):
            scene_json = export_scene_json()
            st.download_button(
                label="⬇️ Download Scene",
                data=scene_json,
                file_name=f"scene_{st.session_state.scene_name.replace(' ', '_')}.json",
                mime="application/json",
                key="dl_scene"
            )
        uploaded_file = st.file_uploader("📥 Load Scene", type=['json'])
        if uploaded_file is not None:
            scene_data = json.loads(uploaded_file.read())
            st.session_state.scene_elements = scene_data['elements']
            st.session_state.scene_name = scene_data['scene_name']
            st.success("Scene loaded!")
            st.rerun()
    
    # Main content - full width 3D view
    view_mode = st.radio(
        "View Mode",
        ["Perspective", "Top-Down", "Side View"],
        horizontal=True
    )
    st.session_state.view_mode = view_mode
    
    fig = generate_3d_scene(view_mode)
    st.plotly_chart(fig, use_container_width=True)
    
    # Elements management tabs
    st.divider()
    st.subheader("Scene Elements")
    
    tabs = st.tabs(["📷 Cameras", "💡 Lights", "🎭 Actors", "🪑 Set Pieces", "🎭 Props", "🚗 Vehicles", "🖥️ Screens", "🟢 Green Screens"])

    
    # Cameras tab
    with tabs[0]:
        if st.session_state.scene_elements['cameras']:
            for i, cam in enumerate(st.session_state.scene_elements['cameras']):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    **{cam['name']}** | FL: {cam['focal_length']}mm | FOV: {cam['fov']}Â°  
                    Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) | Rot: {cam['rotation']}Â°
                    """)
                with col2:
                    if st.button("ðŸ“‹", key=f"copy_cam_{i}"):
                        dup = duplicate_element('cameras', cam)
                        st.session_state.scene_elements['cameras'].append(dup)
                        st.rerun()
                with col3:
                    if st.button("ðŸ—‘ï¸", key=f"del_cam_{i}"):
                        st.session_state.scene_elements['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras. Use sidebar to add.")
    
    # Lights tab
    with tabs[1]:
        if st.session_state.scene_elements['lights']:
            for i, light in enumerate(st.session_state.scene_elements['lights']):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    **{light['name']}** ({light['type']}) | {light['intensity']}%  
                    Pos: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) | Rot: {light['rotation']}Â°
                    """)
                with col2:
                    if st.button("ðŸ“‹", key=f"copy_light_{i}"):
                        dup = duplicate_element('lights', light)
                        st.session_state.scene_elements['lights'].append(dup)
                        st.rerun()
                with col3:
                    if st.button("ðŸ—‘ï¸", key=f"del_light_{i}"):
                        st.session_state.scene_elements['lights'].pop(i)
                        st.rerun()
        else:
            st.info("No lights. Use sidebar to add.")
    
    # Actors tab
    with tabs[2]:
        if st.session_state.scene_elements['actors']:
            for i, actor in enumerate(st.session_state.scene_elements['actors']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{actor['name']}** | Pos: ({actor['x']:.1f}, {actor['y']:.1f})  
                    {actor['notes']}
                    """)
                with col2:
                    if st.button("ðŸ—‘ï¸", key=f"del_actor_{i}"):
                        st.session_state.scene_elements['actors'].pop(i)
                        st.rerun()
        else:
            st.info("No actors. Use sidebar to add.")
    
    # Set pieces tab
    with tabs[3]:
        if st.session_state.scene_elements['set_pieces']:
            for i, piece in enumerate(st.session_state.scene_elements['set_pieces']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{piece['name']}** ({piece['type']}) | Pos: ({piece['x']:.1f}, {piece['y']:.1f})
                    """)
                with col2:
                    if st.button("ðŸ—‘ï¸", key=f"del_piece_{i}"):
                        st.session_state.scene_elements['set_pieces'].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces. Use sidebar to add.")
    
    # Props tab
    with tabs[4]:
        props_list = st.session_state.scene_elements.get('props', [])
        if props_list:
            for i, prop in enumerate(props_list):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{prop['name']}** ({prop.get('type', 'Prop')}) | Pos: ({prop['x']:.1f}, {prop['y']:.1f})  
                    {prop.get('notes', '')}
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_prop_{i}"):
                        st.session_state.scene_elements['props'].pop(i)
                        st.rerun()
        else:
            st.info("No props. Use sidebar to add.")
    
    # Vehicles tab
    with tabs[5]:
        if st.session_state.scene_elements['vehicles']:
            for i, veh in enumerate(st.session_state.scene_elements['vehicles']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{veh['name']}** ({veh['type']}) | Pos: ({veh['x']:.1f}, {veh['y']:.1f}) | Rot: {veh['rotation']}Â°
                    """)
                with col2:
                    if st.button("ðŸ—‘ï¸", key=f"del_veh_{i}"):
                        st.session_state.scene_elements['vehicles'].pop(i)
                        st.rerun()
        else:
            st.info("No vehicles. Use sidebar to add.")
    
    # Screens tab
    with tabs[6]:
        if st.session_state.scene_elements['screens']:
            for i, scr in enumerate(st.session_state.scene_elements['screens']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{scr['name']}** ({scr['size']}) | Pos: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f})
                    """)
                with col2:
                    if st.button("ðŸ—‘ï¸", key=f"del_scr_{i}"):
                        st.session_state.scene_elements['screens'].pop(i)
                        st.rerun()
        else:
            st.info("No screens. Use sidebar to add.")
    
    # Green screens tab
    with tabs[7]:
        if st.session_state.scene_elements['green_screens']:
            for i, gs in enumerate(st.session_state.scene_elements['green_screens']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{gs['name']}** ({gs['size']}) | Pos: ({gs['x']:.1f}, {gs['y']:.1f}) | Rot: {gs['rotation']}Â°
                    """)
                with col2:
                    if st.button("ðŸ—‘ï¸", key=f"del_gs_{i}"):
                        st.session_state.scene_elements['green_screens'].pop(i)
                        st.rerun()
        else:
            st.info("No green screens. Use sidebar to add.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        PreViz v3.0 Professional Edition | Educational Technology for Digital Media Arts<br>
        Developed by Eduardo Carmona | CSUDH & LMU
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
