# -*- coding: utf-8 -*-
"""แดชบอร์ดแสดงผลวิเคราะห์ (HTML + CSS ล้วน ไม่ใช้ JavaScript/ไลบรารีกราฟ)

ทุกฟังก์ชันคืนสตริง HTML บรรทัดเดียวต่อบล็อก (ไม่มีบรรทัดว่าง) เพื่อให้ st.markdown(unsafe_allow_html=True) ไม่ตีความเป็น Markdown
"""
import html as _html

import football_quant_v58 as q

CSS = """
.fq { --acc:#14b8a6; --acc2:#6366f1; --up:#34d399; --down:#f87171; --warn:#fbbf24; --mut:#8fa3c0; --txt:#e6edf7;
      --line:rgba(255,255,255,.09); --panel:rgba(255,255,255,.045); font-variant-numeric:tabular-nums; color:var(--txt); }
.fq * { box-sizing:border-box; }
.fq-grid { display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); gap:12px; margin:12px 0; }
.fq-c2{grid-column:span 2}.fq-c3{grid-column:span 3}.fq-c4{grid-column:span 4}.fq-c5{grid-column:span 5}
.fq-c6{grid-column:span 6}.fq-c7{grid-column:span 7}.fq-c8{grid-column:span 8}.fq-c12{grid-column:span 12}
.fq-card { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 16px; min-width:0; }
.fq-h { display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:.7rem; letter-spacing:.08em;
        text-transform:uppercase; color:var(--mut); font-weight:600; margin-bottom:10px; }
.fq-sec { display:flex; align-items:baseline; gap:10px; margin:22px 2px 4px; font-weight:700; font-size:1.02rem; }
.fq-sec small { color:var(--mut); font-weight:400; font-size:.78rem; }
.fq-sec::after { content:""; flex:1; height:1px; background:var(--line); }
.fq-mut { color:var(--mut); } .fq-up { color:var(--up); } .fq-down { color:var(--down); } .fq-warn { color:var(--warn); }
.fq-small { font-size:.78rem; }
.fq-chip { display:inline-flex; align-items:center; gap:4px; font-size:.74rem; padding:2px 10px; border-radius:99px;
           background:rgba(99,102,241,.16); color:#c7d2fe; border:1px solid rgba(165,180,252,.25); white-space:nowrap; }
.fq-chip.ok { background:rgba(52,211,153,.14); color:#6ee7b7; border-color:rgba(110,231,183,.3); }
.fq-chip.bad { background:rgba(248,113,113,.14); color:#fca5a5; border-color:rgba(252,165,165,.3); }
.fq-chip.warn { background:rgba(251,191,36,.12); color:#fde68a; border-color:rgba(253,224,71,.3); }
.fq-chip.off { background:rgba(255,255,255,.05); color:var(--mut); border-color:var(--line); }
.fq-chip.acc { background:rgba(20,184,166,.16); color:#5eead4; border-color:rgba(94,234,212,.3); }
.fq-chips { display:flex; flex-wrap:wrap; gap:6px; }

/* KPI */
.fq-kpi { display:flex; flex-direction:column; justify-content:space-between; min-height:132px; }
.fq-kpi .big { font-size:1.55rem; font-weight:700; line-height:1.18; margin:2px 0 6px; }
.fq-kpi .num { font-size:1.9rem; font-weight:700; line-height:1.1; }
.fq-hero { background:linear-gradient(135deg, rgba(20,184,166,.22), rgba(99,102,241,.2)); border-color:rgba(94,234,212,.35); }
.fq-hero.low { background:linear-gradient(135deg, rgba(100,116,139,.28), rgba(71,85,105,.22)); border-color:rgba(148,163,184,.3); }
.fq-donut { width:96px; height:96px; border-radius:50%; margin:0 auto;
            background:conic-gradient(var(--c,#14b8a6) calc(var(--p,0)*1%), rgba(255,255,255,.1) 0); display:grid; place-items:center; }
.fq-donut > div { width:74px; height:74px; border-radius:50%; background:#0e182b; display:flex; flex-direction:column;
                  align-items:center; justify-content:center; font-weight:700; font-size:1.2rem; line-height:1.1; }
.fq-donut small { font-weight:400; font-size:.64rem; color:var(--mut); }
.fq-lvl { display:flex; align-items:flex-end; gap:5px; height:36px; }
.fq-lvl i { display:block; width:12px; border-radius:3px; }
.fq-best { margin-top:8px; padding:7px 10px; border-radius:10px; background:rgba(52,211,153,.12); border:1px solid rgba(110,231,183,.3); font-size:.8rem; color:#a7f3d0; }
.fq-meter { height:6px; border-radius:99px; background:rgba(255,255,255,.1); overflow:hidden; margin-top:8px; }
.fq-meter > i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--acc),#22d3ee); }

/* ทีม */
.fq-teams { display:grid; grid-template-columns:1fr auto 1fr; gap:10px; align-items:start; text-align:center; }
.fq-team .nm { font-size:1.12rem; font-weight:700; margin:6px 0 2px; overflow-wrap:anywhere; }
.fq-team .rk { display:inline-block; font-size:.72rem; padding:1px 9px; border-radius:99px; background:rgba(255,255,255,.08); }
.fq-vs { align-self:center; font-weight:700; color:#64748b; padding-top:14px; }
.fq-dots { margin:6px 0 4px; } .fq-dot { display:inline-flex; width:21px; height:21px; border-radius:50%; align-items:center; justify-content:center;
           font-size:.66rem; font-weight:700; margin:0 2px; color:#0b1220; }
.fq-dot.w{background:#34d399}.fq-dot.d{background:#fbbf24}.fq-dot.l{background:#f87171}
.fq-kv { display:flex; justify-content:center; gap:14px; flex-wrap:wrap; font-size:.76rem; color:var(--mut); }
.fq-kv b { color:var(--txt); font-weight:600; }
.fq-h2h { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; margin-top:6px; }
.fq-h2h span { font-size:.78rem; font-weight:600; padding:3px 10px; border-radius:8px; border:1px solid var(--line); }
.fq-h2h .w{color:#6ee7b7;background:rgba(52,211,153,.1)}.fq-h2h .d{color:#fde68a;background:rgba(251,191,36,.1)}.fq-h2h .l{color:#fca5a5;background:rgba(248,113,113,.1)}

/* กราฟแท่ง */
.fq-stack { display:flex; height:30px; border-radius:8px; overflow:hidden; font-size:.72rem; font-weight:600; }
.fq-stack.thin { height:8px; margin-top:5px; opacity:.55; }
.fq-stack > div { display:flex; align-items:center; justify-content:center; white-space:nowrap; overflow:hidden; color:#04201d; }
.fq-stack .h{background:#2dd4bf}.fq-stack .d{background:#94a3b8}.fq-stack .a{background:#818cf8;color:#0b1020}
.fq-cols3 { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:10px; text-align:center; }
.fq-cols3 .o { font-size:1.2rem; font-weight:700; } .fq-cols3 .s { font-size:.7rem; color:var(--mut); }
.fq-line { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.fq-line .t { font-size:.68rem; color:var(--mut); } .fq-line .v { font-size:1.15rem; font-weight:700; }
.fq-line .b { padding:4px 10px; border-radius:10px; background:rgba(255,255,255,.06); border:1px solid var(--line); }
.fq-line .b.cur { background:rgba(20,184,166,.16); border-color:rgba(94,234,212,.4); }
.fq-bar { display:grid; grid-template-columns:minmax(0,1.45fr) 1.7fr auto; gap:8px; align-items:center; margin:7px 0; font-size:.82rem; }
.fq-bar .tr { height:9px; border-radius:99px; background:rgba(255,255,255,.09); overflow:hidden; }
.fq-bar .tr > i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#14b8a6,#22d3ee); }
.fq-bar .tr > i.alt { background:linear-gradient(90deg,#6366f1,#a78bfa); }
.fq-bar .n { text-align:right; font-weight:600; white-space:nowrap; }
.fq-bar .nm { line-height:1.25; font-size:.78rem; overflow-wrap:anywhere; }

/* สกอร์บอร์ดฝั่งตรงข้าม */
.fq-div { display:grid; grid-template-columns:116px 1fr 1fr 116px; gap:8px; align-items:center; margin:12px 0; }
.fq-div .side { min-width:0; line-height:1.25; }
.fq-div .side.r { text-align:right; }
.fq-div .side .nm { display:block; color:var(--mut); font-size:.72rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.fq-div .side b { font-size:1.08rem; font-weight:700; }
.fq-div .side.win b { color:var(--acc); }
.fq-div .side .tg { font-size:.68rem; color:var(--down); margin-left:4px; font-weight:600; }
.fq-div .half { height:16px; background:rgba(255,255,255,.06); display:flex; }
.fq-div .half.l { justify-content:flex-end; border-radius:8px 0 0 8px; }
.fq-div .half.r { border-radius:0 8px 8px 0; }
.fq-div .half i { display:block; height:100%; background:#475569; }
.fq-div .half.l i { border-radius:8px 0 0 8px; } .fq-div .half.r i { border-radius:0 8px 8px 0; }
.fq-div .half.win i { background:linear-gradient(90deg,#14b8a6,#22d3ee); }
.fq-div .half.l.win i { background:linear-gradient(270deg,#14b8a6,#22d3ee); }
.fq-div .half.ban i { background:repeating-linear-gradient(45deg,#475569,#475569 4px,#334155 4px,#334155 8px); opacity:.5; }

/* ตารางสัญญาณ */
.fq-tbl { width:100%; }
.fq-row { display:grid; grid-template-columns:minmax(0,2.3fr) minmax(0,1.5fr) minmax(0,1.6fr) 74px; gap:10px; align-items:center;
          padding:9px 0; border-bottom:1px solid var(--line); font-size:.82rem; }
.fq-row:last-child { border-bottom:none; } .fq-row.head { color:var(--mut); font-size:.68rem; letter-spacing:.06em; text-transform:uppercase; padding-top:0; }
.fq-row .rn { min-width:0; } .fq-row .rn b { display:block; font-weight:600; overflow-wrap:anywhere; }
.fq-row .rn small { color:var(--mut); display:block; line-height:1.35; margin-top:2px; }
.fq-row .sc { display:flex; align-items:center; gap:8px; }
.fq-row .sc .tr { flex:1; height:7px; border-radius:99px; background:rgba(255,255,255,.09); overflow:hidden; }
.fq-row .sc .tr > i { display:block; height:100%; background:linear-gradient(90deg,#14b8a6,#22d3ee); border-radius:99px; }
.fq-row .sc b { min-width:44px; text-align:right; }
.fq-ev { margin:6px 0 0; padding-left:18px; color:#b8c7df; font-size:.84rem; line-height:1.6; }
.fq-check { display:grid; grid-template-columns:22px 1fr; gap:6px; font-size:.82rem; margin:6px 0; line-height:1.4; }

/* สถิติ */
.fq-pl { display:flex; align-items:stretch; gap:3px; height:130px; margin-top:6px; }
.fq-pl > div { flex:1; max-width:34px; position:relative; min-width:3px; }
.fq-pl .mid { position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(255,255,255,.18); }
.fq-pl i { position:absolute; left:10%; right:10%; border-radius:3px; }
.fq-pl i.p { bottom:50%; background:#34d399; } .fq-pl i.n { top:50%; background:#f87171; }
.fq-w { display:grid; grid-template-columns:minmax(0,1.6fr) 2fr 58px; gap:8px; align-items:center; margin:7px 0; font-size:.8rem; }
.fq-w .tr { height:8px; border-radius:99px; background:rgba(255,255,255,.09); position:relative; }
.fq-w .tr > i { display:block; height:100%; border-radius:99px; }
.fq-w .tr > u { position:absolute; top:-3px; width:2px; height:14px; background:rgba(255,255,255,.55); }
.fq-w .nm { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.fq-w .nm small { color:var(--mut); }
.fq-hist { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; padding:9px 0; border-bottom:1px solid var(--line); font-size:.84rem; }
.fq-hist:last-child { border-bottom:none; } .fq-hist small { color:var(--mut); display:block; }
.fq-empty { padding:22px; text-align:center; color:var(--mut); border:1px dashed var(--line); border-radius:14px; }

/* ข้อมูลทีม */
.fq-tn { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:10px 18px; }
.fq-tn h4 { margin:0 0 6px; font-size:.86rem; font-weight:700; }
.fq-tn .it { font-size:.82rem; line-height:1.5; margin:3px 0; }
.fq-tn .src { color:var(--mut); font-size:.7rem; margin-left:4px; }
.fq-tn .na { color:#64748b; font-style:italic; }
.fq-tn .strike { color:#fca5a5; text-decoration:line-through; opacity:.75; }
.fq-tn a, .fq-srcs a { color:#5eead4; text-decoration:none; } .fq-srcs a:hover { text-decoration:underline; }
.fq-tn .xg { display:flex; gap:14px; flex-wrap:wrap; } .fq-tn .xg b { font-size:1.05rem; }
@media (max-width: 820px) { .fq-tn { grid-template-columns:1fr; } }

@media (max-width: 820px) {
  .fq-grid > * { grid-column:span 12 !important; }
  .fq-grid > .fq-m6 { grid-column:span 6 !important; }
  .fq-kpi { min-height:0; }
  .fq-row { grid-template-columns:minmax(0,1fr) minmax(0,1fr); }
  .fq-row .ch, .fq-row .wt { display:none; }
  .fq-row.head { display:none; }
  .fq-div { grid-template-columns:74px 1fr 1fr 74px; gap:6px; }
  .fq-sec { flex-wrap:wrap; row-gap:2px; } .fq-sec small { flex-basis:100%; } .fq-sec::after { display:none; }
}
"""


