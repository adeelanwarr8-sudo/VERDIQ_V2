"""Vector icons and the illustrative site plan used by the UI prototype.

All geometry and values are illustrative; nothing here reads DXF data.
"""
from __future__ import annotations

import math
from html import escape

import streamlit as st

GREEN = "#0f7a43"

# ---------------------------------------------------------------- icons
_ICON_PATHS = {
    "sprout": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "user": '<circle cx="12" cy="8" r="4.5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "tree": '<path d="M8 19a4 4 0 0 1-2.24-7.32A3.5 3.5 0 0 1 9 6.03V6a3 3 0 1 1 6 0v.04a3.5 3.5 0 0 1 3.24 5.65A4 4 0 0 1 16 19Z"/><path d="M12 19v3"/>',
    "cloud_up": '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/>',
    "pointer": '<path d="m4 4 7 16 2.5-7 7-2.5L4 4z"/>',
    "hand": '<path d="M18 11V6a2 2 0 0 0-4 0"/><path d="M14 10V4a2 2 0 0 0-4 0v2"/><path d="M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-6-2.3l-3.6-3.6a2 2 0 0 1 2.8-2.8L7 15"/>',
    "zoom_in": '<circle cx="11" cy="11" r="7.5"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6M8 11h6"/>',
    "zoom_out": '<circle cx="11" cy="11" r="7.5"/><path d="m21 21-4.3-4.3"/><path d="M8 11h6"/>',
    "fullscreen": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    "pencil": '<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "close": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "book": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
}


def icon(name: str, size: int = 20, color: str = "currentColor", stroke: float = 2) -> str:
    return (f'<svg class="v-ic" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{_ICON_PATHS[name]}</svg>')


def check_badge(size: int = 30) -> str:
    return (f'<svg class="v-ic" width="{size}" height="{size}" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#11903f"/>'
            '<path d="m7 12.5 3.2 3.2L17 9" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ---------------------------------------------------------------- plan geometry
# The plot is drawn in a local 300 x 230 grid, then mapped onto a rotated
# parallelogram so it reads like the oblique CAD view in the reference image.
_ORIGIN = (262.0, 22.0)
_U = (243 / 300, 88 / 300)      # local x axis
_V = (-128 / 230, 176 / 230)    # local y axis


def _pt(x: float, y: float) -> tuple[float, float]:
    return (_ORIGIN[0] + x * _U[0] + y * _V[0], _ORIGIN[1] + x * _U[1] + y * _V[1])


def _poly(pts, fill, stroke="none", sw=0, extra="") -> str:
    p = " ".join(f"{a:.1f},{b:.1f}" for a, b in (_pt(x, y) for x, y in pts))
    return f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'


def _rect(x, y, w, h, fill, stroke="none", sw=0, extra="") -> str:
    return _poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw, extra)


def _ring(x, y, w, h, step):
    """Points spaced around the perimeter of a local rectangle."""
    per, pts, d = 2 * (w + h), [], 0.0
    while d < per - 1:
        if d < w:
            pts.append((x + d, y))
        elif d < w + h:
            pts.append((x + w, y + d - w))
        elif d < 2 * w + h:
            pts.append((x + w - (d - w - h), y + h))
        else:
            pts.append((x, y + h - (d - 2 * w - h)))
        d += step
    return pts


C_PLANTED, C_PAVING, C_SEALED, C_BUILD, C_TREE = "#cfeac0", "#eadfd2", "#d9cbb8", "#a99f92", "#14963f"

TREES = (_ring(28, 18, 86, 70, 22.5) + _ring(24, 112, 82, 76, 22.0)
         + [(150, 125), (172, 128), (196, 205), (230, 212), (262, 116), (270, 140), (248, 182),
            (276, 205), (130, 210), (205, 117), (180, 102), (142, 100)])


