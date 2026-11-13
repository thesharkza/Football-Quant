# -*- coding: utf-8 -*-
"""ตัวสร้างหน้าเรื่องเล่า (visual story) ของแต่ละหน้าในแอป — ใช้ชิ้นส่วนจาก story.py"""
import football_quant_v58 as q
import story as S
from story import e, chip, chips, card, chapter, rv, bar, num, tipattr

GROUP_TH = {"flow": "การไหลของราคา", "price": "ราคาปัจจุบัน", "stats": "สถิติ", "context": "บริบท",
            "table": "ตารางคะแนน", "override": "กฎเหนือกว่า"}
PAIR = {"HDP_HOME": "HDP_AWAY", "HDP_AWAY": "HDP_HOME", "OU_OVER": "OU_UNDER", "OU_UNDER": "OU_OVER"}
CTX_LABELS = [("derby", "ดาร์บี้"), ("high_scoring_league", "ลีกประตูเยอะ"), ("high_draw_league", "ลีกเสมอสูง"),
              ("high_volatility", "ลีกผันผวนสูง"), ("cup_group_stage", "ถ้วยรอบแบ่งกลุ่ม"), ("knockout", "น็อคเอาต์"),
              ("continental_cup", "ถ้วยทวีป"), ("late_goal_tendency", "ยิงท้ายเกมสูง"),
              ("women_or_regional", "ฟุตบอลหญิง/ลีกรอง"), ("asian_cup", "ถ้วยเอเชีย")]


def mth(mk, f):
    return {"HDP_HOME": f"แฮนดิแคป {f['home']}", "HDP_AWAY": f"แฮนดิแคป {f['away']}", "OU_OVER": "สูง (Over)",
            "OU_UNDER": "ต่ำ (Under)", "X12_HOME": f"1X2 {f['home']} ชนะ", "X12_AWAY": f"1X2 {f['away']} ชนะ"}.get(mk, mk)


def base_of(mk):
    return mk.replace("X12_", "HDP_") if str(mk).startswith("X12_") else mk


def _fl(v):
    try:
        return q.fmt_line(v)
    except Exception:  # noqa
        return f"{v:g}"


def _wbar(w):
    return max(0.04, min(1.0, (w - 0.6) / 0.7))


def _delta(drop):
    """drop = ค่าน้ำลดลงเท่าไร (+ = ลด = เงินเข้า)"""
    if drop is None or abs(drop) < 0.005:
        return chip("นิ่ง", "off")
    return chip(f"{-drop:+.2f} {'เงินเข้า' if drop > 0 else 'เงินออก'}", "ok" if drop > 0 else "bad")


def _src_tip(p):
    return f"แหล่ง {p.get('source') or '-'} · {p.get('as_of') or '-'}"


def _seq_count(seq):
    s = str(seq or "").upper()
    return s.count("W"), s.count("D"), s.count("L")


# ============================================================================ หน้าผลวิเคราะห์
def analysis_story(res, nav=True):
    m, f, contribs, pick = res["m"], res["f"], res["contribs"] or [], res["pick"]
    chs = [("ch-market", "ตลาด", _ch_market(f)), ("ch-flow", "เงินไหล", _ch_flow(f)), ("ch-score", "สกอร์", _ch_score(f)),
           ("ch-rules", "Rule", _ch_rules(f, contribs, pick)), ("ch-form", "ฟอร์ม", _ch_form(m, f)),
           ("ch-team", "ข้อมูลทีม", _ch_team(m, f)), ("ch-check", "ตรวจสอบ", _ch_check(res)),
           ("ch-sum", "สรุป", _ch_summary(f, contribs, pick))]
    chs = [(cid, sh, h.replace("@N@", str(i))) for i, (cid, sh, h) in enumerate(chs, 1)]
    return S.story(chs, hero=_hero(m, f, pick), nav=nav)


def analysis_document(res):
    f = res["f"]
    return S.document(f"{f['home']} vs {f['away']}", analysis_story(res),
                      "Football Quant · รายงานวิเคราะห์ · ไม่ใช่คำแนะนำทางการเงิน ผลลัพธ์ไม่รับประกัน")


# ---------------------------------------------------------------------------- ฉากเปิด
def _hero(m, f, pick):
    fm = m.get("form") or {}
    rs = m.get("research") or {}

    def team(side):
        x = fm.get(side) or {}
        rk = f.get("rank_home") if side == "home" else f.get("rank_away")
        sub = ("เจ้าบ้าน" if side == "home" else "ทีมเยือน") + (f" · อันดับ {rk:g}" if isinstance(rk, (int, float)) else "")
        fav = chip("ทีมต่อ", "acc") if f["fav"] == side else chip("ทีมรอง", "off")
        return (f'<div class="s-team"><div class="s-chips" style="justify-content:center">{fav}</div>'
                f'<div class="nm">{e(f[side])}</div><div class="sub">{e(sub)}</div>{S.dots(x.get("seq"))}</div>')

    comp = rs.get("competition") or f.get("league") or ""
    skip = pick.get("skip")
    tier = pick.get("tier", "ต่ำ")
    lv = {"ต่ำ": 1, "กลาง": 2, "สูง": 3}.get(tier, 1)
    cls = "skip" if skip else ("low" if tier == "ต่ำ" else "")
    lvl = "".join(f'<i class="{"on" if i < lv else ""}" style="height:{14 + 12 * i}px;--dl:{.35 + .14 * i:.2f}s"></i>' for i in range(3))
    flags = []
    if pick.get("verify_fail"):
        flags.append(("ตรวจเหย้า/เยือนไม่ผ่าน", "bad"))
    if pick.get("move_only"):
        flags.append(("มาจากการไหลของราคาล้วน", "warn"))
    for v in pick.get("veto", []):
        flags.append(("แบน " + mth(v, f), "bad"))
    g = pick.get("gate")
    if g:
        rec_ = f" · ที่ผ่านมา {g['w']}-{g['l']} {g['profit']:+.2f}" if g["n"] else ""
        flags.append(({"pass": "🚦 ช่วงคะแนนผ่าน" + rec_, "fail": "🚦 ช่วงคะแนนไม่ผ่าน" + rec_,
                       "data": f"🚦 ช่วงคะแนนข้อมูลยังไม่พอ ({g['n']}/{g['min_n']} ไม้)"}[g["status"]],
                      {"pass": "ok", "fail": "bad", "data": "off"}[g["status"]]))
    sup, opp = pick.get("support"), pick.get("oppose")
    stats = (f'<div class="s-statline"><div class="v">{num(pick["strength"], 2)}</div><div class="t">คะแนนสัญญาณ</div></div>')
    if sup is not None and opp is not None:
        stats += (f'<div class="s-statline"{tipattr("คะแนนรวมของฝั่งที่เลือก เทียบกับฝั่งตรงข้ามในตลาดเดียวกัน (หลังตัดฝั่งที่ถูกแบน)")}>'
                  f'<div class="v">{sup:.2f} : {opp:.2f}</div><div class="t">หนุน : ค้าน</div></div>')
    best = ""
    b = pick.get("best")
    if b and not skip:
        best = (f'<div class="best">💰 ราคาดีที่สุด <b>{e(b["book"])} @{b["price"]:.2f}</b> · ดีกว่าราคามัธยฐาน +{b["gain"]:.2f} · '
                f'จุดคุ้มทุน {b["breakeven"]:.1%} (จาก {b["breakeven_median"]:.1%})</div>')
    extra = ""
    if skip:
        extra = '<ul class="s-list" style="color:inherit;opacity:.9">' + "".join(f"<li>{e(x)}</li>" for x in pick.get("skip_reasons", [])) + "</ul>"
    ru = [r for r in (pick.get("runner_up") or []) if r[1] > 0.05][:1]
    if ru:
        extra += f'<div class="s-sm" style="margin-top:8px;opacity:.8">ทางเลือกรอง: {e(mth(ru[0][0], f))} ({ru[0][1]:.2f})</div>'
    sm = f.get("score_model")
    if sm:
        extra += (f'<div class="sc">🔢 ประตูคาดหมาย {sm["lh"]:.2f} – {sm["la"]:.2f} · สกอร์ที่น่าจะเป็น '
                  + " · ".join(f"{h}-{a} ({p:.0%})" for h, a, p in sm["top"][:3]) + "</div>")
    pk = (f'<div class="s-pick {cls} s-rv" style="--dl:.25s"><div class="k">{"⏭ ข้ามไม้นี้ · ติดตามเป็นไม้เงา" if skip else "สัญญาณฟันธงเดี่ยว · ราคาปัจจุบัน"}</div>'
          f'<div class="lb">{e(pick["label"])}</div>'
          f'<div class="row"><div style="display:flex;align-items:flex-end;gap:10px"><div class="s-lvl">{lvl}</div>'
          f'<div class="s-statline"><div class="v">{e(tier)}</div><div class="t">ระดับสัญญาณ</div></div></div>{stats}</div>'
          f'{("<div class=s-chips style=margin-top:12px>" + "".join(chip(t, k) for t, k in flags) + "</div>") if flags else ""}{best}{extra}</div>')
    return (f'<div class="s-hero s-rv"><div class="comp">{e(comp)}</div><div class="s-vs">{team("home")}<div class="s-vsx">VS</div>{team("away")}</div>'
            f'{pk}<div class="s-xs s-mut" style="text-align:center;margin-top:10px">ระดับสัญญาณจัดจากคะแนนของ Rule (ต่ำ &lt; 1.2 ≤ กลาง &lt; 2.5 ≤ สูง) '
            f'ไม่ใช่โอกาสชนะ · เลื่อนลงเพื่อดูว่าระบบคิดอย่างไรทีละขั้น</div></div>')


# ---------------------------------------------------------------------------- บท: สกอร์ที่คาด
def _ch_score(f):
    sm = f.get("score_model")
    kick, title = "บทที่ @N@ · สกอร์ที่คาด", "สกอร์ที่น่าจะเป็นจากราคาตลาด"
    if not sm:
        return chapter("ch-score", "@N@", kick, title, "ข้อมูลราคาไม่พอคำนวณสกอร์", "")
    br = q.best_by_result(sm)
    t1 = sm["top"][0]
    lead = (f'ราคาตลาดตอนนี้เทียบเท่ากับ <b>{e(f["home"])}</b> ยิงเฉลี่ย <b>{sm["lh"]:.2f}</b> ประตู และ <b>{e(f["away"])}</b> <b>{sm["la"]:.2f}</b> ประตู '
            f'(รวม {sm["exp_total"]:.2f}) · สกอร์อันดับ 1 คือ <b>{t1[0]}-{t1[1]}</b> แต่มีโอกาสเพียง <b>{t1[2]:.0%}</b> '
            f'จึงควรดูเป็น "รูปเกม" มากกว่าทายสกอร์ตรง ๆ')
    # สกอร์แยกตามผล
    pr = sm["p"]
    sc3 = (f'<div class="s-sc3">'
           f'<div class="s-rv"><div class="t">ถ้า {e(f["home"])} ชนะ ({pr[0]:.0%})</div><div class="v">{br["home"][0]}-{br["home"][1]}</div><div class="t">{br["home"][2]:.1%}</div></div>'
           f'<div class="s-rv" style="--dl:.1s"><div class="t">ถ้าเสมอ ({pr[1]:.0%})</div><div class="v">{br["draw"][0]}-{br["draw"][1]}</div><div class="t">{br["draw"][2]:.1%}</div></div>'
           f'<div class="s-rv" style="--dl:.2s"><div class="t">ถ้า {e(f["away"])} ชนะ ({pr[2]:.0%})</div><div class="v">{br["away"][0]}-{br["away"][1]}</div><div class="t">{br["away"][2]:.1%}</div></div></div>')
    # heatmap
    g = sm["grid"]
    mx = max(max(r) for r in g) or 1
    tops = {(t[0], t[1]) for t in sm["top"][:3]}
    cells = '<div class="ax"></div>' + "".join(f'<div class="ax">{a}</div>' for a in range(6))
    for h in range(6):
        cells += f'<div class="ax">{h}</div>'
        for a in range(6):
            v = g[h][a]
            al = 0.05 + 0.85 * (v / mx)
            fg = "#04201d" if al > 0.55 else "#cfe9e5"
            tip = f"{f['home']} {h}-{a} {f['away']}\nโอกาส {v:.1%}"
            cells += (f'<div class="c s-pop{" top" if (h, a) in tops else ""}" style="--a:{al:.2f};--fg:{fg};--dl:{.02 * (h + a):.2f}s"{tipattr(tip)}>'
                      f'{h}-{a}<small>{v:.0%}</small></div>')
    heat = (f'<div class="s-xs s-mut" style="margin-bottom:6px">แถวตั้ง = ประตู {e(f["home"])} · แถวนอน = ประตู {e(f["away"])} · กรอบเหลือง = 3 อันดับแรก</div>'
            f'<div class="s-heat">{cells}</div>'
            f'<div class="s-note">สกอร์นอกตาราง (ทีมใดทีมหนึ่งยิง 6+) รวม {sm["outside_5"]:.1%}</div>')
    rows = "".join(f'<div class="s-brow s-rv" style="--dl:{.06 * i:.2f}s"><span class="l"><b>{h}-{a}</b></span>{bar(p_ / sm["top"][0][2], "t" if i == 0 else "i", dl=.06 * i)}'
                   f'<span class="n">{p_:.1%}</span></div>' for i, (h, a, p_) in enumerate(sm["top"]))
    mk = sm["market_p"]
    fit = (f'<div class="s-note">ตรวจความเข้ากันกับตลาด: แบบจำลอง {pr[0]:.0%}/{pr[1]:.0%}/{pr[2]:.0%} เทียบราคา 1X2 {mk[0]:.0%}/{mk[1]:.0%}/{mk[2]:.0%} '
           f'(คลาด {sm["rmse"]:.1%}) · ใช้ข้อมูล {sm["inputs"]} ตลาด · แบบจำลอง Dixon-Coles</div>')
    body = (card("สกอร์ที่น่าจะเป็นที่สุดแยกตามผล", sc3) + '<div class="s-grid" style="margin-top:12px">'
            + card("แผนที่ความน่าจะเป็นของสกอร์", heat, dl=.05) + card("6 อันดับแรก", rows + fit, dl=.1) + "</div>"
            + '<div class="s-note s-rv">สกอร์คำนวณจากราคาตลาดเท่านั้น (ไม่ได้ใช้ Rule) และไม่มีผลต่อการฟันธง · จากข้อมูลจริงของระบบ '
              'สกอร์อันดับ 1 ถูกประมาณ 1 ใน 8 นัด และอยู่ใน 3 อันดับแรกประมาณ 1 ใน 3 นัด</div>')
    return chapter("ch-score", "@N@", kick, title, lead, body)


