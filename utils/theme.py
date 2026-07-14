"""
ScholarLens design system: color tokens, Plotly template, and CSS injection.

Palette validated with the dataviz skill's six-check validator against a
custom deep-space-navy dark surface (#0d1220): lightness band, chroma floor,
and contrast all PASS; CVD separation WARNs only on the green/yellow adjacent
pair (8-12 floor band), which is why those two slots always carry a legend or
direct label wherever they appear together.
"""

import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go

BG_PAGE = "#05070d"
BG_SURFACE = "#0d1220"
BG_SURFACE_ELEVATED = "#121a2e"
BORDER = "rgba(255,255,255,0.08)"
BORDER_STRONG = "rgba(120,150,255,0.25)"

TEXT_PRIMARY = "#f5f7fb"
TEXT_SECONDARY = "#a8b3c7"
TEXT_MUTED = "#6b7688"

GRIDLINE = "#1c2540"

# Fixed-order categorical hues (blue, aqua, yellow, green, violet, red, magenta, orange)
CATEGORICAL = [
    "#3987e5", "#199e70", "#c98500", "#008300",
    "#9085e9", "#e66767", "#d55181", "#d95926",
]

NODE_TYPE_COLORS = {
    "paper": CATEGORICAL[0],
    "method": CATEGORICAL[1],
    "dataset": CATEGORICAL[2],
    "author": CATEGORICAL[3],
    "institution": CATEGORICAL[4],
}

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# Single-hue blue ramp for magnitude (sequential) encodings
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

ACCENT = CATEGORICAL[0]
ACCENT_2 = CATEGORICAL[4]

FONT_FAMILY = "'Sora', 'Inter', -apple-system, 'Segoe UI', sans-serif"


def register_plotly_theme():
    """Register a dark template as the Plotly default so every px/go figure
    in the app (including ones with no explicit template) inherits it."""
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY, size=13),
        title=dict(font=dict(color=TEXT_PRIMARY, size=16)),
        colorway=CATEGORICAL,
        xaxis=dict(gridcolor=GRIDLINE, zerolinecolor=GRIDLINE, linecolor=GRIDLINE,
                    tickfont=dict(color=TEXT_SECONDARY)),
        yaxis=dict(gridcolor=GRIDLINE, zerolinecolor=GRIDLINE, linecolor=GRIDLINE,
                    tickfont=dict(color=TEXT_SECONDARY)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SECONDARY)),
        hoverlabel=dict(bgcolor=BG_SURFACE_ELEVATED, font=dict(color=TEXT_PRIMARY, family=FONT_FAMILY)),
        colorscale=dict(
            sequential=[[i / (len(SEQUENTIAL_BLUE) - 1), c] for i, c in enumerate(SEQUENTIAL_BLUE)]
        ),
    )
    pio.templates["scholarlens"] = template
    pio.templates.default = "scholarlens"
    px.defaults.color_discrete_sequence = CATEGORICAL
    px.defaults.template = "scholarlens"


def get_css() -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: {FONT_FAMILY};
}}

.stApp {{
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(57,135,229,0.14), transparent 60%),
        radial-gradient(1000px 500px at 110% 10%, rgba(144,133,233,0.12), transparent 55%),
        {BG_PAGE};
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_SURFACE} 0%, {BG_PAGE} 100%);
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] h1 {{
    background: linear-gradient(90deg, #ffffff, {ACCENT} 80%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-weight: 800;
    letter-spacing: 0.5px;
}}

/* Nav radio -> pill list */
div[data-testid="stRadio"] > div {{
    gap: 4px;
}}
div[data-testid="stRadio"] label {{
    padding: 8px 12px;
    border-radius: 10px;
    transition: background 0.15s ease, color 0.15s ease;
    width: 100%;
}}
div[data-testid="stRadio"] label:hover {{
    background: rgba(255,255,255,0.05);
}}
div[data-testid="stRadio"] label:has(input:checked) {{
    background: linear-gradient(90deg, rgba(57,135,229,0.25), rgba(144,133,233,0.18));
    box-shadow: inset 0 0 0 1px {BORDER_STRONG};
}}
div[data-testid="stRadio"] label:has(input:checked) p {{
    color: {TEXT_PRIMARY};
    font-weight: 600;
}}

/* Headings */
h1, h2, h3 {{
    color: {TEXT_PRIMARY};
    font-weight: 700;
    letter-spacing: 0.2px;
}}
h1:first-of-type {{
    background: linear-gradient(90deg, {TEXT_PRIMARY}, {ACCENT});
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

/* Metrics as glass cards */
div[data-testid="stMetric"] {{
    background: linear-gradient(160deg, {BG_SURFACE_ELEVATED}, {BG_SURFACE});
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 8px 24px rgba(0,0,0,0.35);
}}
div[data-testid="stMetricValue"] {{
    color: {ACCENT};
    font-weight: 700;
}}

/* Buttons */
.stButton > button, .stDownloadButton > button {{
    background: linear-gradient(90deg, {ACCENT}, {ACCENT_2});
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: 0.2px;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    box-shadow: 0 4px 16px rgba(57,135,229,0.25);
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(144,133,233,0.35);
    color: white;
}}

/* Tabs */
button[data-testid="stTab"] {{
    color: {TEXT_SECONDARY};
    font-weight: 600;
}}
button[data-testid="stTab"][aria-selected="true"] {{
    color: {TEXT_PRIMARY};
    border-bottom-color: {ACCENT} !important;
}}

/* Expanders / containers */
div[data-testid="stExpander"] {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

/* File uploader */
section[data-testid="stFileUploaderDropzone"] {{
    background: {BG_SURFACE};
    border: 1.5px dashed {BORDER_STRONG};
    border-radius: 12px;
}}

/* Inputs */
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
    border-radius: 8px !important;
}}

/* Dividers */
hr {{
    border-color: {BORDER};
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {BG_PAGE}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_STRONG}; border-radius: 8px; }}
</style>
"""


def hero_banner(title: str, subtitle: str) -> str:
    return f"""
<div style="
    padding: 28px 32px;
    border-radius: 18px;
    margin-bottom: 20px;
    background: linear-gradient(135deg, rgba(57,135,229,0.16), rgba(144,133,233,0.10));
    border: 1px solid {BORDER};
">
    <div style="font-size:30px; font-weight:800; letter-spacing:0.3px;
                background: linear-gradient(90deg, {TEXT_PRIMARY}, {ACCENT});
                -webkit-background-clip:text; background-clip:text; color:transparent;">
        {title}
    </div>
    <div style="color:{TEXT_SECONDARY}; font-size:15px; margin-top:6px;">{subtitle}</div>
</div>
"""
