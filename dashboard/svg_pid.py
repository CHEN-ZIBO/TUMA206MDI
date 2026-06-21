"""SVG P&ID builder for the SCHEMATIC page.

Pure functions that return SVG markup strings. Each equipment builder accepts
live data and returns a <g> group with shapes, labels, and animated elements.
The main entry point is build_pid_svg() which composes the full diagram.
"""

from __future__ import annotations
from typing import Dict
import config

# ── Color palette (matches dashboard theme) ──────────────────────────
BG = "#0d1117"
CARD = "#161b22"
BDR = "#30363d"
TXT = "#c9d1d9"
TXT2 = "#8b949e"
ACC = "#58a6ff"
GRN = "#3fb950"
ORN = "#d2991d"
RED = "#f85149"
CYA = "#39d2c0"
HOT = "#f0883e"
COLD = "#58a6ff"
LIQUID = "#3a7bd5"
STEEL = "#2d333b"


def _status_color(ok: bool, warn: bool = False) -> str:
    if not ok and warn:
        return ORN
    if not ok:
        return RED
    return GRN


def _glow(cls: str) -> str:
    """Return SVG filter ID + glow color for a state class."""
    return {
        "active": f'filter="url(#glow-grn)" stroke="{GRN}"',
        "warn": f'filter="url(#glow-orn)" stroke="{ORN}"',
        "fault": f'filter="url(#glow-red)" stroke="{RED}"',
    }.get(cls, f'stroke="{BDR}"')


def _pipe(x1: float, y1: float, x2: float, y2: float, flowing: bool) -> str:
    color = ACC if flowing else BDR
    width = 5 if flowing else 4
    dash = "8,4" if flowing else "none"
    cls = 'class="pipe-flow"' if flowing else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" '
            f'stroke-linecap="round" {cls}/>')

_ANIM_CSS = """
@keyframes flow-dash { to { stroke-dashoffset: -24; } }
@keyframes pump-spin { to { transform: rotate(360deg); } }
@keyframes heat-pulse { 0%,100%{opacity:0.3} 50%{opacity:0.8} }
@keyframes fill-blink { 0%,100%{opacity:1} 50%{opacity:0.5} }
@keyframes belt-move { to { transform: translateX(16px); } }
@keyframes glow-pulse-green { 0%,100%{opacity:0.4} 50%{opacity:0.9} }
@keyframes glow-pulse-red { 0%,100%{opacity:0.4} 50%{opacity:0.9} }
.pipe-flow { animation: flow-dash 0.6s linear infinite; }
.pump-impeller { animation: pump-spin 0.8s linear infinite; transform-origin: center; }
.heat-glow { animation: heat-pulse 1.2s ease-in-out infinite; }
.fill-active { animation: fill-blink 0.6s ease-in-out infinite; }
.belt-bottle { animation: belt-move 0.5s linear infinite; }
"""

FILTERS_SVG = f"""
<defs>
  <filter id="glow-grn"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{GRN}" flood-opacity="0.5"/></filter>
  <filter id="glow-orn"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{ORN}" flood-opacity="0.5"/></filter>
  <filter id="glow-red"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{RED}" flood-opacity="0.6"/></filter>
  <filter id="glow-acc"><feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{ACC}" flood-opacity="0.4"/></filter>
  <linearGradient id="grad-tank" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%" stop-color="{LIQUID}" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="{ACC}" stop-opacity="0.5"/>
  </linearGradient>
  <linearGradient id="grad-hot" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{HOT}" stop-opacity="0.7"/>
    <stop offset="100%" stop-color="{RED}" stop-opacity="0.9"/>
  </linearGradient>
  <linearGradient id="grad-cool" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{COLD}" stop-opacity="0.4"/>
    <stop offset="100%" stop-color="{COLD}" stop-opacity="0.8"/>
  </linearGradient>
</defs>
"""

# ─────────────────────────────────────────────────────────────────────
# SVG equipment builders
# ─────────────────────────────────────────────────────────────────────