def gate_chapter(history, params, n):
    P = {**q.DEFAULT_PARAMS, **(params or {})}
    edges = P.get("gate_edges") or q.DEFAULT_PARAMS["gate_edges"]
    tab = q.gate_table(history, P)
    kick, title = f"บทที่ {n} · ตัวกรองช่วงคะแนน", "ช่วงไหนลงทุนได้ ช่วงไหนงด"
    cnt = {"pass": 0, "fail": 0, "data": 0}
    head = '<div class="ax"></div>' + "".join(f'<div class="ax" style="font-size:.66rem">{e(q.gate_label(i, edges))}</div>' for i in range(len(edges) + 1))
    cells = ""
    for k in ("fav", "dog", "over", "under"):
        cells += f'<div class="ax" style="font-size:.66rem;text-align:left;place-items:center start">{e(q.GATE_KIND_TH[k])}</div>'
        for i in range(len(edges) + 1):
            tt = tab.get((k, i))
            stt = q.gate_status(tt, P)
            cnt[stt] += 1 if tt else 0
            if not tt:
                cells += '<div class="c" style="--a:.03;opacity:.45">–</div>'
                continue
            col = {"pass": "rgba(52,211,153,.30)", "fail": "rgba(248,113,113,.32)", "data": "rgba(148,163,184,.12)"}[stt]
            wr = f'{tt["wr"]:.0%}' if tt["wr"] is not None else "–"
            tip = (f'{q.GATE_KIND_TH[k]} · คะแนน {q.gate_label(i, edges)}\n{tt["n"]} ไม้ · ชนะ {tt["w"]} แพ้ {tt["l"]} ({wr})\nกำไร {tt["profit"]:+.2f}\n'
                   + {"pass": "ผ่าน → ลงทุนได้", "fail": "ไม่ผ่าน → งดลงทุน", "data": f"ข้อมูลยังไม่ถึง {P['gate_min_n']} ไม้ → ลงทุนตามปกติ"}[stt])
            cells += (f'<div class="c s-pop" style="background:{col};color:#e6edf7;aspect-ratio:auto;padding:6px 2px"{tipattr(tip)}>'
                      f'{wr}<small>{tt["profit"]:+.1f} · {tt["n"]}</small></div>')
    grid = (f'<div class="s-heat" style="grid-template-columns:96px repeat({len(edges) + 1}, minmax(0,1fr))">{head}{cells}</div>'
            '<div class="s-note">แต่ละช่อง: อัตราชนะ · กำไร · จำนวนไม้ · เขียว = ผ่าน (ลงทุนได้) · แดง = ไม่ผ่าน (งดลงทุน) · เทา = ข้อมูลยังไม่พอ (ลงทุนตามปกติ) · แตะเพื่อดูรายละเอียด</div>')
    sus = [r for r in history if r.get("status") == "settled" and (r.get("pick") or {}).get("gate_suspended")]
    if sus:
        w = sum(r["pick_r"] > 0 for r in sus); l = sum(r["pick_r"] < 0 for r in sus); pf = sum(r["pick_profit"] for r in sus)
        track = (f'<div class="s-kv"><span>ไม้ที่ตัวกรองงดไปแล้ว (ผลจริง)</span><b>{len(sus)} ไม้ · {w}-{l}</b></div>'
                 f'<div class="s-kv"><span>ถ้าเล่นไม้เหล่านั้นจะได้</span><b class="{"s-up" if pf >= 0 else "s-down"}">{pf:+.2f}</b></div>'
                 f'<div class="s-note">{"ติดลบ = ตัวกรองช่วยกันเงินไว้ได้" if pf < 0 else "เป็นบวก = ตัวกรองทำให้พลาดกำไร"} · ต้องสะสมหลายสิบไม้จึงจะสรุปได้</div>')
    else:
        track = '<div class="s-mut s-sm">ยังไม่มีไม้ที่ถูกตัวกรองงดและบันทึกผลแล้ว</div>'
    onoff = "เปิดอยู่" if P.get("gate_enabled", True) else "ปิดอยู่ (แสดงผลอย่างเดียว ไม่งด)"
    lead = (f'ตัวกรอง<b>{onoff}</b> · ช่วงที่ผ่าน <b>{cnt["pass"]}</b> · ไม่ผ่าน <b>{cnt["fail"]}</b> · ข้อมูลยังไม่พอ <b>{cnt["data"]}</b> — '
            f'งดลงทุนเมื่อช่วงนั้นมีอย่างน้อย {P["gate_min_n"]} ไม้ แล้วชนะต่ำกว่า {P["breakeven_wr"]:.1%} หรือขาดทุน')
    body = card("ประเภทไม้ × ช่วงคะแนน", grid) + card("ติดตามผลของตัวกรอง", track, dl=.1).replace('class="s-card s-rv', 'style="margin-top:12px" class="s-card s-rv', 1)
    return chapter("st-gate", n, kick, title, lead, body)


def score_accuracy_chapter(history, n):
    a = q.score_accuracy(history)
    kick, title = f"บทที่ {n} · ทายสกอร์แม่นแค่ไหน", "สกอร์ที่คาดเทียบผลจริง"
    if not a.get("n"):
        return chapter("st-score", n, kick, title, "ยังไม่มีผลที่บันทึก", "")
    N = a["n"]
    lead = (f'จาก <b>{N}</b> นัดที่บันทึกผล สกอร์อันดับ 1 ถูก <b>{a["top1"]}</b> นัด ({a["top1"] / N:.1%}) '
            f'ใกล้กับที่แบบจำลองคาดไว้ ({a["exp_top1"]:.1%}) · อยู่ใน 3 อันดับแรก <b>{a["top3"]}</b> นัด ({a["top3"] / N:.1%})')
    cs = a["common_score"]
    k = (f'<div class="s-kpis">'
         f'<div class="s-kpi s-rv"><div class="t">อันดับ 1 ถูก</div><div class="v">{num(a["top1"] / N * 100, 1, suf="%")}</div><div class="d">{a["top1"]}/{N} · แบบจำลองคาด {a["exp_top1"]:.1%}</div></div>'
         f'<div class="s-kpi s-rv" style="--dl:.08s"><div class="t">อยู่ใน 3 อันดับแรก</div><div class="v">{num(a["top3"] / N * 100, 1, suf="%")}</div><div class="d">{a["top3"]}/{N}</div></div>'
         f'<div class="s-kpi s-rv" style="--dl:.16s"><div class="t">ประตูรวมคลาดเฉลี่ย</div><div class="v">{num(a["mae_total"], 2)}</div><div class="d">ลูกต่อนัด</div></div></div>')
    pf = ", ".join(f"{s_[0]}-{s_[1]} ({c} นัด)" for s_, c in a["pred_freq"][:3])
    notes = [f"สกอร์ที่ออกบ่อยที่สุดในข้อมูลคือ {cs[0]}-{cs[1]} ({a['common_n']} นัด) — ถ้าทาย {cs[0]}-{cs[1]} ทุกนัดจะถูก {a['common_n'] / N:.1%}",
             f"แบบจำลองเลือกสกอร์อันดับ 1 เป็น: {pf} — สกอร์เสมอ 1-1 มักเป็นอันดับ 1 แม้มีทีมเหนือกว่า เพราะโอกาสชนะกระจายไปหลายสกอร์",
             "ค่าที่มีประโยชน์จริงคือการกระจายความน่าจะเป็นทั้งตาราง (ประตูคาดหมาย, สกอร์แยกตามผล) มากกว่าสกอร์อันดับ 1 เพียงตัวเดียว"]
    if a.get("logloss") is not None:
        notes.append(f"คะแนนความแม่นของการกระจาย (log-loss) {a['logloss']:.2f} — ยิ่งต่ำยิ่งดี")
    body = k + card("อ่านผลอย่างไร", '<ul class="s-list">' + "".join(f"<li>{e(x)}</li>" for x in notes) + "</ul>", dl=.1).replace(
        'class="s-card s-rv', 'style="margin-top:12px" class="s-card s-rv', 1)
    return chapter("st-score", n, kick, title, lead, body)


# ---------------------------------------------------------------------------- บท 1: ตลาดคาดอะไร
def _ch_market(f):
    xo, xc = q.implied(f["x12_open"]), q.implied(f["x12_cur"])
    o, c = f["x12_open"], f["x12_cur"]
    fi, di = (0, 2) if f["fav"] == "home" else (2, 0)
    d = (xc[fi] - xo[fi]) * 100
    lead = (f'ตลาดมอง <b>{e(f["fav_name"])}</b> เป็นต่อ ให้โอกาสชนะโดยนัย <b>{xc[fi]:.0%}</b> '
            + (f'({"เพิ่มขึ้น" if d > 0 else "ลดลง"} {abs(d):.1f} จุดจากราคาเปิด)' if abs(d) >= 0.5 else "(ใกล้เคียงราคาเปิด)")
            + f' · เสมอ {xc[1]:.0%} · {e(f["dog_name"])} {xc[di]:.0%}')
    rows = ""
    for i, (lab, col) in enumerate(((f["home"], "t"), ("เสมอ", "n"), (f["away"], "i"))):
        dp = (xc[i] - xo[i]) * 100
        cls = "s-up" if dp > 0.3 else "s-down" if dp < -0.3 else "s-mut"
        tip = f"{lab}\nราคาเปิด {o[i]:.2f} → ปัจจุบัน {c[i]:.2f}\nโอกาสโดยนัย {xo[i]:.1%} → {xc[i]:.1%}"
        rows += (f'<div class="s-prob"{tipattr(tip)}><span class="s-sm" style="overflow-wrap:anywhere">{e(lab)}</span>'
                 f'<div class="stk">{bar(xo[i], "o", "thin", dl=.1 * i)}{bar(xc[i], col, "fat", dl=.1 * i + .1)}</div>'
                 f'<span class="v">{xc[i]:.0%}<div class="s-xs {cls}">{dp:+.1f}pp</div></span></div>')
    odds = "".join(f'<div class="s-kv"><span>{e(lab)}</span><b>{c[i]:.2f} <span class="s-mut s-xs">(เปิด {o[i]:.2f})</span></b></div>'
                   for i, lab in enumerate((f["home"], "เสมอ", f["away"])))
    body = ('<div class="s-grid">' + card("โอกาสโดยนัยจากราคา 1X2", rows + '<div class="s-note">แถบบาง = ราคาเปิด · แถบหนา = ราคาปัจจุบัน · แตะแถบเพื่อดูราคา</div>')
            + card("ราคา 1X2 ปัจจุบัน", odds + f'<div class="s-note">ค่าความขัดแย้งระหว่างตลาด {f.get("conflict", 0):.0%} · '
                   f'พูล 1X2 ทีมต่อ {f.get("x12_pp", 0):+.1f}pp</div>', dl=.1) + "</div>")
    return chapter("ch-market", "@N@", "บทที่ @N@ · ตลาดคาดอะไร", "ราคาบอกว่าใครเหนือกว่า", lead, body)


