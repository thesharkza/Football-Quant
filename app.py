# -*- coding: utf-8 -*-
"""Football Quant V5.9 — หน้าเว็บ Streamlit (ใช้ engine จาก football_quant_v58.py)"""
import hmac
import html as _html
import json
import os
import tempfile
import time

import streamlit as st

st.set_page_config(page_title="Football Quant", page_icon="⚽", layout="centered",
                   initial_sidebar_state="collapsed")

# ---- หน้าตรวจสอบระบบ: เปิดด้วยการเติม ?diag=1 ท้ายลิงก์ (ไม่แสดงข้อมูลลับ) ----
if st.query_params.get("diag") == "1":
    import platform
    st.write("✅ เซิร์ฟเวอร์ Streamlit ทำงาน และส่งหน้านี้ถึงเบราว์เซอร์ได้")
    st.write(f"Streamlit {st.__version__} · Python {platform.python_version()}")
    try:
        import football_quant_v58 as _q
        st.write(f"✅ โหลดตัวคำนวณได้ (Rule {len(_q.RULES)} ข้อ)")
    except Exception as _e:  # noqa
        st.write(f"❌ โหลดตัวคำนวณไม่ได้: {str(_e)[:200]}")
    st.write("ถ้าเห็นหน้านี้ แสดงว่าปัญหาอยู่ที่ส่วนหน้าตา/การแสดงผลของแอปหลัก ไม่ใช่เซิร์ฟเวอร์หรือเครือข่าย")
    st.stop()

import football_quant_v58 as q

DATA_DIR = os.environ.get("QUANT_DATA_DIR", "quant_data")