def tank_svg(x: float, y: float, w: float, h: float, level_pct: float,
             label: str, value: str, sub: str, cls: str = "active",
             man: bool = False) -> str:
    """Vertical tank with liquid fill that moves with level_pct."""
    fill_h = max(4, (level_pct / 100.0) * h * 0.72)
    fill_y = y + 28 + (h * 0.72 - fill_h)
    glow = _glow(cls)
    m = ('<rect x="%.0f" y="%.0f" width="14" height="10" rx="2" fill="%s" '
         'stroke="%s" stroke-width="1" opacity="0.9"/>'
         '<text x="%.0f" y="%.0f" text-anchor="middle" fill="#000" '
         'font-size="7" font-weight="800">M</text>') % (
        x + 2, y + 2, ORN, ORN, x + 9, y + 10) if man else ""
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{STEEL}" {glow} stroke-width="2"/>'
        f'<rect x="{x+6}" y="{fill_y}" width="{w-12}" height="{fill_h}" rx="4" '
        f'  fill="url(#grad-tank)"/>'
        f'{m}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">{label}</text>'
        f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" fill="{TXT}" '
        f'  font-size="14" font-weight="700">{value}</text>'
        f'<text x="{x+w/2}" y="{y+h-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">{sub}</text>'
        f'</g>'
    )


def pump_svg(x: float, y: float, w: float, h: float, label: str, value: str,
             sub: str, cls: str = "active", man: bool = False) -> str:
    """Centrifugal pump: circle + rotating impeller triangle."""
    cx, cy, r = x + w/2, y + 24, 18
    anim = 'class="pump-impeller"' if cls == "active" else ""
    glow = _glow(cls)
    m = ('<rect x="%.0f" y="%.0f" width="14" height="10" rx="2" fill="%s" '
         'stroke="%s" stroke-width="1" opacity="0.9"/>'
         '<text x="%.0f" y="%.0f" text-anchor="middle" fill="#000" '
         'font-size="7" font-weight="800">M</text>') % (
        x + 2, y + 2, ORN, ORN, x + 9, y + 10) if man else ""
    return (
        f'<g>'
        f'<rect x="{x}" y="{y+32}" width="{w}" height="{h-32}" rx="6" fill="{STEEL}" '
        f'  {glow} stroke-width="2"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{STEEL}" stroke="{ACC if cls=="active" else BDR}" '
        f'  stroke-width="2.5" {"" if cls=="active" else ""}/>'
        f'<polygon points="{cx},{cy-10} {cx+10},{cy+6} {cx-10},{cy+6}" '
        f'  fill="{ACC if cls=="active" else TXT2}" {anim}/>'
        f'{m}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">{label}</text>'
        f'<text x="{x+w/2}" y="{y+h-10}" text-anchor="middle" fill="{TXT}" '
        f'  font-size="12" font-weight="700">{value}</text>'
        f'<text x="{x+w/2}" y="{y+h+4}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">{sub}</text>'
        f'</g>'
    )


def pasteurizer_svg(x: float, y: float, w: float, h: float, temp: float,
                    heater_pct: float, cls: str = "active", man: bool = False) -> str:
    """Pasteurizer with heating element bars and temperature display."""
    glow = _glow(cls)
    # Heating element bars
    bars = ""
    n_bars = 5
    bar_w = (w - 20) / n_bars - 4
    heat_alpha = heater_pct / 100.0
    for i in range(n_bars):
        bx = x + 10 + i * (bar_w + 4)
        by = y + h/2 - 8
        bh = 16
        bar_fill = f"rgba(240,136,62,{0.3+0.7*heat_alpha})"
        bars += (f'<rect x="{bx:.0f}" y="{by:.0f}" width="{bar_w:.0f}" height="{bh:.0f}" '
                 f'rx="2" fill="{bar_fill}" class="{"heat-glow" if cls=="active" else ""}"/>')
    m = ('<rect x="%.0f" y="%.0f" width="14" height="10" rx="2" fill="%s" '
         'stroke="%s" stroke-width="1" opacity="0.9"/>'
         '<text x="%.0f" y="%.0f" text-anchor="middle" fill="#000" '
         'font-size="7" font-weight="800">M</text>') % (
        x + 2, y + 2, ORN, ORN, x + 9, y + 10) if man else ""
    tcolor = GRN if config.PASTEUR_SAFE_MIN <= temp <= config.PASTEUR_SAFE_MAX else (ORN if abs(temp - config.PASTEUR_SETPOINT) < 5 else RED)
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{STEEL}" {glow} stroke-width="2"/>'
        f'{bars}'
        f'{m}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">PASTEURIZER</text>'
        f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" fill="{tcolor}" '
        f'  font-size="14" font-weight="700">{temp:.1f}°C</text>'
        f'<text x="{x+w/2}" y="{y+h-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">Heater {heater_pct:.0f}% &middot; SP {config.PASTEUR_SETPOINT:.0f}°C</text>'
        f'</g>'
    )