# ---------------------------------------------------------------------------- บท 2: เงินไหลไปทางไหน
def _ch_flow(f):
    sh = f.get("hdp_shift_fav", 0.0)
    parts = []
    if abs(sh) >= 0.01:
        parts.append(f'เรตแฮนดิแคปขยับจาก <b>{e(_fl(f["line_o"]))}</b> เป็น <b>{e(_fl(f["line_c"]))}</b> — ทีมต่อ<b>{"แรงขึ้น" if sh > 0 else "อ่อนลง"}</b> {abs(sh):g} ลูก')
    else:
        parts.append(f'เรตแฮนดิแคปนิ่งที่ <b>{e(_fl(f["line_c"]))}</b> ตั้งแต่เปิดราคา')
    fd, dd = f.get("fav_drop", 0.0), f.get("dog_drop", 0.0)
    side = max(((f["fav_name"], fd), (f["dog_name"], dd)), key=lambda x: x[1])
    if side[1] >= 0.03:
        parts.append(f'ค่าน้ำฝั่ง <b>{e(side[0])}</b> ลดลง {side[1]:.2f} ซึ่งมักแปลว่ามีเงินเข้าฝั่งนี้')
    else:
        parts.append("ค่าน้ำแทบไม่ขยับ ยังไม่เห็นเงินไหลชัดเจน")
    if f.get("has_ou"):
        ov, un = f.get("over_drop", 0.0), f.get("under_drop", 0.0)
        ou = f'สูง/ต่ำ {f["ou_o"]:g} → <b>{f["ou_c"]:g}</b>'
        if max(ov, un) >= 0.03:
            ou += f' และน้ำฝั่ง<b>{"สูง" if ov > un else "ต่ำ"}</b>ลด {max(ov, un):.2f}'
        parts.append(ou)
    lead = " · ".join(parts)

    def linebox(o, c, delta, fmt):
        col = "#34d399" if delta > 0 else "#f87171" if delta < 0 else "#64748b"
        return (f'<div class="s-line"><div class="b"><div class="t">เปิด</div><div class="v">{e(fmt(o))}</div></div>'
                f'<div class="s-flow" style="--fc:{col}"></div><div class="b cur"><div class="t">ปัจจุบัน</div><div class="v">{e(fmt(c))}</div></div>'
                f'<span class="s-sm" style="color:{col}">{"▲" if delta > 0 else "▼" if delta < 0 else "■"} {delta:+g}</span></div>')

    def wrow(lab, w, drop, col, dl):
        return (f'<div class="s-brow"{tipattr(f"{lab}: ค่าน้ำปัจจุบัน {w:.2f}" + (f" · เปลี่ยน {-drop:+.2f}" if drop else ""))}>'
                f'<span class="l">{e(lab)}</span>{bar(_wbar(w), col, dl=dl)}<span class="n">{w:.2f} {_delta(drop)}</span></div>')

    hb = linebox(f["line_o"], f["line_c"], sh, _fl)
    hb += wrow(f'{f["fav_name"]} (ต่อ)', f["fav_water_c"], fd, "t", .1) + wrow(f'{f["dog_name"]} (รอง)', f["dog_water_c"], dd, "i", .2)
    if abs(sh) >= 0.01:
        hb += (f'<div class="s-note">เรตเปลี่ยน ค่าน้ำจึงขยับตามธรรมชาติ · ค่าที่ปรับตามเรตแล้ว: ทีมต่อ {-f.get("fav_drop_adj", 0):+.2f} · '
               f'ทีมรอง {-f.get("dog_drop_adj", 0):+.2f}</div>')
    hb += '<div class="s-note">เรตแสดงในมุมเจ้าบ้าน (ติดลบ = เจ้าบ้านต่อ)</div>'
    cards = card("แฮนดิแคป", hb, chip(f"ทีมต่อ {f['fav_name']}", "acc"))
    if f.get("has_ou"):
        ob = linebox(f["ou_o"], f["ou_c"], f.get("ou_shift", 0.0), lambda v: f"{v:g}")
        ob += wrow("สูง (Over)", f["over_water_c"], f.get("over_drop", 0.0), "t", .1) + wrow("ต่ำ (Under)", f["under_water_c"], f.get("under_drop", 0.0), "i", .2)
        for lab, v in (("ประตูรวมคาดจากสถิติ", f.get("exp_total")), ("ประตูรวมคาดจาก xG (ข้อมูลทีม)", f.get("tn_xg_total"))):
            if v is not None:
                span = max(f["ou_c"] * 2, v + 0.5, 4.0)
                tp = f"{lab} {v:.2f} เทียบเรต {f['ou_c']:g} (เส้นขาว)"
                ob += (f'<div class="s-brow"{tipattr(tp)}>'
                       f'<span class="l s-sm">{e(lab)}</span>{bar(v / span, "y", mark=f["ou_c"] / span, dl=.3)}'
                       f'<span class="n">{v:.2f}</span></div>')
        cards += card("สูง / ต่ำ", ob, dl=.12)
    else:
        cards += card("สูง / ต่ำ", '<div class="s-mut">ไม่มีข้อมูลราคาสูง/ต่ำ</div>', dl=.12)
    return chapter("ch-flow", "@N@", "บทที่ @N@ · เงินไหลไปทางไหน", "ราคาเปิด → ราคาปัจจุบัน", lead, f'<div class="s-grid">{cards}</div>')


# ---------------------------------------------------------------------------- บท 3: Rule ลงคะแนน
def _rule_row(c, f, kind, dl):
    rid = c["rule"]
    w = c["eff"] / c["raw"] if c.get("raw") else 1.0
    grp = GROUP_TH.get(c.get("group") or (q.rule_group(rid) if hasattr(q, "rule_group") else ""), "")
    tip = f"{q.RULE_NAMES.get(rid, 'Rule ที่ระบบเรียนรู้เอง')} ({rid})\nทางเลือก: {mth(c['market'], f)}\nคะแนนดิบ {c.get('raw', 0):.2f} × น้ำหนัก {w:.2f} = {c['eff']:.2f}"
    if c.get("counted") is False:
        tip += "\n(ไม่ถูกนับซ้ำในโหมดนับกลุ่มละครั้ง)"
    return (f'<div class="s-rule {kind} s-rv" style="--dl:{dl:.2f}s"{tipattr(tip)}><span class="edge"></span>'
            f'<div><div class="nm">{e(q.RULE_NAMES.get(rid, "Rule ที่ระบบเรียนรู้เอง"))}<small>{e(rid)}</small></div>'
            f'<div class="nt">{e(c.get("note", ""))}</div><div class="s-chips" style="margin-top:5px">{chip(mth(c["market"], f), "")}'
            f'{chip(grp, "warn" if rid in q.MOVEMENT_RULES else "off") if grp else ""}</div></div>'
            f'<div class="sc"><b>{c["eff"]:+.2f}</b>{bar(min(c["eff"] / 3.0, 1.0), "t" if kind == "sup" else "r" if kind == "opp" else "n", "thin", dl=dl)}'
            f'<div class="s-xs s-mut">×{w:.2f}</div></div></div>')


def _rule_list(rows, f, kind, key, top=6):
    if not rows:
        return '<div class="s-empty">ไม่มี</div>'
    rows = sorted(rows, key=lambda c: -c["eff"])
    head = "".join(_rule_row(c, f, kind, .05 * i) for i, c in enumerate(rows[:top]))
    if len(rows) <= top:
        return head
    rest = "".join(_rule_row(c, f, kind, 0) for c in rows[top:])
    return (head + f'<div class="s-more" data-pane="{key}">{rest}</div>'
            f'<button class="s-btn" data-tg="{key}" data-alt="ย่อ">ดูอีก {len(rows) - top} ข้อ</button>')


def _ch_rules(f, contribs, pick):
    tot = {}
    for c in contribs:
        if c.get("counted", True):
            tot[c["market"]] = tot.get(c["market"], 0.0) + c["eff"]
    veto = set(pick.get("veto", []))
    bm = base_of(pick["market"])
    om = PAIR.get(bm)
    sup = pick.get("support", tot.get(bm, 0.0))
    opp = pick.get("oppose", tot.get(om, 0.0) if om else 0.0)
    if opp <= 1e-9:
        tone = "ไม่มีสัญญาณค้านในตลาดเดียวกันเลย"
    elif sup > 0 and opp / sup >= 0.6:
        tone = "สองฝั่งสูสี สัญญาณขัดกันค่อนข้างมาก"
    else:
        tone = "ฝั่งที่เลือกนำชัดเจน"
    lead = (f'มี Rule ทำงาน <b>{len(contribs)}</b> ข้อ · ฝั่งที่เลือก (<b>{e(mth(bm, f))}</b>) ได้ <b>{sup:.2f}</b> คะแนน '
            f'เทียบฝั่งตรงข้าม <b>{opp:.2f}</b> — {tone}')
    mx = max([1.0] + [v for k, v in tot.items() if k not in veto])

    def tug(ll, lr, kl, kr, dl):
        vl, vr = (0.0 if kl in veto else tot.get(kl, 0.0)), (0.0 if kr in veto else tot.get(kr, 0.0))
        wl, wr = pick["market"] in (kl, kl.replace("HDP_", "X12_")), pick["market"] in (kr, kr.replace("HDP_", "X12_"))
        tl = '<span class="tg">แบน</span>' if kl in veto else ""
        tr = '<span class="tg">แบน</span>' if kr in veto else ""
        return (f'<div class="s-tug s-rv" style="--dl:{dl:.2f}s"><div class="sd{" win" if wl else ""}"><span class="nm">{e(ll)}</span><b>{vl:.2f}{" ★" if wl else ""}</b>{tl}</div>'
                f'<div class="half l{" win" if wl else ""}{" ban" if kl in veto else ""}"><i class="s-fill" style="--w:{vl / mx * 100:.0f}%;--dl:{dl:.2f}s"></i></div>'
                f'<div class="half r{" win" if wr else ""}{" ban" if kr in veto else ""}"><i class="s-fill" style="--w:{vr / mx * 100:.0f}%;--dl:{dl:.2f}s"></i></div>'
                f'<div class="sd r{" win" if wr else ""}"><span class="nm">{e(lr)}</span><b>{"★ " if wr else ""}{vr:.2f}</b>{tr}</div></div>')

    tb = '<div class="s-xs s-mut" style="letter-spacing:.06em">แฮนดิแคป</div>' + tug(f["home"], f["away"], "HDP_HOME", "HDP_AWAY", .05)
    if f.get("has_ou"):
        tb += '<div class="s-xs s-mut" style="letter-spacing:.06em;margin-top:6px">สูง / ต่ำ</div>' + tug("สูง (Over)", "ต่ำ (Under)", "OU_OVER", "OU_UNDER", .15)
    if veto:
        tb += '<div class="s-chips" style="margin-top:8px">' + "".join(chip("แบน: " + mth(v, f), "bad") for v in sorted(veto)) + "</div>"
    tb += '<div class="s-note">ดึงเชือก: ยิ่งแถบยาวยิ่งได้คะแนนมาก · ★ = ทางเลือกที่ฟันธง · ฝั่งที่ถูกแบนห้ามนำคะแนนไปหักล้างอีกฝั่ง</div>'
    sup_r = [c for c in contribs if c["market"] == bm]
    opp_r = [c for c in contribs if om and c["market"] == om]
    oth_r = [c for c in contribs if c["market"] not in (bm, om)]
    tabs = (f'<div class="s-tabs"><div class="s-tabbar"><button class="on" data-tab="sup">หนุนไม้นี้ ({len(sup_r)})</button>'
            f'<button data-tab="opp">ค้าน ({len(opp_r)})</button><button data-tab="oth">ตลาดอื่น ({len(oth_r)})</button></div>'
            f'<div data-tabpane="sup" class="on">{_rule_list(sup_r, f, "sup", "m-sup")}</div>'
            f'<div data-tabpane="opp">{_rule_list(opp_r, f, "opp", "m-opp")}</div>'
            f'<div data-tabpane="oth">{_rule_list(oth_r, f, "", "m-oth")}</div></div>')
    sh = pick.get("shadow") or []
    if sh:
        items = "".join(f'<li><b>{e(x["id"])}</b> → {e(mth(x["market"], f))}<div class="s-xs s-mut">{e(x.get("note", ""))}</div></li>' for x in sh)
        tabs += (f'<div class="s-note">มี Rule เงา {len(sh)} ข้อที่เงื่อนไขตรงกับแมตช์นี้ (ติดตามผลเบื้องหลัง ไม่มีผลต่อการฟันธง)</div>'
                 f'<button class="s-btn" data-tg="shadow" data-alt="ซ่อน Rule เงา">ดู Rule เงา</button>'
                 f'<div class="s-more" data-pane="shadow"><ul class="s-list">{items}</ul></div>')
    body = card("คะแนนต่อทางเลือก", tb) + card("Rule ที่ทำงาน · แตะแต่ละข้อเพื่อดูการคำนวณ", tabs, dl=.1)
    return chapter("ch-rules", "@N@", "บทที่ @N@ · Rule ลงคะแนน", "สัญญาณแต่ละข้อหนุนฝั่งไหน", lead, body)


# ---------------------------------------------------------------------------- บท 4: ฟอร์มและการพบกัน
def _ch_form(m, f):
    fm, tv, st = m.get("form") or {}, m.get("team_value") or {}, m.get("stats") or {}
    parts = []
    cols = ""
    for i, side in enumerate(("home", "away")):
        x = fm.get(side) or {}
        w, d_, l_ = _seq_count(x.get("seq"))
        if x.get("seq"):
            parts.append(f'<b>{e(f[side])}</b> {w}ชนะ {d_}เสมอ {l_}แพ้')
        rows = ""
        if x.get("win_rate") is not None:
            rows += f'<div class="s-brow"><span class="l s-sm">อัตราชนะ</span>{bar(x["win_rate"] / 100, "g", dl=.1)}<span class="n">{x["win_rate"]:g}%</span></div>'
        if x.get("gf") is not None and x.get("ga") is not None:
            rows += f'<div class="s-kv"><span>ประตูได้ / เสีย</span><b>{x["gf"]:g} / {x["ga"]:g}</b></div>'
        if tv.get(side):
            rows += f'<div class="s-kv"><span>มูลค่าทีม</span><b>{tv[side]:g}</b></div>'
        rk = f.get("rank_home") if side == "home" else f.get("rank_away")
        if isinstance(rk, (int, float)):
            rows += f'<div class="s-kv"><span>อันดับ</span><b>{rk:g}{(" / " + str(f["league_size"])) if f.get("league_size") else ""}</b></div>'
        if st.get("venue"):
            gf, ga = (st.get("home_gf"), st.get("home_ga")) if side == "home" else (st.get("away_gf"), st.get("away_ga"))
            if gf is not None and ga is not None:
                rows += f'<div class="s-kv"><span>{"ในบ้าน" if side == "home" else "นอกบ้าน"} ได้/เสียต่อนัด</span><b>{gf:.2f} / {ga:.2f}</b></div>'
        cols += card(f"{f[side]} · {'เจ้าบ้าน' if side == 'home' else 'ทีมเยือน'}",
                     (S.dots(x.get("seq")) or '<div class="s-mut s-sm">ไม่มีข้อมูลฟอร์ม</div>') + rows, dl=.1 * i)
    h2h = m.get("h2h") or []
    hb = ""
    if h2h:
        items = ""
        for i, hh in enumerate(h2h[:5]):
            same = hh.get("home_is_current_home", True)
            ch_, ca = (hh["hg"], hh["ag"]) if same else (hh["ag"], hh["hg"])
            k = "w" if ch_ > ca else "l" if ch_ < ca else "d"
            tp = f"{f['home']} {ch_}–{ca} {f['away']}" + (f" · {hh.get('date')}" if hh.get("date") else "")
            items += f'<span class="s-score {k} s-pop" style="--dl:{.08 * i:.2f}s"{tipattr(tp)}>{ch_}–{ca}</span>'
        avg = f.get("h2h_avg_total")
        hb = (f'<div class="s-chips" style="gap:8px">{items}</div>'
              f'<div class="s-note">สกอร์มองจากเจ้าบ้านปัจจุบัน (เขียว = {e(f["home"])} ชนะ) · '
              f'{e(f["fav_name"])} ชนะ {f.get("h2h_fav_w", 0)} · เสมอ {f.get("h2h_draw", 0)} · {e(f["dog_name"])} ชนะ {f.get("h2h_dog_w", 0)}'
              + (f' · ประตูรวมเฉลี่ย {avg:.1f}' if avg is not None else "") + "</div>")
        parts.append(f'พบกัน {len(h2h[:5])} นัดหลัง {e(f["fav_name"])} ชนะ {f.get("h2h_fav_w", 0)} เสมอ {f.get("h2h_draw", 0)}')
    lead = " · ".join(parts) if parts else "ไม่มีข้อมูลฟอร์มจากรูป"
    body = f'<div class="s-grid">{cols}</div>' + (card("เจอกัน 5 นัดล่าสุด (H2H)", hb, dl=.15) if hb else "")
    return chapter("ch-form", "@N@", "บทที่ @N@ · ฟอร์มและการพบกัน", "ผลงานช่วงหลังของสองทีม", lead, body)