def e(x):
    return _html.escape(str(x))


def _card(title, body, cls="", tag=""):
    return (f'<div class="fq-card {cls}"><div class="fq-h"><span>{e(title)}</span>{tag}</div>{body}</div>')


def _chip(text, kind=""):
    return f'<span class="fq-chip {kind}">{e(text)}</span>'


def _arrow(v, eps=1e-9):
    return ("fq-up", "▲") if v > eps else (("fq-down", "▼") if v < -eps else ("fq-mut", "■"))


def _market_th(mk, f):
    return {"HDP_HOME": f"แฮนดิแคป {f['home']}", "HDP_AWAY": f"แฮนดิแคป {f['away']}", "OU_OVER": "สูง (Over)",
            "OU_UNDER": "ต่ำ (Under)", "X12_HOME": f"1X2 {f['home']}", "X12_AWAY": f"1X2 {f['away']}"}.get(mk, mk)


def _dots(seq):
    cls = {"W": "w", "D": "d", "L": "l"}
    return "".join(f'<span class="fq-dot {cls.get(c, "d")}">{e(c)}</span>' for c in str(seq or "").upper())


# ------------------------------------------------------------------ ส่วนบน: KPI + แมตช์
def kpi_and_match(res):
    m, f, pick = res["m"], res["f"], res["pick"]
    low = pick["tier"] == "ต่ำ"
    chips = [_chip(f"ระดับ{pick['tier']}", "off" if low else "acc")]
    if pick.get("verify_fail"):
        chips.append(_chip("เหย้า/เยือนไม่ผ่าน", "bad"))
    if pick.get("move_only"):
        chips.append(_chip("มาจากการไหลของราคาล้วน", "warn"))
    for v in pick.get("veto", []):
        chips.append(_chip("แบน " + _market_th(v, f), "bad"))
    ru = [r for r in pick.get("runner_up", []) if r[1] > 0.05][:1]
    runner = (f'<div class="fq-small fq-mut" style="margin-top:6px">ทางเลือกรอง: {e(_market_th(ru[0][0], f))} '
              f'({ru[0][1]:.2f})</div>') if ru else ""
    if pick.get("skip"):
        why = "".join(f"<li>{e(x)}</li>" for x in pick.get("skip_reasons", []))
        c1 = (f'<div class="fq-card fq-c5 fq-kpi fq-hero low"><div class="fq-h"><span>สัญญาณ: ข้ามไม้นี้</span>'
              f'<span class="fq-chip warn">ไม่นับเป็นไม้ที่เล่น</span></div><div><div class="big">⏭ ข้าม</div>'
              f'<div class="fq-small fq-mut">ไม้เงา (ติดตามผลเบื้องหลัง): <b>{e(pick["label"])}</b></div>'
              f'<ul class="fq-ev" style="margin-top:4px">{why}</ul></div></div>')
    else:
        bst = pick.get("best")
        best_html = (f'<div class="fq-best">💰 ราคาดีที่สุด: <b>{e(bst["book"])} @{bst["price"]:.2f}</b> '
                     f'(ดีกว่าราคามัธยฐาน +{bst["gain"]:.2f} · จุดคุ้มทุน {bst["breakeven"]:.1%} จาก {bst["breakeven_median"]:.1%})</div>') if bst else ""
        c1 = (f'<div class="fq-card fq-c5 fq-kpi fq-hero{" low" if low else ""}"><div class="fq-h"><span>สัญญาณฟันธงเดี่ยว</span>'
              f'<span class="fq-chip off">ใช้ราคาปัจจุบัน</span></div><div><div class="big">{e(pick["label"])}</div>'
              f'<div class="fq-chips">{"".join(chips)}</div>{best_html}{runner}</div></div>')
    lv = {"ต่ำ": 1, "กลาง": 2, "สูง": 3}.get(pick["tier"], 1)
    bars = "".join(f'<i style="height:{14 + 10 * i}px;background:{"#14b8a6" if i < lv else "rgba(255,255,255,.12)"}"></i>' for i in range(3))
    c2 = _card("ระดับสัญญาณ",
               f'<div style="display:flex;align-items:flex-end;gap:14px"><div class="fq-lvl">{bars}</div>'
               f'<div><div class="num">{e(pick["tier"])}</div><div class="fq-small fq-mut">จัดระดับจากคะแนน · ไม่ใช่โอกาสชนะ</div></div></div>',
               "fq-c3 fq-m6 fq-kpi")
    c3 = _card("คะแนนสัญญาณ",
               f'<div><div class="num">{pick["strength"]:.2f}</div><div class="fq-small fq-mut">เต็ม ~4.0 ขึ้นไป</div>'
               f'<div class="fq-meter"><i style="width:{min(pick["strength"] / 4 * 100, 100):.0f}%"></i></div></div>', "fq-c2 fq-m6 fq-kpi")
    ok_n = sum(1 for ok, _ in f.get("verify", []) if ok)
    tot = len(f.get("verify", []))
    vkind = "bad" if f.get("verify_fail") else "ok"
    c4 = _card("ตรวจเหย้า/เยือน",
               f'<div><div class="num {"fq-down" if f.get("verify_fail") else "fq-up"}">{ok_n}/{tot}</div>'
               f'<div class="fq-small fq-mut" style="margin-top:6px">{_chip("ผ่านทุกข้อ" if not f.get("verify_fail") else "มีข้อไม่ผ่าน", vkind)}</div></div>', "fq-c2 fq-kpi")
    kpis = '<div class="fq-grid">' + c1 + c2 + c3 + c4 + '</div>'

    # การ์ดแมตช์
    tv, fm, st = m.get("team_value") or {}, m.get("form") or {}, m.get("stats") or {}
    rs = m.get("research") or {}

    def team(side, name):
        rk = f.get("rank_home") if side == "home" else f.get("rank_away")
        x = fm.get(side) or {}
        role = "เจ้าบ้าน" if side == "home" else "ทีมเยือน"
        is_fav = (f["fav"] == side)
        kv = []
        if tv.get(side):
            kv.append(f'มูลค่า <b>{tv[side]:g}</b>')
        if x.get("win_rate") is not None:
            kv.append(f'ชนะ <b>{x["win_rate"]:g}%</b>')
        if x.get("gf") is not None and x.get("ga") is not None:
            kv.append(f'ได้/เสีย <b>{x["gf"]:g}/{x["ga"]:g}</b>')
        return (f'<div class="fq-team"><div class="fq-chips" style="justify-content:center">{_chip(role, "off")}'
                f'{_chip("ทีมต่อ", "acc") if is_fav else ""}</div>'
                f'<div class="nm">{e(name)}</div>'
                f'{"<span class=rk>อันดับ " + e(f"{rk:g}") + "</span>" if rk is not None else ""}'
                f'<div class="fq-dots">{_dots(x.get("seq"))}</div><div class="fq-kv">{"".join(f"<span>{k}</span>" for k in kv)}</div></div>')
    comp = rs.get("competition") or f.get("league") or ""
    h2h = ""
    items = []
    for hh in (m.get("h2h") or [])[:5]:
        same = hh.get("home_is_current_home", True)
        ch, ca = (hh["hg"], hh["ag"]) if same else (hh["ag"], hh["hg"])
        k = "w" if ch > ca else "l" if ch < ca else "d"
        items.append(f'<span class="{k}">{ch}–{ca}</span>')
    if items:
        h2h = (f'<div style="margin-top:12px;text-align:center"><div class="fq-small fq-mut">H2H {len(items)} นัดล่าสุด · '
               f'สกอร์มองจากเจ้าบ้านปัจจุบัน (เขียว = เจ้าบ้านชนะ)</div><div class="fq-h2h">{"".join(items)}</div></div>')
    match = ('<div class="fq-grid"><div class="fq-c12 fq-card"><div class="fq-h"><span>แมตช์</span>'
             f'<span class="fq-chip off">{e(comp)}</span></div><div class="fq-teams">{team("home", f["home"])}'
             f'<div class="fq-vs">VS</div>{team("away", f["away"])}</div>{h2h}</div></div>')
    return '<div class="fq">' + kpis + match + '</div>'


