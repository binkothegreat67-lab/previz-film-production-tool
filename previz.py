"""
PreViz - Interactive Film Production Planning Tool
Educational Technology for Digital Media Arts
Developed by: Eduardo Carmona
Version: 3.5 Phase 1 (Visual Clarity Update)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime
import copy

# Page Configuration
st.set_page_config(
    page_title="PreViz Beta 3.5 - Film Production Planning",
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
        background-color: #2196F3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
    .workflow-note {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
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
        'vehicles': [],
        'screens': [],
        'green_screens': []
    }

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Floor Plan"

if 'scene_name' not in st.session_state:
    st.session_state.scene_name = "Untitled Scene"

if 'editing_element' not in st.session_state:
    st.session_state.editing_element = None

if 'editing_type' not in st.session_state:
    st.session_state.editing_type = None

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
    world_points = [(x + px, y + py, z) for px, py in rotated_points]
    
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
    
    # Smart offset based on element type
    if element_type == 'cameras':
        new_element['x'] += 2.0
        new_element['y'] += 2.0
    else:
        new_element['x'] += 1.0
        new_element['y'] += 1.0
    
    # Rename
    original_name = new_element['name']
    if 'Copy' in original_name:
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

def generate_3d_scene(view_mode="Floor Plan"):
    """Generate enhanced visualization with clear, colored floor plan"""
    fig = go.Figure()
    
    stage_size = 20
    
    # PHASE 1 IMPROVEMENT: Clear visual boundaries
    if view_mode == "Floor Plan":
        # Tan/beige stage floor - clearly bounded
        bg_color = '#d4c4a8'  # Tan/beige
        stage_outline_color = '#8b7355'  # Dark brown
        paper_bg = '#f5f5f5'  # Light gray surrounding
        grid_visible = False  # NO GRID in floor plan
    else:
        bg_color = '#f0f0f0'
        stage_outline_color = 'lightgray'
        paper_bg = 'white'
        grid_visible = True
    
    # Draw stage floor outline (no fill - just boundaries)
    stage_half = stage_size // 2
    fig.add_trace(go.Scatter3d(
        x=[-stage_half, stage_half, stage_half, -stage_half, -stage_half],
        y=[-stage_half, -stage_half, stage_half, stage_half, -stage_half],
        z=[0, 0, 0, 0, 0],
        mode='lines',
        line=dict(color=stage_outline_color, width=6),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add cameras with IMPROVED VISIBILITY
    for cam in st.session_state.scene_elements['cameras']:
        # PHASE 1: Larger, more visible camera marker
        fig.add_trace(go.Scatter3d(
            x=[cam['x']],
            y=[cam['y']],
            z=[cam['z'] if view_mode != "Floor Plan" else 0],
            mode='markers+text',
            marker=dict(
                size=18,  # BIGGER
                color='blue',
                symbol='square',
                line=dict(color='darkblue', width=3)  # BOLD OUTLINE
            ),
            text=[f"📷 {cam['name']}"],  # EMOJI + NAME
            textposition='top center',
            textfont=dict(size=14, color='darkblue', family='Arial Black'),  # BOLD TEXT
            name=cam['name'],
            hovertemplate=f"<b>{cam['name']}</b><br>" +
                         f"Position: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f})<br>" +
                         f"Rotation: {cam['rotation']}°<br>" +
                         f"Focal Length: {cam['focal_length']}mm<br>" +
                         f"FOV: {cam['fov']}°<extra></extra>"
        ))
        
        # Camera viewing direction - BOLD ARROW
        if view_mode != "Floor Plan":
            frustum = create_camera_frustum(cam['x'], cam['y'], cam['z'], 
                                           cam['rotation'], cam['fov'])
            fig.add_trace(go.Scatter3d(
                x=[frustum[0][0], frustum[1][0]],
                y=[frustum[0][1], frustum[1][1]],
                z=[frustum[0][2], frustum[1][2]],
                mode='lines',
                line=dict(color='blue', width=4, dash='dash'),
                showlegend=False,
                hoverinfo='skip',
                opacity=0.7
            ))
            fig.add_trace(go.Scatter3d(
                x=[frustum[0][0], frustum[2][0]],
                y=[frustum[0][1], frustum[2][1]],
                z=[frustum[0][2], frustum[2][2]],
                mode='lines',
                line=dict(color='blue', width=4, dash='dash'),
                showlegend=False,
                hoverinfo='skip',
                opacity=0.7
            ))
        else:
            # Floor plan: THICK direction arrow
            arrow_length = 3
            dx, dy = rotate_point(0, arrow_length, cam['rotation'])
            fig.add_trace(go.Scatter3d(
                x=[cam['x'], cam['x'] + dx],
                y=[cam['y'], cam['y'] + dy],
                z=[0, 0],
                mode='lines',
                line=dict(color='blue', width=6),  # THICKER
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add lights with IMPROVED VISIBILITY
    for light in st.session_state.scene_elements['lights']:
        # Light color based on type
        if light['type'] == "Key Light":
            color = 'gold'
            emoji = "💡"
        elif light['type'] == "Fill Light":
            color = 'yellow'
            emoji = "💡"
        elif light['type'] == "Back Light":
            color = 'orange'
            emoji = "💡"
        elif light['type'] == "LED Panel":
            color = 'white'
            emoji = "⬜"
        elif light['type'] == "Practical":
            color = 'gold'
            emoji = "🔆"
        else:  # Natural Light
            color = 'lightblue'
            emoji = "☀️"
        
        # PHASE 1: Larger, clearer light markers
        z_pos = light['z'] if view_mode != "Floor Plan" else 0
        fig.add_trace(go.Scatter3d(
            x=[light['x']],
            y=[light['y']],
            z=[z_pos],
            mode='markers+text',
            marker=dict(
                size=16,  # BIGGER
                color=color,
                symbol='diamond',
                line=dict(color='black', width=2)  # BLACK OUTLINE
            ),
            text=[f"{emoji} {light['name']}"],  # EMOJI + NAME
            textposition='top center',
            textfont=dict(size=13, color='black', family='Arial Black'),  # BOLD
            name=light['name'],
            hovertemplate=f"<b>{light['name']}</b><br>" +
                         f"Type: {light['type']}<br>" +
                         f"Position: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f})<br>" +
                         f"Rotation: {light['rotation']}°<br>" +
                         f"Intensity: {light['intensity']}%<extra></extra>"
        ))
        
        # Light beam - BOLDER
        beam = create_light_coverage(light['x'], light['y'], light['z'], 
                                     light['rotation'], light['intensity'], 
                                     light['type'])
        beam_z_start = beam[2] if view_mode != "Floor Plan" else 0
        beam_z_end = beam[5] if view_mode != "Floor Plan" else 0
        
        fig.add_trace(go.Scatter3d(
            x=[beam[0], beam[3]],
            y=[beam[1], beam[4]],
            z=[beam_z_start, beam_z_end],
            mode='lines',
            line=dict(color=color, width=5),  # THICKER
            showlegend=False,
            hoverinfo='skip',
            opacity=0.6
        ))
    
    # Add actors with IMPROVED VISIBILITY
    for actor in st.session_state.scene_elements['actors']:
        fig.add_trace(go.Scatter3d(
            x=[actor['x']],
            y=[actor['y']],
            z=[0],
            mode='markers+text',
            marker=dict(
                size=20,  # LARGER
                color='red',
                symbol='circle',
                line=dict(color='darkred', width=3)  # BOLD OUTLINE
            ),
            text=[f"🎭 {actor['name']}"],  # EMOJI
            textposition='top center',
            textfont=dict(size=14, color='darkred', family='Arial Black'),
            name=actor['name'],
            hovertemplate=f"<b>{actor['name']}</b><br>" +
                         f"Position: ({actor['x']:.1f}, {actor['y']:.1f})<br>" +
                         f"Notes: {actor['notes']}<extra></extra>"
        ))
        
        # Movement arrow - BOLDER
        if 'move_to_x' in actor and 'move_to_y' in actor:
            fig.add_trace(go.Scatter3d(
                x=[actor['x'], actor['move_to_x']],
                y=[actor['y'], actor['move_to_y']],
                z=[0, 0],
                mode='lines',
                line=dict(color='red', width=5, dash='dot'),  # THICKER
                showlegend=False,
                hoverinfo='skip'
            ))
            # Arrow destination
            fig.add_trace(go.Scatter3d(
                x=[actor['move_to_x']],
                y=[actor['move_to_y']],
                z=[0],
                mode='markers',
                marker=dict(size=12, color='red', symbol='diamond'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add set pieces with IMPROVED VISIBILITY
    for piece in st.session_state.scene_elements['set_pieces']:
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
            marker=dict(
                size=16,  # LARGER
                color=color,
                symbol='square',
                line=dict(color='black', width=2)
            ),
            text=[f"🪑 {piece['name']}"],
            textposition='top center',
            textfont=dict(size=12, color='black', family='Arial Black'),
            name=piece['name'],
            hovertemplate=f"<b>{piece['name']}</b><br>" +
                         f"Type: {piece['type']}<br>" +
                         f"Position: ({piece['x']:.1f}, {piece['y']:.1f})<extra></extra>"
        ))
    
    # Add vehicles
    for vehicle in st.session_state.scene_elements['vehicles']:
        fig.add_trace(go.Scatter3d(
            x=[vehicle['x']],
            y=[vehicle['y']],
            z=[0],
            mode='markers+text',
            marker=dict(
                size=20,
                color='darkblue',
                symbol='square',
                line=dict(color='black', width=2)
            ),
            text=[f"🚗 {vehicle['name']}"],
            textposition='top center',
            textfont=dict(size=12, color='black', family='Arial Black'),
            name=vehicle['name'],
            hovertemplate=f"<b>{vehicle['name']}</b><br>" +
                         f"Type: {vehicle['type']}<br>" +
                         f"Rotation: {vehicle['rotation']}°<br>" +
                         f"Position: ({vehicle['x']:.1f}, {vehicle['y']:.1f})<extra></extra>"
        ))
    
    # Add screens/monitors
    for screen in st.session_state.scene_elements['screens']:
        z_pos = screen['z'] if view_mode != "Floor Plan" else 0
        fig.add_trace(go.Scatter3d(
            x=[screen['x']],
            y=[screen['y']],
            z=[z_pos],
            mode='markers+text',
            marker=dict(
                size=18,
                color='black',
                symbol='square',
                line=dict(color='white', width=2)
            ),
            text=[f"🖥️ {screen['name']}"],
            textposition='top center',
            textfont=dict(size=12, color='black', family='Arial Black'),
            name=screen['name'],
            hovertemplate=f"<b>{screen['name']}</b><br>" +
                         f"Size: {screen['size']}<br>" +
                         f"Height: {screen['z']} ft<br>" +
                         f"Position: ({screen['x']:.1f}, {screen['y']:.1f})<extra></extra>"
        ))
    
    # PHASE 1: GREEN SCREEN AS WALL (not just a line)
    for gs in st.session_state.scene_elements['green_screens']:
        if view_mode != "Floor Plan":
            # 3D view: vertical surface
            width = 8
            height = 8
            corners = [(-width/2, 0), (width/2, 0)]
            rotated = [rotate_point(px, py, gs['rotation']) for px, py in corners]
            
            fig.add_trace(go.Scatter3d(
                x=[gs['x'] + rotated[0][0], gs['x'] + rotated[1][0]],
                y=[gs['y'] + rotated[0][1], gs['y'] + rotated[1][1]],
                z=[0, height],
                mode='lines',
                line=dict(color='green', width=15),
                showlegend=False,
                hoverinfo='skip',
                opacity=0.7
            ))
        else:
            # FLOOR PLAN: Show green screen as THICK WALL
            width = 8
            # Calculate wall endpoints based on rotation
            half_width = width / 2
            left_point = rotate_point(-half_width, 0, gs['rotation'])
            right_point = rotate_point(half_width, 0, gs['rotation'])
            
            # Draw THICK green wall
            fig.add_trace(go.Scatter3d(
                x=[gs['x'] + left_point[0], gs['x'] + right_point[0]],
                y=[gs['y'] + left_point[1], gs['y'] + right_point[1]],
                z=[0, 0],
                mode='lines',
                line=dict(color='green', width=20),  # VERY THICK
                showlegend=False,
                hoverinfo='skip',
                opacity=0.8
            ))
        
        # Label marker
        fig.add_trace(go.Scatter3d(
            x=[gs['x']],
            y=[gs['y']],
            z=[0],
            mode='markers+text',
            marker=dict(
                size=14,
                color='green',
                symbol='square',
                line=dict(color='darkgreen', width=2)
            ),
            text=[f"🟢 {gs['name']}"],
            textposition='top center',
            textfont=dict(size=12, color='darkgreen', family='Arial Black'),
            name=gs['name'],
            hovertemplate=f"<b>{gs['name']}</b><br>" +
                         f"Size: {gs['size']}<br>" +
                         f"Rotation: {gs['rotation']}°<extra></extra>"
        ))
    
    # Set camera view
    if view_mode == "Floor Plan":
        camera = dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))
        scene_aspectmode = 'cube'
    elif view_mode == "Side View":
        camera = dict(eye=dict(x=2.5, y=0, z=0.5), up=dict(x=0, y=0, z=1))
        scene_aspectmode = 'cube'
    else:  # Perspective
        camera = dict(eye=dict(x=1.5, y=-1.5, z=1.5), up=dict(x=0, y=0, z=1))
        scene_aspectmode = 'cube'
    
    # Update layout with CLEAN appearance
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                range=[-stage_size//2, stage_size//2],
                title="X (feet)" if view_mode != "Floor Plan" else "",
                gridcolor='#bbb' if grid_visible else bg_color,
                showbackground=True,
                backgroundcolor=bg_color,
                showgrid=grid_visible,
                zeroline=False
            ),
            yaxis=dict(
                range=[-stage_size//2, stage_size//2],
                title="Y (feet)" if view_mode != "Floor Plan" else "",
                gridcolor='#bbb' if grid_visible else bg_color,
                showbackground=True,
                backgroundcolor=bg_color,
                showgrid=grid_visible,
                zeroline=False
            ),
            zaxis=dict(
                range=[0, 15],
                title="Z (feet)" if view_mode != "Floor Plan" else "",
                gridcolor='#bbb' if grid_visible else bg_color,
                showbackground=True,
                backgroundcolor=bg_color,
                showgrid=grid_visible,
                zeroline=False
            ),
            aspectmode=scene_aspectmode,
            camera=camera,
            bgcolor=paper_bg
        ),
        height=700,  # TALLER for better visibility
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(
            text=f"Scene: {st.session_state.scene_name} ({view_mode})",
            font=dict(size=20, family='Arial Black')
        ),
        paper_bgcolor=paper_bg,
        plot_bgcolor=bg_color
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
   Rotation: {cam['rotation']}°
   Focal Length: {cam['focal_length']}mm
   Field of View: {cam['fov']}°
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
   Rotation: {light['rotation']}°
   Intensity: {light['intensity']}%
"""
    
    report += f"""
TALENT ({len(st.session_state.scene_elements['actors'])})
-------------------------------------
"""
    for i, actor in enumerate(st.session_state.scene_elements['actors'], 1):
        movement = ""
        if 'move_to_x' in actor and 'move_to_y' in actor:
            movement = f"\n   Movement: → ({actor['move_to_x']:.1f}, {actor['move_to_y']:.1f})"
        report += f"""
{i}. {actor['name']}
   Position: ({actor['x']:.1f}, {actor['y']:.1f}) feet
   Notes: {actor['notes']}{movement}
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
   Rotation: {veh['rotation']}°
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
   Rotation: {gs['rotation']}°
"""
    
    report += """
=====================================
Equipment Checklist:
"""
    report += f"  ☐ {len(st.session_state.scene_elements['cameras'])} Camera(s)\n"
    report += f"  ☐ {len(st.session_state.scene_elements['lights'])} Light(s)\n"
    if st.session_state.scene_elements['screens']:
        report += f"  ☐ {len(st.session_state.scene_elements['screens'])} Monitor(s)\n"
    if st.session_state.scene_elements['green_screens']:
        report += f"  ☐ {len(st.session_state.scene_elements['green_screens'])} Green Screen(s)\n"
    
    return report