# ---------------------------------------------------------------------------- บท 5: ข้อมูลทีม
def _ch_team(m, f):
    tn = m.get("team_news")
    kick, title = "บทที่ @N@ · ข้อมูลทีม", "xG ตัวเจ็บ วันพัก และบอลถ้วย"
    if not tn:
        return chapter("ch-team", "@N@", kick, title, "ไม่ได้ค้นข้อมูลทีมในการวิเคราะห์นี้ (ปิดการค้นหา หรือเป็นรายการที่บันทึกก่อนมีฟีเจอร์นี้)", "")
    if tn.get("error"):
        return chapter("ch-team", "@N@", kick, title, f"ค้นข้อมูลทีมไม่สำเร็จ: {e(tn['error'])}", "")
    xg = tn.get("xg") or {}
    ok_n = sum(1 for s in ("home", "away") if (xg.get(s) or {}).get("status") == "ok")
    ok_n += sum(1 for s in ("home", "away") for p in (tn.get("injuries") or {}).get(s, []) if p.get("st") == "ok")
    ok_n += sum(1 for s in ("home", "away") if ((tn.get("rest") or {}).get(s) or {}).get("status") == "ok")
    miss = (tn.get("problems") or []) + (tn.get("missing") or [])
    rep_n = sum(1 for s in ("home", "away") if (xg.get(s) or {}).get("status") == "reported")
    rep_n += sum(1 for s in ("home", "away") for p in (tn.get("injuries") or {}).get(s, []) if p.get("st") == "reported")
    rep_n += sum(1 for s in ("home", "away") if ((tn.get("rest") or {}).get(s) or {}).get("status") == "reported")
    lead = (f'ยืนยันแหล่งได้ <b>{ok_n}</b> รายการ'
            + (f' · AI รายงานหลังค้นเว็บแต่รอยืนยัน <b>{rep_n}</b> รายการ (ตรวจเองก่อนใช้)' if rep_n else "")
            + (f' · ไม่มีข้อมูลหรือไม่นำไปใช้ <b>{len(miss)}</b> รายการ' if miss else "")
            + ' · ระบบไม่เดาค่าที่หาไม่เจอ และค่าเหล่านี้ยังไม่มีผลต่อการฟันธง')
    na = '<span class="s-mut" style="font-style:italic">ไม่มีข้อมูล</span>'

    # xG สองฝั่งแบบกระจก
    h, a = xg.get("home") or {}, xg.get("away") or {}
    xrows = ""
    for lab, k, good_high in (("xG สร้างได้ต่อนัด", "xg", True), ("xGA เสียต่อนัด", "xga", False), ("ประตูได้จริง", "gf", True), ("ประตูเสียจริง", "ga", False)):
        hv, av = h.get(k), a.get(k)
        if hv is None and av is None:
            continue
        mx = max([0.5] + [v for v in (hv, av) if v is not None]) * 1.15
        xrows += (f'<div class="s-tug s-rv" style="grid-template-columns:52px 1fr 1fr 52px"><div class="sd"><b>{f"{hv:.2f}" if hv is not None else "–"}</b></div>'
                  f'<div class="half l"><i class="s-fill" style="--w:{(hv or 0) / mx * 100:.0f}%;background:#14b8a6"></i></div>'
                  f'<div class="half r"><i class="s-fill" style="--w:{(av or 0) / mx * 100:.0f}%;background:#818cf8"></i></div>'
                  f'<div class="sd r"><b>{f"{av:.2f}" if av is not None else "–"}</b></div></div>'
                  f'<div class="s-xs s-mut" style="text-align:center;margin-top:-8px">{e(lab)}</div>')
    srcs = []
    for s in ("home", "away"):
        x = xg.get(s) or {}
        if x.get("status") == "ok":
            srcs.append(f'{f[s]}: {x.get("source")} {x.get("as_of") or ""} ({x.get("games") or "?"} นัด)')
        elif x.get("status") == "reported":
            srcs.append(f'{f[s]}: AI รายงานจาก {x.get("source")} {x.get("as_of") or ""} — รอยืนยัน ไม่นำไปคำนวณ')
        elif x.get("status") in ("unverified", "invalid"):
            srcs.append(f'{f[s]}: ไม่มีข้อมูลที่ยืนยันได้')
        elif x.get("status") == "stale":
            srcs.append(f'{f[s]}: ข้อมูลเก่า ไม่นำไปใช้')
        else:
            srcs.append(f'{f[s]}: ไม่มีข้อมูล')
    xhead = (f'<div class="s-tug" style="grid-template-columns:1fr 1fr;margin:0 0 6px"><b class="s-sm" style="color:#5eead4">{e(f["home"])}</b>'
             f'<b class="s-sm" style="color:#a5b4fc;text-align:right">{e(f["away"])}</b></div>')
    xbody = (xhead + xrows) if xrows else na
    xbody += '<div class="s-note">' + " · ".join(e(x) for x in srcs) + "</div>"
    cards = card("xG / xGA 5 นัดล่าสุด", xbody)

    # ตัวเจ็บ + วันพัก
    INJ = {"out": ("ไม่ได้ลง", "bad"), "doubtful": ("ไม่แน่", "warn"), "suspended": ("โดนแบน", "bad")}
    ROLE = {"starter": "ตัวจริง", "rotation": "สำรอง", "unknown": "ไม่ทราบบทบาท"}
    for i, s in enumerate(("home", "away")):
        lst = (tn.get("injuries") or {}).get(s) or []
        if lst:
            body = "".join(
                f'<div class="s-kv"{tipattr(_src_tip(p))}>'
                f'<span>{"★ " if p.get("role") == "starter" else ""}{e(p["player"])} <span class="s-xs s-mut">{e(p.get("position"))} · {ROLE.get(p.get("role"), "")}</span></span>'
                f'{chip(*INJ.get(p.get("status"), ("?", "off")))}{" " + chip("ข้อมูลเก่า", "warn") if p.get("st") == "stale" else ""}'
                f'{" " + chip("AI รายงาน", "warn") if p.get("st") == "reported" else ""}</div>' for p in lst)
        else:
            body = ('<div class="s-up s-sm">ไม่พบรายงานตัวเจ็บ/แบน</div>' if (tn.get("injuries_checked") or {}).get(s) else na)
        r = (tn.get("rest") or {}).get(s) or {}
        if r.get("days") is not None and r.get("status") in ("ok", "reported"):
            body += (f'<div class="s-kv" style="margin-top:6px"><span>พักมาแล้ว{" (AI รายงาน)" if r["status"] == "reported" else ""}</span><b class="{"s-warn" if r["days"] <= 3 else ""}">{num(r["days"], 0)} วัน</b></div>'
                     f'<div class="s-xs s-mut">นัดก่อน {e(r.get("last_date"))} {e(r.get("competition") or "")}</div>')
        else:
            body += f'<div class="s-kv" style="margin-top:6px"><span>พักมาแล้ว</span>{na}</div>'
        if ((tn.get("cup") or {}).get("rotation") or {}).get(s):
            body += '<div style="margin-top:6px">' + chip("มีข่าวหมุนเวียน/พักตัวหลัก", "warn") + "</div>"
        cards += card(f"{f[s]} · ตัวเจ็บและวันพัก", body, dl=.08 * (i + 1))
    ex = []
    c = tn.get("cup") or {}
    if c.get("is_cup"):
        ex.append(("บอลถ้วย" + (f" เลก {c['leg']}" if c.get("leg") else "") + (f" · เลกแรก {c['first_leg_score']}" if c.get("first_leg_score") else ""), "acc"))
    lu = tn.get("lineups") or {}
    ex.append(("ประกาศตัวจริงแล้ว", "ok") if lu.get("confirmed") else ("ตัวจริง: ยังไม่ประกาศ / ไม่มีข้อมูล", "off"))
    if tn.get("match_date"):
        ex.append((f"วันแข่ง {tn['match_date']}", "off"))
    ob = chips(ex)
    news = tn.get("other_news") or []
    if news:
        ob += '<ul class="s-list">' + "".join(f'<li>{e(n["text"])} <span class="s-xs s-mut">[{e(n.get("source") or "-")} {e(n.get("as_of") or "")}]</span></li>' for n in news) + "</ul>"
    if miss:
        ob += ('<div class="s-sm s-warn s-b" style="margin-top:10px">ไม่มีข้อมูล / ไม่นำไปใช้</div><ul class="s-list">'
               + "".join(f"<li>{e(x)}</li>" for x in miss) + "</ul>")
    used = []
    if f.get("tn_xg_total") is not None:
        used.append(f"xG รวมคาดการณ์ {f['tn_xg_total']:.2f}")
    if f.get("tn_fav_overperf") is not None:
        used.append(f"ทีมต่อ ผลจริง−xG {f['tn_fav_overperf']:+.2f}/นัด")
    if f.get("tn_fav_starters_out") is not None and f.get("tn_dog_starters_out") is not None:
        used.append(f"ตัวจริงหาย ต่อ {f['tn_fav_starters_out']} / รอง {f['tn_dog_starters_out']}")
    if used:
        ob += '<div class="s-note">ค่าที่ยืนยันแล้วและส่งให้ Rule เงา R42–R46: ' + e(" · ".join(used)) + "</div>"
    srcl = [x for x in (tn.get("sources") or []) if x.get("uri")][:8]
    if srcl:
        ob += ('<div class="s-note">แหล่งที่ค้นเจอ: ' + " · ".join(
            f'<a href="{e(x["uri"])}" target="_blank" rel="noopener">{e(x.get("title") or "ลิงก์")}</a>' for x in srcl) + "</div>")
    ev = (chip(f"แหล่งยืนยัน {len(tn.get('grounded') or [])} เว็บ", "ok") if tn.get("grounded")
          else chip("ค้นเว็บจริง · ไม่มีรายชื่อแหล่ง", "warn") if tn.get("searched") else chip("ไม่มีหลักฐานการค้น", "bad"))
    cards += card("บริบทเพิ่มเติม", ob, ev, dl=.2)
    return chapter("ch-team", "@N@", kick, title, lead, f'<div class="s-grid">{cards}</div>')


# ---------------------------------------------------------------------------- บท 6: บริบทและการตรวจสอบ
def _ch_check(res):
    m, f = res["m"], res["f"]
    ctx = m.get("context") or {}
    cc = [({"league": "ลีก", "cup": "ถ้วย", "playoff": "เพลย์ออฟ"}.get(ctx.get("type", "league"), "ลีก"), "acc")]
    cc += [(lb, "") for k, lb in CTX_LABELS if ctx.get(k)]
    if ctx.get("desperation") in ("home", "away"):
        cc.append(("หนีตาย/ลุ้นหนัก: " + f[ctx["desperation"]], "warn"))
    rs = m.get("research") or {}
    cb = chips(cc if len(cc) > 1 else cc + [("ไม่พบบริบทพิเศษ", "off")])
    if rs.get("evidence"):
        cb += '<ul class="s-list">' + "".join(f"<li>{e(x)}</li>" for x in rs["evidence"]) + "</ul>"
    conf = {"high": "สูง", "medium": "ปานกลาง", "low": "ต่ำ"}.get(rs.get("confidence"))
    if res.get("research_err"):
        cb += f'<div class="s-note s-warn">ค้นหาบริบทอัตโนมัติไม่สำเร็จ (ใช้ค่าตั้งต้นแทน): {e(res["research_err"])}</div>'
    srcl = [x for x in (rs.get("sources") or []) if x.get("uri")][:8]
    if srcl:
        cb += ('<div class="s-note">แหล่งที่ใช้: ' + " · ".join(
            f'<a href="{e(x["uri"])}" target="_blank" rel="noopener">{e(x.get("title") or "ลิงก์")}</a>' for x in srcl) + "</div>")
    ver = f.get("verify") or []
    vb = "".join(f'<div class="s-kv s-rv" style="--dl:{.07 * i:.2f}s"><span>{e(t)}</span><b class="s-pop" style="--dl:{.07 * i + .2:.2f}s">{"✅" if ok else "❌"}</b></div>'
                 for i, (ok, t) in enumerate(ver)) or '<div class="s-mut">ไม่มีข้อมูลการตรวจ</div>'
    warns = res.get("warns") or []
    ok_n = sum(1 for ok, _ in ver if ok)
    lead = (f'ตรวจเหย้า/เยือนผ่าน <b>{ok_n}/{len(ver)}</b> ข้อ' + (" — มีข้อไม่ผ่าน ระบบลดระดับสัญญาณแล้ว" if f.get("verify_fail") else "")
            + (f' · มีคำเตือนจากการอ่านข้อมูล <b>{len(warns)}</b> ข้อ' if warns else " · ไม่มีคำเตือนจากการอ่านข้อมูล"))
    body = card("บริบทแมตช์", cb, chip("ค้นหาอัตโนมัติ" + (f" · ความน่าเชื่อถือ{conf}" if conf else ""), "off") if rs else "")
    body += card("Home/Away Verification", vb, dl=.1)
    if warns:
        body += card(f"คำเตือนจากการอ่านข้อมูล ({len(warns)})", '<ul class="s-list">' + "".join(
            f'<li class="{"s-down" if str(w).startswith("ร้ายแรง") else ""}">{e(w)}</li>' for w in warns) + "</ul>", dl=.15)
    return chapter("ch-check", "@N@", "บทที่ @N@ · ตรวจสอบ", "บริบทและความถูกต้องของข้อมูล", lead, f'<div class="s-grid">{body}</div>')