def plan_svg(improved: bool = False, layers_panel: bool = True) -> str:
    g = []
    # plot: sealed outer band, paving court, planted areas
    g.append(_rect(-8, -8, 316, 246, C_SEALED, "#8e8576", 1.2))
    g.append(_rect(8, 8, 284, 214, C_PAVING))
    g.append(_rect(28, 18, 86, 70, C_PLANTED, extra='rx="6"'))
    g.append(_rect(24, 112, 82, 76, C_PLANTED))
    g.append(_rect(30, 90, 78, 20, "#efe8de"))
    for x, y, w, h in [(138, 22, 34, 22), (196, 34, 26, 44), (140, 58, 30, 40), (232, 92, 32, 30),
                       (144, 142, 30, 48), (208, 132, 26, 40), (246, 152, 30, 40), (182, 180, 34, 22)]:
        g.append(_rect(x, y, w, h, C_BUILD))
    g.append(_rect(-8, -8, 316, 246, "none", "#7a7266", 1.4))
    # shrub blobs
    for x, y, r in [(160, 116, 7), (124, 164, 6), (190, 160, 5), (260, 210, 6), (118, 205, 6)]:
        cx, cy = _pt(x, y)
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#9fd68a"/>')
    if improved:
        g.append(_rect(120, 50, 12, 150, "#7fca8c", extra='opacity=".9"'))
        g.append(_rect(150, 200, 90, 14, "#a9d8a0", extra='opacity=".95"'))
        for x, y in [(126, 70), (126, 110), (126, 150), (126, 190)]:
            cx, cy = _pt(x, y)
            g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="#f2b84b" stroke="#fff" stroke-width="1.4"/>')
    for x, y in TREES:
        cx, cy = _pt(x, y)
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.3" fill="{C_TREE}" stroke="#fff" stroke-width="1"/>')

    north = ('<g transform="translate(32 268)" fill="none" stroke="#33413a" stroke-width="1.6">'
             '<text x="0" y="-22" text-anchor="middle" font-size="13" font-weight="700" fill="#22302a" stroke="none">N</text>'
             '<circle r="12"/><path d="M0-10 5 7 0 3-5 7Z" fill="#33413a"/></g>')
    sx, sy = 512, 290
    scale = (f'<g font-size="11" fill="#22302a" font-family="inherit"><text x="{sx}" y="{sy-8}" text-anchor="middle">0</text>'
             f'<text x="{sx+32}" y="{sy-8}" text-anchor="middle">10</text><text x="{sx+66}" y="{sy-8}" text-anchor="middle">20</text>'
             f'<text x="{sx+136}" y="{sy-8}" text-anchor="middle">40 m</text></g>'
             f'<path d="M{sx} {sy}h136M{sx} {sy-4}v8M{sx+32} {sy-3}v6M{sx+66} {sy-4}v8M{sx+136} {sy-4}v8" stroke="#22302a" stroke-width="1.6" fill="none"/>')
    svg = (f'<svg class="v-plan-svg" viewBox="0 0 680 310" preserveAspectRatio="xMidYMid meet" role="img" '
           f'aria-label="Illustrative site plan">{"".join(g)}{north}{scale}</svg>')
    panel = _layers_panel() if layers_panel else ""
    return f'<div class="v-plan-canvas">{svg}{panel}</div>'


def _layers_panel() -> str:
    rows = [("Planted ground", f'<span class="sw" style="background:{C_PLANTED}"></span>', True),
            ("Permeable paving", f'<span class="sw" style="background:{C_PAVING}"></span>', True),
            ("Sealed surfaces", f'<span class="sw" style="background:{C_SEALED}"></span>', True),
            ("Buildings", f'<span class="sw" style="background:{C_BUILD}"></span>', True),
            ("Trees (44)", f'<span class="dot" style="background:{C_TREE}"></span>', True),
            ("Other elements", '<span class="sw sw-empty"></span>', False)]
    items = "".join(f'<div class="lp-row"><span class="cb{" on" if on else ""}"></span>{sw}<span>{escape(t)}</span></div>'
                    for t, sw, on in rows)
    return f'<div class="v-layers-panel"><div class="lp-head">Layers {icon("close", 15, "#4b5a52")}</div>{items}</div>'


def plan_workspace_html() -> str:
    """Toolbar + plan canvas + layers popover + legend, as one card body."""
    tool = lambda n, active=False: f'<span class="tb{" tb-on" if active else ""}">{icon(n, 19, "#22302a", 1.8)}</span>'
    toolbar = (f'<div class="v-toolbar">{tool("pointer", True)}{tool("hand")}{tool("zoom_in")}{tool("zoom_out")}'
               f'{tool("fullscreen")}<span class="tb-sep"></span>{tool("pencil")}{tool("info")}'
               f'<span class="tb-layers">{icon("layers", 19, "#22302a", 1.8)}<b>Layers</b>{icon("chevron", 17, "#22302a")}</span></div>')
    legend = (f'<div class="v-legend"><span><i style="background:{C_PLANTED}"></i>Planted ground</span>'
              f'<span><i style="background:{C_PAVING}"></i>Permeable paving</span>'
              f'<span><i style="background:{C_SEALED}"></i>Sealed</span>'
              f'<span><i style="background:#6f6a62"></i>Buildings</span>'
              f'<span><i class="d" style="background:{C_TREE}"></i>Trees</span>'
              f'<span><i class="q"></i>Quality area (dashed)</span></div>')
    return toolbar + plan_svg() + legend


def show_plan(improved: bool = False, height: int = 390) -> None:
    st.markdown(f'<div class="v-plan" style="max-height:{height}px">{plan_svg(improved, layers_panel=False)}</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- small blocks
def title(name: str, subtitle: str) -> None:
    st.markdown(f'<div class="v-main-heading">{escape(name)}</div><div class="v-main-sub">{escape(subtitle)}</div>',
                unsafe_allow_html=True)


def card(title_text: str, content: str, sub: str = "") -> None:
    st.markdown(f'<div class="v-card"><div class="v-card-title">{escape(title_text)}</div>'
                f'{f"<div class=v-card-sub>{escape(sub)}</div>" if sub else ""}{content}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "", danger: bool = False) -> None:
    st.markdown(f'<div class="v-stat"><div class="v-stat-label">{escape(label)}</div>'
                f'<div class="v-stat-value {"red" if danger else ""}">{escape(value)}</div>'
                f'<div class="v-stat-note">{escape(note)}</div></div>', unsafe_allow_html=True)


def continue_button(label: str, page: str, key: str) -> None:
    from layout import set_page
    st.button(label, type="primary", key=f"cta_{key}", on_click=set_page, args=(page,), use_container_width=True)
