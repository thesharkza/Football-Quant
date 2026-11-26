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
    st.write("✓ เซิร์ฟเวอร์ Streamlit ทำงาน และส่งหน้านี้ถึงเบราว์เซอร์ได้")
    st.write(f"Streamlit {st.__version__} · Python {platform.python_version()}")
    try:
        import football_quant_v58 as _q
        st.write(f"✓ โหลดตัวคำนวณได้ (Rule {len(_q.RULES)} ข้อ)")
    except Exception as _e:  # noqa
        st.write(f"✕ โหลดตัวคำนวณไม่ได้: {str(_e)[:200]}")
    st.write("ถ้าเห็นหน้านี้ แสดงว่าปัญหาอยู่ที่ส่วนหน้าตา/การแสดงผลของแอปหลัก ไม่ใช่เซิร์ฟเวอร์หรือเครือข่าย")
    st.stop()

import football_quant_v58 as q
import dashboard as d
import theme as _theme
import backtest as bt
import access
import story as STORY
import story_pages as SP

DATA_DIR = os.environ.get("QUANT_DATA_DIR", "quant_data")

CSS = """
<style>
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: -apple-system, BlinkMacSystemFont, 'Sukhumvit Set', 'Thonburi', 'Noto Sans Thai', 'Segoe UI', Tahoma, sans-serif !important; }
.stApp { background: radial-gradient(900px 420px at 12% -8%, rgba(45,212,191,.14), transparent 60%),
                     radial-gradient(800px 380px at 100% 0%, rgba(139,147,248,.13), transparent 55%),
                     linear-gradient(180deg, #0b0f15 0%, #0b0f15 100%); }
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
.stDeployButton, [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1040px; }
h1, h2, h3 { letter-spacing: -.01em; }

.hero { display:flex; align-items:center; gap:14px; margin: 4px 0 18px; }
.hero .logo { width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:24px; background: linear-gradient(135deg,#2dd4bf,#8b93f8); box-shadow: 0 8px 24px rgba(45,212,191,.35); }
.hero .t { font-size:1.45rem; font-weight:700; line-height:1.1; }
.hero .s { color:#a9b4c4; font-size:.86rem; margin-top:2px; }
.pill { display:inline-block; padding:2px 10px; border-radius:99px; font-size:.72rem; font-weight:600;
  background:rgba(45,212,191,.16); color:#2dd4bf; border:1px solid rgba(45,212,191,.3); margin-left:8px; vertical-align:middle; }

.card { background: rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.09); border-radius:18px;
  padding:16px 18px; margin: 12px 0; backdrop-filter: blur(6px); }
.card h4 { margin:0 0 10px; font-size:.82rem; font-weight:600; color:#a9b4c4; letter-spacing:.06em; text-transform:uppercase; }
.muted { color:#a9b4c4; font-size:.84rem; }

.match { text-align:center; }
.match .lg { color:#a9b4c4; font-size:.8rem; margin-bottom:10px; }
.teams { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }
.team { flex:1; min-width:0; }
.team .nm { font-size:1.15rem; font-weight:700; margin:4px 0 2px; }
.team .tg { font-size:.74rem; color:#a9b4c4; }
.team .rk { display:inline-block; font-size:.74rem; padding:1px 9px; border-radius:99px; background:rgba(255,255,255,.08); color:#a9b4c4; }
.vs { align-self:center; font-weight:700; color:#7f8ba0; font-size:.9rem; padding:0 6px; }
.fc { display:inline-flex; width:22px; height:22px; border-radius:50%; align-items:center; justify-content:center;
  font-size:.68rem; font-weight:700; margin:6px 2px 0; color:#0b0f15; }
.fc.w { background:#3ddc97; } .fc.d { background:#f5b942; } .fc.l { background:#ff6b6b; }

.pick { position:relative; overflow:hidden; border-radius:22px; padding:22px 24px; margin:14px 0;
  background: linear-gradient(135deg, #2dd4bf 0%, #2dd4bf 55%, #2dd4bf 120%); color:#042f2b;
  box-shadow: 0 18px 50px rgba(45,212,191,.28); }
.pick.low { background: linear-gradient(135deg, #3b4560 0%, #56627f 60%, #6b7aa0 120%); color:#e9eef5; box-shadow: 0 18px 50px rgba(80,95,130,.3); }
.pick .top { display:flex; justify-content:space-between; align-items:center; }
.pick .badge { font-size:.74rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; opacity:.85; }
.pick .tier { font-size:.74rem; font-weight:700; padding:3px 11px; border-radius:99px; background:rgba(4,47,43,.16); }
.pick.low .tier { background:rgba(255,255,255,.16); }
.pick .lb { font-size:1.75rem; font-weight:700; line-height:1.2; margin:10px 0 4px; }
.pick .sub { font-size:.86rem; opacity:.85; }
.bar { height:8px; border-radius:99px; background:rgba(4,47,43,.2); margin:12px 0 4px; overflow:hidden; }
.bar > div { height:100%; border-radius:99px; background:#042f2b; }
.pick.low .bar { background:rgba(255,255,255,.2); } .pick.low .bar > div { background:#fff; }
.flags { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.flag { font-size:.74rem; padding:3px 10px; border-radius:99px; background:rgba(4,47,43,.18); }
.pick.low .flag { background:rgba(255,255,255,.14); }

.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.tile { background:rgba(255,255,255,.05); border-radius:14px; padding:12px 8px; text-align:center; }
.tile .k { font-size:.72rem; color:#a9b4c4; } .tile .v { font-size:1.25rem; font-weight:700; margin:2px 0; } .tile .p { font-size:.74rem; color:#2dd4bf; }
.row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid rgba(255,255,255,.06); font-size:.92rem; }
.row:last-child { border-bottom:none; } .row .l { color:#9fb2cf; } .row .r { font-weight:600; text-align:right; }
.up { color:#3ddc97; } .down { color:#ff6b6b; } .flat { color:#a9b4c4; }

.sig { padding:10px 0; border-bottom:1px solid rgba(255,255,255,.06); }
.sig:last-child { border-bottom:none; }
.sig .h { display:flex; justify-content:space-between; gap:10px; font-size:.9rem; font-weight:600; }
.sig .h .m { color:#2dd4bf; font-weight:500; font-size:.82rem; }
.sig .b { height:5px; border-radius:99px; background:rgba(255,255,255,.08); margin:7px 0 5px; overflow:hidden; }
.sig .b > div { height:100%; background:linear-gradient(90deg,#2dd4bf,#2dd4bf); border-radius:99px; }
.sig .n { font-size:.8rem; color:#a9b4c4; line-height:1.45; }

.chips { display:flex; flex-wrap:wrap; gap:7px; }
.chip { font-size:.8rem; padding:4px 12px; border-radius:99px; background:rgba(139,147,248,.16); color:#8b93f8; border:1px solid rgba(139,147,248,.25); }
.chip.ok { background:rgba(61,220,151,.14); color:#3ddc97; border-color:rgba(61,220,151,.3); }
.chip.bad { background:rgba(255,107,107,.14); color:#ff6b6b; border-color:rgba(255,107,107,.3); }
.chip.off { background:rgba(255,255,255,.05); color:#a9b4c4; border-color:rgba(255,255,255,.08); }
ul.ev { margin:10px 0 0; padding-left:18px; color:#a9b4c4; font-size:.86rem; line-height:1.6; }

.stat { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08); border-radius:16px; padding:14px 10px; text-align:center; }
.stat .v { font-size:1.45rem; font-weight:700; } .stat .k { font-size:.74rem; color:#a9b4c4; }
.res { border-radius:16px; padding:14px 18px; margin:12px 0; font-weight:600; }
.res.win { background:rgba(61,220,151,.14); border:1px solid rgba(61,220,151,.35); color:#3ddc97; }
.res.lose { background:rgba(255,107,107,.13); border:1px solid rgba(255,107,107,.35); color:#ff6b6b; }
.res.push { background:rgba(245,185,66,.12); border:1px solid rgba(245,185,66,.3); color:#f5b942; }
.hist { display:flex; justify-content:space-between; gap:10px; padding:9px 0; border-bottom:1px solid rgba(255,255,255,.06); font-size:.88rem; }
.hist:last-child { border-bottom:none; } .hist .a { min-width:0; } .hist .a small { color:#a9b4c4; display:block; }

.stButton > button { width:100%; border-radius:14px; font-weight:600; padding:.65rem 1rem; border:1px solid rgba(255,255,255,.12); }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#2dd4bf,#8b93f8); border:none; color:#fff;
  box-shadow:0 10px 28px rgba(45,212,191,.28); }
.stButton > button[kind="primary"]:hover { filter:brightness(1.08); }
.stButton > button:disabled { opacity:.42; box-shadow:none !important; cursor:not-allowed; filter:none !important; }
[data-testid="stFileUploader"] section { border:1.5px dashed rgba(45,212,191,.4); border-radius:16px; background:rgba(255,255,255,.03); }
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:none; }
.stTabs [data-baseweb="tab"] { border-radius:12px; padding:8px 14px; background:rgba(255,255,255,.04); }
.stTabs [aria-selected="true"] { background:rgba(45,212,191,.18) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
[data-testid="stExpander"] { border:1px solid rgba(255,255,255,.08); border-radius:14px; background:rgba(255,255,255,.03); }
.tbl { overflow-x:auto; } .tbl table { width:100%; border-collapse:collapse; font-size:.82rem; }
.tbl th { text-align:left; color:#a9b4c4; font-weight:600; padding:6px 8px; border-bottom:1px solid rgba(255,255,255,.12); }
.tbl td { padding:6px 8px; border-bottom:1px solid rgba(255,255,255,.06); }
@media (max-width: 640px) { .pick .lb { font-size:1.4rem; } .grid3 { gap:6px; } .team .nm { font-size:1rem; } }
</style>
"""
CSS = CSS.replace("</style>", d.CSS + bt.CSS + STORY.RUNTIME_CSS.replace(":host { display:block; }", "") + "</style>")
CSS = CSS.replace("<style>", "<style>" + _theme.FONT_IMPORT, 1).replace("</style>", _theme.APP_CSS + "</style>")   # design system V2
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


for _k in ("SHEETS_URL", "SHEETS_TOKEN", "GITHUB_TOKEN", "GIST_ID"):          # ส่งค่าจาก Secrets ให้ตัวซิงก์ข้อมูล
    _v = secret(_k)
    if _v:
        os.environ[_k] = _v


def show(html_str, key, on_act=False):
    """แสดงหน้าเรื่องเล่า (มีแอนิเมชัน/กราฟโต้ตอบ) · ถ้าเบราว์เซอร์/เวอร์ชันไม่รองรับ จะแสดงแบบนิ่งแทน"""
    try:
        return STORY.mount(html_str, key=key, on_act=on_act)
    except Exception:  # noqa
        st.markdown(html_str, unsafe_allow_html=True)
        return None


