"""Football Quant V2 design system (from the user's Design System artifact "Football Quant").

Flat analyst look: layered surfaces, hairline borders, IBM Plex Sans Thai + IBM Plex Mono for numbers,
one brand colour (teal accent) for "the answer", green/red/amber only for results. No gradients, glows,
blur or animation (hover only). Every rule here is an override layered on top of the older CSS, so the
page structure and class names stay the same.
"""

FONT_URL = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
            "&family=IBM+Plex+Sans+Thai:wght@400;500;600;700&display=swap")
FONT_IMPORT = f"@import url('{FONT_URL}');"

SANS = '"IBM Plex Sans Thai", "Noto Sans Thai", system-ui, -apple-system, "Segoe UI", sans-serif'
MONO = '"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace'

# ---- tokens (dark = app default) -------------------------------------------------------------
DARK = {
    "bg": "#0b0f15", "surface": "#11161e", "surface-2": "#171d27", "surface-3": "#1f2733",
    "border": "#242c38", "border-strong": "#334050",
    "text": "#e9eef5", "text-2": "#a9b4c4", "text-3": "#7f8ba0",
    "accent": "#2dd4bf", "accent-fill": "#2dd4bf", "on-accent": "#042f2b",
    "accent-tint": "rgba(45,212,191,0.12)", "accent-line": "rgba(45,212,191,0.4)",
    "alt": "#8b93f8", "alt-tint": "rgba(139,147,248,0.14)", "neutral": "#8a96a8",
    "pos": "#3ddc97", "pos-tint": "rgba(61,220,151,0.12)",
    "neg": "#ff6b6b", "neg-tint": "rgba(255,107,107,0.12)",
    "warn": "#f5b942", "warn-tint": "rgba(245,185,66,0.12)",
    "on-signal": "#0b0f15", "focus": "#5eead4",
}
LIGHT = {
    "bg": "#f5f7fa", "surface": "#ffffff", "surface-2": "#f0f3f7", "surface-3": "#e5e9ef",
    "border": "#e1e6ed", "border-strong": "#c9d1dc",
    "text": "#101828", "text-2": "#475467", "text-3": "#5d6b7e",
    "accent": "#0f766e", "accent-fill": "#0f766e", "on-accent": "#ffffff",
    "accent-tint": "rgba(15,118,110,0.08)", "accent-line": "rgba(15,118,110,0.35)",
    "alt": "#4f46e5", "alt-tint": "rgba(79,70,229,0.08)", "neutral": "#7d8799",
    "pos": "#067647", "pos-tint": "rgba(6,118,71,0.08)",
    "neg": "#d92d20", "neg-tint": "rgba(217,45,32,0.08)",
    "warn": "#b54708", "warn-tint": "rgba(181,71,8,0.08)",
    "on-signal": "#ffffff", "focus": "#0f766e",
}


def token_vars(t):
    return "".join(f"--{k}:{v};" for k, v in t.items()) + f"--font-sans:{SANS};--font-mono:{MONO};"


