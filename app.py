# -*- coding: utf-8 -*-
"""Football Quant V5.8 — Streamlit UI (ใช้ engine จาก football_quant_v58.py)"""
import hmac
import json
import os
import tempfile
import time

import streamlit as st

import football_quant_v58 as q

st.set_page_config(page_title="Football Quant V5.8", page_icon="⚽", layout="wide")
DATA_DIR = os.environ.get("QUANT_DATA_DIR", "quant_data")


def secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name)


# ---------------------------------------------------------------- รหัสผ่าน (ถ้าตั้งไว้)
_pw = secret("APP_PASSWORD")
if _pw and not st.session_state.get("auth"):
    st.title("⚽ Football Quant V5.8")
    entered = st.text_input("รหัสผ่าน", type="password")
    if entered:
        if hmac.compare_digest(str(entered), str(_pw)):
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.header("⚙ ตั้งค่า")
    api_key = secret("ANTHROPIC_API_KEY") or st.text_input("ANTHROPIC_API_KEY", type="password",
                                                           help="ใช้อ่านรูปเท่านั้น ไม่ถูกบันทึก")
    model = st.text_input("โมเดลอ่านรูป", value=os.environ.get("QUANT_MODEL", q.DEFAULT_MODEL))
    st.subheader("บริบทแมตช์ (override)")
    ctx_over = {
        "derby": st.checkbox("ดาร์บี้แมตช์"),
        "high_volatility": st.checkbox("ลีกผันผวนสูง"),
        "high_scoring_league": st.checkbox("ลีกประตูเยอะ"),
        "cup_group_stage": st.checkbox("บอลถ้วยรอบแบ่งกลุ่ม"),
        "knockout": st.checkbox("น็อคเอาต์/เพลย์ออฟ"),
        "late_goal_tendency": st.checkbox("แนวโน้มยิงท้ายเกมสูง"),
    }
    desp = st.selectbox("Desperation (หนีตาย/ลุ้นแชมป์)", ["ไม่มี", "เจ้าบ้าน", "ทีมเยือน"])
    st.caption("⚠ บน Streamlit Cloud ไฟล์ในเครื่องจะหายเมื่อแอปรีสตาร์ท "
               "ให้สำรองข้อมูลที่แท็บ 💾 สำรอง/กู้คืน เป็นประจำ")

st.title("⚽ Football Quant V5.8 — Self-Learning")
tab1, tab2, tab3, tab4 = st.tabs(["🎯 วิเคราะห์", "🏁 ใส่ผลจริง (เรียนรู้)", "📈 สถิติ & Rule", "💾 สำรอง/กู้คืน"])