def cloud_warn():
    rs = q.REMOTE_STATE
    if rs.get("enabled") and rs.get("ok") is False:
        st.warning(f"บันทึกในเครื่องแล้ว แต่ซิงก์ขึ้นคลาวด์ไม่สำเร็จ: {rs.get('error')}")


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
              ("continental_cup", "ถ้วยทวีป"), ("late_goal_tendency", "ยิงท้ายเกมสูง"),
              ("women_or_regional", "ฟุตบอลหญิง/ลีกรอง"), ("asian_cup", "ถ้วยเอเชีย")]
TYPE_TH = {"league": "ลีก", "cup": "ถ้วย", "playoff": "เพลย์ออฟ"}


# ---------------------------------------------------------------- รหัสผ่าน + หมดเวลาเมื่อไม่ได้ใช้งาน
_pw = secret("APP_PASSWORD")
try:
    IDLE_SEC = 60 * max(1, int(secret("SESSION_MINUTES") or 10))
except ValueError:
    IDLE_SEC = 600


def _clear_token_param():
    if "s" in st.query_params:
        del st.query_params["s"]


def _auth_configured():
    try:
        return "auth" in st.secrets and bool(st.secrets["auth"].get("client_id"))
    except Exception:  # noqa
        return False


AUTH_ON = _auth_configured()
ADMINS = access.admin_emails(secret)
ROLE, EMAIL = "admin", None
_GKEY = None


def _hero(sub):
    st.markdown('<div class="hero"><div class="logo">FQ</div><div><div class="t">Football Quant</div>'
                f'<div class="s">{esc(sub)}</div></div></div>', unsafe_allow_html=True)


if AUTH_ON:
    # ---- ล็อกอินด้วย Google + สิทธิ์ 3 ระดับ (Admin / User / Local) ----
    if not st.user.is_logged_in:
        _hero("เข้าสู่ระบบด้วยบัญชี Google ที่ได้รับเชิญ")
        if st.session_state.pop("idle_out", False):
            st.info(f"หมดเวลาเพราะไม่ได้ใช้งานเกิน {IDLE_SEC // 60} นาที กรุณาเข้าสู่ระบบใหม่")
        st.button("เข้าสู่ระบบด้วย Google", type="primary", on_click=st.login)
        st.stop()
    EMAIL = access.norm(st.user.get("email"))
    ROLE = access.role_of(EMAIL, ADMINS, access.load(DATA_DIR))
    if ROLE is None:
        _hero("บัญชีนี้ยังไม่ได้รับเชิญ")
        st.warning(f"อีเมล {EMAIL or '(ไม่ทราบ)'} ยังไม่ได้รับเชิญให้ใช้งาน · ส่งอีเมลนี้ให้ผู้ดูแลระบบเพื่อขอสิทธิ์")
        st.button("ออกจากระบบ", on_click=st.logout)
        st.stop()
    _GKEY = "g:" + EMAIL
    if _GKEY in q.SESSIONS and not q.session_touch(_GKEY, IDLE_SEC):
        st.session_state["idle_out"] = True       # หมดเวลา -> ออกจากระบบ ต้องล็อกอินใหม่
        st.logout()
        st.stop()
    q.SESSIONS[_GKEY] = time.time()
elif _pw:
    # โทเค็นอยู่ในลิงก์ (?s=...) จึงรอดเมื่อมือถือพับแอป/เชื่อมต่อใหม่ แต่หมดอายุทันทีเมื่อเว้นว่างเกินเวลา
    _tok = st.session_state.get("tok") or st.query_params.get("s")
    if _tok and q.session_touch(_tok, IDLE_SEC):
        st.session_state["tok"] = _tok
        if st.query_params.get("s") != _tok:
            st.query_params["s"] = _tok
    else:
        st.session_state.pop("tok", None)
        _clear_token_param()
        st.markdown('<div class="hero"><div class="logo">FQ</div><div><div class="t">Football Quant</div>'
                    '<div class="s">กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน</div></div></div>', unsafe_allow_html=True)
        if _tok:
            st.info(f"หมดเวลาเพราะไม่ได้ใช้งานเกิน {IDLE_SEC // 60} นาที กรุณาใส่รหัสผ่านใหม่")
        entered = st.text_input("รหัสผ่าน", type="password", label_visibility="collapsed", placeholder="รหัสผ่าน")
        if entered:
            if hmac.compare_digest(str(entered), str(_pw)):
                _new = q.session_new()
                st.session_state["tok"] = _new
                st.query_params["s"] = _new
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
        st.stop()


@st.fragment(run_every=15)
def idle_guard():
    """ตรวจเบื้องหลังทุก 15 วินาที: ถ้าเกินเวลาไม่ได้ใช้งาน ให้กลับหน้าเข้าสู่ระบบทันที (ไม่ต่ออายุเอง)"""
    if not q.session_alive(_GKEY if AUTH_ON else st.session_state.get("tok"), IDLE_SEC):
        st.rerun()


st.markdown('<div class="hero"><div class="logo">FQ</div><div><div class="t">Football Quant'
            '<span class="pill">V5.9</span></div><div class="s">วิเคราะห์ราคาบอลอัตโนมัติ · ฟันธงเดี่ยว · เรียนรู้จากผลจริง</div></div></div>',
            unsafe_allow_html=True)
ss = st.session_state
IS_ADMIN = ROLE == "admin"
if not AUTH_ON and not _pw:
    st.warning("! ยังไม่ได้ตั้งค่าการเข้าสู่ระบบ (ไม่มี [auth] และไม่มี APP_PASSWORD ใน Secrets) — ทุกคนที่มีลิงก์เข้าใช้ได้เต็มสิทธิ์ Admin "
               "รวมถึงใช้ API key ของคุณ ถ้าแอปนี้เปิดสาธารณะ ให้ตั้งค่าใน Secrets ทันที")
if AUTH_ON:
    idle_guard()
    _acc = access.load(DATA_DIR)
    _rem = access.remaining(EMAIL, ROLE, _acc)
    _quota = "ไม่จำกัด" if _rem is None else f"เหลือ {_rem}/{access.limit_of(ROLE, _acc)} ครั้งวันนี้"
    _c1, _c2 = st.columns([5, 1])
    _c1.markdown(f'<div class="chips"><span class="chip">{esc(EMAIL)}</span><span class="chip ok">{access.ROLE_TH[ROLE]}</span>'
                 f'<span class="chip">{esc(_quota)}</span></div>', unsafe_allow_html=True)
    if _c2.button("ออกจากระบบ", key="logout"):
        q.session_revoke(_GKEY)
        st.logout()
elif _pw:
    idle_guard()
    _c1, _c2 = st.columns([5, 1])
    if _c2.button("ออกจากระบบ", key="logout"):
        q.session_revoke(ss.get("tok"))
        ss.pop("tok", None)
        _clear_token_param()
        st.rerun()


# ---------------------------------------------------------------- ตัวประมวลผลหลัก
def get_opts():
    ctx = {k: bool(ss.get("opt_" + k)) for k, _ in CTX_LABELS}
    return {"model": (ss.get("opt_model") or q.MODEL_IMAGES).strip(),
            "model_ctx": (ss.get("opt_model_ctx") or q.MODEL_CONTEXT).strip(),
            "model_clv": (ss.get("opt_model_clv") or q.MODEL_CLV).strip(),
            "api_key": q.get_api_key(secret) or (ss.get("opt_key") or "").strip() or None,
            "ctx": ctx, "league_size": int(ss.get("opt_league_size") or 0),
            "desp": ss.get("opt_desp") or "ไม่มี",
            "team_news": bool(q.Store(DATA_DIR).params.get("team_news_enabled", False))}


def make_result(m, opts, ext_warn=(), research_err=None, save=True):
    m.pop("warnings", None)
    m.pop("_need_research", None)
    m, warns = q.validate_match(m)
    ctx = m["context"]
    ctx.update({k: True for k, v in opts["ctx"].items() if v})
    if opts["desp"] != "ไม่มี":
        ctx["desperation"] = "home" if opts["desp"] == "เจ้าบ้าน" else "away"
    if opts["league_size"] > 0:
        m["league_size"] = opts["league_size"]
    if not m.get("id"):
        m["id"] = q.slug(f"{m['home']}-vs-{m['away']}-{q.now_th('%Y%m%d-%H%M')}")
    # เก็บสถานะการค้นบริบทไว้ในระเบียน (เดิมไม่เก็บ ทำให้ดูย้อนหลังไม่ได้ว่านัดไหนค้นไม่สำเร็จ)
    m["research_status"] = ("ok" if m.get("research") else "missing") if research_err is None else f"error: {str(research_err)[:120]}"
    store = q.Store(DATA_DIR)
    f, contribs, pick = q.analyze_match(m, store)
    crit = ["ร้ายแรง: " + x for x in (m.get("critical") or [])]
    all_w = crit + list(ext_warn) + warns
    saved = None
    if save:
        saved = q.record_prediction(store, m, f, contribs, pick, all_w)   # เก็บคำเตือนครบ (รวมร้ายแรง/จากการอ่านรูป) เพื่อเปิดรายงานย้อนหลังได้ตรงกัน
    return {"m": m, "f": f, "contribs": contribs, "pick": pick, "warns": all_w,
            "research_err": research_err, "saved": saved, "report": q.render_report(m, f, contribs, pick, store)}


def run_research(m, opts, do_research=True, step=None):
    """ค้นบริบทแมตช์ (+ข้อมูลทีมถ้าเปิดไว้) ใส่ลงใน m คืนข้อความผิดพลาดของการค้นบริบท (None = สำเร็จ)"""
    m.pop("_need_research", None)
    if not do_research:
        return None
    research_err = None
    if step:
        step("กำลังค้นหาข้อมูลบริบทแมตช์ (Google Search) ...")
    try:
        r, srcs, qs = q.research_context(m.get("home"), m.get("away"), m.get("league"), opts["model_ctx"], opts["api_key"])
        q.apply_research(m, r, srcs, qs)
    except SystemExit as e:
        research_err = str(e.code)
    except Exception as e:  # noqa
        research_err = f"{type(e).__name__}: {str(e)[:150]}"
    if opts.get("team_news"):
        if step:
            step("กำลังค้นข้อมูลทีม: xG/xGA, ตัวเจ็บ, บอลถ้วย, วันพัก ...")
        try:
            r2, srcs2, qs2 = q.research_team_news(m.get("home"), m.get("away"), m.get("league"), opts["model_ctx"], opts["api_key"])
            q.apply_team_news(m, r2, srcs2, qs2)
        except SystemExit as e:
            m["team_news"] = {"error": str(e.code)}
        except AttributeError:
            m["team_news"] = {"error": "ไฟล์ football_quant_v58.py บน GitHub ยังเป็นรุ่นเก่า — อัปโหลดไฟล์รุ่นล่าสุดแล้วรีบูตแอป"}
        except Exception as e:  # noqa  (ข้อมูลทีมเป็นส่วนเสริม ห้ามทำให้การวิเคราะห์ล้ม)
            m["team_news"] = {"error": f"{type(e).__name__}: {str(e)[:150]}"}
    return research_err