def export_scene_json():
    """Export scene as JSON"""
    scene_data = {
        'scene_name': st.session_state.scene_name,
        'created': datetime.now().isoformat(),
        'elements': st.session_state.scene_elements,
        'version': '3.5-phase1'
    }
    return json.dumps(scene_data, indent=2)

# Main Application
def main():
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header">🎬 PreViz Beta 3.5</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Film Production Planning - Phase 1 Visual Update</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="version-badge">Phase 1</div>', unsafe_allow_html=True)
    
    # Workflow guidance
    st.markdown("""
    <div class="workflow-note">
        <strong>📐 Start with Floor Plan:</strong> Tan stage = your work area. Place elements → Then verify in 3D
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Scene Setup")
        
        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name
        
        st.divider()
        
        # Check if editing mode
        if st.session_state.editing_element is not None:
            st.subheader(f"✏️ Editing {st.session_state.editing_type}")
            
            if st.session_state.editing_type == "Camera":
                cam = st.session_state.scene_elements['cameras'][st.session_state.editing_element]
                
                with st.form("edit_camera_form"):
                    cam_name = st.text_input("Camera Name", value=cam['name'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        cam_x = st.number_input("X Position", value=float(cam['x']), step=0.5)
                        cam_y = st.number_input("Y Position", value=float(cam['y']), step=0.5)
                    with col2:
                        height_preset_keys = list(CAMERA_HEIGHT_PRESETS.keys())
                        closest_preset = min(height_preset_keys, 
                                           key=lambda k: abs(CAMERA_HEIGHT_PRESETS[k] - cam['z']))
                        height_preset = st.selectbox("Height Preset", height_preset_keys,
                                                    index=height_preset_keys.index(closest_preset))
                        cam_z = st.number_input("Height (Z)", 
                            value=CAMERA_HEIGHT_PRESETS[height_preset], step=0.5, min_value=0.0)
                    
                    cam_rotation = st.slider("Rotation (degrees)", 0, 359, int(cam['rotation']))
                    
                    focal_preset_keys = list(FOV_PRESETS.keys())
                    current_focal_str = f"{cam['focal_length']}mm"
                    matching_preset = None
                    for key in focal_preset_keys:
                        if current_focal_str in key:
                            matching_preset = key
                            break
                    if matching_preset is None:
                        matching_preset = "50mm (Normal)"
                    
                    focal_preset = st.selectbox("Focal Length Preset", focal_preset_keys,
                                              index=focal_preset_keys.index(matching_preset))
                    cam_focal = int(focal_preset.split('mm')[0])
                    cam_fov = FOV_PRESETS[focal_preset]
                    
                    st.caption(f"Field of View: {cam_fov}°")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            st.session_state.scene_elements['cameras'][st.session_state.editing_element] = {
                                'name': cam_name,
                                'x': cam_x,
                                'y': cam_y,
                                'z': cam_z,
                                'rotation': cam_rotation,
                                'focal_length': cam_focal,
                                'fov': cam_fov
                            }
                            st.session_state.editing_element = None
                            st.session_state.editing_type = None
                            st.success("Camera updated!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_element = None
                            st.session_state.editing_type = None
                            st.rerun()
            
            elif st.session_state.editing_type == "Light":
                light = st.session_state.scene_elements['lights'][st.session_state.editing_element]
                
                with st.form("edit_light_form"):
                    light_name = st.text_input("Light Name", value=light['name'])
                    light_type = st.selectbox("Type", 
                        ["Key Light", "Fill Light", "Back Light", "LED Panel", "Practical", "Natural Light"],
                        index=["Key Light", "Fill Light", "Back Light", "LED Panel", "Practical", "Natural Light"].index(light['type']))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        light_x = st.number_input("X Position", value=float(light['x']), step=0.5)
                        light_y = st.number_input("Y Position", value=float(light['y']), step=0.5)
                        light_z = st.number_input("Height (Z)", value=float(light['z']), step=0.5, min_value=0.0)
                    with col2:
                        light_rotation = st.slider("Rotation", 0, 359, int(light['rotation']), key="edit_light_rot")
                        light_intensity = st.slider("Intensity (%)", 0, 100, int(light['intensity']), key="edit_light_int")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            st.session_state.scene_elements['lights'][st.session_state.editing_element] = {
                                'name': light_name,
                                'type': light_type,
                                'x': light_x,
                                'y': light_y,
                                'z': light_z,
                                'rotation': light_rotation,
                                'intensity': light_intensity
                            }
                            st.session_state.editing_element = None
                            st.session_state.editing_type = None
                            st.success("Light updated!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_element = None
                            st.session_state.editing_type = None
                            st.rerun()
        
        else:
            # Normal add mode
            element_type = st.selectbox(
                "Add Element",
                ["Select...", "Camera", "Light", "Actor", "Set Piece", "Vehicle", 
                 "Screen/Monitor", "Green Screen"]
            )
            
            if element_type == "Camera":
                st.subheader("📷 Add Camera")
                with st.form("camera_form"):
                    num_cameras = len(st.session_state.scene_elements['cameras'])
                    cam_name = st.text_input("Camera Name", 
                        value=f"Camera {chr(65 + num_cameras)}")
                    
                    base_x = 0.0 + (num_cameras * 2.0)
                    base_y = -5.0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        cam_x = st.number_input("X Position", value=base_x, step=0.5)
                        cam_y = st.number_input("Y Position", value=base_y, step=0.5)
                    with col2:
                        height_preset = st.selectbox("Height Preset", list(CAMERA_HEIGHT_PRESETS.keys()))
                        cam_z = st.number_input("Height (Z)", 
                            value=CAMERA_HEIGHT_PRESETS[height_preset], step=0.5, min_value=0.0)
                    
                    cam_rotation = st.slider("Rotation (degrees)", 0, 359, 0)
                    
                    focal_preset = st.selectbox("Focal Length Preset", list(FOV_PRESETS.keys()))
                    cam_focal = int(focal_preset.split('mm')[0])
                    cam_fov = FOV_PRESETS[focal_preset]
                    
                    st.caption(f"Field of View: {cam_fov}°")
                    
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
                st.subheader("💡 Add Light")
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
                st.subheader("🎭 Add Actor")
                with st.form("actor_form"):
                    actor_name = st.text_input("Actor/Character Name", 
                        value=f"Actor {len(st.session_state.scene_elements['actors'])+1}")
                    
                    st.markdown("**Starting Position**")
                    col1, col2 = st.columns(2)
                    with col1:
                        actor_x = st.number_input("X Position", value=0.0, step=0.5)
                    with col2:
                        actor_y = st.number_input("Y Position", value=0.0, step=0.5)
                    
                    actor_notes = st.text_area("Blocking Notes", 
                        placeholder="e.g., Standing, sitting, walking towards...")
                    
                    st.markdown("**Movement (Optional)**")
                    add_movement = st.checkbox("Add movement arrow")
                    
                    move_to_x = None
                    move_to_y = None
                    
                    if add_movement:
                        col1, col2 = st.columns(2)
                        with col1:
                            move_to_x = st.number_input("Move to X", value=2.0, step=0.5, key="move_x")
                        with col2:
                            move_to_y = st.number_input("Move to Y", value=2.0, step=0.5, key="move_y")
                    
                    if st.form_submit_button("Add Actor"):
                        actor_data = {
                            'name': actor_name,
                            'x': actor_x,
                            'y': actor_y,
                            'notes': actor_notes
                        }
                        if add_movement and move_to_x is not None:
                            actor_data['move_to_x'] = move_to_x
                            actor_data['move_to_y'] = move_to_y
                        
                        st.session_state.scene_elements['actors'].append(actor_data)
                        st.success(f"Added {actor_name}")
                        st.rerun()
            
            elif element_type == "Set Piece":
                st.subheader("🪑 Add Set Piece")
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
            
            elif element_type == "Vehicle":
                st.subheader("🚗 Add Vehicle")
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
                st.subheader("🖥️ Add Screen")
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
                st.subheader("🟢 Add Green Screen")
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
        st.subheader("📋 Quick Templates")
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
        if st.button("🗑️ Clear All Elements", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [], 'lights': [], 'actors': [],
                'set_pieces': [], 'vehicles': [], 'screens': [], 'green_screens': []
            }
            st.rerun()
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # View mode
        view_mode = st.radio(
            "View Mode",
            ["Floor Plan", "Perspective (3D)", "Side View (3D)"],
            horizontal=True,
            help="Start with Floor Plan (tan stage) for planning, use 3D for verification"
        )
        st.session_state.view_mode = view_mode
        
        # 3D Scene
        fig = generate_3d_scene(view_mode)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Scene Summary")
        st.metric("Cameras", len(st.session_state.scene_elements['cameras']))
        st.metric("Lights", len(st.session_state.scene_elements['lights']))
        st.metric("Actors", len(st.session_state.scene_elements['actors']))
        
        total_elements = (
            len(st.session_state.scene_elements['set_pieces']) +
            len(st.session_state.scene_elements['vehicles']) +
            len(st.session_state.scene_elements['screens']) +
            len(st.session_state.scene_elements['green_screens'])
        )
        st.metric("Set Elements", total_elements)
        
        st.divider()
        
        st.subheader("📤 Export")
        
        if st.button("📄 Setup Report"):
            report = export_setup_report()
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"previz_{st.session_state.scene_name.replace(' ', '_')}.txt",
                mime="text/plain"
            )
        
        if st.button("💾 Save Scene"):
            scene_json = export_scene_json()
            st.download_button(
                label="Download Scene",
                data=scene_json,
                file_name=f"scene_{st.session_state.scene_name.replace(' ', '_')}.json",
                mime="application/json"
            )
        
        uploaded_file = st.file_uploader("📥 Load Scene", type=['json'])
        if uploaded_file is not None:
            scene_data = json.loads(uploaded_file.read())
            st.session_state.scene_elements = scene_data['elements']
            st.session_state.scene_name = scene_data['scene_name']
            st.success("Scene loaded!")
            st.rerun()
    
    # Elements management tabs
    st.divider()
    st.subheader("Scene Elements")
    
    tabs = st.tabs(["📷 Cameras", "💡 Lights", "🎭 Actors", "🪑 Set Pieces", 
                    "🚗 Vehicles", "🖥️ Screens", "🟢 Green Screens"])
    
    # Cameras tab
    with tabs[0]:
        if st.session_state.scene_elements['cameras']:
            for i, cam in enumerate(st.session_state.scene_elements['cameras']):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"""
                    **{cam['name']}** | FL: {cam['focal_length']}mm | FOV: {cam['fov']}°  
                    Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) | Rot: {cam['rotation']}°
                    """)
                with col2:
                    if st.button("✏️", key=f"edit_cam_{i}"):
                        st.session_state.editing_element = i
                        st.session_state.editing_type = "Camera"
                        st.rerun()
                with col3:
                    if st.button("📋", key=f"copy_cam_{i}"):
                        dup = duplicate_element('cameras', cam)
                        st.session_state.scene_elements['cameras'].append(dup)
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_cam_{i}"):
                        st.session_state.scene_elements['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras. Use sidebar to add.")
    
    # Lights tab
    with tabs[1]:
        if st.session_state.scene_elements['lights']:
            for i, light in enumerate(st.session_state.scene_elements['lights']):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"""
                    **{light['name']}** ({light['type']}) | {light['intensity']}%  
                    Pos: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) | Rot: {light['rotation']}°
                    """)
                with col2:
                    if st.button("✏️", key=f"edit_light_{i}"):
                        st.session_state.editing_element = i
                        st.session_state.editing_type = "Light"
                        st.rerun()
                with col3:
                    if st.button("📋", key=f"copy_light_{i}"):
                        dup = duplicate_element('lights', light)
                        st.session_state.scene_elements['lights'].append(dup)
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_light_{i}"):
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
                    movement_text = ""
                    if 'move_to_x' in actor and 'move_to_y' in actor:
                        movement_text = f" → ({actor['move_to_x']:.1f}, {actor['move_to_y']:.1f})"
                    st.markdown(f"""
                    **{actor['name']}** | Pos: ({actor['x']:.1f}, {actor['y']:.1f}){movement_text}  
                    {actor['notes']}
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_actor_{i}"):
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
                    if st.button("🗑️", key=f"del_piece_{i}"):
                        st.session_state.scene_elements['set_pieces'].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces. Use sidebar to add.")
    
    # Vehicles tab
    with tabs[4]:
        if st.session_state.scene_elements['vehicles']:
            for i, veh in enumerate(st.session_state.scene_elements['vehicles']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{veh['name']}** ({veh['type']}) | Pos: ({veh['x']:.1f}, {veh['y']:.1f}) | Rot: {veh['rotation']}°
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_veh_{i}"):
                        st.session_state.scene_elements['vehicles'].pop(i)
                        st.rerun()
        else:
            st.info("No vehicles. Use sidebar to add.")
    
    # Screens tab
    with tabs[5]:
        if st.session_state.scene_elements['screens']:
            for i, scr in enumerate(st.session_state.scene_elements['screens']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{scr['name']}** ({scr['size']}) | Pos: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f})
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_scr_{i}"):
                        st.session_state.scene_elements['screens'].pop(i)
                        st.rerun()
        else:
            st.info("No screens. Use sidebar to add.")
    
    # Green screens tab
    with tabs[6]:
        if st.session_state.scene_elements['green_screens']:
            for i, gs in enumerate(st.session_state.scene_elements['green_screens']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{gs['name']}** ({gs['size']}) | Pos: ({gs['x']:.1f}, {gs['y']:.1f}) | Rot: {gs['rotation']}°
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_gs_{i}"):
                        st.session_state.scene_elements['green_screens'].pop(i)
                        st.rerun()
        else:
            st.info("No green screens. Use sidebar to add.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        PreViz Beta 3.5 - Phase 1 Visual Update<br>
        Developed by Eduardo Carmona | Educational Film Production Planning Tool<br>
        Beta Testing Version
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