# ------------------------------------------------------------------ ส่วนล่าง: ตลาดราคา / คะแนน / Rule / บริบท
def _water_bar(label, w, drop=None, alt=False):
    width = max(4, min(100, (w - 0.6) / 0.7 * 100))
    d = ""
    if drop is not None and abs(drop) >= 0.005:
        cls = "fq-up" if drop > 0 else "fq-down"
        d = f' <span class="{cls} fq-small">{-drop:+.2f}</span>'
    return (f'<div class="fq-bar"><span class="nm">{e(label)}</span><div class="tr"><i class="{"alt" if alt else ""}" style="width:{width:.0f}%"></i></div>'
            f'<span class="n">{w:.2f}{d}</span></div>')


def analysis_body(res):
    m, f, contribs, pick = res["m"], res["f"], res["contribs"], res["pick"]
    out = ['<div class="fq">']

    # ---- ตลาดราคา
    out.append('<div class="fq-sec">ตลาดราคา <small>ราคาปัจจุบันเป็นหลัก · ราคาเปิดอ้างอิงการไหล · ค่าน้ำที่เปลี่ยน: ลด = เขียว (เงินเข้า) · ขึ้น = แดง</small></div><div class="fq-grid">')
    xo, xc = q.implied(f["x12_open"]), q.implied(f["x12_cur"])
    o, c = f["x12_open"], f["x12_cur"]
    segs = "".join(f'<div class="{k}" style="width:{p * 100:.1f}%">{lab} {p:.0%}</div>' for k, lab, p in
                   (("h", "เหย้า", xc[0]), ("d", "เสมอ", xc[1]), ("a", "เยือน", xc[2])))
    segs_o = "".join(f'<div class="{k}" style="width:{p * 100:.1f}%"></div>' for k, p in (("h", xo[0]), ("d", xo[1]), ("a", xo[2])))
    cells = ""
    for i, lab in enumerate(("เหย้า", "เสมอ", "เยือน")):
        dpp = (xc[i] - xo[i]) * 100
        cl, ar = _arrow(dpp, 0.3)
        cells += (f'<div><div class="s">{lab}</div><div class="o">{c[i]:.2f}</div>'
                  f'<div class="s">เปิด {o[i]:.2f}</div><div class="s {cl}">{ar} {dpp:+.1f}pp</div></div>')
    out.append(_card("1X2 · โอกาสโดยนัย", f'<div class="fq-stack">{segs}</div><div class="fq-stack thin">{segs_o}</div>'
                     f'<div class="fq-small fq-mut" style="margin-top:3px">แท่งบาง = ราคาเปิด</div><div class="fq-cols3">{cells}</div>', "fq-c4"))

    sh = f["hdp_shift_fav"]
    cl, ar = _arrow(sh)
    word = "แรงขึ้น" if sh > 0 else "อ่อนลง" if sh < 0 else "คงที่"
    hbody = (f'<div class="fq-line"><div class="b"><div class="t">เปิด</div><div class="v">{e(q.fmt_line(f["line_o"]))}</div></div>'
             f'<span class="{cl}">→</span><div class="b cur"><div class="t">ปัจจุบัน</div><div class="v">{e(q.fmt_line(f["line_c"]))}</div></div>'
             f'<span class="{cl} fq-small">{ar} ทีมต่อ{word} {sh:+g}</span></div>')
    hbody += _water_bar(f"{f['fav_name']} (ต่อ)", f["fav_water_c"], f["fav_drop"])
    hbody += _water_bar(f"{f['dog_name']} (รอง)", f["dog_water_c"], f["dog_drop"], alt=True)
    if abs(sh) >= 0.01:
        hbody += (f'<div class="fq-small fq-mut">ปรับตามเรตแล้ว: ทีมต่อ {-f["fav_drop_adj"]:+.2f} · ทีมรอง {-f["dog_drop_adj"]:+.2f}</div>')
    hbody += (f'<div class="fq-small fq-mut" style="margin-top:6px">พูล 1X2 ทีมต่อ {f["x12_pp"]:+.1f}pp · ความขัดแย้ง {f["conflict"]:.0%}</div>')
    out.append(_card("แฮนดิแคป", hbody, "fq-c4", _chip(f"ทีมต่อ {f['fav_name']}", "acc")))

    if f["has_ou"]:
        cl, ar = _arrow(f["ou_shift"])
        obody = (f'<div class="fq-line"><div class="b"><div class="t">เปิด</div><div class="v">{f["ou_o"]:g}</div></div>'
                 f'<span class="{cl}">→</span><div class="b cur"><div class="t">ปัจจุบัน</div><div class="v">{f["ou_c"]:g}</div></div>'
                 f'<span class="{cl} fq-small">{ar} {f["ou_shift"]:+g}</span></div>')
        obody += _water_bar("สูง (Over)", f["over_water_c"], f["over_drop"])
        obody += _water_bar("ต่ำ (Under)", f["under_water_c"], f["under_drop"], alt=True)
        if f.get("exp_total") is not None:
            obody += f'<div class="fq-small fq-mut" style="margin-top:6px">ประตูรวมคาดการณ์จากสถิติ {f["exp_total"]:.2f}</div>'
        out.append(_card("สูง / ต่ำ", obody, "fq-c4"))
    else:
        out.append(_card("สูง / ต่ำ", '<div class="fq-mut">ไม่มีข้อมูล</div>', "fq-c4"))
    out.append('</div>')

    # ---- สกอร์บอร์ด
    tot = {}
    for ct in contribs:
        tot[ct["market"]] = tot.get(ct["market"], 0.0) + ct["eff"]
    veto = set(pick.get("veto", []))
    mx = max([1.0] + [v for k, v in tot.items() if k not in veto])

    def drow(lab_l, lab_r, kl, kr):
        vl, vr = (0.0 if kl in veto else tot.get(kl, 0.0)), (0.0 if kr in veto else tot.get(kr, 0.0))
        win_l, win_r = pick["market"] == kl, pick["market"] == kr
        tl = '<span class="tg">แบน</span>' if kl in veto else ""
        tr_ = '<span class="tg">แบน</span>' if kr in veto else ""
        return (f'<div class="fq-div"><div class="side l{" win" if win_l else ""}"><span class="nm">{e(lab_l)}</span><b>{vl:.2f}{" ★" if win_l else ""}</b>{tl}</div>'
                f'<div class="half l{" win" if win_l else ""}{" ban" if kl in veto else ""}"><i style="width:{vl / mx * 100:.0f}%"></i></div>'
                f'<div class="half r{" win" if win_r else ""}{" ban" if kr in veto else ""}"><i style="width:{vr / mx * 100:.0f}%"></i></div>'
                f'<div class="side r{" win" if win_r else ""}"><span class="nm">{e(lab_r)}</span><b>{"★ " if win_r else ""}{vr:.2f}</b>{tr_}</div></div>')
    cap = lambda t: f'<div class="fq-small fq-mut" style="margin:14px 0 -4px;letter-spacing:.04em">{t}</div>'
    sb = cap("แฮนดิแคป") + drow(f["home"], f["away"], "HDP_HOME", "HDP_AWAY") + (cap("สูง / ต่ำ") + drow("สูง (Over)", "ต่ำ (Under)", "OU_OVER", "OU_UNDER") if f["has_ou"] else "")
    out.append('<div class="fq-sec">คะแนนสัญญาณต่อทางเลือก <small>คะแนนรวมหลังคูณน้ำหนัก · ★ = ทางเลือกที่ฟันธง</small></div>')
    out.append(_card("แฮนดิแคป และ สูง/ต่ำ", sb, "fq-c12"))

    # ---- Rule ที่ทำงาน
    rows = ['<div class="fq-row head"><span>Rule</span><span class="ch">ทางเลือก</span><span>คะแนน</span><span class="wt">น้ำหนัก</span></div>']
    top = sorted(contribs, key=lambda c: -c["eff"])[:8]
    cm = max([0.01] + [c["eff"] for c in top])
    for ct in top:
        rid = ct["rule"]
        basis = ("ไหลราคา", "warn") if rid in q.MOVEMENT_RULES else ("ปัจจุบัน/บริบท", "ok")
        w = ct["eff"] / ct["raw"] if ct["raw"] else 1.0
        rows.append(
            f'<div class="fq-row"><div class="rn"><b>{e(q.RULE_NAMES.get(rid, "Rule ที่เรียนรู้เอง"))} <span class="fq-mut fq-small">{e(rid)}</span></b>'
            f'<small>{e(ct["note"])}</small></div><div class="ch">{_chip(_market_th(ct["market"], f), "info")} {_chip(*basis)}</div>'
            f'<div class="sc"><div class="tr"><i style="width:{ct["eff"] / cm * 100:.0f}%"></i></div><b>{ct["eff"]:+.2f}</b></div>'
            f'<div class="wt fq-mut">×{w:.2f}</div></div>')
    out.append('<div class="fq-sec">Rule ที่ทำงาน <small>แสดง 8 อันดับแรก</small></div>')
    body = "".join(rows) if top else '<div class="fq-empty">ไม่มี Rule ใดทำงาน</div>'
    sh = pick.get("shadow") or []
    if sh:
        items = " · ".join(f'{x["id"]} → {_market_th(x["market"], f)}' for x in sh[:8])
        body += (f'<div class="fq-small fq-mut" style="margin-top:10px">Rule เงาที่เงื่อนไขตรงกับแมตช์นี้ (ติดตามผลเบื้องหลัง ไม่มีผลต่อการฟันธง): {e(items)}</div>')
    out.append(_card("สัญญาณที่ใช้ตัดสิน", body, "fq-c12"))

    # ---- บริบท + ตรวจเหย้า/เยือน
    ctx = m.get("context") or {}
    labels = [("derby", "ดาร์บี้"), ("high_scoring_league", "ลีกประตูเยอะ"), ("high_draw_league", "ลีกเสมอสูง"),
              ("high_volatility", "ลีกผันผวนสูง"), ("cup_group_stage", "ถ้วยรอบแบ่งกลุ่ม"), ("knockout", "น็อคเอาต์"),
              ("continental_cup", "ถ้วยทวีป"), ("late_goal_tendency", "ยิงท้ายเกมสูง"),
              ("women_or_regional", "ฟุตบอลหญิง/ลีกรอง"), ("asian_cup", "ถ้วยเอเชีย")]
    chips = [_chip({"league": "ลีก", "cup": "ถ้วย", "playoff": "เพลย์ออฟ"}.get(ctx.get("type", "league"), "ลีก"), "acc")]
    chips += [_chip(lb, "") for k, lb in labels if ctx.get(k)]
    if ctx.get("desperation") in ("home", "away"):
        chips.append(_chip("หนีตาย/ลุ้นหนัก: " + (f["home"] if ctx["desperation"] == "home" else f["away"]), "warn"))
    if len(chips) == 1:
        chips.append(_chip("ไม่พบบริบทพิเศษ", "off"))
    rs = m.get("research") or {}
    cbody = f'<div class="fq-chips">{"".join(chips)}</div>'
    if rs.get("evidence"):
        cbody += '<ul class="fq-ev">' + "".join(f"<li>{e(x)}</li>" for x in rs["evidence"]) + "</ul>"
    conf = {"high": "สูง", "medium": "ปานกลาง", "low": "ต่ำ"}.get(rs.get("confidence"))
    tag = _chip("ค้นหาอัตโนมัติ" + (f" · ความน่าเชื่อถือ{conf}" if conf else ""), "off") if rs else ""
    vb = "".join(f'<div class="fq-check"><span>{"✅" if ok else "❌"}</span><span>{e(t)}</span></div>' for ok, t in f.get("verify", []))
    out.append('<div class="fq-sec">บริบทแมตช์ และ การตรวจเหย้า/เยือน</div><div class="fq-grid">')
    out.append(_card("บริบทแมตช์", cbody, "fq-c6", tag))
    out.append(_card("Home/Away Verification", vb or '<div class="fq-mut">ไม่มีข้อมูลการตรวจ</div>', "fq-c6"))
    out.append('</div></div>')
    return "".join(out) + team_news_section(m, f)