def pipeline_job(job, blobs, opts, do_research, save):
    """ขั้นตอนวิเคราะห์ทั้งหมด (รันในเธรดเบื้องหลัง ห้ามเรียกคำสั่งแสดงผลของ Streamlit) คืนผลลัพธ์หรือ raise"""
    step = job["steps"].append
    research_err = None
    step("กำลังอ่านรูปด้วย Gemini ...")
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, (name, data) in enumerate(blobs, 1):
            p = os.path.join(td, f"{i}_{os.path.basename(name)}")
            with open(p, "wb") as fh:
                fh.write(data)
            paths.append(p)
        m = q.extract_from_images(paths, opts["model"], opts["api_key"])
    blobs.clear()                                   # ไม่เก็บรูปไว้ในหน่วยความจำ
    ext_warn = m.pop("warnings", None) or []
    # ตรวจราคาที่อ่านได้ก่อนค้นบริบท: ถ้าผิดปกติร้ายแรงจะหยุดไว้ก่อน ไม่เสียโควตา API ค้นบริบทไปฟรี ๆ
    step("กำลังตรวจความสมเหตุสมผลของราคาที่อ่านได้ ...")
    chk = json.loads(json.dumps(m))
    chk.pop("warnings", None)
    q.validate_match(chk)
    if chk.get("critical"):
        if do_research:
            m["_need_research"] = True              # ค้นบริบทภายหลัง เมื่อผู้ใช้กดวิเคราะห์ต่อ/แก้ตัวเลขแล้ว
        return {"_gate": True, "m": m, "ext_warn": ext_warn, "research_err": None,
                "critical": chk["critical"], "save": save,
                "match_json": json.dumps(m, ensure_ascii=False, indent=2, default=str)}
    research_err = run_research(m, opts, do_research, step) if do_research else None
    q._job_check()                                  # ถูกยกเลิก/หมดเวลา -> ไม่บันทึกผล
    step("กำลังวิเคราะห์ราคาและฟันธง ...")
    res = make_result(m, opts, ext_warn, research_err, save)
    res["match_json"] = json.dumps({k: v for k, v in res["m"].items() if k != "warnings"}, ensure_ascii=False, indent=2, default=str)
    return res


JOB_OWNER = (_GKEY if AUTH_ON else st.session_state.get("tok")) or None


def current_job():
    """งานวิเคราะห์ของหน้านี้: จากรหัสในลิงก์ (?job=) หรืองานล่าสุดของผู้ใช้ (กู้คืนหลังหน้าเว็บหลุด/เปิดใหม่)"""
    j = q.job_get(ss.get("job_id") or st.query_params.get("job"))
    if j is None and JOB_OWNER:
        j = q.job_latest(JOB_OWNER)
    if j is not None and (j.get("dismissed") or (JOB_OWNER and j["owner"] not in (None, JOB_OWNER))):
        return None                                  # ปิดไปแล้ว หรือเป็นงานของผู้ใช้อื่น
    return j


def dismiss_job():
    jx = q.job_get(ss.get("job_id") or st.query_params.get("job"))
    if jx and jx["status"] != "running":
        jx["dismissed"] = True
    ss.pop("job_id", None)
    if "job" in st.query_params:
        del st.query_params["job"]


@st.fragment(run_every=2)
def job_watch(jid):
    """แสดงความคืบหน้าของงานเบื้องหลัง ตรวจทุก 2 วินาที เสร็จเมื่อไหร่โหลดผลทันที"""
    j = q.job_get(jid)
    if j is None or j["status"] != "running":
        st.rerun()
    sec = int(time.time() - j["started"])
    steps = "".join(f'<div style="opacity:{1 if i == len(j["steps"]) - 1 else .55}">{"→" if i == len(j["steps"]) - 1 else "✓"} {esc(s_[2:].strip())}</div>'
                    for i, s_ in enumerate(j["steps"]))
    note = f'<div style="color:#f5b942;font-size:.85rem;margin-top:6px">! {esc(j["note"])}</div>' if j.get("note") else ""
    st.markdown(f'<div class="card"><h4>กำลังวิเคราะห์เบื้องหลัง · {sec} วินาที (ไม่เกิน {q.JOB_MAX_SEC // 60} นาที)</h4>{steps}{note}'
                '<div class="muted" style="margin-top:8px">ปกติใช้ 1–2 นาที · สลับไปแอปอื่นหรือปิดหน้าจอได้ งานยังเดินต่อบนเซิร์ฟเวอร์ กลับมาหน้านี้เมื่อไหร่ก็เห็นผล</div></div>',
                unsafe_allow_html=True)
    if st.button("✕ ยกเลิกการวิเคราะห์นี้", key=f"job_cancel_{jid}"):
        j["cancelled"] = True                       # เธรดจะหยุดเองเมื่อคำขอที่ค้างอยู่จบ และไม่บันทึกผล · สิทธิ์ถูกคืนอัตโนมัติ
        j["dismissed"] = True
        ss.pop("job_id", None)
        if "job" in st.query_params:
            del st.query_params["job"]
        st.rerun()


_F_DEFAULTS = {"rank_off": "", "rank_home": None, "rank_away": None, "league_size": None, "verify": [], "verify_fail": False,
               "fav_drop_adj": 0.0, "dog_drop_adj": 0.0, "value_ratio": None, "conflict": 0.0, "x12_pp": 0.0,
               "hdp_shift_fav": 0.0, "has_ou": False, "form": None}


def res_from_record(rec, store):
    f = {**_F_DEFAULTS, **rec["features"]}
    m = dict(rec.get("match") or {})
    if not m:                                   # รายการเก่าที่ยังไม่ได้เก็บข้อมูลแมตช์ทั้งก้อน
        m = {"context": {"type": f.get("ctx_type", "league"), "derby": f.get("derby"), "high_volatility": f.get("high_vol"),
                         "high_scoring_league": f.get("high_scoring"), "cup_group_stage": f.get("cup_group"),
                         "knockout": f.get("knockout"), "continental_cup": f.get("continental"),
                         "high_draw_league": f.get("high_draw"), "late_goal_tendency": f.get("late_goal"),
                         "desperation": f.get("desperation")}, "form": f.get("form")}
    try:
        report = q.render_report(m, f, rec["contribs"], rec["pick"], store)
    except Exception:  # noqa
        report = "(รายงานฉบับเต็มไม่พร้อมใช้งานสำหรับรายการเก่านี้)"
    return {"m": m, "f": f, "contribs": rec["contribs"], "pick": rec["pick"], "warns": rec.get("warns", []),
            "research_err": None, "saved": None, "report": report}


# ---------------------------------------------------------------- แสดงผลลัพธ์
def render_result(res, key="r"):
    f = res["f"]
    if res.get("saved"):
        mid, ok = res["saved"]
        if ok:
            st.success("บันทึกสัญญาณแล้ว → ใส่ผลจริงที่แท็บ “บันทึกผล” หลังจบเกม")
    show(SP.analysis_story(res), key=f"story_{key}")
    st.download_button("ดาวน์โหลดรายงาน (HTML แบบเล่าเรื่อง เปิดได้ทุกเครื่อง)", SP.analysis_document(res),
                       file_name=f"{q.slug(f['home'] + '-vs-' + f['away'])}.html", mime="text/html", key=f"dl_{key}")
    with st.expander("รายงานฉบับเต็ม (ข้อความ)"):
        st.text(res["report"])
    if res.get("saved"):
        mid, ok = res["saved"]
        if not ok:
            st.warning("ไม่บันทึก: รายการนี้ถูกบันทึกผลไปแล้ว")
        cloud_warn()


# ---------------------------------------------------------------- แท็บ
if IS_ADMIN:
    _tabs = ["วิเคราะห์", "บันทึกผล", "สถิติ", "ทดสอบย้อนหลัง", "สำรองข้อมูล"] + (["ผู้ใช้"] if AUTH_ON else [])
    _T = st.tabs(_tabs)
    tab1, tab2, tab3, tab4, tab5 = _T[:5]
    tab6 = _T[5] if AUTH_ON else None
else:
    tab1 = st.container()                         # User / Local เห็นเฉพาะหน้าวิเคราะห์

# ================================================================ TAB 1
def risk_banner(store_):
    """แถบเตือนเมื่อถึงเพดานที่ตั้งไว้ (ไม้ที่ลงเงินจริงเท่านั้น)"""
    rk = q.risk_status(store_.history, store_.params)
    P_ = store_.params
    if rk["day_hit"]:
        st.error(f"ถึงเพดานขาดทุนวันนี้แล้ว ({rk['day']:+.2f} หน่วย · เพดาน −{float(P_['risk_day_limit']):.1f}) · แนะนำหยุดแทงเงินจริงวันนี้ "
                 "(ยังวิเคราะห์และบันทึกเป็นไม้กระดาษได้)")
    if rk["dd_hit"]:
        st.error(f"ช่วงดิ่งถึงเพดานรวมแล้ว ({rk['dd']:+.2f} หน่วย · เพดาน −{float(P_['risk_dd_limit']):.1f}) · แนะนำพักเงินจริง "
                 "แล้วเก็บข้อมูลเป็นไม้กระดาษจนกว่าจะกลับมาทบทวน")
    elif rk.get("dd_pct") is not None and rk["dd_pct"] <= -0.30:
        st.error(f"ช่วงดิ่งเท่ากับ {-rk['dd_pct']:.0%} ของทุนแล้ว ({rk['dd'] * rk['unit']:+,.0f} บาท จากทุน {rk['bank']:,.0f}) "
                 "ทั้งที่ยังไม่ถึงเพดานหน่วยที่ตั้งไว้ · แนะนำลดขนาดหน่วยหรือพักเงินจริง")
    return rk


