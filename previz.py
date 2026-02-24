"""
PreViz 4.0 - Professional Studio Floor Plan
Free Educational Technology for Film Students
Developed by: Eduardo Carmona | CSUDH & LMU
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from datetime import datetime
import copy

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PreViz 4.0 - Studio Floor Plan",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size:2rem; font-weight:bold; color:#1a1a1a; }
    .sub-header  { font-size:0.95rem; color:#666; margin-bottom:0.8rem; }
    .badge       { background:#1565C0; color:white; padding:0.25rem 0.7rem;
                   border-radius:10px; font-size:0.8rem; font-weight:bold; }
    .stButton>button { width:100%; }
    .cam-settings { background:#f0f4ff; color:#0a1a3a; border-radius:8px; padding:10px;
                    border-left:4px solid #1565C0; margin-bottom:8px; font-size:0.85rem; line-height:1.7; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
STUDIO_W = 30.0   # feet, X axis
STUDIO_D = 20.0   # feet, Y axis
# Studio: X from -15 to +15, Y from 0 (open 4th wall) to 20 (back wall)

# Default scene
DEFAULT_SCENE = {
    "cameras": [{
        "name": "Camera A",
        "x": 0.0, "y": -1.5,
        "rotation": 0,
        "focal_length": 35, "fov": 63,
        "fps": "24", "shutter": "1/48",
        "resolution": "1080p",
        "iso": 800,
        "nd": "None",
        "fstop": "T2.8"
    }],
    "subject": {"x": 0.0, "y": 10.0, "name": "Subject"},
    "lights": [
        {"name": "Key Light",   "type": "Key Light",   "x": 12.0, "y": 10.0, "rotation": 90, "intensity": 100, "kelvin": 5600},
        {"name": "Fill 1",      "type": "Fill Light",  "x": -13.0, "y": 18.0, "rotation": 135, "intensity": 50,  "kelvin": 5600},
        {"name": "Back Light",  "type": "Back Light",  "x":  0.0,  "y": 19.0, "rotation": 180, "intensity": 70,  "kelvin": 3200},
        {"name": "Fill 2",      "type": "Fill Light",  "x": 13.0,  "y": 18.0, "rotation": 225, "intensity": 50,  "kelvin": 5600},
    ],
    "set_pieces": [],
    "props": []
}

# ── Session State ─────────────────────────────────────────────────────────────
PREVIZ_VERSION = "4.2"
if st.session_state.get("_version") != PREVIZ_VERSION:
    st.session_state.scene = copy.deepcopy(DEFAULT_SCENE)
    st.session_state.scene_name = "Master Shot - Studio"
    st.session_state._version = PREVIZ_VERSION

# ── Presets ───────────────────────────────────────────────────────────────────
LENSES = {
    "16mm  - Ultra Wide  (107 deg)": (16,  107),
    "24mm  - Wide        (84 deg)":  (24,  84),
    "35mm  - Standard    (63 deg)":  (35,  63),
    "50mm  - Normal      (47 deg)":  (50,  47),
    "85mm  - Portrait    (29 deg)":  (85,  29),
    "135mm - Telephoto   (18 deg)":  (135, 18),
    "200mm - Super Tele  (12 deg)":  (200, 12),
}

TSTOPS = ["T1.4", "T2", "T2.8", "T4", "T5.6", "T8", "T11", "T16"]
FSTOPS = ["f/1.4", "f/2", "f/2.8", "f/4", "f/5.6", "f/8", "f/11", "f/16"]
ND_FILTERS = ["None", "ND 0.3 (1 stop)", "ND 0.6 (2 stop)", "ND 0.9 (3 stop)", "ND 1.2 (4 stop)", "ND 1.5 (5 stop)"]
ISO_VALUES = [100, 200, 400, 800, 1600, 3200, 6400]
KELVIN_VALUES = [2700, 3200, 4000, 4500, 5000, 5600, 6500]
FPS_OPTIONS = ["23.976", "24", "25", "29.97", "30", "48", "60"]
SHUTTER_OPTIONS = ["1/24", "1/48", "1/50", "1/60", "1/96", "1/120", "1/250"]
RESOLUTIONS = ["720p", "1080p", "2K", "4K", "6K"]

LIGHT_TYPES = ["Key Light", "Fill Light", "Back Light", "LED Panel", "Practical", "Natural Light"]

KELVIN_COLOR = {
    2700: "#FFB347",
    3200: "#FFC87A",
    4000: "#FFE0A0",
    4500: "#FFF0C0",
    5000: "#FFFDE0",
    5600: "#FFFFFF",
    6500: "#D0E8FF"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def rotate_pt(x, y, deg):
    r = np.radians(deg)
    return x * np.cos(r) - y * np.sin(r), x * np.sin(r) + y * np.cos(r)

def fov_triangle(cx, cy, rot, fov, length=5.0):
    half = fov / 2.0
    w = np.tan(np.radians(half)) * length
    lx, ly = rotate_pt(-w, length, rot)
    rx, ry = rotate_pt( w, length, rot)
    return (cx, cy), (cx + lx, cy + ly), (cx + rx, cy + ry)

def distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def kelvin_to_hex(k):
    options = sorted(KELVIN_COLOR.keys())
    closest = min(options, key=lambda x: abs(x - k))
    return KELVIN_COLOR[closest]

# ── Floor Plan Generator ──────────────────────────────────────────────────────
def generate_floor_plan():
    fig = go.Figure()
    scene = st.session_state.scene
    name = st.session_state.scene_name

    hw = STUDIO_W / 2  # 15 ft half-width
    d  = STUDIO_D      # 20 ft depth

    # ── Layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        plot_bgcolor="#FDFCFB",
        paper_bgcolor="white",
        xaxis=dict(
            range=[-hw - 3, hw + 3],
            showgrid=True, gridcolor="#E5E5E3", gridwidth=0.4,
            zeroline=True, zerolinecolor="#D0D0CE", zerolinewidth=1,
            tickmode="array",
            tickvals=[-15,-10,-5,0,5,10,15],
            ticktext=["-15ft (-4.6m)","-10ft (-3.0m)","-5ft (-1.5m)","0","5ft (1.5m)","10ft (3.0m)","15ft (4.6m)"],
            title=dict(text="Stage Left  ←  Width  →  Stage Right", font=dict(size=10, color="#888")),
            tickfont=dict(size=8, color="#999")
        ),
        yaxis=dict(
            range=[-4, d + 3],
            showgrid=True, gridcolor="#E5E5E3", gridwidth=0.4,
            zeroline=True, zerolinecolor="#D0D0CE", zerolinewidth=1,
            tickmode="array",
            tickvals=[0,5,10,15,20],
            ticktext=["0","5ft (1.5m)","10ft (3.0m)","15ft (4.6m)","20ft (6.1m)"],
            title=dict(text="Depth", font=dict(size=10, color="#888")),
            tickfont=dict(size=8, color="#999"),
            scaleanchor="x",
            scaleratio=1
        ),
        height=720,
        margin=dict(l=60, r=20, t=60, b=60),
        title=dict(
            text=f"PREVIZ 4.0  |  {name}  |  Studio: {int(STUDIO_W)} x {int(STUDIO_D)} ft  /  {STUDIO_W*0.3048:.1f} x {STUDIO_D*0.3048:.1f} m",
            font=dict(size=14, color="#222", family="Arial Black"),
            x=0.01
        ),
        showlegend=True,
        legend=dict(
            x=1.02, y=1, xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#ccc", borderwidth=1,
            font=dict(size=10)
        )
    )

    # ── Studio walls ──────────────────────────────────────────────────────────
    wall_style = dict(type="line", line=dict(color="#222", width=5))

    # Back wall (y = d)
    fig.add_shape(**wall_style, x0=-hw, y0=d, x1=hw, y1=d)
    # Left wall
    fig.add_shape(**wall_style, x0=-hw, y0=0, x1=-hw, y1=d)
    # Right wall
    fig.add_shape(**wall_style, x0=hw, y0=0, x1=hw, y1=d)

    # 4th wall indicator (open wall, dashed)
    fig.add_shape(type="line", x0=-hw, y0=0, x1=hw, y1=0,
                  line=dict(color="#aaa", width=3, dash="dot"))

    # Wall labels
    fig.add_annotation(x=0, y=d + 0.8, text="BACK WALL",
                       showarrow=False, font=dict(size=10, color="#444", family="Arial Black"))
    fig.add_annotation(x=-hw - 1.5, y=d / 2, text="STAGE<br>LEFT",
                       showarrow=False, font=dict(size=9, color="#444"), textangle=-90)
    fig.add_annotation(x=hw + 1.5, y=d / 2, text="STAGE<br>RIGHT",
                       showarrow=False, font=dict(size=9, color="#444"), textangle=90)
    fig.add_annotation(x=0, y=-2.5, text="4th WALL  (OPEN)  - DIRECTOR'S PERSPECTIVE",
                       showarrow=False, font=dict(size=10, color="#888", family="Arial Black"))

    # Dimension labels
    fig.add_annotation(x=0, y=d + 1.8,
                       text=f"<-- {int(STUDIO_W)} ft -->",
                       showarrow=False, font=dict(size=10, color="#666"))
    fig.add_annotation(x=hw + 2.5, y=d / 2,
                       text=f"{int(STUDIO_D)} ft",
                       showarrow=False, font=dict(size=10, color="#666"), textangle=-90)

    # ── Set pieces ────────────────────────────────────────────────────────────
    piece_color = {"Table": "#8B4513", "Chair": "#A0522D", "Sofa": "#D2B48C",
                   "Desk": "#8B4513", "Wall": "#808080", "Door": "#555", "Window": "#87CEEB"}
    for p in scene.get("set_pieces", []):
        c = piece_color.get(p.get("type", "Table"), "#888")
        fig.add_trace(go.Scatter(
            x=[p["x"]], y=[p["y"]], mode="markers+text",
            marker=dict(size=24, color=c, symbol="square", line=dict(color="#333", width=1.5)),
            text=[p.get("type", "")[:3]], textposition="middle center",
            textfont=dict(color="white", size=9, family="Arial Black"),
            name=f"  {p['name']}", showlegend=True,
            hovertemplate=f"<b>{p['name']}</b><br>({p['x']:.1f}, {p['y']:.1f})<extra></extra>"
        ))

    # ── Props ─────────────────────────────────────────────────────────────────
    for p in scene.get("props", []):
        fig.add_trace(go.Scatter(
            x=[p["x"]], y=[p["y"]], mode="markers+text",
            marker=dict(size=14, color="#9C27B0", symbol="diamond",
                        line=dict(color="#6A0080", width=1.5)),
            text=[p["name"]], textposition="top center",
            textfont=dict(size=9, color="#6A0080"),
            name=f"  {p['name']}", showlegend=True,
            hovertemplate=f"<b>{p['name']}</b><br>{p.get('notes','')}<extra></extra>"
        ))

    # ── Lights ────────────────────────────────────────────────────────────────
    for light in scene.get("lights", []):
        kc = kelvin_to_hex(light.get("kelvin", 5600))
        ltype = light.get("type", "Key Light")
        lx, ly = light["x"], light["y"]
        rot = light.get("rotation", 0)
        intensity = light.get("intensity", 100)
        beam_len = 2.5 + intensity / 40.0
        bx, by = rotate_pt(0, beam_len, rot)

        # Beam line
        fig.add_trace(go.Scatter(
            x=[lx, lx + bx], y=[ly, ly + by],
            mode="lines",
            line=dict(color=kc if kc != "#FFFFFF" else "#FFE080", width=3),
            showlegend=False, hoverinfo="skip", opacity=0.7
        ))

        # Key light = half dome shape (dome opens toward direction light is pointing)
        if ltype == "Key Light":
            rot_rad_dome = np.radians(rot)
            theta = np.linspace(rot_rad_dome, np.pi + rot_rad_dome, 40)
            r = 1.4
            hx = lx + r * np.cos(theta)
            hy = ly + r * np.sin(theta)
            fig.add_trace(go.Scatter(
                x=list(hx) + [lx], y=list(hy) + [ly],
                mode="lines",
                fill="toself",
                fillcolor=kc if kc != "#FFFFFF" else "#FFE080",
                line=dict(color="#AA7700", width=2),
                showlegend=False, hoverinfo="skip", opacity=0.85
            ))
            # Key light marker
            fig.add_trace(go.Scatter(
                x=[lx], y=[ly], mode="markers+text",
                marker=dict(size=20, color="#FFD700",
                            symbol="star", line=dict(color="#AA7700", width=2)),
                text=[f"KEY\n{light.get('kelvin',5600)}K\n{intensity}%"],
                textposition="bottom center",
                textfont=dict(size=8, color="#774400"),
                name=f"  KEY LIGHT ({light.get('kelvin',5600)}K)",
                hovertemplate=(
                    f"<b>{light['name']}</b><br>"
                    f"Type: {ltype}<br>"
                    f"Intensity: {intensity}%<br>"
                    f"Color Temp: {light.get('kelvin',5600)}K<extra></extra>"
                )
            ))
        else:
            # Fill / Back lights = circle marker
            fill_color = "#ADD8E6" if ltype == "Back Light" else "#FFFACD"
            fig.add_trace(go.Scatter(
                x=[lx], y=[ly], mode="markers+text",
                marker=dict(size=18, color=fill_color,
                            symbol="circle", line=dict(color="#666", width=1.5)),
                text=[f"{light['name']}\n{light.get('kelvin',5600)}K"],
                textposition="top center",
                textfont=dict(size=8, color="#444"),
                name=f"  {light['name']} ({light.get('kelvin',5600)}K)",
                hovertemplate=(
                    f"<b>{light['name']}</b><br>"
                    f"Type: {ltype}<br>"
                    f"Intensity: {intensity}%<br>"
                    f"Color Temp: {light.get('kelvin',5600)}K<extra></extra>"
                )
            ))

    # ── Subject ───────────────────────────────────────────────────────────────
    subj = scene.get("subject", {"x": 0, "y": 10, "name": "Subject"})
    sx, sy = subj["x"], subj["y"]

    fig.add_trace(go.Scatter(
        x=[sx], y=[sy], mode="markers+text",
        marker=dict(size=26, color="#E53935", symbol="circle",
                    line=dict(color="#B71C1C", width=2.5)),
        text=[subj["name"]], textposition="top center",
        textfont=dict(size=11, color="#B71C1C", family="Arial Black"),
        name=f"  {subj['name']} (Subject)",
        hovertemplate=f"<b>{subj['name']}</b><br>({sx:.1f}, {sy:.1f})<extra></extra>"
    ))

    # ── Camera ────────────────────────────────────────────────────────────────
    for cam in scene.get("cameras", []):
        cx, cy = cam["x"], cam["y"]
        rot = cam.get("rotation", 0)
        fov = cam.get("fov", 63)
        fl  = cam.get("focal_length", 35)

        # FOV cone
        apex, left, right = fov_triangle(cx, cy, rot, fov, length=7.0)
        fig.add_trace(go.Scatter(
            x=[apex[0], left[0], right[0], apex[0]],
            y=[apex[1], left[1], right[1], apex[1]],
            mode="lines", fill="toself",
            fillcolor="rgba(21,101,192,0.13)",
            line=dict(color="#1565C0", width=2.5, dash="dash"),
            showlegend=False, hoverinfo="skip"
        ))

        # Camera body — single clean marker
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy],
            mode="markers+text",
            marker=dict(size=28, color="#1565C0", symbol="square",
                        line=dict(color="#0D47A1", width=3)),
            text=["🎥"],
            textfont=dict(size=18),
            textposition="middle center",
            showlegend=False, hoverinfo="skip"
        ))

        # Camera specs label
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy - 1.8],
            mode="text",
            text=[f"{cam['name']}  {fl}mm | FOV {fov}deg"],
            textfont=dict(size=9, color="#0D47A1", family="Arial Black"),
            textposition="middle center",
            name=f"Camera: {cam['name']} ({fl}mm)",
            hovertemplate=(
                f"<b>{cam['name']}</b><br>"
                f"Lens: {fl}mm | FOV: {fov} deg<br>"
                f"T-Stop: {cam.get('fstop','T2.8')}<br>"
                f"ISO: {cam.get('iso',800)}<br>"
                f"ND: {cam.get('nd','None')}<br>"
                f"{cam.get('fps','24')} fps | {cam.get('shutter','1/48')} | {cam.get('resolution','1080p')}<br>"
                f"({cx:.1f}, {cy:.1f}) ft<extra></extra>"
            )
        ))

        # ── Distance line: camera to subject ──────────────────────────────────
        dist = distance(cx, cy, sx, sy)
        fig.add_trace(go.Scatter(
            x=[cx, sx], y=[cy, sy],
            mode="lines+text",
            line=dict(color="#888", width=1, dash="dot"),
            text=["", f"  {dist:.1f} ft"],
            textposition="middle right",
            textfont=dict(size=9, color="#555"),
            showlegend=False, hoverinfo="skip"
        ))

    # ── Compass / orientation note ────────────────────────────────────────────
    fig.add_annotation(x=-hw + 0.5, y=d - 0.8,
                       text="[Upstage]", showarrow=False,
                       font=dict(size=8, color="#aaa"))
    fig.add_annotation(x=-hw + 0.5, y=0.6,
                       text="[Downstage]", showarrow=False,
                       font=dict(size=8, color="#aaa"))

    return fig


# ── Export ────────────────────────────────────────────────────────────────────
def export_report():
    sc = st.session_state.scene
    nm = st.session_state.scene_name
    lines = [
        "=" * 50,
        "PRODUCTION SETUP REPORT",
        f"Scene:   {nm}",
        f"Studio:  {int(STUDIO_W)} x {int(STUDIO_D)} ft",
        f"Date:    {datetime.now().strftime('%Y-%m-%d  %H:%M')}",
        "=" * 50, ""
    ]

    for cam in sc.get("cameras", []):
        subj = sc.get("subject", {"x": 0, "y": 10})
        dist = distance(cam["x"], cam["y"], subj["x"], subj["y"])
        lines += [
            "CAMERA",
            "-" * 30,
            f"  Name:          {cam['name']}",
            f"  Lens:          {cam['focal_length']}mm",
            f"  FOV:           {cam['fov']} deg",
            f"  T-Stop:        {cam.get('fstop','T2.8')}",
            f"  ISO / Gain:    {cam.get('iso', 800)}",
            f"  ND Filter:     {cam.get('nd','None')}",
            f"  Frame Rate:    {cam.get('fps','24')} fps",
            f"  Shutter:       {cam.get('shutter','1/48')}",
            f"  Resolution:    {cam.get('resolution','1080p')}",
            f"  Position:      ({cam['x']:.1f}, {cam['y']:.1f}) ft",
            f"  Rotation:      {cam.get('rotation',0)} deg",
            f"  Dist to Subj:  {dist:.1f} ft",
            ""
        ]

    lines += ["LIGHTING", "-" * 30]
    for l in sc.get("lights", []):
        lines += [
            f"  {l['name']} ({l['type']})",
            f"    Position:   ({l['x']:.1f}, {l['y']:.1f}) ft",
            f"    Rotation:   {l.get('rotation',0)} deg",
            f"    Intensity:  {l.get('intensity',100)}%",
            f"    Color Temp: {l.get('kelvin',5600)}K",
            ""
        ]

    lines += ["SUBJECT", "-" * 30]
    subj = sc.get("subject", {})
    lines += [
        f"  Name:      {subj.get('name','Subject')}",
        f"  Position:  ({subj.get('x',0):.1f}, {subj.get('y',10):.1f}) ft",
        ""
    ]

    lines += ["EQUIPMENT CHECKLIST", "-" * 30]
    lines.append(f"  [ ] {len(sc.get('cameras',[]))} Camera(s)")
    lines.append(f"  [ ] {len(sc.get('lights',[]))} Light(s)")
    if sc.get("set_pieces"):
        lines.append(f"  [ ] {len(sc['set_pieces'])} Set Piece(s)")
    if sc.get("props"):
        lines.append(f"  [ ] {len(sc['props'])} Prop(s)")

    return "\n".join(lines)


def export_json():
    return json.dumps({
        "scene_name": st.session_state.scene_name,
        "created": datetime.now().isoformat(),
        "studio_w": STUDIO_W,
        "studio_d": STUDIO_D,
        "scene": st.session_state.scene,
        "version": "4.0"
    }, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    scene = st.session_state.scene

    # Header
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown('<div class="main-header">🎬 PreViz 4.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Free Educational Technology for Film Students</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="badge">Studio Floor Plan</div>', unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Scene Setup")

        sname = st.text_input("Scene Name", value=st.session_state.scene_name)
        if sname != st.session_state.scene_name:
            st.session_state.scene_name = sname

        st.divider()

        # ── What to add ───────────────────────────────────────────────────────
        element_type = st.selectbox("Add Element", [
            "-- Select --",
            "🎥  Camera",
            "💡  Light",
            "🧍  Subject / Actor",
            "🪑  Set Piece",
            "🎭  Prop"
        ])

        # ── Camera Form ───────────────────────────────────────────────────────
        if "Camera" in element_type:
            st.subheader("🎥 Camera Settings")
            with st.form("cam_form"):
                cam_name = st.text_input("Camera Name", value="Camera A")

                # Position
                st.markdown("**Position**")
                c1, c2 = st.columns(2)
                with c1:
                    cx = st.number_input("X (ft)", value=0.0, step=0.5,
                                         min_value=-14.0, max_value=14.0)
                with c2:
                    cy = st.number_input("Y (ft)", value=-1.5, step=0.5,
                                         min_value=-3.0, max_value=19.0)
                cam_rot = st.slider("Pan L/R (deg)", -90, 90, 0,
                                    help="0 = straight ahead | neg = left | pos = right")
                cam_tilt = st.slider("Tilt Up/Down (deg)", -45, 45, 0,
                                     help="Negative = tilt down | Positive = tilt up")

                st.markdown("**Optics**")
                lens_key = st.selectbox("Lens", list(LENSES.keys()))
                fl, fov = LENSES[lens_key]
                st.caption(f"Focal length: {fl}mm   FOV: {fov} deg")

                c1, c2 = st.columns(2)
                with c1:
                    fstop = st.selectbox("T-Stop", TSTOPS, index=2)
                with c2:
                    nd = st.selectbox("ND Filter", ND_FILTERS)

                st.markdown("**Recording**")
                c1, c2 = st.columns(2)
                with c1:
                    fps = st.selectbox("Frame Rate", FPS_OPTIONS, index=1)
                    res = st.selectbox("Resolution", RESOLUTIONS, index=1)
                with c2:
                    shutter = st.selectbox("Shutter", SHUTTER_OPTIONS, index=1)
                    iso = st.select_slider("ISO / Gain", options=ISO_VALUES, value=800)

                st.markdown("**Camera Moves**")
                dolly = st.selectbox("Dolly", ["Static", "Dolly In", "Dolly Out (Push)"])

                if st.form_submit_button("✅ Set Camera"):
                    new_cam = {
                        "name": cam_name,
                        "x": cx, "y": cy,
                        "rotation": cam_rot,
                        "tilt": cam_tilt,
                        "focal_length": fl, "fov": fov,
                        "fstop": fstop,
                        "nd": nd,
                        "fps": fps,
                        "shutter": shutter,
                        "resolution": res,
                        "iso": iso,
                        "dolly": dolly
                    }
                    # Replace or add
                    existing = [c for c in scene["cameras"] if c["name"] == cam_name]
                    if existing:
                        idx = next(i for i, c in enumerate(scene["cameras"]) if c["name"] == cam_name)
                        scene["cameras"][idx] = new_cam
                    else:
                        scene["cameras"].append(new_cam)
                    st.success(f"Camera set: {cam_name}")
                    st.rerun()

        # ── Light Form ────────────────────────────────────────────────────────
        elif "Light" in element_type:
            st.subheader("💡 Add / Edit Light")
            with st.form("light_form"):
                # Pick existing or new
                light_names = [l["name"] for l in scene.get("lights", [])]
                light_names_opts = ["-- New Light --"] + light_names
                sel = st.selectbox("Edit existing or add new", light_names_opts)

                # Defaults
                default = next((l for l in scene["lights"] if l["name"] == sel), None)
                lname     = st.text_input("Light Name", value=default["name"] if default else "Light")
                ltype     = st.selectbox("Type", LIGHT_TYPES,
                                         index=LIGHT_TYPES.index(default["type"]) if default else 0)
                c1, c2 = st.columns(2)
                with c1:
                    lx = st.number_input("X (ft)", value=float(default["x"]) if default else 0.0,
                                         step=0.5, min_value=-15.0, max_value=15.0)
                    ly = st.number_input("Y (ft)", value=float(default["y"]) if default else 5.0,
                                         step=0.5, min_value=0.0, max_value=20.0)
                with c2:
                    lrot = st.slider("Rotation", 0, 359,
                                     int(default["rotation"]) if default else 180, key="lrot")
                    lint = st.slider("Intensity %", 0, 100,
                                     int(default["intensity"]) if default else 80, key="lint")

                kelvin = st.select_slider("Color Temp (K)", options=KELVIN_VALUES,
                                          value=int(default["kelvin"]) if default else 5600)
                k_hex = kelvin_to_hex(kelvin)
                st.markdown(
                    f'<div style="background:{k_hex};border:1px solid #ccc;'
                    f'border-radius:4px;padding:4px;text-align:center;font-size:0.8rem;">'
                    f'{kelvin}K</div>', unsafe_allow_html=True
                )

                if st.form_submit_button("✅ Set Light"):
                    new_l = {"name": lname, "type": ltype,
                             "x": lx, "y": ly, "rotation": lrot,
                             "intensity": lint, "kelvin": kelvin}
                    existing = [l for l in scene["lights"] if l["name"] == sel]
                    if existing:
                        idx = next(i for i, l in enumerate(scene["lights"]) if l["name"] == sel)
                        scene["lights"][idx] = new_l
                    else:
                        scene["lights"].append(new_l)
                    st.success(f"Light set: {lname}")
                    st.rerun()

        # ── Subject Form ──────────────────────────────────────────────────────
        elif "Subject" in element_type or "Actor" in element_type:
            st.subheader("🧍 Subject / Actor")
            with st.form("subj_form"):
                sname = st.text_input("Name", value=scene["subject"].get("name", "Subject"))
                c1, c2 = st.columns(2)
                with c1:
                    sx = st.number_input("X (ft)", value=float(scene["subject"]["x"]),
                                         step=0.5, min_value=-14.0, max_value=14.0)
                with c2:
                    sy = st.number_input("Y (ft)", value=float(scene["subject"]["y"]),
                                         step=0.5, min_value=0.5, max_value=19.0)
                if st.form_submit_button("✅ Place Subject"):
                    scene["subject"] = {"name": sname, "x": sx, "y": sy}
                    st.success(f"Subject placed at ({sx}, {sy}) ft")
                    st.rerun()

        # ── Set Piece Form ────────────────────────────────────────────────────
        elif "Set Piece" in element_type:
            st.subheader("🪑 Add Set Piece")
            with st.form("piece_form"):
                pname = st.text_input("Name", value="Chair")
                ptype = st.selectbox("Type", ["Table", "Chair", "Sofa", "Desk", "Wall", "Door", "Window"])
                c1, c2 = st.columns(2)
                with c1:
                    px = st.number_input("X (ft)", value=0.0, step=0.5)
                with c2:
                    py = st.number_input("Y (ft)", value=5.0, step=0.5)
                if st.form_submit_button("✅ Add Set Piece"):
                    if "set_pieces" not in scene:
                        scene["set_pieces"] = []
                    scene["set_pieces"].append({"name": pname, "type": ptype, "x": px, "y": py})
                    st.success(f"Added {pname}")
                    st.rerun()

        # ── Prop Form ─────────────────────────────────────────────────────────
        elif "Prop" in element_type:
            st.subheader("🎭 Add Prop")
            with st.form("prop_form"):
                prname = st.text_input("Prop Name", value="Prop")
                prtype = st.selectbox("Category",
                    ["Weapon", "Phone", "Bag", "Food / Drink", "Book", "Electronics", "Tool", "Other"])
                c1, c2 = st.columns(2)
                with c1:
                    prx = st.number_input("X (ft)", value=0.0, step=0.5)
                with c2:
                    pry = st.number_input("Y (ft)", value=5.0, step=0.5)
                prnotes = st.text_input("Notes", placeholder="Hero prop, breakaway...")
                if st.form_submit_button("✅ Add Prop"):
                    if "props" not in scene:
                        scene["props"] = []
                    scene["props"].append({"name": prname, "type": prtype,
                                           "x": prx, "y": pry, "notes": prnotes})
                    st.success(f"Added {prname}")
                    st.rerun()

        st.divider()

        # ── Quick Templates ───────────────────────────────────────────────────
        st.subheader("Quick Templates")

        if st.button("Master Shot (Standard)"):
            st.session_state.scene = copy.deepcopy(DEFAULT_SCENE)
            st.rerun()

        if st.button("Two-Person Interview"):
            st.session_state.scene = {
                "cameras": [
                    {"name": "Camera A (Wide)", "x": 0.0, "y": -1.5, "rotation": 0,
                     "focal_length": 35, "fov": 63, "fps": "24", "shutter": "1/48",
                     "resolution": "1080p", "iso": 800, "nd": "None", "fstop": "T2.8"},
                    {"name": "Camera B (Close)", "x": -3.0, "y": -1.0, "rotation": 10,
                     "focal_length": 85, "fov": 29, "fps": "24", "shutter": "1/48",
                     "resolution": "1080p", "iso": 800, "nd": "None", "fstop": "T2.8"}
                ],
                "subject": {"x": -2.0, "y": 8.0, "name": "Person A"},
                "lights": [
                    {"name": "Key Light",  "type": "Key Light",  "x": 10.0, "y":  8.0, "rotation": 210, "intensity": 100, "kelvin": 5600},
                    {"name": "Fill 1",     "type": "Fill Light", "x": -12.0,"y": 17.0, "rotation": 135, "intensity": 50,  "kelvin": 5600},
                    {"name": "Back Light", "type": "Back Light", "x":  0.0, "y": 18.0, "rotation": 180, "intensity": 60,  "kelvin": 3200},
                    {"name": "Fill 2",     "type": "Fill Light", "x": 12.0, "y": 17.0, "rotation": 225, "intensity": 50,  "kelvin": 5600},
                ],
                "set_pieces": [{"name": "Chair A", "type": "Chair", "x": -2.0, "y": 8.0},
                               {"name": "Chair B", "type": "Chair", "x":  2.0, "y": 8.0}],
                "props": []
            }
            st.rerun()

        if st.button("Green Screen Setup"):
            st.session_state.scene = {
                "cameras": [{"name": "Camera A", "x": 0.0, "y": -1.5, "rotation": 0,
                              "focal_length": 50, "fov": 47, "fps": "24", "shutter": "1/48",
                              "resolution": "1080p", "iso": 800, "nd": "None", "fstop": "T4"}],
                "subject": {"x": 0.0, "y": 7.0, "name": "Subject"},
                "lights": [
                    {"name": "Key Light",          "type": "Key Light",  "x": 10.0, "y":  5.0, "rotation": 200, "intensity": 100, "kelvin": 5600},
                    {"name": "Fill",               "type": "Fill Light", "x": -8.0, "y":  5.0, "rotation": 160, "intensity": 60,  "kelvin": 5600},
                    {"name": "Green Screen L",     "type": "LED Panel",  "x": -8.0, "y": 17.0, "rotation": 180, "intensity": 80,  "kelvin": 5600},
                    {"name": "Green Screen R",     "type": "LED Panel",  "x":  8.0, "y": 17.0, "rotation": 180, "intensity": 80,  "kelvin": 5600},
                ],
                "set_pieces": [],
                "props": []
            }
            st.rerun()

        st.divider()

        if st.button("🗑️ Reset to Default", type="secondary"):
            st.session_state.scene = copy.deepcopy(DEFAULT_SCENE)
            st.session_state.scene_name = "Master Shot - Studio"
            st.rerun()

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    col_plan, col_info = st.columns([3, 1])

    with col_plan:
        fig = generate_floor_plan()
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.subheader("Scene Summary")
        subj = scene.get("subject", {})

        # Camera specs display
        for cam in scene.get("cameras", []):
            dist = distance(cam["x"], cam["y"],
                            subj.get("x", 0), subj.get("y", 10))
            st.markdown(f"""