# ------------------------------------------------------------------ ข้อมูลทีม (xG, ตัวเจ็บ, บอลถ้วย, วันพัก)
_NA = '<span class="na">ไม่มีข้อมูล</span>'


def _src(d, as_of=None):
    t = " · ".join(x for x in (d, as_of) if x)
    return f'<span class="src">[{e(t)}]</span>' if t else ""


def _flag(st, why):
    if st == "ok":
        return ""
    lb = {"reported": "AI รายงาน รอยืนยัน", "unverified": "ไม่ยืนยันแหล่ง", "stale": "ข้อมูลเก่า", "invalid": "ค่าผิดปกติ"}.get(st, st)
    return " " + _chip(f"{lb} · ไม่นำไปใช้", "warn") + (f' <span class="src">{e(why)}</span>' if why else "")


def team_news_section(m, f):
    tn = m.get("team_news")
    if not tn:
        return ""
    head = ('<div class="fq-sec">ข้อมูลทีม <small>ค้นจาก Google · ไม่มีข้อมูล = แสดงว่าไม่มี (ไม่เดา) · '
            'ยังไม่มีผลต่อการฟันธง (Rule R42–R46 อยู่ในสถานะเงา)</small></div>')
    if tn.get("error"):
        return '<div class="fq">' + head + _card("ข้อมูลทีม", f'<div class="fq-mut">ค้นข้อมูลทีมไม่สำเร็จ: {e(tn["error"])}</div>', "fq-c12") + "</div>"
    INJ = {"out": ("ไม่ได้ลง", "bad"), "doubtful": ("ไม่แน่", "warn"), "suspended": ("โดนแบน", "bad")}
    ROLE = {"starter": "ตัวจริง", "rotation": "สำรอง", "unknown": "ไม่ทราบบทบาท"}
    cols = []
    for side in ("home", "away"):
        name = f[side]
        h = [f"<h4>{e(name)} <span class='fq-mut fq-small'>{'เจ้าบ้าน' if side == 'home' else 'ทีมเยือน'}</span></h4>"]
        x = (tn.get("xg") or {}).get(side) or {}
        if x.get("status", "none") == "none" or "xg" not in x:
            h.append(f'<div class="it">xG / xGA: ' + (_NA if x.get("status", "none") == "none" else '<span class="na">ไม่มีข้อมูลที่ยืนยันได้</span>') + "</div>")
        else:
            cls = "" if x["status"] == "ok" else "strike"
            gfga = (f' · ได้/เสียจริง <b>{x["gf"]:.2f}</b>/<b>{x["ga"]:.2f}</b>' if x.get("gf") is not None and x.get("ga") is not None else "")
            h.append(f'<div class="it"><span class="{cls}">xG <b>{x["xg"]:.2f}</b> · xGA <b>{x["xga"]:.2f}</b>{gfga}</span>'
                     f' <span class="fq-mut fq-small">({x.get("games") or "?"} นัดล่าสุด)</span>{_src(x.get("source"), x.get("as_of"))}{_flag(x["status"], x.get("why"))}</div>')
        lst = (tn.get("injuries") or {}).get(side) or []
        if not lst:
            h.append(f'<div class="it">ตัวเจ็บ/แบน: ' + ('<span class="fq-up">ไม่พบรายงาน</span>' if (tn.get("injuries_checked") or {}).get(side) else _NA) + "</div>")
        else:
            h.append('<div class="it">ตัวเจ็บ/แบน:</div>')
            for p in lst:
                lb, k = INJ.get(p.get("status"), ("?", "off"))
                star = "★ " if p.get("role") == "starter" else ""
                cls = "" if p.get("st") == "ok" else "strike"
                h.append(f'<div class="it" style="padding-left:10px"><span class="{cls}">{star}{e(p["player"])}</span> '
                         f'<span class="fq-mut fq-small">{e(p.get("position"))} · {ROLE.get(p.get("role"), "")}</span> {_chip(lb, k)}'
                         f'{_src(p.get("source"), p.get("as_of"))}{_flag(p.get("st"), p.get("why"))}</div>')
        r = (tn.get("rest") or {}).get(side) or {}
        if r.get("days") is None:
            h.append(f'<div class="it">วันพัก: {_NA}</div>')
        else:
            warn = " fq-warn" if r["days"] <= 3 else ""
            h.append(f'<div class="it">วันพัก: <b class="{warn}">{r["days"]} วัน</b> <span class="fq-mut fq-small">นัดก่อน {e(r["last_date"])}'
                     f'{" · " + e(r["competition"]) if r.get("competition") else ""}</span>{_src(r.get("source"))}{_flag(r["status"], None)}</div>')
        if ((tn.get("cup") or {}).get("rotation") or {}).get(side):
            h.append('<div class="it">' + _chip("มีข่าวหมุนเวียน/พักตัวหลัก", "warn") + "</div>")
        cols.append('<div>' + "".join(h) + "</div>")
    body = f'<div class="fq-tn">{"".join(cols)}</div>'
    extra = []
    c = tn.get("cup") or {}
    if c.get("is_cup"):
        extra.append(_chip("บอลถ้วย" + (f" เลก {c['leg']}" if c.get("leg") else "") + (f" · เลกแรก {c['first_leg_score']}" if c.get("first_leg_score") else ""), "acc"))
    lu = tn.get("lineups") or {}
    extra.append(_chip("ประกาศตัวจริงแล้ว", "ok") if lu.get("confirmed") else _chip("ตัวจริง: ยังไม่ประกาศ / ไม่มีข้อมูล", "off"))
    if tn.get("match_date"):
        extra.append(_chip(f"วันแข่ง {tn['match_date']}", "off"))
    body += f'<div class="fq-chips" style="margin-top:10px">{"".join(extra)}</div>'
    if c.get("evidence") and any((c.get("rotation") or {}).values()):
        body += f'<div class="fq-small fq-mut" style="margin-top:6px">หลักฐานบอลถ้วย: {e(c["evidence"])}{_src(c.get("source"))}</div>'
    if lu.get("confirmed") and lu.get("notes"):
        body += f'<div class="fq-small" style="margin-top:6px">ตัวจริง: {e(lu["notes"])}</div>'
    news = tn.get("other_news") or []
    if news:
        body += '<ul class="fq-ev">' + "".join(
            f'<li><span class="{"" if n.get("st") == "ok" else "strike"}">{e(n["text"])}</span> {_src(n.get("source"), n.get("as_of"))}{_flag(n.get("st"), n.get("why"))}</li>' for n in news) + "</ul>"
    miss = tn.get("missing") or []
    probs = tn.get("problems") or []
    if miss or probs:
        body += ('<div class="fq-small" style="margin-top:10px"><b class="fq-warn">ไม่มีข้อมูล / ไม่นำไปใช้</b><ul class="fq-ev">'
                 + "".join(f"<li>{e(x)}</li>" for x in probs + miss) + "</ul></div>")
    # สรุปค่าที่ Rule เงาใช้
    used = []
    if f.get("tn_xg_total") is not None:
        used.append(f"xG รวมคาดการณ์ {f['tn_xg_total']:.2f}" + (f" vs เรต {f['ou_c']:g}" if f.get("has_ou") else ""))
    if f.get("tn_fav_overperf") is not None:
        used.append(f"ทีมต่อ ผลจริง−xG {f['tn_fav_overperf']:+.2f}/นัด")
    if f.get("tn_fav_starters_out") is not None and f.get("tn_dog_starters_out") is not None:
        used.append(f"ตัวจริงหาย ต่อ {f['tn_fav_starters_out']} / รอง {f['tn_dog_starters_out']}")
    tag = _chip(f"แหล่งยืนยัน {len(tn.get('grounded') or [])} เว็บ", "ok" if tn.get("grounded") else "bad")
    if used:
        body += '<div class="fq-small fq-mut" style="margin-top:8px">ค่าที่ยืนยันแล้วและส่งให้ Rule เงา: ' + e(" · ".join(used)) + "</div>"
    srcs = [s_ for s_ in (tn.get("sources") or []) if s_.get("uri")][:8]
    if srcs:
        body += ('<div class="fq-small fq-mut fq-srcs" style="margin-top:6px">แหล่งที่ค้นเจอ: '
                 + " · ".join(f'<a href="{e(s_["uri"])}" target="_blank" rel="noopener">{e(s_.get("title") or "ลิงก์")}</a>' for s_ in srcs) + "</div>")
    return '<div class="fq">' + head + '<div class="fq-grid">' + _card("ข้อมูลทีม", body, "fq-c12", tag) + "</div></div>"