with tab1:
    risk_banner(q.Store(DATA_DIR))
    ss.setdefault("up_ver", 0)            # เปลี่ยนเลขเวอร์ชันของ key = ล้างรูปที่อัปโหลดทิ้งทันที
    files = st.file_uploader("อัปโหลดรูป 5 รูป: ภาพสรุปแมตช์ · 1X2 · Handicap · Over/Under · H2H",
                             type=["png", "jpg", "jpeg", "webp", "gif"], accept_multiple_files=True,
                             key=f"uploader_{ss['up_ver']}")
    if ss.pop("cleared_msg", False):
        st.caption("ล้างรูปที่อัปโหลดออกแล้ว (ระบบไม่เก็บรูปไว้)")
    t1, t2 = st.columns(2)
    do_research = t1.toggle("ค้นหาบริบทแมตช์อัตโนมัติ", value=True, key="opt_research",
                            help="ให้ Gemini ค้นหาข้อมูลจริงทาง Google Search (คิดค่าบริการตามจำนวนคำค้น)")
    if IS_ADMIN:
        do_save = t2.toggle("บันทึกสัญญาณลงประวัติ", value=True, key="opt_save")
    else:
        do_save = False                                 # User / Local ไม่บันทึกผลลงระบบ
    quota_left = access.remaining(EMAIL, ROLE, access.load(DATA_DIR)) if AUTH_ON else None
    if quota_left == 0:
        st.markdown(f'<div class="res lose">ใช้สิทธิ์วิเคราะห์ของวันนี้ครบแล้ว · รีเซ็ตในอีก {access.reset_in()} (เที่ยงคืนเวลาไทย)</div>',
                    unsafe_allow_html=True)
    _running = (current_job() or {}).get("status") == "running"
    go = st.button("วิเคราะห์อัตโนมัติ", type="primary", disabled=not files or quota_left == 0 or _running)
    box = st.container()
    opts = get_opts()
    if go:
        if not opts["api_key"]:
            with box:
                st.error("ยังไม่ได้ตั้งค่า GEMINI_API_KEY (ใส่ที่ Secrets หรือช่องใน “ตั้งค่าขั้นสูง”)")
        elif AUTH_ON and not access.reserve(DATA_DIR, EMAIL, ROLE):
            with box:
                st.error(f"ใช้สิทธิ์วิเคราะห์ของวันนี้ครบแล้ว · รีเซ็ตในอีก {access.reset_in()}")
        else:
            dismiss_job()                            # งานก่อนหน้า (ถ้ามี) ไม่ต้องกู้คืนอีก
            job = q.job_new(JOB_OWNER)
            if AUTH_ON:
                job["on_finish"] = lambda j_, e_=EMAIL, r_=ROLE: (access.refund(DATA_DIR, e_, r_) if j_["status"] == "error" else None)
            q.job_start(job, pipeline_job, [(uf.name, uf.getvalue()) for uf in files], opts, do_research, do_save)
            ss["job_id"] = job["id"]
            st.query_params["job"] = job["id"]
            ss.pop("res", None)
            ss.pop("gate", None)
            ss["up_ver"] += 1                 # ส่งรูปให้งานเบื้องหลังแล้ว -> เคลียร์รูปจากหน้าจอทันที
            ss["cleared_msg"] = True
            st.rerun()
    job = current_job()
    if job is not None:
        if job["status"] == "running":
            ss["job_id"] = job["id"]
            with box:
                job_watch(job["id"])
        elif ss.get("job_seen") != job["id"]:      # โหลดผลครั้งเดียวต่อการเปิดหน้า (เปิดหน้าใหม่/เชื่อมต่อใหม่ = โหลดผลกลับมาให้)
            ss["job_seen"] = job["id"]
            ss["job_id"] = job["id"]
            if job["status"] == "error":
                ss["job_err"] = job["error"]
            elif job["status"] == "gate":
                ss["gate"] = job["result"]
                ss["match_json"] = job["result"].get("match_json") or ss.get("match_json")
            else:
                ss["res"] = job["result"]
                ss["match_json"] = job["result"].get("match_json") or ss.get("match_json")
    if ss.get("job_err"):
        with box:
            st.error(ss["job_err"])
            if st.button("ปิดข้อความ", key="job_err_close"):
                ss.pop("job_err", None)
                dismiss_job()
                st.rerun()
    if ss.get("gate"):
        g = ss["gate"]
        with box:
            items = "".join(f"<li>{esc(x)}</li>" for x in g["critical"])
            st.markdown(f'<div class="res lose">พบข้อมูลที่อาจอ่านผิดจากรูป ({len(g["critical"])} จุด) ระบบหยุดไว้ก่อนวิเคราะห์'
                        f'<ul style="margin:8px 0 0;padding-left:18px;font-weight:400">{items}</ul></div>', unsafe_allow_html=True)
            st.caption(("ตรวจตัวเลขในรูปเทียบกับข้อมูลที่อ่านได้ (เปิด “ตั้งค่าขั้นสูง” ด้านล่างเพื่อแก้ แล้วกด “วิเคราะห์ใหม่จากข้อมูลที่แก้ไข”) "
                        if IS_ADMIN else "ตรวจตัวเลขในรูปอีกครั้ง ") + "หรือกดวิเคราะห์ต่อเพื่อดูผล (ไม่เสียสิทธิ์เพิ่ม) · "
                       "ถ้าวิเคราะห์ต่อโดยไม่แก้ตัวเลข ไม้นี้จะถูก “ข้ามอัตโนมัติ” เป็นไม้เงา ไม่ควรลงเงิน"
                       + (" · ระบบยังไม่ได้ค้นบริบท (ประหยัดโควตา API) จะค้นตอนกดวิเคราะห์ต่อ หรือหลังแก้ตัวเลขจนผ่านการตรวจ"
                          if g["m"].get("_need_research") else ""))
            g1, g2 = st.columns(2)
            if g1.button("▶ วิเคราะห์ต่อ (ไม้นี้จะเป็นไม้เงา)", type="primary", key="gate_go"):
                try:
                    gm, rerr = json.loads(json.dumps(g["m"])), g["research_err"]
                    if gm.get("_need_research"):
                        with st.spinner("กำลังค้นหาข้อมูลบริบทแมตช์ ..."):
                            rerr = run_research(gm, get_opts())
                    ss["res"] = make_result(gm, get_opts(), g["ext_warn"], rerr, g["save"])
                    ss.pop("gate", None)
                    dismiss_job()
                    st.rerun()
                except ValueError as e:
                    st.error(f"ข้อมูลไม่ครบ/ไม่ถูกต้อง: {e}")
            if g2.button("✕ ยกเลิก", key="gate_cancel"):
                ss.pop("gate", None)
                dismiss_job()
                if AUTH_ON:
                    access.refund(DATA_DIR, EMAIL, ROLE)      # ไม่ได้ผลวิเคราะห์ -> คืนสิทธิ์
                st.rerun()
    if ss.get("res"):
        with box:
            render_result(ss["res"], key="t1")

    if not IS_ADMIN:
        st.caption("ผลวิเคราะห์เป็นแบบจำลองเชิงสถิติ ไม่รับประกันผล และไม่ใช่คำแนะนำทางการเงิน")
        st.stop()                                     # User / Local: จบที่หน้าวิเคราะห์

    with st.expander("ตั้งค่าขั้นสูง"):
        mc1, mc2, mc3 = st.columns(3)
        mc1.text_input("โมเดลอ่านรูป", value=q.MODEL_IMAGES, key="opt_model")
        mc2.text_input("โมเดลค้นบริบท", value=q.MODEL_CONTEXT, key="opt_model_ctx")
        mc3.text_input("โมเดลอ่านราคาปิด (CLV)", value=q.MODEL_CLV, key="opt_model_clv")
        if not q.get_api_key(secret):
            st.text_input("GEMINI_API_KEY", type="password", key="opt_key", help="ใช้อ่านรูปเท่านั้น ไม่ถูกบันทึก")
        else:
            st.caption("✓ พบ API key ใน Secrets แล้ว")
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
                rerr = None
                if m2.get("_need_research"):            # ข้ามการค้นบริบทไว้ตอนเจอราคาผิดปกติ -> ค้นตอนนี้ (ถ้าราคาที่แก้ผ่านแล้ว)
                    chk2 = json.loads(json.dumps(m2))
                    chk2.pop("warnings", None)
                    q.validate_match(chk2)
                    if not chk2.get("critical"):
                        with st.spinner("ราคาผ่านการตรวจแล้ว กำลังค้นหาข้อมูลบริบทแมตช์ ..."):
                            rerr = run_research(m2, get_opts())
                ss["res"] = make_result(m2, get_opts(), research_err=rerr, save=bool(ss.get("opt_save", True)))
                ss.pop("gate", None)
                dismiss_job()
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"รูปแบบข้อมูลไม่ถูกต้อง: {e}")
            except ValueError as e:
                st.error(f"ข้อมูลไม่ครบ/ไม่ถูกต้อง: {e}")

