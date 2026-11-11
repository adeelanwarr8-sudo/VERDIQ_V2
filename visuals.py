"""Standalone vector mockup figures. All shapes and values are illustrative."""
from __future__ import annotations

from html import escape
import streamlit as st


def plan_svg(improved: bool = False, height: int = 390) -> str:
    trees = ''.join(
        f'<circle cx="{x}" cy="{y}" r="5" fill="#27774d" stroke="#fff" stroke-width="1.4"/>'
        for x,y in [(106,62),(105,83),(105,105),(105,128),(105,150),(105,172),(105,194),(105,218),
                    (138,60),(138,82),(138,104),(138,127),(138,150),(138,173),(138,195),(138,218),
                    (256,59),(274,70),(283,207),(263,227),(243,213),(190,231),(210,215)]
    )
    buildings = ''.join(
        f'<rect x="{x}" y="{y}" width="66" height="33" rx="2" fill="#92948d" stroke="#fff" stroke-width="2"/>'
        for x,y in [(183,66),(183,108),(183,150)]
    )
    improvements = '''<path d="M151 58 L169 58 L169 228 L151 228Z" fill="#70b88b" opacity=".85" />
        <path d="M181 193 L249 193 L249 222 L181 222Z" fill="#9dca8e" opacity=".9"/>
        <g fill="#f8c65e" stroke="#fff" stroke-width="1.5"><circle cx="163" cy="78" r="5"/><circle cx="163" cy="115" r="5"/><circle cx="163" cy="152" r="5"/><circle cx="163" cy="190" r="5"/></g>''' if improved else ''
    return f'''<div class="v-plan"><svg viewBox="0 0 360 290" role="img" aria-label="Illustrative landscape CAD plan preview" style="max-height:{height}px">
    <rect width="360" height="290" fill="#f3f6f1"/><g opacity=".55" stroke="#d8e1d7" stroke-width=".7">
    {''.join(f'<path d="M{x} 0V290"/>' for x in range(0,361,20))}
    {''.join(f'<path d="M0 {y}H360"/>' for y in range(0,291,20))}</g>
    <g transform="translate(180 145) rotate(21) translate(-180 -145)">
    <rect x="83" y="33" width="205" height="219" fill="#bdbdb3" stroke="#344b3a" stroke-width="2.5"/>
    <rect x="93" y="46" width="65" height="189" rx="2" fill="#b9d0ad"/>
    <rect x="175" y="49" width="83" height="183" fill="#d5d4c9"/>
    <path d="M162 45V238" stroke="#e7e2d2" stroke-width="14"/>
    <rect x="93" y="235" width="184" height="10" fill="#a7a9a0"/>{buildings}{improvements}{trees}
    </g><path d="M32 259 L32 219" stroke="#42584a" stroke-width="2"/><path d="M32 219 L27 231 L37 231 Z" fill="#42584a"/>
    <text x="27" y="211" font-size="12" font-family="sans-serif" fill="#42584a">N</text>
    <text x="260" y="274" font-size="9" fill="#607969" font-family="sans-serif">Illustrative plan · not DXF data</text>
    </svg></div>'''


def show_plan(improved: bool = False, height: int = 390) -> None:
    st.markdown(plan_svg(improved, height), unsafe_allow_html=True)


def title(name: str, subtitle: str) -> None:
    st.markdown(f'<div class="v-eyebrow">VERDIQ WORKSPACE</div><div class="v-page-title">{escape(name)}</div><div class="v-page-sub">{escape(subtitle)}</div>', unsafe_allow_html=True)


def card(title_text: str, content: str, sub: str = "") -> None:
    st.markdown(f'<div class="v-card"><div class="v-card-title">{escape(title_text)}</div>'
                f'{f"<div class=v-card-sub>{escape(sub)}</div>" if sub else ""}{content}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "", danger: bool = False) -> None:
    st.markdown(f'<div class="v-stat"><div class="v-stat-label">{escape(label)}</div>'
                f'<div class="v-stat-value {"red" if danger else ""}">{escape(value)}</div>'
                f'<div class="v-stat-note">{escape(note)}</div></div>', unsafe_allow_html=True)


def continue_button(label: str, page: str, key: str) -> None:
    from layout import set_page
    st.button(label, type="primary", key=key, on_click=set_page, args=(page,), use_container_width=True)
