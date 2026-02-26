"""
PreViz 4.3 — Open Educational Edition  ·  KINETIC BUILD
Developed by Eduardo Carmona, MFA — CSUDH · LMU
GNU General Public License v3.0
Free for every student — from Los Angeles to Lima to Windhoek.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math
from datetime import datetime
import time

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
PREVIZ_VERSION = "4.3"
STAGE_W = 30
STAGE_H = 20

LENS_OPTIONS = ["12mm", "16mm", "24mm", "35mm", "50mm", "85mm", "100mm", "135mm"]
LENS_FOV = {"12mm":90,"16mm":83,"24mm":73,"35mm":54,"50mm":39,"85mm":24,"100mm":20,"135mm":15}

ISO_OPTIONS       = [100, 200, 400, 800, 1600, 3200, 6400]
RESOLUTION_OPTIONS= ["720p","1080p","4K UHD","4K DCI"]
FPS_OPTIONS       = [24, 25, 30, 60]
SHUTTER_BY_FPS    = {24:"1/48", 25:"1/50", 30:"1/60", 60:"1/120"}
SHUTTER_DENOM     = {"1/48":48,"1/50":50,"1/60":60,"1/120":120}

ND_OPTIONS = {
    "None (0 stops)":0,"ND 0.3 — 1 stop":1,"ND 0.6 — 2 stops":2,
    "ND 0.9 — 3 stops":3,"ND 1.2 — 4 stops":4,"ND 1.8 — 6 stops":6,
    "ND 2.4 — 8 stops":8,"ND 3.0 — 10 stops":10,
}
FSTOPS = [1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11, 16, 22]

KELVIN_SCALE = [
    (2000,"#FF5500","Candlelight"),(2700,"#FF8040","Incandescent"),
    (3200,"#FFB347","Tungsten"),(4000,"#FFD580","Warm White"),
    (4300,"#FFE8C0","Late Afternoon"),(5600,"#FFF8E7","Daylight"),
    (6500,"#EEF5FF","Overcast Sky"),(7500,"#D5E8FF","Cloudy"),
    (10000,"#B8D5FF","Blue Sky"),
]
RATIO_TABLE = [
    (1.2,"1:1","#4A90D9","Flat — broadcast / news"),
    (1.7,"2:1","#4A90D9","Soft, commercial look"),
    (2.5,"3:1","#00C896","Classic cinematic"),
    (3.5,"4:1","#00C896","Dramatic portrait"),
    (5.0,"6:1","#FF6B00","High contrast"),
    (10.0,"8:1","#FF6B00","Near noir"),
    (999,"16:1","#FF1744","High contrast noir"),
]
TIPS = {
    "Key Light":    "The main light source. Establishes exposure and direction of primary shadows. Everything else is relative to it.",
    "Fill Light":   "Fills in the shadows from the Key. Always softer and dimmer. Controls how deep the shadows are.",
    "Back Light":   "Behind and above the subject. Creates a rim that separates them from the background. Also called a hair light.",
    "Kelvin":       "Color temperature. Low values (2000K) = warm orange. High values (10000K) = cool blue. Daylight = 5600K.",
    "f-stop":       "The aperture setting. Lower number (f/1.4) = wide open = more light. Higher (f/16) = less light.",
    "ISO":          "Sensor sensitivity. ISO 100 = base, least noise. ISO 6400 = most sensitive, more grain. In video = Gain.",
    "Shutter Speed":"How long each frame is exposed. 180-degree rule: shutter = 2x frame rate. 24fps = 1/48s.",
    "ND Filter":    "Neutral Density — sunglasses for the lens. Reduces light without changing color. Shoot wide open outdoors.",
    "Pan":          "Rotating the camera left or right on its vertical axis. Measured in degrees from center.",
    "Dolly":        "Physically moving the camera toward or away from subject. Changes perspective, not just framing.",
    "FOV":          "Field of View. Wide lens (12mm) = 90-deg FOV. Telephoto (135mm) = only 15-deg FOV.",
    "Light Ratio":  "Brightness relationship between Key and Fill. 3:1 is classic Hollywood. 8:1+ creates noir and drama.",
    "Master Shot":  "A wide establishing shot that captures all the action. Set up first so everything else is covered.",
    "Fourth Wall":  "The imaginary wall between actors and camera. Open means camera lives outside the scene.",
    "Approval Gate":"All three department heads (DP, Gaffer, Director) sign off before floor plan becomes official.",
    "Moving Shot":  "Simulates camera movement from A to B. Teaches how POV and lighting evolve during dollies.",
    "Chiaroscuro":  "Strong light/dark contrasts as an artistic choice. Watch ratios shift as camera moves.",
    "Mode":         "Video/Cinema = FPS and shutter for motion. Photography = stills-focused, simpler exposure.",
    "Click Stage":  "CLICK anywhere on the stage floor to instantly move talent to that spot. Try it.",
}

# ─────────────────────────────────────────────
# KINETIC CSS  —  broadcast control room energy
# ─────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  --orange:  #FF4500;
  --teal:    #00D4CC;
  --yellow:  #FFE200;
  --green:   #00FF88;
  --red:     #FF1744;
  --navy:    #03060F;
  --panel:   #060A15;
  --card:    #080E1C;
  --border:  #0F1A30;
  --dim:     #1A2540;
  --muted:   #304060;
  --text:    #C8D8F0;
}

html, body, [data-testid="stApp"] {
  background: var(--navy) !important;
  color: var(--text) !important;
}
.block-container {
  padding: 0.8rem 1.2rem 1.5rem !important;
  max-width: 100% !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: var(--panel) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: #8A9EC0 !important; }
[data-testid="stSidebar"] label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.10em !important;
  color: var(--muted) !important;
}
[data-testid="stSidebar"] h3 {
  font-family: 'Barlow Condensed', sans-serif !important;
  font-size: 17px !important;
  font-weight: 800 !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  color: var(--orange) !important;
  border-bottom: 2px solid var(--border) !important;
  padding-bottom: 3px !important;
  margin-top: 14px !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: 5px 0 !important; }
[data-testid="stSidebar"] .stExpander {
  background: #040810 !important;
  border: 1px solid var(--dim) !important;
  border-radius: 3px !important;
}
[data-testid="stSidebar"] .stExpander summary {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  color: var(--teal) !important;
}

/* ── HEADER ── */
.pv-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 56px;
  font-weight: 900;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--orange);
  line-height: 0.9;
  text-shadow: 0 0 60px rgba(255,69,0,0.40), 0 0 20px rgba(255,69,0,0.25);
  margin: 0;
}
.pv-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin: 4px 0 0 3px;
}
.pv-click-hint {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--teal);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 2px 0 0 3px;
  animation: blink-hint 2.4s ease-in-out infinite;
}
@keyframes blink-hint {
  0%,100% { opacity: 0.5; }
  50%      { opacity: 1.0; }
}

/* ── METRIC STRIP ── */
.metric-strip {
  display: flex;
  gap: 6px;
  margin: 8px 0 10px 0;
  flex-wrap: wrap;
}
.mc {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 12px;
  flex: 1;
  min-width: 90px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}
.mc:hover { border-color: var(--muted); }
.mc-top {
  position: absolute;
  top: 0; left: 10%; right: 10%;
  height: 2px;
  border-radius: 0 0 2px 2px;
}
.mc-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.18em;
  margin-bottom: 2px;
}
.mc-val {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.02em;
}
.mc-hint {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  color: var(--dim);
  margin-top: 1px;
}
.mc.live .mc-val { animation: pulse-live 1.4s ease-in-out infinite; }
@keyframes pulse-live {
  0%,100% { opacity: 1.0; }
  50%      { opacity: 0.6; }
}

/* ── REC BADGE ── */
.rec-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 5px 12px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: white;
}
.rec-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.rec-dot.live {
  background: var(--red);
  animation: rec-pulse 0.9s ease-in-out infinite;
  box-shadow: 0 0 8px var(--red);
}
.rec-dot.idle { background: var(--muted); }
@keyframes rec-pulse {
  0%,100% { transform: scale(1.0); opacity: 1.0; box-shadow: 0 0 8px var(--red); }
  50%      { transform: scale(1.3); opacity: 0.7; box-shadow: 0 0 18px var(--red); }
}

/* ── APPROVAL BADGE ── */
.appr {
  border-radius: 4px;
  padding: 5px 10px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: white;
  text-align: center;
  display: inline-block;
}
.appr.ok {
  background: #003A10;
  border: 1px solid var(--green);
  color: var(--green);
  animation: glow-ok 2.5s ease-in-out infinite;
}
@keyframes glow-ok {
  0%,100% { box-shadow: 0 0 6px rgba(0,255,136,0.3); }
  50%      { box-shadow: 0 0 18px rgba(0,255,136,0.6); }
}
.appr.pending { background: #200500; border: 1px solid #5A1500; color: #FF6030; }

/* ── KELVIN SWATCH ── */
.kswatch {
  display: inline-block;
  border-radius: 3px;
  padding: 3px 9px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #111;
  margin: 3px 0 2px 0;
}

/* ── RATIO BADGE sidebar ── */
.ratio-sb {
  border-radius: 4px;
  padding: 8px 12px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: white;
  text-align: center;
  margin: 4px 0;
}
.ratio-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  opacity: 0.75;
  font-weight: 400;
}

/* ── APERTURE READOUT ── */
.fstop-card {
  background: #020A04;
  border: 1px solid #0A2A0A;
  border-radius: 4px;
  padding: 7px 12px;
  text-align: center;
  margin: 5px 0;
}
.fstop-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #204020;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}
.fstop-val {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 30px;
  font-weight: 800;
  color: var(--green);
  text-shadow: 0 0 16px rgba(0,255,136,0.5);
  letter-spacing: 0.04em;
  animation: fstop-breathe 3s ease-in-out infinite;
}
@keyframes fstop-breathe {
  0%,100% { text-shadow: 0 0 14px rgba(0,255,136,0.45); }
  50%      { text-shadow: 0 0 28px rgba(0,255,136,0.75); }
}

/* ── SHUTTER INFO ── */
.shutter-info {
  background: #0A0800;
  border: 1px solid #2A2000;
  border-radius: 3px;
  padding: 4px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--yellow);
  letter-spacing: 0.06em;
  margin: 4px 0;
  text-align: center;
}

/* ── DISTANCE READOUT ── */
.dist-readout {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #3A5080;
  padding: 3px 0;
  line-height: 1.7;
}
.dist-readout b { color: #6080B0; }

/* ── VERSION ── */
.versionstamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--dim);
  text-align: center;
  padding: 3px;
  letter-spacing: 0.1em;
}

/* ── FOOTER ── */
.previz-footer {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--dim);
  text-align: center;
  padding: 12px;
  letter-spacing: 0.10em;
  border-top: 1px solid var(--border);
  margin-top: 8px;
}

/* ── PRINT ── */
@media print {
  [data-testid="stSidebar"],[data-testid="stToolbar"],header,.stButton,.metric-strip { display:none!important; }
  .block-container { padding:0!important; }
  @page { size:landscape; margin:0.4in; }
}
</style>
"""

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def kelvin_to_display(k):
    for mx, color, name in KELVIN_SCALE:
        if k <= mx: return color, name
    return KELVIN_SCALE[-1][1], KELVIN_SCALE[-1][2]