<div class="cam-settings">
<b>{cam['name']}</b><br>
Lens: <b>{cam['focal_length']}mm</b>  FOV: {cam['fov']} deg<br>
T-Stop: <b>{cam.get('fstop','T2.8')}</b>  ISO: <b>{cam.get('iso',800)}</b><br>
ND: {cam.get('nd','None')}<br>
{cam.get('fps','24')} fps  |  {cam.get('shutter','1/48')}  |  {cam.get('resolution','1080p')}<br>
<b>Dist to subject: {dist:.1f} ft</b>
</div>
""", unsafe_allow_html=True)

        st.divider()

        st.markdown("**Lights**")
        for l in scene.get("lights", []):
            st.caption(f"{l['name']}: {l.get('intensity',100)}%  |  {l.get('kelvin',5600)}K")

        st.divider()

        # Export
        st.subheader("Export / Save")

        if st.button("📄 Setup Report"):
            rpt = export_report()
            st.download_button("Download Report (.txt)", data=rpt,
                file_name=f"previz_{st.session_state.scene_name.replace(' ','_')}.txt",
                mime="text/plain")

        if st.button("💾 Save Scene"):
            st.download_button("Download Scene (.json)", data=export_json(),
                file_name=f"scene_{st.session_state.scene_name.replace(' ','_')}.json",
                mime="application/json")

        st.divider()
        uploaded = st.file_uploader("Load Scene (.json)", type=["json"])
        if uploaded:
            data = json.loads(uploaded.read())
            st.session_state.scene = data.get("scene", data.get("elements", {}))
            st.session_state.scene_name = data.get("scene_name", "Loaded Scene")
            st.success("Scene loaded!")
            st.rerun()

    # ── ELEMENT TABS ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Scene Elements")

    tabs = st.tabs(["🎥 Cameras", "💡 Lights", "🧍 Subject", "🪑 Set Pieces", "🎭 Props"])

    # ── Cameras tab ───────────────────────────────────────────────────────────
    with tabs[0]:
        if scene.get("cameras"):
            for i, cam in enumerate(scene["cameras"]):
                subj = scene.get("subject", {"x": 0, "y": 10})
                dist = distance(cam["x"], cam["y"], subj["x"], subj["y"])
                dist_m = dist * 0.3048
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
<div style="background:#EFF4FF;border-left:5px solid #1565C0;border-radius:6px;
padding:12px 16px;margin-bottom:8px;font-size:0.9rem;line-height:1.9;">
<span style="font-size:1.3rem;">📷</span>&nbsp;&nbsp;
<b style="font-size:1.05rem;color:#0D47A1;">{cam['name']}</b>
<span style="background:#1565C0;color:white;border-radius:4px;
padding:2px 8px;font-size:0.75rem;margin-left:8px;">{cam['focal_length']}mm</span>
<span style="background:#37474F;color:white;border-radius:4px;
padding:2px 8px;font-size:0.75rem;margin-left:4px;">FOV {cam['fov']}&deg;</span>
<br>
<span style="color:#555;">
&nbsp;&nbsp;&nbsp;&nbsp;
🔍 <b>{cam.get('fstop','T2.8')}</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
🎞 ISO <b>{cam.get('iso',800)}</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
🌫 ND: <b>{cam.get('nd','None')}</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
🎬 <b>{cam.get('fps','24')} fps</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
⏱ <b>{cam.get('shutter','1/48')}</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
📺 <b>{cam.get('resolution','1080p')}</b>
<br>&nbsp;&nbsp;&nbsp;&nbsp;
📍 Position: ({cam['x']:.1f}, {cam['y']:.1f}) ft
&nbsp;&nbsp;|&nbsp;&nbsp;
📐 Dist to subject: <b>{dist:.1f} ft / {dist_m:.1f} m</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
🔄 Pan: {cam.get('rotation',0)}&deg;
&nbsp;&nbsp;|&nbsp;&nbsp;
↕ Tilt: {cam.get('tilt',0)}&deg;
</span>
</div>
""", unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"del_cam_{i}", help="Remove camera"):
                        scene["cameras"].pop(i)
                        st.rerun()
        else:
            st.info("No cameras yet. Use the sidebar to add one.")

    # ── Lights tab ────────────────────────────────────────────────────────────
    with tabs[1]:
        LIGHT_ICON = {"Key Light":"☀️","Fill Light":"💡","Back Light":"🔦","LED Panel":"🟦","Practical":"🕯️","Natural Light":"🌤️"}
        LIGHT_COLOR = {"Key Light":"#FFF8E1","Fill Light":"#F9FBE7","Back Light":"#E3F2FD","LED Panel":"#E8EAF6","Practical":"#FFF3E0","Natural Light":"#E0F7FA"}
        LIGHT_BORDER = {"Key Light":"#F9A825","Fill Light":"#9CCC65","Back Light":"#42A5F5","LED Panel":"#5C6BC0","Practical":"#FF7043","Natural Light":"#26C6DA"}
        if scene.get("lights"):
            for i, l in enumerate(scene["lights"]):
                ltype = l.get("type","Key Light")
                icon  = LIGHT_ICON.get(ltype,"💡")
                bg    = LIGHT_COLOR.get(ltype,"#FFF8E1")
                bdr   = LIGHT_BORDER.get(ltype,"#F9A825")
                k     = l.get("kelvin",5600)
                intensity = l.get("intensity",100)
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
<div style="background:{bg};border-left:5px solid {bdr};border-radius:6px;
padding:12px 16px;margin-bottom:8px;font-size:0.9rem;line-height:1.9;">
<span style="font-size:1.3rem;">{icon}</span>&nbsp;&nbsp;
<b style="font-size:1.05rem;">{l['name']}</b>
<span style="background:{bdr};color:white;border-radius:4px;
padding:2px 8px;font-size:0.75rem;margin-left:8px;">{ltype}</span>
<br>
<span style="color:#555;">
&nbsp;&nbsp;&nbsp;&nbsp;
🌡 Color Temp: <b>{k}K</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
💪 Intensity: <b>{intensity}%</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
📍 Pos: ({l['x']:.1f}, {l['y']:.1f}) ft
&nbsp;&nbsp;|&nbsp;&nbsp;
🔄 Rot: {l.get('rotation',0)}&deg;
</span>
</div>
""", unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"del_light_{i}", help="Remove light"):
                        scene["lights"].pop(i)
                        st.rerun()
        else:
            st.info("No lights yet. Use the sidebar to add one.")

    # ── Subject tab ───────────────────────────────────────────────────────────
    with tabs[2]:
        subj = scene.get("subject", {})
        sx, sy = subj.get("x",0), subj.get("y",10)
        cam_list = scene.get("cameras",[])
        st.markdown(f"""
