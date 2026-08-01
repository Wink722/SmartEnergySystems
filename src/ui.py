"""Reusable interface building blocks and effects."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "smart_energy_systems.pdf"


# ------------------------------------------------------------- slide images

@st.cache_resource(show_spinner=False)
def _doc():
    import fitz
    return fitz.open(PDF_PATH)


@st.cache_data(show_spinner=False, max_entries=160)
def slide_png(page: int, dpi: int = 190) -> bytes:
    doc = _doc()
    pix = doc[page - 1].get_pixmap(dpi=dpi)
    return pix.tobytes("png")


def show_slide(page: int, caption: str = "", dpi: int = 190) -> None:
    try:
        st.image(slide_png(page, dpi), width="stretch",
                 caption=caption or f"Original slide – page {page} of the script")
    except Exception as exc:  # pragma: no cover - defensive
        st.warning(f"Slide {page} could not be rendered ({exc}).")


def slide_download(page: int) -> None:
    try:
        st.download_button("Slide as PNG", slide_png(page, 220),
                           file_name=f"slide_{page:03d}.png", mime="image/png",
                           key=f"dl_slide_{page}")
    except Exception:
        pass


# --------------------------------------------------------- building blocks

def hero(eyebrow: str, title: str, sub: str = "") -> None:
    # Deliberately without line breaks: a blank line would end the HTML block
    # early inside Streamlit's markdown renderer.
    parts = ['<div class="hero fade">',
             f'<div class="eyebrow">{html.escape(eyebrow)}</div>',
             f"<h1>{html.escape(title)}</h1>"]
    if sub:
        parts.append(f'<div class="sub">{html.escape(sub)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def stat_grid(items: list[tuple[str, str, str]]) -> None:
    """items: (value, label, note)"""
    cells = []
    for v, l, d in items:
        cell = (f'<div class="stat"><div class="v">{html.escape(v)}</div>'
                f'<div class="l">{html.escape(l)}</div>')
        if d:
            cell += f'<div class="d">{html.escape(d)}</div>'
        cells.append(cell + "</div>")
    st.markdown(f'<div class="stats rise">{"".join(cells)}</div>',
                unsafe_allow_html=True)


def bar(fraction: float, thin: bool = False) -> None:
    pct = max(0.0, min(1.0, fraction)) * 100
    st.markdown(
        f'<div class="bar{" thin" if thin else ""}"><i style="width:{pct:.1f}%"></i></div>',
        unsafe_allow_html=True,
    )


def chip(text: str, tone: str = "") -> str:
    cls = {"ok": "chip ac", "warn": "chip wa", "bad": "chip ba"}.get(tone, "chip")
    return f'<span class="{cls}">{html.escape(text)}</span>'


def card_open(extra: str = "") -> None:
    st.markdown(f'<div class="card {extra}">', unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def spacer(size: str = "") -> None:
    cls = {"s": "spacer-s", "l": "spacer-l"}.get(size, "spacer")
    st.markdown(f'<div class="{cls}"></div>', unsafe_allow_html=True)


def section_title(text: str, note: str = "") -> None:
    st.markdown(
        f"""<div style="display:flex;align-items:baseline;justify-content:space-between;
        gap:1rem;margin:.2rem 0 .7rem;">
        <div class="eyebrow">{html.escape(text)}</div>
        <div class="small muted">{html.escape(note)}</div></div>""",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ effects

def confetti(intensity: int = 90, seconds: float = 2.2) -> None:
    """Restrained confetti in the accent colours, no external libraries."""
    components.html(
        f"""
<canvas id="cf" style="position:fixed;inset:0;pointer-events:none;z-index:9999"></canvas>
<script>
const c=document.getElementById('cf'),x=c.getContext('2d');
function fit(){{c.width=window.innerWidth;c.height=window.innerHeight;}}
fit();window.addEventListener('resize',fit);
const cols=['#3F6B52','#55876A','#86C29B','#C8A24A','#D8D1C6'];
const P=[];
for(let i=0;i<{intensity};i++){{
  P.push({{x:Math.random()*c.width, y:-20-Math.random()*c.height*0.4,
    w:4+Math.random()*5, h:6+Math.random()*8,
    vy:1.6+Math.random()*2.6, vx:-0.9+Math.random()*1.8,
    a:Math.random()*Math.PI, va:-0.09+Math.random()*0.18,
    col:cols[(Math.random()*cols.length)|0]}});
}}
const t0=Date.now();
(function loop(){{
  const el=(Date.now()-t0)/1000;
  x.clearRect(0,0,c.width,c.height);
  const fade=Math.max(0,1-Math.max(0,el-{seconds}*0.55)/({seconds}*0.45));
  P.forEach(p=>{{
    p.x+=p.vx; p.y+=p.vy; p.a+=p.va; p.vy+=0.012;
    x.save(); x.translate(p.x,p.y); x.rotate(p.a);
    x.globalAlpha=fade; x.fillStyle=p.col;
    x.fillRect(-p.w/2,-p.h/2,p.w,p.h); x.restore();
  }});
  if(el<{seconds}) requestAnimationFrame(loop); else x.clearRect(0,0,c.width,c.height);
}})();
</script>""",
        height=0,
    )


def toast(message: str, icon: str = "✓") -> None:
    try:
        st.toast(message, icon=icon)
    except Exception:
        st.success(message)