def cooler_svg(x: float, y: float, w: float, h: float, temp: float,
               valve_pct: float, cls: str = "active", man: bool = False) -> str:
    """Cooler HX with cooling coil lines and temperature display."""
    glow = _glow(cls)
    # Cooling coil — wavy line
    coil_alpha = valve_pct / 100.0
    coil = ""
    cx_base = x + 10
    cy_base = y + h/2
    for i in range(6):
        coil_x = cx_base + i * (w - 20) / 5
        coil_y = cy_base + (-5 if i % 2 == 0 else 5)
        coil += (f'<circle cx="{coil_x:.0f}" cy="{coil_y:.0f}" r="4" '
                 f'fill="{COLD}" opacity="{0.3+0.7*coil_alpha}"/>')
    m = ('<rect x="%.0f" y="%.0f" width="14" height="10" rx="2" fill="%s" '
         'stroke="%s" stroke-width="1" opacity="0.9"/>'
         '<text x="%.0f" y="%.0f" text-anchor="middle" fill="#000" '
         'font-size="7" font-weight="800">M</text>') % (
        x + 2, y + 2, ORN, ORN, x + 9, y + 10) if man else ""
    tcolor = GRN if temp <= config.COOLER_MAX_BOTTLING else ORN
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{STEEL}" {glow} stroke-width="2"/>'
        f'{coil}'
        f'<line x1="{x+10}" y1="{cy_base:.0f}" x2="{x+w-10}" y2="{cy_base:.0f}" '
        f'  stroke="{COLD}" stroke-width="1" opacity="{0.2+0.5*coil_alpha}" stroke-dasharray="3,3"/>'
        f'{m}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">COOLER</text>'
        f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" fill="{tcolor}" '
        f'  font-size="14" font-weight="700">{temp:.1f}°C</text>'
        f'<text x="{x+w/2}" y="{y+h-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">Valve {valve_pct:.0f}% &middot; Tgt {config.COOLER_SETPOINT:.0f}°C</text>'
        f'</g>'
    )


def filler_svg(x: float, y: float, w: float, h: float, nozzle_status: list,
               fill_progress: float, fill_phase: str, flow: float,
               cls: str = "active") -> str:
    """Inline 4-nozzle filler. Each nozzle drawn as a column with fill level."""
    glow = _glow(cls)
    n = len(nozzle_status)
    nw = (w - 20) / n - 6  # per-nozzle width
    nozzles = ""
    for i in range(n):
        nx = x + 10 + i * (nw + 6)
        ny = y + h * 0.35
        nh = h * 0.55
        ns = nozzle_status[i] if i < len(nozzle_status) else 0
        # Bottle outline
        nozzles += f'<rect x="{nx:.0f}" y="{ny:.0f}" width="{nw:.0f}" height="{nh:.0f}" rx="3" fill="none" stroke="{ACC if ns>0 else BDR}" stroke-width="1.5"/>'
        # Fill level inside bottle
        fill_level = fill_progress if ns == 1 else (1.0 if ns == 2 else 0.0)
        if fill_level > 0:
            fh = fill_level * nh
            fy = ny + nh - fh
            nozzles += f'<rect x="{nx+2:.0f}" y="{fy:.0f}" width="{nw-4:.0f}" height="{fh:.0f}" rx="1" fill="{LIQUID}" opacity="0.8"/>'
        # Fill stream from top (when filling)
        if ns == 1:
            nozzles += (f'<line x1="{nx+nw/2:.0f}" y1="{ny-8:.0f}" x2="{nx+nw/2:.0f}" y2="{ny+nh*fill_level:.0f}" '
                        f'stroke="{ACC}" stroke-width="1.5" stroke-dasharray="4,4" class="fill-active"/>')
        # Nozzle head dot
        dot_color = GRN if ns == 2 else (ACC if ns == 1 else BDR)
        nozzles += f'<circle cx="{nx+nw/2:.0f}" cy="{ny-10:.0f}" r="3" fill="{dot_color}"/>'
        # Label
        nozzles += f'<text x="{nx+nw/2:.0f}" y="{ny+nh+12:.0f}" text-anchor="middle" fill="{TXT2}" font-size="7">N{i+1}</text>'

    ph_color = ACC if fill_phase == "FILL" else TXT2
    prog_pct = int(fill_progress * 100)
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{STEEL}" {glow} stroke-width="2"/>'
        f'{nozzles}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">FILLER x4</text>'
        f'<text x="{x+w/2}" y="{y+h-5}" text-anchor="middle" fill="{ph_color}" '
        f'  font-size="9" font-weight="600">{fill_phase} {prog_pct}%</text>'
        f'<text x="{x+w/2}" y="{y+h+10}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">Flow {flow:.1f} L/min &middot; 500mL/bottle</text>'
        f'</g>'
    )