def calculate_fstop(key_intensity, iso, shutter_str, nd_stops, mode):
    if key_intensity <= 0: return "---"
    denom       = SHUTTER_DENOM.get(shutter_str, 100 if mode=="Photography" else 48)
    base_idx    = 5
    key_adj     =  math.log2(max(key_intensity, 0.1) / 100)
    iso_adj     =  math.log2(iso / 800)
    shutter_adj =  math.log2(48 / denom)
    nd_adj      = -nd_stops
    idx = max(0, min(len(FSTOPS)-1, round(base_idx + key_adj + iso_adj + shutter_adj + nd_adj)))
    return f"f/{FSTOPS[int(idx)]}"

def calculate_ratio(key_int, fill_int):
    if fill_int <= 0: return "INF:1","#FF1744","No fill — maximum contrast"
    ratio = key_int / max(fill_int, 0.1)
    for upper, label, color, mood in RATIO_TABLE:
        if ratio < upper: return label, color, mood
    return "16:1","#FF1744","High contrast noir"

def chiaroscuro_index(ratio_label):
    if ratio_label in ["1:1","2:1","3:1"]: return "Low Contrast","#4A90D9"
    elif ratio_label in ["4:1","6:1"]:    return "Medium Contrast","#FF6B00"
    else:                                  return "High Contrast","#FF1744"

def get_suggestion(ratio_label, progress):
    if progress > 0.5 and "High" in chiaroscuro_index(ratio_label)[0]:
        return "Increase fill — reduce shadow crush as camera approaches"
    elif progress < 0.5 and "Low" in chiaroscuro_index(ratio_label)[0]:
        return "Decrease fill — build drama before dolly"
    return ""

def dist(x1,y1,x2,y2): return math.sqrt((x2-x1)**2+(y2-y1)**2)
def ft_m(ft):           return round(ft*0.3048,1)
def rot2d(vx,vy,theta): return (vx*math.cos(theta)-vy*math.sin(theta), vx*math.sin(theta)+vy*math.cos(theta))
def hex_rgb(h):         return int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)