# ------------------------------------------------------------------ รายงาน HTML แบบไฟล์เดี่ยว (ดาวน์โหลด)
def report_document(res):
    f = res["f"]
    body = kpi_and_match(res) + analysis_body(res)
    warns = "".join(f"<li>{e(w)}</li>" for w in res.get("warns", []))
    extra = f'<div class="fq"><div class="fq-sec">คำเตือนจากการอ่านข้อมูล</div><ul class="fq-ev">{warns}</ul></div>' if warns else ""
    return ('<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(f["home"])} vs {e(f["away"])} · Football Quant</title><style>'
            "body{margin:0;padding:20px;background:#0b1220;color:#e6edf7;font-family:-apple-system,BlinkMacSystemFont,'Sukhumvit Set','Thonburi','Noto Sans Thai','Segoe UI',Tahoma,sans-serif}"
            ".wrap{max-width:1000px;margin:0 auto}h1{font-size:1.2rem;margin:0 0 4px}.sub{color:#8fa3c0;font-size:.8rem;margin-bottom:10px}"
            f"{CSS}</style></head><body><div class=\"wrap\"><h1>⚽ {e(f['home'])} vs {e(f['away'])}</h1>"
            f"<div class=\"sub\">Football Quant V5.9 · รายงานวิเคราะห์ · ไม่ใช่คำแนะนำทางการเงิน ผลลัพธ์ไม่รับประกัน</div>{body}{extra}</div></body></html>")