# ---- old palette -> design-system palette (applied to literal colours in the older CSS/HTML) ---
COLOR_MAP = [
    ("#0b1220", "#0b0f15"), ("#0d1526", "#0b0f15"), ("#0e1829", "#11161e"), ("#0f1a2e", "#11161e"),
    ("#111a2e", "#11161e"), ("#0f172a", "#171d27"),
    ("#e6edf7", "#e9eef5"), ("#e2e8f0", "#e9eef5"), ("#eef2fb", "#e9eef5"), ("#e6fffb", "#e9eef5"),
    ("#8fa3c0", "#a9b4c4"), ("#a9b8cf", "#a9b4c4"), ("#b8c7df", "#a9b4c4"), ("#c0cde2", "#a9b4c4"),
    ("#c6d3e7", "#a9b4c4"), ("#c8d4e8", "#a9b4c4"), ("#6b7f9e", "#7f8ba0"), ("#64748b", "#8a96a8"),
    ("#475569", "#334050"), ("#334155", "#1f2733"),
    ("#14b8a6", "#2dd4bf"), ("#0f766e", "#2dd4bf"), ("#5eead4", "#2dd4bf"), ("#99f6e4", "#2dd4bf"),
    ("#7dd3c8", "#2dd4bf"), ("#22d3ee", "#2dd4bf"), ("#cfe9e5", "#e9eef5"), ("#04201d", "#042f2b"),
    ("#6366f1", "#8b93f8"), ("#a78bfa", "#8b93f8"), ("#c7d2fe", "#8b93f8"), ("#e0e7ff", "#e9eef5"),
    ("#a5b4fc", "#8b93f8"),
    ("#34d399", "#3ddc97"), ("#6ee7b7", "#3ddc97"),
    ("#f87171", "#ff6b6b"), ("#fca5a5", "#ff6b6b"),
    ("#fbbf24", "#f5b942"), ("#fde68a", "#f5b942"), ("#fde047", "#f5b942"),
    ("rgba(20,184,166,", "rgba(45,212,191,"), ("rgba(94,234,212,", "rgba(45,212,191,"),
    ("rgba(99,102,241,", "rgba(139,147,248,"), ("rgba(165,180,252,", "rgba(139,147,248,"),
    ("rgba(52,211,153,", "rgba(61,220,151,"), ("rgba(110,231,183,", "rgba(61,220,151,"),
    ("rgba(248,113,113,", "rgba(255,107,107,"), ("rgba(252,165,165,", "rgba(255,107,107,"),
    ("rgba(251,191,36,", "rgba(245,185,66,"), ("rgba(253,224,71,", "rgba(245,185,66,"),
    ("rgba(4,32,29,", "rgba(4,47,43,"),
]


def remap(s):
    for a, b in COLOR_MAP:
        s = s.replace(a, b).replace(a.upper(), b)
    return s


