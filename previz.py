"""
PreViz - Interactive Film Production Planning Tool
Free Educational Technology for Film Students
Developed by: Eduardo Carmona
Version: 4.0
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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1.5rem;
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

# Field of View presets
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
    return np.radians(angle_deg)

def rotate_point(x, y, angle_deg):
    angle_rad = angle_to_radians(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x, new_y

def create_camera_frustum(x, y, z, rotation, fov=60, name="Camera"):
    cone_length = 4
    cone_width = np.tan(np.radians(fov / 2)) * cone_length
    points = [
        (0, 0),
        (-cone_width, cone_length),
        (cone_width, cone_length),
    ]
    rotated_points = [rotate_point(px, py, rotation) for px, py in points]
    # rotate_point returns exactly 2 values (px, py)
    world_points = [(x + px, y + py, z) for px, py in rotated_points]
    return world_points

def create_light_coverage(x, y, z, rotation, intensity, light_type):
    if light_type in ["Key Light", "Fill Light", "Back Light"]:
        beam_length = intensity / 15
    elif light_type == "LED Panel":
        beam_length = intensity / 25
    elif light_type == "Practical":
        beam_length = intensity / 40
    else:
        beam_length = intensity / 10
    dx, dy = rotate_point(0, beam_length, rotation)
    return [x, y, z, x + dx, y + dy, z]

def duplicate_element(element_type, element_data):
    new_element = copy.deepcopy(element_data)
    new_element['x'] += 1.0
    new_element['y'] += 1.0
    original_name = new_element['name']
    if 'Copy' in original_name:
        try:
            parts = original_name.rsplit('Copy', 1)
            if len(parts) == 2 and parts[1].strip().isdigit():
                num = int(parts[1].strip()) + 1
                new_element['name'] = f"{parts[0]}Copy {num}"
            else:
                new_element['name'] = f"{original_name} Copy 2"
        except Exception:
            new_element['name'] = f"{original_name} Copy"
    else:
        new_element['name'] = f"{original_name} Copy"
    return new_element


# 3D Scene Generator

def generate_3d_scene(view_mode="Perspective"):
    fig = go.Figure()
    stage_size = 20

    # Floor grid
    grid_lines_x = []
    grid_lines_y = []
    for i in range(-stage_size // 2, stage_size // 2 + 1, 2):
        grid_lines_x.extend([i, i, None])
        grid_lines_y.extend([-stage_size // 2, stage_size // 2, None])
        grid_lines_x.extend([-stage_size // 2, stage_size // 2, None])
        grid_lines_y.extend([i, i, None])

    fig.add_trace(go.Scatter3d(
        x=grid_lines_x, y=grid_lines_y,
        z=[0] * len(grid_lines_x),
        mode='lines',
        line=dict(color='lightgray', width=1),
        showlegend=False, hoverinfo='skip'
    ))

    # Cameras
    for cam in st.session_state.scene_elements['cameras']:
        # Camera body — large, bold, unmistakable
        fig.add_trace(go.Scatter3d(
            x=[cam['x']], y=[cam['y']], z=[cam['z']],
            mode='markers+text',
            marker=dict(size=18, color='royalblue', symbol='square'),
            text=[f"🎥 {cam['name']}"],
            textposition='top center',
            name=cam['name'],
            hovertemplate=(
                f"<b>{cam['name']}</b><br>"
                f"Position: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f})<br>"
                f"Rotation: {cam['rotation']} deg<br>"
                f"Focal Length: {cam['focal_length']}mm<br>"
                f"FOV: {cam['fov']} deg<extra></extra>"
            )
        ))
        # Camera direction arrow
        dx, dy = rotate_point(0, 3, cam['rotation'])
        fig.add_trace(go.Scatter3d(
            x=[cam['x'], cam['x'] + dx],
            y=[cam['y'], cam['y'] + dy],
            z=[cam['z'], cam['z']],
            mode='lines',
            line=dict(color='royalblue', width=6),
            showlegend=False, hoverinfo='skip'
        ))
        # FOV frustum
        frustum = create_camera_frustum(
            cam['x'], cam['y'], cam['z'], cam['rotation'], cam['fov']
        )
        fig.add_trace(go.Scatter3d(
            x=[frustum[0][0], frustum[1][0]],
            y=[frustum[0][1], frustum[1][1]],
            z=[frustum[0][2], frustum[1][2]],
            mode='lines', line=dict(color='royalblue', width=4, dash='dash'),
            showlegend=False, hoverinfo='skip', opacity=0.7
        ))
        fig.add_trace(go.Scatter3d(
            x=[frustum[0][0], frustum[2][0]],
            y=[frustum[0][1], frustum[2][1]],
            z=[frustum[0][2], frustum[2][2]],
            mode='lines', line=dict(color='royalblue', width=4, dash='dash'),
            showlegend=False, hoverinfo='skip', opacity=0.7
        ))
        # Close the frustum mouth
        fig.add_trace(go.Scatter3d(
            x=[frustum[1][0], frustum[2][0]],
            y=[frustum[1][1], frustum[2][1]],
            z=[frustum[1][2], frustum[2][2]],
            mode='lines', line=dict(color='royalblue', width=4, dash='dash'),
            showlegend=False, hoverinfo='skip', opacity=0.7
        ))

    # Lights
    light_colors = {
        "Key Light": 'yellow', "Fill Light": 'lightyellow',
        "Back Light": 'orange', "LED Panel": 'white',
        "Practical": 'gold', "Natural Light": 'lightblue'
    }
    for light in st.session_state.scene_elements['lights']:
        color = light_colors.get(light['type'], 'yellow')
        fig.add_trace(go.Scatter3d(
            x=[light['x']], y=[light['y']], z=[light['z']],
            mode='markers+text',
            marker=dict(size=10, color=color, symbol='diamond'),
            text=[light['name']], textposition='top center',
            name=light['name'],
            hovertemplate=(
                f"<b>{light['name']}</b><br>"
                f"Type: {light['type']}<br>"
                f"Position: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f})<br>"
                f"Rotation: {light['rotation']} deg<br>"
                f"Intensity: {light['intensity']}%<extra></extra>"
            )
        ))
        beam = create_light_coverage(
            light['x'], light['y'], light['z'],
            light['rotation'], light['intensity'], light['type']
        )
        fig.add_trace(go.Scatter3d(
            x=[beam[0], beam[3]], y=[beam[1], beam[4]], z=[beam[2], beam[5]],
            mode='lines', line=dict(color=color, width=4),
            showlegend=False, hoverinfo='skip', opacity=0.5
        ))

    # Actors
    for actor in st.session_state.scene_elements['actors']:
        fig.add_trace(go.Scatter3d(
            x=[actor['x']], y=[actor['y']], z=[0],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='circle'),
            text=[actor['name']], textposition='top center',
            name=actor['name'],
            hovertemplate=(
                f"<b>{actor['name']}</b><br>"
                f"Position: ({actor['x']:.1f}, {actor['y']:.1f})<br>"
                f"Notes: {actor['notes']}<extra></extra>"
            )
        ))

    # Set Pieces
    piece_colors = {
        'Table': 'brown', 'Chair': 'saddlebrown', 'Sofa': 'tan',
        'Desk': 'sienna', 'Wall': 'gray', 'Door': 'darkgray', 'Window': 'lightblue'
    }
    for piece in st.session_state.scene_elements['set_pieces']:
        color = piece_colors.get(piece['type'], 'green')
        fig.add_trace(go.Scatter3d(
            x=[piece['x']], y=[piece['y']], z=[0],
            mode='markers+text',
            marker=dict(size=12, color=color, symbol='square'),
            text=[piece['name']], textposition='top center',
            name=piece['name'],
            hovertemplate=(
                f"<b>{piece['name']}</b><br>"
                f"Type: {piece['type']}<br>"
                f"Position: ({piece['x']:.1f}, {piece['y']:.1f})<extra></extra>"
            )
        ))

    # Props
    prop_colors = {
        'Weapon': 'darkred', 'Phone': 'purple',
        'Bag / Briefcase': 'saddlebrown', 'Food / Drink': 'orange',
        'Book / Document': 'khaki', 'Electronics': 'steelblue',
        'Tool': 'dimgray', 'Other': 'olive'
    }
    for prop in st.session_state.scene_elements.get('props', []):
        color = prop_colors.get(prop.get('type', 'Other'), 'olive')
        fig.add_trace(go.Scatter3d(
            x=[prop['x']], y=[prop['y']], z=[0.5],
            mode='markers+text',
            marker=dict(size=8, color=color, symbol='cross'),
            text=[prop['name']], textposition='top center',
            name=prop['name'],
            hovertemplate=(
                f"<b>{prop['name']}</b><br>"
                f"Type: {prop.get('type', 'Prop')}<br>"
                f"Position: ({prop['x']:.1f}, {prop['y']:.1f})<br>"
                f"Notes: {prop.get('notes', '')}<extra></extra>"
            )
        ))

    # Vehicles
    for vehicle in st.session_state.scene_elements['vehicles']:
        fig.add_trace(go.Scatter3d(
            x=[vehicle['x']], y=[vehicle['y']], z=[0],
            mode='markers+text',
            marker=dict(size=18, color='darkblue', symbol='square'),
            text=[vehicle['name']], textposition='top center',
            name=vehicle['name'],
            hovertemplate=(
                f"<b>{vehicle['name']}</b><br>"
                f"Type: {vehicle['type']}<br>"
                f"Rotation: {vehicle['rotation']} deg<br>"
                f"Position: ({vehicle['x']:.1f}, {vehicle['y']:.1f})<extra></extra>"
            )
        ))

    # Screens
    for screen in st.session_state.scene_elements['screens']:
        fig.add_trace(go.Scatter3d(
            x=[screen['x']], y=[screen['y']], z=[screen['z']],
            mode='markers+text',
            marker=dict(size=14, color='black', symbol='square'),
            text=[screen['name']], textposition='top center',
            name=screen['name'],
            hovertemplate=(
                f"<b>{screen['name']}</b><br>"
                f"Size: {screen['size']}<br>"
                f"Height: {screen['z']} ft<br>"
                f"Position: ({screen['x']:.1f}, {screen['y']:.1f})<extra></extra>"
            )
        ))

    # Green Screens
    for gs in st.session_state.scene_elements['green_screens']:
        width = 8
        height = 8
        corners = [(-width / 2, 0), (width / 2, 0)]
        rotated = [rotate_point(px, py, gs['rotation']) for px, py in corners]
        fig.add_trace(go.Scatter3d(
            x=[gs['x'] + rotated[0][0], gs['x'] + rotated[1][0]],
            y=[gs['y'] + rotated[0][1], gs['y'] + rotated[1][1]],
            z=[0, height],
            mode='lines', line=dict(color='green', width=10),
            showlegend=False, hoverinfo='skip', opacity=0.6
        ))
        fig.add_trace(go.Scatter3d(
            x=[gs['x']], y=[gs['y']], z=[height / 2],
            mode='text', text=[gs['name']], textposition='middle center',
            name=gs['name'],
            hovertemplate=(
                f"<b>{gs['name']}</b><br>"
                f"Size: {gs['size']}<br>"
                f"Rotation: {gs['rotation']} deg<extra></extra>"
            )
        ))

    # Camera view angle
    if view_mode == "Top-Down":
        camera = dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))
    elif view_mode == "Side View":
        camera = dict(eye=dict(x=2.5, y=0, z=0.5), up=dict(x=0, y=0, z=1))
    else:
        camera = dict(eye=dict(x=1.5, y=-1.5, z=1.5), up=dict(x=0, y=0, z=1))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-stage_size // 2, stage_size // 2], title="X (feet)"),
            yaxis=dict(range=[-stage_size // 2, stage_size // 2], title="Y (feet)"),
            zaxis=dict(range=[0, 15], title="Z (feet)"),
            aspectmode='cube',
            camera=camera
        ),
        height=620,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"Scene: {st.session_state.scene_name} ({view_mode})"
    )
    return fig


# Export Functions

def export_setup_report():
    elems = st.session_state.scene_elements
    report = f"""
