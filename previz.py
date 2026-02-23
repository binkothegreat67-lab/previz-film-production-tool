"""
PreViz - Interactive Film Production Planning Tool
Educational Technology for Digital Media Arts
Developed by: Eduardo Carmona, MFA — CSUDH · LMU
Version: 4.0 (Open Educational Edition)

Licensed under the GNU General Public License v3.0
Free and open for all students worldwide — from Los Angeles to Lima to Windhoek.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime
import copy

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PreViz 4.0 - Film Production Planning",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .version-badge {
        background-color: #2E7D32;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .open-badge {
        background-color: #1565C0;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    .nav-selected {
        background-color: #1f1f1f;
        color: white;
        padding: 0.4rem 1.2rem;
        border-radius: 8px;
    }
    .camera-hud {
        background-color: #0a0a0a;
        color: #00ff88;
        padding: 12px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.85rem;
        border: 1px solid #00ff88;
    }
    .stButton>button {
        width: 100%;
    }
    .kelvin-label {
        font-size: 0.8rem;
        color: #555;
    }
    @media print {
        @page { size: landscape; margin: 0.5cm; }
        .stSidebar, .stButton, header, footer, [data-testid="stToolbar"],
        [data-testid="stDecoration"], .stDownloadButton { display: none !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; }
        .js-plotly-plot, .plotly { page-break-inside: avoid; }
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def init_session_state():
    # Studio 3D state
    if 'scene_elements' not in st.session_state:
        st.session_state.scene_elements = {
            'cameras': [], 'lights': [], 'actors': [],
            'set_pieces': [], 'vehicles': [], 'screens': []
        }
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "Perspective"
    if 'scene_name' not in st.session_state:
        st.session_state.scene_name = "Untitled Scene"
    if 'clipboard' not in st.session_state:
        st.session_state.clipboard = None

    # Navigation state
    if 'active_page' not in st.session_state:
        st.session_state.active_page = "Preset Set"

    # Preset page state
    if 'preset_cam_pan' not in st.session_state:
        st.session_state.preset_cam_pan = 0
    if 'preset_cam_dolly' not in st.session_state:
        st.session_state.preset_cam_dolly = 1.5
    if 'preset_cam_focal' not in st.session_state:
        st.session_state.preset_cam_focal = "24mm (Wide - Master Shot)"
    if 'preset_key_intensity' not in st.session_state:
        st.session_state.preset_key_intensity = 75
    if 'preset_key_kelvin' not in st.session_state:
        st.session_state.preset_key_kelvin = 5600
    if 'preset_key_x' not in st.session_state:
        st.session_state.preset_key_x = 3.0
    if 'preset_fill1_kelvin' not in st.session_state:
        st.session_state.preset_fill1_kelvin = 5600
    if 'preset_back_kelvin' not in st.session_state:
        st.session_state.preset_back_kelvin = 5600
    if 'preset_fill2_kelvin' not in st.session_state:
        st.session_state.preset_fill2_kelvin = 5600
    if 'preset_iso' not in st.session_state:
        st.session_state.preset_iso = 800
    if 'preset_nd' not in st.session_state:
        st.session_state.preset_nd = 0
    if 'preset_show_fill1' not in st.session_state:
        st.session_state.preset_show_fill1 = True
    if 'preset_show_back' not in st.session_state:
        st.session_state.preset_show_back = True
    if 'preset_show_fill2' not in st.session_state:
        st.session_state.preset_show_fill2 = True
    if 'preset_show_key' not in st.session_state:
        st.session_state.preset_show_key = True
    if 'preset_fps' not in st.session_state:
        st.session_state.preset_fps = 24
    if 'preset_resolution' not in st.session_state:
        st.session_state.preset_resolution = "1080p"
    # Talent position
    if 'preset_talent_x' not in st.session_state:
        st.session_state.preset_talent_x = 15.0
    if 'preset_talent_y' not in st.session_state:
        st.session_state.preset_talent_y = 10.0

    # Slate / production info
    if 'slate_production' not in st.session_state:
        st.session_state.slate_production = "My Production"
    if 'slate_scene' not in st.session_state:
        st.session_state.slate_scene = "1"
    if 'slate_shot' not in st.session_state:
        st.session_state.slate_shot = "A"
    if 'slate_shot_type' not in st.session_state:
        st.session_state.slate_shot_type = "Master Shot"
    if 'slate_director' not in st.session_state:
        st.session_state.slate_director = ""
    if 'slate_dp' not in st.session_state:
        st.session_state.slate_dp = ""
    if 'slate_gaffer' not in st.session_state:
        st.session_state.slate_gaffer = ""

    # Approval gate
    if 'approved_dp' not in st.session_state:
        st.session_state.approved_dp = False
    if 'approved_gaffer' not in st.session_state:
        st.session_state.approved_gaffer = False
    if 'approved_director' not in st.session_state:
        st.session_state.approved_director = False
    if 'approval_timestamp' not in st.session_state:
        st.session_state.approval_timestamp = ""

    # Light intensities for ratio
    if 'preset_fill_intensity' not in st.session_state:
        st.session_state.preset_fill_intensity = 50
    if 'preset_back_intensity' not in st.session_state:
        st.session_state.preset_back_intensity = 70


init_session_state()

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
CAMERA_HEIGHT_PRESETS = {
    "Eye Level (5 ft)": 5.0, "Shoulder Level (4.5 ft)": 4.5,
    "Chest Level (4 ft)": 4.0, "Waist Level (3 ft)": 3.0,
    "Low Angle (2 ft)": 2.0, "Ground Level (0.5 ft)": 0.5,
    "High Angle (7 ft)": 7.0, "Overhead (9 ft)": 9.0, "Crane Height (12 ft)": 12.0
}

FOV_PRESETS = {
    "16mm (Ultra Wide)": 107, "24mm (Wide)": 84,
    "35mm (Standard Wide)": 63, "50mm (Normal)": 47,
    "85mm (Portrait)": 29, "135mm (Telephoto)": 18, "200mm (Super Telephoto)": 12
}

PRESET_FOCAL_LENGTHS = {
    "12mm (Ultra Wide - 120°)": {"mm": 12, "fov": 120},
    "24mm (Wide - Master Shot)": {"mm": 24, "fov": 84},
    "35mm (Standard Wide)": {"mm": 35, "fov": 63},
    "50mm (Normal)": {"mm": 50, "fov": 47},
    "85mm (Portrait / Close-Up)": {"mm": 85, "fov": 29},
    "135mm (Telephoto)": {"mm": 135, "fov": 18},
}

ND_FILTERS = {
    "None (0 stops)": 0,
    "ND 0.3 (1 stop)": 1,
    "ND 0.6 (2 stops)": 2,
    "ND 0.9 (3 stops)": 3,
    "ND 1.2 (4 stops)": 4,
    "ND 1.5 (5 stops)": 5,
    "ND 1.8 (6 stops)": 6,
    "ND 3.0 (10 stops)": 10,
}

STANDARD_FSTOPS = [1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0]

# ─────────────────────────────────────────────────────────────────────────────
# TOOLTIPS — multilingual-ready (Phase 2: swap this dict for each language)
# ─────────────────────────────────────────────────────────────────────────────
TIPS = {
    "key_light":    "The Key Light is the main, dominant light source on your subject. It defines shadows and sets the mood of the scene.",
    "fill_light":   "Fill Lights reduce the harshness of shadows created by the Key Light. Lower fill = more dramatic contrast.",
    "back_light":   "The Back Light (or hair light) separates the subject from the background, adding depth and dimension.",
    "kelvin":       "Color Temperature (Kelvin) describes the color of light. Lower K = warm orange. Higher K = cool blue. 5600K = natural daylight.",
    "fstop":        "The f-stop (aperture) controls how much light enters the lens. f/1.4 = very open (bright). f/16 = very closed (dim).",
    "iso":          "ISO / Gain controls the camera sensor's sensitivity to light. Higher ISO = brighter image but more digital noise (grain).",
    "shutter":      "Shutter speed determines motion blur. For video, the 180° rule: shutter = 2x frame rate. At 24fps use 1/48.",
    "nd_filter":    "ND (Neutral Density) filters reduce light entering the lens without changing color. Like sunglasses for your camera.",
    "pan":          "Pan moves the camera left or right on a horizontal axis, like turning your head. Pan left / Pan right.",
    "tilt":         "Tilt moves the camera up or down on a vertical axis, like nodding. Tilt up / Tilt down.",
    "dolly":        "Dolly moves the entire camera physically forward (push in) or backward (pull back) toward or away from the subject.",
    "fov":          "Field of View (FOV) is how wide the camera sees. Wide lenses (short focal length) capture more. Telephoto captures less but magnifies.",
    "light_ratio":  "Light Ratio is the relationship between Key and Fill intensities. 2:1 = soft, even. 4:1 = dramatic. 8:1 = extreme contrast.",
    "master_shot":  "A Master Shot frames the entire scene from a wide angle, establishing the geography of the set for the audience.",
    "four_wall":    "The Fourth Wall is the invisible boundary between the set and the camera. It is always open — the camera lives there.",
    "approval":     "A floor plan must be approved by the DP, Gaffer, and Director before it becomes an official production document.",
}

def tip(key):
    """Render a collapsible tooltip expander for a given key."""
    if key in TIPS:
        with st.expander("ℹ️ What is this?", expanded=False):
            st.caption(TIPS[key])


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS — SHARED
# ─────────────────────────────────────────────────────────────────────────────
def angle_to_radians(angle_deg):
    return np.radians(angle_deg)

def rotate_point(x, y, angle_deg):
    angle_rad = angle_to_radians(angle_deg)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    return x * cos_a - y * sin_a, x * sin_a + y * cos_a

def create_camera_frustum(x, y, z, rotation, fov=60, name="Camera"):
    cone_length = 4
    cone_width = np.tan(np.radians(fov / 2)) * cone_length
    points = [(0, 0), (-cone_width, cone_length), (cone_width, cone_length)]
    rotated_points = [rotate_point(px, py, rotation) for px, py in points]
    return [(x + px, y + py, z) for px, py, _ in rotated_points]

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
        except:
            new_element['name'] = f"{original_name} Copy"
    else:
        new_element['name'] = f"{original_name} Copy"
    return new_element

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS — PRESET PAGE
# ─────────────────────────────────────────────────────────────────────────────
def kelvin_to_color(kelvin):
    """Map color temperature in Kelvin to approximate hex color."""
    k = int(kelvin)
    if k <= 2000:   return '#FF6600'
    elif k <= 2500: return '#FF8C30'
    elif k <= 2700: return '#FFA040'
    elif k <= 3200: return '#FFB560'
    elif k <= 4000: return '#FFCC88'
    elif k <= 4500: return '#FFE0B0'
    elif k <= 5000: return '#FFF0D5'
    elif k <= 5600: return '#FFFAF4'
    elif k <= 6000: return '#F4F8FF'
    elif k <= 6500: return '#E8F0FF'
    elif k <= 8000: return '#D0E4FF'
    else:           return '#BBCEFF'

def kelvin_to_name(kelvin):
    """Human-readable color temperature label."""
    k = int(kelvin)
    if k <= 2200:   return "Candlelight"
    elif k <= 2700: return "Warm Tungsten"
    elif k <= 3200: return "Tungsten / Halogen"
    elif k <= 4000: return "Warm White"
    elif k <= 4500: return "Neutral White"
    elif k <= 5000: return "Horizon Daylight"
    elif k <= 5600: return "Daylight (Standard)"
    elif k <= 6000: return "Bright Daylight"
    elif k <= 6500: return "Overcast Sky"
    elif k <= 8000: return "Cloudy / Shade"
    else:           return "Blue Sky / HMI"

def calculate_fstop(key_intensity, iso, shutter_denom, nd_stops=0):
    """
    Calculate suggested f-stop based on Key Light intensity.
    Uses photographic exposure formula scaled for educational clarity.
    Key Light intensity 0–100 maps to scene EV 8–14 range.
    """
    if key_intensity <= 0:
        return "N/A"
    scene_ev = 8.0 + (key_intensity / 100.0) * 6.0
    # N² = 2^scene_ev * (100/ISO) * (1/shutter_denom) / 2^nd_stops
    f_squared = (2 ** scene_ev) * (100.0 / iso) * (1.0 / shutter_denom) / (2 ** nd_stops)
    f_raw = np.sqrt(max(f_squared, 0.01))
    # Snap to nearest standard f-stop
    closest = min(STANDARD_FSTOPS, key=lambda x: abs(x - f_raw))
    return closest

def draw_camera_shape(fig, cam_x, cam_y, pan_deg, fov_deg):
    """Draw a 2D overhead camera body + FOV cone on the Plotly figure."""
    # Camera body: 1.6 ft wide, 0.8 ft deep (overhead rectangle)
    body_w, body_d = 0.8, 0.4
    # Lens protrusion: 0.5 ft forward
    lens_l = 0.5

    # Define camera body corners relative to camera center, facing +Y (toward stage)
    body_pts = [
        (-body_w, -body_d), (body_w, -body_d),
        (body_w, body_d), (-body_w, body_d), (-body_w, -body_d)
    ]
    # Lens points (front center protrusion)
    lens_pts = [
        (-body_w * 0.4, body_d), (body_w * 0.4, body_d),
        (0, body_d + lens_l), (-body_w * 0.4, body_d)
    ]

    # Rotate all points by pan angle
    def rot(pts, angle):
        return [rotate_point(x, y, angle) for x, y in pts]

    body_rot = rot(body_pts, pan_deg)
    lens_rot = rot(lens_pts, pan_deg)

    # Draw camera body
    bx = [cam_x + p[0] for p in body_rot]
    by = [cam_y + p[1] for p in body_rot]
    fig.add_trace(go.Scatter(
        x=bx, y=by, mode='lines',
        fill='toself', fillcolor='#1a1a2e',
        line=dict(color='#4a90d9', width=2),
        showlegend=False, hoverinfo='skip', name='_cam_body'
    ))

    # Draw lens
    lx = [cam_x + p[0] for p in lens_rot]
    ly = [cam_y + p[1] for p in lens_rot]
    fig.add_trace(go.Scatter(
        x=lx, y=ly, mode='lines',
        fill='toself', fillcolor='#4a90d9',
        line=dict(color='#74b9ff', width=1.5),
        showlegend=False, hoverinfo='skip', name='_cam_lens'
    ))

    # FOV cone — extend to a reasonable distance
    half_fov = np.radians(fov_deg / 2)
    cone_dist = 18  # feet

    # Left ray: pan_deg + 90 offset for facing-up convention, then add half_fov
    # Camera faces +Y, pan rotates from there
    base_angle_rad = np.radians(pan_deg) + np.pi / 2  # facing direction in math coords
    left_angle = base_angle_rad + half_fov
    right_angle = base_angle_rad - half_fov

    lx_end = cam_x + cone_dist * np.cos(left_angle)
    ly_end = cam_y + cone_dist * np.sin(left_angle)
    rx_end = cam_x + cone_dist * np.cos(right_angle)
    ry_end = cam_y + cone_dist * np.sin(right_angle)

    # Clip to stage (rough clipping, just limit to stage bounds)
    lx_end = np.clip(lx_end, -2, 32)
    ly_end = np.clip(ly_end, -2, 22)
    rx_end = np.clip(rx_end, -2, 32)
    ry_end = np.clip(ry_end, -2, 22)

    fig.add_trace(go.Scatter(
        x=[cam_x, lx_end, rx_end, cam_x],
        y=[cam_y, ly_end, ry_end, cam_y],
        mode='lines',
        fill='toself',
        fillcolor='rgba(74, 144, 217, 0.08)',
        line=dict(color='rgba(74,144,217,0.5)', width=1.5, dash='dash'),
        showlegend=False, hoverinfo='skip', name='_fov'
    ))

    # Camera label
    fig.add_annotation(
        x=cam_x, y=cam_y - 1.2,
        text="<b>📷 CAMERA</b><br><i>Wall 4 — Master Shot</i>",
        showarrow=False,
        font=dict(size=10, color='#4a90d9'),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='#4a90d9',
        borderwidth=1,
        borderpad=3
    )

def draw_key_light(fig, key_x, key_y, key_kelvin, talent_x=15, talent_y=10, visible=True):
    """Draw the Key Light as a half-dome (semicircle) facing right toward subject."""
    if not visible:
        return
    color = kelvin_to_color(key_kelvin)
    dome_r = 1.2
    # Half dome: arc from -90° to +90° (right-facing semicircle)
    theta = np.linspace(-np.pi / 2, np.pi / 2, 40)
    dome_x = [key_x + dome_r * np.cos(t) for t in theta]
    dome_y = [key_y + dome_r * np.sin(t) for t in theta]
    # Close with straight line (flat back on left)
    dome_x_full = dome_x + [key_x, key_x + dome_r * np.cos(-np.pi / 2)]
    dome_y_full = dome_y + [key_y, key_y + dome_r * np.sin(-np.pi / 2)]

    fig.add_trace(go.Scatter(
        x=dome_x_full, y=dome_y_full, mode='lines',
        fill='toself',
        fillcolor=f'rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.35)',
        line=dict(color=color, width=2.5),
        showlegend=False, hoverinfo='skip', name='_key'
    ))

    # Beam line toward subject
    fig.add_trace(go.Scatter(
        x=[key_x + dome_r, talent_x], y=[key_y, talent_y],
        mode='lines',
        line=dict(color=color, width=1.5, dash='dot'),
        showlegend=False, hoverinfo='skip', name='_keybeam'
    ))

    fig.add_annotation(
        x=key_x - 0.5, y=key_y + 1.8,
        text=f"<b>KEY LIGHT</b><br>{key_kelvin}K",
        showarrow=False,
        font=dict(size=9, color='#333'),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor=color, borderwidth=1.5, borderpad=3
    )

def draw_overhead_light(fig, lx, ly, label, kelvin, visible=True):
    """Draw an overhead/preset light as a circle marker with label."""
    if not visible:
        return
    color = kelvin_to_color(kelvin)
    # Outer glow circle
    theta = np.linspace(0, 2 * np.pi, 36)
    glow_r = 0.9
    gx = [lx + glow_r * np.cos(t) for t in theta]
    gy = [ly + glow_r * np.sin(t) for t in theta]
    fig.add_trace(go.Scatter(
        x=gx, y=gy, mode='lines',
        fill='toself',
        fillcolor=f'rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.4)',
        line=dict(color=color, width=2),
        showlegend=False, hoverinfo='skip', name=f'_light_{label}'
    ))
    # Inner dot
    fig.add_trace(go.Scatter(
        x=[lx], y=[ly], mode='markers',
        marker=dict(size=8, color=color, symbol='circle',
                    line=dict(color='#555', width=1)),
        showlegend=False, hoverinfo='skip', name=f'_lightcenter_{label}'
    ))
    # Label
    fig.add_annotation(
        x=lx, y=ly - 1.3,
        text=f"<b>{label}</b><br>{kelvin}K",
        showarrow=False,
        font=dict(size=8.5, color='#333'),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor=color, borderwidth=1, borderpad=2
    )

def draw_subject(fig, talent_x=15, talent_y=10, talent_name="TALENT"):
    """Draw the subject/actor marker at given position."""
    fig.add_trace(go.Scatter(
        x=[talent_x], y=[talent_y], mode='markers+text',
        marker=dict(size=20, color='#e74c3c', symbol='circle',
                    line=dict(color='#922b21', width=2.5)),
        text=[talent_name],
        textposition='top center',
        textfont=dict(size=10, color='#922b21'),
        showlegend=False, name='Talent',
        hovertemplate=f'<b>{talent_name}</b><br>X: {talent_x:.1f} ft ({talent_x*0.3048:.2f} m)<br>Y: {talent_y:.1f} ft ({talent_y*0.3048:.2f} m)<extra></extra>'
    ))
    # Small crosshair lines for precision
    cross = 0.6
    fig.add_trace(go.Scatter(
        x=[talent_x - cross, talent_x + cross, None, talent_x, talent_x],
        y=[talent_y, talent_y, None, talent_y - cross, talent_y + cross],
        mode='lines', line=dict(color='#922b21', width=1, dash='dot'),
        showlegend=False, hoverinfo='skip', name='_talent_cross'
    ))

def calculate_light_ratio(key_intensity, fill_intensity):
    """Calculate Key:Fill light ratio and return ratio string + mood description."""
    if fill_intensity <= 0:
        return "Key Only", "No fill — maximum contrast / silhouette"
    ratio_raw = key_intensity / fill_intensity
    # Snap to standard ratios
    standard = [1, 1.5, 2, 2.5, 3, 4, 6, 8, 16]
    closest = min(standard, key=lambda x: abs(x - ratio_raw))
    ratio_str = f"{closest}:1" if closest != 1 else "1:1"
    moods = {
        1:   "1:1 — Flat, even. Perfect for product shots or news.",
        1.5: "1.5:1 — Very soft. Gentle, natural look.",
        2:   "2:1 — Classic soft portrait. Flattering, cinematic.",
        2.5: "2.5:1 — Balanced drama. Common for interviews.",
        3:   "3:1 — Standard cinematic. Clear shadows, strong shape.",
        4:   "4:1 — Dramatic. Deep shadows, bold contrast.",
        6:   "6:1 — High contrast. Noir, thriller, tension.",
        8:   "8:1 — Extreme drama. Strong chiaroscuro effect.",
        16:  "16:1 — Near silhouette. Expressionistic, abstract.",
    }
    return ratio_str, moods.get(closest, f"{closest}:1 — High contrast")


def draw_light_ratio_badge(fig, ratio_str, mood_str, key_intensity, fill_intensity):
    """Draw the light ratio badge on the floor plan."""
    # Color coding by drama level
    ratio_val = key_intensity / fill_intensity if fill_intensity > 0 else 99
    if ratio_val <= 2:
        badge_color = "#2196F3"   # blue — soft
    elif ratio_val <= 4:
        badge_color = "#4CAF50"   # green — classic
    elif ratio_val <= 6:
        badge_color = "#FF9800"   # orange — dramatic
    else:
        badge_color = "#F44336"   # red — extreme

    fig.add_shape(type="rect",
        x0=19, y0=14.5, x1=29.5, y1=17.5,
        fillcolor="rgba(10,10,10,0.82)",
        line=dict(color=badge_color, width=2), layer="above"
    )
    fig.add_annotation(
        x=24.2, y=16.8,
        text=f"<b>LIGHT RATIO</b>",
        showarrow=False, font=dict(size=8.5, color=badge_color, family="monospace"),
        bgcolor="rgba(0,0,0,0)"
    )
    fig.add_annotation(
        x=24.2, y=15.9,
        text=f"<b>Key : Fill = {ratio_str}</b>",
        showarrow=False, font=dict(size=10, color="white", family="monospace"),
        bgcolor="rgba(0,0,0,0)"
    )
    fig.add_annotation(
        x=24.2, y=15.1,
        text=f"<i>{mood_str.split('—')[1].strip() if '—' in mood_str else mood_str}</i>",
        showarrow=False, font=dict(size=8, color="#CCCCCC", family="monospace"),
        bgcolor="rgba(0,0,0,0)"
    )


def draw_slate(fig, production, scene, shot, shot_type, director, dp, gaffer,
               date_str, approved_dp, approved_gaffer, approved_director, approval_ts):
    """Draw a film-slate clapperboard panel on the floor plan."""
    # Main slate body — upper left area of the stage
    sx0, sy0, sx1, sy1 = 0.3, 12.0, 10.0, 19.5

    # Slate body (black)
    fig.add_shape(type="rect", x0=sx0, y0=sy0, x1=sx1, y1=sy1,
        fillcolor="#111111", line=dict(color="#333333", width=2), layer="above")

    # Clapper stripe band (top of slate — diagonal stripes = classic clapperboard)
    stripe_h = 1.5
    for i in range(6):
        fig.add_shape(type="rect",
            x0=sx0 + i * 1.6, y0=sy1 - stripe_h,
            x1=sx0 + i * 1.6 + 0.8, y1=sy1,
            fillcolor="#FFFFFF" if i % 2 == 0 else "#111111",
            line=dict(color="#111111", width=0.5), layer="above"
        )

    # Diagonal slash overlay on stripe
    fig.add_shape(type="line",
        x0=sx0, y0=sy1 - stripe_h, x1=sx1, y1=sy1,
        line=dict(color="#FF3333", width=2), layer="above"
    )

    # SLATE label
    fig.add_annotation(x=(sx0 + sx1) / 2, y=sy1 - 0.75,
        text="<b>🎬 PREVIZ SLATE</b>",
        showarrow=False, font=dict(size=7.5, color="#000000", family="monospace"),
        bgcolor="rgba(0,0,0,0)"
    )

    # Production fields
    fields = [
        ("PROD", production[:20]),
        ("SCENE", f"{scene}  SHOT {shot}"),
        ("TYPE", shot_type),
        ("DIR", director[:16] if director else "—"),
        ("DP", dp[:16] if dp else "—"),
        ("GAFFER", gaffer[:14] if gaffer else "—"),
        ("DATE", date_str),
    ]
    for idx, (label, value) in enumerate(fields):
        y_pos = sy1 - stripe_h - 0.75 - idx * 0.95
        if y_pos < sy0 + 0.3:
            break
        fig.add_annotation(x=sx0 + 0.3, y=y_pos, xanchor="left",
            text=f"<span style='color:#888888;font-size:7px'>{label}</span>  "
                 f"<span style='color:#FFFFFF;font-size:8px'><b>{value}</b></span>",
            showarrow=False, font=dict(size=8, family="monospace"),
            bgcolor="rgba(0,0,0,0)"
        )

    # Divider line
    fig.add_shape(type="line",
        x0=sx0 + 0.2, y0=sy0 + 1.8, x1=sx1 - 0.2, y1=sy0 + 1.8,
        line=dict(color="#444444", width=0.8), layer="above"
    )

    # Approval status
    all_approved = approved_dp and approved_gaffer and approved_director
    if all_approved:
        badge_txt = f"✅ APPROVED — {approval_ts}"
        badge_col = "#00FF88"
    else:
        checks = []
        if not approved_dp:       checks.append("DP")
        if not approved_gaffer:   checks.append("GAFFER")
        if not approved_director: checks.append("DIR")
        badge_txt = f"⏳ PENDING: {', '.join(checks)}"
        badge_col = "#FF9900"

    fig.add_annotation(x=(sx0 + sx1) / 2, y=sy0 + 0.9,
        text=f"<b>{badge_txt}</b>",
        showarrow=False, font=dict(size=7.5, color=badge_col, family="monospace"),
        bgcolor="rgba(0,0,0,0)"
    )


def draw_lower_third(fig, cam_pan, cam_dolly, focal_key, fov,
                     key_intensity, key_kelvin, fill1_kelvin, back_kelvin, fill2_kelvin,
                     suggested_fstop, iso, shutter_denom, nd_label,
                     fps, resolution, talent_x, talent_y,
                     show_key, show_fill1, show_back, show_fill2):
    """Draw a live lower-third info bar directly on the floor plan figure."""
    lens_mm = PRESET_FOCAL_LENGTHS.get(focal_key, {"mm": 24})["mm"]
    dist_cam_sub = round(abs(talent_y - cam_dolly), 1)
    dist_key_sub = round(abs(talent_x - st.session_state.preset_key_x), 1)

    # Build light summary string
    active_lights = []
    if show_key:   active_lights.append(f"KEY {key_kelvin}K {key_intensity}%")
    if show_fill1: active_lights.append(f"FILL1 {fill1_kelvin}K")
    if show_back:  active_lights.append(f"BACK {back_kelvin}K")
    if show_fill2: active_lights.append(f"FILL2 {fill2_kelvin}K")
    lights_str = "  |  ".join(active_lights) if active_lights else "NO LIGHTS"

    left_text  = (f"<b>📷 CAMERA</b>  {lens_mm}mm · FOV {fov}°  |  "
                  f"Pan {cam_pan:+}°  |  Dolly {cam_dolly:.1f}ft  |  "
                  f"Dist→Talent {dist_cam_sub}ft / {dist_cam_sub*0.3048:.2f}m")

    center_text = (f"<b>EXPOSURE</b>  f/{suggested_fstop}  |  "
                   f"ISO {iso}  |  1/{shutter_denom}  |  {nd_label.split('(')[0].strip()}  |  "
                   f"{fps}fps  {resolution}")

    right_text  = (f"<b>💡 LIGHTING</b>  {lights_str}  |  "
                   f"Key→Talent {dist_key_sub}ft / {dist_key_sub*0.3048:.2f}m")

    # Lower-third background band — lives below y=0 in figure space
    fig.add_shape(type="rect",
        x0=-5, y0=-8.8, x1=35, y1=-5.5,
        fillcolor="#1a1a1a", line=dict(color="#333", width=0),
        layer="below"
    )
    # Thin accent line on top of band
    fig.add_shape(type="line",
        x0=-5, y0=-5.5, x1=35, y1=-5.5,
        line=dict(color="#00ff88", width=1.5)
    )

    # Left block — camera
    fig.add_annotation(x=-4.5, y=-6.2, xanchor="left",
        text=left_text, showarrow=False,
        font=dict(size=8.5, color='#DDDDDD', family='monospace'),
        bgcolor='rgba(0,0,0,0)', borderpad=0
    )
    # Center block — exposure
    fig.add_annotation(x=15, y=-7.2, xanchor="center",
        text=center_text, showarrow=False,
        font=dict(size=8.5, color='#00ff88', family='monospace'),
        bgcolor='rgba(0,0,0,0)', borderpad=0
    )
    # Right block — lighting
    fig.add_annotation(x=34.5, y=-8.2, xanchor="right",
        text=right_text, showarrow=False,
        font=dict(size=8.5, color='#AADDFF', family='monospace'),
        bgcolor='rgba(0,0,0,0)', borderpad=0
    )
    # Talent position info
    fig.add_annotation(x=15, y=-8.6, xanchor="center",
        text=f"🎭 TALENT  X: {talent_x:.1f}ft / {talent_x*0.3048:.2f}m   Y: {talent_y:.1f}ft / {talent_y*0.3048:.2f}m",
        showarrow=False,
        font=dict(size=8, color='#FF9999', family='monospace'),
        bgcolor='rgba(0,0,0,0)', borderpad=0
    )



def generate_preset_floor_plan(
    cam_pan, cam_dolly, focal_key,
    key_intensity, key_kelvin, key_x,
    fill1_kelvin, back_kelvin, fill2_kelvin,
    show_fill1, show_back, show_fill2, show_key,
    talent_x=15, talent_y=10, talent_name="TALENT",
    suggested_fstop="N/A", iso=800, shutter_denom=48,
    nd_label="None (0 stops)", fps="24 fps", resolution="1080p",
    fill_intensity=50, back_intensity=70,
    slate_production="", slate_scene="1", slate_shot="A",
    slate_shot_type="Master Shot", slate_director="", slate_dp="",
    slate_gaffer="", slate_date="",
    approved_dp=False, approved_gaffer=False, approved_director=False,
    approval_ts=""
):
    """Generate the 2D overhead floor plan for the Preset Set page."""
    fig = go.Figure()

    stage_w, stage_d = 30, 20

    # ── Stage floor (satin white) ──────────────────────────────────────────
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=stage_w, y1=stage_d,
        fillcolor="#FAF8F4",
        line=dict(color="#FAF8F4", width=0)
    )

    # ── Overhead grid (soft grey, every 2 feet) ────────────────────────────
    for x in range(0, stage_w + 1, 2):
        fig.add_shape(type="line",
            x0=x, y0=0, x1=x, y1=stage_d,
            line=dict(color="#D8D8D8", width=0.6)
        )
    for y in range(0, stage_d + 1, 2):
        fig.add_shape(type="line",
            x0=0, y0=y, x1=stage_w, y1=y,
            line=dict(color="#D8D8D8", width=0.6)
        )

    # ── Walls ──────────────────────────────────────────────────────────────
    wall_style = dict(color="#222222", width=5)
    # Wall 1 — Left
    fig.add_shape(type="line", x0=0, y0=0, x1=0, y1=stage_d, line=wall_style)
    # Wall 2 — Back
    fig.add_shape(type="line", x0=0, y0=stage_d, x1=stage_w, y1=stage_d, line=wall_style)
    # Wall 3 — Right
    fig.add_shape(type="line", x0=stage_w, y0=0, x1=stage_w, y1=stage_d, line=wall_style)
    # Wall 4 — OPEN (camera side, dashed)
    fig.add_shape(type="line", x0=0, y0=0, x1=stage_w, y1=0,
        line=dict(color="#AAAAAA", width=2, dash="dash")
    )

    # Wall labels
    for label, lx, ly, angle in [
        ("WALL 1", -1.5, stage_d / 2, 0),
        ("WALL 2", stage_w / 2, stage_d + 1.2, 0),
        ("WALL 3", stage_w + 1.5, stage_d / 2, 0),
        ("4TH WALL — OPEN (CAMERA)", stage_w / 2, -1.5, 0),
    ]:
        fig.add_annotation(
            x=lx, y=ly, text=f"<i>{label}</i>",
            showarrow=False, font=dict(size=9, color='#888888')
        )

    # ── Dimension labels ────────────────────────────────────────────────────
    fig.add_annotation(
        x=stage_w / 2, y=-2.8,
        text=f"<b>Stage Width: 30 ft / 9.14 m</b>",
        showarrow=False, font=dict(size=10, color='#555')
    )
    fig.add_annotation(
        x=-3.5, y=stage_d / 2,
        text=f"<b>20 ft<br>6.1 m</b>",
        showarrow=False, font=dict(size=9, color='#555'), textangle=-90
    )

    # ── Grid tick labels (feet + meters) ───────────────────────────────────
    for x in range(0, stage_w + 1, 5):
        m = round(x * 0.3048, 1)
        fig.add_annotation(
            x=x, y=-0.6,
            text=f"{x}ft<br>{m}m",
            showarrow=False, font=dict(size=7, color='#999')
        )
    for y in range(0, stage_d + 1, 5):
        m = round(y * 0.3048, 1)
        fig.add_annotation(
            x=-0.8, y=y,
            text=f"{y}ft<br>{m}m",
            showarrow=False, font=dict(size=7, color='#999')
        )

    # ── Overhead preset lights ──────────────────────────────────────────────
    draw_overhead_light(fig, 4.5, 17, "Fill #1", fill1_kelvin, show_fill1)
    draw_overhead_light(fig, 15, 19, "Back Light", back_kelvin, show_back)
    draw_overhead_light(fig, 25.5, 17, "Fill #2", fill2_kelvin, show_fill2)

    # ── Key Light (half-dome, left side) ───────────────────────────────────
    key_y = talent_y  # tracks talent depth
    draw_key_light(fig, key_x, key_y, key_kelvin, talent_x=talent_x, talent_y=talent_y, visible=show_key)

    # ── Subject (talent, movable) ──────────────────────────────────────────
    draw_subject(fig, talent_x=talent_x, talent_y=talent_y, talent_name=talent_name)

    # ── Camera ─────────────────────────────────────────────────────────────
    fov = PRESET_FOCAL_LENGTHS.get(focal_key, {"fov": 84})["fov"]
    cam_x_pos = 15
    cam_y_pos = cam_dolly  # dolly position (push in / pull back)
    draw_camera_shape(fig, cam_x_pos, cam_y_pos, cam_pan, fov)

    # Distance marker — camera to talent
    dist_ft = abs(talent_y - cam_y_pos)
    dist_m = round(dist_ft * 0.3048, 2)
    fig.add_annotation(
        x=16.5, y=(cam_y_pos + talent_y) / 2,
        text=f"↕ {dist_ft:.1f}ft<br>↕ {dist_m}m",
        showarrow=False, font=dict(size=8, color='#666'),
        bgcolor='rgba(255,255,255,0.8)'
    )

    # ── Slate (clapperboard panel) ────────────────────────────────────────
    draw_slate(fig, slate_production, slate_scene, slate_shot, slate_shot_type,
               slate_director, slate_dp, slate_gaffer, slate_date,
               approved_dp, approved_gaffer, approved_director, approval_ts)

    # ── Light Ratio Badge ─────────────────────────────────────────────────
    if show_key and fill_intensity > 0:
        ratio_str, mood_str = calculate_light_ratio(key_intensity, fill_intensity)
        draw_light_ratio_badge(fig, ratio_str, mood_str, key_intensity, fill_intensity)
    elif show_key:
        draw_light_ratio_badge(fig, "Key Only", "No fill — maximum contrast", key_intensity, 0)

    # ── Lower Third ────────────────────────────────────────────────────────
    draw_lower_third(
        fig, cam_pan, cam_dolly, focal_key, fov,
        key_intensity, key_kelvin, fill1_kelvin, back_kelvin, fill2_kelvin,
        suggested_fstop, iso, shutter_denom, nd_label, fps, resolution,
        talent_x, talent_y, show_key, show_fill1, show_back, show_fill2
    )

    # ── Layout ─────────────────────────────────────────────────────────────
    fig.update_layout(
        xaxis=dict(
            range=[-5, 35], showgrid=False, zeroline=False,
            showticklabels=False, scaleanchor="y", scaleratio=1
        ),
        yaxis=dict(
            range=[-9.5, 24], showgrid=False, zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='#F0EEE8',
        paper_bgcolor='#F0EEE8',
        height=700,
        margin=dict(l=60, r=20, t=40, b=20),
        showlegend=False,
        title=dict(
            text="<b>PreViz 4.0 — Preset Set · 2D Overhead Floor Plan · 30×20 ft / 9.14×6.10 m</b>",
            font=dict(size=13, color='#333'), x=0.5
        )
    )

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PRESET PAGE
# ─────────────────────────────────────────────────────────────────────────────
def preset_page():
    st.markdown("### 🎯 Preset Set — Guided Production Setup")
    st.caption("30 × 20 ft studio stage · Three-point lighting · Video camera (Master Shot) · Beginner & Intermediate")

    with st.sidebar:
        st.header("🎯 Preset Controls")

        # ── 🎬 Slate / Production Info ──────────────────────────────────────
        st.subheader("🎬 Production Slate")
        tip("approval")
        slate_production = st.text_input("Production Title", value=st.session_state.slate_production, key="slate_prod_input")
        st.session_state.slate_production = slate_production
        c1, c2, c3 = st.columns(3)
        with c1:
            slate_scene = st.text_input("Scene #", value=st.session_state.slate_scene, key="slate_scene_input")
            st.session_state.slate_scene = slate_scene
        with c2:
            slate_shot = st.text_input("Shot", value=st.session_state.slate_shot, key="slate_shot_input")
            st.session_state.slate_shot = slate_shot
        with c3:
            slate_shot_type = st.selectbox("Shot Type",
                ["Master Shot", "Wide", "Medium", "Close-Up", "ECU", "OTS", "Insert", "Cutaway"],
                index=0, key="slate_type_sel")
            st.session_state.slate_shot_type = slate_shot_type
        slate_director = st.text_input("Director", value=st.session_state.slate_director, key="slate_dir_input")
        st.session_state.slate_director = slate_director
        c1, c2 = st.columns(2)
        with c1:
            slate_dp = st.text_input("DP / Cinematographer", value=st.session_state.slate_dp, key="slate_dp_input")
            st.session_state.slate_dp = slate_dp
        with c2:
            slate_gaffer = st.text_input("Gaffer", value=st.session_state.slate_gaffer, key="slate_gaffer_input")
            st.session_state.slate_gaffer = slate_gaffer
        slate_date = st.session_state.slate_date

        st.divider()

        # ── 📷 Camera ─────────────────────────────────────────────────────────
        st.subheader("📷 Camera")
        st.caption("Video Camera — Wall 4 (Open) · Master Shot")
        tip("master_shot")

        focal_key = st.selectbox(
            "Lens / Focal Length",
            list(PRESET_FOCAL_LENGTHS.keys()),
            index=1,  # 24mm default
            key="preset_focal_sel"
        )
        st.session_state.preset_cam_focal = focal_key
        sel_lens = PRESET_FOCAL_LENGTHS[focal_key]
        st.caption(f"FOV: {sel_lens['fov']}° | {sel_lens['mm']}mm")
        tip("fov")

        cam_pan = st.slider("Pan (°) — Left / Right", -45, 45,
                            st.session_state.preset_cam_pan, key="preset_pan_slider")
        st.session_state.preset_cam_pan = cam_pan
        tip("pan")

        cam_dolly = st.slider("Dolly — Push In / Pull Back (ft)", 0.5, 9.0,
                               st.session_state.preset_cam_dolly, step=0.5, key="preset_dolly_slider")
        st.session_state.preset_cam_dolly = cam_dolly
        tip("dolly")

        cam_tilt = st.select_slider(
            "Tilt",
            options=["Extreme Down", "Low Angle", "Neutral", "High Angle", "Extreme Up"],
            value="Neutral",
            key="preset_tilt"
        )
        st.caption(f"🎬 Tilt: {cam_tilt} (applies in 3D mode)")
        tip("tilt")

        st.divider()

        # ── Video Specs ─────────────────────────────────────────────────────
        st.subheader("📹 Video Specifications")
        fps = st.selectbox("Frame Rate", ["24 fps", "25 fps", "30 fps", "60 fps"],
                           index=0, key="preset_fps_sel")
        shutter_display = st.selectbox("Shutter Speed",
            ["1/48 (24fps sync)", "1/50 (25fps sync)", "1/60 (30fps sync)", "1/120 (60fps sync)"],
            index=0, key="preset_shutter_sel"
        )
        shutter_denom_map = {"1/48 (24fps sync)": 48, "1/50 (25fps sync)": 50,
                             "1/60 (30fps sync)": 60, "1/120 (60fps sync)": 120}
        shutter_denom = shutter_denom_map[shutter_display]

        resolution = st.selectbox("Resolution", ["720p", "1080p", "4K UHD", "4K DCI"],
                                  index=1, key="preset_res_sel")
        iso = st.select_slider("ISO / Gain",
            options=[100, 200, 400, 800, 1600, 3200, 6400],
            value=st.session_state.preset_iso, key="preset_iso_slider"
        )
        st.session_state.preset_iso = iso
        tip("iso")

        st.divider()

        # ── Exposure ─────────────────────────────────────────────────────
        st.subheader("🔆 Exposure")
        nd_label = st.selectbox("ND Filter", list(ND_FILTERS.keys()),
                                index=0, key="preset_nd_sel")
        nd_stops = ND_FILTERS[nd_label]
        st.session_state.preset_nd = nd_stops
        tip("nd_filter")

        st.divider()

        # ── Key Light ──────────────────────────────────────────────────────
        st.subheader("💡 Key Light")
        st.caption("Left side — 90° to camera — Half-dome")
        tip("key_light")
        show_key = st.toggle("Show Key Light", value=st.session_state.preset_show_key,
                              key="toggle_key")
        st.session_state.preset_show_key = show_key

        key_intensity = st.slider("Intensity (%)", 0, 100,
                                   st.session_state.preset_key_intensity, key="key_int")
        st.session_state.preset_key_intensity = key_intensity

        key_kelvin = st.slider("Color Temp (K) — Key", 2000, 10000,
                                st.session_state.preset_key_kelvin, step=100, key="key_k")
        st.session_state.preset_key_kelvin = key_kelvin
        st.caption(f"🌡 {key_kelvin}K — {kelvin_to_name(key_kelvin)}")
        tip("kelvin")

        key_x = st.slider("Dolly — Key Light (X position)", 1.0, 12.0,
                           st.session_state.preset_key_x, step=0.5, key="key_x_sl")
        st.session_state.preset_key_x = key_x
        key_dist = abs(st.session_state.preset_talent_x - key_x)
        st.caption(f"Distance to talent: {key_dist:.1f} ft / {key_dist*0.3048:.2f} m")

        st.divider()

        # ── Overhead Lights ────────────────────────────────────────────────
        st.subheader("🔆 Overhead Lights (Fill & Back)")
        st.caption("All default: 5600K Daylight")
        tip("fill_light")
        tip("back_light")

        # ── Fill Intensity (for light ratio) ───────────────────────────────
        fill_intensity = st.slider("Fill Light Intensity (%)", 0, 100,
                                    st.session_state.preset_fill_intensity, key="fill_int_sl")
        st.session_state.preset_fill_intensity = fill_intensity
        tip("light_ratio")

        if show_key and key_intensity > 0 and fill_intensity > 0:
            ratio_str, mood_str = calculate_light_ratio(key_intensity, fill_intensity)
            st.success(f"**Light Ratio** — {ratio_str}   {mood_str}")
        elif show_key and fill_intensity == 0:
            st.warning("Key Only — no fill, maximum contrast")

        back_intensity = st.slider("Back Light Intensity (%)", 0, 100,
                                    st.session_state.preset_back_intensity, key="back_int_sl")
        st.session_state.preset_back_intensity = back_intensity

        show_fill1 = st.toggle("Fill #1 (Upper Left)", value=st.session_state.preset_show_fill1,
                                key="toggle_fill1")
        st.session_state.preset_show_fill1 = show_fill1
        if show_fill1:
            fill1_k = st.slider("Fill #1 Color Temp (K)", 2000, 10000,
                                  st.session_state.preset_fill1_kelvin, step=100, key="fill1_k")
            st.session_state.preset_fill1_kelvin = fill1_k
            st.caption(f"🌡 {fill1_k}K — {kelvin_to_name(fill1_k)}")
        else:
            fill1_k = st.session_state.preset_fill1_kelvin

        show_back = st.toggle("Back Light (Center Wall 2)", value=st.session_state.preset_show_back,
                               key="toggle_back")
        st.session_state.preset_show_back = show_back
        if show_back:
            back_k = st.slider("Back Light Color Temp (K)", 2000, 10000,
                                 st.session_state.preset_back_kelvin, step=100, key="back_k")
            st.session_state.preset_back_kelvin = back_k
            st.caption(f"🌡 {back_k}K — {kelvin_to_name(back_k)}")
        else:
            back_k = st.session_state.preset_back_kelvin

        show_fill2 = st.toggle("Fill #2 (Upper Right)", value=st.session_state.preset_show_fill2,
                                key="toggle_fill2")
        st.session_state.preset_show_fill2 = show_fill2
        if show_fill2:
            fill2_k = st.slider("Fill #2 Color Temp (K)", 2000, 10000,
                                  st.session_state.preset_fill2_kelvin, step=100, key="fill2_k")
            st.session_state.preset_fill2_kelvin = fill2_k
            st.caption(f"🌡 {fill2_k}K — {kelvin_to_name(fill2_k)}")
        else:
            fill2_k = st.session_state.preset_fill2_kelvin

        st.divider()

        # ── Talent Position ────────────────────────────────────────────────
        st.subheader("🎭 Talent Position")
        st.caption("Move the actor/subject on the stage floor")
        talent_name = st.text_input("Talent Name", value="TALENT", key="talent_name_input")
        talent_x = st.slider("Stage Left / Right (X)", 2.0, 28.0,
                              float(st.session_state.preset_talent_x), step=0.5, key="talent_x_sl")
        talent_y = st.slider("Stage Depth (Y) — back ↑ front ↓", 2.0, 18.0,
                              float(st.session_state.preset_talent_y), step=0.5, key="talent_y_sl")
        st.session_state.preset_talent_x = talent_x
        st.session_state.preset_talent_y = talent_y
        t_x_m = round(talent_x * 0.3048, 2)
        t_y_m = round(talent_y * 0.3048, 2)
        st.caption(f"Position: ({talent_x}ft, {talent_y}ft) · ({t_x_m}m, {t_y_m}m)")
        if st.button("↩️ Reset to Center", key="reset_talent"):
            st.session_state.preset_talent_x = 15.0
            st.session_state.preset_talent_y = 10.0
            st.rerun()

        st.divider()

        # ── ✅ Approval Gate ────────────────────────────────────────────────
        st.subheader("✅ Floor Plan Approval")
        st.caption("All three must approve before printing is enabled.")
        tip("approval")

        approved_dp = st.checkbox("✅ DP / Cinematographer Approved",
                                   value=st.session_state.approved_dp, key="chk_dp")
        approved_gaffer = st.checkbox("✅ Gaffer Approved",
                                       value=st.session_state.approved_gaffer, key="chk_gaffer")
        approved_director = st.checkbox("✅ Director Approved",
                                         value=st.session_state.approved_director, key="chk_director")
        st.session_state.approved_dp = approved_dp
        st.session_state.approved_gaffer = approved_gaffer
        st.session_state.approved_director = approved_director

        all_approved = approved_dp and approved_gaffer and approved_director

        if all_approved:
            if not st.session_state.approval_timestamp:
                st.session_state.approval_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success(f"🟢 APPROVED — {st.session_state.approval_timestamp}")
            if st.button("🖨️ Print Approved Floor Plan", key="print_btn", type="primary"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        else:
            # Reset timestamp if approvals removed
            st.session_state.approval_timestamp = ""
            missing = []
            if not approved_dp:       missing.append("DP")
            if not approved_gaffer:   missing.append("Gaffer")
            if not approved_director: missing.append("Director")
            st.warning(f"⏳ Awaiting approval from: {', '.join(missing)}")
            st.button("🔒 Print Locked — Pending Approval", key="print_btn_locked",
                      disabled=True)

        st.divider()
        st.caption("PreViz 4.0 · GPL Open Educational Edition\nFree for all students worldwide 🌍")


    col_main, col_hud = st.columns([3, 1])

    # Compute exposure before drawing (needed by lower third)
    suggested_fstop = calculate_fstop(key_intensity, iso, shutter_denom, nd_stops)
    dist_cam_to_sub = abs(talent_y - cam_dolly)

    with col_main:
        fig = generate_preset_floor_plan(
            cam_pan=cam_pan,
            cam_dolly=cam_dolly,
            focal_key=focal_key,
            key_intensity=key_intensity,
            key_kelvin=key_kelvin,
            key_x=key_x,
            fill1_kelvin=fill1_k,
            back_kelvin=back_k,
            fill2_kelvin=fill2_k,
            show_fill1=show_fill1,
            show_back=show_back,
            show_fill2=show_fill2,
            show_key=show_key,
            talent_x=talent_x,
            talent_y=talent_y,
            talent_name=talent_name,
            suggested_fstop=suggested_fstop,
            iso=iso,
            shutter_denom=shutter_denom,
            nd_label=nd_label,
            fps=fps,
            resolution=resolution,
            fill_intensity=fill_intensity,
            back_intensity=back_intensity,
            slate_production=slate_production,
            slate_scene=slate_scene,
            slate_shot=slate_shot,
            slate_shot_type=slate_shot_type,
            slate_director=slate_director,
            slate_dp=slate_dp,
            slate_gaffer=slate_gaffer,
            slate_date=slate_date,
            approved_dp=approved_dp,
            approved_gaffer=approved_gaffer,
            approved_director=approved_director,
            approval_ts=st.session_state.approval_timestamp
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_hud:
        # ── Camera HUD ─────────────────────────────────────────────────────

        st.markdown("#### 📷 Camera Data")
        st.markdown(f"""
