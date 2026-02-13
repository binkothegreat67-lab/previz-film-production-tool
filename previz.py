"""
PreViz - Interactive Film Production Planning Tool
Educational Technology for Digital Media Arts
Developed by: Eduardo Carmona
Version: 2.0 (Enhanced)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="PreViz - Film Production Planning",
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
    .element-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .export-section {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scene_elements' not in st.session_state:
    st.session_state.scene_elements = {
        'cameras': [],
        'lights': [],
        'actors': [],
        'props': []
    }

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Perspective"

if 'scene_name' not in st.session_state:
    st.session_state.scene_name = "Untitled Scene"

# Helper Functions
def create_camera_cone(x, y, z, direction, angle=60, name="Camera"):
    """Create a camera frustum/cone visualization"""
    cone_length = 3
    cone_width = np.tan(np.radians(angle/2)) * cone_length
    
    # Direction vectors
    if direction == "North":
        dx, dy = 0, 1
    elif direction == "South":
        dx, dy = 0, -1
    elif direction == "East":
        dx, dy = 1, 0
    else:  # West
        dx, dy = -1, 0
    
    # Camera cone vertices
    vertices = np.array([
        [x, y, z],  # apex
        [x - cone_width*dy, y + cone_width*dx, z],  # base corner 1
        [x + cone_width*dy, y - cone_width*dx, z],  # base corner 2
        [x - cone_width*dy + cone_length*dx, y - cone_width*dy + cone_length*dy, z],  # far corner 1
        [x + cone_width*dy + cone_length*dx, y + cone_width*dy + cone_length*dy, z]   # far corner 2
    ])
    
    return vertices

def create_light_cone(x, y, z, direction, intensity=100):
    """Create a light beam visualization"""
    beam_length = intensity / 20
    beam_width = beam_length * 0.5
    
    # Similar to camera but with different proportions
    if direction == "North":
        dx, dy = 0, 1
    elif direction == "South":
        dx, dy = 0, -1
    elif direction == "East":
        dx, dy = 1, 0
    else:  # West
        dx, dy = -1, 0
    
    end_x = x + beam_length * dx
    end_y = y + beam_length * dy
    
    return [x, y, z, end_x, end_y, z]

def generate_3d_scene(view_mode="Perspective"):
    """Generate the 3D visualization of the scene"""
    fig = go.Figure()
    
    # Define stage boundaries (20x20 feet default)
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
    
    # Add cameras
    for camera in st.session_state.scene_elements['cameras']:
        # Camera body (as a marker)
        fig.add_trace(go.Scatter3d(
            x=[camera['x']],
            y=[camera['y']],
            z=[camera['z']],
            mode='markers+text',
            marker=dict(size=12, color='blue', symbol='square'),
            text=[camera['name']],
            textposition='top center',
            name=camera['name'],
            hovertemplate=f"<b>{camera['name']}</b><br>" +
                         f"Position: ({camera['x']}, {camera['y']}, {camera['z']})<br>" +
                         f"Direction: {camera['direction']}<br>" +
                         f"Focal Length: {camera['focal_length']}mm<extra></extra>"
        ))
        
        # Camera viewing direction (simple arrow)
        direction_length = 2
        if camera['direction'] == "North":
            dx, dy = 0, direction_length
        elif camera['direction'] == "South":
            dx, dy = 0, -direction_length
        elif camera['direction'] == "East":
            dx, dy = direction_length, 0
        else:  # West
            dx, dy = -direction_length, 0
        
        fig.add_trace(go.Scatter3d(
            x=[camera['x'], camera['x'] + dx],
            y=[camera['y'], camera['y'] + dy],
            z=[camera['z'], camera['z']],
            mode='lines',
            line=dict(color='blue', width=4, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add lights
    for light in st.session_state.scene_elements['lights']:
        # Light fixture
        fig.add_trace(go.Scatter3d(
            x=[light['x']],
            y=[light['y']],
            z=[light['z']],
            mode='markers+text',
            marker=dict(size=10, color='yellow', symbol='diamond'),
            text=[light['name']],
            textposition='top center',
            name=light['name'],
            hovertemplate=f"<b>{light['name']}</b><br>" +
                         f"Type: {light['type']}<br>" +
                         f"Position: ({light['x']}, {light['y']}, {light['z']})<br>" +
                         f"Intensity: {light['intensity']}%<br>" +
                         f"Direction: {light['direction']}<extra></extra>"
        ))
        
        # Light beam
        beam_coords = create_light_cone(light['x'], light['y'], light['z'], 
                                       light['direction'], light['intensity'])
        fig.add_trace(go.Scatter3d(
            x=[beam_coords[0], beam_coords[3]],
            y=[beam_coords[1], beam_coords[4]],
            z=[beam_coords[2], beam_coords[5]],
            mode='lines',
            line=dict(color='yellow', width=3),
            showlegend=False,
            hoverinfo='skip',
            opacity=0.6
        ))
    
    # Add actors
    for actor in st.session_state.scene_elements['actors']:
        fig.add_trace(go.Scatter3d(
            x=[actor['x']],
            y=[actor['y']],
            z=[0],  # Actors on floor
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='circle'),
            text=[actor['name']],
            textposition='top center',
            name=actor['name'],
            hovertemplate=f"<b>{actor['name']}</b><br>" +
                         f"Position: ({actor['x']}, {actor['y']})<br>" +
                         f"Notes: {actor['notes']}<extra></extra>"
        ))
    
    # Add props
    for prop in st.session_state.scene_elements['props']:
        fig.add_trace(go.Scatter3d(
            x=[prop['x']],
            y=[prop['y']],
            z=[0],
            mode='markers+text',
            marker=dict(size=10, color='green', symbol='square'),
            text=[prop['name']],
            textposition='top center',
            name=prop['name'],
            hovertemplate=f"<b>{prop['name']}</b><br>" +
                         f"Position: ({prop['x']}, {prop['y']})<extra></extra>"
        ))
    
    # Set camera view based on view mode
    if view_mode == "Top-Down":
        camera = dict(
            eye=dict(x=0, y=0, z=2.5),
            up=dict(x=0, y=1, z=0)
        )
    elif view_mode == "Side View":
        camera = dict(
            eye=dict(x=2.5, y=0, z=0.5),
            up=dict(x=0, y=0, z=1)
        )
    else:  # Perspective
        camera = dict(
            eye=dict(x=1.5, y=-1.5, z=1.5),
            up=dict(x=0, y=0, z=1)
        )
    
    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-stage_size//2, stage_size//2], title="X (feet)"),
            yaxis=dict(range=[-stage_size//2, stage_size//2], title="Y (feet)"),
            zaxis=dict(range=[0, 10], title="Z (feet)"),
            aspectmode='cube',
            camera=camera
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"Scene: {st.session_state.scene_name} ({view_mode})"
    )
    
    return fig

def export_setup_report():
    """Generate a text-based setup report"""
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
   Position: ({cam['x']}, {cam['y']}, {cam['z']}) feet
   Direction: {cam['direction']}
   Focal Length: {cam['focal_length']}mm
   Height: {cam['z']} feet
"""
    
    report += f"""
LIGHTING ({len(st.session_state.scene_elements['lights'])})
-------------------------------------
"""
    for i, light in enumerate(st.session_state.scene_elements['lights'], 1):
        report += f"""
{i}. {light['name']}
   Type: {light['type']}
   Position: ({light['x']}, {light['y']}, {light['z']}) feet
   Direction: {light['direction']}
   Intensity: {light['intensity']}%
"""
    
    report += f"""
TALENT ({len(st.session_state.scene_elements['actors'])})
-------------------------------------
"""
    for i, actor in enumerate(st.session_state.scene_elements['actors'], 1):
        report += f"""
{i}. {actor['name']}
   Position: ({actor['x']}, {actor['y']}) feet
   Notes: {actor['notes']}
"""
    
    report += f"""
PROPS ({len(st.session_state.scene_elements['props'])})
-------------------------------------
"""
    for i, prop in enumerate(st.session_state.scene_elements['props'], 1):
        report += f"""
{i}. {prop['name']}
   Position: ({prop['x']}, {prop['y']}) feet
"""
    
    report += """
=====================================
Equipment Checklist:
"""
    report += f"  ☐ {len(st.session_state.scene_elements['cameras'])} Camera(s)\n"
    report += f"  ☐ {len(st.session_state.scene_elements['lights'])} Light(s)\n"
    
    return report