# ================================================================ TAB 1
with tab1:
    st.subheader("1) อ่านรูปตารางราคา (ปกติ 5 รูป)")
    files = st.file_uploader("ภาพสรุปแมตช์/ฟอร์ม, 1X2, Handicap, Over/Under, H2H",
                             type=["png", "jpg", "jpeg", "webp", "gif"], accept_multiple_files=True)
    if st.button("🖼 อ่านรูปด้วย Claude", disabled=not files):
        if not api_key:
            st.error("ต้องใส่ ANTHROPIC_API_KEY (Secrets หรือช่องใน Sidebar)")
        else:
            with st.spinner("กำลังอ่านรูป..."):
                try:
                    with tempfile.TemporaryDirectory() as td:
                        paths = []
                        for i, uf in enumerate(files, 1):
                            p = os.path.join(td, f"{i}_{os.path.basename(uf.name)}")
                            with open(p, "wb") as fh:
                                fh.write(uf.getbuffer())
                            paths.append(p)
                        m = q.extract_from_images(paths, model, api_key)
                    st.session_state["ext_warn"] = m.pop("warnings", None) or []
                    st.session_state["match_json"] = json.dumps(m, ensure_ascii=False, indent=2)
                    st.success("อ่านรูปสำเร็จ ตรวจสอบตัวเลขด้านล่างก่อนวิเคราะห์")
                except SystemExit as e:
                    st.error(str(e.code))
                except Exception as e:  # noqa
                    st.error(f"เกิดข้อผิดพลาด: {e}")

    st.subheader("2) ตรวจ/แก้ข้อมูล")
    with st.expander("หรือโหลดไฟล์ JSON / ตัวอย่าง"):
        jf = st.file_uploader("ไฟล์ JSON ของแมตช์", type=["json"], key="jsonfile")
        c1, c2 = st.columns(2)
        if c1.button("โหลดไฟล์ JSON ที่อัปโหลด", disabled=jf is None):
            st.session_state["match_json"] = jf.getvalue().decode("utf-8")
            st.session_state["ext_warn"] = []
        if c2.button("โหลดตัวอย่าง (Portland vs Houston)"):
            with open("example_match.json", encoding="utf-8") as fh:
                d = json.load(fh)
            st.session_state["ext_warn"] = d.pop("warnings", [])
            st.session_state["match_json"] = json.dumps(d, ensure_ascii=False, indent=2)
    st.session_state.setdefault("match_json", json.dumps(q.TEMPLATE, ensure_ascii=False, indent=2))
    st.text_area("ข้อมูลแมตช์ (JSON) — เรต HDP/OU มองจากฝั่งเจ้าบ้าน (ลบ = เจ้าบ้านต่อ)", key="match_json", height=380)

    save = st.checkbox("บันทึกสัญญาณลงประวัติ (เพื่อใส่ผลจริงทีหลัง)", value=True)
    if st.button("🎯 วิเคราะห์และฟันธง", type="primary"):
        try:
            m = json.loads(st.session_state["match_json"])
        except json.JSONDecodeError as e:
            m = None
            st.error(f"JSON ไม่ถูกต้อง: {e}")
        if m is not None:
            m.pop("warnings", None)
            try:
                m, warns = q.validate_match(m)
            except ValueError as e:
                m = None
                st.error(f"ข้อมูลไม่ครบ/ไม่ถูกต้อง: {e}")
        if m is not None:
            m["context"].update({k: True for k, v in ctx_over.items() if v})
            if desp != "ไม่มี":
                m["context"]["desperation"] = "home" if desp == "เจ้าบ้าน" else "away"
            store = q.Store(DATA_DIR)
            f, contribs, pick = q.analyze_match(m, store)
            for w in (st.session_state.get("ext_warn") or []) + warns:
                st.warning(w)
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.metric("🎯 สัญญาณฟันธงเดี่ยว", pick["label"])
            c2.metric("ความมั่นใจ", f"{pick['confidence']:.0f}%")
            c3.metric("ระดับ", pick["tier"])
            if pick["tier"] == "ต่ำ":
                st.info("สัญญาณอ่อน: ระบบถูกบังคับให้ฟันธง (Rule 13) ควรลดสัดส่วนเงินเดิมพัน")
            st.code(q.render_report(m, f, contribs, pick, store), language=None)
            with st.expander("รายละเอียดคะแนนของแต่ละ Rule"):
                st.dataframe(contribs)
            if save:
                mid, ok = q.record_prediction(store, m, f, contribs, pick)
                if ok:
                    st.success(f"บันทึกแล้ว id = {mid} → ไปใส่ผลจริงที่แท็บ 🏁 หลังจบเกม")
                else:
                    st.warning(f"ไม่บันทึก: id '{mid}' ถูก settle ไปแล้ว (เปลี่ยน id ในช่อง JSON)")

# ================================================================ TAB 2
with tab2:
    store = q.Store(DATA_DIR)
    pend = {r["id"]: r for r in store.history if r["status"] == "pending"}
    if not pend:
        st.info("ยังไม่มีสัญญาณที่รอผล (วิเคราะห์ในแท็บแรกโดยติ๊กบันทึกก่อน)")
    else:
        rid = st.selectbox("เลือกแมตช์ที่จบแล้ว", list(pend),
                           format_func=lambda i: f"{pend[i]['features']['home']} vs {pend[i]['features']['away']} — {pend[i]['pick']['label']}")
        rec = pend[rid]
        c1, c2 = st.columns(2)
        hg = c1.number_input(f"ประตู {rec['features']['home']} (เหย้า)", 0, 30, 0)
        ag = c2.number_input(f"ประตู {rec['features']['away']} (เยือน)", 0, 30, 0)
        if st.button("✅ บันทึกผลจริง & ให้ระบบเรียนรู้", type="primary"):
            outcomes, r, pf, changes, new = q.do_settle(store, rec, int(hg), int(ag))
            (st.success if r > 0 else st.error if r < 0 else st.info)(
                f"สัญญาณ {rec['pick']['label']} → {q.result_word(r)} ({pf:+.2f} หน่วย)")
            st.write("**Post-Mortem ทุกตลาด**")
            st.dataframe([{"ตลาด": k, "ผล": q.result_word(v[0])} for k, v in outcomes.items()])
            if changes:
                st.write("**ปรับน้ำหนัก Rule**")
                st.dataframe([{"Rule": k, "ชื่อ": q.RULE_NAMES.get(k, "Learned Rule"), "เดิม": round(o, 3),
                               "ใหม่": round(n, 3), "ความถูกต้อง": round(rr, 2)} for k, (o, n, rr) in changes.items()])
            for r_ in new:
                st.success(f"🧠 Rule ใหม่ {r_['id']}: ถ้า [{' + '.join(r_['tags'])}] → {q.ROLE_TH[r_['role']]} "
                           f"(ชนะ {r_['wr']:.0%} จาก {r_['n']} นัด)")