def conveyor_svg(x: float, y: float, w: float, h: float, buffer_level: int,
                 buffer_max: int, completed: int, conv_pct: float,
                 cls: str = "active") -> str:
    """Conveyor belt with moving bottles on top."""
    glow = _glow(cls)
    # Belt surface
    belt_y = y + h * 0.6
    belt_h = 10
    # Roller circles
    rollers = ""
    for rx in [x + 15, x + w - 15]:
        rollers += f'<circle cx="{rx:.0f}" cy="{belt_y+belt_h/2:.0f}" r="6" fill="{STEEL}" stroke="{BDR}" stroke-width="1.5"/>'
    # Bottles on the belt
    bottles = ""
    btls_to_show = min(buffer_level, 18)
    btl_spacing = (w - 40) / max(btls_to_show, 1)
    btl_r = 4.5
    for i in range(btls_to_show):
        bx = x + 20 + i * btl_spacing
        by = belt_y - btl_r - 2
        bottles += (f'<rect x="{bx-btl_r/2:.0f}" y="{by-btl_r:.0f}" width="{btl_r:.0f}" '
                    f'height="{btl_r*2:.0f}" rx="2" fill="{LIQUID}" opacity="0.7" '
                    f'class="{"belt-bottle" if cls=="active" else ""}"/>')
    # Buffer count text
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{STEEL}" {glow} stroke-width="2"/>'
        f'<rect x="{x+10}" y="{belt_y:.0f}" width="{w-20}" height="{belt_h:.0f}" rx="3" fill="#1c2128" stroke="{BDR}" stroke-width="1"/>'
        f'{rollers}'
        f'{bottles}'
        f'<text x="{x+w/2}" y="{y-6}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="9" font-weight="600">CONVEYOR/CAPPER</text>'
        f'<text x="{x+w/2}" y="{y+h-5}" text-anchor="middle" fill="{TXT}" '
        f'  font-size="12" font-weight="700">Done: {completed}</text>'
        f'<text x="{x+w/2}" y="{y+h+10}" text-anchor="middle" fill="{TXT2}" '
        f'  font-size="8">Belt {buffer_level}/{buffer_max} &middot; Conv {conv_pct:.0f}%</text>'
        f'</g>'
    )


# ─────────────────────────────────────────────────────────────────────
# Full P&ID composition
# ─────────────────────────────────────────────────────────────────────