# ------------------------------------------------------------------ แดชบอร์ดสถิติ
def stats_dashboard(state, history):
    allset = [r for r in history if r.get("status") == "settled"]
    skipped = [r for r in allset if (r.get("pick") or {}).get("skip")]
    done = [r for r in allset if not (r.get("pick") or {}).get("skip")]      # ไม้ที่เล่นจริง
    pend = [r for r in history if r.get("status") == "pending"]
    if not done and not skipped:
        return ('<div class="fq"><div class="fq-empty">ยังไม่มีผลที่บันทึก · ใส่ผลจริงที่แท็บ “บันทึกผล” เพื่อดูสถิติและให้ระบบเรียนรู้'
                f'<br><span class="fq-small">รอผล {len(pend)} นัด</span></div></div>')
    w = sum(1 for r in done if r["pick_r"] > 0)
    l = sum(1 for r in done if r["pick_r"] < 0)
    p = len(done) - w - l
    pr = sum(r["pick_profit"] for r in done)
    wr = w / (w + l) if (w + l) else 0
    roi = pr / len(done) if done else 0.0
    kp = []
    kp.append(_card("อัตราชนะ (ไม่นับเจ๊า)", f'<div class="fq-donut" style="--p:{wr * 100:.0f};--c:{"#34d399" if wr >= .5 else "#f87171"}"><div>{wr:.0%}<small>{w}ช / {l}พ</small></div></div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("กำไรสุทธิ (หน่วย)", f'<div class="num {"fq-up" if pr >= 0 else "fq-down"}">{pr:+.2f}</div><div class="fq-small fq-mut">ROI {roi:+.1%} ต่อไม้</div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("บันทึกผลแล้ว", f'<div class="num">{len(done)}</div><div class="fq-small fq-mut">ชนะ {w} · เจ๊า {p} · แพ้ {l}</div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("รอผล", f'<div class="num">{len(pend)}</div><div class="fq-small fq-mut">สัญญาณที่ยังไม่จบเกม</div>', "fq-c3 fq-m6 fq-kpi"))
    out = ['<div class="fq"><div class="fq-grid">' + "".join(kp) + "</div>"]
    wb = [r for r in done if "pick_profit_best" in r]
    if wb:
        pm, pb = sum(r["pick_profit"] for r in wb), sum(r["pick_profit_best"] for r in wb)
        out.append(_card(f"Line shopping · {len(wb)} ไม้ที่มีข้อมูลราคาดีที่สุด",
                         f'<div class="fq-small">กำไรที่ราคามัธยฐาน <b class="{"fq-up" if pm >= 0 else "fq-down"}">{pm:+.2f}</b> · '
                         f'ถ้าวางที่เจ้าที่ให้ราคาดีที่สุด <b class="{"fq-up" if pb >= 0 else "fq-down"}">{pb:+.2f}</b> '
                         f'(ต่าง {pb - pm:+.2f} หน่วย = {(pb - pm) / len(wb):+.3f} ต่อไม้)</div>'
                         '<div class="fq-small fq-mut" style="margin-top:6px">สถิติหลักยังคิดที่ราคามัธยฐานเพื่อเทียบกับประวัติเดิมได้</div>'))
    if skipped:
        sw = sum(1 for r in skipped if r["pick_r"] > 0)
        sl = sum(1 for r in skipped if r["pick_r"] < 0)
        spr = sum(r["pick_profit"] for r in skipped)
        verdict = ("ไม้ที่ข้ามทำผลแย่กว่าไม้ที่เล่น → การข้ามช่วย" if spr / len(skipped) < roi else
                   "ไม้ที่ข้ามทำผลดีกว่าหรือพอ ๆ กับไม้ที่เล่น → การข้ามยังไม่ช่วย")
        out.append(_card(f"ไม้ที่ข้าม (ติดตามเป็นไม้เงา) · {len(skipped)} ไม้",
                         f'<div class="fq-small">ชนะ {sw} · แพ้ {sl} · อัตราชนะ <b>{(sw / (sw + sl)) if (sw + sl) else 0:.0%}</b> · '
                         f'กำไรถ้าเล่น <b class="{"fq-up" if spr >= 0 else "fq-down"}">{spr:+.2f}</b> (ROI {spr / len(skipped):+.1%}) · '
                         f'เทียบไม้ที่เล่น ROI {roi:+.1%}</div><div class="fq-small fq-mut" style="margin-top:6px">{e(verdict)} · '
                         'ต้องมีไม้ที่ข้ามหลายสิบไม้จึงจะสรุปได้ · สถิติด้านบนนับเฉพาะไม้ที่เล่น</div>'))
    if not done:
        out.append('</div>')
        return "".join(out)

    # กำไร/ขาดทุนต่อไม้
    last = done[-40:]
    mx = max([1.0] + [abs(r["pick_profit"]) for r in last])
    cum, run = [], 0.0
    for r in done:
        run += r["pick_profit"]
        cum.append(run)
    bars = "".join(
        f'<div title="{e(r["features"]["home"])} vs {e(r["features"]["away"])}"><span class="mid"></span>'
        f'<i class="{"p" if r["pick_profit"] >= 0 else "n"}" style="height:{max(abs(r["pick_profit"]) / mx * 50, 2):.0f}%"></i></div>' for r in last)
    out.append('<div class="fq-sec">ผลงานต่อไม้ <small>แท่งเขียว = กำไร · แดง = ขาดทุน · ล่าสุด 40 ไม้</small></div>')
    out.append(_card("กำไร/ขาดทุนต่อไม้", f'<div class="fq-pl">{bars}</div>'
                     f'<div class="fq-small fq-mut" style="margin-top:8px">กำไรสะสม: <b class="{"fq-up" if cum[-1] >= 0 else "fq-down"}">{cum[-1]:+.2f}</b> '
                     f'· สูงสุด {max(cum):+.2f} · ต่ำสุด {min(cum):+.2f}</div>', "fq-c12"))

    # แยกตามตลาด
    by = {}
    for r in done:
        k = r["pick"]["market"].split("_")[0]
        b = by.setdefault(k, [0, 0, 0, 0.0])
        b[0] += 1
        b[1] += r["pick_r"] > 0
        b[2] += r["pick_r"] < 0
        b[3] += r["pick_profit"]
    names = {"HDP": "แฮนดิแคป", "OU": "สูง/ต่ำ", "X12": "1X2"}
    rows = ['<div class="fq-row head" style="grid-template-columns:1.4fr 1fr 1fr 1fr"><span>ตลาด</span><span>ไม้</span><span>ชนะ/แพ้</span><span>กำไร</span></div>']
    for k, (n, ww, ll, pf) in by.items():
        rows.append(f'<div class="fq-row" style="grid-template-columns:1.4fr 1fr 1fr 1fr"><b>{names.get(k, k)}</b><span>{n}</span><span>{ww}/{ll}</span>'
                    f'<b class="{"fq-up" if pf >= 0 else "fq-down"}">{pf:+.2f}</b></div>')
    out.append('<div class="fq-sec">แยกตามตลาด</div>')
    out.append(_card("ผลงานแยกตลาด", "".join(rows), "fq-c12"))

    # น้ำหนัก Rule
    wts = state.get("weights") or {}
    rs = state.get("rule_stats") or {}
    items = []
    for k, v in wts.items():
        d0 = q.DEFAULT_WEIGHTS.get(k, 1.0)
        items.append((abs(v - d0), rs.get(k, {}).get("n", 0), k, v, d0))
    items.sort(key=lambda x: (-x[1], -x[0]))
    wrows = []
    for _, n, k, v, d0 in items[:14]:
        col = "#34d399" if v > d0 + 0.005 else "#f87171" if v < d0 - 0.005 else "#64748b"
        wrows.append(f'<div class="fq-w"><span class="nm">{e(k)} <small>{e(q.RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง"))}</small></span>'
                     f'<div class="tr"><i style="width:{min(v / 3 * 100, 100):.0f}%;background:{col}"></i><u style="left:{min(d0 / 3 * 100, 100):.0f}%"></u></div>'
                     f'<span class="fq-small" style="text-align:right">{v:.2f} <span class="fq-mut">({n})</span></span></div>')
    out.append('<div class="fq-sec">น้ำหนัก Rule ที่เรียนรู้ <small>แถบ = น้ำหนักปัจจุบัน · เส้นขาว = ค่าเริ่มต้น · วงเล็บ = จำนวนครั้งที่ใช้</small></div>')
    out.append(_card("น้ำหนัก Rule (เรียงตามจำนวนครั้งที่ใช้)", "".join(wrows), "fq-c12"))

    # ประวัติล่าสุด
    hist = []
    for r in list(reversed(history))[:10]:
        fe = r["features"]
        if r["status"] == "settled":
            kind = "ok" if r["pick_r"] > 0 else "bad" if r["pick_r"] < 0 else "warn"
            tail = _chip(f'{q.result_word(r["pick_r"])} {r["pick_profit"]:+.2f}', kind) + (" " + _chip("แก้ไขแล้ว", "warn") if r.get("edits") else "")
        else:
            tail = _chip("รอผล", "off")
        hist.append(f'<div class="fq-hist"><div>{e(fe["home"])} vs {e(fe["away"])}<small>{e(r["pick"]["label"])}</small></div><div>{tail}</div></div>')
    out.append('<div class="fq-sec">รายการล่าสุด</div>')
    out.append(_card("ประวัติ 10 รายการล่าสุด", "".join(hist), "fq-c12"))
    out.append("</div>")
    return "".join(out)


# ------------------------------------------------------------------ ไล่ระดับคะแนนสัญญาณ
def _pick_kind(r):
    f, mk = r["features"], r["pick"]["market"]
    if mk.startswith("HDP"):
        return "แฮนดิแคปทีมต่อ" if mk == f.get("fav_hdp") else "แฮนดิแคปทีมรอง"
    if mk.startswith("OU"):
        return "สูง (Over)" if mk == "OU_OVER" else "ต่ำ (Under)"
    return "1X2"


def _ladder_rows(recs, nb):
    recs = sorted(recs, key=lambda r: r["pick"]["strength"])
    n = len(recs)
    out = []
    for i in range(nb):
        seg = recs[i * n // nb:(i + 1) * n // nb]
        if not seg:
            continue
        w = sum(1 for r in seg if r["pick_r"] > 0)
        l = sum(1 for r in seg if r["pick_r"] < 0)
        out.append((seg[0]["pick"]["strength"], seg[-1]["pick"]["strength"], len(seg), w, l,
                    sum(r["pick_profit"] for r in seg) / len(seg)))
    return out


def _spearman(recs):
    pts = [(r["pick"]["strength"], 1 if r["pick_r"] > 0 else 0) for r in recs if r["pick_r"] != 0]
    n = len(pts)
    if n < 8:
        return None
    xs = [p[0] for p in pts]
    o = sorted(range(n), key=lambda i: xs[i])
    rx = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[o[j + 1]] == xs[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rx[o[k]] = (i + j) / 2
        i = j + 1
    ys = [p[1] for p in pts]
    mx, my = sum(rx) / n, sum(ys) / n
    sx = sum((a - mx) ** 2 for a in rx)
    sy = sum((b - my) ** 2 for b in ys)
    if sx <= 0 or sy <= 0:
        return None
    rho = sum((a - mx) * (b - my) for a, b in zip(rx, ys)) / (sx * sy) ** 0.5
    return rho, rho * ((n - 1) ** 0.5)          # ค่า z โดยประมาณ


def score_ladder(history, breakeven=0.525):
    """ตารางไล่ระดับคะแนนสัญญาณ: อัตราชนะตามช่วงคะแนน ทั้งรวมและแยกประเภทไม้ (ไม้ที่ฟันธงจริง)"""
    done = [r for r in history if r.get("status") == "settled" and r.get("pick") and "pick_r" in r]
    if len(done) < 10:
        return '<div class="fq"><div class="fq-empty">ต้องมีผลที่บันทึกแล้วอย่างน้อย 10 นัดจึงจะไล่ระดับคะแนนได้</div></div>'

    def table(recs, nb):
        rows = _ladder_rows(recs, nb)
        head = ('<div class="fq-row head" style="grid-template-columns:1.3fr .6fr 1.6fr .8fr"><span>ช่วงคะแนน</span>'
                '<span>ไม้</span><span>อัตราชนะ (เส้น = จุดคุ้มทุน)</span><span>ROI/ไม้</span></div>')
        body = ""
        for lo, hi, n, w, l, roi in rows:
            wr = w / (w + l) if (w + l) else 0
            col = "#34d399" if wr >= breakeven else "#f87171"
            body += (f'<div class="fq-row" style="grid-template-columns:1.3fr .6fr 1.6fr .8fr"><span>{lo:.2f} – {hi:.2f}</span><span>{n}</span>'
                     f'<div class="fq-w" style="grid-template-columns:1fr 46px;margin:0"><div class="tr"><i style="width:{wr * 100:.0f}%;background:{col}"></i>'
                     f'<u style="left:{breakeven * 100:.1f}%"></u></div><span class="fq-small" style="text-align:right">{wr:.0%}</span></div>'
                     f'<b class="{"fq-up" if roi >= 0 else "fq-down"}">{roi:+.2f}</b></div>')
        sp = _spearman(recs)
        if sp:
            rho, z = sp
            trend = ("คะแนนสูงชนะมากกว่า" if rho > 0 else "คะแนนสูงชนะน้อยกว่า") + (" (มีนัยสำคัญ)" if abs(z) >= 1.96 else " (ยังไม่มีนัยสำคัญ)")
            body += f'<div class="fq-small fq-mut" style="margin-top:8px">ความสัมพันธ์คะแนน↔ชนะ (Spearman) {rho:+.2f} · z ≈ {z:+.1f} · {trend}</div>'
        return head + body

    nb = 5 if len(done) >= 75 else 3
    out = ['<div class="fq">', '<div class="fq-sec">ไล่ระดับคะแนนสัญญาณ <small>ไม้ที่ฟันธงจริง · แบ่งกลุ่มเท่า ๆ กันตามคะแนน · '
           f'จุดคุ้มทุน ≈ {breakeven:.1%}</small></div>']
    out.append(_card(f"รวมทุกประเภท ({len(done)} ไม้)", table(done, nb)))
    groups = {}
    for r in done:
        groups.setdefault(_pick_kind(r), []).append(r)
    out.append('<div class="fq-grid">')
    for kind in ("แฮนดิแคปทีมต่อ", "แฮนดิแคปทีมรอง", "สูง (Over)", "ต่ำ (Under)", "1X2"):
        g = groups.get(kind) or []
        if len(g) >= 12:
            out.append(_card(f"{kind} ({len(g)} ไม้)", table(g, 3), "fq-c6"))
        elif g:
            out.append(_card(f"{kind} ({len(g)} ไม้)", '<div class="fq-mut fq-small">ข้อมูลยังน้อย (ต้องมีอย่างน้อย 12 ไม้)</div>', "fq-c6"))
    out.append('</div><div class="fq-small fq-mut" style="margin:4px 2px 0">หมายเหตุ: คะแนนของไม้ที่บันทึกต่างช่วงเวลา '
               'อาจอยู่คนละสเกลเพราะน้ำหนัก Rule ถูกปรับระหว่างทาง ใช้ดูแนวโน้ม ไม่ใช่ตัวตัดสินขาด</div></div>')
    return "".join(out)


# ------------------------------------------------------------------ สถานะ Rule ผู้สมัคร (เงา / ใช้งาน / ถอด)
def rule_lifecycle(state, params):
    life = state.get("lifecycle") or {}
    learned = {r["id"]: r for r in state.get("learned_rules", [])}
    rows = []
    for rid, e in life.items():
        dec = e["w"] + e["l"]
        rows.append((rid, e, dec, e["w"] / dec if dec else 0.0))
    for rid in learned:                          # Rule ที่ยังไม่เคยมีผลนอกกลุ่มตัวอย่าง
        if rid not in life:
            rows.append((rid, {"kind": "learned", "status": "shadow", "n": 0, "w": 0, "l": 0, "reason": "ยังไม่มีผลนอกกลุ่มตัวอย่าง"}, 0, 0.0))
    if not rows:
        return '<div class="fq"><div class="fq-empty">ยังไม่มี Rule ผู้สมัคร</div></div>'
    order = {"active": 0, "shadow": 1, "retired": 2}
    rows.sort(key=lambda x: (order.get(x[1]["status"], 3), -x[1]["n"]))
    cnt = {k: sum(1 for x in rows if x[1]["status"] == k) for k in order}
    lab = {"active": ("ใช้งาน", "ok"), "shadow": ("เงา (ระงับ)", "off"), "retired": ("ถอดแล้ว", "bad")}
    head = ('<div class="fq-row head" style="grid-template-columns:.7fr 2.4fr .9fr 1.4fr"><span>Rule</span><span>เงื่อนไข / เหตุผลสถานะ</span>'
            '<span>สถานะ</span><span>ผลนอกกลุ่มตัวอย่าง</span></div>')
    body = ""
    for rid, e, dec, wr in rows[:40]:
        if e["kind"] == "learned" and rid in learned:
            lr = learned[rid]
            desc = f'{" + ".join(lr["tags"])} → {q.ROLE_TH[lr["role"]]}'
        else:
            desc = q.RULE_NAMES.get(rid, rid)
        t, kd = lab.get(e["status"], (e["status"], "off"))
        need = max(0, params["judge_n"] - e["n"])
        prog = (f'{e["w"]}/{dec} = {wr:.0%}' if dec else "–") + (f' · อีก {need} ครั้งถึงตัดสิน' if e["status"] == "shadow" and need else "")
        body += (f'<div class="fq-row" style="grid-template-columns:.7fr 2.4fr .9fr 1.4fr"><b>{e_(rid)}</b>'
                 f'<div class="rn"><b>{e_(desc)}</b><small>{e_(e.get("reason", ""))}</small></div>'
                 f'<span>{_chip(t, kd)}</span><span class="fq-small">{prog}</span></div>')
    rules = (f'<div class="fq-small fq-mut" style="margin-bottom:8px">ทุก Rule ใหม่ (ที่ระบบสร้าง และ R28–R40 จากเอกสาร และ R42–R46 จากข้อมูลทีม) เริ่มเป็น <b>เงา</b>: '
             f'ติดตามผลเบื้องหลังโดยไม่มีผลต่อการฟันธง · <b>ปลดล็อค</b> เมื่อชนะ ≥ {params["unlock_wr"]:.0%} จาก ≥ {params["unlock_min_n"]} ครั้ง '
             f'(และสูงกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ) หรือครบ {params["judge_n"]} ครั้งแล้วผ่านเกณฑ์ · <b>ถอด</b> เมื่อครบ {params["judge_n"]} ครั้งไม่ผ่าน, '
             f'ต่ำกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ หรืออัตราชนะลดลงต่อเนื่อง 3 ช่วง</div>')
    tag = " ".join(_chip("{} {}".format(t_, cnt[k_]), c_) for k_, t_, c_ in (("active", "ใช้งาน", "ok"), ("shadow", "เงา", "off"), ("retired", "ถอด", "bad")))
    return '<div class="fq">' + _card("สถานะ Rule ผู้สมัคร", rules + head + body, "", tag) + '</div>'


def e_(x):
    return e(x)