# ---------------------------------------------------------------------------- บท 7: สรุป
def _ch_summary(f, contribs, pick):
    bm = base_of(pick["market"])
    om = PAIR.get(bm)
    sup = sorted([c for c in contribs if c["market"] == bm], key=lambda c: -c["eff"])[:3]
    opp = sorted([c for c in contribs if om and c["market"] == om], key=lambda c: -c["eff"])[:2]
    why = "".join(f'<li><b>{e(q.RULE_NAMES.get(c["rule"], c["rule"]))}</b> ({c["eff"]:+.2f}) — {e(c.get("note", ""))}</li>' for c in sup) \
        or "<li>ไม่มี Rule หนุนโดยตรง (ระบบบังคับฟันธงตามกติกาข้อ 13)</li>"
    risk = [f'{q.RULE_NAMES.get(c["rule"], c["rule"])} ({c["eff"]:+.2f}) — {c.get("note", "")}' for c in opp]
    if pick.get("move_only"):
        risk.append("สัญญาณมาจากการไหลของราคาล้วน ไม่มีราคาปัจจุบัน/บริบทหนุน (ระบบลดคะแนนเหลือ 60%)")
    if pick.get("verify_fail"):
        risk.append("ตรวจเหย้า/เยือนไม่ผ่าน ควรตรวจรูปอีกครั้ง")
    risk += list(pick.get("skip_reasons") or [])
    if pick.get("tier") == "ต่ำ" and not pick.get("skip"):
        risk.append("สัญญาณอ่อน ควรลดสัดส่วนเงินเดิมพัน")
    rk = "".join(f"<li>{e(x)}</li>" for x in risk) or "<li>ไม่มีสัญญาณค้านที่สำคัญ</li>"
    lead = (f'{"ระบบแนะนำให้<b>ข้ามไม้นี้</b> และติดตาม " if pick.get("skip") else "ไม้ของแมตช์นี้คือ "}<b>{e(pick["label"])}</b> '
            f'ระดับสัญญาณ<b>{e(pick.get("tier", ""))}</b> (คะแนน {pick["strength"]:.2f})')
    b = pick.get("best")
    price = (f'<div class="s-big s-up">{e(b["book"])} @{b["price"]:.2f}</div><div class="s-sm s-mut">ดีกว่าราคามัธยฐาน +{b["gain"]:.2f} · '
             f'จุดคุ้มทุนลดจาก {b["breakeven_median"]:.1%} เหลือ {b["breakeven"]:.1%}</div>') if b else \
        f'<div class="s-mid">@{pick.get("price_win", 0):.2f}</div><div class="s-sm s-mut">ไม่มีเจ้าที่ให้ราคาดีกว่าราคามัธยฐาน</div>'
    body = ('<div class="s-grid">' + card("เหตุผลหลัก", f'<ul class="s-list">{why}</ul>') + card("สิ่งที่ต้องระวัง", f'<ul class="s-list">{rk}</ul>', dl=.1)
            + card("ราคาที่ควรหา", price, dl=.2) + "</div>"
            + '<div class="s-note s-rv">ผลวิเคราะห์เป็นแบบจำลองเชิงสถิติจากราคาและข้อมูลที่อ่านได้ ไม่รับประกันผล และไม่ใช่คำแนะนำทางการเงิน</div>')
    return chapter("ch-sum", "@N@", "บทที่ @N@ · สรุป", "ไม้นี้ เหตุผล และความเสี่ยง", lead, body)


# ============================================================================ หน้าสถิติ
KIND_ORDER = ("แฮนดิแคปทีมต่อ", "แฮนดิแคปทีมรอง", "สูง (Over)", "ต่ำ (Under)", "1X2")


def pick_kind(r):
    f, mk = r["features"], r["pick"]["market"]
    if mk.startswith("HDP"):
        return "แฮนดิแคปทีมต่อ" if mk == f.get("fav_hdp") else "แฮนดิแคปทีมรอง"
    if mk.startswith("OU"):
        return "สูง (Over)" if mk == "OU_OVER" else "ต่ำ (Under)"
    return "1X2"


def _wl(recs):
    w = sum(1 for r in recs if r["pick_r"] > 0)
    l = sum(1 for r in recs if r["pick_r"] < 0)
    return w, len(recs) - w - l, l


def _cum(vals):
    out, run, peak, dd = [], 0.0, 0.0, 0.0
    for v in vals:
        run += v
        out.append(run)
        peak = max(peak, run)
        dd = max(dd, peak - run)
    return out, dd


def _res_word(r):
    return q.result_word(r)


def stats_story(state, history, params):
    be = params.get("breakeven_wr", 0.525)
    allset = [r for r in history if r.get("status") == "settled" and "pick_r" in r]
    skipped = [r for r in allset if (r.get("pick") or {}).get("skip")]
    done = [r for r in allset if not (r.get("pick") or {}).get("skip")]
    pend = [r for r in history if r.get("status") == "pending"]
    if not done and not skipped:
        return S.plain(f'<div class="s-empty">ยังไม่มีผลที่บันทึก · ใส่ผลจริงที่แท็บ “บันทึกผล” เพื่อดูสถิติและให้ระบบเรียนรู้<br>'
                       f'<span class="s-sm">รอผล {len(pend)} นัด</span></div>')
    chs = []
    w, p_, l = _wl(done)
    pr = sum(r["pick_profit"] for r in done)
    wr = w / (w + l) if (w + l) else 0.0
    roi = pr / len(done) if done else 0.0
    cum, dd = _cum([r["pick_profit"] for r in done])

    # 1 ภาพรวม
    lead = (f'เล่นไปแล้ว <b>{len(done)}</b> ไม้ ชนะ {w} · เจ๊า {p_} · แพ้ {l} — อัตราชนะ <b>{wr:.1%}</b> '
            f'{"สูงกว่า" if wr >= be else "ต่ำกว่า"}จุดคุ้มทุนราว {be:.1%} · กำไรสุทธิ <b class="{"s-up" if pr >= 0 else "s-down"}">{pr:+.2f}</b> หน่วย'
            + (f' · ข้ามไว้ {len(skipped)} ไม้' if skipped else "") + f' · รอผล {len(pend)} นัด')
    ring_html = S.ring(wr, '<div class="s-big">' + num(wr * 100, 1, suf="%") + "</div>", f"ชนะ {w} / แพ้ {l}", "#34d399" if wr >= be else "#f87171")
    k = (f'<div class="s-kpis">'
         f'<div class="s-kpi wide s-rv">{ring_html}</div>'
         f'<div class="s-kpi s-rv" style="--dl:.08s"><div class="t">กำไรสุทธิ</div><div class="v {"s-up" if pr >= 0 else "s-down"}">{num(pr, 2, sign=True)}</div><div class="d">ROI {roi:+.1%} ต่อไม้</div></div>'
         f'<div class="s-kpi s-rv" style="--dl:.16s"><div class="t">ไม้ที่เล่น</div><div class="v">{num(len(done), 0)}</div><div class="d">เจ๊า {p_} · ข้าม {len(skipped)}</div></div>'
         f'<div class="s-kpi s-rv" style="--dl:.24s"><div class="t">Drawdown สูงสุด</div><div class="v s-warn">{num(dd, 2)}</div><div class="d">หน่วย จากจุดสูงสุด</div></div>'
         f'<div class="s-kpi s-rv" style="--dl:.32s"><div class="t">รอผล</div><div class="v">{num(len(pend), 0)}</div><div class="d">สัญญาณที่ยังไม่จบเกม</div></div></div>')
    chs.append(("st-all", "ภาพรวม", chapter("st-all", 1, "บทที่ 1 · ภาพรวม", "ผลงานทั้งหมดจนถึงวันนี้", lead, k)))

    # 2 เส้นทางกำไร
    if len(done) >= 2:
        labels = [f"#{i + 1} {r['features']['home']} vs {r['features']['away']} · {r['pick']['label']} → {_res_word(r['pick_r'])} {r['pick_profit']:+.2f}"
                  for i, r in enumerate(done)]
        streak, sk = 0, None
        for r in reversed(done):
            s_ = "W" if r["pick_r"] > 0 else "L" if r["pick_r"] < 0 else "P"
            if sk is None:
                sk = s_
            if s_ != sk:
                break
            streak += 1
        sw = {"W": "ชนะติด", "L": "แพ้ติด", "P": "เจ๊าติด"}[sk]
        lead = (f'กำไรสะสมสูงสุด <b>{max(cum):+.2f}</b> ต่ำสุด <b>{min(cum):+.2f}</b> ตอนนี้ <b>{cum[-1]:+.2f}</b> · '
                f'ช่วงล่าสุด{sw} <b>{streak}</b> ไม้ · ชี้หรือแตะบนกราฟเพื่อดูแต่ละไม้')
        last = done[-40:]
        vb = S.vbars([r["pick_profit"] for r in last],
                     [f"{r['features']['home']} vs {r['features']['away']}\n{r['pick']['label']}\n{_res_word(r['pick_r'])} {r['pick_profit']:+.2f}" for r in last])
        body = card("กำไรสะสมตามลำดับไม้", S.line_chart([("กำไรสะสม", "#2dd4bf", cum)], labels, ends=("ไม้ที่ 1", f"ไม้ที่ {len(done)}"))) + \
            card("กำไร/ขาดทุนต่อไม้ · 40 ไม้ล่าสุด", vb + '<div class="s-note">แท่งเขียว = กำไร · แดง = ขาดทุน · เทา = เจ๊า</div>', dl=.1)
        chs.append(("st-path", "เส้นทางกำไร", chapter("st-path", 2, "บทที่ 2 · เส้นทางกำไร", "ขึ้นลงอย่างไรระหว่างทาง", lead, body)))

    # 3 เล่นอะไรได้ผล
    groups = {}
    for r in done:
        groups.setdefault(pick_kind(r), []).append(r)
    rows, best_k = "", None
    for i, kind in enumerate(KIND_ORDER):
        g = groups.get(kind) or []
        if not g:
            continue
        gw, gp, gl = _wl(g)
        gwr = gw / (gw + gl) if (gw + gl) else 0
        gpr = sum(r["pick_profit"] for r in g)
        if best_k is None or gpr > best_k[1]:
            best_k = (kind, gpr, len(g))
        rows += (f'<div class="s-brow s-rv" style="--dl:{.06 * i:.2f}s"{tipattr(f"{kind}: {len(g)} ไม้ · ชนะ {gw} เจ๊า {gp} แพ้ {gl} · กำไร {gpr:+.2f}")}>'
                 f'<span class="l">{e(kind)} <span class="s-xs s-mut">({len(g)})</span></span>{bar(gwr, "g" if gwr >= be else "r", "fat", mark=be, dl=.06 * i)}'
                 f'<span class="n">{gwr:.0%} <span class="{"s-up" if gpr >= 0 else "s-down"} s-sm">{gpr:+.2f}</span></span></div>')
    lead = (f'ประเภทไม้ที่ทำกำไรมากที่สุดคือ <b>{e(best_k[0])}</b> ({best_k[1]:+.2f} จาก {best_k[2]} ไม้) · เส้นขาวบนแถบ = จุดคุ้มทุน'
            if best_k else "ยังไม่มีข้อมูล")
    body = card("อัตราชนะและกำไรแยกประเภทไม้", rows or '<div class="s-mut">ไม่มีข้อมูล</div>')
    wb = [r for r in done if "pick_profit_best" in r]
    extra = ""
    if wb:
        pm, pb = sum(r["pick_profit"] for r in wb), sum(r["pick_profit_best"] for r in wb)
        extra += card(f"Line shopping · {len(wb)} ไม้",
                      f'<div class="s-kv"><span>กำไรที่ราคามัธยฐาน</span><b class="{"s-up" if pm >= 0 else "s-down"}">{pm:+.2f}</b></div>'
                      f'<div class="s-kv"><span>ถ้าวางที่เจ้าที่ให้ราคาดีที่สุด</span><b class="{"s-up" if pb >= 0 else "s-down"}">{pb:+.2f}</b></div>'
                      f'<div class="s-kv"><span>ส่วนต่าง</span><b class="s-up">{pb - pm:+.2f} ({(pb - pm) / len(wb):+.3f}/ไม้)</b></div>', dl=.1)
    if skipped:
        sw_, sp_, sl_ = _wl(skipped)
        spr = sum(r["pick_profit"] for r in skipped)
        verdict = ("ไม้ที่ข้ามทำผลแย่กว่าไม้ที่เล่น → การข้ามช่วย" if spr / len(skipped) < roi else
                   "ไม้ที่ข้ามทำผลดีกว่าหรือพอ ๆ กับไม้ที่เล่น → การข้ามยังไม่ช่วย")
        extra += card(f"ไม้ที่ข้าม (ไม้เงา) · {len(skipped)} ไม้",
                      f'<div class="s-kv"><span>ชนะ / แพ้</span><b>{sw_} / {sl_}</b></div>'
                      f'<div class="s-kv"><span>กำไรถ้าเล่น</span><b class="{"s-up" if spr >= 0 else "s-down"}">{spr:+.2f} (ROI {spr / len(skipped):+.1%})</b></div>'
                      f'<div class="s-kv"><span>เทียบไม้ที่เล่น</span><b>ROI {roi:+.1%}</b></div><div class="s-note">{e(verdict)} · ต้องมีหลายสิบไม้จึงจะสรุปได้</div>', dl=.15)
    if extra:
        body += f'<div class="s-grid" style="margin-top:12px">{extra}</div>'
    chs.append(("st-kind", "ประเภทไม้", chapter("st-kind", len(chs) + 1, f"บทที่ {len(chs) + 1} · เล่นอะไรได้ผล", "แยกตามประเภทไม้", lead, body)))

    # 4 คะแนนเชื่อได้แค่ไหน
    if len(done) >= 10:
        chs.append(("st-ladder", "คะแนน", _ladder_chapter(done, be, len(chs) + 1)))
    chs.append(("st-gate", "ตัวกรอง", gate_chapter(history, params, len(chs) + 1)))
    chs.append(("st-score", "สกอร์", score_accuracy_chapter(history, len(chs) + 1)))
    # 5 Rule
    chs.append(("st-life", "Rule", lifecycle_chapter(state, params, len(chs) + 1)))
    # 6 น้ำหนัก
    chs.append(("st-w", "น้ำหนัก", _weights_chapter(state, len(chs) + 1)))
    # 7 ล่าสุด
    items = ""
    for r in list(reversed(history))[:12]:
        fe = r["features"]
        if r["status"] == "settled":
            k_ = "w" if r["pick_r"] > 0 else "l" if r["pick_r"] < 0 else "p"
            tail = chip(f'{_res_word(r["pick_r"])} {r["pick_profit"]:+.2f}', {"w": "ok", "l": "bad", "p": "warn"}[k_])
            sc = f' {r["score"][0]}-{r["score"][1]}' if r.get("score") else ""
            tail += (" " + chip("ข้าม", "off") if r["pick"].get("skip") else "") + (" " + chip("แก้ไขแล้ว", "warn") if r.get("edits") else "")
        else:
            k_, sc, tail = "", "", chip("รอผล", "off")
        items += (f'<div class="it {k_} s-rv"><div>{e(fe["home"])}{e(sc)} {e(fe["away"])}<small>{e(r["pick"]["label"])} · {e(r.get("created", ""))}</small></div>'
                  f'<div>{tail}</div></div>')
    n = len(chs) + 1
    chs.append(("st-recent", "ล่าสุด", chapter("st-recent", n, f"บทที่ {n} · ล่าสุด", "12 รายการล่าสุด", "ไล่จากใหม่ไปเก่า", card("", f'<div class="s-tl">{items}</div>'))))
    return S.story(chs)


