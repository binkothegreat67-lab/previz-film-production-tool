"""
PreViz - Interactive Film Production Planning Tool
Free Educational Technology for Film Students
Developed by: Eduardo Carmona
Version: 4.0 - 2D Floor Plan Edition
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime
import copy

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PreViz 4.0 - Floor Plan",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.2rem;
    }
    .version-badge {
        background-color: #2196F3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if 'scene_elements' not in st.session_state:
    st.session_state.scene_elements = {
        'cameras': [],
        'lights': [],
        'actors': [],
        'set_pieces': [],
        'props': [],
        'vehicles': [],
        'green_screens': []
    }

if 'scene_name' not in st.session_state:
    st.session_state.scene_name = "Untitled Scene"

# ── Presets ───────────────────────────────────────────────────────────────────
FOV_PRESETS = {
    "16mm (Ultra Wide - 107 deg)": 107,
    "24mm (Wide - 84 deg)": 84,
    "35mm (Standard Wide - 63 deg)": 63,
    "50mm (Normal - 47 deg)": 47,
    "85mm (Portrait - 29 deg)": 29,
    "135mm (Telephoto - 18 deg)": 18,
    "200mm (Super Telephoto - 12 deg)": 12
}

LIGHT_COLORS = {
    "Key Light":    "#FFD700",
    "Fill Light":   "#FFFACD",
    "Back Light":   "#FFA500",
    "LED Panel":    "#ADD8E6",
    "Practical":    "#FFD700",
    "Natural Light":"#87CEEB"
}

# ── Helper Functions ──────────────────────────────────────────────────────────
def rotate_point(x, y, angle_deg):
    angle_rad = np.radians(angle_deg)
    nx = x * np.cos(angle_rad) - y * np.sin(angle_rad)
    ny = x * np.sin(angle_rad) + y * np.cos(angle_rad)
    return nx, ny

def fov_triangle(cx, cy, rotation, fov, length=4.0):
    """Return the three points of a FOV triangle: apex, left, right."""
    half = fov / 2.0
    w = np.tan(np.radians(half)) * length
    lx, ly = rotate_point(-w, length, rotation)
    rx, ry = rotate_point( w, length, rotation)
    return (cx, cy), (cx + lx, cy + ly), (cx + rx, cy + ry)

def light_beam(cx, cy, rotation, intensity):
    """Return endpoint of a light beam line."""
    length = 2.0 + intensity / 25.0
    dx, dy = rotate_point(0, length, rotation)
    return cx + dx, cy + dy

def duplicate_element(elem):
    new = copy.deepcopy(elem)
    new['x'] += 1.0
    new['y'] += 1.0
    name = new['name']
    new['name'] = f"{name} Copy" if 'Copy' not in name else f"{name} 2"
    return new

# ── 2D Floor Plan Generator ───────────────────────────────────────────────────
def generate_floor_plan():
    fig = go.Figure()
    stage = 20

    # White background, gray grid
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            range=[-stage/2, stage/2],
            showgrid=True, gridcolor='#e0e0e0', gridwidth=1,
            zeroline=True, zerolinecolor='#bbb', zerolinewidth=2,
            tickmode='linear', tick0=-10, dtick=2,
            title="← West / East →  (feet)"
        ),
        yaxis=dict(
            range=[-stage/2, stage/2],
            showgrid=True, gridcolor='#e0e0e0', gridwidth=1,
            zeroline=True, zerolinecolor='#bbb', zerolinewidth=2,
            tickmode='linear', tick0=-10, dtick=2,
            scaleanchor='x', scaleratio=1,
            title="← South / North →  (feet)"
        ),
        height=680,
        margin=dict(l=60, r=20, t=50, b=50),
        title=dict(
            text=f"🎬  {st.session_state.scene_name}  —  Floor Plan",
            font=dict(size=15, color='#333'),
            x=0.01
        ),
        showlegend=True,
        legend=dict(
            x=1.01, y=1,
            xanchor='left', yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#ccc', borderwidth=1,
            font=dict(size=11)
        )
    )

    elems = st.session_state.scene_elements

    # ── Stage boundary ────────────────────────────────────────────────────────
    s = stage / 2
    fig.add_shape(type="rect", x0=-s, y0=-s, x1=s, y1=s,
                  line=dict(color='#999', width=2, dash='dot'))

    # ── Green Screens ─────────────────────────────────────────────────────────
    for gs in elems.get('green_screens', []):
        w = 6 if '6x8' in gs['size'] else 8 if '8x10' in gs['size'] else 10 if '10x12' in gs['size'] else 12
        dx, dy = rotate_point(w/2, 0, gs['rotation'])
        x0, y0 = gs['x'] - dx, gs['y'] - dy
        x1, y1 = gs['x'] + dx, gs['y'] + dy
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode='lines+markers',
            line=dict(color='#00AA00', width=8),
            marker=dict(size=6, color='#00AA00'),
            name=f"🟢 {gs['name']}",
            hovertemplate=f"<b>{gs['name']}</b><br>Size: {gs['size']}<extra></extra>"
        ))

    # ── Set Pieces ────────────────────────────────────────────────────────────
    piece_colors = {
        'Table': '#8B4513', 'Chair': '#A0522D', 'Sofa': '#D2B48C',
        'Desk': '#8B4513', 'Wall': '#808080', 'Door': '#696969', 'Window': '#87CEEB'
    }
    for piece in elems.get('set_pieces', []):
        color = piece_colors.get(piece['type'], '#888')
        fig.add_trace(go.Scatter(
            x=[piece['x']], y=[piece['y']],
            mode='markers+text',
            marker=dict(size=22, color=color, symbol='square',
                        line=dict(color='#333', width=1.5)),
            text=[piece['type'][0]],
            textfont=dict(color='white', size=10, family='Arial Black'),
            textposition='middle center',
            name=f"🪑 {piece['name']}",
            hovertemplate=f"<b>{piece['name']}</b><br>Type: {piece['type']}<br>({piece['x']:.1f}, {piece['y']:.1f})<extra></extra>"
        ))

    # ── Props ─────────────────────────────────────────────────────────────────
    for prop in elems.get('props', []):
        fig.add_trace(go.Scatter(
            x=[prop['x']], y=[prop['y']],
            mode='markers+text',
            marker=dict(size=14, color='#9C27B0', symbol='diamond',
                        line=dict(color='#6A0080', width=1.5)),
            text=[prop['name']],
            textposition='top center',
            textfont=dict(size=9, color='#6A0080'),
            name=f"🎭 {prop['name']}",
            hovertemplate=f"<b>{prop['name']}</b><br>Type: {prop.get('type','Prop')}<br>Notes: {prop.get('notes','')}<extra></extra>"
        ))

    # ── Vehicles ──────────────────────────────────────────────────────────────
    for veh in elems.get('vehicles', []):
        fig.add_trace(go.Scatter(
            x=[veh['x']], y=[veh['y']],
            mode='markers+text',
            marker=dict(size=28, color='#1565C0', symbol='square',
                        line=dict(color='#0D47A1', width=2)),
            text=[veh['type'][:3]],
            textfont=dict(color='white', size=9, family='Arial Black'),
            textposition='middle center',
            name=f"🚗 {veh['name']}",
            hovertemplate=f"<b>{veh['name']}</b><br>Type: {veh['type']}<br>Rot: {veh['rotation']} deg<extra></extra>"
        ))

    # ── Lights ────────────────────────────────────────────────────────────────
    for light in elems.get('lights', []):
        color = LIGHT_COLORS.get(light['type'], '#FFD700')
        bx, by = light_beam(light['x'], light['y'], light['rotation'], light['intensity'])
        # Beam line
        fig.add_trace(go.Scatter(
            x=[light['x'], bx], y=[light['y'], by],
            mode='lines',
            line=dict(color=color, width=3),
            showlegend=False, hoverinfo='skip', opacity=0.6
        ))
        # Light fixture
        fig.add_trace(go.Scatter(
            x=[light['x']], y=[light['y']],
            mode='markers+text',
            marker=dict(size=18, color=color, symbol='star',
                        line=dict(color='#AA8800', width=1.5)),
            text=[light['name']],
            textposition='top center',
            textfont=dict(size=9, color='#555'),
            name=f"💡 {light['name']} ({light['type']})",
            hovertemplate=(
                f"<b>{light['name']}</b><br>Type: {light['type']}<br>"
                f"Intensity: {light['intensity']}%<br>"
                f"Rot: {light['rotation']} deg<extra></extra>"
            )
        ))

    # ── Actors ────────────────────────────────────────────────────────────────
    for actor in elems.get('actors', []):
        # Actor circle
        fig.add_trace(go.Scatter(
            x=[actor['x']], y=[actor['y']],
            mode='markers+text',
            marker=dict(size=22, color='#E53935', symbol='circle',
                        line=dict(color='#B71C1C', width=2)),
            text=[actor['name']],
            textposition='top center',
            textfont=dict(size=10, color='#B71C1C', family='Arial Black'),
            name=f"🧍 {actor['name']}",
            hovertemplate=f"<b>{actor['name']}</b><br>({actor['x']:.1f}, {actor['y']:.1f})<br>{actor.get('notes','')}<extra></extra>"
        ))
        # Blocking arrow if present
        if actor.get('move_to_x') is not None and actor.get('move_to_y') is not None:
            fig.add_annotation(
                x=actor['move_to_x'], y=actor['move_to_y'],
                ax=actor['x'], ay=actor['y'],
                axref='x', ayref='y',
                arrowhead=3, arrowsize=1.5, arrowwidth=2,
                arrowcolor='#E53935',
                opacity=0.8
            )

    # ── Cameras ───────────────────────────────────────────────────────────────
    for cam in elems.get('cameras', []):
        apex, left, right = fov_triangle(cam['x'], cam['y'], cam['rotation'], cam['fov'])

        # FOV cone (filled triangle)
        fig.add_trace(go.Scatter(
            x=[apex[0], left[0], right[0], apex[0]],
            y=[apex[1], left[1], right[1], apex[1]],
            mode='lines',
            fill='toself',
            fillcolor='rgba(33, 150, 243, 0.12)',
            line=dict(color='#2196F3', width=2, dash='dash'),
            showlegend=False, hoverinfo='skip'
        ))

        # Camera body
        fig.add_trace(go.Scatter(
            x=[cam['x']], y=[cam['y']],
            mode='markers+text',
            marker=dict(size=20, color='#1565C0', symbol='square',
                        line=dict(color='#0D47A1', width=2.5)),
            text=[f"🎥 {cam['name']}"],
            textposition='bottom center',
            textfont=dict(size=10, color='#0D47A1', family='Arial Black'),
            name=f"🎥 {cam['name']} ({cam['focal_length']}mm)",
            hovertemplate=(
                f"<b>{cam['name']}</b><br>"
                f"Focal Length: {cam['focal_length']}mm<br>"
                f"FOV: {cam['fov']} deg<br>"
                f"Rotation: {cam['rotation']} deg<br>"
                f"({cam['x']:.1f}, {cam['y']:.1f})<extra></extra>"
            )
        ))

    return fig


# ── Export Functions ──────────────────────────────────────────────────────────
def export_setup_report():
    elems = st.session_state.scene_elements
    lines = [
        "PRODUCTION SETUP REPORT",
        "=" * 45,
        f"Scene: {st.session_state.scene_name}",
        f"Date:  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 45, ""
    ]

    if elems['cameras']:
        lines += [f"CAMERAS ({len(elems['cameras'])})", "-" * 30]
        for i, c in enumerate(elems['cameras'], 1):
            lines += [
                f"{i}. {c['name']}",
                f"   Focal Length: {c['focal_length']}mm  |  FOV: {c['fov']} deg",
                f"   Position: ({c['x']:.1f}, {c['y']:.1f})",
                f"   Rotation: {c['rotation']} deg", ""
            ]

    if elems['lights']:
        lines += [f"LIGHTING ({len(elems['lights'])})", "-" * 30]
        for i, l in enumerate(elems['lights'], 1):
            lines += [
                f"{i}. {l['name']}  ({l['type']})",
                f"   Intensity: {l['intensity']}%",
                f"   Position: ({l['x']:.1f}, {l['y']:.1f})",
                f"   Rotation: {l['rotation']} deg", ""
            ]

    if elems['actors']:
        lines += [f"TALENT ({len(elems['actors'])})", "-" * 30]
        for i, a in enumerate(elems['actors'], 1):
            lines += [
                f"{i}. {a['name']}",
                f"   Position: ({a['x']:.1f}, {a['y']:.1f})",
                f"   Notes: {a.get('notes', '')}", ""
            ]

    if elems.get('props'):
        lines += [f"PROPS ({len(elems['props'])})", "-" * 30]
        for i, p in enumerate(elems['props'], 1):
            lines += [
                f"{i}. {p['name']}  ({p.get('type','Prop')})",
                f"   Notes: {p.get('notes','')}",
                f"   Position: ({p['x']:.1f}, {p['y']:.1f})", ""
            ]

    if elems['set_pieces']:
        lines += [f"SET PIECES ({len(elems['set_pieces'])})", "-" * 30]
        for i, s in enumerate(elems['set_pieces'], 1):
            lines += [f"{i}. {s['name']}  ({s['type']})  at ({s['x']:.1f}, {s['y']:.1f})", ""]

    if elems['vehicles']:
        lines += [f"VEHICLES ({len(elems['vehicles'])})", "-" * 30]
        for i, v in enumerate(elems['vehicles'], 1):
            lines += [f"{i}. {v['name']}  ({v['type']})  Rot: {v['rotation']} deg", ""]

    if elems['green_screens']:
        lines += [f"GREEN SCREENS ({len(elems['green_screens'])})", "-" * 30]
        for i, g in enumerate(elems['green_screens'], 1):
            lines += [f"{i}. {g['name']}  ({g['size']})  at ({g['x']:.1f}, {g['y']:.1f})", ""]

    lines += ["=" * 45, "EQUIPMENT CHECKLIST"]
    lines.append(f"  [ ] {len(elems['cameras'])} Camera(s)")
    lines.append(f"  [ ] {len(elems['lights'])} Light(s)")
    if elems.get('props'):
        lines.append(f"  [ ] {len(elems['props'])} Prop(s)")
    if elems['green_screens']:
        lines.append(f"  [ ] {len(elems['green_screens'])} Green Screen(s)")

    return "\n".join(lines)


def export_scene_json():
    return json.dumps({
        'scene_name': st.session_state.scene_name,
        'created': datetime.now().isoformat(),
        'elements': st.session_state.scene_elements,
        'version': '4.0'
    }, indent=2)


# ── Main Application ──────────────────────────────────────────────────────────
def main():
    elems = st.session_state.scene_elements

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header">🎬 PreViz 4.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Free Educational Technology for Film Students</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="version-badge">Floor Plan Edition</div>', unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Scene Setup")

        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name

        st.divider()

        element_type = st.selectbox(
            "Add Element to Scene",
            [
                "-- Select --",
                "🎥  Camera",
                "💡  Light",
                "🧍  Actor / Blocking",
                "🪑  Set Piece",
                "🎭  Prop",
                "🚗  Vehicle",
                "🟢  Green Screen"
            ]
        )

        # ── Camera ────────────────────────────────────────────────────────────
        if "Camera" in element_type:
            st.subheader("🎥 Add Camera")
            with st.form("camera_form"):
                n = len(elems['cameras'])
                cam_name = st.text_input("Camera Name", value=f"Camera {chr(65 + n)}")
                col1, col2 = st.columns(2)
                with col1:
                    cam_x = st.number_input("X (feet)", value=float(n * 2), step=0.5)
                    cam_y = st.number_input("Y (feet)", value=-5.0, step=0.5)
                with col2:
                    cam_rotation = st.slider("Rotation (deg)", 0, 359, 0)
                focal_preset = st.selectbox("Focal Length", list(FOV_PRESETS.keys()))
                cam_focal = int(focal_preset.split('mm')[0])
                cam_fov = FOV_PRESETS[focal_preset]
                st.caption(f"Field of View: {cam_fov} deg")
                if st.form_submit_button("✅ Add Camera"):
                    elems['cameras'].append({
                        'name': cam_name,
                        'x': cam_x, 'y': cam_y,
                        'rotation': cam_rotation,
                        'focal_length': cam_focal,
                        'fov': cam_fov
                    })
                    st.success(f"Added {cam_name}")
                    st.rerun()

        # ── Light ─────────────────────────────────────────────────────────────
        elif "Light" in element_type:
            st.subheader("💡 Add Light")
            with st.form("light_form"):
                light_name = st.text_input("Light Name",
                    value=f"Light {len(elems['lights']) + 1}")
                light_type = st.selectbox("Type",
                    ["Key Light", "Fill Light", "Back Light",
                     "LED Panel", "Practical", "Natural Light"])
                col1, col2 = st.columns(2)
                with col1:
                    light_x = st.number_input("X (feet)", value=3.0, step=0.5)
                    light_y = st.number_input("Y (feet)", value=3.0, step=0.5)
                with col2:
                    light_rotation = st.slider("Rotation", 0, 359, 225, key="light_rot")
                    light_intensity = st.slider("Intensity %", 0, 100, 80, key="light_int")
                if st.form_submit_button("✅ Add Light"):
                    elems['lights'].append({
                        'name': light_name, 'type': light_type,
                        'x': light_x, 'y': light_y,
                        'rotation': light_rotation, 'intensity': light_intensity
                    })
                    st.success(f"Added {light_name}")
                    st.rerun()

        # ── Actor ─────────────────────────────────────────────────────────────
        elif "Actor" in element_type:
            st.subheader("🧍 Add Actor / Blocking")
            with st.form("actor_form"):
                actor_name = st.text_input("Name",
                    value=f"Actor {len(elems['actors']) + 1}")
                col1, col2 = st.columns(2)
                with col1:
                    ax = st.number_input("Start X (feet)", value=0.0, step=0.5)
                    ay = st.number_input("Start Y (feet)", value=0.0, step=0.5)
                with col2:
                    add_move = st.checkbox("Add blocking arrow")
                    mx = st.number_input("Move to X", value=0.0, step=0.5)
                    my = st.number_input("Move to Y", value=2.0, step=0.5)
                notes = st.text_input("Blocking notes",
                    placeholder="e.g. Walks toward camera")
                if st.form_submit_button("✅ Add Actor"):
                    entry = {
                        'name': actor_name, 'x': ax, 'y': ay, 'notes': notes,
                        'move_to_x': mx if add_move else None,
                        'move_to_y': my if add_move else None
                    }
                    elems['actors'].append(entry)
                    st.success(f"Added {actor_name}")
                    st.rerun()

        # ── Set Piece ─────────────────────────────────────────────────────────
        elif "Set Piece" in element_type:
            st.subheader("🪑 Add Set Piece")
            with st.form("setpiece_form"):
                piece_name = st.text_input("Name", value="Furniture")
                piece_type = st.selectbox("Type",
                    ["Table", "Chair", "Sofa", "Desk", "Wall", "Door", "Window"])
                col1, col2 = st.columns(2)
                with col1:
                    px = st.number_input("X (feet)", value=0.0, step=0.5)
                with col2:
                    py = st.number_input("Y (feet)", value=0.0, step=0.5)
                if st.form_submit_button("✅ Add Set Piece"):
                    elems['set_pieces'].append({
                        'name': piece_name, 'type': piece_type, 'x': px, 'y': py
                    })
                    st.success(f"Added {piece_name}")
                    st.rerun()

        # ── Prop ──────────────────────────────────────────────────────────────
        elif "Prop" in element_type:
            st.subheader("🎭 Add Prop")
            with st.form("props_form"):
                prop_name = st.text_input("Prop Name", value="Prop")
                prop_type = st.selectbox("Category",
                    ["Weapon", "Phone", "Bag / Briefcase", "Food / Drink",
                     "Book / Document", "Electronics", "Tool", "Other"])
                col1, col2 = st.columns(2)
                with col1:
                    ppx = st.number_input("X (feet)", value=0.0, step=0.5)
                with col2:
                    ppy = st.number_input("Y (feet)", value=0.0, step=0.5)
                prop_notes = st.text_input("Notes",
                    placeholder="e.g. Hero prop, breakaway version")
                if st.form_submit_button("✅ Add Prop"):
                    elems['props'].append({
                        'name': prop_name, 'type': prop_type,
                        'x': ppx, 'y': ppy, 'notes': prop_notes
                    })
                    st.success(f"Added {prop_name}")
                    st.rerun()

        # ── Vehicle ───────────────────────────────────────────────────────────
        elif "Vehicle" in element_type:
            st.subheader("🚗 Add Vehicle")
            with st.form("vehicle_form"):
                veh_name = st.text_input("Name", value="Car")
                veh_type = st.selectbox("Type",
                    ["Car", "Van", "Truck", "Motorcycle", "Bicycle"])
                col1, col2 = st.columns(2)
                with col1:
                    vx = st.number_input("X (feet)", value=0.0, step=0.5)
                    vy = st.number_input("Y (feet)", value=0.0, step=0.5)
                with col2:
                    vrot = st.slider("Rotation", 0, 359, 0, key="veh_rot")
                if st.form_submit_button("✅ Add Vehicle"):
                    elems['vehicles'].append({
                        'name': veh_name, 'type': veh_type,
                        'x': vx, 'y': vy, 'rotation': vrot
                    })
                    st.success(f"Added {veh_name}")
                    st.rerun()

        # ── Green Screen ──────────────────────────────────────────────────────
        elif "Green" in element_type:
            st.subheader("🟢 Add Green Screen")
            with st.form("greenscreen_form"):
                gs_name = st.text_input("Name", value="Green Screen")
                gs_size = st.selectbox("Size",
                    ["6x8 ft", "8x10 ft", "10x12 ft", "12x20 ft"])
                col1, col2 = st.columns(2)
                with col1:
                    gsx = st.number_input("X (feet)", value=0.0, step=0.5)
                    gsy = st.number_input("Y (feet)", value=6.0, step=0.5)
                with col2:
                    gsrot = st.slider("Rotation", 0, 359, 0, key="gs_rot")
                if st.form_submit_button("✅ Add Green Screen"):
                    elems['green_screens'].append({
                        'name': gs_name, 'size': gs_size,
                        'x': gsx, 'y': gsy, 'rotation': gsrot
                    })
                    st.success(f"Added {gs_name}")
                    st.rerun()

        st.divider()

        # Quick Templates
        st.subheader("📋 Quick Templates")

        if st.button("Three-Point Lighting"):
            elems['lights'] = [
                {'name': 'Key Light',  'type': 'Key Light',  'x':  3.0, 'y':  3.0, 'rotation': 225, 'intensity': 100},
                {'name': 'Fill Light', 'type': 'Fill Light', 'x': -3.0, 'y':  3.0, 'rotation': 135, 'intensity': 50},
                {'name': 'Back Light', 'type': 'Back Light', 'x':  0.0, 'y': -3.0, 'rotation': 0,   'intensity': 70}
            ]
            elems['actors'] = [{'name': 'Subject', 'x': 0.0, 'y': 0.0, 'notes': 'Center frame', 'move_to_x': None, 'move_to_y': None}]
            elems['cameras'] = [{'name': 'Camera A', 'x': 0.0, 'y': -8.0, 'rotation': 0, 'focal_length': 50, 'fov': 47}]
            st.rerun()

        if st.button("Multi-Camera Interview"):
            elems['cameras'] = [
                {'name': 'Camera A (Wide)',          'x':  0.0, 'y': -8.0, 'rotation': 0,   'focal_length': 35, 'fov': 63},
                {'name': 'Camera B (Close)',          'x': -3.0, 'y': -7.0, 'rotation': 15,  'focal_length': 85, 'fov': 29},
                {'name': 'Camera C (Over Shoulder)', 'x':  2.0, 'y': -2.0, 'rotation': 180, 'focal_length': 50, 'fov': 47}
            ]
            elems['actors'] = [{'name': 'Interviewee', 'x': 0.0, 'y': 0.0, 'notes': 'Seated, camera left', 'move_to_x': None, 'move_to_y': None}]
            elems['set_pieces'] = [{'name': 'Chair', 'type': 'Chair', 'x': 0.0, 'y': 0.0}]
            st.rerun()

        if st.button("Green Screen Setup"):
            elems['green_screens'] = [{'name': 'Main Green Screen', 'size': '12x20 ft', 'x': 0.0, 'y': 8.0, 'rotation': 0}]
            elems['cameras'] = [{'name': 'Camera A', 'x': 0.0, 'y': -6.0, 'rotation': 0, 'focal_length': 50, 'fov': 47}]
            elems['lights'] = [
                {'name': 'Subject Key',          'type': 'Key Light',  'x':  3.0, 'y': -2.0, 'rotation': 200, 'intensity': 100},
                {'name': 'Subject Fill',         'type': 'Fill Light', 'x': -3.0, 'y': -2.0, 'rotation': 160, 'intensity': 60},
                {'name': 'Green Screen Light L', 'type': 'LED Panel',  'x': -4.0, 'y':  6.0, 'rotation': 90,  'intensity': 80},
                {'name': 'Green Screen Light R', 'type': 'LED Panel',  'x':  4.0, 'y':  6.0, 'rotation': 90,  'intensity': 80}
            ]
            elems['actors'] = [{'name': 'Subject', 'x': 0.0, 'y': 2.0, 'notes': '6 ft from green screen', 'move_to_x': None, 'move_to_y': None}]
            st.rerun()

        st.divider()

        if st.button("🗑️ Clear All", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [], 'lights': [], 'actors': [],
                'set_pieces': [], 'props': [], 'vehicles': [], 'green_screens': []
            }
            st.rerun()

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    col_plan, col_info = st.columns([3, 1])

    with col_plan:
        fig = generate_floor_plan()
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.subheader("Scene Summary")
        st.metric("🎥 Cameras",   len(elems['cameras']))
        st.metric("💡 Lights",    len(elems['lights']))
        st.metric("🧍 Actors",    len(elems['actors']))
        st.metric("🎭 Props",     len(elems.get('props', [])))
        st.metric("🪑 Set Pieces",len(elems['set_pieces']))

        st.divider()
        st.subheader("📤 Export")

        if st.button("📄 Setup Report"):
            report = export_setup_report()
            st.download_button("⬇️ Download Report", data=report,
                file_name=f"previz_{st.session_state.scene_name.replace(' ','_')}.txt",
                mime="text/plain")

        if st.button("💾 Save Scene"):
            st.download_button("⬇️ Download Scene", data=export_scene_json(),
                file_name=f"scene_{st.session_state.scene_name.replace(' ','_')}.json",
                mime="application/json")

        st.divider()
        uploaded = st.file_uploader("📥 Load Scene", type=['json'])
        if uploaded:
            data = json.loads(uploaded.read())
            st.session_state.scene_elements = data['elements']
            st.session_state.scene_name = data['scene_name']
            st.success("Scene loaded!")
            st.rerun()

    # ── ELEMENT TABS ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Scene Elements")

    tabs = st.tabs([
        "🎥 Cameras", "💡 Lights", "🧍 Actors",
        "🪑 Set Pieces", "🎭 Props", "🚗 Vehicles", "🟢 Green Screens"
    ])

    with tabs[0]:
        if elems['cameras']:
            for i, cam in enumerate(elems['cameras']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{cam['name']}** | {cam['focal_length']}mm | FOV {cam['fov']} deg | Rot {cam['rotation']} deg  \n"
                                f"Pos: ({cam['x']:.1f}, {cam['y']:.1f})")
                with c2:
                    if st.button("📋", key=f"dup_cam_{i}"):
                        elems['cameras'].append(duplicate_element(cam))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_cam_{i}"):
                        elems['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras yet. Use sidebar to add.")

    with tabs[1]:
        if elems['lights']:
            for i, l in enumerate(elems['lights']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{l['name']}** | {l['type']} | {l['intensity']}%  \n"
                                f"Pos: ({l['x']:.1f}, {l['y']:.1f}) | Rot {l['rotation']} deg")
                with c2:
                    if st.button("📋", key=f"dup_light_{i}"):
                        elems['lights'].append(duplicate_element(l))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_light_{i}"):
                        elems['lights'].pop(i)
                        st.rerun()
        else:
            st.info("No lights yet. Use sidebar to add.")

    with tabs[2]:
        if elems['actors']:
            for i, a in enumerate(elems['actors']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{a['name']}** | Pos: ({a['x']:.1f}, {a['y']:.1f})  \n"
                                f"{a.get('notes','')}")
                with c2:
                    if st.button("🗑️", key=f"del_actor_{i}"):
                        elems['actors'].pop(i)
                        st.rerun()
        else:
            st.info("No actors yet. Use sidebar to add.")

    with tabs[3]:
        if elems['set_pieces']:
            for i, s in enumerate(elems['set_pieces']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{s['name']}** ({s['type']}) | ({s['x']:.1f}, {s['y']:.1f})")
                with c2:
                    if st.button("🗑️", key=f"del_piece_{i}"):
                        elems['set_pieces'].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces yet. Use sidebar to add.")

    with tabs[4]:
        props_list = elems.get('props', [])
        if props_list:
            for i, p in enumerate(props_list):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{p['name']}** ({p.get('type','Prop')}) | ({p['x']:.1f}, {p['y']:.1f})  \n"
                                f"{p.get('notes','')}")
                with c2:
                    if st.button("🗑️", key=f"del_prop_{i}"):
                        elems['props'].pop(i)
                        st.rerun()
        else:
            st.info("No props yet. Use sidebar to add.")

    with tabs[5]:
        if elems['vehicles']:
            for i, v in enumerate(elems['vehicles']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{v['name']}** ({v['type']}) | ({v['x']:.1f}, {v['y']:.1f}) | Rot {v['rotation']} deg")
                with c2:
                    if st.button("🗑️", key=f"del_veh_{i}"):
                        elems['vehicles'].pop(i)
                        st.rerun()
        else:
            st.info("No vehicles yet. Use sidebar to add.")

    with tabs[6]:
        if elems['green_screens']:
            for i, g in enumerate(elems['green_screens']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{g['name']}** ({g['size']}) | ({g['x']:.1f}, {g['y']:.1f}) | Rot {g['rotation']} deg")
                with c2:
                    if st.button("🗑️", key=f"del_gs_{i}"):
                        elems['green_screens'].pop(i)
                        st.rerun()
        else:
            st.info("No green screens yet. Use sidebar to add.")

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.85rem; padding: 0.5rem;'>
        PreViz v4.0 &nbsp;|&nbsp; Free Educational Technology for Film Students
        &nbsp;|&nbsp; Developed by Eduardo Carmona &nbsp;|&nbsp; CSUDH &amp; LMU
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