# ================================================================ TAB 3
with tab3:
    store = q.Store(DATA_DIR)
    S = store.state
    done = [r for r in store.history if r["status"] == "settled"]
    pend_n = sum(1 for r in store.history if r["status"] == "pending")
    if done:
        w = sum(r["pick_r"] > 0 for r in done)
        l = sum(r["pick_r"] < 0 for r in done)
        pr = sum(r["pick_profit"] for r in done)
        c = st.columns(5)
        c[0].metric("settle แล้ว", len(done))
        c[1].metric("รอผล", pend_n)
        c[2].metric("ชนะ/แพ้", f"{w}/{l}")
        c[3].metric("กำไรสุทธิ", f"{pr:+.2f}")
        c[4].metric("ROI ต่อไม้", f"{pr / len(done):+.1%}")
    else:
        st.info(f"ยังไม่มีผลที่ settle (รอผล {pend_n} นัด)")
    st.subheader("น้ำหนัก Rule")
    st.dataframe([{"Rule": k, "ชื่อ": q.RULE_NAMES.get(k, "Learned Rule"), "น้ำหนัก": round(v, 3),
                   "ใช้(ครั้ง)": S["rule_stats"].get(k, {}).get("n", 0),
                   "avg r": round(S["rule_stats"].get(k, {}).get("sum_r", 0) / max(S["rule_stats"].get(k, {}).get("n", 0), 1), 2)}
                  for k, v in sorted(S["weights"].items())])
    st.subheader("🧠 Rule ที่ระบบสร้างเอง")
    if S["learned_rules"]:
        st.dataframe([{"id": r["id"], "สถานะ": "ON" if r.get("enabled", True) else "OFF",
                       "เงื่อนไข": " + ".join(r["tags"]), "เล่น": q.ROLE_TH[r["role"]],
                       "ชนะ": f"{r['wr']:.0%}", "จำนวนนัด": r["n"], "strength": r["strength"]}
                      for r in S["learned_rules"]])
    else:
        st.caption("ยังไม่มี (ต้องสะสมผลจริงอย่างน้อย ~10 นัดที่มีรูปแบบซ้ำกัน)")
    if st.button("🔍 ค้นหา Rule ใหม่จากประวัติอีกครั้ง"):
        new = q.discover_rules(store, verbose=False)
        store.save()
        st.success(f"สร้าง Rule ใหม่ {len(new)} ข้อ") if new else st.info("ยังไม่พบรูปแบบใหม่ที่มีนัยสำคัญ")
    st.subheader("ประวัติ")
    st.dataframe([{"id": r["id"], "คู่": f"{r['features']['home']} vs {r['features']['away']}",
                   "สัญญาณ": r["pick"]["label"], "สถานะ": r["status"],
                   "สกอร์": "-".join(map(str, r.get("score", []))) or "-",
                   "ผล": q.result_word(r["pick_r"]) if r["status"] == "settled" else "-",
                   "กำไร": r.get("pick_profit", "")} for r in reversed(store.history)])

# ================================================================ TAB 4
with tab4:
    store = q.Store(DATA_DIR)
    st.write("สำรองข้อมูลการเรียนรู้ (น้ำหนัก Rule, Rule ที่สร้างเอง, ประวัติ) เป็นไฟล์เดียว")
    blob = json.dumps({"state": store.state, "history": store.history}, ensure_ascii=False, indent=1)
    st.download_button("⬇ ดาวน์โหลดไฟล์สำรอง", blob, file_name=f"quant_backup_{time.strftime('%Y%m%d')}.json",
                       mime="application/json")
    up = st.file_uploader("กู้คืนจากไฟล์สำรอง (จะเขียนทับข้อมูลปัจจุบัน)", type=["json"], key="restore")
    if up is not None and st.button("♻ กู้คืน", type="primary"):
        try:
            d = json.loads(up.getvalue().decode("utf-8"))
            assert "state" in d and "history" in d
            store.state, store.history = d["state"], d["history"]
            for k, v in q.DEFAULT_WEIGHTS.items():
                store.state["weights"].setdefault(k, v)
            store.save()
            st.success("กู้คืนสำเร็จ")
        except Exception as e:  # noqa
            st.error(f"ไฟล์ไม่ถูกต้อง: {e}")