# ================================================================ TAB 2
with tab2:
    store = q.Store(DATA_DIR)
    if ss.get("settle_html"):
        show(ss.pop("settle_html"), key="settle_res")
        cloud_warn()
    pend_list = [r for r in reversed(store.history) if r["status"] == "pending"]
    pend = {r["id"]: r for r in pend_list}
    if ss.get("settle_sel") not in pend:
        ss["settle_sel"] = pend_list[0]["id"] if pend_list else None
    picked = show(SP.pending_cards(pend_list, ss["settle_sel"]), key="pend", on_act=True)
    if picked and picked in pend and picked != ss["settle_sel"]:
        ss["settle_sel"] = picked
        st.rerun()
    if pend:
        rid = ss["settle_sel"]
        rec = pend[rid]
        fe = rec["features"]
        st.markdown(f'<div class="fq"><div class="fq-sec">ใส่ผลจริง <small>{esc(fe["home"])} vs {esc(fe["away"])} · {esc(rec["pick"]["label"])}</small></div></div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        hg = c1.number_input(f"ประตู {fe['home']}", 0, 30, 0, key=f"hg_{rid}")
        ag = c2.number_input(f"ประตู {fe['away']}", 0, 30, 0, key=f"ag_{rid}")
        with st.expander("ราคาปิดก่อนเตะ (CLV) · ไม่บังคับ" + (" · บันทึกแล้ว" if rec.get("clv") else "")):
            pk_ = rec["pick"]
            mk_ = pk_["market"]
            if mk_.startswith("HDP") or mk_.startswith("OU"):
                old_c = rec.get("clv") or {}
                bk_ = (pk_.get("best") or {}).get("book")
                st.caption(f"แคปตาราง{'แฮนดิแคป' if mk_.startswith('HDP') else 'สูง/ต่ำ'}ของคู่นี้ตอนใกล้เตะที่สุด (ราว 5–15 นาทีก่อนเตะ) แล้วส่งรูป "
                           f"ระบบจะอ่านราคาปัจจุบันของ{('เจ้าเดิมที่ให้ราคาดีที่สุดตอนวิเคราะห์ (' + bk_ + ')') if bk_ else 'ทุกเจ้า'} "
                           "แล้วคำนวณและบันทึก CLV ให้ทันที · CLV ไม่เปลี่ยนไม้และไม่เปลี่ยนการเรียนรู้")
                if old_c and q.clv_suspect(rec):
                    st.warning(f"ราคาปิดที่บันทึกไว้น่าสงสัย: {q.clv_suspect(rec)} · ไม่นับในสรุป CLV · ส่งรูปใหม่หรือแก้ตัวเลขเอง")
                elif old_c:
                    st.success(f"CLV ที่บันทึกไว้: {old_c.get('clv_best', old_c['clv']) * 100:+.2f}% ที่ราคาที่แทง "
                               f"(ราคากลาง {old_c['clv'] * 100:+.2f}%) · ราคาปิด {old_c['line']:+.2f} @{old_c['w_mine']:.2f}/{old_c['w_other']:.2f}"
                               + (f" · {old_c['source']}" if old_c.get("source") else "") + f" · {old_c.get('at', '')}")
                up_ = st.file_uploader("รูปตารางราคาตอนใกล้เตะ", type=["png", "jpg", "jpeg", "webp"], key=f"clv_img_{rid}")
                if up_ is not None and st.button("อ่านราคาและบันทึก CLV", key=f"clv_read_{rid}", type="primary"):
                    o_ = get_opts()
                    if not o_["api_key"]:
                        st.error("ยังไม่ได้ตั้งค่า GEMINI_API_KEY")
                    else:
                        try:
                            with st.spinner("กำลังอ่านราคาจากรูป ..."):
                                rd_ = q.read_closing_image(rec, up_.getvalue(), up_.type or "image/png", o_["model_clv"], o_["api_key"])
                            c_ = q.set_clv(store, rid, rd_["line"], rd_["w_mine"], rd_["w_other"], source=rd_["source"])
                            sus_ = q.clv_suspect(rec, c_) if c_ else None
                            if sus_:
                                st.warning(f"ราคาปิดที่อ่านได้น่าสงสัย: {sus_} · ไม่นับในสรุป CLV จนกว่าจะแก้ (ติ๊ก “แก้ตัวเลขเอง” ด้านล่าง)")
                            if c_:
                                st.success(f"บันทึกแล้ว · CLV {c_['clv_best'] * 100:+.2f}% ที่ราคาที่แทง (ราคากลาง {c_['clv'] * 100:+.2f}%) · "
                                           f"ราคาปิด {rd_['line']:+.2f} @{rd_['w_mine']:.2f}/{rd_['w_other']:.2f} · {rd_['source']}")
                                st.caption("อ่านได้: " + " · ".join(f"{d['book']} {d['line']:+.2f} {d['a']:.2f}/{d['b']:.2f}" for d in rd_["detail"][:8]))
                                cloud_warn()
                            else:
                                st.error("คำนวณ CLV ไม่ได้")
                        except (ValueError, SystemExit) as ex_:
                            st.error(str(ex_))
                if st.checkbox("แก้ตัวเลขเอง (กรณีอ่านรูปผิด)", key=f"clv_man_{rid}"):
                    if mk_.startswith("HDP"):
                        tm_ = fe["home"] if mk_ == "HDP_HOME" else fe["away"]
                        l0 = fe["line_c"] if mk_ == "HDP_HOME" else -fe["line_c"]
                        mine0, oth0 = ((fe["fav_water_c"], fe["dog_water_c"]) if mk_ == fe["fav_hdp"] else (fe["dog_water_c"], fe["fav_water_c"]))
                        l_lab = f"เรตของ {tm_} ตอนปิด"
                    else:
                        l0 = fe["ou_c"]
                        mine0, oth0 = ((fe["over_water_c"], fe["under_water_c"]) if mk_ == "OU_OVER" else (fe["under_water_c"], fe["over_water_c"]))
                        l_lab = "เส้นสูง/ต่ำตอนปิด"
                    k1, k2, k3 = st.columns(3)
                    cl_line = k1.number_input(l_lab, -10.0, 10.0, float(old_c.get("line", l0)), 0.25, format="%.2f", key=f"clv_l_{rid}")
                    cl_m = k2.number_input("ค่าน้ำฝั่งที่แทง", 0.3, 2.5, float(old_c.get("w_mine", round(mine0, 2))), 0.01, format="%.2f", key=f"clv_m_{rid}")
                    cl_o = k3.number_input("ค่าน้ำอีกฝั่ง", 0.3, 2.5, float(old_c.get("w_other", round(oth0, 2))), 0.01, format="%.2f", key=f"clv_o_{rid}")
                    if st.button("บันทึกราคาปิด", key=f"clv_go_{rid}"):
                        c_ = q.set_clv(store, rid, cl_line, cl_m, cl_o, source="กรอกเอง")
                        if c_:
                            st.success(f"บันทึกแล้ว · CLV {c_['clv_best'] * 100:+.2f}% ที่ราคาที่แทง (ราคากลาง {c_['clv'] * 100:+.2f}%)")
                            cloud_warn()
                        else:
                            st.error("คำนวณ CLV ไม่ได้ ตรวจตัวเลขอีกครั้ง")
            else:
                st.caption("ไม้ตลาด 1X2 ยังไม่รองรับ CLV")
        paper_ = st.checkbox("ไม้กระดาษ (ไม่ได้ลงเงินจริง) · ระบบยังเรียนรู้ตามปกติ แต่ไม่นับในสถิติเงินจริงและเพดานความเสี่ยง",
                             value=bool(rec.get("paper", store.params.get("risk_paper_default", False))), key=f"paper_{rid}")
        if st.button("✓ บันทึกผลจริง & ให้ระบบเรียนรู้", type="primary"):
            rec["paper"] = bool(paper_)
            outcomes, r, pf, changes, new = q.do_settle(store, rec, int(hg), int(ag))
            ss["settle_html"] = SP.settle_result(fe, rec["pick"], int(hg), int(ag), outcomes, r, pf, changes, new, rec.get("life_changes") or [])
            ss.pop("settle_sel", None)
            st.rerun()
        with st.expander("ลบรายการนี้ (ถ้าไม่ต้องการ)"):
            sure = st.checkbox("ยืนยันลบรายการที่เลือกอยู่", key=f"del_{rid}")
            if st.button("ลบรายการนี้", disabled=not sure):
                q.delete_records(store, [rid])
                ss.pop("settle_sel", None)
                st.rerun()
        render_result(res_from_record(rec, store), key="t2")

    # ---------------- แก้ไข/ยกเลิกผลที่ใส่ผิด ----------------
    st.markdown('<div class="fq"><div class="fq-sec">แก้ไขผลที่ใส่ผิด <small>แก้สกอร์แล้วระบบคำนวณน้ำหนัก Rule และ Rule ที่เรียนรู้ใหม่จากประวัติทั้งหมด</small></div></div>',
                unsafe_allow_html=True)
    em = ss.pop("edit_msg", None)
    if em:
        show(SP.edit_message(em), key="edit_msg")
        cloud_warn()
    done_recs = [r for r in reversed(store.history) if r["status"] == "settled"]
    if not done_recs:
        st.caption("ยังไม่มีรายการที่บันทึกผลแล้ว")
    else:
        eid = st.selectbox("เลือกรายการที่ต้องการแก้", [r["id"] for r in done_recs], key="edit_sel",
                           format_func=lambda i: next(f"{r['features']['home']} {r['score'][0]}-{r['score'][1]} {r['features']['away']}"
                                                      + (" (เคยแก้ไข)" if r.get("edits") else "") for r in done_recs if r["id"] == i))
        er = next(r for r in done_recs if r["id"] == eid)
        fe = er["features"]
        show(SP.record_card(er), key="rec_card")
        c1, c2 = st.columns(2)
        ehg = c1.number_input(f"ประตู {fe['home']} (ที่ถูกต้อง)", 0, 30, int(er["score"][0]), key=f"ed_hg_{eid}")
        eag = c2.number_input(f"ประตู {fe['away']} (ที่ถูกต้อง)", 0, 30, int(er["score"][1]), key=f"ed_ag_{eid}")
        changed = (int(ehg), int(eag)) != tuple(er["score"])
        sure = st.checkbox("ยืนยัน: ระบบจะคำนวณน้ำหนัก Rule และ Rule ที่เรียนรู้ใหม่จากประวัติทั้งหมด (ผลลัพธ์เท่ากับใส่สกอร์ที่ถูกตั้งแต่แรก)", key=f"ed_ok_{eid}")
        b1, b2 = st.columns(2)
        if b1.button("บันทึกการแก้ไขสกอร์", type="primary", disabled=not (sure and changed)):
            with st.spinner("กำลังคำนวณการเรียนรู้ใหม่จากประวัติทั้งหมด (ประมาณ 10-20 วินาที) ..."):
                r_ = q.edit_result(store, eid, int(ehg), int(eag))
            ss["edit_msg"] = {"kind": "edit", "title": f"{fe['home']} vs {fe['away']}", **r_}
            st.rerun()
        if b2.button("↩ ยกเลิกผลนี้ (กลับเป็นรอผล)", disabled=not sure):
            with st.spinner("กำลังยกเลิกผลและคำนวณการเรียนรู้ใหม่ (ประมาณ 10-20 วินาที) ..."):
                r_ = q.revert_result(store, eid)
            ss["edit_msg"] = {"kind": "revert", "title": f"{fe['home']} vs {fe['away']}", **r_}
            st.rerun()
        if not changed:
            st.caption("แก้ตัวเลขสกอร์ให้ต่างจากที่บันทึกไว้ ปุ่มบันทึกจึงจะใช้งานได้")

# ================================================================ TAB 3
def _data_stamp():
    """ลายเซ็นของไฟล์ข้อมูล (เวลาแก้ไข + ขนาด) เปลี่ยนเมื่อมีการบันทึกผล/แก้ไขจากเครื่องใดก็ได้"""
    out = []
    for fn in ("history.json", "state.json"):
        try:
            s_ = os.stat(os.path.join(DATA_DIR, fn))
            out.append((s_.st_mtime_ns, s_.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


@st.fragment(run_every=10)
def stats_live():
    """หน้าสถิติแบบ realtime: ตรวจทุก 10 วินาที ถ้ามีผลใหม่ (จากเครื่องใดก็ได้) จะคำนวณกราฟใหม่ทันที"""
    stamp = _data_stamp()
    cache = ss.get("_stats_live")
    if not cache or cache["stamp"] != stamp:
        st_ = q.Store(DATA_DIR)
        n_done = sum(1 for r in st_.history if r.get("status") == "settled")
        html_ = SP.stats_story(st_.state, st_.history, st_.params)
        if cache and n_done != cache["n"]:
            st.toast(f"มีผลใหม่ อัปเดตสถิติแล้ว ({n_done} นัด)")
        cache = {"stamp": stamp, "html": html_, "n": n_done, "at": q.now_th("%H:%M:%S")}
        ss["_stats_live"] = cache
    st.caption(f"อัปเดตอัตโนมัติ · ข้อมูลล่าสุดเมื่อ {cache['at']} · ตรวจผลใหม่ทุก 10 วินาที")
    show(cache["html"], key="stats")


with tab3:
    store = q.Store(DATA_DIR)
    S = store.state
    rk_ = risk_banner(store)
    stats_live()
    with st.expander("คุมความเสี่ยง: ทุน · หน่วย · เพดานขาดทุน · ไม้กระดาษ"):
        P0 = store.params
        r1, r2 = st.columns(2)
        n_bank = r1.number_input("ทุนทั้งหมด (บาท) · 0 = ไม่ระบุ", 0.0, 1e9, float(P0.get("risk_bankroll", 0.0)), 100.0, key="rk_bank")
        n_unit = r2.number_input("1 หน่วย = กี่บาท · 0 = ไม่ระบุ", 0.0, 1e8, float(P0.get("risk_unit", 0.0)), 10.0, key="rk_unit")
        r3, r4 = st.columns(2)
        n_day = r3.number_input("เพดานขาดทุนต่อวัน (หน่วย) · 0 = ปิด", 0.0, 100.0, float(P0.get("risk_day_limit", 5.0)), 0.5, key="rk_day")
        n_dd = r4.number_input("เพดานช่วงดิ่งรวม (หน่วย) · 0 = ปิด", 0.0, 500.0, float(P0.get("risk_dd_limit", 40.0)), 1.0, key="rk_dd")
        n_pp = st.toggle("ติ๊ก “ไม้กระดาษ” ไว้เป็นค่าเริ่มต้นตอนบันทึกผล (สำหรับช่วงพักเงินจริง)", value=bool(P0.get("risk_paper_default", False)), key="rk_pp")
        if n_unit and n_bank:
            st.caption(f"1 หน่วย = {n_unit / n_bank:.2%} ของทุน · ช่วงดิ่ง 60 หน่วย (กรณีแย่ที่จำลองไว้) = {60 * n_unit / n_bank:.0%} ของทุน"
                       + (" · แนะนำไม่เกิน 1% ต่อหน่วย" if n_unit / n_bank > 0.01 else ""))
        if n_unit and n_bank:                        # เพดานที่ตั้งเป็น "หน่วย" ต้องไม่เกินทุน ไม่เช่นนั้นทุนหมดก่อนระบบเตือน
            cf = []
            if n_dd and n_dd * n_unit > n_bank:
                cf.append(f"เพดานช่วงดิ่ง {n_dd:g} หน่วย = {n_dd * n_unit:,.0f} บาท มากกว่าทุน {n_bank:,.0f} บาท "
                          f"(ควรไม่เกิน {n_bank * 0.3 / n_unit:.0f} หน่วย = 30% ของทุน)")
            if n_day and n_day * n_unit > n_bank * 0.2:
                cf.append(f"เพดานต่อวัน {n_day:g} หน่วย = {n_day * n_unit:,.0f} บาท = {n_day * n_unit / n_bank:.0%} ของทุนในวันเดียว")
            if cf:
                st.warning("ค่าที่ตั้งขัดกับทุน: " + " · ".join(cf) + " — ระบบจะเตือนช้ากว่าที่ทุนรับไหว")
        if st.button("บันทึกการตั้งค่าความเสี่ยง", key="rk_save"):
            store.state["params"].update({"risk_bankroll": float(n_bank), "risk_unit": float(n_unit), "risk_day_limit": float(n_day),
                                          "risk_dd_limit": float(n_dd), "risk_paper_default": bool(n_pp)})
            store.save()
            st.success("บันทึกแล้ว")
            cloud_warn()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("กำไรเงินจริง (หน่วย)", f"{rk_['cum']:+.2f}", f"{rk_['cum_money']:+,.0f} บาท" if "cum_money" in rk_ else None)
        m2.metric("ช่วงดิ่งตอนนี้ (หน่วย)", f"{rk_['dd']:+.2f}", f"{rk_['dd_pct']:+.1%} ของทุน" if "dd_pct" in rk_ else None)
        m3.metric("วันนี้ (หน่วย)", f"{rk_['day']:+.2f}", f"{rk_['day_n']} ไม้")
        m4.metric("ไม้กระดาษ", f"{rk_['paper_n']}")
        st.caption("นับเฉพาะไม้ที่ลงเงินจริง (ไม่นับไม้ที่ระบบข้ามและไม้กระดาษ) · เพดานไม่เปลี่ยนไม้ที่ระบบเลือก แค่เตือนให้หยุด")
    with st.expander("ตั้งค่าระบบ: สถานะ “ข้าม” และการแช่แข็งน้ำหนัก Rule"):
        P0 = store.params
        a1, a2 = st.columns(2)
        n_skip = a1.toggle("เปิดสถานะ “ข้าม” เมื่อสัญญาณอ่อน/ขัดกัน", value=bool(P0["skip_enabled"]), key="cfg_skip")
        n_frz = a2.toggle("แช่แข็งน้ำหนัก Rule (เรียนรู้เบื้องหลัง)", value=bool(P0["freeze_weights"]), key="cfg_frz")
        b1, b2 = st.columns(2)
        n_min = b1.number_input("ข้ามเมื่อคะแนนต่ำกว่า", 0.0, 10.0, float(P0["skip_min_strength"]), 0.1, key="cfg_min")
        n_cf = b2.number_input("ข้ามเมื่อฝั่งตรงข้ามได้คะแนน ≥ (สัดส่วนของฝั่งที่เลือก)", 0.1, 1.0, float(P0["skip_conflict"]), 0.05, key="cfg_cf")
        c1_, c2_ = st.columns(2)
        n_mv = c1_.checkbox("ข้ามเมื่อสัญญาณมาจากการไหลของราคาล้วน", value=bool(P0["skip_move_only"]), key="cfg_mv")
        n_vf = c2_.checkbox("ข้ามเมื่อตรวจเหย้า/เยือนไม่ผ่าน", value=bool(P0["skip_verify_fail"]), key="cfg_vf")
        g1_, g2_ = st.columns([3, 2])
        n_gate = g1_.toggle("ตัวกรองช่วงคะแนน: งดลงทุนเมื่อประเภทไม้ × ช่วงคะแนนนั้นชนะต่ำกว่าจุดคุ้มทุนหรือขาดทุน",
                            value=bool(P0.get("gate_enabled", True)), key="cfg_gate")
        n_gmin = g2_.number_input("ตัดสินเมื่อช่วงนั้นมีอย่างน้อย (ไม้)", 5, 200, int(P0.get("gate_min_n", 20)), key="cfg_gmin")
        n_tn = st.toggle("ค้นข่าวทีม (xG/ตัวเจ็บ/วันพัก) ทุกการวิเคราะห์ · ใช้โควตา Gemini เพิ่มราว 1 เท่า และยังไม่มีผลต่อการฟันธง",
                         value=bool(P0.get("team_news_enabled", False)), key="cfg_tn")
        n_cupr = st.toggle("บอลถ้วยรอบแบ่งกลุ่ม/ลีกเฟส: ไม่ใช้อันดับตารางด้วย (ปิด = ใช้ได้ เพราะสองทีมอยู่ตารางเดียวกัน · "
                           "น็อกเอาต์/ถ้วยในประเทศ/กระชับมิตร ไม่ใช้อันดับเสมอ)",
                           value=bool(P0.get("cup_rank_off_all", False)), key="cfg_cupr")
        n_lock = st.toggle("ล็อกสถานะ Rule: ไม่เปิดใช้ Rule ใหม่อัตโนมัติ (Rule ที่ผ่านเกณฑ์จะติดป้าย “พร้อมใช้” แต่ยังไม่มีผลต่อการฟันธง)",
                           value=bool(P0.get("lock_unlocks", True)), key="cfg_lock")
        if st.button("บันทึกการตั้งค่า", key="cfg_save"):
            store.state.setdefault("params", {}).update({"skip_enabled": n_skip, "freeze_weights": n_frz,
                                                         "skip_min_strength": float(n_min), "skip_conflict": float(n_cf),
                                                         "skip_move_only": n_mv, "skip_verify_fail": n_vf, "lock_unlocks": n_lock,
                                                         "gate_enabled": n_gate, "gate_min_n": int(n_gmin),
                                                         "team_news_enabled": n_tn, "cup_rank_off_all": n_cupr})
            if n_frz:
                q.weight_key(store)                # สร้างน้ำหนักเงาจากน้ำหนักปัจจุบัน
            store.save()
            st.success("บันทึกแล้ว · มีผลกับการวิเคราะห์ครั้งถัดไป (ไม้ที่บันทึกไว้แล้วไม่เปลี่ยน)")
            cloud_warn()
        st.caption("การตั้งค่าเหล่านี้ไม่เปลี่ยนไม้ที่ระบบเลือก แค่ติดป้าย “ข้าม” ให้ไม้ที่ไม่ผ่านเกณฑ์ และนับแยกในสถิติ")
        ready_ = sorted(k for k, v in (store.state.get("lifecycle") or {}).items() if v.get("status") == "shadow" and v.get("ready"))
        st.markdown("**อนุมัติ Rule ที่ผ่านเกณฑ์**")
        if not ready_:
            st.caption("ยังไม่มี Rule เงาที่ผ่านเกณฑ์ · เมื่อมี จะขึ้นที่นี่ให้อนุมัติทีละข้อ (Rule ที่อนุมัติแล้วจะมีผลต่อการฟันธงนัดถัดไป)")
        else:
            lc_ = store.state["lifecycle"]
            k_tested = sum(1 for k, v in lc_.items() if k in q.EXPERIMENTAL and v.get("status") in ("shadow", "retired", "active"))
            rows_ = []
            for k in ready_:
                p1, pk_ = q.rule_luck(lc_[k], k_tested, float(store.params.get("breakeven_wr", 0.5263)))
                cv, cn = q.rule_clv(store.history, k)
                verdict_ = ("น่าเชื่อ" if pk_ < 0.05 and (cv is None or cv > 0) else
                            "ระวัง: อาจเป็นโชค" if pk_ >= 0.05 else "ระวัง: CLV ติดลบ")
                rows_.append([k, q.RULE_NAMES.get(k, ""), f"{lc_[k]['w']}-{lc_[k]['l']}", f"{p1:.1%}", f"{pk_:.0%}",
                              (f"{cv * 100:+.1f}% ({cn} ไม้)" if cv is not None else "ยังไม่มี"), verdict_])
            st.markdown(html_table(["Rule", "ชื่อ", "ผล", "โอกาสเป็นโชค (ข้อเดียว)", f"เมื่อนับว่าทดสอบ {k_tested} ข้อ", "CLV", "สรุป"], rows_),
                        unsafe_allow_html=True)
            st.caption("อนุมัติเฉพาะข้อที่ “โอกาสเป็นโชคเมื่อนับจำนวนที่ทดสอบ” ต่ำกว่า 5% และ CLV ไม่ติดลบ · ยิ่งทดสอบหลายข้อพร้อมกัน ยิ่งมีข้อที่ผ่านเพราะโชคได้")
            sel_ = st.multiselect("เลือก Rule ที่จะอนุมัติ", ready_, key="cfg_appr",
                                  format_func=lambda k: f"{k} {q.RULE_NAMES.get(k, '')} · ชนะ {lc_[k]['w']}-{lc_[k]['l']}")
            ok_ap = st.checkbox("ยืนยัน: Rule ที่เลือกจะเริ่มมีผลต่อการฟันธง", key="cfg_appr_ok")
            if st.button("อนุมัติ Rule ที่เลือก", disabled=not (sel_ and ok_ap), key="cfg_appr_go"):
                for k_ in sel_:
                    q.approve_rule(store, k_)
                store.save()
                st.success("อนุมัติแล้ว: " + ", ".join(sel_))
                cloud_warn()
        # ---- เฝ้าดู Rule หลัก: เสนอพักเมื่อครบ 150 ครั้งและ z ≤ −2.5 (ไม่พักเอง ต้องอนุมัติ) ----
        st.markdown("**เฝ้าดู Rule หลัก**")
        bw_ = q.base_rule_watch(store.history, store.params)
        susp_ = list(store.params.get("suspended_base") or [])
        flag_ = [x for x in bw_ if x["propose"] or x["propose_back"] or x["suspended"]]
        show_ = flag_ + [x for x in bw_ if x not in flag_][:max(0, 6 - len(flag_))]
        st.markdown(html_table(["Rule", "ชื่อ", "ครั้ง", "ผล", "กำไรถ้าแทงตาม", "z (เทียบแทงสุ่ม)", "สถานะ"],
                               [[x["rule"], q.RULE_NAMES.get(x["rule"], ""), x["n"], f"{x['w']}-{x['l']}", f"{x['profit']:+.2f}",
                                 f"{x['z']:+.2f}",
                                 ("พักอยู่" + (" · ผลกลับมาบวก เสนอเปิดคืน" if x["propose_back"] else "")) if x["suspended"] else
                                 "เสนอพัก" if x["propose"] else
                                 (f"เฝ้าดู ({x['n']}/{q.BASE_WATCH_N})" if x["n"] < q.BASE_WATCH_N else "ใช้งานปกติ")] for x in show_]),
                    unsafe_allow_html=True)
        st.caption(f"แสดง Rule หลักที่ผลแย่ที่สุด {len(show_)} ข้อ · เสนอพักเมื่อครบ {q.BASE_WATCH_N} ครั้งและ z ≤ {q.BASE_WATCH_Z} เท่านั้น "
                   "(ทดสอบย้อนหลังแล้ว การพักเร็วกว่านี้ทำให้ผลแย่ลง เพราะ Rule หลายสิบข้อย่อมมีบางข้อโชคร้าย) · "
                   "Rule ที่พักยังคำนวณเก็บไว้ทุกนัด แต่ไม่นับคะแนนตอนฟันธง")
        cand_ = [x["rule"] for x in bw_ if x["propose"] or x["suspended"]]
        if cand_:
            sel_b = st.multiselect("Rule หลักที่พักไว้ (เลือก = พัก · เอาออก = เปิดคืน)", sorted(set(cand_)), default=[r for r in susp_ if r in cand_],
                                   key="cfg_susp", format_func=lambda k: f"{k} {q.RULE_NAMES.get(k, '')}")
            ok_b = st.checkbox("ยืนยันการเปลี่ยน Rule หลักที่พัก (มีผลต่อการฟันธงนัดถัดไป)", key="cfg_susp_ok")
            if st.button("บันทึก Rule หลักที่พัก", disabled=not ok_b, key="cfg_susp_go"):
                store.state["params"]["suspended_base"] = sorted(sel_b)
                store.save()
                st.success("บันทึกแล้ว: " + (", ".join(sel_b) if sel_b else "ไม่มี Rule หลักที่พัก"))
                cloud_warn()
        ws_ = q.weakskip_study(store.history)
        st.markdown("**ศึกษา: การข้ามเพราะสัญญาณอ่อน**")
        st.caption(f"ไม้ที่ข้ามเพราะสัญญาณอ่อน {ws_['n']} ไม้ ถ้าแทงไปจะได้ {ws_['w']}-{ws_['l']} {ws_['profit']:+.2f} หน่วย "
                   f"(คนแทงสุ่มคาดได้ {ws_['expected']:+.2f}) · z = {ws_['z']:+.2f} · "
                   + {"testing": f"กำลังศึกษา {ws_['n']}/{ws_['need']} ไม้ · ยังข้ามตามเดิม",
                      "keep": "ครบแล้ว การข้ามไม่ได้ทำให้พลาดไม้ดีอย่างมีนัยสำคัญ · ข้ามต่อไป",
                      "propose_off": f"ผ่านเกณฑ์ (z ≥ {ws_['z_need']:g}) · เสนอให้ลดเกณฑ์ “ข้ามเมื่อคะแนนต่ำกว่า” หรือปิดการข้ามสัญญาณอ่อน"}[ws_["status"]])
        sw_ = store.state.get("shadow_weights")
        if sw_:
            live = store.state["weights"]
            diffs = sorted(((k, live.get(k, 1.0), v) for k, v in sw_.items() if k in q.DEFAULT_WEIGHTS),
                           key=lambda x: -abs(x[2] - x[1]))[:10]
            st.markdown(html_table(["Rule", "ชื่อ", "ที่ใช้ฟันธง", "เบื้องหลัง (เงา)"],
                                   [[k, q.RULE_NAMES.get(k, ""), f"{a:.3f}", f"{b:.3f}"] for k, a, b in diffs]),
                        unsafe_allow_html=True)
            st.caption("น้ำหนักเงาคือค่าที่ระบบ “จะใช้” ถ้าไม่แช่แข็ง ใช้แท็บ “ทดสอบย้อนหลัง” เทียบว่าการปรับน้ำหนักช่วยจริงไหมก่อนนำมาใช้")
            w1, w2 = st.columns(2)
            ok_w = st.checkbox("ยืนยันการเปลี่ยนน้ำหนักที่ใช้ฟันธง", key="cfg_wok")
            if w1.button("ใช้น้ำหนักเบื้องหลังแทน", disabled=not ok_w, key="cfg_apply"):
                store.state["weights"].update({k: v for k, v in sw_.items() if k in q.DEFAULT_WEIGHTS})
                store.save()
                st.success("เปลี่ยนน้ำหนักที่ใช้ฟันธงเป็นค่าเบื้องหลังแล้ว")
            if w2.button("รีเซ็ตน้ำหนักที่ใช้ฟันธงเป็นค่าเริ่มต้น", disabled=not ok_w, key="cfg_reset"):
                store.state["weights"].update(q.DEFAULT_WEIGHTS)
                store.save()
                st.success("รีเซ็ตแล้ว (ค่าเริ่มต้นคือแบบที่ทำผลดีที่สุดใน backtest ของข้อมูลชุดปัจจุบัน)")
    with st.expander("คำนวณสถานะ Rule ใหม่ทั้งหมดจากประวัติ"):
        st.caption("ไล่คำนวณการเรียนรู้ใหม่ตั้งแต่นัดแรกตามลำดับที่บันทึกผล ด้วยเกณฑ์ปัจจุบัน: ตัวนับผลของ Rule ผู้สมัครจะครบตั้งแต่วันที่ Rule ถูกสร้าง "
                   "Rule ที่ผ่านเกณฑ์จะเปลี่ยนเป็น “ใช้งาน” และมีผลต่อการฟันธงนัดถัดไป · ไม้ที่บันทึกไว้แล้วและน้ำหนักที่ใช้ฟันธง (ขณะแช่แข็ง) ไม่เปลี่ยน · "
                   "ระบบจะทำขั้นตอนเดียวกันนี้เองทุกครั้งที่คุณแก้สกอร์หรือยกเลิกผล")
        ok_rb = st.checkbox("ยืนยันการคำนวณใหม่ (ควรดาวน์โหลดไฟล์สำรองที่แท็บ “สำรองข้อมูล” ก่อน)", key="rb_ok")
        if st.button("คำนวณใหม่ทั้งหมด", disabled=not ok_rb, key="rb_go"):
            before_ = {k: v.get("status") for k, v in (store.state.get("lifecycle") or {}).items()}
            n_rb = q.rebuild_learning(store)
            store.save()
            life_ = store.state.get("lifecycle") or {}
            act_ = sorted(k for k, v in life_.items() if v.get("status") == "active")
            chg_ = sum(1 for k, v in life_.items() if before_.get(k) != v.get("status"))
            st.success(f"คำนวณใหม่จาก {n_rb} นัดแล้ว · Rule ที่เปลี่ยนสถานะ {chg_} ข้อ · ใช้งานอยู่: {', '.join(act_) if act_ else 'ไม่มี'}")
            cloud_warn()
    with st.expander("ลบรายการในประวัติ"):
        opts_h = {r["id"]: f"{r['features']['home']} vs {r['features']['away']} ({'ผลแล้ว' if r['status'] == 'settled' else 'รอผล'})"
                  for r in reversed(store.history)}
        pick_ids = st.multiselect("เลือกรายการที่จะลบ", list(opts_h), format_func=lambda i: opts_h[i])
        st.caption("การลบรายการที่บันทึกผลแล้วจะไม่ย้อนน้ำหนัก Rule ที่เคยปรับไปแล้ว")
        if st.button("ลบที่เลือก", disabled=not (pick_ids and st.checkbox("ยืนยันการลบ", key="confirm_hist_del"))):
            q.delete_records(store, pick_ids)
            st.rerun()

# ================================================================ TAB 4 (ทดสอบย้อนหลัง)
with tab4:
    store = q.Store(DATA_DIR)
    n_done = sum(1 for r in store.history if r["status"] == "settled" and r.get("features") and r.get("score"))
    st.markdown('<div class="fq"><div class="fq-sec">ทดสอบย้อนหลัง <small>เทียบ “ไม่เรียนรู้” กับ “เรียนรู้ต่อเนื่อง” บนผลที่บันทึกไว้ · ไม่มองอนาคต (walk-forward)</small></div></div>',
                unsafe_allow_html=True)
    card("วิธีทดสอบ", '<div class="muted">เดินตามลำดับที่ใส่ผลทีละนัด · ให้ 3 แบบฟันธงด้วยสถานะ ณ ตอนนั้น: '
         '<b>ไม่เรียนรู้</b> (Rule เดิมตลอด) · <b>เรียนรู้เฉพาะน้ำหนัก</b> · <b>เรียนรู้เต็มรูปแบบ</b> (น้ำหนัก + สร้าง Rule ใหม่) '
         'แล้วตัดสินด้วยสกอร์จริงก่อนให้แบบที่เรียนรู้อัปเดตตัวเอง ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากัน</div>')
    if n_done < 2:
        st.info(f"ตอนนี้มีรายการที่บันทึกผลแล้ว {n_done} นัด ต้องมีอย่างน้อย 2 นัด (และควรมี {bt.MIN_RELIABLE} นัดขึ้นไปจึงจะสรุปได้)")
    else:
        st.caption(f"ข้อมูลที่ใช้ได้: {n_done} นัด" + ("" if n_done >= bt.MIN_RELIABLE else f" · น้อยกว่า {bt.MIN_RELIABLE} นัด ผลที่ได้ใช้ตัดสินไม่ได้"))
        b1, b2 = st.columns(2)
        bt_min = b1.number_input("จำนวนนัดขั้นต่ำก่อนสร้าง Rule ใหม่", 3, 30, int(store.params["disc_min_n"]), key="bt_minn")
        bt_mode = st.radio("วิธีรวมคะแนนสัญญาณ", ["sum", "grouped"], horizontal=True, key="bt_mode",
                           format_func=lambda x: {"sum": "รวมทุก Rule (ปัจจุบัน)", "grouped": "นับกลุ่มข้อมูลละครั้ง (ไม่บวกซ้ำ)"}[x])
        bt_perm = b2.number_input("จำนวนรอบสุ่มสลับสกอร์ (0 = ไม่รัน)", 0, 200, 60, step=20, key="bt_perm",
                                  help="ยิ่งมากยิ่งแม่นแต่ช้าลง ใช้คำนวณ p-value ว่ากำไรจากการเรียนรู้สูงกว่าความบังเอิญหรือไม่")
        if st.button("▶ รัน Backtest", type="primary"):
            with st.spinner("กำลังทดสอบย้อนหลัง..."):
                ss["bt"] = bt.run_backtest(store.history, {"disc_min_n": int(bt_min), "score_mode": bt_mode}, permute=int(bt_perm))
        if ss.get("bt"):
            show(SP.backtest_story(ss["bt"]), key="bt")
            st.download_button("ดาวน์โหลดรายงาน Backtest (HTML แบบเล่าเรื่อง)", SP.backtest_document(ss["bt"]),
                               file_name=f"backtest_{q.now_th('%Y%m%d')}.html", mime="text/html", key="dl_bt")

# ================================================================ TAB 4
with tab5:
    store = q.Store(DATA_DIR)
    rs = q.REMOTE_STATE
    be = q.remote_backend()
    cfg_ok = be is not None
    be_name = {"sheets": "Google Sheets", "gist": "GitHub Gist"}.get(be, "")
    show(SP.sync_story(be_name if cfg_ok else None, rs.get("ok"), rs.get("error"), rs.get("last"), len(store.history),
                       sum(1 for r in store.history if r["status"] == "settled"), len(store.state.get("learned_rules", [])), be == "sheets"),
         key="sync")
    if cfg_ok:
        c1, c2 = st.columns(2)
        if c1.button("ซิงก์ขึ้นคลาวด์ตอนนี้"):
            store.save()
            if rs.get("ok"):
                st.success("ซิงก์สำเร็จ")
            else:
                st.error(rs.get("error"))
        if c2.button("ดึงข้อมูลจากคลาวด์"):
            if store.pull_remote():
                st.success("ดึงข้อมูลสำเร็จ")
                st.rerun()
            else:
                st.error(rs.get("error") or "ดึงข้อมูลไม่สำเร็จ")
    with st.expander("วิธีตั้งค่าด้วย Google Sheets (แนะนำ · ทำครั้งเดียว)"):
        st.markdown(
            "1. เปิดไฟล์ Google Sheets ของคุณ → เมนู **Extensions → Apps Script**  \n"
            "2. ลบโค้ดเดิม แล้ววางโค้ดด้านล่าง จากนั้นแก้ค่า `TOKEN` เป็นรหัสลับที่คุณตั้งเอง (ยาว ๆ เดายาก) แล้วกด Save  \n"
            "3. กด **Deploy → New deployment** → ประเภท **Web app** → Execute as: **Me** · Who has access: **Anyone** → Deploy "
            "→ กดอนุญาตสิทธิ์ (ถ้าขึ้นว่า Google ยังไม่ได้ตรวจสอบแอป ให้เลือก Advanced → Go to ... เพราะเป็นสคริปต์ของคุณเอง)  \n"
            "4. คัดลอก **Web app URL** (ลงท้ายด้วย `/exec`) แล้วใส่ใน Streamlit Secrets:")
        st.code('SHEETS_URL = "https://script.google.com/macros/s/.../exec"\nSHEETS_TOKEN = "รหัสลับเดียวกับ TOKEN ในสคริปต์"', language="toml")
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps_script", "Code.gs"), encoding="utf-8") as fh:
                st.code(fh.read(), language="javascript")
        except Exception:  # noqa
            st.caption("ไม่พบไฟล์ apps_script/Code.gs ใน repo")
        st.caption("แก้โค้ดสคริปต์ภายหลัง ต้อง Deploy → Manage deployments → แก้ไข → New version อีกครั้ง · "
                   "แนะนำให้ตั้งการแชร์ชีตเป็น “Restricted” (เฉพาะคุณ) เพราะสคริปต์ทำงานในนามเจ้าของไฟล์ ไม่ต้องเปิดลิงก์สาธารณะ")
    with st.expander("ทางเลือก: GitHub Gist"):
        st.markdown(
            "สร้าง Secret Gist ที่ gist.github.com (ไฟล์ `state.json` เนื้อหา `{}`) แล้วสร้าง Fine-grained token สิทธิ์ **Gists: Read and write**")
        st.code('GITHUB_TOKEN = "github_pat_..."\nGIST_ID = "รหัส gist ของคุณ"', language="toml")
        st.caption("ถ้าตั้งทั้ง Google Sheets และ Gist ระบบจะใช้ Google Sheets")
    card("ไฟล์สำรอง (ทางเลือก)", '<div class="muted">ดาวน์โหลดเก็บไว้เองอีกชั้นหนึ่ง หรือใช้กู้คืนข้อมูลจากเครื่องอื่น</div>')
    blob = json.dumps({"state": store.state, "history": store.history}, ensure_ascii=False, indent=1)
    st.download_button("ดาวน์โหลดไฟล์สำรอง", blob, file_name=f"quant_backup_{q.now_th('%Y%m%d')}.json",
                       mime="application/json")
    up = st.file_uploader("กู้คืนจากไฟล์สำรอง (เขียนทับข้อมูลปัจจุบัน)", type=["json"], key="restore")
    if up is not None and st.button("กู้คืน", type="primary"):
        try:
            d = json.loads(up.getvalue().decode("utf-8"))
            assert "state" in d and "history" in d
            store.state, store.history = d["state"], d["history"]
            for k, v in q.DEFAULT_WEIGHTS.items():
                store.state["weights"].setdefault(k, v)
            q.REMOTE_STATE["blocked"] = False          # ผู้ใช้ตั้งใจกู้คืนเอง -> อนุญาตให้ซิงก์ทับคลาวด์
            store.save()
            st.success("กู้คืนสำเร็จ")
            cloud_warn()
        except Exception:  # noqa
            st.error("ไฟล์สำรองไม่ถูกต้อง")


# ================================================================ TAB 6 (จัดการผู้ใช้ · Admin)
if tab6 is not None:
    with tab6:
        acc = access.load(DATA_DIR)
        if access.ACCESS_REMOTE.get("ok") is False:
            st.warning(f"บันทึกรายชื่อ/โควตาขึ้นที่เก็บถาวรไม่สำเร็จ: {access.ACCESS_REMOTE['error']}")
        show(SP.users_story(acc, ADMINS, lambda e_: access.used_today(e_, acc), lambda r_: access.limit_of(r_, acc), access.ROLE_TH), key="users")
        st.caption("Admin = อีเมลใน Secrets ADMIN_EMAILS · User / Local ต้องได้รับเชิญ เห็นเฉพาะหน้าวิเคราะห์ และไม่บันทึกผล · "
                   "โควตารีเซ็ตเที่ยงคืนเวลาไทย · นับเฉพาะการวิเคราะห์ที่สำเร็จ")
        st.markdown('<div class="fq"><div class="fq-sec">เชิญผู้ใช้</div></div>', unsafe_allow_html=True)
        i1, i2, i3 = st.columns([3, 1.3, 1])
        new_email = i1.text_input("อีเมล Google", key="inv_email", placeholder="name@gmail.com", label_visibility="collapsed")
        new_role = i2.selectbox("ระดับ", ["user", "local"], key="inv_role", label_visibility="collapsed",
                                format_func=lambda r: f"{access.ROLE_TH[r]} ({acc['limits'][r]} ครั้ง/วัน)")
        if i3.button("เชิญ", type="primary", key="inv_go"):
            try:
                if access.norm(new_email) in ADMINS:
                    st.info("อีเมลนี้เป็น Admin อยู่แล้ว")
                else:
                    access.invite(DATA_DIR, new_email, new_role, EMAIL)
                    st.success(f"เชิญ {access.norm(new_email)} เป็น {access.ROLE_TH[new_role]} แล้ว")
                    st.rerun()
            except ValueError as e_:
                st.error(str(e_))
        st.caption("ถ้าแอปใน Google Cloud ยังอยู่สถานะ Testing ต้องเพิ่มอีเมลนี้ใน Test users ด้วย ไม่เช่นนั้น Google จะไม่ให้ล็อกอิน")
        st.markdown('<div class="fq"><div class="fq-sec">จัดการผู้ใช้</div></div>', unsafe_allow_html=True)
        if acc["users"]:
            m1, m2 = st.columns([3, 2])
            sel = m1.selectbox("เลือกผู้ใช้", sorted(acc["users"]), key="usr_sel")
            act = m2.selectbox("การกระทำ", ["เปลี่ยนเป็น User", "เปลี่ยนเป็น Local", "รีเซ็ตโควตาวันนี้", "ลบผู้ใช้"], key="usr_act")
            if st.checkbox("ยืนยันการกระทำ", key="usr_ok") and st.button("ดำเนินการ", key="usr_go"):
                if act == "ลบผู้ใช้":
                    access.remove(DATA_DIR, sel, EMAIL)
                elif act == "รีเซ็ตโควตาวันนี้":
                    access.reset_usage(DATA_DIR, sel, EMAIL)
                else:
                    access.invite(DATA_DIR, sel, "user" if "User" in act else "local", EMAIL)
                st.success("เรียบร้อย")
                st.rerun()
        st.markdown('<div class="fq"><div class="fq-sec">โควตาต่อวัน</div></div>', unsafe_allow_html=True)
        l1, l2, l3 = st.columns([1, 1, 1])
        nu = l1.number_input("User (ครั้ง/วัน)", 0, 100, int(acc["limits"]["user"]), key="lim_u")
        nl = l2.number_input("Local (ครั้ง/วัน)", 0, 100, int(acc["limits"]["local"]), key="lim_l")
        if l3.button("บันทึกโควตา", key="lim_go"):
            access.set_limits(DATA_DIR, nu, nl, EMAIL)
            st.success("บันทึกแล้ว")
            st.rerun()
