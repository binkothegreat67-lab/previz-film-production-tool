"""
PreViz 4.2 — Open Educational Edition  # UPDATED VERSION
Developed by Eduardo Carmona, MFA — CSUDH · LMU
GNU General Public License v3.0
Free for every student — from Los Angeles to Lima to Windhoek.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math
from datetime import datetime
import time  # For auto-play animation

# 
# CONSTANTS
# 
PREVIZ_VERSION = "4.2"  # UPDATED
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

# 
# TIPS DICTIONARY  (swap this dict for multilingual support)
# 
TIPS = {
    "Key Light":     "The main light source. It establishes exposure and the direction of primary shadows. Everything else is relative to it.",
    "Fill Light":    "Fills in the shadows from the Key. Always softer and dimmer than the Key. Controls how deep the shadows are.",
    "Back Light":    "Positioned behind and above the subject. Creates a rim that separates them from the background. Also called a hair light.",
    "Kelvin":        "Color temperature of light. Low values (2000K) are warm orange. High values (10000K) are cool blue. Daylight is 5600K.",
    "f-stop":        "The aperture setting. Lower number (f/1.4) = wide open = more light. Higher number (f/16) = closed down = less light.",
    "ISO":           "Sensor sensitivity. ISO 100 = base, least noise. ISO 6400 = very sensitive, more noise. Higher ISO brightens the image. In video/cinema, think of it as Gain for low-light flexibility.",
    "Shutter Speed": "How long each frame is exposed. The 180° rule: set shutter to 2× your frame rate. At 24fps, use 1/48s for natural motion blur.",
    "ND Filter":     "Neutral Density filter — sunglasses for the lens. Reduces light without changing color. Lets you shoot wide open outdoors.",
    "Pan":           "Rotating the camera left or right on its vertical axis without moving it. Measured in degrees from center.",
    "Tilt":          "Rotating the camera up or down on its horizontal axis. Five positions from low to high.",
    "Dolly":         "Physically moving the camera toward or away from the subject. Changes perspective, not just framing. As you dolly in, watch how lighting ratios shift for chiaroscuro effects.",
    "FOV":           "Field of View. The angle the lens captures. Wide lens (12mm) = 90° FOV. Telephoto (135mm) = only 15° FOV.",
    "Light Ratio":   "The brightness relationship between Key and Fill lights. 3:1 is classic Hollywood. 8:1+ creates noir and drama.",
    "Master Shot":   "A wide establishing shot that captures all the action in a scene. Usually set up first so everything else is covered relative to it.",
    "Fourth Wall":   "The imaginary wall between the actors and the camera. Leaving it open means the camera lives outside the scene.",
    "Approval Gate": "All three department heads (DP, Gaffer, Director) must sign off before a floor plan becomes an official production document.",
    "Moving Shot":   "Simulates camera movement from Position A to B. Teaches how POV and lighting evolve during dollies or tracks. Use the progress slider to scrub and see suggestions for adjustments.",
    "Chiaroscuro":   "Artistic use of strong light/dark contrasts. As the camera moves, watch how ratios shift for dramatic effect.",
    "POV Dynamics":  "Point-of-view changes with movement: foreground/background relationships shift, altering composition and mood.",
    # NEW: Mode Switch
    "Mode":          "Switch between Video/Cinema (with FPS and shutter for motion) and Photography (stills-focused, simpler exposure)."
}

# 
# HELPERS
# 

def kelvin_to_display(k):
    """Return (hex_color, name) for a Kelvin value."""
    for max_k, color, name in KELVIN_SCALE:
        if k <= max_k:
            return color, name
    return KELVIN_SCALE[-1][1], KELVIN_SCALE[-1][2]

def calculate_fstop(key_intensity, iso, shutter_str, nd_stops, mode):
    """
    Calculate suggested f-stop from exposure parameters.
    Baseline: key=100%, ISO=800, 1/48s (video) or 1/100s (photo), ND=0 f/5.6
    Key Light drives exposure (pedagogical principle).
    """
    if key_intensity <= 0:
        return "---"
    denom = SHUTTER_DENOM.get(shutter_str, 100 if mode == "Photography" else 48)
    base_idx = 5  # f/5.6
    key_adj     =  math.log2(max(key_intensity, 0.1) / 100)  # brighter key close down
    iso_adj     =  math.log2(iso / 800)                       # higher ISO  close down
    shutter_adj =  math.log2(48 / denom)                      # faster shutter open up
    nd_adj      = -nd_stops                                    # more ND open up
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

# NEW: Chiaroscuro index helper
def chiaroscuro_index(ratio_label):
    if ratio_label in ["1:1", "2:1", "3:1"]:
        return "Low Contrast", "#4A90D9"
    elif ratio_label in ["4:1", "6:1"]:
        return "Medium Contrast", "#E67E22"
    else:
        return "High Contrast (Chiaroscuro)", "#C0392B"

# NEW: Suggestion helper based on movement
def get_suggestion(ratio_label, progress):
    if progress > 0.5 and "High" in chiaroscuro_index(ratio_label)[0]:
        return "Suggestion: Increase fill intensity to reduce shadows as camera approaches."
    elif progress < 0.5 and "Low" in chiaroscuro_index(ratio_label)[0]:
        return "Suggestion: Decrease fill for more drama at start."
    return ""

def dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def ft_m(ft):
    return round(ft * 0.3048, 1)

def rot2d(vx, vy, theta):
    """Rotate vector (vx, vy) by theta radians."""
    return (vx * math.cos(theta) - vy * math.sin(theta),
            vx * math.sin(theta) + vy * math.cos(theta))

# NEW: Interpolate position for animation
def interpolate_path(start_dolly, end_dolly, start_pan, end_pan, path_type, progress):
    if path_type == "Line":
        dolly = start_dolly + progress * (end_dolly - start_dolly)
        pan = start_pan + progress * (end_pan - start_pan)
    else:  # Soft Curve
        mid_dolly = (start_dolly + end_dolly) / 2 + 2.0
        t = progress
        dolly = (1 - t)**2 * start_dolly + 2*(1 - t)*t * mid_dolly + t**2 * end_dolly
        pan = start_pan + t * (end_pan - start_pan)
    return dolly, pan

# 
# SESSION STATE
# 

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
        # Mode NEW
        "mode":         "Video/Cinema",
        # Key Light
        "key_intensity": 80,
        "key_kelvin":    5600,
        "key_x":         22.0,
        # Fill #1 (fixed upper left)
        "fill1_on":        True,
        "fill1_intensity": 40,
        "fill1_kelvin":    5600,
        # Back Light (fixed center Wall 2)
        "back_on":        True,
        "back_intensity": 60,
        "back_kelvin":    5600,
        # Fill #2 (now mobile, optional)
        "fill2_on":        False,  # Default off
        "fill2_intensity": 40,
        "fill2_kelvin":    5600,
        "fill2_x":         26.0,
        "fill2_y":         16.0,
        # Talent
        "talent_name": "Actor",
        "talent_x":    15.0,
        "talent_y":    10.0,
        # Approval
        "approved_dp":      False,
        "approved_gaffer":  False,
        "approved_director": False,
        "approved_at":      None,
        # Moving Shot
        "moving_shot_on":   False,
        "start_dolly":      3.0,
        "end_dolly":        7.0,
        "start_pan":        -15,
        "end_pan":          15,
        "path_type":        "Line",
        # NEW: Animation
        "progress":         0.0,
        "auto_play":        False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# 
# FLOOR PLAN
# 

def draw_floor_plan():
    s = st.session_state
    W, H = STAGE_W, STAGE_H

    # Derived values
    fov = LENS_FOV[s.lens]
    shutter_str = SHUTTER_BY_FPS[s.fps] if s.mode == "Video/Cinema" else "1/100"  # Photo default
    nd_stops = ND_OPTIONS[s.nd_label]
    fstop = calculate_fstop(s.key_intensity, s.iso, shutter_str, nd_stops, s.mode)
    cam_x = W / 2
    progress = s.progress  # For animation
    if s.moving_shot_on:
        cam_y, cam_pan = interpolate_path(s.start_dolly, s.end_dolly, s.start_pan, s.end_pan, s.path_type, progress)
    else:
        cam_y = s.cam_dolly
        cam_pan = s.cam_pan
    key_x = s.key_x
    key_y = cam_y  # Tied to camera depth
    tx, ty = s.talent_x, s.talent_y
    key_color, key_kname = kelvin_to_display(s.key_kelvin)
    fill_int = ((s.fill1_intensity if s.fill1_on else 0) + (s.fill2_intensity if s.fill2_on else 0)) / 2  # Average if both
    ratio_label, ratio_color, ratio_mood = calculate_ratio(s.key_intensity, fill_int)
    cam_to_talent = dist(cam_x, cam_y, tx, ty)
    key_to_talent = dist(key_x, key_y, tx, ty)
    chiaro_idx, chiaro_color = chiaroscuro_index(ratio_label)
    suggestion = get_suggestion(ratio_label, progress)

    fig = go.Figure()

    # STAGE FLOOR \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)

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

    # Wall labels (unchanged)
    for ann in [
        dict(x=-1.8, y=H/2, text="WALL 1", textangle=-90,
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W/2, y=H+1.5, text="WALL 2 — BACK",
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W+1.8, y=H/2, text="WALL 3", textangle=90,
             showarrow=False, font=dict(size=9, color="#999")),
        dict(x=W/2, y=-0.7, text="4TH WALL — OPEN (CAMERA)",
             showarrow=False, font=dict(size=9, color="#999")),
    ]:
        fig.add_annotation(**ann)

    # Stage dimensions (unchanged)
    fig.add_annotation(x=W/2, y=H+0.7, text="30 ft  |  9.1 m",
                       showarrow=False, font=dict(size=8, color="#AAA"))
    fig.add_annotation(x=-0.6, y=H/2, text="20 ft | 6.1 m",
                       showarrow=False, font=dict(size=8, color="#AAA"), textangle=-90)

    # OVERHEAD LIGHTS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 
    overhead = [
        (4, 16, "fill1_on", "fill1_intensity", "fill1_kelvin", "Fill #1"),  # Fixed
        (W / 2, 18, "back_on", "back_intensity", "back_kelvin", "Back"),    # Fixed
    ]
    for lx, ly, key_on, key_int, key_k, label in overhead:
        is_on = getattr(s, key_on)
        lkelvin = getattr(s, key_k)
        lintens = getattr(s, key_int)
        lcolor, lkname = kelvin_to_display(lkelvin)
        if is_on:
            r, g, b = int(lcolor[1:3], 16), int(lcolor[3:5], 16), int(lcolor[5:7], 16)
            fig.add_shape(type="circle", x0=lx-1, y0=ly-1, x1=lx+1, y1=ly+1,
                          fillcolor=f"rgba({r},{g},{b},0.33)", line=dict(color=lcolor, width=2))
        marker_color = "#FF9900" if is_on else "#BBBBBB"
        fig.add_trace(go.Scatter(x=[lx], y=[ly], mode="markers", marker=dict(size=18, color=marker_color, symbol="square", line=dict(color="#333", width=2)),
                                 showlegend=False, hovertemplate=f"<b>{label}</b><br>{'ON' if is_on else 'OFF'}<br>{lkelvin}K — {lkname}<br>Intensity: {lintens}%<extra></extra>"))
        fig.add_annotation(x=lx, y=ly, text="", showarrow=False, font=dict(size=13), xanchor="center", yanchor="middle")
        fig.add_annotation(x=lx, y=ly+1.5, text=f"{label}<br>{lkelvin}K", showarrow=False, font=dict(size=8, color="#555"), align="center")

    # NEW: Mobile Fill #2
    if s.fill2_on:
        lx, ly = s.fill2_x, s.fill2_y
        lkelvin = s.fill2_kelvin
        lintens = s.fill2_intensity
        lcolor, lkname = kelvin_to_display(lkelvin)
        r, g, b = int(lcolor[1:3], 16), int(lcolor[3:5], 16), int(lcolor[5:7], 16)
        fig.add_shape(type="circle", x0=lx-1, y0=ly-1, x1=lx+1, y1=ly+1,
                      fillcolor=f"rgba({r},{g},{b},0.33)", line=dict(color=lcolor, width=2))
        marker_color = "#FF9900"
        fig.add_trace(go.Scatter(x=[lx], y=[ly], mode="markers", marker=dict(size=18, color=marker_color, symbol="square", line=dict(color="#333", width=2)),
                                 showlegend=False, hovertemplate=f"<b>Fill #2 (Mobile)</b><br>ON<br>{lkelvin}K — {lkname}<br>Intensity: {lintens}%<extra></extra>"))
        fig.add_annotation(x=lx, y=ly, text="", showarrow=False, font=dict(size=13), xanchor="center", yanchor="middle")
        fig.add_annotation(x=lx, y=ly+1.5, text=f"Fill #2<br>{lkelvin}K", showarrow=False, font=dict(size=8, color="#555"), align="center")

    # KEY LIGHT \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged, but dynamic with cam_y)
    fig.add_trace(go.Scatter(x=[key_x, tx], y=[key_y, ty], mode="lines", line=dict(color=key_color, width=3), showlegend=False, hoverinfo="skip"))
    angle_to_talent = math.atan2(ty - key_y, tx - key_x)
    dome_r = 1.4
    n_pts = 30
    arc_a = np.linspace(angle_to_talent - math.pi / 2, angle_to_talent + math.pi / 2, n_pts)
    dome_xs = [key_x + dome_r * math.cos(a) for a in arc_a]
    dome_ys = [key_y + dome_r * math.sin(a) for a in arc_a]
    fig.add_trace(go.Scatter(x=dome_xs, y=dome_ys, mode="lines", fill="toself", fillcolor=f"rgba({int(key_color[1:3],16)},{int(key_color[3:5],16)},{int(key_color[5:7],16)},0.80)",
                             line=dict(color=key_color, width=3), showlegend=False, hovertemplate=f"<b>Key Light</b><br>{s.key_kelvin}K — {key_kname}<br>Intensity: {s.key_intensity}%<extra></extra>"))
    fig.add_annotation(x=key_x - 0.4, y=key_y + dome_r + 1.2, text=f"KEY<br>{s.key_kelvin}K", showarrow=False, font=dict(size=9, color="#333"), align="center")

    # CAMERA (Dynamic with Perspective) \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 
    def add_camera_and_fov(cam_y_pos, pan_deg, label="", opacity=1.0, is_ghost=False):
        pan_rad = math.radians(pan_deg)
        fov_half_rad = math.radians(fov / 2)
        fwd = (math.sin(pan_rad), math.cos(pan_rad))
        cone_len = min(15.0, H - cam_y_pos + 0.5)
        left_dir = rot2d(fwd[0], fwd[1], fov_half_rad)
        right_dir = rot2d(fwd[0], fwd[1], -fov_half_rad)
        fov_lx = cam_x + left_dir[0] * cone_len
        fov_ly = cam_y_pos + left_dir[1] * cone_len
        fov_rx = cam_x + right_dir[0] * cone_len
        fov_ry = cam_y_pos + right_dir[1] * cone_len
        fig.add_trace(go.Scatter(x=[cam_x, fov_lx, fov_rx, cam_x], y=[cam_y_pos, fov_ly, fov_ry, cam_y_pos], fill="toself",
                                 fillcolor=f"rgba(60,90,200,{0.10*opacity})", line=dict(color=f"rgba(60,90,200,{0.45*opacity})", width=1.5), mode="lines", showlegend=False, hoverinfo="skip"))
        # NEW: Perspective scale
        scale_factor = max(0.5, 3.0 / cam_y_pos)  # Smaller when farther (higher y)
        marker_size = 24 * scale_factor
        marker_opacity = max(0.5, 1.0 - (cam_y_pos / H) * 0.5)  # Fade slightly
        marker_color = f"rgba(30,58,138,{marker_opacity if not is_ghost else marker_opacity*0.5})"
        fig.add_trace(go.Scatter(x=[cam_x], y=[cam_y_pos], mode="markers", marker=dict(size=marker_size, color=marker_color, symbol="square",
                                                                                      line=dict(color="white", width=2)), showlegend=False,
                                 hovertemplate=f"<b>{label}</b><br>{s.lens} | FOV: {fov}°<br>Pan: {pan_deg}°<br>Dolly: {cam_y_pos:.1f} ft<extra></extra>"))
        fig.add_annotation(x=cam_x, y=cam_y_pos, text="", showarrow=False, font=dict(size=16*scale_factor), xanchor="center", yanchor="middle")
        if label:
            fig.add_annotation(x=cam_x + 2.0, y=cam_y_pos + 0.3, text=f"{label}: {s.lens} | {fov}°", showarrow=False, font=dict(size=9, color="#1E3A8A"))

    if not s.moving_shot_on:
        add_camera_and_fov(cam_y, cam_pan, "Camera — Master Shot")
    else:
        # Path line
        path_points = [interpolate_path(s.start_dolly, s.end_dolly, s.start_pan, s.end_pan, s.path_type, t) for t in np.linspace(0,1,20)]
        path_ys, path_pans = zip(*path_points)
        path_xs = [cam_x] * len(path_ys)
        dash_style = "dash" if s.path_type == "Line" else "dot"
        fig.add_trace(go.Scatter(x=path_xs, y=path_ys, mode="lines", line=dict(color="#1E3A8A", width=3, dash=dash_style), showlegend=False, hovertemplate="Camera Path<extra></extra>"))
        # Current position
        add_camera_and_fov(cam_y, cam_pan, f"Current (Progress: {int(progress*100)}%)")
        # Endpoints as ghosts
        add_camera_and_fov(s.start_dolly, s.start_pan, "Pos A", opacity=0.6, is_ghost=True)
        add_camera_and_fov(s.end_dolly, s.end_pan, "Pos B", opacity=0.6, is_ghost=True)
        # Dynamic lighting
        rel_key_y = key_y - (cam_y - s.start_dolly)
        rel_key_to_t = dist(key_x, rel_key_y, tx, ty)
        arrow_angle = math.atan2(ty - rel_key_y, tx - key_x)
        arrow_len = 1.5
        arrow_dx = arrow_len * math.cos(arrow_angle)
        arrow_dy = arrow_len * math.sin(arrow_angle)
        fig.add_shape(type="line", x0=tx - arrow_dx, y0=ty - arrow_dy, x1=tx + arrow_dx, y1=ty + arrow_dy,
                      line=dict(color="rgba(0,0,0,0.4)", width=2, dash="dot"))
        fig.add_annotation(x=cam_x - 2.0, y=cam_y - 1.0, text=f"{chiaro_idx}<br>Ratio: {ratio_label}", showarrow=False, bgcolor=chiaro_color,
                           bordercolor=chiaro_color, borderwidth=1, font=dict(size=8, color="white"), align="center")
        if suggestion:
            fig.add_annotation(x=W / 2, y=H + 2.0, text=suggestion, showarrow=False, font=dict(size=10, color="#E67E22"), align="center")

    # TALENT \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    fig.add_trace(go.Scatter(x=[tx-1.4, tx+1.4, None, tx, tx], y=[ty, ty, None, ty-1.4, ty+1.4], mode="lines", line=dict(color="#CC0000", width=2), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[tx], y=[ty], mode="markers", marker=dict(size=26, color="rgba(210,0,0,0.12)", symbol="circle", line=dict(color="#CC0000", width=3)),
                             showlegend=False, hovertemplate=f"<b>{s.talent_name}</b><br>X: {tx:.1f} ft ({ft_m(tx):.1f} m)<br>Y: {ty:.1f} ft ({ft_m(ty):.1f} m)<br>Camera \u8594  Talent: {cam_to_talent:.1f} ft ({ft_m(cam_to_talent):.1f} m)<br>Key \u8594  Talent: {key_to_talent:.1f} ft ({ft_m(key_to_talent):.1f} m)<extra></extra>"))
    fig.add_annotation(x=tx, y=ty + 2.0, text=f"{s.talent_name}", showarrow=False, font=dict(size=11, color="#CC0000", family="Arial Black"), align="center")

    # LIGHT RATIO BADGE \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    fig.add_annotation(x=W + 0.5, y=H - 1, xanchor="left", text=f"<b>KEY : FILL</b><br><span style='font-size:16px'><b>{ratio_label}</b></span><br><i>{ratio_mood}</i>",
                       showarrow=False, bgcolor=ratio_color, bordercolor=ratio_color, borderwidth=2, borderpad=8, font=dict(size=10, color="white"), align="center")

    # LOWER THIRD \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (updated for mode/movement)
    active_lights = f"KEY {s.key_kelvin}K"
    if s.fill1_on: active_lights += f"  |  FILL-1 {s.fill1_kelvin}K"
    if s.back_on:  active_lights += f"  |  BACK {s.back_kelvin}K"
    if s.fill2_on: active_lights += f"  |  FILL-2 {s.fill2_kelvin}K"
    rows = [
        ("#444444", f"{s.lens}   FOV:{fov}°   PAN:{cam_pan}°   DOLLY:{cam_y:.1f}ft   C\u8594 T: {cam_to_talent:.1f}ft / {ft_m(cam_to_talent):.1f}m"),
        ("#1A6B3C", f"{fstop}   ISO:{s.iso}   {shutter_str}s   {s.nd_label.split('—')[0].strip()}   {s.fps if s.mode == 'Video/Cinema' else ''}fps   {s.resolution if s.mode == 'Video/Cinema' else ''}"),
        ("#1A3C6B", f"{active_lights}"),
        ("#8B0000", f"{s.talent_name}   X:{tx:.1f}ft / {ft_m(tx):.1f}m   Y:{ty:.1f}ft / {ft_m(ty):.1f}m   K\u8594 T: {key_to_talent:.1f}ft / {ft_m(key_to_talent):.1f}m"),
    ]
    if s.moving_shot_on:
        rows[0] = ("#444444", f"Moving (Progress {int(progress*100)}%): A({s.start_dolly}ft, {s.start_pan}°) to B({s.end_dolly}ft, {s.end_pan}°) | Path: {s.path_type} | C\u8594 T: {cam_to_talent:.1f}ft")

    for i, (row_color, row_text) in enumerate(rows):
        row_y = -2.5 - i * 1.35
        r, g, b = int(row_color[1:3],16), int(row_color[3:5],16), int(row_color[5:7],16)
        fig.add_shape(type="rect", x0=0, y0=row_y-0.55, x1=W, y1=row_y+0.55, fillcolor=f"rgba({r},{g},{b},0.09)", line=dict(color=row_color, width=1.5))
        fig.add_annotation(x=0.4, y=row_y, text=row_text, showarrow=False, font=dict(size=9, color=row_color, family="monospace"), xanchor="left", align="left")

    # LAYOUT \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    fig.update_layout(margin=dict(l=60, r=160, t=40, b=30), paper_bgcolor="white", plot_bgcolor="white",
                      xaxis=dict(range=[-3, W+9], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1, fixedrange=True),
                      yaxis=dict(range=[-11.5, H+4], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
                      height=760, dragmode=False, showlegend=False)
    return fig

# 
# SIDEBAR
# 

def render_sidebar():
    s = st.session_state
    # Define shutter_str safely upfront so it's always available below
    shutter_str = SHUTTER_BY_FPS.get(s.fps, "1/48") if s.mode == "Video/Cinema" else "1/100"

    st.sidebar.markdown(f"<div style='text-align:center; font-size:11px; color:#999; padding:4px'>PreViz {PREVIZ_VERSION} — Open Educational Edition</div>", unsafe_allow_html=True)
    st.sidebar.divider()

    # NEW: Mode Switch
    mode_options = ["Video/Cinema", "Photography"]
    mode_idx = mode_options.index(s.mode)
    new_mode = st.sidebar.selectbox("Mode", mode_options, index=mode_idx)
    if new_mode != s.mode:
        st.session_state.mode = new_mode
        st.rerun()
    with st.sidebar.expander("What is Mode?"):
        st.caption(TIPS["Mode"])

    # CAMERA \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 
    st.sidebar.subheader("Camera — Master Shot")
    lens_idx = LENS_OPTIONS.index(s.lens)
    new_lens = st.sidebar.selectbox("Lens", LENS_OPTIONS, index=lens_idx)
    if new_lens != s.lens:
        st.session_state.lens = new_lens
        st.rerun()
    with st.sidebar.expander("What is FOV?"):
        st.caption(TIPS["FOV"])

    st.sidebar.checkbox("Enable Moving Shot", key="moving_shot_on")
    if s.moving_shot_on:
        st.sidebar.subheader("Moving Shot Settings")
        st.sidebar.slider("Start Dolly (Pos A, ft from Wall 4)", 0.5, 9.0, step=0.5, key="start_dolly")
        st.sidebar.slider("Start Pan (Pos A, °)", -45, 45, step=1, key="start_pan")
        st.sidebar.slider("End Dolly (Pos B, ft from Wall 4)", 0.5, 9.0, step=0.5, key="end_dolly")
        st.sidebar.slider("End Pan (Pos B, °)", -45, 45, step=1, key="end_pan")
        path_options = ["Line", "Soft Curve"]
        path_idx = path_options.index(s.path_type)
        new_path = st.sidebar.selectbox("Path Type", path_options, index=path_idx)
        if new_path != s.path_type:
            st.session_state.path_type = new_path
            st.rerun()
        # NEW: Animation Controls
        st.sidebar.slider("Progress (%)", 0.0, 1.0, step=0.01, key="progress")
        col_play, col_stop = st.sidebar.columns(2)
        with col_play:
            if st.button("▶ Auto-Play", disabled=s.auto_play):
                s.auto_play = True
                st.rerun()
        with col_stop:
            if st.button("■ Stop", disabled=not s.auto_play):
                s.auto_play = False
                st.rerun()
        if s.auto_play:
            s.progress = min(1.0, s.progress + 0.05)
            if s.progress >= 1.0:
                s.auto_play = False
            time.sleep(0.08)  # Frame delay
            st.rerun()
        with st.sidebar.expander("What is Moving Shot?"):
            st.caption(TIPS["Moving Shot"])
        with st.sidebar.expander("What is Chiaroscuro?"):
            st.caption(TIPS["Chiaroscuro"])
        with st.sidebar.expander("What is POV Dynamics?"):
            st.caption(TIPS["POV Dynamics"])
    else:
        st.sidebar.slider("Pan  (°)", -45, 45, step=1, key="cam_pan")
        with st.sidebar.expander("What is Pan?"):
            st.caption(TIPS["Pan"])
        st.sidebar.slider("Dolly  (ft from Wall 4)", 0.5, 9.0, step=0.5, key="cam_dolly")
        with st.sidebar.expander("What is Dolly?"):
            st.caption(TIPS["Dolly"])

    with st.sidebar.expander("What is Master Shot?"):
        st.caption(TIPS["Master Shot"])
    with st.sidebar.expander("What is the Fourth Wall?"):
        st.caption(TIPS["Fourth Wall"])

    st.sidebar.divider()

    # VIDEO SPECS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 
    st.sidebar.subheader("Specifications")
    if s.mode == "Video/Cinema":
        fps_idx = FPS_OPTIONS.index(s.fps)
        new_fps = st.sidebar.selectbox("Frame Rate (fps)", FPS_OPTIONS, index=fps_idx)
        if new_fps != s.fps:
            st.session_state.fps = new_fps
            st.rerun()
        shutter_str = SHUTTER_BY_FPS[s.fps]
        st.sidebar.info(f"Shutter: **{shutter_str}s**  (180° rule 2× frame rate)")
        with st.sidebar.expander("What is Shutter Speed?"):
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
    with st.sidebar.expander("What is ISO?"):
        st.caption(TIPS["ISO"])

    nd_labels = list(ND_OPTIONS.keys())
    nd_idx = nd_labels.index(s.nd_label)
    new_nd = st.sidebar.selectbox("ND Filter", nd_labels, index=nd_idx)
    if new_nd != s.nd_label:
        st.session_state.nd_label = new_nd
        st.rerun()
    with st.sidebar.expander("What is an ND Filter?"):
        st.caption(TIPS["ND Filter"])

    nd_stops = ND_OPTIONS[s.nd_label]
    fstop = calculate_fstop(s.key_intensity, s.iso, shutter_str, nd_stops, s.mode)
    st.sidebar.success(f"**Suggested f-stop: {fstop}**")
    with st.sidebar.expander("What is f-stop?"):
        st.caption(TIPS["f-stop"])

    st.sidebar.divider()

    # KEY LIGHT \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    st.sidebar.subheader("Key Light")
    st.sidebar.slider("Intensity (%)", 0, 100, step=1, key="key_intensity")
    st.sidebar.slider("Color Temperature (K)", 2000, 10000, step=100, key="key_kelvin")
    kc, kname = kelvin_to_display(s.key_kelvin)
    st.sidebar.markdown(f"<div style='background:{kc};border-radius:6px;padding:4px 10px;font-size:12px;color:#333;display:inline-block'><b>{s.key_kelvin}K</b> — {kname}</div>", unsafe_allow_html=True)
    st.sidebar.slider("Position — Stage Left/Right (ft)", 2.0, 28.0, step=0.5, key="key_x")
    with st.sidebar.expander("What is Key Light?"):
        st.caption(TIPS["Key Light"])
    with st.sidebar.expander("What is Kelvin?"):
        st.caption(TIPS["Kelvin"])

    st.sidebar.divider()

    # OVERHEAD THREE-POINT LIGHTS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 
    st.sidebar.subheader("Overhead Lights")
    for label, key_on, key_int, key_k, tip_key in [
        ("Fill #1  (upper left fixed)", "fill1_on", "fill1_intensity", "fill1_kelvin", "Fill Light"),
        ("Back Light  (Wall 2 fixed)", "back_on", "back_intensity", "back_kelvin", "Back Light"),
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
            st.sidebar.markdown(f"<div style='background:{lc};border-radius:4px;padding:2px 8px;font-size:11px;color:#333;display:inline-block;margin-bottom:6px'>{getattr(s, key_k)}K — {lname}</div>", unsafe_allow_html=True)

    # NEW: Extended Menu for Mobile Fill #2
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.markdown("**Fill #2  (mobile optional)**")
    with col2:
        st.toggle("", value=s.fill2_on, key="fill2_on")
    if s.fill2_on:
        with st.sidebar.expander("Extended Fill #2 Settings"):
            st.slider("Intensity (%)", 0, 100, step=1, key="fill2_intensity")
            st.slider("Color Temperature (K)", 2000, 10000, step=100, key="fill2_kelvin")
            lc, lname = kelvin_to_display(s.fill2_kelvin)
            st.markdown(f"<div style='background:{lc};border-radius:4px;padding:2px 8px;font-size:11px;color:#333;display:inline-block'>{s.fill2_kelvin}K — {lname}</div>", unsafe_allow_html=True)
            st.slider("Position X (Stage Left/Right ft)", 2.0, 28.0, step=0.5, key="fill2_x")
            st.slider("Position Y (Depth ft from Wall 4)", 2.0, 18.0, step=0.5, key="fill2_y")

    with st.sidebar.expander("What is Fill Light?"):
        st.caption(TIPS["Fill Light"])
    with st.sidebar.expander("What is Back Light?"):
        st.caption(TIPS["Back Light"])

    st.sidebar.divider()

    # LIGHT RATIO \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    st.sidebar.subheader("Light Ratio")
    ratio_label, ratio_color, ratio_mood = calculate_ratio(s.key_intensity, ((s.fill1_intensity if s.fill1_on else 0) + (s.fill2_intensity if s.fill2_on else 0)) / 2)
    st.sidebar.markdown(f"<div style='background:{ratio_color};border-radius:8px;padding:8px 14px;font-size:13px;color:white;text-align:center'><b>Key : Fill — {ratio_label}</b><br><span style='font-size:11px'>{ratio_mood}</span></div>", unsafe_allow_html=True)
    with st.sidebar.expander("What is Light Ratio?"):
        st.caption(TIPS["Light Ratio"])

    st.sidebar.divider()

    # TALENT \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    st.sidebar.subheader("Talent")
    st.sidebar.text_input("Name", key="talent_name")
    tx_val = st.sidebar.slider("Stage Left / Right  (ft)", 2.0, 28.0, value=float(s.talent_x), step=0.5)
    s.talent_x = tx_val
    ty_val = st.sidebar.slider("Stage Depth  (ft from Wall 4)", 2.0, 18.0, value=float(s.talent_y), step=0.5)
    s.talent_y = ty_val
    cam_to_t = dist(STAGE_W / 2, s.cam_dolly, tx_val, ty_val)
    key_to_t = dist(s.key_x, ty_val, tx_val, ty_val)
    st.sidebar.caption(f"Camera \u8594  Talent: **{cam_to_t:.1f} ft** / {ft_m(cam_to_t):.1f} m  \\n\u55357 \u56527   Key \u8594  Talent: **{key_to_t:.1f} ft** / {ft_m(key_to_t):.1f} m")
    if st.sidebar.button("Reset to Center"):
        s.talent_x = 15.0
        s.talent_y = 10.0
        st.rerun()

    st.sidebar.divider()

    # APPROVAL GATE \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472  (unchanged)
    st.sidebar.subheader("Approval Gate")
    st.sidebar.checkbox("DP Approved", key="approved_dp")
    st.sidebar.checkbox("Gaffer Approved", key="approved_gaffer")
    st.sidebar.checkbox("Director Approved", key="approved_director")
    all_approved = s.approved_dp and s.approved_gaffer and s.approved_director
    if all_approved and not s.approved_at:
        s.approved_at = datetime.now().strftime("%Y-%m-%d  %H:%M")
    elif not all_approved:
        s.approved_at = None
    if all_approved:
        st.sidebar.success(f"All approved  |  {s.approved_at}")
        st.sidebar.button("Print Floor Plan")
        st.sidebar.caption("Use browser Print (P / Ctrl+P) — landscape applied.")
    else:
        st.sidebar.button("Print Floor Plan", disabled=True)
        remaining = [name for cond, name in [(not s.approved_dp, "DP"), (not s.approved_gaffer, "Gaffer"), (not s.approved_director, "Director")] if cond]
        st.sidebar.caption(f"Waiting for: {', '.join(remaining)}")
    with st.sidebar.expander("What is the Approval Gate?"):
        st.caption(TIPS["Approval Gate"])

# 
# MAIN
# 

def main():
    st.set_page_config(page_title=f"PreViz {PREVIZ_VERSION} — Open Educational Edition", page_icon="", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        header { display: none !important; }
        .stButton { display: none !important; }
        .block-container { padding: 0 !important; }
        @page { size: landscape; margin: 0.4in; }
    }
    </style>
    """, unsafe_allow_html=True)

    init_state()
    render_sidebar()

    # Header (unchanged)
    col_title, col_badge = st.columns([6, 1])
    with col_title:
        st.markdown(f"<h2 style='margin-bottom:2px'>PreViz {PREVIZ_VERSION} — Preset Set  <span style='font-size:14px;color:#888'>Phase 1: Studio Lighting</span></h2>", unsafe_allow_html=True)
        st.caption("30 × 20 ft studio stage  |  One subject  |  Three-point lighting  |  Adjust Observe \u8594  Understand")
    with col_badge:
        s = st.session_state
        all_approved = s.approved_dp and s.approved_gaffer and s.approved_director
        badge_color, badge_text = ("#27AE60", "APPROVED") if all_approved else ("#E67E22", "\u9203  PENDING")
        st.markdown(f"<div style='background:{badge_color};color:white;border-radius:8px;padding:6px 12px;text-align:center;font-size:12px'>{badge_text}</div>", unsafe_allow_html=True)

    # Floor plan
    fig = draw_floor_plan()
    st.plotly_chart(fig, use_container_width=True)

    # Footer (unchanged)
    st.markdown("<div style='text-align:center;color:#BBB;font-size:11px;padding:8px'>Developed by Eduardo Carmona, MFA — CSUDH · LMU  |  GNU GPL v3.0  |  Free for every student — from Los Angeles to Lima to Windhoek.</div>", unsafe_allow_html=True)

if __name__ == "__main__":    main()