PRODUCTION SETUP REPORT
=====================================
Scene: {st.session_state.scene_name}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
=====================================

CAMERAS ({len(elems['cameras'])})
-------------------------------------
"""
    for i, cam in enumerate(elems['cameras'], 1):
        report += f"\n{i}. {cam['name']}\n"
        report += f"   Position: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) feet\n"
        report += f"   Rotation: {cam['rotation']} deg\n"
        report += f"   Focal Length: {cam['focal_length']}mm\n"
        report += f"   Field of View: {cam['fov']} deg\n"

    report += f"\nLIGHTING ({len(elems['lights'])})\n-------------------------------------\n"
    for i, light in enumerate(elems['lights'], 1):
        report += f"\n{i}. {light['name']}\n"
        report += f"   Type: {light['type']}\n"
        report += f"   Position: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) feet\n"
        report += f"   Rotation: {light['rotation']} deg\n"
        report += f"   Intensity: {light['intensity']}%\n"

    report += f"\nTALENT ({len(elems['actors'])})\n-------------------------------------\n"
    for i, actor in enumerate(elems['actors'], 1):
        report += f"\n{i}. {actor['name']}\n"
        report += f"   Position: ({actor['x']:.1f}, {actor['y']:.1f}) feet\n"
        report += f"   Notes: {actor['notes']}\n"

    if elems.get('props'):
        report += f"\nPROPS ({len(elems['props'])})\n-------------------------------------\n"
        for i, prop in enumerate(elems['props'], 1):
            report += f"\n{i}. {prop['name']} ({prop.get('type', 'Prop')})\n"
            report += f"   Position: ({prop['x']:.1f}, {prop['y']:.1f}) feet\n"
            report += f"   Notes: {prop.get('notes', '')}\n"

    if elems['set_pieces']:
        report += f"\nSET PIECES ({len(elems['set_pieces'])})\n-------------------------------------\n"
        for i, piece in enumerate(elems['set_pieces'], 1):
            report += f"\n{i}. {piece['name']} ({piece['type']})\n"
            report += f"   Position: ({piece['x']:.1f}, {piece['y']:.1f}) feet\n"

    if elems['vehicles']:
        report += f"\nVEHICLES ({len(elems['vehicles'])})\n-------------------------------------\n"
        for i, veh in enumerate(elems['vehicles'], 1):
            report += f"\n{i}. {veh['name']} ({veh['type']})\n"
            report += f"   Position: ({veh['x']:.1f}, {veh['y']:.1f}) feet\n"
            report += f"   Rotation: {veh['rotation']} deg\n"

    if elems['screens']:
        report += f"\nSCREENS/MONITORS ({len(elems['screens'])})\n-------------------------------------\n"
        for i, scr in enumerate(elems['screens'], 1):
            report += f"\n{i}. {scr['name']} ({scr['size']})\n"
            report += f"   Position: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f}) feet\n"

    if elems['green_screens']:
        report += f"\nGREEN SCREENS ({len(elems['green_screens'])})\n-------------------------------------\n"
        for i, gs in enumerate(elems['green_screens'], 1):
            report += f"\n{i}. {gs['name']} ({gs['size']})\n"
            report += f"   Position: ({gs['x']:.1f}, {gs['y']:.1f}) feet\n"
            report += f"   Rotation: {gs['rotation']} deg\n"

    report += "\n=====================================\nEquipment Checklist:\n"
    report += f"  [ ] {len(elems['cameras'])} Camera(s)\n"
    report += f"  [ ] {len(elems['lights'])} Light(s)\n"
    if elems.get('props'):
        report += f"  [ ] {len(elems['props'])} Prop(s)\n"
    if elems['screens']:
        report += f"  [ ] {len(elems['screens'])} Monitor(s)\n"
    if elems['green_screens']:
        report += f"  [ ] {len(elems['green_screens'])} Green Screen(s)\n"
    return report


def export_scene_json():
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
        st.markdown('<div class="main-header">🎬 PreViz 4.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Free Educational Technology for Film Students</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="version-badge">v4.0</div>', unsafe_allow_html=True)

    # SIDEBAR
    with st.sidebar:
        st.header("🎬 Scene Setup")

        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name

        st.divider()

        # Visual icon reference
        st.markdown("**Element Guide**")
        st.markdown(
            "🎥 Camera &nbsp;|&nbsp; 💡 Light &nbsp;|&nbsp; 🧍 Actor\n\n"
            "🪑 Set Piece &nbsp;|&nbsp; 🎭 Props &nbsp;|&nbsp; 🚗 Vehicle\n\n"
            "🖥️ Screen &nbsp;|&nbsp; 🟢 Green Screen"
        )

        st.divider()

        # Element selector
        element_type = st.selectbox(
            "Add Element to Scene",
            [
                "-- Select --",
                "🎥  Camera",
                "💡  Light",
                "🧍  Actor",
                "🪑  Set Piece",
                "🎭  Props",
                "🚗  Vehicle",
                "🖥️  Screen / Monitor",
                "🟢  Green Screen"
            ]
        )

        # Camera Form
        if "Camera" in element_type:
            st.subheader("🎥 Add Camera")
            with st.form("camera_form"):
                cam_name = st.text_input(
                    "Camera Name",
                    value=f"Camera {chr(65 + len(st.session_state.scene_elements['cameras']))}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    cam_x = st.number_input("X Position", value=0.0, step=0.5)
                    cam_y = st.number_input("Y Position", value=-5.0, step=0.5)
                with col2:
                    height_preset = st.selectbox("Height Preset", list(CAMERA_HEIGHT_PRESETS.keys()))
                    cam_z = st.number_input(
                        "Height (Z)",
                        value=CAMERA_HEIGHT_PRESETS[height_preset],
                        step=0.5, min_value=0.0
                    )
                cam_rotation = st.slider("Rotation (degrees)", 0, 359, 0)
                focal_preset = st.selectbox("Focal Length Preset", list(FOV_PRESETS.keys()))
                cam_focal = int(focal_preset.split('mm')[0])
                cam_fov = FOV_PRESETS[focal_preset]
                st.caption(f"Field of View: {cam_fov} degrees")
                if st.form_submit_button("Add Camera"):
                    st.session_state.scene_elements['cameras'].append({
                        'name': cam_name, 'x': cam_x, 'y': cam_y, 'z': cam_z,
                        'rotation': cam_rotation, 'focal_length': cam_focal, 'fov': cam_fov
                    })
                    st.success(f"Added {cam_name}")
                    st.rerun()

        # Light Form
        elif "Light" in element_type:
            st.subheader("💡 Add Light")
            with st.form("light_form"):
                light_name = st.text_input(
                    "Light Name",
                    value=f"Light {len(st.session_state.scene_elements['lights']) + 1}"
                )
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
                        'name': light_name, 'type': light_type,
                        'x': light_x, 'y': light_y, 'z': light_z,
                        'rotation': light_rotation, 'intensity': light_intensity
                    })
                    st.success(f"Added {light_name}")
                    st.rerun()

        # Actor Form
        elif "Actor" in element_type:
            st.subheader("🧍 Add Actor")
            with st.form("actor_form"):
                actor_name = st.text_input(
                    "Actor / Character Name",
                    value=f"Actor {len(st.session_state.scene_elements['actors']) + 1}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    actor_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    actor_y = st.number_input("Y Position", value=0.0, step=0.5)
                actor_notes = st.text_area(
                    "Blocking Notes",
                    placeholder="e.g., Standing, sitting, walking towards camera..."
                )
                if st.form_submit_button("Add Actor"):
                    st.session_state.scene_elements['actors'].append({
                        'name': actor_name, 'x': actor_x, 'y': actor_y, 'notes': actor_notes
                    })
                    st.success(f"Added {actor_name}")
                    st.rerun()

        # Set Piece Form
        elif "Set Piece" in element_type:
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
                        'name': piece_name, 'type': piece_type, 'x': piece_x, 'y': piece_y
                    })
                    st.success(f"Added {piece_name}")
                    st.rerun()

        # Props Form
        elif "Props" in element_type:
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
                prop_notes = st.text_input(
                    "Notes", placeholder="e.g., Hero prop, breakaway version"
                )
                if st.form_submit_button("Add Prop"):
                    if 'props' not in st.session_state.scene_elements:
                        st.session_state.scene_elements['props'] = []
                    st.session_state.scene_elements['props'].append({
                        'name': prop_name, 'type': prop_type,
                        'x': prop_x, 'y': prop_y, 'notes': prop_notes
                    })
                    st.success(f"Added {prop_name}")
                    st.rerun()

        # Vehicle Form
        elif "Vehicle" in element_type:
            st.subheader("🚗 Add Vehicle")
            with st.form("vehicle_form"):
                veh_name = st.text_input("Name", value="Car")
                veh_type = st.selectbox("Type",
                    ["Car", "Van", "Truck", "Motorcycle", "Bicycle"])
                col1, col2 = st.columns(2)
                with col1:
                    veh_x = st.number_input("X Position", value=0.0, step=0.5)
                    veh_y = st.number_input("Y Position", value=0.0, step=0.5)
                with col2:
                    veh_rotation = st.slider("Rotation", 0, 359, 0, key="veh_rot")
                if st.form_submit_button("Add Vehicle"):
                    st.session_state.scene_elements['vehicles'].append({
                        'name': veh_name, 'type': veh_type,
                        'x': veh_x, 'y': veh_y, 'rotation': veh_rotation
                    })
                    st.success(f"Added {veh_name}")
                    st.rerun()

        # Screen / Monitor Form
        elif "Screen" in element_type and "Green" not in element_type:
            st.subheader("🖥️ Add Screen / Monitor")
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
                        'name': scr_name, 'size': scr_size,
                        'x': scr_x, 'y': scr_y, 'z': scr_z
                    })
                    st.success(f"Added {scr_name}")
                    st.rerun()

        # Green Screen Form
        elif "Green" in element_type:
            st.subheader("🟢 Add Green Screen")
            with st.form("greenscreen_form"):
                gs_name = st.text_input("Name", value="Green Screen")
                gs_size = st.selectbox("Size",
                    ["6x8 ft", "8x10 ft", "10x12 ft", "12x20 ft"])
                col1, col2 = st.columns(2)
                with col1:
                    gs_x = st.number_input("X Position", value=0.0, step=0.5)
                    gs_y = st.number_input("Y Position", value=5.0, step=0.5)
                with col2:
                    gs_rotation = st.slider("Rotation", 0, 359, 0, key="gs_rot")
                if st.form_submit_button("Add Green Screen"):
                    st.session_state.scene_elements['green_screens'].append({
                        'name': gs_name, 'size': gs_size,
                        'x': gs_x, 'y': gs_y, 'rotation': gs_rotation
                    })
                    st.success(f"Added {gs_name}")
                    st.rerun()

        st.divider()

        # Quick Templates
        st.subheader("📋 Quick Templates")

        if st.button("Three-Point Lighting"):
            st.session_state.scene_elements['lights'] = [
                {'name': 'Key Light',  'type': 'Key Light',  'x': 3,  'y': 3,  'z': 6, 'rotation': 225, 'intensity': 100},
                {'name': 'Fill Light', 'type': 'Fill Light', 'x': -3, 'y': 3,  'z': 5, 'rotation': 135, 'intensity': 50},
                {'name': 'Back Light', 'type': 'Back Light', 'x': 0,  'y': -3, 'z': 7, 'rotation': 0,   'intensity': 70}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Subject', 'x': 0, 'y': 0, 'notes': 'Center frame'}
            ]
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Main Camera', 'x': 0, 'y': -8, 'z': 5,
                 'rotation': 0, 'focal_length': 50, 'fov': 47}
            ]
            st.rerun()

        if st.button("Multi-Camera Interview"):
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Camera A (Wide)',          'x': 0,  'y': -8, 'z': 5,   'rotation': 0,   'focal_length': 35, 'fov': 63},
                {'name': 'Camera B (Close)',          'x': -3, 'y': -7, 'z': 4.5, 'rotation': 15,  'focal_length': 85, 'fov': 29},
                {'name': 'Camera C (Over Shoulder)',  'x': 2,  'y': -2, 'z': 4,   'rotation': 180, 'focal_length': 50, 'fov': 47}
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
                {'name': 'Main Camera', 'x': 0, 'y': -6, 'z': 5,
                 'rotation': 0, 'focal_length': 50, 'fov': 47}
            ]
            st.session_state.scene_elements['lights'] = [
                {'name': 'Subject Key',          'type': 'Key Light',  'x': 3,  'y': -2, 'z': 6, 'rotation': 200, 'intensity': 100},
                {'name': 'Subject Fill',         'type': 'Fill Light', 'x': -3, 'y': -2, 'z': 5, 'rotation': 160, 'intensity': 60},
                {'name': 'Green Screen Light L', 'type': 'LED Panel',  'x': -4, 'y': 6,  'z': 4, 'rotation': 90,  'intensity': 80},
                {'name': 'Green Screen Light R', 'type': 'LED Panel',  'x': 4,  'y': 6,  'z': 4, 'rotation': 90,  'intensity': 80}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Subject', 'x': 0, 'y': 2, 'notes': 'Standing 6 ft from green screen'}
            ]
            st.rerun()

        st.divider()

        if st.button("🗑️ Clear All Elements", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [], 'lights': [], 'actors': [],
                'set_pieces': [], 'props': [], 'vehicles': [],
                'screens': [], 'green_screens': []
            }
            st.rerun()

    # MAIN CONTENT
    col_main, col_summary = st.columns([3, 1])

    with col_main:
        view_mode = st.radio(
            "View Mode",
            ["Perspective", "Top-Down", "Side View"],
            horizontal=True
        )
        st.session_state.view_mode = view_mode
        fig = generate_3d_scene(view_mode)
        st.plotly_chart(fig, use_container_width=True)

    with col_summary:
        st.subheader("Scene Summary")
        elems = st.session_state.scene_elements
        st.metric("🎥 Cameras",     len(elems['cameras']))
        st.metric("💡 Lights",      len(elems['lights']))
        st.metric("🧍 Actors",      len(elems['actors']))
        st.metric("🎭 Props",       len(elems.get('props', [])))
        total_set = (
            len(elems['set_pieces']) + len(elems['vehicles']) +
            len(elems['screens']) + len(elems['green_screens'])
        )
        st.metric("🪑 Set Elements", total_set)

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

    # SCENE ELEMENT TABS
    st.divider()
    st.subheader("Scene Elements")

    tabs = st.tabs([
        "🎥 Cameras", "💡 Lights", "🧍 Actors",
        "🪑 Set Pieces", "🎭 Props", "🚗 Vehicles",
        "🖥️ Screens", "🟢 Green Screens"
    ])

    # Cameras
    with tabs[0]:
        if elems['cameras']:
            for i, cam in enumerate(elems['cameras']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(
                        f"**{cam['name']}** | FL: {cam['focal_length']}mm | FOV: {cam['fov']} deg  \n"
                        f"Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) | Rot: {cam['rotation']} deg"
                    )
                with c2:
                    if st.button("📋", key=f"copy_cam_{i}"):
                        st.session_state.scene_elements['cameras'].append(
                            duplicate_element('cameras', cam))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_cam_{i}"):
                        st.session_state.scene_elements['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras. Use sidebar to add.")

    # Lights
    with tabs[1]:
        if elems['lights']:
            for i, light in enumerate(elems['lights']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(
                        f"**{light['name']}** ({light['type']}) | {light['intensity']}%  \n"
                        f"Pos: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) | Rot: {light['rotation']} deg"
                    )
                with c2:
                    if st.button("📋", key=f"copy_light_{i}"):
                        st.session_state.scene_elements['lights'].append(
                            duplicate_element('lights', light))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_light_{i}"):
                        st.session_state.scene_elements['lights'].pop(i)
                        st.rerun()
        else:
            st.info("No lights. Use sidebar to add.")

    # Actors
    with tabs[2]:
        if elems['actors']:
            for i, actor in enumerate(elems['actors']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{actor['name']}** | Pos: ({actor['x']:.1f}, {actor['y']:.1f})  \n"
                        f"{actor['notes']}"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_actor_{i}"):
                        st.session_state.scene_elements['actors'].pop(i)
                        st.rerun()
        else:
            st.info("No actors. Use sidebar to add.")

    # Set Pieces
    with tabs[3]:
        if elems['set_pieces']:
            for i, piece in enumerate(elems['set_pieces']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{piece['name']}** ({piece['type']}) | "
                        f"Pos: ({piece['x']:.1f}, {piece['y']:.1f})"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_piece_{i}"):
                        st.session_state.scene_elements['set_pieces'].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces. Use sidebar to add.")

    # Props
    with tabs[4]:
        props_list = elems.get('props', [])
        if props_list:
            for i, prop in enumerate(props_list):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{prop['name']}** ({prop.get('type', 'Prop')}) | "
                        f"Pos: ({prop['x']:.1f}, {prop['y']:.1f})  \n"
                        f"{prop.get('notes', '')}"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_prop_{i}"):
                        st.session_state.scene_elements['props'].pop(i)
                        st.rerun()
        else:
            st.info("No props. Use sidebar to add.")

    # Vehicles
    with tabs[5]:
        if elems['vehicles']:
            for i, veh in enumerate(elems['vehicles']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{veh['name']}** ({veh['type']}) | "
                        f"Pos: ({veh['x']:.1f}, {veh['y']:.1f}) | Rot: {veh['rotation']} deg"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_veh_{i}"):
                        st.session_state.scene_elements['vehicles'].pop(i)
                        st.rerun()
        else:
            st.info("No vehicles. Use sidebar to add.")

    # Screens
    with tabs[6]:
        if elems['screens']:
            for i, scr in enumerate(elems['screens']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{scr['name']}** ({scr['size']}) | "
                        f"Pos: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f})"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_scr_{i}"):
                        st.session_state.scene_elements['screens'].pop(i)
                        st.rerun()
        else:
            st.info("No screens. Use sidebar to add.")

    # Green Screens
    with tabs[7]:
        if elems['green_screens']:
            for i, gs in enumerate(elems['green_screens']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{gs['name']}** ({gs['size']}) | "
                        f"Pos: ({gs['x']:.1f}, {gs['y']:.1f}) | Rot: {gs['rotation']} deg"
                    )
                with c2:
                    if st.button("🗑️", key=f"del_gs_{i}"):
                        st.session_state.scene_elements['green_screens'].pop(i)
                        st.rerun()
        else:
            st.info("No green screens. Use sidebar to add.")

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        PreViz v4.0 | Free Educational Technology for Film Students<br>
        Developed by Eduardo Carmona | CSUDH &amp; LMU
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