<div class="camera-hud">
REC ● &nbsp;<b>VIDEO</b><br>
━━━━━━━━━━━━━━━━━━<br>
SHOT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MASTER / WIDE<br>
LENS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{PRESET_FOCAL_LENGTHS[focal_key]['mm']}mm<br>
FOV &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{PRESET_FOCAL_LENGTHS[focal_key]['fov']}°<br>
RES &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{resolution}<br>
FPS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{fps}<br>
SHUTTER &nbsp;1/{shutter_denom}<br>
ISO &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{iso}<br>
ND &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{nd_label.split('(')[0].strip()}<br>
━━━━━━━━━━━━━━━━━━<br>
F-STOP &nbsp;&nbsp;&nbsp;<b>f/{suggested_fstop}</b><br>
━━━━━━━━━━━━━━━━━━<br>
PAN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{cam_pan:+}°<br>
TILT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{cam_tilt}<br>
DOLLY &nbsp;&nbsp;&nbsp;&nbsp;{cam_dolly:.1f} ft<br>
DIST→TALENT {dist_cam_to_sub:.1f} ft<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{dist_cam_to_sub*0.3048:.2f} m<br>
TALENT POS&nbsp;({talent_x:.1f}, {talent_y:.1f}) ft<br>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### 💡 Lighting Summary")
        lights_info = []
        if show_key:
            lights_info.append(f"**Key Light** · {key_kelvin}K · {key_intensity}% · {kelvin_to_name(key_kelvin)}")
        if show_fill1:
            lights_info.append(f"**Fill #1** · {fill1_k}K · {kelvin_to_name(fill1_k)}")
        if show_back:
            lights_info.append(f"**Back Light** · {back_k}K · {kelvin_to_name(back_k)}")
        if show_fill2:
            lights_info.append(f"**Fill #2** · {fill2_k}K · {kelvin_to_name(fill2_k)}")
        for li in lights_info:
            st.markdown(f"• {li}")

        if not lights_info:
            st.info("All lights off")

        st.markdown("#### 📐 Stage Dimensions")
        st.markdown("""
| | Feet | Meters |
|--|--|--|
| Width | 30 ft | 9.14 m |
| Depth | 20 ft | 6.10 m |
""")

        st.markdown("#### 📖 Exposure Guide")
        if key_intensity > 0:
            st.markdown(f"""
The suggested **f/{suggested_fstop}** is calculated from:
- Key Light intensity: **{key_intensity}%**
- ISO: **{iso}**
- Shutter: **1/{shutter_denom}**
- ND: **{nd_stops} stops**

*Key Light drives exposure. Adjust intensity, ISO, or ND to control your f-stop.*
""")
        else:
            st.warning("Key Light is at 0%. No exposure reference available.")


