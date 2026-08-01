"""Design system: colours, typography, component CSS."""

from __future__ import annotations

import streamlit as st

PALETTES = {
    "light": {
        "bg": "#FAF8F5",
        "bg2": "#F2EEE8",
        "surface": "#FFFFFF",
        "text": "#16181C",
        "muted": "#6E7178",
        "faint": "#9B9EA4",
        "line": "#E5DFD6",
        "line2": "#D8D1C6",
        "accent": "#3F6B52",
        "accent2": "#55876A",
        "on_accent": "#FFFFFF",
        "accent_soft": "#E4EDE6",
        "warn": "#9A6216",
        "warn_soft": "#F7EEDF",
        "bad": "#A33A2E",
        "bad_soft": "#F8E9E6",
        "shadow": "0 1px 2px rgba(24,22,18,.05), 0 8px 28px -14px rgba(24,22,18,.18)",
        "shadow_lift": "0 2px 4px rgba(24,22,18,.06), 0 18px 44px -18px rgba(24,22,18,.28)",
    },
    "dark": {
        "bg": "#0E1013",
        "bg2": "#15181C",
        "surface": "#171A1F",
        "text": "#ECEAE6",
        "muted": "#9DA2AA",
        "faint": "#6E747D",
        "line": "#262B31",
        "line2": "#333940",
        "accent": "#86C29B",
        "accent2": "#A3D4B3",
        "on_accent": "#0A1B11",
        "accent_soft": "#16301F",
        "warn": "#D9A85C",
        "warn_soft": "#2B2318",
        "bad": "#E58A7C",
        "bad_soft": "#2E1C1A",
        "shadow": "0 1px 2px rgba(0,0,0,.4), 0 10px 30px -16px rgba(0,0,0,.7)",
        "shadow_lift": "0 2px 6px rgba(0,0,0,.45), 0 22px 48px -20px rgba(0,0,0,.85)",
    },
}

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&"
    "family=Inter:wght@400;500;600&display=swap"
)
# Streamlit does not execute @import inside injected CSS - a <link> element does.
FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    f'<link rel="stylesheet" href="{FONT_URL}">'
)