def export_scene_json():
    """Export scene as JSON for saving/loading"""
    scene_data = {
        'scene_name': st.session_state.scene_name,
        'created': datetime.now().isoformat(),
        'elements': st.session_state.scene_elements
    }
    return json.dumps(scene_data, indent=2)

# Main Application
def main():
    # Header
    st.markdown('<div class="main-header">🎬 PreViz</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive Film Production Planning Tool</div>', unsafe_allow_html=True)
    
    # Sidebar for adding elements
    with st.sidebar:
        st.header("Scene Setup")
        
        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name
        
        st.divider()
        
        # Add element selector
        element_type = st.selectbox(
            "Add Element",
            ["Select...", "Camera", "Light", "Actor", "Prop"]
        )
        
        if element_type == "Camera":
            st.subheader("➕ Add Camera")
            with st.form("camera_form"):
                cam_name = st.text_input("Camera Name", value=f"Camera {len(st.session_state.scene_elements['cameras'])+1}")
                col1, col2 = st.columns(2)
                with col1:
                    cam_x = st.number_input("X Position", value=0.0, step=0.5)
                    cam_y = st.number_input("Y Position", value=-5.0, step=0.5)
                with col2:
                    cam_z = st.number_input("Height (Z)", value=5.0, step=0.5, min_value=0.0)
                    cam_direction = st.selectbox("Direction", ["North", "South", "East", "West"])
                
                cam_focal = st.slider("Focal Length (mm)", 16, 200, 50)
                
                if st.form_submit_button("Add Camera"):
                    st.session_state.scene_elements['cameras'].append({
                        'name': cam_name,
                        'x': cam_x,
                        'y': cam_y,
                        'z': cam_z,
                        'direction': cam_direction,
                        'focal_length': cam_focal
                    })
                    st.success(f"Added {cam_name}")
                    st.rerun()
        
        elif element_type == "Light":
            st.subheader("💡 Add Light")
            with st.form("light_form"):
                light_name = st.text_input("Light Name", value=f"Light {len(st.session_state.scene_elements['lights'])+1}")
                light_type = st.selectbox("Type", ["Key Light", "Fill Light", "Back Light", "Practical"])
                
                col1, col2 = st.columns(2)
                with col1:
                    light_x = st.number_input("X Position", value=3.0, step=0.5)
                    light_y = st.number_input("Y Position", value=0.0, step=0.5)
                with col2:
                    light_z = st.number_input("Height (Z)", value=7.0, step=0.5, min_value=0.0)
                    light_direction = st.selectbox("Direction", ["North", "South", "East", "West"])
                
                light_intensity = st.slider("Intensity (%)", 0, 100, 80)
                
                if st.form_submit_button("Add Light"):
                    st.session_state.scene_elements['lights'].append({
                        'name': light_name,
                        'type': light_type,
                        'x': light_x,
                        'y': light_y,
                        'z': light_z,
                        'direction': light_direction,
                        'intensity': light_intensity
                    })
                    st.success(f"Added {light_name}")
                    st.rerun()
        
        elif element_type == "Actor":
            st.subheader("🎭 Add Actor")
            with st.form("actor_form"):
                actor_name = st.text_input("Actor/Character Name", value=f"Actor {len(st.session_state.scene_elements['actors'])+1}")
                col1, col2 = st.columns(2)
                with col1:
                    actor_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    actor_y = st.number_input("Y Position", value=0.0, step=0.5)
                
                actor_notes = st.text_area("Blocking Notes", placeholder="e.g., Standing, sitting, walking towards...")
                
                if st.form_submit_button("Add Actor"):
                    st.session_state.scene_elements['actors'].append({
                        'name': actor_name,
                        'x': actor_x,
                        'y': actor_y,
                        'notes': actor_notes
                    })
                    st.success(f"Added {actor_name}")
                    st.rerun()
        
        elif element_type == "Prop":
            st.subheader("📦 Add Prop")
            with st.form("prop_form"):
                prop_name = st.text_input("Prop Name", value=f"Prop {len(st.session_state.scene_elements['props'])+1}")
                col1, col2 = st.columns(2)
                with col1:
                    prop_x = st.number_input("X Position", value=0.0, step=0.5)
                with col2:
                    prop_y = st.number_input("Y Position", value=0.0, step=0.5)
                
                if st.form_submit_button("Add Prop"):
                    st.session_state.scene_elements['props'].append({
                        'name': prop_name,
                        'x': prop_x,
                        'y': prop_y
                    })
                    st.success(f"Added {prop_name}")
                    st.rerun()
        
        st.divider()
        
        # Templates
        st.subheader("📋 Quick Templates")
        if st.button("Three-Point Lighting Setup"):
            st.session_state.scene_elements['lights'] = [
                {'name': 'Key Light', 'type': 'Key Light', 'x': 3, 'y': 3, 'z': 6, 'direction': 'South', 'intensity': 100},
                {'name': 'Fill Light', 'type': 'Fill Light', 'x': -3, 'y': 3, 'z': 5, 'direction': 'South', 'intensity': 50},
                {'name': 'Back Light', 'type': 'Back Light', 'x': 0, 'y': -3, 'z': 7, 'direction': 'North', 'intensity': 70}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Subject', 'x': 0, 'y': 0, 'notes': 'Center frame'}
            ]
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Main Camera', 'x': 0, 'y': -8, 'z': 5, 'direction': 'North', 'focal_length': 50}
            ]
            st.rerun()
        
        if st.button("Interview Setup"):
            st.session_state.scene_elements['cameras'] = [
                {'name': 'A-Cam', 'x': -2, 'y': -6, 'z': 5, 'direction': 'North', 'focal_length': 85},
                {'name': 'B-Cam', 'x': 2, 'y': -6, 'z': 5, 'direction': 'North', 'focal_length': 50}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Interviewee', 'x': 0, 'y': 0, 'notes': 'Seated, looking camera left'}
            ]
            st.rerun()
        
        st.divider()
        
        # Clear scene
        if st.button("🗑️ Clear All Elements", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [],
                'lights': [],
                'actors': [],
                'props': []
            }
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # View mode selector
        view_mode = st.radio(
            "View Mode",
            ["Perspective", "Top-Down", "Side View"],
            horizontal=True,
            key="view_selector"
        )
        st.session_state.view_mode = view_mode
        
        # Display 3D scene
        fig = generate_3d_scene(view_mode)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Scene Summary")
        st.metric("Cameras", len(st.session_state.scene_elements['cameras']))
        st.metric("Lights", len(st.session_state.scene_elements['lights']))
        st.metric("Actors", len(st.session_state.scene_elements['actors']))
        st.metric("Props", len(st.session_state.scene_elements['props']))
        
        st.divider()
        
        st.subheader("📤 Export Options")
        
        # Setup Report
        if st.button("📄 Generate Setup Report"):
            report = export_setup_report()
            st.download_button(
                label="Download Setup Report",
                data=report,
                file_name=f"previz_setup_{st.session_state.scene_name.replace(' ', '_')}.txt",
                mime="text/plain"
            )
        
        # JSON Export
        if st.button("💾 Export Scene (JSON)"):
            scene_json = export_scene_json()
            st.download_button(
                label="Download Scene File",
                data=scene_json,
                file_name=f"scene_{st.session_state.scene_name.replace(' ', '_')}.json",
                mime="application/json"
            )
        
        # Import scene
        uploaded_file = st.file_uploader("📥 Import Scene", type=['json'])
        if uploaded_file is not None:
            scene_data = json.loads(uploaded_file.read())
            st.session_state.scene_elements = scene_data['elements']
            st.session_state.scene_name = scene_data['scene_name']
            st.success("Scene imported successfully!")
            st.rerun()
    
    # Current elements list
    st.divider()
    st.subheader("Current Scene Elements")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📷 Cameras", "💡 Lights", "🎭 Actors", "📦 Props"])
    
    with tab1:
        if st.session_state.scene_elements['cameras']:
            for i, cam in enumerate(st.session_state.scene_elements['cameras']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{cam['name']}**  
                    Position: ({cam['x']}, {cam['y']}, {cam['z']}) | Direction: {cam['direction']} | FL: {cam['focal_length']}mm
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_cam_{i}"):
                        st.session_state.scene_elements['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras added yet. Use the sidebar to add cameras.")
    
    with tab2:
        if st.session_state.scene_elements['lights']:
            for i, light in enumerate(st.session_state.scene_elements['lights']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{light['name']}** ({light['type']})  
                    Position: ({light['x']}, {light['y']}, {light['z']}) | Direction: {light['direction']} | Intensity: {light['intensity']}%
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_light_{i}"):
                        st.session_state.scene_elements['lights'].pop(i)
                        st.rerun()
        else:
            st.info("No lights added yet. Use the sidebar to add lights.")
    
    with tab3:
        if st.session_state.scene_elements['actors']:
            for i, actor in enumerate(st.session_state.scene_elements['actors']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{actor['name']}**  
                    Position: ({actor['x']}, {actor['y']}) | Notes: {actor['notes']}
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_actor_{i}"):
                        st.session_state.scene_elements['actors'].pop(i)
                        st.rerun()
        else:
            st.info("No actors added yet. Use the sidebar to add actors.")
    
    with tab4:
        if st.session_state.scene_elements['props']:
            for i, prop in enumerate(st.session_state.scene_elements['props']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    **{prop['name']}**  
                    Position: ({prop['x']}, {prop['y']})
                    """)
                with col2:
                    if st.button("🗑️", key=f"del_prop_{i}"):
                        st.session_state.scene_elements['props'].pop(i)
                        st.rerun()
        else:
            st.info("No props added yet. Use the sidebar to add props.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        PreViz v2.0 | Educational Technology for Digital Media Arts<br>
        Developed by Eduardo Carmona | CSUDH & LMU
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