# ─────────────────────────────────────────────────────────────────────────────
# SANDLOT PAGE (placeholder — Phase 2)
# ─────────────────────────────────────────────────────────────────────────────
def sandlot_page():
    st.markdown("### 🏖️ Sandlot — Open Creative Stage")
    st.caption("Full creative freedom · Four-wall stage · No preset configuration")

    st.info("""
**Sandlot is coming in Phase 2.**

This will be an open, fully customizable stage where creativity leads.
Same four-wall architecture as the Preset Set — but nothing pre-placed.
You build it from scratch for each production need.

Features planned:
- Same 2D floor plan, blank canvas
- Drag-to-place elements
- Custom stage dimensions
- Free lighting placement (any position, any angle, any color temp)
- Save / load your custom layouts
- Export to 3D Studio mode for full pre-visualization

*Designed for advanced students and experienced directors/DPs/gaffers.*
""")

    st.markdown("---")
    st.markdown("#### 🌍 PreViz is free and open for all students — everywhere.")
    st.markdown("Licensed under **GNU GPL v3.0** · Developed by Eduardo Carmona, MFA — CSUDH · LMU")


# ─────────────────────────────────────────────────────────────────────────────
# STUDIO 3D PAGE (existing functionality)
# ─────────────────────────────────────────────────────────────────────────────
def generate_3d_scene(view_mode="Perspective"):
    """Generate enhanced 3D visualization."""
    fig = go.Figure()
    stage_size = 20

    grid_lines_x, grid_lines_y = [], []
    for i in range(-stage_size // 2, stage_size // 2 + 1, 2):
        grid_lines_x.extend([i, i, None])
        grid_lines_y.extend([-stage_size // 2, stage_size // 2, None])
        grid_lines_x.extend([-stage_size // 2, stage_size // 2, None])
        grid_lines_y.extend([i, i, None])

    fig.add_trace(go.Scatter3d(
        x=grid_lines_x, y=grid_lines_y,
        z=[0] * len(grid_lines_x), mode='lines',
        line=dict(color='lightgray', width=1),
        showlegend=False, hoverinfo='skip'
    ))

    for cam in st.session_state.scene_elements['cameras']:
        fig.add_trace(go.Scatter3d(
            x=[cam['x']], y=[cam['y']], z=[cam['z']],
            mode='markers+text',
            marker=dict(size=12, color='blue', symbol='diamond'),
            text=[cam['name']], textposition='top center',
            name=cam['name'],
            hovertemplate=f"<b>{cam['name']}</b><br>Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f})<br>Rot: {cam['rotation']}°<br>FL: {cam['focal_length']}mm<extra></extra>"
        ))
        frustum = create_camera_frustum(cam['x'], cam['y'], cam['z'],
                                        cam['rotation'], cam['fov'])
        for pt in [frustum[1], frustum[2]]:
            fig.add_trace(go.Scatter3d(
                x=[frustum[0][0], pt[0]], y=[frustum[0][1], pt[1]],
                z=[frustum[0][2], pt[2]], mode='lines',
                line=dict(color='blue', width=3, dash='dash'),
                showlegend=False, hoverinfo='skip', opacity=0.6
            ))

    for light in st.session_state.scene_elements['lights']:
        color_map = {"Key Light": 'yellow', "Fill Light": 'lightyellow',
                     "Back Light": 'orange', "LED Panel": 'white',
                     "Practical": 'gold', "Natural Light": 'lightblue'}
        lc = color_map.get(light['type'], 'white')
        fig.add_trace(go.Scatter3d(
            x=[light['x']], y=[light['y']], z=[light['z']],
            mode='markers+text',
            marker=dict(size=10, color=lc, symbol='diamond'),
            text=[light['name']], textposition='top center',
            name=light['name'],
            hovertemplate=f"<b>{light['name']}</b><br>{light['type']}<br>Intensity: {light['intensity']}%<extra></extra>"
        ))
        beam = create_light_coverage(light['x'], light['y'], light['z'],
                                     light['rotation'], light['intensity'], light['type'])
        fig.add_trace(go.Scatter3d(
            x=[beam[0], beam[3]], y=[beam[1], beam[4]], z=[beam[2], beam[5]],
            mode='lines', line=dict(color=lc, width=4),
            showlegend=False, hoverinfo='skip', opacity=0.5
        ))

    for actor in st.session_state.scene_elements['actors']:
        fig.add_trace(go.Scatter3d(
            x=[actor['x']], y=[actor['y']], z=[0],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='circle'),
            text=[actor['name']], textposition='top center',
            name=actor['name'],
            hovertemplate=f"<b>{actor['name']}</b><br>Pos: ({actor['x']:.1f}, {actor['y']:.1f})<br>{actor['notes']}<extra></extra>"
        ))

    for piece in st.session_state.scene_elements['set_pieces']:
        cm = {'Table': 'brown', 'Chair': 'saddlebrown', 'Sofa': 'tan',
              'Desk': 'sienna', 'Wall': 'gray', 'Door': 'darkgray', 'Window': 'lightblue'}
        fig.add_trace(go.Scatter3d(
            x=[piece['x']], y=[piece['y']], z=[0],
            mode='markers+text',
            marker=dict(size=12, color=cm.get(piece['type'], 'green'), symbol='square'),
            text=[piece['name']], textposition='top center', name=piece['name']
        ))

    for veh in st.session_state.scene_elements['vehicles']:
        fig.add_trace(go.Scatter3d(
            x=[veh['x']], y=[veh['y']], z=[0],
            mode='markers+text',
            marker=dict(size=18, color='darkblue', symbol='square'),
            text=[veh['name']], textposition='top center', name=veh['name']
        ))

    for scr in st.session_state.scene_elements['screens']:
        fig.add_trace(go.Scatter3d(
            x=[scr['x']], y=[scr['y']], z=[scr['z']],
            mode='markers+text',
            marker=dict(size=14, color='black', symbol='square'),
            text=[scr['name']], textposition='top center', name=scr['name']
        ))


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
            aspectmode='cube', camera=camera
        ),
        height=600, margin=dict(l=0, r=0, t=30, b=0),
        title=f"Scene: {st.session_state.scene_name} ({view_mode})"
    )
    return fig


def export_setup_report():
    report = f"""
PRODUCTION SETUP REPORT
=====================================
Scene: {st.session_state.scene_name}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
=====================================
PreViz 4.0 — Open Educational Edition (GPL)
Free for all students worldwide

CAMERAS ({len(st.session_state.scene_elements['cameras'])})
"""
    for i, cam in enumerate(st.session_state.scene_elements['cameras'], 1):
        report += f"\n{i}. {cam['name']}\n   Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f}) ft\n   Rot: {cam['rotation']}°  FL: {cam['focal_length']}mm  FOV: {cam['fov']}°\n"
    report += f"\nLIGHTING ({len(st.session_state.scene_elements['lights'])})\n"
    for i, light in enumerate(st.session_state.scene_elements['lights'], 1):
        report += f"\n{i}. {light['name']} ({light['type']})\n   Pos: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f}) ft  Intensity: {light['intensity']}%\n"
    report += f"\nTALENT ({len(st.session_state.scene_elements['actors'])})\n"
    for i, actor in enumerate(st.session_state.scene_elements['actors'], 1):
        report += f"\n{i}. {actor['name']}\n   Pos: ({actor['x']:.1f}, {actor['y']:.1f}) ft\n   Notes: {actor['notes']}\n"
    return report


def export_scene_json():
    return json.dumps({
        'scene_name': st.session_state.scene_name,
        'created': datetime.now().isoformat(),
        'elements': st.session_state.scene_elements,
        'version': '4.0'
    }, indent=2)


def studio_3d_page():
    with st.sidebar:
        st.header("Scene Setup")
        scene_name = st.text_input("Scene Name", value=st.session_state.scene_name)
        if scene_name != st.session_state.scene_name:
            st.session_state.scene_name = scene_name
        st.divider()

        element_type = st.selectbox(
            "Add Element",
            ["Select...", "Camera", "Light", "Actor", "Set Piece", "Vehicle",
             "Screen/Monitor"]
        )

        if element_type == "Camera":
            st.subheader("📷 Add Camera")
            with st.form("camera_form"):
                cam_name = st.text_input("Camera Name",
                    value=f"Camera {chr(65 + len(st.session_state.scene_elements['cameras']))}")
                c1, c2 = st.columns(2)
                with c1:
                    cam_x = st.number_input("X Position", value=0.0, step=0.5)
                    cam_y = st.number_input("Y Position", value=-5.0, step=0.5)
                with c2:
                    h_preset = st.selectbox("Height Preset", list(CAMERA_HEIGHT_PRESETS.keys()))
                    cam_z = st.number_input("Height (Z)", value=CAMERA_HEIGHT_PRESETS[h_preset], step=0.5, min_value=0.0)
                cam_rotation = st.slider("Rotation", 0, 359, 0)
                focal_preset = st.selectbox("Focal Length Preset", list(FOV_PRESETS.keys()))
                cam_focal = int(focal_preset.split('mm')[0])
                cam_fov = FOV_PRESETS[focal_preset]
                st.caption(f"FOV: {cam_fov}°")
                if st.form_submit_button("Add Camera"):
                    st.session_state.scene_elements['cameras'].append({
                        'name': cam_name, 'x': cam_x, 'y': cam_y, 'z': cam_z,
                        'rotation': cam_rotation, 'focal_length': cam_focal, 'fov': cam_fov
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
                c1, c2 = st.columns(2)
                with c1:
                    light_x = st.number_input("X", value=3.0, step=0.5)
                    light_y = st.number_input("Y", value=0.0, step=0.5)
                    light_z = st.number_input("Z (Height)", value=7.0, step=0.5, min_value=0.0)
                with c2:
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

        elif element_type == "Actor":
            st.subheader("🎭 Add Actor")
            with st.form("actor_form"):
                actor_name = st.text_input("Actor Name",
                    value=f"Actor {len(st.session_state.scene_elements['actors'])+1}")
                c1, c2 = st.columns(2)
                with c1:
                    actor_x = st.number_input("X", value=0.0, step=0.5)
                with c2:
                    actor_y = st.number_input("Y", value=0.0, step=0.5)
                actor_notes = st.text_area("Blocking Notes")
                if st.form_submit_button("Add Actor"):
                    st.session_state.scene_elements['actors'].append({
                        'name': actor_name, 'x': actor_x, 'y': actor_y, 'notes': actor_notes
                    })
                    st.success(f"Added {actor_name}")
                    st.rerun()

        elif element_type == "Set Piece":
            st.subheader("🪑 Add Set Piece")
            with st.form("setpiece_form"):
                piece_name = st.text_input("Name", value="Furniture")
                piece_type = st.selectbox("Type",
                    ["Table", "Chair", "Sofa", "Desk", "Wall", "Door", "Window"])
                c1, c2 = st.columns(2)
                with c1:
                    piece_x = st.number_input("X", value=0.0, step=0.5)
                with c2:
                    piece_y = st.number_input("Y", value=0.0, step=0.5)
                if st.form_submit_button("Add Set Piece"):
                    st.session_state.scene_elements['set_pieces'].append({
                        'name': piece_name, 'type': piece_type, 'x': piece_x, 'y': piece_y
                    })
                    st.success(f"Added {piece_name}")
                    st.rerun()

        elif element_type == "Vehicle":
            st.subheader("🚗 Add Vehicle")
            with st.form("vehicle_form"):
                veh_name = st.text_input("Name", value="Car")
                veh_type = st.selectbox("Type", ["Car", "Van", "Truck", "Motorcycle", "Bicycle"])
                c1, c2 = st.columns(2)
                with c1:
                    veh_x = st.number_input("X", value=0.0, step=0.5)
                    veh_y = st.number_input("Y", value=0.0, step=0.5)
                with c2:
                    veh_rotation = st.slider("Rotation", 0, 359, 0, key="veh_rot")
                if st.form_submit_button("Add Vehicle"):
                    st.session_state.scene_elements['vehicles'].append({
                        'name': veh_name, 'type': veh_type,
                        'x': veh_x, 'y': veh_y, 'rotation': veh_rotation
                    })
                    st.success(f"Added {veh_name}")
                    st.rerun()

        elif element_type == "Screen/Monitor":
            st.subheader("🖥️ Add Screen")
            with st.form("screen_form"):
                scr_name = st.text_input("Name", value="Monitor")
                scr_size = st.selectbox("Size",
                    ['24" Monitor', '32" Monitor', '55" TV', '75" TV', 'Projector Screen'])
                c1, c2 = st.columns(2)
                with c1:
                    scr_x = st.number_input("X", value=0.0, step=0.5)
                    scr_y = st.number_input("Y", value=0.0, step=0.5)
                with c2:
                    scr_z = st.number_input("Height", value=3.0, step=0.5, min_value=0.0)
                if st.form_submit_button("Add Screen"):
                    st.session_state.scene_elements['screens'].append({
                        'name': scr_name, 'size': scr_size,
                        'x': scr_x, 'y': scr_y, 'z': scr_z
                    })
                    st.success(f"Added {scr_name}")
                    st.rerun()

        st.divider()
        st.subheader("📋 Quick Templates")
        if st.button("Three-Point Lighting"):
            st.session_state.scene_elements['lights'] = [
                {'name': 'Key Light', 'type': 'Key Light', 'x': 3, 'y': 3, 'z': 6, 'rotation': 225, 'intensity': 100},
                {'name': 'Fill Light', 'type': 'Fill Light', 'x': -3, 'y': 3, 'z': 5, 'rotation': 135, 'intensity': 50},
                {'name': 'Back Light', 'type': 'Back Light', 'x': 0, 'y': -3, 'z': 7, 'rotation': 0, 'intensity': 70}
            ]
            st.session_state.scene_elements['actors'] = [{'name': 'Subject', 'x': 0, 'y': 0, 'notes': 'Center frame'}]
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Main Camera', 'x': 0, 'y': -8, 'z': 5, 'rotation': 0, 'focal_length': 50, 'fov': 47}
            ]
            st.rerun()

        if st.button("Multi-Camera Interview"):
            st.session_state.scene_elements['cameras'] = [
                {'name': 'Camera A (Wide)', 'x': 0, 'y': -8, 'z': 5, 'rotation': 0, 'focal_length': 35, 'fov': 63},
                {'name': 'Camera B (Close)', 'x': -3, 'y': -7, 'z': 4.5, 'rotation': 15, 'focal_length': 85, 'fov': 29},
                {'name': 'Camera C (OTS)', 'x': 2, 'y': -2, 'z': 4, 'rotation': 180, 'focal_length': 50, 'fov': 47}
            ]
            st.session_state.scene_elements['actors'] = [
                {'name': 'Interviewee', 'x': 0, 'y': 0, 'notes': 'Seated, looking camera left'}
            ]
            st.rerun()

        st.divider()
        if st.button("🗑️ Clear All Elements", type="secondary"):
            st.session_state.scene_elements = {
                'cameras': [], 'lights': [], 'actors': [],
                'set_pieces': [], 'vehicles': [], 'screens': []
            }
            st.rerun()

    col1, col2 = st.columns([3, 1])
    with col1:
        view_mode = st.radio("View Mode", ["Perspective", "Top-Down", "Side View"], horizontal=True)
        st.session_state.view_mode = view_mode
        fig = generate_3d_scene(view_mode)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Scene Summary")
        st.metric("Cameras", len(st.session_state.scene_elements['cameras']))
        st.metric("Lights", len(st.session_state.scene_elements['lights']))
        st.metric("Actors", len(st.session_state.scene_elements['actors']))
        total_el = sum(len(st.session_state.scene_elements[k])
                       for k in ['set_pieces', 'vehicles', 'screens'])
        st.metric("Set Elements", total_el)
        st.divider()
        st.subheader("📤 Export")
        if st.button("📄 Setup Report"):
            report = export_setup_report()
            st.download_button("Download Report", data=report,
                file_name=f"previz_{st.session_state.scene_name.replace(' ', '_')}.txt",
                mime="text/plain")
        if st.button("💾 Save Scene"):
            scene_json = export_scene_json()
            st.download_button("Download Scene", data=scene_json,
                file_name=f"scene_{st.session_state.scene_name.replace(' ', '_')}.json",
                mime="application/json")
        uploaded_file = st.file_uploader("📥 Load Scene", type=['json'])
        if uploaded_file is not None:
            scene_data = json.loads(uploaded_file.read())
            st.session_state.scene_elements = scene_data['elements']
            st.session_state.scene_name = scene_data['scene_name']
            st.success("Scene loaded!")
            st.rerun()

    st.divider()
    st.subheader("Scene Elements")
    tabs = st.tabs(["📷 Cameras", "💡 Lights", "🎭 Actors", "🪑 Set Pieces",
                    "🚗 Vehicles", "🖥️ Screens"])

    with tabs[0]:
        if st.session_state.scene_elements['cameras']:
            for i, cam in enumerate(st.session_state.scene_elements['cameras']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{cam['name']}** | FL: {cam['focal_length']}mm | FOV: {cam['fov']}° | Pos: ({cam['x']:.1f}, {cam['y']:.1f}, {cam['z']:.1f})")
                with c2:
                    if st.button("📋", key=f"copy_cam_{i}"):
                        st.session_state.scene_elements['cameras'].append(duplicate_element('cameras', cam))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_cam_{i}"):
                        st.session_state.scene_elements['cameras'].pop(i)
                        st.rerun()
        else:
            st.info("No cameras. Use sidebar to add.")

    with tabs[1]:
        if st.session_state.scene_elements['lights']:
            for i, light in enumerate(st.session_state.scene_elements['lights']):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{light['name']}** ({light['type']}) | {light['intensity']}% | Pos: ({light['x']:.1f}, {light['y']:.1f}, {light['z']:.1f})")
                with c2:
                    if st.button("📋", key=f"copy_light_{i}"):
                        st.session_state.scene_elements['lights'].append(duplicate_element('lights', light))
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_light_{i}"):
                        st.session_state.scene_elements['lights'].pop(i)
                        st.rerun()
        else:
            st.info("No lights. Use sidebar to add.")

    with tabs[2]:
        if st.session_state.scene_elements['actors']:
            for i, actor in enumerate(st.session_state.scene_elements['actors']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{actor['name']}** | Pos: ({actor['x']:.1f}, {actor['y']:.1f}) | {actor['notes']}")
                with c2:
                    if st.button("🗑️", key=f"del_actor_{i}"):
                        st.session_state.scene_elements['actors'].pop(i)
                        st.rerun()
        else:
            st.info("No actors. Use sidebar to add.")

    with tabs[3]:
        if st.session_state.scene_elements['set_pieces']:
            for i, piece in enumerate(st.session_state.scene_elements['set_pieces']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{piece['name']}** ({piece['type']}) | Pos: ({piece['x']:.1f}, {piece['y']:.1f})")
                with c2:
                    if st.button("🗑️", key=f"del_piece_{i}"):
                        st.session_state.scene_elements['set_pieces'].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces.")

    with tabs[4]:
        if st.session_state.scene_elements['vehicles']:
            for i, veh in enumerate(st.session_state.scene_elements['vehicles']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{veh['name']}** ({veh['type']}) | Rot: {veh['rotation']}°")
                with c2:
                    if st.button("🗑️", key=f"del_veh_{i}"):
                        st.session_state.scene_elements['vehicles'].pop(i)
                        st.rerun()
        else:
            st.info("No vehicles.")

    with tabs[5]:
        if st.session_state.scene_elements['screens']:
            for i, scr in enumerate(st.session_state.scene_elements['screens']):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{scr['name']}** ({scr['size']}) | Pos: ({scr['x']:.1f}, {scr['y']:.1f}, {scr['z']:.1f})")
                with c2:
                    if st.button("🗑️", key=f"del_scr_{i}"):
                        st.session_state.scene_elements['screens'].pop(i)
                        st.rerun()
        else:
            st.info("No screens.")




# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION ENTRY POINT — NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────
def app():
    # Header
    col_title, col_badge, col_nav = st.columns([3, 1, 4])
    with col_title:
        st.markdown('<div class="main-header">🎬 PreViz 4.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Interactive Film Production Planning · Open Educational Edition</div>',
                    unsafe_allow_html=True)
    with col_badge:
        st.markdown('<div class="version-badge">v4.0 GPL</div>', unsafe_allow_html=True)
        st.markdown('<div class="open-badge">🌍 Free for All Students</div>', unsafe_allow_html=True)
    with col_nav:
        st.markdown("#### Navigation")
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("🎯 Preset Set", use_container_width=True,
                          type="primary" if st.session_state.active_page == "Preset Set" else "secondary"):
                st.session_state.active_page = "Preset Set"
                st.rerun()
        with nav_col2:
            if st.button("🏖️ Sandlot", use_container_width=True,
                          type="primary" if st.session_state.active_page == "Sandlot" else "secondary"):
                st.session_state.active_page = "Sandlot"
                st.rerun()
        with nav_col3:
            if st.button("🎬 Studio 3D", use_container_width=True,
                          type="primary" if st.session_state.active_page == "Studio 3D" else "secondary"):
                st.session_state.active_page = "Studio 3D"
                st.rerun()

    st.divider()

    # Route to page
    page = st.session_state.active_page
    if page == "Preset Set":
        preset_page()
    elif page == "Sandlot":
        sandlot_page()
    else:
        studio_3d_page()

    # Footer
    st.divider()
    st.markdown("""
<div style='text-align: center; color: #888; padding: 0.8rem; font-size: 0.8rem;'>
    PreViz 4.0 · Open Educational Edition · GNU GPL v3.0<br>
    Developed by Eduardo Carmona, MFA — CSUDH · LMU<br>
    <i>Free for every student — from Los Angeles to Lima to Windhoek 🌍</i>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    app()