def interpolate_path(sd,ed,sp,ep,pt,prog):
    if pt=="Line":
        return sd+prog*(ed-sd), sp+prog*(ep-sp)
    mid = (sd+ed)/2+2.0; t=prog
    return (1-t)**2*sd+2*(1-t)*t*mid+t**2*ed, sp+t*(ep-sp)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def init_state():
    defaults = {
        "lens":"24mm","cam_pan":0,"cam_dolly":3.0,"fps":24,
        "resolution":"1080p","iso":800,"nd_label":"None (0 stops)","mode":"Video/Cinema",
        "key_intensity":80,"key_kelvin":5600,"key_x":22.0,
        "fill1_on":True,"fill1_intensity":40,"fill1_kelvin":5600,
        "back_on":True,"back_intensity":60,"back_kelvin":5600,
        "fill2_on":False,"fill2_intensity":40,"fill2_kelvin":5600,"fill2_x":26.0,"fill2_y":16.0,
        "talent_name":"Actor","talent_x":15.0,"talent_y":10.0,
        "approved_dp":False,"approved_gaffer":False,"approved_director":False,"approved_at":None,
        "moving_shot_on":False,"start_dolly":3.0,"end_dolly":7.0,
        "start_pan":-15,"end_pan":15,"path_type":"Line",
        "progress":0.0,"auto_play":False,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────
# FLOOR PLAN  — kinetic broadcast look
# ─────────────────────────────────────────────

def draw_floor_plan():
    s    = st.session_state
    W, H = STAGE_W, STAGE_H

    fov         = LENS_FOV[s.lens]
    shutter_str = SHUTTER_BY_FPS.get(s.fps,"1/48") if s.mode=="Video/Cinema" else "1/100"
    nd_stops    = ND_OPTIONS[s.nd_label]
    fstop       = calculate_fstop(s.key_intensity, s.iso, shutter_str, nd_stops, s.mode)
    cam_x       = W / 2
    progress    = s.progress

    if s.moving_shot_on:
        cam_y, cam_pan = interpolate_path(s.start_dolly,s.end_dolly,s.start_pan,s.end_pan,s.path_type,progress)
    else:
        cam_y, cam_pan = s.cam_dolly, s.cam_pan

    key_x, key_y         = s.key_x, cam_y
    tx, ty               = s.talent_x, s.talent_y
    key_color, key_kname = kelvin_to_display(s.key_kelvin)
    fill_int             = ((s.fill1_intensity if s.fill1_on else 0)+
                            (s.fill2_intensity if s.fill2_on else 0))/2
    rl, rc, rm           = calculate_ratio(s.key_intensity, fill_int)
    cam_to_t             = dist(cam_x,cam_y,tx,ty)
    key_to_t             = dist(key_x,key_y,tx,ty)
    chiaro_idx, chiaro_c = chiaroscuro_index(rl)
    suggestion           = get_suggestion(rl, progress)
    kr, kg, kb           = hex_rgb(key_color)

    fig = go.Figure()

    # ── STAGE FLOOR  deep-toned with scanlines ──────────────────────
    FLOOR  = "#050912"
    WALL   = "#0E1830"
    GRID_M = "#090E1A"   # minor grid
    GRID_5 = "#0C1224"   # 5-ft grid
    DIM    = "#1E2A44"
    LBL    = "#2A3A5A"

    fig.add_shape(type="rect",x0=0,y0=0,x1=W,y1=H,
                  fillcolor=FLOOR, line=dict(color=WALL,width=3))

    # Minor grid every 1 ft (very faint)
    for x in range(1,W):
        c = GRID_5 if x%5==0 else GRID_M
        w = 1.2 if x%5==0 else 0.5
        fig.add_shape(type="line",x0=x,y0=0,x1=x,y1=H,line=dict(color=c,width=w))
    for y in range(1,H):
        c = GRID_5 if y%5==0 else GRID_M
        w = 1.2 if y%5==0 else 0.5
        fig.add_shape(type="line",x0=0,y0=y,x1=W,y1=y,line=dict(color=c,width=w))

    # 4th wall — open (glowing blue)
    fig.add_shape(type="line",x0=0,y0=0,x1=W,y1=0,
                  line=dict(color="#0040A0",width=2.5,dash="dot"))

    # Wall labels
    for ann in [
        dict(x=-2,y=H/2,text="WALL 1",textangle=-90,showarrow=False,
             font=dict(size=9,color=LBL,family="JetBrains Mono")),
        dict(x=W/2,y=H+1.6,text="WALL 2 — BACK",showarrow=False,
             font=dict(size=9,color=LBL,family="JetBrains Mono")),
        dict(x=W+2,y=H/2,text="WALL 3",textangle=90,showarrow=False,
             font=dict(size=9,color=LBL,family="JetBrains Mono")),
        dict(x=W/2,y=-0.7,text="4TH WALL — OPEN  ·  CLICK STAGE TO MOVE TALENT",
             showarrow=False,font=dict(size=9,color="#0050C0",family="JetBrains Mono")),
    ]:
        fig.add_annotation(**ann)

    fig.add_annotation(x=W/2,y=H+0.8,text="30 ft  ·  9.1 m",
                       showarrow=False,font=dict(size=8,color=DIM,family="JetBrains Mono"))
    fig.add_annotation(x=-0.7,y=H/2,text="20 ft · 6.1 m",textangle=-90,
                       showarrow=False,font=dict(size=8,color=DIM,family="JetBrains Mono"))

    # ── INVISIBLE CLICK-CAPTURE GRID (1-ft resolution) ──────────────
    # Students click here to move talent — the magic interaction
    cx_g = [float(x) for x in range(0,W+1) for _ in range(0,H+1)]
    cy_g = [float(y) for _ in range(0,W+1) for y in range(0,H+1)]
    fig.add_trace(go.Scatter(
        x=cx_g, y=cy_g, mode="markers",
        marker=dict(size=10, color="rgba(0,0,0,0)", opacity=0),
        showlegend=False,
        hovertemplate="Click to place talent here<br>X: %{x:.0f} ft  ·  Y: %{y:.0f} ft<extra></extra>",
        name="__stage_click__"
    ))

    # ── OVERHEAD LIGHTS  — glowing halos ────────────────────────────
    overhead = [
        (4,   16, "fill1_on","fill1_intensity","fill1_kelvin","FILL 1"),
        (W/2, 18, "back_on", "back_intensity", "back_kelvin", "BACK"),
    ]
    for lx,ly,k_on,k_int,k_k,label in overhead:
        is_on   = getattr(s,k_on)
        lkelvin = getattr(s,k_k)
        lintens = getattr(s,k_int)
        lc, ln  = kelvin_to_display(lkelvin)
        r,g,b   = hex_rgb(lc)

        if is_on:
            # Wide diffuse halo
            ga = max(0.03, lintens/100*0.22)
            for radius, alpha_mult in [(4.5,0.4),(2.8,0.7),(1.5,1.0)]:
                fig.add_shape(type="circle",x0=lx-radius,y0=ly-radius,x1=lx+radius,y1=ly+radius,
                              fillcolor=f"rgba({r},{g},{b},{ga*alpha_mult:.3f})",
                              line=dict(color="rgba(0,0,0,0)",width=0))
            # Fixture body
            fig.add_shape(type="circle",x0=lx-1.0,y0=ly-1.0,x1=lx+1.0,y1=ly+1.0,
                          fillcolor=f"rgba({r},{g},{b},0.55)",line=dict(color=lc,width=2))
            mc = lc
        else:
            fig.add_shape(type="circle",x0=lx-1.0,y0=ly-1.0,x1=lx+1.0,y1=ly+1.0,
                          fillcolor="#0A0E18",line=dict(color="#151E30",width=1.5))
            mc = "#151E30"

        fig.add_trace(go.Scatter(x=[lx],y=[ly],mode="markers",
            marker=dict(size=14,color=mc,symbol="square",line=dict(color="#02050C",width=2)),
            showlegend=False,
            hovertemplate=f"<b>{label}</b><br>{'ON' if is_on else 'OFF'}<br>{lkelvin}K — {ln}<br>Intensity: {lintens}%<extra></extra>"))
        fig.add_annotation(x=lx,y=ly+1.9,text=f"<b>{label}</b><br>{lkelvin}K",
                           showarrow=False,font=dict(size=8,color=lc if is_on else DIM,family="JetBrains Mono"),align="center")

    # Mobile Fill #2
    if s.fill2_on:
        lx,ly   = s.fill2_x, s.fill2_y
        lkelvin = s.fill2_kelvin
        lintens = s.fill2_intensity
        lc,ln   = kelvin_to_display(lkelvin)
        r,g,b   = hex_rgb(lc)
        ga      = max(0.03, lintens/100*0.22)
        for radius, am in [(4.0,0.35),(2.5,0.65),(1.3,1.0)]:
            fig.add_shape(type="circle",x0=lx-radius,y0=ly-radius,x1=lx+radius,y1=ly+radius,
                          fillcolor=f"rgba({r},{g},{b},{ga*am:.3f})",line=dict(color="rgba(0,0,0,0)",width=0))
        fig.add_shape(type="circle",x0=lx-1.0,y0=ly-1.0,x1=lx+1.0,y1=ly+1.0,
                      fillcolor=f"rgba({r},{g},{b},0.55)",line=dict(color=lc,width=2))
        fig.add_trace(go.Scatter(x=[lx],y=[ly],mode="markers",
            marker=dict(size=14,color=lc,symbol="square",line=dict(color="#02050C",width=2)),
            showlegend=False,
            hovertemplate=f"<b>FILL 2 Mobile</b><br>ON<br>{lkelvin}K — {ln}<br>Intensity: {lintens}%<extra></extra>"))
        fig.add_annotation(x=lx,y=ly+1.9,text=f"<b>FILL 2</b><br>{lkelvin}K",
                           showarrow=False,font=dict(size=8,color=lc,family="JetBrains Mono"),align="center")

    # ── KEY LIGHT  — hot beam + fresnel ─────────────────────────────
    key_alpha = max(0.04, s.key_intensity/100*0.30)

    # Staged concentric glow — like a real fresnel spill
    for r_halo, a_mult in [(6.0,0.25),(4.0,0.5),(2.5,0.8)]:
        fig.add_shape(type="circle",x0=key_x-r_halo,y0=key_y-r_halo,x1=key_x+r_halo,y1=key_y+r_halo,
                      fillcolor=f"rgba({kr},{kg},{kb},{key_alpha*a_mult:.3f})",
                      line=dict(color="rgba(0,0,0,0)",width=0))

    # Beam line (hot, thick)
    beam_w = max(1.5, s.key_intensity/100*4.0)
    fig.add_trace(go.Scatter(
        x=[key_x,tx],y=[key_y,ty],mode="lines",
        line=dict(color=f"rgba({kr},{kg},{kb},0.55)",width=beam_w),
        showlegend=False,hoverinfo="skip"))

    # Fresnel dome arc
    ang_to_t = math.atan2(ty-key_y, tx-key_x)
    dome_r   = 1.8
    arc_a    = np.linspace(ang_to_t-math.pi/2, ang_to_t+math.pi/2, 48)
    fig.add_trace(go.Scatter(
        x=[key_x+dome_r*math.cos(a) for a in arc_a],
        y=[key_y+dome_r*math.sin(a) for a in arc_a],
        mode="lines",fill="toself",
        fillcolor=f"rgba({kr},{kg},{kb},0.92)",
        line=dict(color=key_color,width=2.5),
        showlegend=False,
        hovertemplate=f"<b>KEY LIGHT</b><br>{s.key_kelvin}K — {key_kname}<br>Intensity: {s.key_intensity}%<extra></extra>"))
    fig.add_annotation(x=key_x,y=key_y+dome_r+1.5,
                       text=f"<b>KEY</b><br>{s.key_kelvin}K",
                       showarrow=False,font=dict(size=9,color=key_color,family="JetBrains Mono"),align="center")

    # ── CAMERA  — teal tactical ──────────────────────────────────────
    TEAL_CAM = "#00D4CC"
    rc_r,rc_g,rc_b = hex_rgb(TEAL_CAM)

    def add_camera(cy_pos, pan_deg, label="", opacity=1.0, ghost=False):
        pan_rad      = math.radians(pan_deg)
        fov_half_rad = math.radians(fov/2)
        fwd          = (math.sin(pan_rad), math.cos(pan_rad))
        cone_len     = min(14.0, H-cy_pos+0.5)
        ld           = rot2d(fwd[0],fwd[1], fov_half_rad)
        rd           = rot2d(fwd[0],fwd[1],-fov_half_rad)

        # FOV cone with gradient-like layering
        for scale, ao in [(1.0,0.08),(0.6,0.05)]:
            lx2 = cam_x + ld[0]*cone_len*scale; ly2 = cy_pos + ld[1]*cone_len*scale
            rx2 = cam_x + rd[0]*cone_len*scale; ry2 = cy_pos + rd[1]*cone_len*scale
            fig.add_trace(go.Scatter(
                x=[cam_x,lx2,rx2,cam_x],y=[cy_pos,ly2,ry2,cy_pos],
                fill="toself",
                fillcolor=f"rgba({rc_r},{rc_g},{rc_b},{ao*opacity:.3f})",
                line=dict(color=f"rgba({rc_r},{rc_g},{rc_b},{0.4*opacity:.3f})",width=1.5 if scale==1.0 else 0),
                mode="lines",showlegend=False,hoverinfo="skip"))

        # Camera body scale with dolly distance (closer = bigger)
        sf   = max(0.55, 3.0/max(cy_pos,0.5))
        ga   = opacity*(0.35 if ghost else 1.0)
        body = f"rgba({rc_r},{rc_g},{rc_b},{ga:.2f})"

        # Glow behind camera
        if not ghost:
            for gr,gao in [(3.5,0.06),(2.0,0.12)]:
                fig.add_shape(type="circle",
                              x0=cam_x-gr,y0=cy_pos-gr,x1=cam_x+gr,y1=cy_pos+gr,
                              fillcolor=f"rgba({rc_r},{rc_g},{rc_b},{gao*opacity:.3f})",
                              line=dict(color="rgba(0,0,0,0)",width=0))

        fig.add_trace(go.Scatter(x=[cam_x],y=[cy_pos],mode="markers",
            marker=dict(size=28*sf,color=body,symbol="square",
                        line=dict(color=f"rgba(0,240,230,{ga:.2f})",width=2.5)),
            showlegend=False,
            hovertemplate=f"<b>{label}</b><br>{s.lens} | FOV:{fov}deg<br>Pan:{pan_deg}deg<br>Dolly:{cy_pos:.1f}ft<extra></extra>"))

        if label and not ghost:
            fig.add_annotation(x=cam_x+2.6,y=cy_pos+0.5,text=label,showarrow=False,
                               font=dict(size=9,color=TEAL_CAM,family="JetBrains Mono"))

    if not s.moving_shot_on:
        add_camera(cam_y,cam_pan,"MASTER SHOT")
    else:
        # Path trail
        pts    = [interpolate_path(s.start_dolly,s.end_dolly,s.start_pan,s.end_pan,s.path_type,t)
                  for t in np.linspace(0,1,30)]
        py_s, _ = zip(*pts)
        dash    = "dash" if s.path_type=="Line" else "dot"
        fig.add_trace(go.Scatter(
            x=[cam_x]*len(py_s),y=list(py_s),mode="lines",
            line=dict(color=f"rgba({rc_r},{rc_g},{rc_b},0.25)",width=2,dash=dash),
            showlegend=False,hovertemplate="Camera Path<extra></extra>"))
        add_camera(cam_y,        cam_pan,    f"PROGRESS {int(progress*100)}%")
        add_camera(s.start_dolly,s.start_pan,"POS A",opacity=0.4,ghost=True)
        add_camera(s.end_dolly,  s.end_pan,  "POS B",opacity=0.4,ghost=True)

        fig.add_annotation(x=cam_x-3.0,y=cam_y-1.4,
                           text=f"<b>{chiaro_idx}</b><br>{rl}",
                           showarrow=False,bgcolor=chiaro_c,
                           bordercolor=chiaro_c,borderwidth=1,
                           font=dict(size=8,color="white",family="JetBrains Mono"),align="center")
        if suggestion:
            fig.add_annotation(x=W/2,y=H+2.5,text=f"// {suggestion}",showarrow=False,
                               font=dict(size=10,color="#FFE200",family="JetBrains Mono"),align="center")

    # ── TALENT  — hot red crosshair + light spill ────────────────────
    # Key light spill on subject
    spill = min(3.5, max(0.8, s.key_intensity/100*3.5))
    fig.add_shape(type="circle",x0=tx-spill,y0=ty-spill,x1=tx+spill,y1=ty+spill,
                  fillcolor=f"rgba({kr},{kg},{kb},{max(0.03,s.key_intensity/100*0.12):.3f})",
                  line=dict(color="rgba(0,0,0,0)",width=0))

    # Outer targeting ring
    fig.add_shape(type="circle",x0=tx-2.2,y0=ty-2.2,x1=tx+2.2,y1=ty+2.2,
                  fillcolor="rgba(0,0,0,0)",
                  line=dict(color="rgba(255,23,68,0.30)",width=1,dash="dot"))

    # Crosshair lines
    fig.add_trace(go.Scatter(
        x=[tx-2.0,tx+2.0,None,tx,tx],y=[ty,ty,None,ty-2.0,ty+2.0],
        mode="lines",line=dict(color="#FF1744",width=2.5),
        showlegend=False,hoverinfo="skip"))

    # Center dot
    fig.add_trace(go.Scatter(x=[tx],y=[ty],mode="markers",
        marker=dict(size=30,color="rgba(255,23,68,0.08)",symbol="circle",
                    line=dict(color="#FF1744",width=3.0)),
        showlegend=False,
        hovertemplate=(f"<b>{s.talent_name}</b><br>"
                       f"X: {tx:.1f} ft ({ft_m(tx):.1f} m)<br>"
                       f"Y: {ty:.1f} ft ({ft_m(ty):.1f} m)<br>"
                       f"Cam→Talent: {cam_to_t:.1f} ft ({ft_m(cam_to_t):.1f} m)<br>"
                       f"Key→Talent: {key_to_t:.1f} ft ({ft_m(key_to_t):.1f} m)<extra></extra>")))

    fig.add_annotation(x=tx,y=ty+2.6,text=f"<b>{s.talent_name.upper()}</b>",
                       showarrow=False,font=dict(size=12,color="#FF4466",family="Barlow Condensed"),align="center")

    # ── RATIO BADGE (right margin) ───────────────────────────────────
    rr,rg,rb = hex_rgb(rc)
    fig.add_annotation(x=W+0.8,y=H-1,xanchor="left",
        text=f"<b>KEY:FILL</b><br><span style='font-size:22px'><b>{rl}</b></span><br><i style='font-size:9px'>{rm}</i>",
        showarrow=False,bgcolor=rc,bordercolor=rc,
        borderwidth=2,borderpad=10,font=dict(size=10,color="white",family="Barlow Condensed"),align="center")

    # ── LOWER-THIRD TELEMETRY BARS ───────────────────────────────────
    al = f"KEY {s.key_kelvin}K"
    if s.fill1_on: al += f"  ·  F1 {s.fill1_kelvin}K"
    if s.back_on:  al += f"  ·  BACK {s.back_kelvin}K"
    if s.fill2_on: al += f"  ·  F2 {s.fill2_kelvin}K"
    nd_s   = s.nd_label.split("—")[0].strip()
    fps_s  = f"{s.fps}fps {s.resolution}" if s.mode=="Video/Cinema" else "PHOTO"

    rows = [
        ("#0A1428","#4060A0",f"  CAM  {s.lens}  FOV:{fov}d  PAN:{cam_pan}d  DOLLY:{cam_y:.1f}ft  C>T:{cam_to_t:.1f}ft/{ft_m(cam_to_t):.1f}m"),
        ("#081508","#208040",f"  EXP  {fstop}  ISO:{s.iso}  {shutter_str}s  {nd_s}  {fps_s}"),
        ("#0C0A04","#806020",f"  LGT  {al}"),
        ("#150408","#A03030",f"  TLT  {s.talent_name.upper()}  X:{tx:.1f}ft/{ft_m(tx):.1f}m  Y:{ty:.1f}ft/{ft_m(ty):.1f}m  K>T:{key_to_t:.1f}ft/{ft_m(key_to_t):.1f}m"),
    ]
    if s.moving_shot_on:
        rows[0] = ("#0A1428","#4060A0",
                   f"  MOV  {int(progress*100)}%  A({s.start_dolly}ft,{s.start_pan}d)>B({s.end_dolly}ft,{s.end_pan}d)  PATH:{s.path_type}  C>T:{cam_to_t:.1f}ft")

    for i,(bg,tc,txt) in enumerate(rows):
        ry = -2.6-i*1.45
        br2,bg2,bb2 = hex_rgb(bg)
        tr,tg,tb    = hex_rgb(tc)
        fig.add_shape(type="rect",x0=0,y0=ry-0.6,x1=W,y1=ry+0.6,
                      fillcolor=f"rgba({br2},{bg2},{bb2},0.85)",
                      line=dict(color=f"rgba({tr},{tg},{tb},0.6)",width=1))
        # Left accent stripe
        fig.add_shape(type="rect",x0=0,y0=ry-0.6,x1=0.4,y1=ry+0.6,
                      fillcolor=f"rgba({tr},{tg},{tb},0.8)",
                      line=dict(color="rgba(0,0,0,0)",width=0))
        fig.add_annotation(x=0.7,y=ry,text=txt,showarrow=False,
                           font=dict(size=9,color=tc,family="JetBrains Mono"),
                           xanchor="left",align="left")

    # ── LAYOUT ──────────────────────────────────────────────────────
    fig.update_layout(
        margin=dict(l=55,r=175,t=16,b=16),
        paper_bgcolor="#02040A",
        plot_bgcolor="#02040A",
        xaxis=dict(range=[-3,W+11],showgrid=False,zeroline=False,
                   showticklabels=False,scaleanchor="y",scaleratio=1,fixedrange=True),
        yaxis=dict(range=[-12.5,H+4.5],showgrid=False,zeroline=False,
                   showticklabels=False,fixedrange=True),
        height=780, dragmode=False, showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────
# METRIC STRIP
# ─────────────────────────────────────────────

def render_metric_strip(fstop, fov, rl, rc, shutter_str, c_to_t):
    s        = st.session_state
    _, kname = kelvin_to_display(s.key_kelvin)
    fps_lbl  = f"{s.fps} fps" if s.mode=="Video/Cinema" else "stills"
    is_live  = s.auto_play
    live_cls = "live" if is_live else ""

    st.markdown(f"""
<div class="metric-strip">
  <div class="mc gold {live_cls}">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#FF4500,transparent)"></div>
    <div class="mc-label">Aperture</div>
    <div class="mc-val" style="color:#FF4500;text-shadow:0 0 16px rgba(255,69,0,0.55)">{fstop}</div>
    <div class="mc-hint">key drives exp</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#00D4CC,transparent)"></div>
    <div class="mc-label">Lens · FOV</div>
    <div class="mc-val" style="color:#00D4CC;text-shadow:0 0 16px rgba(0,212,204,0.55)">{s.lens}</div>
    <div class="mc-hint">{fov} deg field</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,{rc},transparent)"></div>
    <div class="mc-label">Key:Fill Ratio</div>
    <div class="mc-val" style="color:{rc};text-shadow:0 0 16px {rc}88">{rl}</div>
    <div class="mc-hint">lighting contrast</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#00FF88,transparent)"></div>
    <div class="mc-label">ISO</div>
    <div class="mc-val" style="color:#00FF88;text-shadow:0 0 16px rgba(0,255,136,0.55)">{s.iso}</div>
    <div class="mc-hint">{shutter_str}s shutter</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#FF6B00,transparent)"></div>
    <div class="mc-label">Cam to Talent</div>
    <div class="mc-val" style="color:#FF6B00;text-shadow:0 0 16px rgba(255,107,0,0.55)">{c_to_t:.1f}<span style="font-size:14px;opacity:0.7">ft</span></div>
    <div class="mc-hint">{ft_m(c_to_t):.1f} m</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#FFE200,transparent)"></div>
    <div class="mc-label">Key Temp</div>
    <div class="mc-val" style="color:#FFE200;font-size:20px;text-shadow:0 0 16px rgba(255,226,0,0.55)">{s.key_kelvin}K</div>
    <div class="mc-hint">{kname}</div>
  </div>
  <div class="mc">
    <div class="mc-top" style="background:linear-gradient(90deg,transparent,#8080C0,transparent)"></div>
    <div class="mc-label">Mode</div>
    <div class="mc-val" style="color:#8080C0;font-size:20px">{"CINE" if s.mode=="Video/Cinema" else "PHOTO"}</div>
    <div class="mc-hint">{fps_lbl}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar():
    s = st.session_state
    shutter_str = SHUTTER_BY_FPS.get(s.fps,"1/48") if s.mode=="Video/Cinema" else "1/100"

    st.sidebar.markdown("<div class='versionstamp'>PreViz 4.3 · Open Educational Edition</div>",
                        unsafe_allow_html=True)
    st.sidebar.divider()

    # ── MODE ──────────────────────────────────────
    st.sidebar.subheader("Mode")
    opts    = ["Video/Cinema","Photography"]
    nm      = st.sidebar.selectbox("Mode",opts,index=opts.index(s.mode),label_visibility="collapsed")
    if nm != s.mode: st.session_state.mode=nm; st.rerun()
    with st.sidebar.expander("i  What is Mode?"): st.caption(TIPS["Mode"])
    st.sidebar.divider()

    # ── CAMERA ────────────────────────────────────
    st.sidebar.subheader("Camera")
    nl = st.sidebar.selectbox("Lens",LENS_OPTIONS,index=LENS_OPTIONS.index(s.lens))
    if nl != s.lens: st.session_state.lens=nl; st.rerun()
    with st.sidebar.expander("i  What is FOV?"): st.caption(TIPS["FOV"])

    st.sidebar.checkbox("Enable Moving Shot",key="moving_shot_on")
    if s.moving_shot_on:
        st.sidebar.subheader("Moving Shot")
        st.sidebar.slider("Start Dolly — Pos A (ft)",0.5,9.0,step=0.5,key="start_dolly")
        st.sidebar.slider("Start Pan — Pos A (deg)", -45,45, step=1,  key="start_pan")
        st.sidebar.slider("End Dolly — Pos B (ft)",  0.5,9.0,step=0.5,key="end_dolly")
        st.sidebar.slider("End Pan — Pos B (deg)",   -45,45, step=1,  key="end_pan")
        po  = ["Line","Soft Curve"]
        npt = st.sidebar.selectbox("Path Type",po,index=po.index(s.path_type))
        if npt != s.path_type: st.session_state.path_type=npt; st.rerun()
        st.sidebar.slider("Progress",0.0,1.0,step=0.01,key="progress",
                          format="%d%%",help="Scrub through the move")
        cp,cs = st.sidebar.columns(2)
        with cp:
            if st.button("PLAY",disabled=s.auto_play,use_container_width=True):
                s.auto_play=True; st.rerun()
        with cs:
            if st.button("STOP",disabled=not s.auto_play,use_container_width=True):
                s.auto_play=False; st.rerun()
        if s.auto_play:
            s.progress = min(1.0,s.progress+0.05)
            if s.progress >= 1.0: s.auto_play=False
            time.sleep(0.08); st.rerun()
        with st.sidebar.expander("i  Moving Shot"):  st.caption(TIPS["Moving Shot"])
        with st.sidebar.expander("i  Chiaroscuro"):  st.caption(TIPS["Chiaroscuro"])
    else:
        st.sidebar.slider("Pan (deg)",  -45,45, step=1,  key="cam_pan")
        st.sidebar.slider("Dolly (ft)",  0.5,9.0,step=0.5,key="cam_dolly")
        with st.sidebar.expander("i  What is Pan?"):   st.caption(TIPS["Pan"])
        with st.sidebar.expander("i  What is Dolly?"): st.caption(TIPS["Dolly"])
    with st.sidebar.expander("i  Master Shot"):  st.caption(TIPS["Master Shot"])
    with st.sidebar.expander("i  Fourth Wall"):  st.caption(TIPS["Fourth Wall"])
    with st.sidebar.expander("i  Click Stage"):  st.caption(TIPS["Click Stage"])
    st.sidebar.divider()

    # ── SPECS ─────────────────────────────────────
    st.sidebar.subheader("Specs")
    if s.mode=="Video/Cinema":
        nf = st.sidebar.selectbox("FPS",FPS_OPTIONS,index=FPS_OPTIONS.index(s.fps))
        if nf != s.fps: st.session_state.fps=nf; st.rerun()
        shutter_str = SHUTTER_BY_FPS[s.fps]
        st.sidebar.markdown(
            f"<div class='shutter-info'>SHUTTER {shutter_str}s  ·  180-DEG RULE</div>",
            unsafe_allow_html=True)
        nr = st.sidebar.selectbox("Resolution",RESOLUTION_OPTIONS,index=RESOLUTION_OPTIONS.index(s.resolution))
        if nr != s.resolution: st.session_state.resolution=nr; st.rerun()
        with st.sidebar.expander("i  Shutter Speed"): st.caption(TIPS["Shutter Speed"])

    ni = st.sidebar.selectbox("ISO / Gain",ISO_OPTIONS,index=ISO_OPTIONS.index(s.iso))
    if ni != s.iso: st.session_state.iso=ni; st.rerun()
    with st.sidebar.expander("i  ISO"): st.caption(TIPS["ISO"])

    ndl   = list(ND_OPTIONS.keys())
    nn    = st.sidebar.selectbox("ND Filter",ndl,index=ndl.index(s.nd_label))
    if nn != s.nd_label: st.session_state.nd_label=nn; st.rerun()
    with st.sidebar.expander("i  ND Filter"): st.caption(TIPS["ND Filter"])

    nd_stops = ND_OPTIONS[s.nd_label]
    fstop    = calculate_fstop(s.key_intensity,s.iso,shutter_str,nd_stops,s.mode)
    st.sidebar.markdown(
        f"<div class='fstop-card'><div class='fstop-label'>Suggested Aperture</div>"
        f"<div class='fstop-val'>{fstop}</div></div>",
        unsafe_allow_html=True)
    with st.sidebar.expander("i  f-stop"): st.caption(TIPS["f-stop"])
    st.sidebar.divider()

    # ── KEY LIGHT ─────────────────────────────────
    st.sidebar.subheader("Key Light")
    st.sidebar.slider("Intensity (%)",     0,100,  step=1,  key="key_intensity")
    st.sidebar.slider("Color Temp (K)", 2000,10000,step=100,key="key_kelvin")
    kc,kn = kelvin_to_display(s.key_kelvin)
    st.sidebar.markdown(f"<div class='kswatch' style='background:{kc}'><b>{s.key_kelvin}K</b>  ·  {kn}</div>",
                        unsafe_allow_html=True)
    st.sidebar.slider("Position Left/Right (ft)",2.0,28.0,step=0.5,key="key_x")
    with st.sidebar.expander("i  Key Light"): st.caption(TIPS["Key Light"])
    with st.sidebar.expander("i  Kelvin"):    st.caption(TIPS["Kelvin"])
    st.sidebar.divider()

    # ── OVERHEAD LIGHTS ───────────────────────────
    st.sidebar.subheader("Overhead Lights")
    for lbl,k_on,k_int,k_k in [
        ("Fill 1  (upper left)","fill1_on","fill1_intensity","fill1_kelvin"),
        ("Back Light (Wall 2)", "back_on", "back_intensity", "back_kelvin"),
    ]:
        c1,c2 = st.sidebar.columns([3,1])
        with c1: st.markdown(f"**{lbl}**")
        with c2: st.toggle("",value=getattr(s,k_on),key=k_on)
        if getattr(s,k_on):
            st.sidebar.slider(f"Intensity ({lbl[:4]})",0,100,step=1,key=k_int)
            st.sidebar.slider(f"Kelvin ({lbl[:4]})",2000,10000,step=100,key=k_k)
            lc,ln = kelvin_to_display(getattr(s,k_k))
            st.sidebar.markdown(f"<div class='kswatch' style='background:{lc}'>{getattr(s,k_k)}K · {ln}</div>",
                                unsafe_allow_html=True)

    c1,c2 = st.sidebar.columns([3,1])
    with c1: st.markdown("**Fill 2  (mobile)**")
    with c2: st.toggle("",value=s.fill2_on,key="fill2_on")
    if s.fill2_on:
        with st.sidebar.expander("Fill 2 Settings"):
            st.slider("Intensity (%)",0,100,step=1,key="fill2_intensity")
            st.slider("Color Temp (K)",2000,10000,step=100,key="fill2_kelvin")
            lc,ln = kelvin_to_display(s.fill2_kelvin)
            st.markdown(f"<div class='kswatch' style='background:{lc}'>{s.fill2_kelvin}K · {ln}</div>",
                        unsafe_allow_html=True)
            st.slider("Pos X (ft)",2.0,28.0,step=0.5,key="fill2_x")
            st.slider("Pos Y (ft)",2.0,18.0,step=0.5,key="fill2_y")

    with st.sidebar.expander("i  Fill Light"): st.caption(TIPS["Fill Light"])
    with st.sidebar.expander("i  Back Light"): st.caption(TIPS["Back Light"])
    st.sidebar.divider()

    # ── LIGHT RATIO ───────────────────────────────
    st.sidebar.subheader("Light Ratio")
    rl,rc2,rm = calculate_ratio(
        s.key_intensity,
        ((s.fill1_intensity if s.fill1_on else 0)+
         (s.fill2_intensity if s.fill2_on else 0))/2)
    st.sidebar.markdown(
        f"<div class='ratio-sb' style='background:{rc2}'>"
        f"KEY : FILL  {rl}<br><span class='ratio-sub'>{rm}</span></div>",
        unsafe_allow_html=True)
    with st.sidebar.expander("i  Light Ratio"): st.caption(TIPS["Light Ratio"])
    st.sidebar.divider()

    # ── TALENT ────────────────────────────────────
    st.sidebar.subheader("Talent")
    st.sidebar.text_input("Name",key="talent_name")
    txv = st.sidebar.slider("Left / Right (ft)",2.0,28.0,value=float(s.talent_x),step=0.5)
    s.talent_x = txv
    tyv = st.sidebar.slider("Depth from Wall 4 (ft)",2.0,18.0,value=float(s.talent_y),step=0.5)
    s.talent_y = tyv
    c2t = dist(STAGE_W/2,s.cam_dolly,txv,tyv)
    k2t = dist(s.key_x,tyv,txv,tyv)
    st.sidebar.markdown(
        f"<div class='dist-readout'>Cam to Talent: <b>{c2t:.1f} ft / {ft_m(c2t):.1f} m</b><br>"
        f"Key to Talent: <b>{k2t:.1f} ft / {ft_m(k2t):.1f} m</b></div>",
        unsafe_allow_html=True)
    if st.sidebar.button("Reset to Center",use_container_width=True):
        s.talent_x, s.talent_y = 15.0, 10.0; st.rerun()
    st.sidebar.divider()

    # ── APPROVAL GATE ─────────────────────────────
    st.sidebar.subheader("Approval Gate")
    st.sidebar.checkbox("DP Approved",      key="approved_dp")
    st.sidebar.checkbox("Gaffer Approved",  key="approved_gaffer")
    st.sidebar.checkbox("Director Approved",key="approved_director")
    all_ok = s.approved_dp and s.approved_gaffer and s.approved_director
    if all_ok and not s.approved_at:
        s.approved_at = datetime.now().strftime("%Y-%m-%d  %H:%M")
    elif not all_ok:
        s.approved_at = None
    if all_ok:
        st.sidebar.markdown(
            f"<div class='appr ok'>ALL APPROVED  ·  {s.approved_at}</div>",
            unsafe_allow_html=True)
        st.sidebar.button("Print Floor Plan",use_container_width=True)
        st.sidebar.caption("Cmd/Ctrl+P → Landscape")
    else:
        st.sidebar.button("Print Floor Plan",disabled=True,use_container_width=True)
        rem = [n for c,n in [(not s.approved_dp,"DP"),(not s.approved_gaffer,"Gaffer"),
               (not s.approved_director,"Director")] if c]
        st.sidebar.markdown(
            f"<div class='appr pending'>WAITING: {' · '.join(rem)}</div>",
            unsafe_allow_html=True)
    with st.sidebar.expander("i  Approval Gate"): st.caption(TIPS["Approval Gate"])


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title=f"PreViz {PREVIZ_VERSION} — Open Educational Edition",
        page_icon="🎬", layout="wide", initial_sidebar_state="expanded")

    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    render_sidebar()

    s = st.session_state

    # ── Derived values for header/strip ──
    shutter_str = SHUTTER_BY_FPS.get(s.fps,"1/48") if s.mode=="Video/Cinema" else "1/100"
    nd_stops    = ND_OPTIONS[s.nd_label]
    fstop       = calculate_fstop(s.key_intensity,s.iso,shutter_str,nd_stops,s.mode)
    fov         = LENS_FOV[s.lens]
    fill_int    = ((s.fill1_intensity if s.fill1_on else 0)+
                   (s.fill2_intensity if s.fill2_on else 0))/2
    rl, rc, _   = calculate_ratio(s.key_intensity, fill_int)
    c_to_t      = dist(STAGE_W/2,s.cam_dolly,s.talent_x,s.talent_y)
    all_ok      = s.approved_dp and s.approved_gaffer and s.approved_director
    is_live     = s.auto_play

    # ── HEADER ──────────────────────────────────
    c_title, c_rec, c_badge = st.columns([6,2,1])
    with c_title:
        st.markdown(
            f"<p class='pv-title'>PreViz {PREVIZ_VERSION}</p>"
            f"<p class='pv-sub'>Phase 1 · Studio Lighting · 30×20 ft Stage · Three-Point Setup</p>"
            f"<p class='pv-click-hint'>>>> Click anywhere on stage floor to move talent instantly</p>",
            unsafe_allow_html=True)
    with c_rec:
        dot_cls   = "live" if is_live else "idle"
        rec_label = "RECORDING" if is_live else "STANDBY"
        st.markdown(
            f"<div class='rec-badge' style='margin-top:12px'>"
            f"<span class='rec-dot {dot_cls}'></span>{rec_label}</div>",
            unsafe_allow_html=True)
    with c_badge:
        cls       = "ok" if all_ok else "pending"
        badge_txt = "APPROVED" if all_ok else "PENDING"
        st.markdown(
            f"<div class='appr {cls}' style='margin-top:14px'>{badge_txt}</div>",
            unsafe_allow_html=True)

    # ── METRIC STRIP ────────────────────────────
    render_metric_strip(fstop, fov, rl, rc, shutter_str, c_to_t)

    # ── FLOOR PLAN + CLICK-TO-PLACE ─────────────
    fig = draw_floor_plan()
    chart_event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="previz_stage",
    )

    # Handle click — move talent to clicked stage position
    if chart_event and hasattr(chart_event,"selection") and chart_event.selection:
        pts = getattr(chart_event.selection,"points",[])
        for pt in pts:
            x_click = pt.get("x", None)
            y_click = pt.get("y", None)
            if x_click is not None and y_click is not None:
                # Only move talent if click is inside stage bounds
                if 0.5 <= x_click <= STAGE_W-0.5 and 0.5 <= y_click <= STAGE_H-0.5:
                    st.session_state.talent_x = round(float(x_click), 1)
                    st.session_state.talent_y = round(float(y_click), 1)
                    st.rerun()

    # ── FOOTER ──────────────────────────────────
    st.markdown(
        "<div class='previz-footer'>"
        "Developed by Eduardo Carmona, MFA — CSUDH · LMU  ·  "
        "GNU GPL v3.0  ·  "
        "Free for every student — from Los Angeles to Lima to Windhoek."
        "</div>",
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