def build_pid_svg(data: Dict) -> str:
    """Compose the complete process flow P&ID as an inline SVG string.

    Layout (viewBox 0 0 1150 280):
      [Inlet Valve+Pump] → [Raw Tank] → [Feed Pump] → [Pasteurizer]
      → [Cooler] → [Filler x4] → [Conveyor/Capper]
    Horizontal pipeline with flow animation.
    """
    # Unpack data
    level = float(data.get("tank_level", 0))
    temp = float(data.get("pasteur_temp", 0))
    cool = float(data.get("cooler_temp", 0))
    flow = float(data.get("flow_rate", 0))
    belt = int(data.get("conveyor_queue", 0))
    belt_max = int(data.get("conveyor_max", config.CONVEYOR_MAX_BOTTLES))
    ic = float(data.get("inlet_valve_cmd", 0))
    pc = float(data.get("pump_cmd", 0))
    hc = float(data.get("heater_power_cmd", 0))
    cc = float(data.get("cooling_valve_cmd", 0))
    cvc = float(data.get("conveyor_cmd", 0))
    pf = int(data.get("pump_feedback", 0))
    fc = int(data.get("fill_valve_cmd", 0))
    bp = int(data.get("bottle_present", 0))
    fcode = int(data.get("fault_status", 0))
    plc = data.get("plc_state", "IDLE")
    nozzle_status = data.get("nozzle_status", [0, 0, 0, 0])
    fill_phase = data.get("fill_phase", "INDEX")
    fill_progress = float(data.get("fill_progress", 0.0))
    completed = int(data.get("bottles_completed", 0))
    man = set(data.get("_manuals", []))

    running = plc in ("RUNNING", "STARTING")
    flow_ok = running and pc > 0 and pf == 1
    s1_ok = config.TANK_LEVEL_LOW <= level <= config.TANK_LEVEL_HIGH
    s2_ok = config.PASTEUR_SAFE_MIN <= temp <= config.PASTEUR_SAFE_MAX
    s3_ok = cool <= config.COOLER_MAX_BOTTLING
    s4_ok = fc and bp

    def eq_cls(ok, warn_cond=False):
        if not running:
            return "idle"
        if not ok:
            return "warn" if warn_cond else "fault"
        return "active"

    # Equipment positions (x, y, width, height)
    # Row: icon on top, data below
    Y_TOP = 18
    H_EQ = 75

    # Layout: compact horizontal strip
    positions = [
        # (x, w, type)
        (8, 70, "tank"),       # Raw Tank (S1)
        (90, 80, "pasteur"),   # Pasteurizer (S2)
        (180, 70, "cooler"),    # Cooler (S3)
        (260, 95, "filler"),    # Filler x4 (S4)
        (365, 105, "conveyor"), # Conveyor/Capper (S5)
    ]

    # Assemble SVG
    svg_parts = [f'<svg viewBox="0 0 480 130" xmlns="http://www.w3.org/2000/svg" '
                 f'style="width:100%;background:{BG};">']
    svg_parts.append(FILTERS_SVG)
    svg_parts.append(f"<style>{_ANIM_CSS}</style>")

    # Pipes between equipment
    pipe_y = Y_TOP + H_EQ / 2
    for i in range(len(positions) - 1):
        x1 = positions[i][0] + positions[i][1] + 2
        x2 = positions[i + 1][0] - 2
        svg_parts.append(_pipe(x1, pipe_y, x2, pipe_y, flow_ok))

    # Title
    svg_parts.append(
        f'<text x="240" y="10" text-anchor="middle" fill="{TXT}" '
        f'font-size="10" font-weight="700" letter-spacing="1">PROCESS FLOW &mdash; '
        f'{plc.upper()}</text>')

    # S1: Raw Tank
    pos = positions[0]
    svg_parts.append(tank_svg(
        pos[0], Y_TOP, pos[1], H_EQ, level,
        "RAW TANK", f"{level:.0f}%",
        f"In {ic:.0f}% / Pump {pc:.0f}%",
        eq_cls(s1_ok),
        "inlet_valve_cmd" in man or "pump_cmd" in man))

    # S2: Pasteurizer
    pos = positions[1]
    svg_parts.append(pasteurizer_svg(
        pos[0], Y_TOP, pos[1], H_EQ, temp, hc,
        eq_cls(s2_ok),
        "heater_power_cmd" in man))

    # S3: Cooler
    pos = positions[2]
    svg_parts.append(cooler_svg(
        pos[0], Y_TOP, pos[1], H_EQ, cool, cc,
        eq_cls(s3_ok),
        "cooling_valve_cmd" in man))

    # S4: Filler
    pos = positions[3]
    svg_parts.append(filler_svg(
        pos[0], Y_TOP, pos[1], H_EQ, nozzle_status, fill_progress, fill_phase, flow,
        eq_cls(s4_ok)))

    # S5: Conveyor
    pos = positions[4]
    svg_parts.append(conveyor_svg(
        pos[0], Y_TOP, pos[1], H_EQ, belt, belt_max, completed, cvc,
        eq_cls(cvc > 0)))

    # Top-right: KPI summary strip
    kpi_x, kpi_y = 260, 10
    kpis = [
        (f"Flow: {flow:.1f} L/min", ACC if flow > 0 else TXT2),
        (f"Tank: {level:.0f}%", GRN if s1_ok else ORN),
        (f"Temp: {temp:.1f}°C", GRN if s2_ok else RED),
        (f"Completed: {completed}", CYA if completed > 0 else TXT2),
    ]
    kpi_text = "  |  ".join(
        f'<tspan fill="{c}">{t}</tspan>' for t, c in kpis)
    svg_parts.append(
        f'<text x="{kpi_x}" y="{kpi_y}" font-size="8" fill="{TXT2}">{kpi_text}</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