<div style="background:#FFEBEE;border-left:5px solid #E53935;border-radius:6px;
padding:12px 16px;margin-bottom:8px;font-size:0.9rem;line-height:1.9;">
<span style="font-size:1.3rem;">🧍</span>&nbsp;&nbsp;
<b style="font-size:1.05rem;color:#B71C1C;">{subj.get('name','Subject')}</b>
<br>
<span style="color:#555;">
&nbsp;&nbsp;&nbsp;&nbsp;
📍 Position: <b>({sx:.1f}, {sy:.1f}) ft</b>
&nbsp;&nbsp;|&nbsp;&nbsp;
🌍 <b>({sx*0.3048:.2f}, {sy*0.3048:.2f}) m</b>
</span>
</div>
""", unsafe_allow_html=True)
        for cam in cam_list:
            d_ft = distance(cam["x"], cam["y"], sx, sy)
            d_m  = d_ft * 0.3048
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;📷 Distance from **{cam['name']}**: **{d_ft:.1f} ft / {d_m:.1f} m**")

    # ── Set Pieces tab ────────────────────────────────────────────────────────
    with tabs[3]:
        PIECE_ICON = {"Table":"🪵","Chair":"🪑","Sofa":"🛋️","Desk":"🖥️","Wall":"🧱","Door":"🚪","Window":"🪟"}
        if scene.get("set_pieces"):
            for i, p in enumerate(scene["set_pieces"]):
                icon = PIECE_ICON.get(p.get("type","Table"),"🪑")
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
<div style="background:#F1F8E9;border-left:5px solid #7CB342;border-radius:6px;
padding:10px 16px;margin-bottom:6px;font-size:0.9rem;line-height:1.8;">
<span style="font-size:1.2rem;">{icon}</span>&nbsp;&nbsp;
<b>{p['name']}</b>
<span style="background:#7CB342;color:white;border-radius:4px;
padding:2px 7px;font-size:0.75rem;margin-left:8px;">{p.get('type','')}</span>
&nbsp;&nbsp;
<span style="color:#555;">📍 ({p['x']:.1f}, {p['y']:.1f}) ft &nbsp;/&nbsp; ({p['x']*0.3048:.2f}, {p['y']*0.3048:.2f}) m</span>
</div>
""", unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"del_piece_{i}"):
                        scene["set_pieces"].pop(i)
                        st.rerun()
        else:
            st.info("No set pieces yet. Use the sidebar to add one.")

    # ── Props tab ─────────────────────────────────────────────────────────────
    with tabs[4]:
        PROP_ICON = {"Weapon":"🔫","Phone":"📱","Bag":"👜","Food / Drink":"🍽️","Book":"📖","Electronics":"💻","Tool":"🔧","Other":"🎭"}
        if scene.get("props"):
            for i, p in enumerate(scene["props"]):
                icon = PROP_ICON.get(p.get("type","Other"),"🎭")
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
<div style="background:#F3E5F5;border-left:5px solid #8E24AA;border-radius:6px;
padding:10px 16px;margin-bottom:6px;font-size:0.9rem;line-height:1.8;">
<span style="font-size:1.2rem;">{icon}</span>&nbsp;&nbsp;
<b>{p['name']}</b>
<span style="background:#8E24AA;color:white;border-radius:4px;
padding:2px 7px;font-size:0.75rem;margin-left:8px;">{p.get('type','Prop')}</span>
<br>
<span style="color:#555;">
&nbsp;&nbsp;&nbsp;&nbsp;📍 ({p['x']:.1f}, {p['y']:.1f}) ft
{f" &nbsp;|&nbsp; 📝 {p.get('notes','')}" if p.get('notes') else ""}
</span>
</div>
""", unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"del_prop_{i}"):
                        scene["props"].pop(i)
                        st.rerun()
        else:
            st.info("No props yet. Use the sidebar to add one.")

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align:center; color:#aaa; font-size:0.8rem; padding:0.5rem;'>
        PreViz v4.0 &nbsp;|&nbsp; Free Educational Technology for Film Students
        &nbsp;|&nbsp; Developed by Eduardo Carmona &nbsp;|&nbsp; CSUDH &amp; LMU
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