# ---- story pages (shadow DOM component) ------------------------------------------------------
STORY_CSS = """
/* ===== Football Quant V2 design system ===== */
.s-root { %(vars)s --panel:#11161e; --panel2:#171d27; --line:#242c38; --txt:#e9eef5; --mut:#a9b4c4;
  --acc:#2dd4bf; --acc2:#8b93f8; --up:#3ddc97; --down:#ff6b6b; --warn:#f5b942;
  font-family:%(sans)s; font-size:14px; line-height:22px; -webkit-font-smoothing:antialiased; }
.s-root a { color:var(--accent); }
.s-root *, .s-root *::before, .s-root *::after { transition:none !important; animation:none !important; }
.s-js .s-rv, .s-js .s-rv.in { opacity:1 !important; transform:none !important; }
.s-js .s-rv:not(.in) .s-fill { width:var(--w) !important; }
.s-js .s-rv:not(.in) .s-vfill { height:var(--h) !important; }
.s-js .s-rv:not(.in) .s-draw { stroke-dashoffset:0 !important; }
.s-js .s-rv:not(.in) .s-ring { stroke-dashoffset:var(--o) !important; }
.s-js .s-rv:not(.in) .s-pop { transform:none !important; opacity:1 !important; }
.s-js .s-rv:not(.in) .s-lvl i { transform:none !important; }
.s-flow::after { display:none; }
.s-flow { background:var(--border-strong); }

/* numbers = mono, tabular */
.s-big, .s-mid, .s-statline .v, .s-brow .n, .s-kv > b, .s-kpi .v, .s-line .b .v, .s-prob .v, .s-tug .sd b, .s-rule .sc b,
.s-score, .s-result .sc, .s-sc3 .v, .s-heat .c, .s-node, [data-n] {
  font-family:%(mono)s; font-variant-numeric:tabular-nums; font-weight:500; letter-spacing:-.01em; }

/* chapter menu */
.s-nav { background:var(--bg); }
.s-nav a { border-radius:var(--radius-md,8px); background:var(--surface); border-color:var(--border); color:var(--text-2); font-size:12px; }
.s-nav a i { border-radius:4px; background:var(--surface-3); color:var(--text-2); font-family:%(mono)s; font-weight:500; }
.s-nav a.on { background:var(--accent-tint); color:var(--accent); border-color:var(--accent-line); }
.s-nav a.on i { background:var(--accent-fill); color:var(--on-accent); }
.s-nav a.seen i { background:var(--surface-3); color:var(--text); }

/* chapters */
.s-ch::before { background:var(--border); width:1px; }
.s-node { background:var(--surface); border:1px solid var(--border-strong); color:var(--accent); box-shadow:none; border-radius:8px; }
.s-kick { color:var(--text-2); font-size:11px; line-height:16px; letter-spacing:.06em; font-weight:600; }
.s-ch h2 { font-size:18px; line-height:26px; font-weight:600; letter-spacing:0; }
.s-lead { color:var(--text-2); font-size:14px; line-height:22px; }
.s-lead b { color:var(--text); font-weight:600; }

/* cards, labels */
.s-card, .s-kpi, .s-sel { background:var(--surface); border:1px solid var(--border); border-radius:12px; box-shadow:0 1px 0 rgba(255,255,255,0.03) inset; }
.s-card { padding:20px; }
.s-h, .s-kpi .t { font-size:11px; line-height:16px; letter-spacing:.06em; font-weight:600; color:var(--text-2); }
.s-kpi .d, .s-note, .s-legend { color:var(--text-3); font-size:12px; line-height:16px; }
.s-kpi .v { font-size:32px; line-height:36px; }
.s-big { font-size:32px; line-height:36px; } .s-mid { font-size:22px; line-height:28px; }
.s-list, .s-rule .nt, .s-sel .pk, .s-kv > span:first-child { color:var(--text-2); }
.s-empty { border:1px dashed var(--border-strong); border-radius:12px; color:var(--text-2); }

/* badges */
.s-chip { border-radius:6px; font-size:12px; font-weight:500; padding:2px 8px; background:var(--surface-2); color:var(--text-2); border:1px solid var(--border); }
.s-chip.ok { background:var(--pos-tint); color:var(--pos); border-color:transparent; }
.s-chip.bad { background:var(--neg-tint); color:var(--neg); border-color:transparent; }
.s-chip.warn { background:var(--warn-tint); color:var(--warn); border-color:transparent; }
.s-chip.acc { background:var(--accent-tint); color:var(--accent); border-color:transparent; }
.s-chip.off { background:var(--surface-2); color:var(--text-3); border-color:var(--border); }

/* bars & meters */
.s-bar, .s-tug .half { background:var(--surface-3); }
.s-fill.t, .s-tug .half.win .s-fill, .s-tug .half.l.win .s-fill { background:var(--accent); }
.s-fill.i { background:var(--alt); } .s-fill.g { background:var(--pos); } .s-fill.r { background:var(--neg); }
.s-fill.y { background:var(--warn); } .s-fill.n, .s-tug .half .s-fill { background:var(--neutral); } .s-fill.o { background:var(--border-strong); }
.s-tug .half.ban .s-fill { background:repeating-linear-gradient(45deg,var(--neg) 0 3px,transparent 3px 6px); opacity:.8; }
.s-tug .sd.win b { color:var(--accent); }
.s-bar .s-mark { background:var(--text); }
.s-rule .edge { background:var(--neutral); } .s-rule.sup .edge { background:var(--accent); } .s-rule.opp .edge { background:var(--neg); }

/* hero + verdict */
.s-hero { background:var(--surface); border:1px solid var(--border); border-radius:16px; box-shadow:none; }
.s-hero .comp { color:var(--text-2); }
.s-team .nm { font-size:24px; line-height:32px; font-weight:600; }
.s-team .sub { color:var(--text-3); font-size:12px; }
.s-vsx { color:var(--text-3); font-family:%(mono)s; font-weight:500; font-size:12px; letter-spacing:0;
  border:1px solid var(--border); border-radius:6px; padding:2px 8px; align-self:center; }
.s-pick { background:var(--surface); color:var(--text); border:1px solid var(--accent-line); border-radius:16px; box-shadow:none; }
.s-pick::after { display:none; }
.s-pick .k { color:var(--accent); opacity:1; font-size:11px; letter-spacing:.06em; font-weight:600; }
.s-pick .lb { font-size:32px; line-height:40px; font-weight:600; letter-spacing:-.01em; }
.s-pick .s-chip { background:var(--accent-tint); color:var(--accent); border-color:transparent; }
.s-pick .s-chip.ok { background:var(--pos-tint); color:var(--pos); }
.s-pick .s-chip.bad { background:var(--neg-tint); color:var(--neg); }
.s-pick .s-chip.warn { background:var(--warn-tint); color:var(--warn); }
.s-pick .s-chip.off { background:var(--surface-2); color:var(--text-3); border-color:var(--border); }
.s-pick .best { background:var(--surface-2); color:var(--text-2); border-radius:8px; }
.s-pick .sc { color:var(--text-2); opacity:1; }
.s-statline .t { color:var(--text-2); opacity:1; font-size:11px; letter-spacing:.06em; font-weight:600; }
.s-statline .v { font-size:22px; line-height:28px; }
.s-lvl i { background:var(--surface-3); border-radius:2px; } .s-lvl i.on { background:var(--accent); }
.s-pick.low { border-color:var(--border-strong); }
.s-pick.low .k, .s-pick.skip .k { color:var(--text-2); }
.s-pick.low .lb, .s-pick.skip .lb { color:var(--text-2); }
.s-pick.low .s-lvl i.on, .s-pick.skip .s-lvl i.on { background:var(--neutral); }
.s-pick.skip { background:var(--surface); border:1px dashed var(--border-strong); color:var(--text); }
.s-pick.low .s-chip, .s-pick.skip .s-chip { background:var(--surface-2); color:var(--text-2); border-color:var(--border); }
.s-pick.low .best, .s-pick.skip .best { background:var(--surface-2); }

.s-negband { margin-top:14px; padding:10px 14px; border-radius:12px; background:var(--neg-tint); color:var(--text);
  display:flex; flex-direction:column; gap:2px; border:1px solid rgba(255,107,107,0.35); }
.s-negband b { color:var(--neg); font-size:15px; line-height:22px; font-weight:600; }
.s-negband span { color:var(--text-2); font-size:13px; line-height:20px; }

/* form + scores */
.s-dot { border-radius:4px; width:22px; height:22px; color:var(--on-signal); font-family:%(mono)s; font-weight:600; font-size:11px; }
.s-dot.w { background:var(--pos); } .s-dot.d { background:var(--warn); } .s-dot.l { background:var(--neg); }
.s-score { border-radius:4px; background:var(--surface-2); border-color:var(--border); }
.s-score.w { color:var(--pos); background:var(--surface-2); } .s-score.d { color:var(--warn); background:var(--surface-2); }
.s-score.l { color:var(--neg); background:var(--surface-2); }

/* lines */
.s-line .b { background:var(--surface-2); border-color:var(--border); border-radius:8px; }
.s-line .b.cur { background:var(--accent-tint); border-color:var(--accent-line); }
.s-line .b .t { color:var(--text-3); }

/* buttons + tabs */
.s-btn { border-radius:8px; border:1px solid var(--border-strong); color:var(--text); background:var(--surface); font-weight:600; }
.s-btn:hover { background:var(--surface-2); }
.s-tabs .s-tabbar { gap:2px; padding:3px; border-radius:8px; background:var(--surface-2); border:1px solid var(--border); display:inline-flex; }
.s-tabs .s-tabbar button { border-radius:6px; border:0; background:none; color:var(--text-2); font-weight:500; font-size:13px; }
.s-tabs .s-tabbar button.on { background:var(--surface); color:var(--text); outline:1px solid var(--border); }
.s-sel:hover { transform:none; border-color:var(--border-strong); background:var(--surface-2); }
.s-sel.on { border-color:var(--accent-line); background:var(--accent-tint); box-shadow:none; }

/* charts */
.s-chart .s-guide { stroke:var(--text-3); }
.s-vbars .mid { background:var(--border-strong); }
.s-vbars .s-vfill.p { background:var(--pos); } .s-vbars .s-vfill.n { background:var(--neg); } .s-vbars .s-vfill.z { background:var(--neutral); }
.s-ringw .bg { stroke:var(--surface-3); }
.s-tl::before { background:var(--border); }
.s-tl .it::before { background:var(--neutral); border-color:var(--surface); }
.s-tl .it.w::before { background:var(--pos); } .s-tl .it.l::before { background:var(--neg); } .s-tl .it.p::before { background:var(--warn); }
.s-tl .it small { color:var(--text-3); }

/* result banner */
.s-result { border-radius:16px; background:var(--surface); border:1px solid var(--border); }
.s-result.w { background:var(--pos-tint); border-color:transparent; } .s-result.w .vd { color:var(--pos); }
.s-result.l { background:var(--neg-tint); border-color:transparent; } .s-result.l .vd { color:var(--neg); }
.s-result.p { background:var(--warn-tint); border-color:transparent; } .s-result.p .vd { color:var(--warn); }
.s-result .sc { font-size:32px; line-height:36px; } .s-result .vd { font-size:22px; font-weight:600; }

/* score heat-map */
.s-heat .c { border-radius:4px; background:rgba(45,212,191,var(--a)); color:var(--fg,var(--text)); border-color:var(--border); }
.s-heat .c.top { outline-color:var(--warn); }
.s-sc3 > div { background:var(--surface-2); border-color:var(--border); border-radius:8px; }

/* tooltip */
.s-tipbox { background:var(--surface-2); border:1px solid var(--border-strong); color:var(--text); border-radius:8px;
  box-shadow:0 12px 32px rgba(0,0,0,0.45); font-size:12px; line-height:18px; }

@media (max-width: 640px) {
  .s-team .nm { font-size:18px; line-height:26px; } .s-pick .lb { font-size:24px; line-height:32px; }
  .s-big, .s-kpi .v { font-size:24px; line-height:30px; } .s-card { padding:16px; }
}
""" % {"vars": token_vars(DARK), "sans": SANS, "mono": MONO}