CSS = """
<style>
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: -apple-system, BlinkMacSystemFont, 'Sukhumvit Set', 'Thonburi', 'Noto Sans Thai', 'Segoe UI', Tahoma, sans-serif !important; }
.stApp { background: radial-gradient(900px 420px at 12% -8%, rgba(20,184,166,.14), transparent 60%),
                     radial-gradient(800px 380px at 100% 0%, rgba(99,102,241,.13), transparent 55%),
                     linear-gradient(180deg, #0b1220 0%, #0d1526 100%); }
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
.stDeployButton, [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 880px; }
h1, h2, h3 { letter-spacing: -.01em; }

.hero { display:flex; align-items:center; gap:14px; margin: 4px 0 18px; }
.hero .logo { width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:24px; background: linear-gradient(135deg,#14b8a6,#6366f1); box-shadow: 0 8px 24px rgba(20,184,166,.35); }
.hero .t { font-size:1.45rem; font-weight:700; line-height:1.1; }
.hero .s { color:#8fa3c0; font-size:.86rem; margin-top:2px; }
.pill { display:inline-block; padding:2px 10px; border-radius:99px; font-size:.72rem; font-weight:600;
  background:rgba(20,184,166,.16); color:#5eead4; border:1px solid rgba(94,234,212,.3); margin-left:8px; vertical-align:middle; }

.card { background: rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.09); border-radius:18px;
  padding:16px 18px; margin: 12px 0; backdrop-filter: blur(6px); }
.card h4 { margin:0 0 10px; font-size:.82rem; font-weight:600; color:#8fa3c0; letter-spacing:.06em; text-transform:uppercase; }
.muted { color:#8fa3c0; font-size:.84rem; }

.match { text-align:center; }
.match .lg { color:#8fa3c0; font-size:.8rem; margin-bottom:10px; }
.teams { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }
.team { flex:1; min-width:0; }
.team .nm { font-size:1.15rem; font-weight:700; margin:4px 0 2px; }
.team .tg { font-size:.74rem; color:#8fa3c0; }
.team .rk { display:inline-block; font-size:.74rem; padding:1px 9px; border-radius:99px; background:rgba(255,255,255,.08); color:#c8d4e8; }
.vs { align-self:center; font-weight:700; color:#6b7f9e; font-size:.9rem; padding:0 6px; }
.fc { display:inline-flex; width:22px; height:22px; border-radius:50%; align-items:center; justify-content:center;
  font-size:.68rem; font-weight:700; margin:6px 2px 0; color:#0b1220; }
.fc.w { background:#34d399; } .fc.d { background:#fbbf24; } .fc.l { background:#f87171; }

.pick { position:relative; overflow:hidden; border-radius:22px; padding:22px 24px; margin:14px 0;
  background: linear-gradient(135deg, #0f766e 0%, #14b8a6 55%, #22d3ee 120%); color:#04201d;
  box-shadow: 0 18px 50px rgba(20,184,166,.28); }
.pick.low { background: linear-gradient(135deg, #3b4560 0%, #56627f 60%, #6b7aa0 120%); color:#eef2fb; box-shadow: 0 18px 50px rgba(80,95,130,.3); }
.pick .top { display:flex; justify-content:space-between; align-items:center; }
.pick .badge { font-size:.74rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; opacity:.85; }
.pick .tier { font-size:.74rem; font-weight:700; padding:3px 11px; border-radius:99px; background:rgba(4,32,29,.16); }
.pick.low .tier { background:rgba(255,255,255,.16); }
.pick .lb { font-size:1.75rem; font-weight:700; line-height:1.2; margin:10px 0 4px; }
.pick .sub { font-size:.86rem; opacity:.85; }
.bar { height:8px; border-radius:99px; background:rgba(4,32,29,.2); margin:12px 0 4px; overflow:hidden; }
.bar > div { height:100%; border-radius:99px; background:#04201d; }
.pick.low .bar { background:rgba(255,255,255,.2); } .pick.low .bar > div { background:#fff; }
.flags { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.flag { font-size:.74rem; padding:3px 10px; border-radius:99px; background:rgba(4,32,29,.18); }
.pick.low .flag { background:rgba(255,255,255,.14); }

.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.tile { background:rgba(255,255,255,.05); border-radius:14px; padding:12px 8px; text-align:center; }
.tile .k { font-size:.72rem; color:#8fa3c0; } .tile .v { font-size:1.25rem; font-weight:700; margin:2px 0; } .tile .p { font-size:.74rem; color:#7dd3c8; }
.row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid rgba(255,255,255,.06); font-size:.92rem; }
.row:last-child { border-bottom:none; } .row .l { color:#9fb2cf; } .row .r { font-weight:600; text-align:right; }
.up { color:#34d399; } .down { color:#f87171; } .flat { color:#c8d4e8; }

.sig { padding:10px 0; border-bottom:1px solid rgba(255,255,255,.06); }
.sig:last-child { border-bottom:none; }
.sig .h { display:flex; justify-content:space-between; gap:10px; font-size:.9rem; font-weight:600; }
.sig .h .m { color:#5eead4; font-weight:500; font-size:.82rem; }
.sig .b { height:5px; border-radius:99px; background:rgba(255,255,255,.08); margin:7px 0 5px; overflow:hidden; }
.sig .b > div { height:100%; background:linear-gradient(90deg,#14b8a6,#22d3ee); border-radius:99px; }
.sig .n { font-size:.8rem; color:#8fa3c0; line-height:1.45; }

.chips { display:flex; flex-wrap:wrap; gap:7px; }
.chip { font-size:.8rem; padding:4px 12px; border-radius:99px; background:rgba(99,102,241,.16); color:#c7d2fe; border:1px solid rgba(165,180,252,.25); }
.chip.ok { background:rgba(52,211,153,.14); color:#6ee7b7; border-color:rgba(110,231,183,.3); }
.chip.bad { background:rgba(248,113,113,.14); color:#fca5a5; border-color:rgba(252,165,165,.3); }
.chip.off { background:rgba(255,255,255,.05); color:#8fa3c0; border-color:rgba(255,255,255,.08); }
ul.ev { margin:10px 0 0; padding-left:18px; color:#b8c7df; font-size:.86rem; line-height:1.6; }

.stat { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08); border-radius:16px; padding:14px 10px; text-align:center; }
.stat .v { font-size:1.45rem; font-weight:700; } .stat .k { font-size:.74rem; color:#8fa3c0; }
.res { border-radius:16px; padding:14px 18px; margin:12px 0; font-weight:600; }
.res.win { background:rgba(52,211,153,.14); border:1px solid rgba(110,231,183,.35); color:#6ee7b7; }
.res.lose { background:rgba(248,113,113,.13); border:1px solid rgba(252,165,165,.35); color:#fca5a5; }
.res.push { background:rgba(251,191,36,.12); border:1px solid rgba(253,224,71,.3); color:#fde68a; }
.hist { display:flex; justify-content:space-between; gap:10px; padding:9px 0; border-bottom:1px solid rgba(255,255,255,.06); font-size:.88rem; }
.hist:last-child { border-bottom:none; } .hist .a { min-width:0; } .hist .a small { color:#8fa3c0; display:block; }

.stButton > button { width:100%; border-radius:14px; font-weight:600; padding:.65rem 1rem; border:1px solid rgba(255,255,255,.12); }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#14b8a6,#6366f1); border:none; color:#fff;
  box-shadow:0 10px 28px rgba(20,184,166,.28); }
.stButton > button[kind="primary"]:hover { filter:brightness(1.08); }
[data-testid="stFileUploader"] section { border:1.5px dashed rgba(94,234,212,.4); border-radius:16px; background:rgba(255,255,255,.03); }
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:none; }
.stTabs [data-baseweb="tab"] { border-radius:12px; padding:8px 14px; background:rgba(255,255,255,.04); }
.stTabs [aria-selected="true"] { background:rgba(20,184,166,.18) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
[data-testid="stExpander"] { border:1px solid rgba(255,255,255,.08); border-radius:14px; background:rgba(255,255,255,.03); }
.tbl { overflow-x:auto; } .tbl table { width:100%; border-collapse:collapse; font-size:.82rem; }
.tbl th { text-align:left; color:#8fa3c0; font-weight:600; padding:6px 8px; border-bottom:1px solid rgba(255,255,255,.12); }
.tbl td { padding:6px 8px; border-bottom:1px solid rgba(255,255,255,.06); }
@media (max-width: 640px) { .pick .lb { font-size:1.4rem; } .grid3 { gap:6px; } .team .nm { font-size:1rem; } }
</style>
"""
if st.query_params.get("plain") != "1":      # ?plain=1 = ปิดการตกแต่ง CSS (ไว้ทดสอบ)
    st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- เครื่องมือช่วย