def css(mode: str) -> str:
    p = PALETTES["dark" if mode == "dark" else "light"]
    return f"""
<style>

:root {{
  --bg:{p['bg']}; --bg2:{p['bg2']}; --surface:{p['surface']};
  --text:{p['text']}; --muted:{p['muted']}; --faint:{p['faint']};
  --line:{p['line']}; --line2:{p['line2']};
  --accent:{p['accent']}; --accent2:{p['accent2']}; --accent-soft:{p['accent_soft']};
  --on-accent:{p['on_accent']};
  --warn:{p['warn']}; --warn-soft:{p['warn_soft']};
  --bad:{p['bad']}; --bad-soft:{p['bad_soft']};
  --shadow:{p['shadow']}; --shadow-lift:{p['shadow_lift']};
  --serif:'Fraunces', 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif;
  --sans:'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif;
  --r:14px;
}}

/* ---------- Base layout ---------- */
.stApp {{ background: var(--bg); }}
html, body, [class*="css"] {{ font-family: var(--sans); color: var(--text); }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.6rem; padding-bottom: 6rem; max-width: 1080px; }}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display:none; }}

/* Streamlit ships its own heading styles - hence the high specificity */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stHeadingWithActionElements"] h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
  font-family: var(--serif) !important; font-weight: 500 !important;
  letter-spacing: -.015em; color: var(--text); padding: 0; margin-top: 0;
}}
h1, .stMarkdown h1, [data-testid="stMarkdownContainer"] h1 {{
  font-size: 2.3rem !important; line-height: 1.13 !important; }}
h2, .stMarkdown h2, [data-testid="stMarkdownContainer"] h2 {{
  font-size: 1.5rem !important; line-height: 1.25 !important; }}
h3, .stMarkdown h3 {{ font-size: 1.18rem !important; }}
[data-testid="stHeadingActionElements"] {{ display: none; }}
p, li, label {{ color: var(--text); }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
  background: var(--bg2);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .45rem; }}
.sb-brand {{ padding: .2rem 0 1.1rem; }}
.sb-brand .k {{ font-family: var(--serif); font-size: 1.22rem; line-height:1.15; }}
.sb-brand .s {{ font-size: .74rem; color: var(--faint); letter-spacing:.09em; text-transform: uppercase; margin-top:.28rem; }}
.sb-label {{ font-size:.68rem; letter-spacing:.13em; text-transform:uppercase; color:var(--faint);
  margin: 1.4rem 0 .35rem; font-weight:600; }}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  font-family: var(--sans); font-size: .875rem; font-weight: 500;
  border-radius: 10px; border: 1px solid var(--line2);
  background: var(--surface); color: var(--text);
  padding: .5rem .95rem; transition: all .16s cubic-bezier(.2,.7,.3,1);
  box-shadow: none; width: 100%;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
  border-color: var(--accent); color: var(--accent); transform: translateY(-1px);
}}
.stButton > button:focus:not(:active) {{ color: var(--accent); border-color: var(--accent); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
  background: var(--accent); border-color: var(--accent); color: var(--on-accent);
}}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {{
  background: var(--accent2); border-color: var(--accent2); color: var(--on-accent); }}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {{
  background: var(--surface) !important; color: var(--text) !important;
  border: 1px solid var(--line2) !important; border-radius: 10px !important;
  font-family: var(--sans) !important; font-size: .95rem !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important;
}}
[data-baseweb="select"] > div {{
  background: var(--surface) !important; border-color: var(--line2) !important; border-radius:10px !important;
}}
.stRadio [role="radiogroup"] {{ gap:.4rem; }}
.stRadio label {{ font-size:.94rem; }}
[data-testid="stWidgetLabel"] p {{ font-size:.78rem; color:var(--muted); font-weight:500;
  letter-spacing:.02em; }}

/* ---------- Cards ---------- */
.card {{
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--r); padding: 1.5rem 1.65rem; box-shadow: var(--shadow);
}}
.card.pad-lg {{ padding: 2rem 2.1rem; }}
.card + .card {{ margin-top: .85rem; }}

.eyebrow {{ font-size:.7rem; letter-spacing:.14em; text-transform:uppercase;
  color: var(--faint); font-weight:600; }}
.hairline {{ height:1px; background: var(--line); border:0; margin:1.15rem 0; }}
.muted {{ color: var(--muted); }}
.small {{ font-size:.83rem; }}

/* ---------- Hero ---------- */
.hero {{ margin-bottom: 1.6rem; }}
.hero h1 {{ margin:.35rem 0 .3rem; }}
.hero .sub {{ color: var(--muted); font-size:1.02rem; max-width: 60ch; }}

/* ---------- Key figures ---------- */
.stats {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(120px,1fr)); gap:.7rem; }}
.stat {{ background: var(--surface); border:1px solid var(--line); border-radius: 12px;
  padding: .95rem 1.05rem; }}
.stat .v {{ font-family: var(--serif); font-size:1.75rem; line-height:1; }}
.stat .l {{ font-size:.72rem; color:var(--faint); text-transform:uppercase;
  letter-spacing:.1em; margin-top:.45rem; font-weight:600; }}
.stat .d {{ font-size:.78rem; color:var(--muted); margin-top:.2rem; }}

/* ---------- Progress ---------- */
.bar {{ height:6px; background: var(--bg2); border-radius:99px; overflow:hidden; border:1px solid var(--line); }}
.bar > i {{ display:block; height:100%; background: var(--accent);
  border-radius:99px; transition: width .7s cubic-bezier(.2,.8,.2,1); }}
.bar.thin {{ height:4px; }}

/* ---------- Question and study card, with flip ---------- */
@keyframes flipIn {{
  0%   {{ transform: rotateX(-92deg); opacity:0; }}
  55%  {{ transform: rotateX(8deg);  opacity:1; }}
  100% {{ transform: rotateX(0deg);  opacity:1; }}
}}
@keyframes riseIn {{
  from {{ transform: translateY(9px); opacity:0; }}
  to   {{ transform: translateY(0);   opacity:1; }}
}}
@keyframes softIn {{ from {{ opacity:0 }} to {{ opacity:1 }} }}
.flip {{ animation: flipIn .5s cubic-bezier(.25,.9,.3,1) both; transform-origin: top center; }}
.rise {{ animation: riseIn .34s cubic-bezier(.2,.8,.2,1) both; }}
.fade {{ animation: softIn .45s ease both; }}

.qcard {{ background: var(--surface); border:1px solid var(--line); border-radius: var(--r);
  padding: 1.8rem 1.9rem; box-shadow: var(--shadow-lift); }}
.qcard .qmeta {{ display:flex; gap:.5rem; align-items:center; flex-wrap:wrap; margin-bottom:1rem; }}
.qcard .qtext {{ font-family: var(--serif); font-size: 1.42rem; line-height:1.36; }}
.acard {{ border-left: 3px solid var(--accent); background: var(--accent-soft);
  border-radius: 4px 12px 12px 4px; padding: 1.15rem 1.35rem; }}
.acard.miss {{ border-left-color: var(--bad); background: var(--bad-soft); }}
.acard .lab {{ font-size:.68rem; letter-spacing:.14em; text-transform:uppercase;
  font-weight:700; color: var(--accent); margin-bottom:.5rem; }}
.acard.miss .lab {{ color: var(--bad); }}
.acard p {{ margin:0; line-height:1.62; font-size:.97rem; }}

/* ---------- Chips ---------- */
.chip {{ display:inline-flex; align-items:center; gap:.35rem; font-size:.71rem; font-weight:600;
  letter-spacing:.05em; padding:.24rem .6rem; border-radius:99px;
  background: var(--bg2); color: var(--muted); border:1px solid var(--line); }}
.chip.ac {{ background: var(--accent-soft); color: var(--accent); border-color: transparent; }}
.chip.wa {{ background: var(--warn-soft); color: var(--warn); border-color: transparent; }}
.chip.ba {{ background: var(--bad-soft); color: var(--bad); border-color: transparent; }}
.kw {{ display:inline-block; font-size:.78rem; padding:.2rem .55rem; border-radius:7px;
  margin:.15rem .25rem .15rem 0; border:1px solid var(--line); }}
.kw.hit {{ background: var(--accent-soft); color: var(--accent); border-color:transparent; font-weight:600; }}
.kw.mis {{ background: var(--bg2); color: var(--faint); }}

/* ---------- Study card ---------- */
.lk-title {{ font-family: var(--serif); font-size:1.3rem; line-height:1.3; margin:.1rem 0 .1rem; }}
.lk-point {{ display:flex; gap:.75rem; padding:.55rem 0; border-bottom:1px dashed var(--line);
  font-size:.955rem; line-height:1.6; }}
.lk-point:last-child {{ border-bottom:0; }}
.lk-point .n {{ flex:0 0 1.35rem; height:1.35rem; border-radius:50%; background:var(--accent-soft);
  color:var(--accent); font-size:.7rem; font-weight:700; display:flex; align-items:center;
  justify-content:center; margin-top:.12rem; }}

/* ---------- Lists and section navigation ---------- */
.rowline {{ display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding:.62rem 0; border-bottom:1px solid var(--line); font-size:.93rem; }}
.rowline:last-child {{ border-bottom:0; }}
.rowline .nm {{ flex:1; min-width:0; }}
.rowline .nm b {{ font-weight:500; }}
.dot {{ width:7px; height:7px; border-radius:50%; display:inline-block; }}
.dot.on {{ background: var(--accent); }}
.dot.half {{ background: var(--warn); }}
.dot.off {{ background: var(--line2); }}

/* ---------- Heatmap ---------- */
.heat {{ display:flex; gap:3px; flex-wrap:wrap; }}
.heat i {{ width:13px; height:13px; border-radius:3px; background: var(--bg2);
  border:1px solid var(--line); display:block; }}
.heat i.l1 {{ background: var(--accent-soft); border-color:transparent; }}
.heat i.l2 {{ background: var(--accent); opacity:.45; border-color:transparent; }}
.heat i.l3 {{ background: var(--accent); opacity:.72; border-color:transparent; }}
.heat i.l4 {{ background: var(--accent); border-color:transparent; }}

/* ---------- Glossary ---------- */
.gl {{ padding:.85rem 0; border-bottom:1px solid var(--line); }}
.gl:last-child {{ border-bottom:0; }}
.gl .t {{ font-family: var(--serif); font-size:1.05rem; }}
.gl .d {{ font-size:.9rem; color:var(--muted); line-height:1.6; margin-top:.2rem; }}

/* ---------- Tabs / Expander ---------- */
.stTabs [data-baseweb="tab-list"] {{ gap:.15rem; border-bottom:1px solid var(--line); }}
.stTabs [data-baseweb="tab"] {{ font-size:.87rem; font-weight:500; color:var(--muted);
  padding: .5rem .9rem; }}
.stTabs [aria-selected="true"] {{ color: var(--accent) !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: var(--accent); }}
[data-testid="stExpander"] {{ border:1px solid var(--line); border-radius:12px;
  background: var(--surface); }}
[data-testid="stExpander"] summary {{ font-size:.87rem; font-weight:500; }}

[data-testid="stImage"] img, [data-testid="stImageContainer"] img {{
  border-radius: 10px; border: 1px solid var(--line); box-shadow: var(--shadow);
}}
[data-testid="stProgress"] > div > div > div > div {{ background: var(--accent); }}
[data-testid="stSlider"] [role="slider"] {{ background: var(--accent) !important; }}
hr {{ border-color: var(--line); }}
code {{ background: var(--bg2); color: var(--accent); padding:.1rem .35rem;
  border-radius:5px; font-size:.85em; }}

/* ---------- Odds and ends ---------- */
.spacer-s {{ height:.5rem; }} .spacer {{ height:1.1rem; }} .spacer-l {{ height:2rem; }}
.center {{ text-align:center; }}
.big-num {{ font-family: var(--serif); font-size:3.6rem; line-height:1; }}
::-webkit-scrollbar {{ width:9px; height:9px; }}
::-webkit-scrollbar-thumb {{ background: var(--line2); border-radius:99px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
</style>
"""


def inject(mode: str) -> None:
    st.markdown(FONT_LINK, unsafe_allow_html=True)
    st.markdown(css(mode), unsafe_allow_html=True)