# ---- Streamlit page + legacy cards (light DOM) -----------------------------------------------
APP_CSS = """
/* ===== Football Quant V2 design system ===== */
:root { %(vars)s }
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp select,
.stMarkdown, [data-testid="stMarkdownContainer"], [data-baseweb] { font-family:%(sans)s; }
.stApp code, .stApp pre { font-family:%(mono)s; }
.stApp { background:var(--bg) !important; color:var(--text); }
.block-container { max-width:1120px; }
[data-testid="stCaptionContainer"], .stCaption { color:var(--text-3) !important; }

/* app bar */
.hero { gap:12px; padding-bottom:12px; border-bottom:1px solid var(--border); }
.hero .logo { width:32px; height:32px; border-radius:8px; background:var(--accent-fill); color:var(--on-accent); box-shadow:none;
  font-family:%(mono)s; font-weight:600; font-size:13px; letter-spacing:-.02em; }
.hero .t { font-size:15px; line-height:22px; font-weight:600; }
.hero .s { color:var(--text-3); font-size:12px; line-height:16px; }
.pill { border-radius:6px; background:var(--accent-tint); color:var(--accent); border-color:transparent; font-weight:500; }

/* cards */
.card, .tile, .stat { background:var(--surface); border:1px solid var(--border); border-radius:12px; backdrop-filter:none; box-shadow:0 1px 0 rgba(255,255,255,0.03) inset; }
.card h4, .stat .k, .tile .k { color:var(--text-2); font-size:11px; letter-spacing:.06em; font-weight:600; }
.muted, .hist .a small, .team .tg, .match .lg { color:var(--text-3); }
.tile .v, .stat .v { font-family:%(mono)s; font-weight:500; }
.chip { border-radius:6px; background:var(--surface-2); color:var(--text-2); border:1px solid var(--border); font-size:12px; }
.chip.ok { background:var(--pos-tint); color:var(--pos); border-color:transparent; }
.chip.bad { background:var(--neg-tint); color:var(--neg); border-color:transparent; }
.chip.off { color:var(--text-3); }
.fc { border-radius:4px; color:var(--on-signal); }
.pick { background:var(--surface); color:var(--text); border:1px solid var(--accent-line); border-radius:16px; box-shadow:none; }
.pick.low { background:var(--surface); color:var(--text); border-color:var(--border-strong); box-shadow:none; }
.pick .tier, .pick .flag { background:var(--accent-tint); color:var(--accent); border-radius:6px; }
.pick.low .tier, .pick.low .flag { background:var(--surface-2); color:var(--text-2); }
.pick .bar, .sig .b { background:var(--surface-3); }
.pick .bar > div, .sig .b > div { background:var(--accent); }
.pick.low .bar > div { background:var(--neutral); }
.res { border-radius:12px; }
.res.win { background:var(--pos-tint); border-color:transparent; color:var(--pos); }
.res.lose { background:var(--neg-tint); border-color:transparent; color:var(--neg); }
.res.push { background:var(--warn-tint); border-color:transparent; color:var(--warn); }

/* streamlit widgets */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius:8px; min-height:36px; font-weight:600;
  border:1px solid var(--border-strong); background:var(--surface); color:var(--text); box-shadow:none; }
.stButton > button:hover, .stDownloadButton > button:hover { background:var(--surface-2); border-color:var(--border-strong); color:var(--text); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:var(--accent-fill); color:var(--on-accent);
  border-color:transparent; box-shadow:none; }
.stButton > button[kind="primary"]:hover { background:var(--accent-fill); color:var(--on-accent); filter:brightness(1.06); }
.stButton > button:focus-visible, .stTabs [data-baseweb="tab"]:focus-visible { outline:2px solid var(--focus); outline-offset:2px; }
[data-testid="stFileUploader"] section { border:1px dashed var(--border-strong); border-radius:12px; background:var(--surface); }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius:0; padding:8px 12px; background:transparent; color:var(--text-2); }
.stTabs [aria-selected="true"] { background:transparent !important; color:var(--text) !important; font-weight:600;
  box-shadow:inset 0 -2px 0 var(--accent); }
[data-testid="stExpander"] { border:1px solid var(--border); border-radius:12px; background:var(--surface); }
[data-testid="stMetricValue"] { font-family:%(mono)s; font-weight:500; }
.stTextInput input, .stNumberInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  background:var(--surface-2) !important; border-color:var(--border-strong) !important; border-radius:6px !important; }
.tbl th { color:var(--text-3); background:var(--surface-2); font-weight:500; border-bottom-color:var(--border); }
.tbl td { border-bottom-color:var(--border); }
""" % {"vars": token_vars(DARK), "sans": SANS, "mono": MONO}

