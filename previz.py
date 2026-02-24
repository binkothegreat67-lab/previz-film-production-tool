"""
PreViz 4.0 — Open Educational Edition
Developed by Eduardo Carmona, MFA — CSUDH · LMU
GNU General Public License v3.0
Free for every student — from Los Angeles to Lima to Windhoek.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
PREVIZ_VERSION = "4.0"
STAGE_W = 30   # feet wide
STAGE_H = 20   # feet deep

LENS_OPTIONS = ["12mm", "16mm", "24mm", "35mm", "50mm", "85mm", "100mm", "135mm"]
LENS_FOV = {
    "12mm": 90, "16mm": 83, "24mm": 73, "35mm": 54,
    "50mm": 39, "85mm": 24, "100mm": 20, "135mm": 15
}

ISO_OPTIONS = [100, 200, 400, 800, 1600, 3200, 6400]
RESOLUTION_OPTIONS = ["720p", "1080p", "4K UHD", "4K DCI"]
FPS_OPTIONS = [24, 25, 30, 60]
SHUTTER_BY_FPS = {24: "1/48", 25: "1/50", 30: "1/60", 60: "1/120"}
SHUTTER_DENOM  = {"1/48": 48, "1/50": 50, "1/60": 60, "1/120": 120}

ND_OPTIONS = {
    "None (0 stops)": 0,
    "ND 0.3 — 1 stop":  1,
    "ND 0.6 — 2 stops": 2,
    "ND 0.9 — 3 stops": 3,
    "ND 1.2 — 4 stops": 4,
    "ND 1.8 — 6 stops": 6,
    "ND 2.4 — 8 stops": 8,
    "ND 3.0 — 10 stops": 10,
}

FSTOPS = [1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11, 16, 22]

# (max_kelvin, hex_color, display_name)
KELVIN_SCALE = [
    (2000,  "#FF5500", "Candlelight"),
    (2700,  "#FF8040", "Incandescent"),
    (3200,  "#FFB347", "Tungsten"),
    (4000,  "#FFD580", "Warm White"),
    (4300,  "#FFE8C0", "Late Afternoon"),
    (5600,  "#FFF3DC", "Daylight"),
    (6500,  "#EEF5FF", "Overcast Sky"),
    (7500,  "#D5E8FF", "Cloudy"),
    (10000, "#B8D5FF", "Blue Sky"),
]

# (ratio_upper_bound, label, badge_color, mood)
RATIO_TABLE = [
    (1.2,  "1:1",  "#4A90D9", "Flat, even — broadcast / news"),
    (1.7,  "2:1",  "#4A90D9", "Soft, commercial look"),
    (2.5,  "3:1",  "#27AE60", "Classic cinematic"),
    (3.5,  "4:1",  "#27AE60", "Dramatic portrait"),
    (5.0,  "6:1",  "#E67E22", "High contrast"),
    (10.0, "8:1",  "#E67E22", "Near noir"),
    (999,  "16:1", "#C0392B", "High contrast noir"),
]

# ─────────────────────────────────────────────────────────────────
# TIPS DICTIONARY  (swap this dict for multilingual support)
# ─────────────────────────────────────────────────────────────────
TIPS = {
    "Key Light":     "The main light source. It establishes exposure and the direction of primary shadows. Everything else is relative to it.",
    "Fill Light":    "Fills in the shadows from the Key. Always softer and dimmer than the Key. Controls how deep the shadows are.",
    "Back Light":    "Positioned behind and above the subject. Creates a rim that separates them from the background. Also called a hair light.",
    "Kelvin":        "Color temperature of light. Low values (2000K) are warm orange. High values (10000K) are cool blue. Daylight is 5600K.",
    "f-stop":        "The aperture setting. Lower number (f/1.4) = wide open = more light. Higher number (f/16) = closed down = less light.",
    "ISO":           "Sensor sensitivity. ISO 100 = base, least noise. ISO 6400 = very sensitive, more noise. Higher ISO brightens the image.",
    "Shutter Speed": "How long each frame is exposed. The 180° rule: set shutter to 2× your frame rate. At 24fps, use 1/48s for natural motion blur.",
    "ND Filter":     "Neutral Density filter — sunglasses for the lens. Reduces light without changing color. Lets you shoot wide open outdoors.",
    "Pan":           "Rotating the camera left or right on its vertical axis without moving it. Measured in degrees from center.",
    "Tilt":          "Rotating the camera up or down on its horizontal axis. Five positions from low to high.",
    "Dolly":         "Physically moving the camera toward or away from the subject. Changes perspective, not just framing.",
    "FOV":           "Field of View. The angle the lens captures. Wide lens (12mm) = 90° FOV. Telephoto (135mm) = only 15° FOV.",
    "Light Ratio":   "The brightness relationship between Key and Fill lights. 3:1 is classic Hollywood. 8:1+ creates noir and drama.",
    "Master Shot":   "A wide establishing shot that captures all the action in a scene. Usually set up first so everything else is covered relative to it.",
    "Fourth Wall":   "The imaginary wall between the actors and the camera. Leaving it open means the camera lives outside the scene.",
    "Approval Gate": "All three department heads (DP, Gaffer, Director) must sign off before a floor plan becomes an official production document.",
}

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def kelvin_to_display(k):
    """Return (hex_color, name) for a Kelvin value."""
    for max_k, color, name in KELVIN_SCALE:
        if k <= max_k:
            return color, name
    return KELVIN_SCALE[-1][1], KELVIN_SCALE[-1][2]

def calculate_fstop(key_intensity, iso, shutter_str, nd_stops):
    """
    Calculate suggested f-stop from exposure parameters.
    Baseline: key=100%, ISO=800, 1/48s, ND=0 → f/5.6
    Key Light drives exposure (pedagogical principle).
    """
    if key_intensity <= 0:
        return "---"
    denom = SHUTTER_DENOM.get(shutter_str, 48)
    base_idx = 5  # f/5.6
    key_adj     =  math.log2(max(key_intensity, 0.1) / 100)  # brighter key → close down
    iso_adj     =  math.log2(iso / 800)                       # higher ISO  → close down
    shutter_adj =  math.log2(48 / denom)                      # faster shutter → open up
    nd_adj      = -nd_stops                                    # more ND → open up
    total = key_adj + iso_adj + shutter_adj + nd_adj
    idx = max(0, min(len(FSTOPS) - 1, round(base_idx + total)))
    return f"f/{FSTOPS[int(idx)]}"

def calculate_ratio(key_int, fill_int):
    """Return (label, badge_color, mood) for Key:Fill ratio."""
    if fill_int <= 0:
        return "∞:1", "#C0392B", "No fill — maximum contrast"
    ratio = key_int / max(fill_int, 0.1)
    for upper, label, color, mood in RATIO_TABLE:
        if ratio < upper:
            return label, color, mood
    return "16:1", "#C0392B", "High contrast noir"

def dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def ft_m(ft):
    return round(ft * 0.3048, 1)

def rot2d(vx, vy, theta):
    """Rotate vector (vx, vy) by theta radians."""
    return (vx * math.cos(theta) - vy * math.sin(theta),
            vx * math.sin(theta) + vy * math.cos(theta))

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        # Camera
        "lens":         "24mm",
        "cam_pan":      0,
        "cam_dolly":    3.0,
        "fps":          24,
        # Video specs
        "resolution":   "1080p",
        "iso":          800,
        "nd_label":     "None (0 stops)",
        # Key Light
        "key_intensity": 80,
        "key_kelvin":    5600,
        "key_x":         5.0,  # stage left, ft from Wall 1
        # Fill #1 (upper left corner)
        "fill1_on":        True,
        "fill1_intensity": 40,
        "fill1_kelvin":    5600,
        # Back Light (center of Wall 2)
        "back_on":        True,
        "back_intensity": 60,
        "back_kelvin":    5600,
        # Fill #2 (upper right corner)
        "fill2_on":        True,
        "fill2_intensity": 40,
        "fill2_kelvin":    5600,
        # Talent
        "talent_name": "Actor",
        "talent_x":    15.0,
        "talent_y":    10.0,
        # Approval
        "approved_dp":      False,
        "approved_gaffer":  False,
        "approved_director": False,
        "approved_at":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────
# FLOOR PLAN
# ─────────────────────────────────────────────────────────────────

def draw_floor_plan():
    s  = st.session_state
    W, H = STAGE_W, STAGE_H

    # Derived values
    fov         = LENS_FOV[s.lens]
    shutter_str = SHUTTER_BY_FPS[s.fps]
    nd_stops    = ND_OPTIONS[s.nd_label]
    fstop       = calculate_fstop(s.key_intensity, s.iso, shutter_str, nd_stops)
    cam_x       = W / 2
    cam_y       = s.cam_dolly
    key_x       = s.key_x
    key_y       = s.talent_y          # key light tracks talent depth
    tx, ty      = s.talent_x, s.talent_y
    key_color, key_kname  = kelvin_to_display(s.key_kelvin)
    ratio_label, ratio_color, ratio_mood = calculate_ratio(
        s.key_intensity,
        s.fill1_intensity if s.fill1_on else 0
    )
    cam_to_talent = dist(cam_x, cam_y, tx, ty)
    key_to_talent = dist(key_x, key_y, tx, ty)

    fig = go.Figure()

    # ── STAGE FLOOR ───────────────────────────────────────────
    fig.add_shape(type="rect", x0=0, y0=0, x1=W, y1=H,
                  fillcolor="#FAF8F4",
                  line=dict(color="#8B7355", width=4))

    # Grid every 5 ft
    for x in range(5, W, 5):
        fig.add_shape(type="line", x0=x, y0=0, x1=x, y1=H,
                      line=dict(color="#E0D8C8", width=1))
    for y in range(5, H, 5):
        fig.add_shape(type="line", x0=0, y0=y, x1=W, y1=y,
                      line=dict(color="#E0D8C8", width=1))

    # Wall 4 — open (camera side, bottom) — dashed
    fig.add_shape(type="line", x0=0, y0=0, x1=W, y1=0,
                  line=dict(color="#888", width=2.5, dash="dot"))

    # Wall labels
    for ann in [
        dict(x=-1.8, y=H/2, text="WALL 1", textangle=-90,
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W/2, y=H+1.5, text="WALL 2 — BACK",
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W+1.8, y=H/2, text="WALL 3", textangle=90,
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W/2, y=-1.3, text="4TH WALL — OPEN (CAMERA)",
             showarrow=False, font=dict(size=9, color="#999")),
    ]:
        fig.add_annotation(**ann)

    # Stage dimensions
    fig.add_annotation(x=W/2, y=H+0.7, text="30 ft  |  9.1 m",
                       showarrow=False, font=dict(size=8, color="#AAA"))
    fig.add_annotation(x=-0.6, y=H/2, text="20 ft | 6.1 m",
                       showarrow=False, font=dict(size=8, color="#AAA"), textangle=-90)

    # ── OVERHEAD LIGHTS ───────────────────────────────────────
    overhead = [
        (4,      16, "fill1_on", "fill1_intensity", "fill1_kelvin", "Fill #1"),
        (W / 2,  18, "back_on",  "back_intensity",  "back_kelvin",  "Back"),
        (W - 4,  16, "fill2_on", "fill2_intensity", "fill2_kelvin", "Fill #2"),
    ]
    for lx, ly, key_on, key_int, key_k, label in overhead:
        is_on   = getattr(s, key_on)
        lkelvin = getattr(s, key_k)
        lintens = getattr(s, key_int)
        lcolor, lkname = kelvin_to_display(lkelvin)

        # Glow if on
        if is_on:
            fig.add_shape(type="circle",
                          x0=lx - 1.0, y0=ly - 1.0,
                          x1=lx + 1.0, y1=ly + 1.0,
                          fillcolor=lcolor + "55",
                          line=dict(color=lcolor, width=2))

        fig.add_trace(go.Scatter(
            x=[lx], y=[ly],
            mode="markers+text",
            marker=dict(
                size=16,
                color=lcolor if is_on else "#BBBBBB",
                symbol="square",
                line=dict(color="#333", width=2)
            ),
            text=[f"💡"],
            textposition="middle center",
            showlegend=False,
            hovertemplate=(
                f"<b>{label}</b><br>"
                f"{'ON' if is_on else 'OFF'}<br>"
                f"{lkelvin}K — {lkname}<br>"
                f"Intensity: {lintens}%<extra></extra>"
            )
        ))
        fig.add_annotation(
            x=lx, y=ly + 1.5,
            text=f"{label}<br>{lkelvin}K",
            showarrow=False,
            font=dict(size=8, color="#555"),
            align="center"
        )

    # ── KEY LIGHT ─────────────────────────────────────────────
    # Beam line: key → talent
    fig.add_trace(go.Scatter(
        x=[key_x, tx], y=[key_y, ty],
        mode="lines",
        line=dict(color=key_color, width=3),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Half-dome (semicircle) facing talent
    angle_to_talent = math.atan2(ty - key_y, tx - key_x)
    dome_r   = 1.4
    n_pts    = 30
    arc_a    = np.linspace(angle_to_talent - math.pi / 2,
                           angle_to_talent + math.pi / 2, n_pts)
    dome_xs  = [key_x + dome_r * math.cos(a) for a in arc_a]
    dome_ys  = [key_y + dome_r * math.sin(a) for a in arc_a]

    fig.add_trace(go.Scatter(
        x=dome_xs, y=dome_ys,
        mode="lines",
        fill="toself",
        fillcolor=key_color + "CC",
        line=dict(color=key_color, width=3),
        showlegend=False,
        hovertemplate=(
            f"<b>🔆 Key Light</b><br>"
            f"{s.key_kelvin}K — {key_kname}<br>"
            f"Intensity: {s.key_intensity}%<extra></extra>"
        )
    ))

    fig.add_annotation(
        x=key_x - 0.4, y=key_y + dome_r + 1.2,
        text=f"🔆 KEY<br>{s.key_kelvin}K",
        showarrow=False,
        font=dict(size=9, color="#333"),
        align="center"
    )

    # ── CAMERA ────────────────────────────────────────────────
    pan_rad      = math.radians(s.cam_pan)
    fov_half_rad = math.radians(fov / 2)
    fwd          = (math.sin(pan_rad), math.cos(pan_rad))  # faces +y at pan=0
    cone_len     = min(15.0, H - cam_y + 0.5)

    left_dir  = rot2d(fwd[0], fwd[1],  fov_half_rad)
    right_dir = rot2d(fwd[0], fwd[1], -fov_half_rad)

    fov_lx = cam_x + left_dir[0]  * cone_len
    fov_ly = cam_y + left_dir[1]  * cone_len
    fov_rx = cam_x + right_dir[0] * cone_len
    fov_ry = cam_y + right_dir[1] * cone_len

    # FOV cone (filled)
    fig.add_trace(go.Scatter(
        x=[cam_x, fov_lx, fov_rx, cam_x],
        y=[cam_y, fov_ly, fov_ry, cam_y],
        fill="toself",
        fillcolor="rgba(60, 90, 200, 0.10)",
        line=dict(color="rgba(60, 90, 200, 0.45)", width=1.5),
        mode="lines",
        showlegend=False,
        hoverinfo="skip"
    ))

    # Camera body
    fig.add_trace(go.Scatter(
        x=[cam_x], y=[cam_y],
        mode="markers+text",
        marker=dict(
            size=22, color="#1E3A8A", symbol="square",
            line=dict(color="white", width=2)
        ),
        text=["📷"],
        textposition="middle center",
        showlegend=False,
        hovertemplate=(
            f"<b>📷 Camera — Master Shot</b><br>"
            f"{s.lens} | FOV: {fov}°<br>"
            f"Pan: {s.cam_pan}°<br>"
            f"Dolly: {s.cam_dolly} ft from Wall 4<extra></extra>"
        )
    ))

    fig.add_annotation(
        x=cam_x + 2.0, y=cam_y + 0.3,
        text=f"📷 {s.lens} | {fov}°",
        showarrow=False,
        font=dict(size=9, color="#1E3A8A")
    )

    # ── TALENT ────────────────────────────────────────────────
    # Crosshair
    fig.add_trace(go.Scatter(
        x=[tx - 1.4, tx + 1.4, None, tx, tx],
        y=[ty,       ty,       None, ty - 1.4, ty + 1.4],
        mode="lines",
        line=dict(color="#CC0000", width=2),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=[tx], y=[ty],
        mode="markers",
        marker=dict(
            size=26,
            color="rgba(210,0,0,0.12)",
            symbol="circle",
            line=dict(color="#CC0000", width=3)
        ),
        showlegend=False,
        hovertemplate=(
            f"<b>🎭 {s.talent_name}</b><br>"
            f"X: {tx:.1f} ft ({ft_m(tx):.1f} m)<br>"
            f"Y: {ty:.1f} ft ({ft_m(ty):.1f} m)<br>"
            f"Camera → Talent: {cam_to_talent:.1f} ft ({ft_m(cam_to_talent):.1f} m)<br>"
            f"Key → Talent: {key_to_talent:.1f} ft ({ft_m(key_to_talent):.1f} m)<extra></extra>"
        )
    ))

    fig.add_annotation(
        x=tx, y=ty + 2.0,
        text=f"🎭 {s.talent_name}",
        showarrow=False,
        font=dict(size=11, color="#CC0000", family="Arial Black"),
        align="center"
    )

    # ── LIGHT RATIO BADGE (outside stage, upper right) ────────
    fig.add_annotation(
        x=W + 0.5, y=H - 1,
        xanchor="left",
        text=(
            f"<b>KEY : FILL</b><br>"
            f"<span style='font-size:16px'><b>{ratio_label}</b></span><br>"
            f"<i>{ratio_mood}</i>"
        ),
        showarrow=False,
        bgcolor=ratio_color,
        bordercolor=ratio_color,
        borderwidth=2,
        borderpad=8,
        font=dict(size=10, color="white"),
        align="center"
    )

    # ── LOWER THIRD ───────────────────────────────────────────
    active_lights = f"KEY {s.key_kelvin}K"
    if s.fill1_on: active_lights += f"  |  FILL-1 {s.fill1_kelvin}K"
    if s.back_on:  active_lights += f"  |  BACK {s.back_kelvin}K"
    if s.fill2_on: active_lights += f"  |  FILL-2 {s.fill2_kelvin}K"

    rows = [
        ("#444444", f"📷  {s.lens}   FOV:{fov}°   PAN:{s.cam_pan}°   DOLLY:{s.cam_dolly}ft   C→T: {cam_to_talent:.1f}ft / {ft_m(cam_to_talent):.1f}m"),
        ("#1A6B3C", f"🎯  {fstop}   ISO:{s.iso}   {shutter_str}s   {s.nd_label.split('—')[0].strip()}   {s.fps}fps   {s.resolution}"),
        ("#1A3C6B", f"💡  {active_lights}"),
        ("#8B0000", f"🎭  {s.talent_name}   X:{tx:.1f}ft / {ft_m(tx):.1f}m   Y:{ty:.1f}ft / {ft_m(ty):.1f}m   K→T: {key_to_talent:.1f}ft / {ft_m(key_to_talent):.1f}m"),
    ]

    for i, (row_color, row_text) in enumerate(rows):
        row_y = -1.8 - i * 1.35
        fig.add_shape(
            type="rect",
            x0=0, y0=row_y - 0.55,
            x1=W, y1=row_y + 0.55,
            fillcolor=row_color + "18",
            line=dict(color=row_color, width=1.5)
        )
        fig.add_annotation(
            x=0.4, y=row_y,
            text=row_text,
            showarrow=False,
            font=dict(size=9, color=row_color, family="monospace"),
            xanchor="left",
            align="left"
        )

    # ── LAYOUT ────────────────────────────────────────────────
    fig.update_layout(
        margin=dict(l=60, r=160, t=40, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            range=[-3, W + 9],
            showgrid=False, zeroline=False,
            showticklabels=False,
            scaleanchor="y", scaleratio=1,
            fixedrange=True
        ),
        yaxis=dict(
            range=[-8.5, H + 4],
            showgrid=False, zeroline=False,
            showticklabels=False,
            fixedrange=True
        ),
        height=760,
        dragmode=False,
        showlegend=False,
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────

def render_sidebar():
    s = st.session_state

    st.sidebar.markdown(
        f"<div style='text-align:center; font-size:11px; color:#999; padding:4px'>"
        f"PreViz {PREVIZ_VERSION} — Open Educational Edition</div>",
        unsafe_allow_html=True
    )
    st.sidebar.divider()

    # ── 📷 CAMERA ─────────────────────────────────────────────
    st.sidebar.subheader("📷 Camera — Master Shot")

    lens_idx = LENS_OPTIONS.index(s.lens)
    new_lens = st.sidebar.selectbox("Lens", LENS_OPTIONS, index=lens_idx)
    if new_lens != s.lens:
        st.session_state.lens = new_lens
        st.rerun()

    with st.sidebar.expander("ℹ️ What is FOV?"):
        st.caption(TIPS["FOV"])

    st.sidebar.slider("Pan  (°)",  -45, 45, step=1, key="cam_pan")
    with st.sidebar.expander("ℹ️ What is Pan?"):
        st.caption(TIPS["Pan"])

    st.sidebar.slider("Dolly  (ft from Wall 4)", 0.5, 9.0, step=0.5, key="cam_dolly")
    with st.sidebar.expander("ℹ️ What is Dolly?"):
        st.caption(TIPS["Dolly"])

    with st.sidebar.expander("ℹ️ What is Master Shot?"):
        st.caption(TIPS["Master Shot"])
    with st.sidebar.expander("ℹ️ What is the Fourth Wall?"):
        st.caption(TIPS["Fourth Wall"])

    st.sidebar.divider()

    # ── 📹 VIDEO SPECS ────────────────────────────────────────
    st.sidebar.subheader("📹 Video Specifications")

    fps_idx = FPS_OPTIONS.index(s.fps)
    new_fps = st.sidebar.selectbox("Frame Rate (fps)", FPS_OPTIONS, index=fps_idx)
    if new_fps != s.fps:
        st.session_state.fps = new_fps
        st.rerun()

    shutter_str = SHUTTER_BY_FPS[s.fps]
    st.sidebar.info(f"Shutter: **{shutter_str}s**  (180° rule → 2× frame rate)")
    with st.sidebar.expander("ℹ️ What is Shutter Speed?"):
        st.caption(TIPS["Shutter Speed"])

    res_idx = RESOLUTION_OPTIONS.index(s.resolution)
    new_res = st.sidebar.selectbox("Resolution", RESOLUTION_OPTIONS, index=res_idx)
    if new_res != s.resolution:
        st.session_state.resolution = new_res
        st.rerun()

    iso_idx = ISO_OPTIONS.index(s.iso)
    new_iso = st.sidebar.selectbox("ISO / Gain", ISO_OPTIONS, index=iso_idx)
    if new_iso != s.iso:
        st.session_state.iso = new_iso
        st.rerun()
    with st.sidebar.expander("ℹ️ What is ISO?"):
        st.caption(TIPS["ISO"])

    nd_labels = list(ND_OPTIONS.keys())
    nd_idx = nd_labels.index(s.nd_label)
    new_nd = st.sidebar.selectbox("ND Filter", nd_labels, index=nd_idx)
    if new_nd != s.nd_label:
        st.session_state.nd_label = new_nd
        st.rerun()
    with st.sidebar.expander("ℹ️ What is an ND Filter?"):
        st.caption(TIPS["ND Filter"])

    # Exposure result
    nd_stops = ND_OPTIONS[s.nd_label]
    fstop = calculate_fstop(s.key_intensity, s.iso, shutter_str, nd_stops)
    st.sidebar.success(f"**Suggested f-stop: {fstop}**")
    with st.sidebar.expander("ℹ️ What is f-stop?"):
        st.caption(TIPS["f-stop"])

    st.sidebar.divider()

    # ── 🔆 KEY LIGHT ──────────────────────────────────────────
    st.sidebar.subheader("🔆 Key Light")

    st.sidebar.slider("Intensity (%)", 0, 100, step=1, key="key_intensity")
    st.sidebar.slider("Color Temperature (K)", 2000, 10000, step=100, key="key_kelvin")

    kc, kname = kelvin_to_display(s.key_kelvin)
    st.sidebar.markdown(
        f"<div style='background:{kc};border-radius:6px;padding:4px 10px;"
        f"font-size:12px;color:#333;display:inline-block'>"
        f"<b>{s.key_kelvin}K</b> — {kname}</div>",
        unsafe_allow_html=True
    )

    st.sidebar.slider("Position — Stage Left/Right (ft)", 2.0, 14.0, step=0.5, key="key_x")
    with st.sidebar.expander("ℹ️ What is Key Light?"):
        st.caption(TIPS["Key Light"])
    with st.sidebar.expander("ℹ️ What is Kelvin?"):
        st.caption(TIPS["Kelvin"])

    st.sidebar.divider()

    # ── 💡 OVERHEAD THREE-POINT LIGHTS ───────────────────────
    st.sidebar.subheader("💡 Overhead Three-Point Lights")

    for label, key_on, key_int, key_k, tip_key in [
        ("Fill #1  (upper left)",  "fill1_on", "fill1_intensity", "fill1_kelvin",  "Fill Light"),
        ("Back Light  (Wall 2)",   "back_on",  "back_intensity",  "back_kelvin",   "Back Light"),
        ("Fill #2  (upper right)", "fill2_on", "fill2_intensity", "fill2_kelvin",  "Fill Light"),
    ]:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            st.toggle("", value=getattr(s, key_on), key=key_on)

        if getattr(s, key_on):
            st.sidebar.slider(f"Intensity  ({label[:6]})", 0, 100, step=1, key=key_int)
            st.sidebar.slider(f"Kelvin  ({label[:6]})", 2000, 10000, step=100, key=key_k)
            lc, lname = kelvin_to_display(getattr(s, key_k))
            st.sidebar.markdown(
                f"<div style='background:{lc};border-radius:4px;padding:2px 8px;"
                f"font-size:11px;color:#333;display:inline-block;margin-bottom:6px'>"
                f"{getattr(s, key_k)}K — {lname}</div>",
                unsafe_allow_html=True
            )

    with st.sidebar.expander("ℹ️ What is Fill Light?"):
        st.caption(TIPS["Fill Light"])
    with st.sidebar.expander("ℹ️ What is Back Light?"):
        st.caption(TIPS["Back Light"])

    st.sidebar.divider()

    # ── 📊 LIGHT RATIO ────────────────────────────────────────
    st.sidebar.subheader("📊 Light Ratio")
    ratio_label, ratio_color, ratio_mood = calculate_ratio(
        s.key_intensity,
        s.fill1_intensity if s.fill1_on else 0
    )
    st.sidebar.markdown(
        f"<div style='background:{ratio_color};border-radius:8px;padding:8px 14px;"
        f"font-size:13px;color:white;text-align:center'>"
        f"<b>Key : Fill — {ratio_label}</b><br>"
        f"<span style='font-size:11px'>{ratio_mood}</span></div>",
        unsafe_allow_html=True
    )
    with st.sidebar.expander("ℹ️ What is Light Ratio?"):
        st.caption(TIPS["Light Ratio"])

    st.sidebar.divider()

    # ── 🎭 TALENT ─────────────────────────────────────────────
    st.sidebar.subheader("🎭 Talent")

    st.sidebar.text_input("Name", key="talent_name")
    st.sidebar.slider("Stage Left / Right  (ft)", 2.0, 28.0, step=0.5, key="talent_x")
    st.sidebar.slider("Stage Depth  (ft from Wall 4)", 2.0, 18.0, step=0.5, key="talent_y")

    cam_to_t = dist(STAGE_W / 2, s.cam_dolly, s.talent_x, s.talent_y)
    key_to_t = dist(s.key_x, s.talent_y, s.talent_x, s.talent_y)
    st.sidebar.caption(
        f"📏  Camera → Talent: **{cam_to_t:.1f} ft** / {ft_m(cam_to_t):.1f} m  \n"
        f"📏  Key → Talent: **{key_to_t:.1f} ft** / {ft_m(key_to_t):.1f} m"
    )

    if st.sidebar.button("↩ Reset to Center"):
        st.session_state.talent_x = 15.0
        st.session_state.talent_y = 10.0
        st.rerun()

    st.sidebar.divider()

    # ── ✅ APPROVAL GATE ──────────────────────────────────────
    st.sidebar.subheader("✅ Approval Gate")

    st.sidebar.checkbox("DP Approved",       key="approved_dp")
    st.sidebar.checkbox("Gaffer Approved",   key="approved_gaffer")
    st.sidebar.checkbox("Director Approved", key="approved_director")

    all_approved = s.approved_dp and s.approved_gaffer and s.approved_director

    if all_approved and not s.approved_at:
        st.session_state.approved_at = datetime.now().strftime("%Y-%m-%d  %H:%M")
    elif not all_approved:
        st.session_state.approved_at = None

    if all_approved:
        st.sidebar.success(f"✅ All approved  |  {s.approved_at}")
        st.sidebar.button("🖨️ Print Floor Plan", on_click=lambda: None)
        st.sidebar.caption("Use your browser's Print command (⌘P / Ctrl+P) — landscape layout is applied automatically.")
    else:
        st.sidebar.button("🖨️ Print Floor Plan", disabled=True)
        remaining = []
        if not s.approved_dp:      remaining.append("DP")
        if not s.approved_gaffer:  remaining.append("Gaffer")
        if not s.approved_director: remaining.append("Director")
        st.sidebar.caption(f"Waiting for: {', '.join(remaining)}")

    with st.sidebar.expander("ℹ️ What is the Approval Gate?"):
        st.caption(TIPS["Approval Gate"])


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title=f"PreViz {PREVIZ_VERSION} — Open Educational Edition",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Print CSS
    st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"]  { display: none !important; }
        [data-testid="stToolbar"]  { display: none !important; }
        header                     { display: none !important; }
        .stButton                  { display: none !important; }
        .block-container           { padding: 0 !important; }
        @page                      { size: landscape; margin: 0.4in; }
    }
    </style>
    """, unsafe_allow_html=True)

    init_state()
    render_sidebar()

    # Header
    col_title, col_badge = st.columns([6, 1])
    with col_title:
        st.markdown(
            f"<h2 style='margin-bottom:2px'>🎬 PreViz {PREVIZ_VERSION}"
            f" — Preset Set  <span style='font-size:14px;color:#888'>"
            f"Phase 1: Studio Lighting</span></h2>",
            unsafe_allow_html=True
        )
        st.caption("30 × 20 ft studio stage  |  One subject  |  Three-point lighting  |  Adjust → Observe → Understand")
    with col_badge:
        s = st.session_state
        all_approved = s.approved_dp and s.approved_gaffer and s.approved_director
        if all_approved:
            st.markdown(
                "<div style='background:#27AE60;color:white;border-radius:8px;"
                "padding:6px 12px;text-align:center;font-size:12px'>"
                "✅ APPROVED</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='background:#E67E22;color:white;border-radius:8px;"
                "padding:6px 12px;text-align:center;font-size:12px'>"
                "⏳ PENDING</div>",
                unsafe_allow_html=True
            )

    # Floor plan
    fig = draw_floor_plan()
    st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.markdown(
        "<div style='text-align:center;color:#BBB;font-size:11px;padding:8px'>"
        "Developed by Eduardo Carmona, MFA — CSUDH · LMU  |  "
        "GNU GPL v3.0  |  Free for every student — from Los Angeles to Lima to Windhoek."
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