def _ladder_rows(recs, nb):
    recs = sorted(recs, key=lambda r: r["pick"]["strength"])
    n, out = len(recs), []
    for i in range(nb):
        seg = recs[i * n // nb:(i + 1) * n // nb]
        if seg:
            w, _, l = _wl(seg)
            out.append((seg[0]["pick"]["strength"], seg[-1]["pick"]["strength"], len(seg), w, l, sum(r["pick_profit"] for r in seg) / len(seg)))
    return out


def _ladder_html(recs, nb, be):
    h = ""
    for i, (lo, hi, n, w, l, roi) in enumerate(_ladder_rows(recs, nb)):
        wr = w / (w + l) if (w + l) else 0
        h += (f'<div class="s-brow s-rv" style="--dl:{.07 * i:.2f}s"{tipattr(f"คะแนน {lo:.2f}–{hi:.2f}: {n} ไม้ · ชนะ {w} แพ้ {l} · ROI {roi:+.2f}/ไม้")}>'
              f'<span class="l s-sm">{lo:.2f} – {hi:.2f} <span class="s-mut">({n})</span></span>{bar(wr, "g" if wr >= be else "r", "fat", mark=be, dl=.07 * i)}'
              f'<span class="n">{wr:.0%} <span class="{"s-up" if roi >= 0 else "s-down"} s-sm">{roi:+.2f}</span></span></div>')
    return h


def _spearman(recs):
    pts = [(r["pick"]["strength"], 1 if r["pick_r"] > 0 else 0) for r in recs if r["pick_r"] != 0]
    n = len(pts)
    if n < 8:
        return None
    xs = [p[0] for p in pts]
    o = sorted(range(n), key=lambda i: xs[i])
    rx, i = [0.0] * n, 0
    while i < n:
        j = i
        while j + 1 < n and xs[o[j + 1]] == xs[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rx[o[k]] = (i + j) / 2
        i = j + 1
    ys = [p[1] for p in pts]
    mx, my = sum(rx) / n, sum(ys) / n
    sx, sy = sum((a - mx) ** 2 for a in rx), sum((b - my) ** 2 for b in ys)
    if sx <= 0 or sy <= 0:
        return None
    rho = sum((a - mx) * (b - my) for a, b in zip(rx, ys)) / (sx * sy) ** 0.5
    return rho, rho * ((n - 1) ** 0.5)


def _ladder_chapter(done, be, n):
    nb = 5 if len(done) >= 75 else 3
    sp = _spearman(done)
    if sp:
        rho, z = sp
        trend = (f'ความสัมพันธ์คะแนน↔ชนะ (Spearman) <b>{rho:+.2f}</b> (z ≈ {z:+.1f}) — '
                 + ("คะแนนสูงชนะมากกว่า" if rho > 0 else "คะแนนสูงชนะน้อยกว่า")
                 + (" อย่างมีนัยสำคัญ" if abs(z) >= 1.96 else " แต่ยังไม่มีนัยสำคัญ จึงยังใช้คะแนนเป็นตัวบอกโอกาสชนะไม่ได้"))
    else:
        trend = "ข้อมูลยังไม่พอวัดความสัมพันธ์"
    groups = {}
    for r in done:
        groups.setdefault(pick_kind(r), []).append(r)
    tabs = [("all", f"รวม ({len(done)})", _ladder_html(done, nb, be))]
    for i, kind in enumerate(KIND_ORDER):
        g = groups.get(kind) or []
        if g:
            tabs.append((f"k{i}", f"{kind} ({len(g)})", _ladder_html(g, 3, be) if len(g) >= 12 else '<div class="s-mut s-sm">ข้อมูลยังน้อย (ต้องมีอย่างน้อย 12 ไม้)</div>'))
    tb = ('<div class="s-tabs"><div class="s-tabbar">' + "".join(f'<button class="{"on" if i == 0 else ""}" data-tab="{k}">{e(t)}</button>' for i, (k, t, _) in enumerate(tabs))
          + "</div>" + "".join(f'<div data-tabpane="{k}" class="{"on" if i == 0 else ""}">{h}</div>' for i, (k, _, h) in enumerate(tabs)) + "</div>")
    tb += ('<div class="s-note">แบ่งไม้เป็นกลุ่มเท่า ๆ กันตามคะแนน · แถบ = อัตราชนะ (เส้นขาว = จุดคุ้มทุน) · ตัวเลขสีเล็ก = ROI ต่อไม้ · '
           'คะแนนต่างช่วงเวลาอาจคนละสเกลเพราะน้ำหนัก Rule ถูกปรับระหว่างทาง</div>')
    return chapter("st-ladder", n, f"บทที่ {n} · คะแนนเชื่อได้แค่ไหน", "ไล่ระดับคะแนนสัญญาณ", trend, card("อัตราชนะตามช่วงคะแนน", tb))


def lifecycle_chapter(state, params, n, cid="st-life"):
    life = state.get("lifecycle") or {}
    learned = {r["id"]: r for r in state.get("learned_rules", [])}
    rows = [(rid, x) for rid, x in life.items()]
    rows += [(rid, {"kind": "learned", "status": "shadow", "n": 0, "w": 0, "l": 0, "reason": "ยังไม่มีผลนอกกลุ่มตัวอย่าง"})
             for rid in learned if rid not in life]
    title, kick = "Rule ไหนกำลังพิสูจน์ตัว", f"บทที่ {n} · สถานะ Rule ผู้สมัคร"
    if not rows:
        return chapter(cid, n, kick, title, "ยังไม่มี Rule ผู้สมัคร", "")
    cnt = {k: sum(1 for _, x in rows if x["status"] == k) for k in ("active", "shadow", "retired")}
    ready = sorted(rid for rid, x in rows if x.get("ready") and x["status"] == "shadow")
    lead = ((f'<b>{", ".join(ready)}</b> ผ่านเกณฑ์แล้วแต่ยังไม่เปิดใช้เพราะล็อกสถานะ Rule อยู่ (ปลดล็อกได้ที่ “ตั้งค่าระบบ”) · ' if ready else "")
            + f'ใช้งาน <b>{cnt["active"]}</b> · เงา (ติดตามผลเบื้องหลัง) <b>{cnt["shadow"]}</b> · ถอดแล้ว <b>{cnt["retired"]}</b> — '
            f'Rule ใหม่ทุกข้อเริ่มเป็นเงา ปลดล็อคเมื่อชนะ ≥ {params["unlock_wr"]:.0%} จาก ≥ {params["unlock_min_n"]} ครั้ง '
            f'หรือครบ {params["judge_n"]} ครั้งแล้วผ่านเกณฑ์')

    def item(rid, x, i):
        dec = x["w"] + x["l"]
        wr = x["w"] / dec if dec else 0.0
        if x.get("kind") == "learned" and rid in learned:
            lr = learned[rid]
            desc = f'{" + ".join(lr["tags"])} → {q.ROLE_TH[lr["role"]]}'
        else:
            desc = q.RULE_NAMES.get(rid, rid)
        prog = min(1.0, x["n"] / max(params["judge_n"], 1))
        tip = f'{rid}: {desc}\nผลนอกกลุ่มตัวอย่าง {x["w"]}/{dec}' + (f' = {wr:.0%}' if dec else "") + f'\nใช้ไป {x["n"]}/{params["judge_n"]} ครั้ง\n{x.get("reason", "")}'
        rdy = (" " + chip("พร้อมใช้ · ล็อกอยู่", "warn")) if x.get("ready") and x["status"] == "shadow" else ""
        return (f'<div class="s-brow s-rv" style="--dl:{min(.03 * i, .6):.2f}s"{tipattr(tip)}><span class="l s-sm"><b>{e(rid)}</b>{rdy} '
                f'<span class="s-mut">{e(desc[:60])}</span></span>{bar(prog, "t" if x["status"] == "active" else "n" if x["status"] == "shadow" else "r", mark=None)}'
                f'<span class="n s-sm">{(f"{wr:.0%}" if dec else "–")} <span class="s-mut">({x["n"]})</span></span></div>')

    order = {"active": 0, "shadow": 1, "retired": 2}
    rows.sort(key=lambda t: (order.get(t[1]["status"], 3), not t[1].get("ready"), -t[1]["n"]))
    tabs = []
    for k, lab in (("active", "ใช้งาน"), ("shadow", "เงา"), ("retired", "ถอดแล้ว")):
        sub = [t for t in rows if t[1]["status"] == k]
        h = "".join(item(rid, x, i) for i, (rid, x) in enumerate(sub[:60])) or '<div class="s-mut s-sm">ไม่มี</div>'
        tabs.append((k, f"{lab} ({len(sub)})", h))
    first = next((i for i, t in enumerate(tabs) if not t[2].startswith('<div class="s-mut')), 1)
    tb = ('<div class="s-tabs"><div class="s-tabbar">' + "".join(f'<button class="{"on" if i == first else ""}" data-tab="{k}">{e(t)}</button>' for i, (k, t, _) in enumerate(tabs))
          + "</div>" + "".join(f'<div data-tabpane="{k}" class="{"on" if i == first else ""}">{h}</div>' for i, (k, _, h) in enumerate(tabs)) + "</div>"
          + f'<div class="s-note">แถบ = ความคืบหน้าสู่การตัดสิน ({params["judge_n"]} ครั้ง) · ตัวเลข = อัตราชนะนอกกลุ่มตัวอย่าง (จำนวนครั้งที่ใช้) · แตะเพื่อดูเหตุผลสถานะ</div>')
    tag = "".join(chip(f"{t} {cnt[k]}", c) for k, t, c in (("active", "ใช้งาน", "ok"), ("shadow", "เงา", "off"), ("retired", "ถอด", "bad")))
    return chapter(cid, n, kick, title, lead, card("Rule ผู้สมัคร", tb, f'<span class="s-chips">{tag}</span>'))


def _weights_chapter(state, n):
    wts = state.get("weights") or {}
    rs = state.get("rule_stats") or {}
    items = sorted(((rs.get(k, {}).get("n", 0), k, v, q.DEFAULT_WEIGHTS.get(k, 1.0)) for k, v in wts.items()), key=lambda x: (-x[0], x[1]))[:16]
    rows = ""
    for i, (cnt, k, v, d0) in enumerate(items):
        col = "g" if v > d0 + 0.005 else "r" if v < d0 - 0.005 else "n"
        tp = f"{k} {q.RULE_NAMES.get(k, '')}\nน้ำหนักปัจจุบัน {v:.2f} · ค่าเริ่มต้น {d0:.2f} · ใช้ {cnt} ครั้ง"
        rows += (f'<div class="s-brow s-rv" style="--dl:{.03 * i:.2f}s"{tipattr(tp)}>'
                 f'<span class="l s-sm"><b>{e(k)}</b> <span class="s-mut">{e(q.RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง"))[:40]}</span></span>'
                 f'{bar(min(v / 3, 1), col, mark=min(d0 / 3, 1), dl=.03 * i)}<span class="n s-sm">{v:.2f} <span class="s-mut">({cnt})</span></span></div>')
    frz = (state.get("params") or {}).get("freeze_weights", q.DEFAULT_PARAMS.get("freeze_weights"))
    lead = ("ตอนนี้<b>แช่แข็งน้ำหนัก</b>อยู่ ระบบเรียนรู้เบื้องหลังโดยไม่เปลี่ยนน้ำหนักที่ใช้ฟันธง" if frz else
            "น้ำหนักที่ใช้ฟันธงถูกปรับตามผลจริงหลังบันทึกผลแต่ละนัด") + " · เขียว = สูงกว่าค่าเริ่มต้น · แดง = ต่ำกว่า · เส้นขาว = ค่าเริ่มต้น"
    return chapter("st-w", n, f"บทที่ {n} · น้ำหนัก Rule", "Rule ไหนมีเสียงดังแค่ไหน", lead, card("น้ำหนัก Rule (เรียงตามจำนวนครั้งที่ใช้)", rows))


# ============================================================================ หน้าทดสอบย้อนหลัง
ARM_SHORT = {"static": "ไม่เรียนรู้", "weights": "ปรับน้ำหนัก", "full": "มีด่านคัดกรอง", "legacy": "แบบเดิม"}


def backtest_story(res):
    import backtest as bt
    n = res["n"]
    if n < 2:
        return S.plain('<div class="s-empty">ต้องมีรายการที่บันทึกผลแล้วอย่างน้อย 2 นัดจึงจะทดสอบย้อนหลังได้</div>')
    ms, cp, vd = res["metrics"], res["compare"], res["verdict"]
    tone = {"full": ("w", "✅"), "static": ("p", "⚠️")}.get(vd["tag"], ("p", "🔍"))
    hero = (f'<div class="s-result {tone[0]} s-rv" style="text-align:left"><div class="s-kick">ข้อสรุปของการทดสอบ · {n} นัด'
            f'{(" · ข้าม " + str(res["skipped"]) + " นัดที่ข้อมูลไม่ครบ") if res["skipped"] else ""}</div>'
            f'<div class="vd" style="margin:6px 0">{tone[1]} {e(vd["title"])}</div><ul class="s-list">' + "".join(f"<li>{e(x)}</li>" for x in vd["lines"]) + "</ul></div>")
    chs = []
    # 1 เส้นกำไร
    labels = ["เริ่ม"] + [f"#{i + 1} {b['home']} vs {b['away']}" for i, b in enumerate(res["bets"]["static"])]
    series = [(bt.ARM_LABEL[k], bt.ARM_COLOR[k], [0.0] + ms[k]["cum"]) for k in ("full", "static", "weights", "legacy")]
    fin = sorted(((ms[k]["profit"], k) for k in bt.ARMS), reverse=True)
    lead = (f'ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากันแล้วเดินไปทีละนัดแบบไม่มองอนาคต · ปลายทางสูงสุดคือ <b>{e(bt.ARM_LABEL[fin[0][1]])}</b> '
            f'({fin[0][0]:+.2f}) · ชี้หรือแตะบนกราฟเพื่อเทียบทั้ง 4 แบบในแต่ละนัด')
    chs.append(("bt-curve", "เส้นกำไร", chapter("bt-curve", 1, "บทที่ 1 · เส้นทางกำไร", "4 แบบเดินคู่กัน", lead, card("กำไรสะสม (walk-forward)", S.line_chart(series, labels, ends=("เริ่ม", f"นัดที่ {n}"))))))
    # 2 เทียบตัวชี้วัด
    rows = [("อัตราชนะ", "win_rate", "pct", 1), ("กำไรสุทธิ", "profit", "sgn", 1), ("ROI ต่อไม้", "roi", "sgn", 1),
            ("Drawdown สูงสุด (ต่ำ = ดี)", "max_dd", "num", -1), ("แพ้ติดสูงสุด (ต่ำ = ดี)", "loss_streak", "n", -1),
            ("ช่วง 10 ไม้ที่กำไร", "roll_pos", "pct", 1), ("ROI ครึ่งแรก", "roi_first", "sgn", None), ("ROI ครึ่งหลัง", "roi_second", "sgn", None)]
    blocks = ""
    for j, (lab, key, kind, dirn) in enumerate(rows):
        vals = {k: ms[k].get(key) for k in bt.ARMS}
        cand = [v for v in vals.values() if v is not None]
        if not cand:
            continue
        span = max(abs(v) for v in cand) or 1
        best = (max(cand) if dirn > 0 else min(cand)) if dirn and len({round(v, 6) for v in cand}) > 1 else None
        inner = ""
        for k in bt.ARMS:
            v = vals[k]
            if v is None:
                continue
            isb = best is not None and abs(v - best) < 1e-9
            inner += (f'<div class="s-brow" style="margin:4px 0;grid-template-columns:92px 1fr 70px"{tipattr(bt.ARM_LABEL[k])}><span class="l s-xs">{e(ARM_SHORT[k])}</span>'
                      f'<div class="s-bar"><i class="s-fill" style="--w:{abs(v) / span * 100:.0f}%;background:{bt.ARM_COLOR[k]};opacity:{1 if isb or best is None else .55}"></i></div>'
                      f'<span class="n s-sm {"s-up" if isb else ""}">{bt._fmt(v, kind)}{" ★" if isb else ""}</span></div>')
        blocks += card(lab, inner, dl=.04 * j)
    chs.append(("bt-cmp", "ตัวชี้วัด", chapter("bt-cmp", 2, "บทที่ 2 · เทียบตัวชี้วัด", "ใครดีกว่าในมุมไหน",
                                                "★ = ดีที่สุดในตัวชี้วัดนั้น (เฉพาะเมื่อค่าต่างกัน) · แถบโปร่ง = ไม่ใช่อันดับหนึ่ง", f'<div class="s-grid">{blocks}</div>')))
    # 3 ความต่างรายนัด + bootstrap
    cf = cp["full"]
    span = max(abs(cf["lo"]), abs(cf["hi"]), abs(cf["mean"]), 0.05) * 1.3
    pos = lambda v: (v + span) / (2 * span) * 100
    ci = (f'<div style="position:relative;height:46px;margin:6px 4px"><div style="position:absolute;left:0;right:0;top:22px;height:2px;background:rgba(255,255,255,.12)"></div>'
          f'<div style="position:absolute;left:50%;top:8px;height:30px;width:2px;background:rgba(255,255,255,.5)"></div>'
          f'<div class="s-rv" style="position:absolute;left:{pos(cf["lo"]):.1f}%;width:{pos(cf["hi"]) - pos(cf["lo"]):.1f}%;top:16px;height:14px;border-radius:8px;'
          f'background:{"rgba(52,211,153,.35)" if cf["lo"] > 0 else "rgba(248,113,113,.35)" if cf["hi"] < 0 else "rgba(148,163,184,.35)"}"></div>'
          f'<div style="position:absolute;left:calc({pos(cf["mean"]):.1f}% - 6px);top:17px;width:12px;height:12px;border-radius:50%;background:#fff"></div>'
          f'<span class="s-xs s-mut" style="position:absolute;left:50%;top:38px;transform:translateX(-50%)">0</span></div>'
          f'<div class="s-sm" style="text-align:center">ค่าเฉลี่ย <b>{cf["mean"]:+.3f}</b> ต่อไม้ · ช่วงเชื่อมั่น 95% [{cf["lo"]:+.3f}, {cf["hi"]:+.3f}] · P(ต่าง &gt; 0) ≈ {cf["p_pos"]:.0%}</div>')
    dif = [(i, x) for i, x in enumerate(cf["diffs"]) if abs(x) > 1e-9][-60:]
    bf, bs = res["bets"]["full"], res["bets"]["static"]
    tips = [f"นัดที่ {i + 1} {bf[i]['home']} vs {bf[i]['away']}\nมีด่าน: {bf[i].get('label', bf[i].get('market', ''))}\nไม่เรียนรู้: {bs[i].get('label', bs[i].get('market', ''))}\nต่างกัน {x:+.2f}" for i, x in dif]
    lead = (f'แบบเรียนรู้มีด่านคัดกรองฟันธงต่างจากแบบไม่เรียนรู้ <b>{cf["changed"]}</b>/{n} นัด · ดีกว่า {cf["better"]} นัด · แย่กว่า {cf["worse"]} นัด · '
            + ("ช่วงเชื่อมั่นอยู่เหนือศูนย์" if cf["lo"] > 0 else "ช่วงเชื่อมั่นอยู่ใต้ศูนย์" if cf["hi"] < 0 else "ช่วงเชื่อมั่นคร่อมศูนย์ = แยกไม่ออกจากความบังเอิญ"))
    body = card("ช่วงเชื่อมั่นของกำไรต่อไม้ที่ต่างกัน (bootstrap)", ci) + (card(f"เฉพาะนัดที่ฟันธงต่างกัน ({len(dif)} นัด)", S.vbars([x for _, x in dif], tips)
                                                                              + '<div class="s-note">เขียว = แบบมีด่านคัดกรองได้ดีกว่า · แดง = แย่กว่า · แตะแท่งเพื่อดูไม้ของทั้งสองแบบ</div>', dl=.1)
                                                                              if dif else card("ความต่างรายนัด", '<div class="s-mut">ทั้งสองแบบฟันธงเหมือนกันทุกนัด</div>', dl=.1))
    pm = res.get("perm")
    if pm:
        z = (pm["obs"] - pm["null_mean"]) / pm["null_sd"] if pm["null_sd"] > 1e-9 else 0.0
        body += card("การทดสอบสุ่มสลับสกอร์ (permutation)",
                     f'<div class="s-kv"><span>ถ้าไม่มีความสัมพันธ์จริง (สุ่ม {pm["B"]} รอบ)</span><b>{pm["null_mean"]:+.3f} ± {pm["null_sd"]:.3f}</b></div>'
                     f'<div class="s-kv"><span>ของจริง</span><b class="{"s-up" if pm["p"] < 0.05 else ""}">{pm["obs"]:+.3f} (z ≈ {z:+.1f})</b></div>'
                     f'<div class="s-kv"><span>p-value</span><b>{pm["p"]:.3f} {chip("ผ่าน", "ok") if pm["p"] < 0.05 else chip("ไม่ผ่าน", "off")}</b></div>', dl=.15)
    chs.append(("bt-diff", "ความต่าง", chapter("bt-diff", 3, "บทที่ 3 · การเรียนรู้ช่วยจริงไหม", "แยกฝีมือออกจากความบังเอิญ", lead, body)))
    # 4 ข้าม + นโยบาย
    sk, lg = res.get("skip"), cp.get("legacy")
    extra = ""
    if sk and sk["skipped"].get("n"):
        def ln(lab, x):
            return (f'<div class="s-kv"><span>{e(lab)}</span><b>{x.get("n", 0)} ไม้ · {bt._fmt(x.get("win_rate"), "pct")} · '
                    f'{bt._fmt(x.get("profit"), "sgn")} (ROI {bt._fmt(x.get("roi"), "sgn")})</b></div>') if x.get("n") else ""
        gap = (sk["played"].get("roi") or 0) - (sk["skipped"].get("roi") or 0)
        extra += card("ผลของเกณฑ์ “ข้าม”", ln("เล่นทุกนัด", sk["all"]) + ln("เล่นเฉพาะไม้ที่ไม่ถูกข้าม", sk["played"]) + ln("ไม้ที่ถูกข้าม (เงา)", sk["skipped"])
                      + f'<div class="s-note">{"ไม้ที่ข้ามแย่กว่าไม้ที่เล่น (การข้ามน่าจะช่วย)" if gap > 0 else "ไม้ที่ข้ามดีกว่าหรือพอ ๆ กับไม้ที่เล่น (การข้ามยังไม่ช่วย)"}</div>')
    if lg:
        extra += card("นโยบายเดิม vs ด่านคัดกรอง",
                      f'<div class="s-kv"><span>ใช้ Rule ใหม่ทันที − ไม่เรียนรู้</span><b class="{"s-up" if lg["mean"] > 0 else "s-down"}">{lg["mean"]:+.3f} [{lg["lo"]:+.3f}, {lg["hi"]:+.3f}]</b></div>'
                      f'<div class="s-kv"><span>มีด่านคัดกรอง − ไม่เรียนรู้</span><b class="{"s-up" if cf["mean"] > 0 else "s-down"}">{cf["mean"]:+.3f} [{cf["lo"]:+.3f}, {cf["hi"]:+.3f}]</b></div>', dl=.1)
    if extra:
        chs.append(("bt-pol", "ข้าม/นโยบาย", chapter("bt-pol", 4, "บทที่ 4 · เกณฑ์ข้ามและนโยบาย Rule", "ตัวกรองช่วยอะไรบ้าง", "เทียบผลเมื่อใช้และไม่ใช้ตัวกรอง", f'<div class="s-grid">{extra}</div>')))
    import football_quant_v58 as _q
    chs.append(("bt-life", "Rule", lifecycle_chapter({"lifecycle": res.get("lifecycle") or {}, "learned_rules": res["learned"]}, dict(_q.DEFAULT_PARAMS), len(chs) + 1, "bt-life")))
    notes = ["ผลทั้งหมดคำนวณจากประวัติที่บันทึกในระบบ ฟันธงซ้ำด้วย features ที่เก็บไว้ ไม่ใช่ไม้ที่คุณเดิมพันจริง",
             "ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากัน ทดสอบตั้งแต่ “เริ่มเรียนรู้จากศูนย์”",
             f"ข้อมูลน้อยกว่า {bt.MIN_RELIABLE} นัด ผลต่างเกือบทั้งหมดเป็นการสุ่ม · แม้ข้อมูลมาก ผลย้อนหลังก็ไม่รับประกันผลในอนาคต",
             "การสร้าง Rule ใหม่จากข้อมูลน้อยเสี่ยงจับรูปแบบบังเอิญ ซึ่งการทดสอบแบบ walk-forward นี้ช่วยเปิดเผยได้"]
    k = len(chs) + 1
    chs.append(("bt-note", "ข้อจำกัด", chapter("bt-note", k, f"บทที่ {k} · ข้อจำกัด", "อ่านผลอย่างระวัง", "สิ่งที่การทดสอบนี้บอกไม่ได้",
                                               card("", '<ul class="s-list">' + "".join(f"<li>{e(x)}</li>" for x in notes) + "</ul>"))))
    return S.story(chs, hero=hero)


def backtest_document(res):
    return S.document("Backtest: ไม่เรียนรู้ vs เรียนรู้ต่อเนื่อง", backtest_story(res), "Football Quant · ทดสอบย้อนหลังแบบ walk-forward")


# ============================================================================ หน้าบันทึกผล
def pending_cards(pend, sel):
    """การ์ดแมตช์ที่รอผล กดเพื่อเลือก (ส่งค่า id กลับ Python)"""
    if not pend:
        return S.plain('<div class="s-empty">ยังไม่มีสัญญาณที่รอผล — วิเคราะห์ในแท็บแรกโดยเปิด “บันทึกสัญญาณลงประวัติ”</div>')
    items = ""
    for i, r in enumerate(pend):
        fe, pk = r["features"], r["pick"]
        tier = pk.get("tier", "")
        items += (f'<button class="s-sel s-rv{" on" if r["id"] == sel else ""}" style="--dl:{min(.04 * i, .5):.2f}s" data-act="{e(r["id"])}">'
                  f'<div class="tm">{e(fe["home"])} <span class="s-mut">vs</span> {e(fe["away"])}</div><div class="pk">{e(pk["label"])}</div>'
                  f'<div class="s-chips">{chip("ระดับ" + tier, "acc" if tier in ("สูง", "กลาง") else "off")}'
                  f'{chip("ข้าม", "warn") if pk.get("skip") else ""}{chip(r.get("created", ""), "off")}</div></button>')
    return S.plain(f'<div class="s-h s-rv"><span>รอผล {len(pend)} นัด · แตะการ์ดเพื่อเลือกแมตช์ที่จบแล้ว</span></div><div class="s-pickgrid">{items}</div>')


def settle_result(fe, pick, hg, ag, outcomes, r, pf, changes, new, life_changes):
    k = "w" if r > 0 else "l" if r < 0 else "p"
    word = q.result_word(r)
    skp = ' <span class="s-chip warn">ไม้เงา · ไม่นับเป็นไม้ที่เล่น</span>' if pick.get("skip") else ""
    hero = (f'<div class="s-result {k} s-rv"><div class="s-kick">ผลออกแล้ว</div><div class="sc">{e(fe["home"])} {hg} – {ag} {e(fe["away"])}</div>'
            f'<div class="s-sm s-mut">{e(pick["label"])}{skp}</div><div class="vd s-pop" style="--dl:.4s;margin-top:8px">{e(word)} '
            f'<span class="{"s-up" if pf > 0 else "s-down" if pf < 0 else ""}">{num(pf, 2, sign=True)}</span> หน่วย</div></div>')
    th = {"HDP_HOME": f"แฮนดิแคป {fe['home']}", "HDP_AWAY": f"แฮนดิแคป {fe['away']}", "OU_OVER": "สูง (Over)", "OU_UNDER": "ต่ำ (Under)",
          "X12_HOME": f"1X2 {fe['home']}", "X12_AWAY": f"1X2 {fe['away']}"}
    cells = "".join(f'<div class="s-kv s-rv" style="--dl:{.05 * i:.2f}s"><span>{e(th.get(mk, mk))}{" ★" if mk == pick["market"] else ""}</span>'
                    f'{chip(q.result_word(v[0]), "ok" if v[0] > 0 else "bad" if v[0] < 0 else "warn")}</div>' for i, (mk, v) in enumerate(outcomes.items()))
    body = card("ผลของทุกตลาด (Post-mortem)", cells)
    if changes:
        wr = "".join(f'<div class="s-kv"><span>{e(q.RULE_NAMES.get(k_, "Rule ที่เรียนรู้เอง"))} <span class="s-mut s-xs">{e(k_)}</span></span>'
                     f'<b class="{"s-up" if n_ > o_ else "s-down" if n_ < o_ else ""}">{o_:.2f} → {n_:.2f}</b></div>' for k_, (o_, n_, _) in changes.items())
        body += card("ระบบปรับน้ำหนัก Rule", wr, dl=.1)
    if life_changes:
        lab = {"active": "ใช้งาน", "shadow": "เงา", "retired": "ถอด"}
        body += card("สถานะ Rule ผู้สมัครที่เปลี่ยน", "".join(
            f'<div class="s-kv"><span><b>{e(x[0])}</b> {lab.get(x[1], x[1])} → {lab.get(x[2], x[2])}<div class="s-xs s-mut">{e(x[3])}</div></span></div>' for x in life_changes), dl=.15)
    if new:
        body += card("🧠 Rule ใหม่ที่ระบบสร้าง (เริ่มเป็นเงา)", "".join(
            f'<div class="s-kv"><span><b>{e(r_["id"])}</b> {e(" + ".join(r_["tags"]))} → {e(q.ROLE_TH[r_["role"]])}</span>'
            f'<b>ชนะ {r_["wr"]:.0%} จาก {r_["n"]} นัด</b></div>' for r_ in new), dl=.2)
    return S.plain(hero + f'<div class="s-grid">{body}</div>')


def record_card(er):
    fe = er["features"]
    k = "ok" if er["pick_r"] > 0 else "bad" if er["pick_r"] < 0 else "warn"
    return S.plain(card("ผลที่บันทึกไว้",
                        f'<div class="s-mid">{e(fe["home"])} {er["score"][0]}–{er["score"][1]} {e(fe["away"])}</div>'
                        f'<div class="s-sm s-mut" style="margin:4px 0 8px">{e(er["pick"]["label"])}</div>'
                        + chips([(f'{q.result_word(er["pick_r"])} · {er["pick_profit"]:+.2f} หน่วย', k)] + ([(f'แก้ไขแล้ว {er["edits"]} ครั้ง', "warn")] if er.get("edits") else []))))


def edit_message(em):
    if em["kind"] == "edit":
        o, n = em["old"], em["new"]
        k = "w" if n["r"] > 0 else "l" if n["r"] < 0 else "p"
        head = (f'<div class="s-result {k} s-rv"><div class="s-kick">แก้สกอร์แล้ว · {e(em["title"])}</div>'
                f'<div class="sc" style="font-size:1.8rem">{o["score"][0]}-{o["score"][1]} → {n["score"][0]}-{n["score"][1]}</div>'
                f'<div class="s-sm">ผลสัญญาณ {e(q.result_word(o["r"]))} ({o["profit"]:+.2f}) → <b>{e(q.result_word(n["r"]))} ({n["profit"]:+.2f})</b></div></div>')
    else:
        head = (f'<div class="s-result p s-rv"><div class="s-kick">ยกเลิกผลแล้ว</div><div class="vd">{e(em["title"])}</div>'
                '<div class="s-sm">กลับเป็น “รอผล” (บันทึกผลใหม่ได้ด้านบน)</div></div>')
    wc = sorted(em["weight_changes"], key=lambda x: -abs((x[2] or 1.0) - (x[1] or 1.0)))[:8]
    body = "".join(f'<div class="s-kv"><span>{e(k_)} · {e(q.RULE_NAMES.get(k_, "Rule ที่เรียนรู้เอง"))}</span>'
                   f'<b>{("-" if a is None else f"{a:.2f}")} → {("ถูกลบ" if b is None else f"{b:.2f}")}</b></div>' for k_, a, b in wc)
    body += (f'<div class="s-note">คำนวณการเรียนรู้ใหม่จาก {em["replayed"]} นัด · Rule ที่ระบบสร้างเอง {em["rules_before"]} → {em["rules_after"]}</div>')
    return S.plain(head + card("ผลของการคำนวณการเรียนรู้ใหม่" + ("" if wc else " (น้ำหนัก Rule ไม่เปลี่ยน)"), body))


# ============================================================================ หน้าสำรองข้อมูล / ผู้ใช้
def sync_story(be_name, ok, err, last, n_hist, n_settled, n_rules, sheets):
    if not be_name:
        st_ = ("bad", "ยังไม่ได้เปิดซิงก์", "ข้อมูลจะหายเมื่อแอปรีสตาร์ท ตั้งค่าตามขั้นตอนด้านล่างครั้งเดียว")
    elif ok is False:
        st_ = ("bad", "ซิงก์มีปัญหา", err or "")
    else:
        st_ = ("ok", f"ซิงก์อัตโนมัติเปิดอยู่ · {be_name}", f"ซิงก์ล่าสุด {last or 'ยังไม่มีการซิงก์ในรอบนี้'}")
    k = {"ok": "w", "bad": "l"}[st_[0]]
    hero = (f'<div class="s-result {k} s-rv" style="text-align:left"><div class="s-kick">เก็บข้อมูลถาวร</div><div class="vd">{"☁️" if st_[0] == "ok" else "⚠️"} {e(st_[1])}</div>'
            f'<div class="s-sm" style="margin-top:4px">{e(st_[2])}</div>'
            + ('<div class="s-note">ใน Google Sheets มีชีต “ประวัติ” และ “น้ำหนัก Rule” ให้เปิดดูได้</div>' if sheets else "") + "</div>")
    kp = (f'<div class="s-kpis"><div class="s-kpi s-rv"><div class="t">รายการทั้งหมด</div><div class="v">{num(n_hist, 0)}</div></div>'
          f'<div class="s-kpi s-rv" style="--dl:.08s"><div class="t">บันทึกผลแล้ว</div><div class="v">{num(n_settled, 0)}</div></div>'
          f'<div class="s-kpi s-rv" style="--dl:.16s"><div class="t">Rule ที่ระบบสร้าง</div><div class="v">{num(n_rules, 0)}</div></div></div>')
    return S.plain(hero + kp)


def users_story(acc, admins, used_today, limit_of, role_th):
    users = acc.get("users") or {}
    total_today = sum(used_today(u) for u in users)
    kp = (f'<div class="s-kpis"><div class="s-kpi s-rv"><div class="t">Admin</div><div class="v">{num(len(admins), 0)}</div><div class="d">จาก Secrets</div></div>'
          f'<div class="s-kpi s-rv" style="--dl:.08s"><div class="t">User</div><div class="v">{num(sum(1 for u in users.values() if u["role"] == "user"), 0)}</div><div class="d">{acc["limits"]["user"]} ครั้ง/วัน</div></div>'
          f'<div class="s-kpi s-rv" style="--dl:.16s"><div class="t">Local</div><div class="v">{num(sum(1 for u in users.values() if u["role"] == "local"), 0)}</div><div class="d">{acc["limits"]["local"]} ครั้ง/วัน</div></div>'
          f'<div class="s-kpi s-rv" style="--dl:.24s"><div class="t">วิเคราะห์วันนี้</div><div class="v">{num(total_today, 0)}</div><div class="d">รวมผู้ใช้ที่เชิญ</div></div></div>')
    cards = "".join(f'<div class="s-sel s-rv" style="cursor:default"><div class="tm" style="overflow-wrap:anywhere">{e(a)}</div>'
                    f'<div class="s-chips" style="margin-top:6px">{chip("Admin", "acc")}{chip("ไม่จำกัด", "off")}</div></div>' for a in sorted(admins))
    for i, (em, u) in enumerate(sorted(users.items())):
        lim = limit_of(u["role"]) or 0
        used = used_today(em)
        cards += (f'<div class="s-sel s-rv" style="cursor:default;--dl:{min(.04 * i, .5):.2f}s"><div class="tm" style="overflow-wrap:anywhere">{e(em)}</div>'
                  f'<div class="s-chips" style="margin:6px 0 8px">{chip(role_th[u["role"]], "ok" if u["role"] == "user" else "")}{chip("เชิญ " + str(u.get("added", "")), "off")}</div>'
                  f'<div class="s-brow" style="margin:0;grid-template-columns:auto 1fr auto"><span class="s-xs s-mut">ใช้วันนี้</span>'
                  f'{bar(used / lim if lim else 1, "r" if lim and used >= lim else "t")}<span class="n s-sm">{used}/{lim}</span></div></div>')
    log = acc.get("log") or []
    tl = ""
    act_th = {"invite": "เชิญ", "role": "เปลี่ยนระดับ", "remove": "ลบ", "limits": "ตั้งโควตา", "reset": "รีเซ็ตโควตา"}
    for x in list(reversed(log))[:12]:
        tl += f'<div class="it"><div>{e(act_th.get(x[2], x[2]))} {e(x[3])} {e(x[4])}<small>{e(x[0])} · โดย {e(x[1])}</small></div></div>'
    body = kp + f'<div class="s-pickgrid" style="margin-top:14px">{cards}</div>'
    if tl:
        body += card("ประวัติการจัดการผู้ใช้", f'<div class="s-tl">{tl}</div>')
        body = body.replace('class="s-card s-rv', 'style="margin-top:14px" class="s-card s-rv', 1)
    return S.plain(body)