# ---- dashboard cards (fq-*) ------------------------------------------------------------------
DASH_CSS = """
/* ===== Football Quant V2 design system ===== */
.fq { %(vars)s --acc:#2dd4bf; --acc2:#8b93f8; --up:#3ddc97; --down:#ff6b6b; --warn:#f5b942; --mut:#a9b4c4; --txt:#e9eef5;
  --line:#242c38; --panel:#11161e; font-family:%(sans)s; color:var(--text); }
.fq-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; box-shadow:0 1px 0 rgba(255,255,255,0.03) inset; }
.fq-h { font-size:11px; letter-spacing:.06em; color:var(--text-2); font-weight:600; }
.fq-sec { font-size:18px; line-height:26px; font-weight:600; }
.fq-meter { background:var(--surface-3); }
.fq-meter > i { background:var(--accent); }
.fq-num, .fq .v, .fq b.n { font-family:%(mono)s; font-variant-numeric:tabular-nums; }
""" % {"vars": token_vars(DARK), "sans": SANS, "mono": MONO}


def report_light_css():
    """Light theme for the downloadable HTML report (design system: Light = reports and print)."""
    return (":root{%s}body{background:var(--bg)!important;color:var(--text)!important;font-family:%s!important}"
            ".fq{%s --acc:#0f766e;--acc2:#4f46e5;--up:#067647;--down:#d92d20;--warn:#b54708;--mut:#475467;--txt:#101828;"
            "--line:#e1e6ed;--panel:#ffffff;color:var(--text)}"
            ".fq-card{background:var(--surface);border-color:var(--border)}.sub{color:var(--text-3)!important}"
            % (token_vars(LIGHT), SANS, token_vars(LIGHT)))