def esc(x):
    return _html.escape(str(x))


def secret(name):
    try:
        v = st.secrets[name]
    except Exception:
        v = os.environ.get(name)
    if v is None:
        return None
    v = str(v).strip().strip('"').strip("'").strip()
    return v or None


def card(title, body):
    st.markdown(f'<div class="card"><h4>{esc(title)}</h4>{body}</div>', unsafe_allow_html=True)


def html_table(headers, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def chips_html(items):
    return '<div class="chips">' + "".join(f'<span class="chip {c}">{esc(t)}</span>' for t, c in items) + "</div>"


def form_chips(seq):
    cls = {"W": "w", "D": "d", "L": "l"}
    return "".join(f'<span class="fc {cls.get(c, "d")}">{esc(c)}</span>' for c in str(seq or "").upper())


def market_th(mk, f):
    return {"HDP_HOME": f"แฮนดิแคป {f['home']}", "HDP_AWAY": f"แฮนดิแคป {f['away']}", "OU_OVER": "สูง (Over)",
            "OU_UNDER": "ต่ำ (Under)", "X12_HOME": f"1X2 {f['home']} ชนะ", "X12_AWAY": f"1X2 {f['away']} ชนะ"}.get(mk, mk)


def arrow(v, eps=1e-9):
    return ("up", "▲") if v > eps else (("down", "▼") if v < -eps else ("flat", "■"))


CTX_LABELS = [("derby", "ดาร์บี้"), ("high_scoring_league", "ลีกประตูเยอะ"), ("high_draw_league", "ลีกเสมอสูง"),
              ("high_volatility", "ลีกผันผวนสูง"), ("cup_group_stage", "ถ้วยรอบแบ่งกลุ่ม"), ("knockout", "น็อคเอาต์"),
              ("continental_cup", "ถ้วยทวีป"), ("late_goal_tendency", "ยิงท้ายเกมสูง")]
TYPE_TH = {"league": "ลีก", "cup": "ถ้วย", "playoff": "เพลย์ออฟ"}


# ---------------------------------------------------------------- รหัสผ่าน (ถ้าตั้งไว้)
_pw = secret("APP_PASSWORD")
if _pw and not st.session_state.get("auth"):
    st.markdown('<div class="hero"><div class="logo">⚽</div><div><div class="t">Football Quant</div>'
                '<div class="s">กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน</div></div></div>', unsafe_allow_html=True)
    entered = st.text_input("รหัสผ่าน", type="password", label_visibility="collapsed", placeholder="รหัสผ่าน")
    if entered:
        if hmac.compare_digest(str(entered), str(_pw)):
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

st.markdown('<div class="hero"><div class="logo">⚽</div><div><div class="t">Football Quant'
            '<span class="pill">V5.9</span></div><div class="s">วิเคราะห์ราคาบอลอัตโนมัติ · ฟันธงเดี่ยว · เรียนรู้จากผลจริง</div></div></div>',
            unsafe_allow_html=True)
ss = st.session_state


# ---------------------------------------------------------------- ตัวประมวลผลหลัก
def get_opts():
    ctx = {k: bool(ss.get("opt_" + k)) for k, _ in CTX_LABELS}
    return {"model": (ss.get("opt_model") or q.DEFAULT_MODEL).strip(),
            "api_key": q.get_api_key(secret) or (ss.get("opt_key") or "").strip() or None,
            "ctx": ctx, "league_size": int(ss.get("opt_league_size") or 0),
            "desp": ss.get("opt_desp") or "ไม่มี"}


def make_result(m, opts, ext_warn=(), research_err=None, save=True):
    m.pop("warnings", None)
    m, warns = q.validate_match(m)
    ctx = m["context"]
    ctx.update({k: True for k, v in opts["ctx"].items() if v})
    if opts["desp"] != "ไม่มี":
        ctx["desperation"] = "home" if opts["desp"] == "เจ้าบ้าน" else "away"
    if opts["league_size"] > 0:
        m["league_size"] = opts["league_size"]
    if not m.get("id"):
        m["id"] = q.slug(f"{m['home']}-vs-{m['away']}-{time.strftime('%Y%m%d-%H%M')}")
    store = q.Store(DATA_DIR)
    f, contribs, pick = q.analyze_match(m, store)
    saved = None
    if save:
        saved = q.record_prediction(store, m, f, contribs, pick)
    return {"m": m, "f": f, "contribs": contribs, "pick": pick, "warns": list(ext_warn) + warns,
            "research_err": research_err, "saved": saved, "report": q.render_report(m, f, contribs, pick, store)}


def run_pipeline(files, opts, do_research, save, box):
    with box:
        status = st.status("กำลังวิเคราะห์...", expanded=True)
    ext_warn, research_err = [], None
    try:
        with status:
            st.write("🖼 กำลังอ่านรูปด้วย Gemini ...")
            with tempfile.TemporaryDirectory() as td:
                paths = []
                for i, uf in enumerate(files, 1):
                    p = os.path.join(td, f"{i}_{os.path.basename(uf.name)}")
                    with open(p, "wb") as fh:
                        fh.write(uf.getbuffer())
                    paths.append(p)
                m = q.extract_from_images(paths, opts["model"], opts["api_key"])
            ext_warn = m.pop("warnings", None) or []
            if do_research:
                st.write("🔎 กำลังค้นหาข้อมูลบริบทแมตช์ (Google Search) ...")
                try:
                    r, srcs, qs = q.research_context(m.get("home"), m.get("away"), m.get("league"),
                                                     opts["model"], opts["api_key"])
                    q.apply_research(m, r, srcs, qs)
                except SystemExit as e:
                    research_err = str(e.code)
            st.write("📊 กำลังวิเคราะห์ราคาและฟันธง ...")
            res = make_result(m, opts, ext_warn, research_err, save)
            ss["match_json"] = json.dumps({k: v for k, v in res["m"].items() if k != "warnings"},
                                          ensure_ascii=False, indent=2, default=str)
            status.update(label="วิเคราะห์เสร็จแล้ว", state="complete", expanded=False)
        return res
    except SystemExit as e:
        status.update(label="เกิดข้อผิดพลาด", state="error")
        with box:
            st.error(str(e.code))
    except ValueError as e:
        status.update(label="ข้อมูลไม่ครบ", state="error")
        with box:
            st.error(f"อ่านข้อมูลจากรูปได้ไม่ครบ: {e}")
    except Exception as e:  # noqa
        status.update(label="เกิดข้อผิดพลาด", state="error")
        with box:
            st.error(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
    return None


# ---------------------------------------------------------------- แสดงผลลัพธ์
def render_result(res):
    m, f, contribs, pick = res["m"], res["f"], res["contribs"], res["pick"]
    rs = m.get("research") or {}
    tv = m.get("team_value") or {}
    fm = m.get("form") or {}

    def team(side, name, tag):
        rk = f["rank_home"] if side == "home" else f["rank_away"]
        v = tv.get(side)
        return (f'<div class="team">{"<span class=rk>อันดับ " + esc(f"{rk:g}") + "</span>" if rk is not None else ""}'
                f'<div class="nm">{esc(name)}</div><div class="tg">{tag}</div>'
                f'<div>{form_chips((fm.get(side) or {}).get("seq"))}</div>'
                f'{"<div class=tg>มูลค่าทีม " + esc(f"{v:g}") + "</div>" if v else ""}</div>')
    comp = rs.get("competition") or f["league"]
    card("แมตช์", f'<div class="match"><div class="lg">{esc(comp)}</div><div class="teams">'
         f'{team("home", f["home"], "เจ้าบ้าน")}<div class="vs">VS</div>{team("away", f["away"], "ทีมเยือน")}</div></div>')

    low = pick["tier"] == "ต่ำ"
    flags = []
    if pick.get("verify_fail"):
        flags.append("❌ เหย้า/เยือนไม่ผ่านการยืนยัน")
    if pick.get("move_only"):
        flags.append("⚠ มาจากการไหลของราคาล้วน (ลดคะแนนแล้ว)")
    if pick["veto"]:
        flags.append("🚫 แบน: " + ", ".join(market_th(v, f) for v in pick["veto"]))
    if low:
        flags.append("สัญญาณอ่อน · ควรลดสัดส่วนเดิมพัน")
    st.markdown(
        f'<div class="pick{" low" if low else ""}"><div class="top"><span class="badge">สัญญาณฟันธงเดี่ยว</span>'
        f'<span class="tier">ระดับ{esc(pick["tier"])}</span></div><div class="lb">{esc(pick["label"])}</div>'
        f'<div class="sub">ใช้ราคาปัจจุบัน · ความมั่นใจเชิงสัญญาณ {pick["confidence"]:.0f}%</div>'
        f'<div class="bar"><div style="width:{pick["confidence"]:.0f}%"></div></div>'
        f'<div class="flags">{"".join(f"<span class=flag>{esc(x)}</span>" for x in flags)}</div></div>',
        unsafe_allow_html=True)
    st.caption("ความมั่นใจนี้แปลงจากคะแนนสัญญาณ ยังไม่ผ่านการสอบเทียบกับผลจริง ไม่ใช่ความน่าจะเป็นที่แท้จริง")

    # ราคาปัจจุบัน
    xc = f["x12_cur"]
    pc = q.implied(xc)
    hw = f["fav_water_c"] if f["fav"] == "home" else f["dog_water_c"]
    aw = f["dog_water_c"] if f["fav"] == "home" else f["fav_water_c"]
    tiles = "".join(f'<div class="tile"><div class="k">{k}</div><div class="v">{o:.2f}</div><div class="p">{p:.0%}</div></div>'
                    for k, o, p in (("เหย้า", xc[0], pc[0]), ("เสมอ", xc[1], pc[1]), ("เยือน", xc[2], pc[2])))
    rows = (f'<div class="row"><span class="l">แฮนดิแคป</span><span class="r">{esc(f["home"])} {esc(q.fmt_line(f["line_c"]))}'
            f' <span class="muted">น้ำ {hw:.2f}</span> · {esc(f["away"])} <span class="muted">น้ำ {aw:.2f}</span></span></div>')
    if f["has_ou"]:
        rows += (f'<div class="row"><span class="l">สูง/ต่ำ</span><span class="r">{f["ou_c"]:g} '
                 f'<span class="muted">สูง {f["over_water_c"]:.2f} · ต่ำ {f["under_water_c"]:.2f}</span></span></div>')
    card("ราคาปัจจุบัน (ราคาหลักที่ใช้ตัดสิน)", f'<div class="grid3">{tiles}</div><div style="margin-top:10px">{rows}</div>')

    # การไหลของราคา
    c1, a1 = arrow(f["hdp_shift_fav"])
    c2, a2 = arrow(f["x12_pp"], 0.5)
    flow = (f'<div class="row"><span class="l">เรตแฮนดิแคป (ทีมต่อ {esc(f["fav_name"])})</span><span class="r {c1}">'
            f'{esc(q.fmt_line(f["line_o"]))} → {esc(q.fmt_line(f["line_c"]))} {a1}</span></div>'
            f'<div class="row"><span class="l">พูล 1X2 ทีมต่อ</span><span class="r {c2}">{f["x12_pp"]:+.1f} จุด % {a2}</span></div>')
    if f["has_ou"]:
        c3, a3 = arrow(f["ou_shift"])
        flow += (f'<div class="row"><span class="l">เรตสูง/ต่ำ</span><span class="r {c3}">{f["ou_o"]:g} → {f["ou_c"]:g} {a3}</span></div>')
    flow += f'<div class="muted" style="margin-top:6px">ความขัดแย้งพูล↔แฮนดิแคป {f["conflict"]:.0%} · ราคาเปิดใช้อ้างอิงการไหลเท่านั้น</div>'
    card("การไหลของราคา", flow)

    # สัญญาณหลัก
    top = sorted(contribs, key=lambda c: -c["eff"])[:5]
    if top:
        mx = max(c["eff"] for c in top) or 1
        body = "".join(
            f'<div class="sig"><div class="h"><span>{esc(q.RULE_NAMES.get(c["rule"], "Rule ที่เรียนรู้เอง"))}</span>'
            f'<span class="m">{esc(market_th(c["market"], f))} · {c["eff"]:+.2f}</span></div>'
            f'<div class="b"><div style="width:{max(c["eff"] / mx * 100, 4):.0f}%"></div></div>'
            f'<div class="n">{esc(c["note"])}</div></div>' for c in top)
    else:
        body = '<div class="muted">ไม่มี Rule ใดทำงาน</div>'
    card("สัญญาณที่ใช้ตัดสิน", body)

    # บริบทแมตช์
    ctx = m.get("context") or {}
    items = [(TYPE_TH.get(ctx.get("type", "league"), "ลีก"), "")]
    items += [(lb, "") for k, lb in CTX_LABELS if ctx.get(k)]
    if ctx.get("desperation") in ("home", "away"):
        items.append(("หนีตาย/ลุ้นหนัก: " + (f["home"] if ctx["desperation"] == "home" else f["away"]), ""))
    if len(items) == 1:
        items.append(("ไม่พบบริบทพิเศษ", "off"))
    ctx_body = chips_html(items)
    if rs.get("evidence"):
        ctx_body += '<ul class="ev">' + "".join(f"<li>{esc(x)}</li>" for x in rs["evidence"]) + "</ul>"
    conf = {"high": "สูง", "medium": "ปานกลาง", "low": "ต่ำ"}.get(rs.get("confidence"))
    title = "บริบทแมตช์ (ค้นหาอัตโนมัติ" + (f" · ความน่าเชื่อถือ{conf}" if conf else "") + ")" if rs else "บริบทแมตช์"
    card(title, ctx_body)
    if res.get("research_err"):
        st.warning(f"ค้นหาบริบทอัตโนมัติไม่สำเร็จ (ใช้ค่าตั้งต้นแทน): {res['research_err']}")
    if rs.get("sources"):
        with st.expander("แหล่งข้อมูลที่ Gemini ใช้ค้นหา"):
            for s_ in rs["sources"]:
                st.markdown(f"- [{s_['title'] or s_['uri']}]({s_['uri']})" if s_["uri"] else f"- {s_['title']}")

    # ยืนยันเหย้า/เยือน
    ok_n = sum(1 for ok, _ in f["verify"] if ok)
    vc = "ok" if not f["verify_fail"] else "bad"
    card("Home/Away Verification", chips_html([(f"{'ผ่าน' if not f['verify_fail'] else 'ไม่ผ่าน'} {ok_n}/{len(f['verify'])} ข้อ", vc)]))
    with st.expander("รายละเอียดการตรวจเหย้า/เยือน"):
        for ok, txt in f["verify"]:
            st.write(("✅ " if ok else "❌ ") + txt)

    if res["warns"]:
        with st.expander(f"คำเตือนจากการอ่านข้อมูล ({len(res['warns'])})"):
            for w in res["warns"]:
                st.write("• " + w)
    with st.expander("รายงานฉบับเต็ม"):
        st.text(res["report"])
    if res.get("saved"):
        mid, ok = res["saved"]
        st.success("บันทึกสัญญาณแล้ว → ใส่ผลจริงที่แท็บ “บันทึกผล” หลังจบเกม" if ok
                   else "ไม่บันทึก: รายการนี้ถูกบันทึกผลไปแล้ว")


# ---------------------------------------------------------------- แท็บ
tab1, tab2, tab3, tab4 = st.tabs(["🎯 วิเคราะห์", "🏁 บันทึกผล", "📈 สถิติ", "💾 สำรองข้อมูล"])

# ================================================================ TAB 1
with tab1:
    ss.setdefault("up_ver", 0)            # เปลี่ยนเลขเวอร์ชันของ key = ล้างรูปที่อัปโหลดทิ้งทันที
    files = st.file_uploader("อัปโหลดรูป 5 รูป: ภาพสรุปแมตช์ · 1X2 · Handicap · Over/Under · H2H",
                             type=["png", "jpg", "jpeg", "webp", "gif"], accept_multiple_files=True,
                             key=f"uploader_{ss['up_ver']}")
    if ss.pop("cleared_msg", False):
        st.caption("🧹 ล้างรูปที่อัปโหลดออกแล้ว (ระบบไม่เก็บรูปไว้)")
    t1, t2 = st.columns(2)
    do_research = t1.toggle("ค้นหาบริบทแมตช์อัตโนมัติ", value=True, key="opt_research",
                            help="ให้ Gemini ค้นหาข้อมูลจริงทาง Google Search (คิดค่าบริการตามจำนวนคำค้น)")
    do_save = t2.toggle("บันทึกสัญญาณลงประวัติ", value=True, key="opt_save")
    go = st.button("🚀 วิเคราะห์อัตโนมัติ", type="primary", disabled=not files)
    box = st.container()
    opts = get_opts()
    if go:
        if not opts["api_key"]:
            with box:
                st.error("ยังไม่ได้ตั้งค่า GEMINI_API_KEY (ใส่ที่ Secrets หรือช่องใน “ตั้งค่าขั้นสูง”)")
        else:
            res = run_pipeline(files, opts, do_research, do_save, box)
            if res:
                ss["res"] = res
                ss["up_ver"] += 1             # วิเคราะห์สำเร็จ -> เคลียร์รูปทันที (ถ้าล้มเหลวจะคงรูปไว้ให้ลองใหม่)
                ss["cleared_msg"] = True
                st.rerun()
    if ss.get("res"):
        with box:
            render_result(ss["res"])

    with st.expander("⚙ ตั้งค่าขั้นสูง"):
        st.text_input("โมเดล Gemini", value=q.DEFAULT_MODEL, key="opt_model")
        if not q.get_api_key(secret):
            st.text_input("GEMINI_API_KEY", type="password", key="opt_key", help="ใช้อ่านรูปเท่านั้น ไม่ถูกบันทึก")
        else:
            st.caption("✅ พบ API key ใน Secrets แล้ว")
        st.caption("บังคับบริบท (ติ๊กเพื่อบังคับเป็น “ใช่” ทับผลค้นหา)")
        cols = st.columns(2)
        for i, (k, lb) in enumerate(CTX_LABELS):
            cols[i % 2].checkbox(lb, key="opt_" + k)
        c1, c2 = st.columns(2)
        c1.number_input("จำนวนทีมในลีก (0 = ไม่ระบุ)", 0, 40, 0, key="opt_league_size")
        c2.selectbox("ทีมที่หนีตาย/ลุ้นหนัก", ["ไม่มี", "เจ้าบ้าน", "ทีมเยือน"], key="opt_desp")
        st.divider()
        st.caption("แก้ไขข้อมูลแมตช์เอง แล้ววิเคราะห์ใหม่")
        ss.setdefault("match_json", json.dumps(q.TEMPLATE, ensure_ascii=False, indent=2))
        jf = st.file_uploader("หรือโหลดไฟล์ข้อมูลแมตช์", type=["json"], key="jsonfile")
        if jf is not None and st.button("โหลดไฟล์ที่อัปโหลด"):
            ss["match_json"] = jf.getvalue().decode("utf-8")
            st.rerun()
        st.text_area("ข้อมูลแมตช์", key="match_json", height=300, label_visibility="collapsed")
        if st.button("วิเคราะห์ใหม่จากข้อมูลที่แก้ไข"):
            try:
                m2 = json.loads(ss["match_json"])
                ss["res"] = make_result(m2, get_opts(), save=bool(ss.get("opt_save", True)))
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"รูปแบบข้อมูลไม่ถูกต้อง: {e}")
            except ValueError as e:
                st.error(f"ข้อมูลไม่ครบ/ไม่ถูกต้อง: {e}")

# ================================================================ TAB 2
with tab2:
    store = q.Store(DATA_DIR)
    pend = {r["id"]: r for r in store.history if r["status"] == "pending"}
    if not pend:
        st.markdown('<div class="card"><div class="muted">ยังไม่มีสัญญาณที่รอผล — วิเคราะห์ในแท็บแรกโดยเปิด “บันทึกสัญญาณลงประวัติ”</div></div>',
                    unsafe_allow_html=True)
    else:
        rid = st.selectbox("เลือกแมตช์ที่จบแล้ว", list(pend), label_visibility="collapsed",
                           format_func=lambda i: f"{pend[i]['features']['home']} vs {pend[i]['features']['away']} — {pend[i]['pick']['label']}")
        rec = pend[rid]
        fe = rec["features"]
        card("สัญญาณที่ฟันธงไว้", f'<div class="row"><span class="l">{esc(fe["home"])} vs {esc(fe["away"])}</span>'
             f'<span class="r">{esc(rec["pick"]["label"])}</span></div>')
        c1, c2 = st.columns(2)
        hg = c1.number_input(f"ประตู {fe['home']}", 0, 30, 0)
        ag = c2.number_input(f"ประตู {fe['away']}", 0, 30, 0)
        if st.button("✅ บันทึกผลจริง & ให้ระบบเรียนรู้", type="primary"):
            outcomes, r, pf, changes, new = q.do_settle(store, rec, int(hg), int(ag))
            cls = "win" if r > 0 else "lose" if r < 0 else "push"
            st.markdown(f'<div class="res {cls}">{esc(fe["home"])} {int(hg)}-{int(ag)} {esc(fe["away"])} · '
                        f'{esc(rec["pick"]["label"])} → {q.result_word(r)} ({pf:+.2f} หน่วย)</div>', unsafe_allow_html=True)
            card("ผลของแต่ละตลาด", "".join(
                f'<div class="row"><span class="l">{esc(market_th(k, fe))}</span><span class="r">{q.result_word(v[0])}</span></div>'
                for k, v in outcomes.items()))
            if changes:
                card("ระบบปรับน้ำหนัก Rule", "".join(
                    f'<div class="row"><span class="l">{esc(q.RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง"))}</span>'
                    f'<span class="r {"up" if n > o else "down" if n < o else "flat"}">{o:.2f} → {n:.2f}</span></div>'
                    for k, (o, n, rr) in changes.items()))
            for r_ in new:
                st.success(f"🧠 ระบบสร้าง Rule ใหม่ {r_['id']}: [{' + '.join(r_['tags'])}] → {q.ROLE_TH[r_['role']]} "
                           f"(ชนะ {r_['wr']:.0%} จาก {r_['n']} นัด)")
        with st.expander("🗑 ลบรายการนี้ (ถ้าไม่ต้องการ)"):
            sure = st.checkbox("ยืนยันลบรายการที่เลือกอยู่", key=f"del_{rid}")
            if st.button("ลบรายการนี้", disabled=not sure):
                q.delete_records(store, [rid])
                st.rerun()

# ================================================================ TAB 3
with tab3:
    store = q.Store(DATA_DIR)
    S = store.state
    done = [r for r in store.history if r["status"] == "settled"]
    pend_n = sum(1 for r in store.history if r["status"] == "pending")
    w_ = sum(r["pick_r"] > 0 for r in done)
    l_ = sum(r["pick_r"] < 0 for r in done)
    pr = sum(r["pick_profit"] for r in done)
    vals = [("บันทึกผลแล้ว", len(done)), ("รอผล", pend_n), ("ชนะ/แพ้", f"{w_}/{l_}"), ("กำไรสุทธิ", f"{pr:+.2f}"),
            ("ROI ต่อไม้", f"{pr / len(done):+.1%}" if done else "-")]
    st.markdown('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px">' + "".join(
        f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{k}</div></div>' for k, v in vals) + "</div>",
        unsafe_allow_html=True)
    recent = list(reversed(store.history))[:10]
    if recent:
        rows = ""
        for r in recent:
            fe = r["features"]
            if r["status"] == "settled":
                cls = "up" if r["pick_r"] > 0 else "down" if r["pick_r"] < 0 else "flat"
                tail = f'<span class="{cls}">{q.result_word(r["pick_r"])} ({r["pick_profit"]:+.2f})</span>'
            else:
                tail = '<span class="muted">รอผล</span>'
            rows += (f'<div class="hist"><div class="a">{esc(fe["home"])} vs {esc(fe["away"])}<small>{esc(r["pick"]["label"])}</small></div>'
                     f'<div>{tail}</div></div>')
        card("รายการล่าสุด", rows)
    with st.expander("น้ำหนัก Rule ปัจจุบัน"):
        st.markdown(html_table(["Rule", "ชื่อ", "น้ำหนัก", "ใช้ (ครั้ง)"],
                               [[k, q.RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง"), f"{v:.3f}", S["rule_stats"].get(k, {}).get("n", 0)]
                                for k, v in sorted(S["weights"].items())]), unsafe_allow_html=True)
    with st.expander(f"🧠 Rule ที่ระบบสร้างเอง ({len(S['learned_rules'])})"):
        if S["learned_rules"]:
            st.markdown(html_table(["id", "สถานะ", "เงื่อนไข", "เล่น", "ชนะ", "นัด"],
                                   [[r["id"], "เปิด" if r.get("enabled", True) else "ปิด", " + ".join(r["tags"]),
                                     q.ROLE_TH[r["role"]], f"{r['wr']:.0%}", r["n"]] for r in S["learned_rules"]]),
                        unsafe_allow_html=True)
        else:
            st.caption("ยังไม่มี — ต้องสะสมผลจริงอย่างน้อย ~10 นัดที่มีรูปแบบซ้ำกัน")
        if st.button("ค้นหา Rule ใหม่จากประวัติอีกครั้ง"):
            new = q.discover_rules(store, verbose=False)
            store.save()
            st.success(f"สร้าง Rule ใหม่ {len(new)} ข้อ") if new else st.info("ยังไม่พบรูปแบบใหม่ที่มีนัยสำคัญ")
    with st.expander("🗑 ลบรายการในประวัติ"):
        opts_h = {r["id"]: f"{r['features']['home']} vs {r['features']['away']} ({'ผลแล้ว' if r['status'] == 'settled' else 'รอผล'})"
                  for r in reversed(store.history)}
        pick_ids = st.multiselect("เลือกรายการที่จะลบ", list(opts_h), format_func=lambda i: opts_h[i])
        st.caption("การลบรายการที่บันทึกผลแล้วจะไม่ย้อนน้ำหนัก Rule ที่เคยปรับไปแล้ว")
        if st.button("ลบที่เลือก", disabled=not (pick_ids and st.checkbox("ยืนยันการลบ", key="confirm_hist_del"))):
            q.delete_records(store, pick_ids)
            st.rerun()

# ================================================================ TAB 4
with tab4:
    store = q.Store(DATA_DIR)
    card("สำรองข้อมูลการเรียนรู้",
         '<div class="muted">เก็บน้ำหนัก Rule, Rule ที่ระบบสร้างเอง และประวัติทั้งหมดเป็นไฟล์เดียว '
         'บน Streamlit Cloud ข้อมูลจะหายเมื่อแอปรีสตาร์ท ควรสำรองหลังบันทึกผลทุกครั้ง</div>')
    blob = json.dumps({"state": store.state, "history": store.history}, ensure_ascii=False, indent=1)
    st.download_button("⬇ ดาวน์โหลดไฟล์สำรอง", blob, file_name=f"quant_backup_{time.strftime('%Y%m%d')}.json",
                       mime="application/json")
    up = st.file_uploader("กู้คืนจากไฟล์สำรอง (เขียนทับข้อมูลปัจจุบัน)", type=["json"], key="restore")
    if up is not None and st.button("♻ กู้คืน", type="primary"):
        try:
            d = json.loads(up.getvalue().decode("utf-8"))
            assert "state" in d and "history" in d
            store.state, store.history = d["state"], d["history"]
            for k, v in q.DEFAULT_WEIGHTS.items():
                store.state["weights"].setdefault(k, v)
            store.save()
            st.success("กู้คืนสำเร็จ")
        except Exception:  # noqa
            st.error("ไฟล์สำรองไม่ถูกต้อง")
