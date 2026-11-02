#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant V5.8 (Advanced Volatility, Trap Shield & Class Superiority Edition)
+ Self-Learning Rule Engine

ทำอะไรได้บ้าง
  1) analyze : วิเคราะห์ตารางราคา (1X2 / HDP / OU) ตาม Rule 1-16 แล้ว "ฟันธงเดี่ยว" 1 ตัวเลือก
  2) settle  : ใส่สกอร์จริง -> Post-Match Post-Mortem -> ปรับน้ำหนักแต่ละ Rule อัตโนมัติ
               และ "สร้าง Rule ใหม่" (Learned Rules) จากรูปแบบที่ชนะ/แพ้ซ้ำ ๆ
  3) learn   : รันการค้นหา Rule ใหม่จากประวัติทั้งหมดอีกครั้ง
  4) stats   : ดูผลงาน, ROI, น้ำหนักของแต่ละ Rule, Rule ที่ระบบสร้างเอง
  5) template: พิมพ์ไฟล์ JSON ตัวอย่างสำหรับกรอกข้อมูลแมตช์
  6) images  : นำเข้ารูปภาพ 5 รูป -> Claude Vision สกัดค่าราคา/H2H/สถิติ -> ตรวจสอบ -> วิเคราะห์
               (ต้องตั้ง ANTHROPIC_API_KEY)

ใช้ไลบรารีมาตรฐานของ Python เท่านั้น (ไม่ต้องติดตั้งอะไรเพิ่ม)

ตัวอย่าง
  python football_quant_v58.py template > match.json
  python football_quant_v58.py analyze match.json
  python football_quant_v58.py settle <match_id> 2-1
  python football_quant_v58.py stats
  python football_quant_v58.py images 1.png 2.png 3.png 4.png 5.png --derby

หมายเหตุ: เครื่องมือนี้เป็นโมเดลเชิงสถิติ/ฮิวริสติก ไม่รับประกันผลลัพธ์
"""
from __future__ import annotations

import argparse
import base64
import itertools
import json
import math
import os
import re
import statistics
import sys
import time
from collections import Counter
import urllib.error
import urllib.request

# ----------------------------------------------------------------------------
# 0) ค่าพารามิเตอร์ และน้ำหนักเริ่มต้นของ Rule
# ----------------------------------------------------------------------------
DEFAULT_PARAMS = {
    "hdp_pp_per_quarter": 4.0,   # เรตขยับ 0.25 ลูก ~ เปลี่ยนความน่าจะเป็นชนะ ~4 จุด %
    "decouple_threshold": 0.20,  # Rule 11/15: ความขัดแย้งพูล vs แฮนดิแคป > 20%
    "decouple_min_pp": 3.0,      # และต้องต่างกันอย่างน้อย 3 จุด %
    "crash_min": 0.25,           # เรตร่วงอย่างน้อย 0.25 ถึงเรียก Crash
    "water_drop_min": 0.06,      # ค่าน้ำลดอย่างน้อย 0.06 ถึงนับเป็น Silent Money
    "x12_flat_pp": 1.0,
    "x12_steam_pp": 3.0,
    "ou_gap": 0.35,
    "leak_ga": 1.5,              # เสียประตูเฉลี่ย >= 1.5 ถือว่ารั่ว
    "class_ratio": 2.0,          # Rule 14: มูลค่าทีม > 2 เท่า
    "derby_stat_factor": 0.75,   # Rule 10: ลดน้ำหนักกฎสถิติ 25% ในดาร์บี้
    "noise_factor": 0.30,        # Rule 11: ลดน้ำหนัก Rule 1/9 เมื่อเป็นแค่ Public noise
    # --- การเรียนรู้ ---
    "lr": 0.15, "lr_min": 0.03, "decay": 0.01, "w_min": 0.2, "w_max": 3.0,
    "disc_min_n": 10,            # ต้องมีตัวอย่างอย่างน้อยกี่นัดถึงจะสร้าง Rule ใหม่
    "disc_z": 1.645,             # ความเชื่อมั่น ~90% (Wilson interval)
    "disc_max_combo": 3,         # รวมเงื่อนไข (tags) ได้สูงสุดกี่ตัวต่อ 1 Rule
    "disc_max_new": 5,           # สร้าง Rule ใหม่สูงสุดต่อรอบ
    "disc_max_total": 40,
    "learned_base": 1.5,
}

DEFAULT_WEIGHTS = {
    "R1": 1.0, "R2": 1.5, "R3": 1.0, "R4": 1.0, "R5": 1.0, "R6": 1.0, "R7": 1.0,
    "R8": 1.0, "R9": 1.0, "R10": 1.0, "R11": 1.0, "R12": 1.0, "R14": 1.5, "R16": 1.0,
}

RULE_NAMES = {
    "R1": "Noisy Crash (กรองด้วย 1X2 Anchor)",
    "R2": "Silent Money Supremacy",
    "R3": "Volatility & Defensive Leakage",
    "R4": "Cup Group Stage Conservatism",
    "R5": "H2H & Public Bias",
    "R6": "Desperation Index",
    "R7": "Playoff Pressure",
    "R8": "Dynamic OU Filtering",
    "R9": "Anti-Fake Steam Matrix",
    "R10": "Derby Volatility Calibration",
    "R11": "Refined Decoupling Filter (Rule 11/15)",
    "R12": "Away Favorite Volatility Guard",
    "R14": "Class Superiority Override",
    "R16": "Late-Goal Buffer for Derbies",
}
STAT_RULES = {"R3", "R5", "R8"}          # กฎที่อิงสถิติ -> ถูกลดน้ำหนักในดาร์บี้ (Rule 10)
NOISE_RULES = {"R1", "R9"}               # กฎที่ถูกลดน้ำหนักเมื่อความขัดแย้ง <= 20% (Rule 11)

ROLE_TH = {
    "HDP_FAV": "แฮนดิแคป ทีมต่อ", "HDP_DOG": "แฮนดิแคป ทีมรอง",
    "OU_OVER": "สูง (Over)", "OU_UNDER": "ต่ำ (Under)", "X12_FAV": "1X2 ทีมต่อชนะ",
}
ALL_MARKETS = ["HDP_HOME", "HDP_AWAY", "OU_OVER", "OU_UNDER", "X12_HOME", "X12_AWAY"]


# ----------------------------------------------------------------------------
# 1) เครื่องมือช่วย
# ----------------------------------------------------------------------------
def implied(odds):
    inv = [1.0 / o for o in odds]
    s = sum(inv)
    return [x / s for x in inv]


def fmt_line(x):
    return "0" if abs(x) < 1e-9 else f"{x:+g}"


def slug(s):
    return re.sub(r"[^0-9A-Za-z\u0E00-\u0E7F]+", "-", str(s)).strip("-")


def sign(x, eps=1e-9):
    return (x > eps) - (x < -eps)


def wilson(p, n, z):
    if n == 0:
        return 0.0, 1.0
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0))
    return (c - a) / d, (c + a) / d


def split_line(x):
    """ราคาเอเชียนแบบ .25/.75 แบ่งเป็น 2 ครึ่ง"""
    q = round(x * 4)
    if q % 2 == 0:
        return [x]
    return [(q - 1) / 4.0, (q + 1) / 4.0]


# ----------------------------------------------------------------------------
# 2) สกัด Feature จากข้อมูลแมตช์ (Step 1: Data Extraction & Context)
# ----------------------------------------------------------------------------
def build_features(m, P):
    ctx = m.get("context", {}) or {}
    st = m.get("stats", {}) or {}
    home, away = m.get("home", "Home"), m.get("away", "Away")

    x12 = m["x12"]
    po, pc = implied(x12["open"]), implied(x12["current"])
    hdp = m["hdp"]
    lo, lc = float(hdp["open"]["line"]), float(hdp["current"]["line"])

    if lc < 0:
        fav = "home"
    elif lc > 0:
        fav = "away"
    else:
        fav = "home" if x12["current"][0] <= x12["current"][2] else "away"
    dog = "away" if fav == "home" else "home"
    fdir = 1 if fav == "home" else -1
    fav_idx, dog_idx = (0, 2) if fav == "home" else (2, 0)

    f = {
        "home": home, "away": away, "league": m.get("league", ""),
        "fav": fav, "dog": dog, "fav_name": home if fav == "home" else away,
        "dog_name": home if dog == "home" else away,
        "fav_hdp": "HDP_" + fav.upper(), "dog_hdp": "HDP_" + dog.upper(),
        "fav_x12": "X12_" + fav.upper(), "dog_x12": "X12_" + dog.upper(),
        "line_o": lo, "line_c": lc, "fav_line_c": abs(lc), "fav_line_o": abs(lo),
        "x12_open": x12["open"], "x12_cur": x12["current"],
    }

    # --- HDP ---
    f["hdp_shift_fav"] = fdir * ((-lc) - (-lo))        # + = ทีมต่อแรงขึ้น, - = เรตร่วง
    ho, hc = hdp["open"], hdp["current"]
    fo = ho["home_water"] if fav == "home" else ho["away_water"]
    fc = hc["home_water"] if fav == "home" else hc["away_water"]
    do = ho["away_water"] if fav == "home" else ho["home_water"]
    dc = hc["away_water"] if fav == "home" else hc["home_water"]
    f["fav_drop"], f["dog_drop"] = fo - fc, do - dc    # + = ค่าน้ำลด
    f["fav_water_c"], f["dog_water_c"] = fc, dc

    # --- 1X2 anchor ---
    f["x12_pp"] = (pc[fav_idx] - po[fav_idx]) * 100
    f["dog_pp"] = (pc[dog_idx] - po[dog_idx]) * 100
    f["hdp_pp"] = f["hdp_shift_fav"] / 0.25 * P["hdp_pp_per_quarter"]
    mx = max(abs(f["hdp_pp"]), abs(f["x12_pp"]))
    f["conflict"] = 0.0 if mx < 2.0 else abs(f["hdp_pp"] - f["x12_pp"]) / mx
    f["conflict_pp"] = f["hdp_pp"] - f["x12_pp"]

    # --- OU ---
    ou = m.get("ou")
    f["has_ou"] = bool(ou)
    if ou:
        f["ou_o"], f["ou_c"] = float(ou["open"]["line"]), float(ou["current"]["line"])
        f["ou_shift"] = f["ou_c"] - f["ou_o"]
        f["over_drop"] = ou["open"]["over"] - ou["current"]["over"]
        f["under_drop"] = ou["open"]["under"] - ou["current"]["under"]
        f["over_water_c"], f["under_water_c"] = ou["current"]["over"], ou["current"]["under"]

    # --- สถิติ / H2H / มูลค่าทีม ---
    g = lambda k: st.get(k)
    fav_ga = g("home_ga") if fav == "home" else g("away_ga")
    dog_ga = g("away_ga") if fav == "home" else g("home_ga")
    f["fav_ga"], f["dog_ga"] = fav_ga, dog_ga
    f["exp_total"] = None
    if all(g(k) is not None for k in ("home_gf", "home_ga", "away_gf", "away_ga")):
        f["exp_total"] = (g("home_gf") + g("away_ga")) / 2 + (g("away_gf") + g("home_ga")) / 2

    h2h = m.get("h2h") or []
    fw = dw = dr = 0
    tot = 0
    for e in h2h:
        same = e.get("home_is_current_home", True)
        fg = e["hg"] if (fav == "home") == same else e["ag"]
        dg = e["ag"] if (fav == "home") == same else e["hg"]
        fw += fg > dg
        dw += dg > fg
        dr += fg == dg
        tot += e["hg"] + e["ag"]
    f["h2h_n"], f["h2h_fav_w"], f["h2h_dog_w"], f["h2h_draw"] = len(h2h), fw, dw, dr
    f["h2h_avg_total"] = tot / len(h2h) if h2h else None

    tv = m.get("team_value") or {}
    f["class_sup"] = False
    f["value_ratio"] = None
    if tv.get("home") and tv.get("away"):
        fv, dv = (tv["home"], tv["away"]) if fav == "home" else (tv["away"], tv["home"])
        f["value_ratio"] = fv / dv
        f["class_sup"] = f["value_ratio"] >= P["class_ratio"] and 0.5 <= f["fav_line_o"] <= 1.0

    # --- บริบท ---
    f["ctx_type"] = ctx.get("type", "league")
    f["derby"] = bool(ctx.get("derby"))
    f["high_vol"] = bool(ctx.get("high_volatility"))
    f["high_scoring"] = bool(ctx.get("high_scoring_league"))
    f["cup_group"] = bool(ctx.get("cup_group_stage"))
    f["knockout"] = bool(ctx.get("knockout")) or f["ctx_type"] == "playoff"
    f["desperation"] = ctx.get("desperation")           # "home"/"away"/None
    f["late_goal"] = bool(ctx.get("late_goal_tendency"))
    pub = m.get("public_pct") or {}                      # % ของเงินเดิมพันมหาชน (ถ้ามี)
    f["public_fav"] = pub.get("home" if fav == "home" else "away")
    f["public_dog"] = pub.get("home" if dog == "home" else "away")

    f["form"] = m.get("form")
    f["n_books"] = m.get("n_books")
    f["tags"] = make_tags(f, P)
    return f


def make_tags(f, P):
    t = [f"ctx:{f['ctx_type']}", f"fav:{f['fav']}"]
    for flag, name in (("derby", "derby"), ("high_vol", "high_vol"), ("high_scoring", "high_scoring"),
                       ("cup_group", "cup_group"), ("knockout", "knockout"), ("class_sup", "class_sup")):
        if f[flag]:
            t.append(name)
    if f["desperation"]:
        t.append("desperation:" + ("fav" if f["desperation"] == f["fav"] else "dog"))
    a = f["fav_line_c"]
    t.append("line:pk" if a <= 0.25 else "line:half" if a <= 0.75 else "line:one" if a <= 1.25 else "line:big")
    s = f["hdp_shift_fav"]
    t.append("hdp:crash" if s <= -0.25 else "hdp:rise" if s >= 0.25 else "hdp:stable")
    if abs(s) < 0.01:
        if f["fav_drop"] >= P["water_drop_min"] and f["fav_drop"] >= f["dog_drop"]:
            t.append("water:fav_drop")
        elif f["dog_drop"] >= P["water_drop_min"]:
            t.append("water:dog_drop")
    x = f["x12_pp"]
    t.append("x12:fav_up" if x >= 2 else "x12:fav_down" if x <= -2 else "x12:flat")
    if f["conflict"] > P["decouple_threshold"] and abs(f["conflict_pp"]) >= P["decouple_min_pp"]:
        t.append("decoupled")
    if f["has_ou"]:
        c = f["ou_c"]
        t.append("ou:low" if c <= 2.25 else "ou:mid" if c <= 2.75 else "ou:high")
        if abs(f["ou_shift"]) >= 0.25:
            t.append("ou_move:" + ("up" if f["ou_shift"] > 0 else "down"))
        if abs(f["ou_shift"]) < 0.01:
            if f["over_drop"] >= P["water_drop_min"]:
                t.append("ou_water:over_drop")
            elif f["under_drop"] >= P["water_drop_min"]:
                t.append("ou_water:under_drop")
        if f["exp_total"] is not None:
            d = f["exp_total"] - c
            if d >= P["ou_gap"]:
                t.append("exp:over")
            elif d <= -P["ou_gap"]:
                t.append("exp:under")
    if f["h2h_n"] >= 3:
        r = (f["h2h_fav_w"] - f["h2h_dog_w"]) / f["h2h_n"]
        if r >= 0.6:
            t.append("h2h:fav_dom")
        elif r <= -0.6:
            t.append("h2h:dog_dom")
    if f["public_fav"] is not None and f["public_fav"] >= 65:
        t.append("public:fav")
    if f["public_dog"] is not None and f["public_dog"] >= 65:
        t.append("public:dog")
    return sorted(set(t))


# ----------------------------------------------------------------------------
# 3) Rule 1-16  (แต่ละ Rule คืนรายการ (rule_id, market, value>0, note))
# ----------------------------------------------------------------------------
def rule1(f, P):
    s = f["hdp_shift_fav"]
    if s > -P["crash_min"]:
        return []
    mag = min(abs(s) / 0.25, 4) * 0.5
    if f["x12_pp"] > -2 * P["x12_flat_pp"]:
        return [("R1", f["fav_hdp"], mag,
                 f"HDP ร่วง {s:+g} ลูก แต่พูล 1X2 ไม่ตามลง ({f['x12_pp']:+.1f}pp) -> Noisy Crash ให้ Fade (หนุนทีมต่อ)")]
    return [("R1", f["fav_hdp"], mag * 0.25,
             f"HDP ร่วง {s:+g} และ 1X2 ตามลง ({f['x12_pp']:+.1f}pp) -> ลดความเด็ดขาดของการ Fade")]


def rule2(f, P):
    out = []
    unit = P["water_drop_min"]
    if abs(f["hdp_shift_fav"]) < 0.01:
        fd, dd = f["fav_drop"], f["dog_drop"]
        side, v = ("fav", fd) if fd >= dd else ("dog", dd)
        if v >= unit:
            mk = f["fav_hdp"] if side == "fav" else f["dog_hdp"]
            nm = f["fav_name"] if side == "fav" else f["dog_name"]
            out.append(("R2", mk, min(v / unit, 3.0),
                        f"Silent Money: เรตนิ่ง {fmt_line(f['line_c'])} แต่น้ำฝั่ง {nm} ลดลง {v:.2f}"))
    if f["has_ou"] and abs(f["ou_shift"]) < 0.01:
        od, ud = f["over_drop"], f["under_drop"]
        mk, v = ("OU_OVER", od) if od >= ud else ("OU_UNDER", ud)
        if v >= unit:
            out.append(("R2", mk, min(v / unit, 3.0) * 0.8,
                        f"Silent Money (OU): เรตสกอร์รวมนิ่ง {f['ou_c']:g} น้ำฝั่ง {mk[3:]} ลด {v:.2f}"))
    return out


def rule3(f, P):
    if not f["high_vol"]:
        return []
    out = []
    fl = f["fav_ga"] is not None and f["fav_ga"] >= P["leak_ga"]
    dl = f["dog_ga"] is not None and f["dog_ga"] >= P["leak_ga"]
    if fl and dl:
        out.append(("R3", "OU_OVER", 1.5, "ลีกผันผวนสูง + ทั้งสองทีมเสียประตูรั่ว -> Over"))
    elif fl:
        out.append(("R3", f["dog_hdp"], 1.2, f"ลีกผันผวนสูง ทีมต่อเสียเฉลี่ย {f['fav_ga']:.2f} -> เกมรับรั่วเหนือกว่าการไหลของราคา"))
        out.append(("R3", "OU_OVER", 0.8, "เกมรับทีมต่อรั่ว หนุน Over"))
    elif dl:
        out.append(("R3", f["fav_hdp"], 0.6, f"ทีมรองเสียเฉลี่ย {f['dog_ga']:.2f} ในลีกผันผวนสูง"))
        out.append(("R3", "OU_OVER", 0.8, "เกมรับทีมรองรั่ว หนุน Over"))
    return out


def rule4(f, P):
    if not f["cup_group"]:
        return []
    a = f["fav_line_c"]
    if a >= 1.25:
        return [("R4", f["dog_hdp"], (a - 1.0) * 1.5, f"บอลถ้วยรอบแบ่งกลุ่ม ต่อแพง {a:g} -> ห้ามถือหาง มองทีมรอง")]
    if a <= 0.5:
        return [("R4", f["dog_hdp"], 0.3, "บอลถ้วยเรตปริ่มน้ำ -> เน้นมองรอง/ต่ำ"), ("R4", "OU_UNDER", 0.3, "บอลถ้วยรอบแบ่งกลุ่ม เน้นเกมระมัดระวัง")]
    return []


def rule5(f, P):
    out = []
    n = f["h2h_n"]
    if n >= 3:
        r = (f["h2h_fav_w"] - f["h2h_dog_w"]) / n
        lure = f["hdp_shift_fav"] > 0 or f["fav_drop"] < -0.04
        if r >= 0.6 and lure:
            out.append(("R5", f["dog_hdp"], 0.8, f"H2H ทีมต่อเด่น ({f['h2h_fav_w']}/{n}) แต่ราคาถูกดันตามมหาชน -> ระวัง Public Bias ล่อเม่า"))
        elif r >= 0.6:
            out.append(("R5", f["fav_hdp"], 0.6 * r, f"H2H ทีมต่อเหนือกว่า {f['h2h_fav_w']}/{n} และราคาไม่ถูกล่อ"))
        elif r <= -0.6:
            out.append(("R5", f["dog_hdp"], 0.5 * -r, f"H2H ทีมรองเหนือกว่า {f['h2h_dog_w']}/{n}"))
        if f["has_ou"] and f["h2h_avg_total"] is not None:
            d = f["h2h_avg_total"] - f["ou_c"]
            if d >= 0.5:
                out.append(("R5", "OU_OVER", 0.4, f"H2H ประตูรวมเฉลี่ย {f['h2h_avg_total']:.1f} สูงกว่าเรต {f['ou_c']:g}"))
            elif d <= -0.5:
                out.append(("R5", "OU_UNDER", 0.4, f"H2H ประตูรวมเฉลี่ย {f['h2h_avg_total']:.1f} ต่ำกว่าเรต {f['ou_c']:g}"))
    return out


def rule6(f, P):
    d = f["desperation"]
    if d in ("home", "away"):
        return [("R6", "HDP_" + d.upper(), 0.9, f"Desperation Index: ทีม{'เจ้าบ้าน' if d == 'home' else 'เยือน'}มีแรงจูงใจสูง (หนีตาย/ลุ้นแชมป์/โควตา)")]
    return []


def rule7(f, P):
    if f["knockout"]:
        return [("R7", "OU_UNDER", 0.6, "รอบน็อคเอาต์/เพลย์ออฟ เล่นระวังตัว"),
                ("R7", f["dog_hdp"], 0.4, "แรงกดดันสูง ต่อรองเรตได้เปรียบทีมรอง")]
    return []


def rule8(f, P):
    if not f["has_ou"] or f["exp_total"] is None:
        return []
    d = f["exp_total"] - f["ou_c"]
    if abs(d) < P["ou_gap"]:
        return []
    mag = min(abs(d) / P["ou_gap"], 3) * 0.6
    mk = "OU_OVER" if d > 0 else "OU_UNDER"
    return [("R8", mk, mag, f"ประตูรวมคาดการณ์จากสถิติรุก/รับ = {f['exp_total']:.2f} เทียบเรต {f['ou_c']:g} ({d:+.2f})")]


def rule9(f, P):
    """Anti-Fake Steam Matrix: แยก Silent Money ออกจาก Public Steam"""
    silent = abs(f["hdp_shift_fav"]) < 0.01 and max(f["fav_drop"], f["dog_drop"]) >= P["water_drop_min"]
    if silent:
        return []
    out = []
    for side, pp, pct, water_drop, mk_fade in (
        ("fav", f["x12_pp"], f["public_fav"], f["fav_drop"], f["dog_hdp"]),
        ("dog", f["dog_pp"], f["public_dog"], f["dog_drop"], f["fav_hdp"]),
    ):
        if pp >= P["x12_steam_pp"] and water_drop < P["water_drop_min"]:
            v = 0.6 + (0.4 if (pct is not None and pct >= 65) else 0.0)
            nm = f["fav_name"] if side == "fav" else f["dog_name"]
            out.append(("R9", mk_fade, v, f"Public Steam: พูล 1X2 ของ {nm} ไหล +{pp:.1f}pp โดยไม่มีลายเซ็น Silent Money -> Fade"))
    return out


def rule11(f, P):
    """Refined Decoupling Filter: จับ Super Trap เมื่อพูล vs แฮนดิแคป ขัดกัน > 20%"""
    if f["conflict"] > P["decouple_threshold"] and abs(f["conflict_pp"]) >= P["decouple_min_pp"]:
        mag = min(f["conflict"], 1.5) * 2.0
        if f["conflict_pp"] < 0:  # แฮนดิแคปอ่อนกว่าพูล -> ทีมต่อถูกตีราคาต่ำเกินไป
            return [("R11", f["fav_hdp"], mag,
                     f"Super Trap: HDP ({f['hdp_pp']:+.1f}pp) ขัดกับพูล 1X2 ({f['x12_pp']:+.1f}pp) ความขัดแย้ง {f['conflict']:.0%} -> พูลชี้ทีมต่อ")]
        return [("R11", f["dog_hdp"], mag,
                 f"Super Trap: HDP ({f['hdp_pp']:+.1f}pp) ขัดกับพูล 1X2 ({f['x12_pp']:+.1f}pp) ความขัดแย้ง {f['conflict']:.0%} -> พูลชี้ทีมรอง")]
    return []


def rule12(f, P):
    if f["fav"] == "away" and f["high_scoring"]:
        v = 0.8 + (0.4 if f["fav_line_c"] >= 0.75 else 0.0)
        return [("R12", f["dog_hdp"], v, "ทีมเยือนต่อในลีกประตูเยอะ -> ระวังสะดุดท้ายเกม ลดการถือหางทีมต่อ")]
    return []


def rule14(f, P):
    if f["class_sup"]:
        return [("R14", f["fav_hdp"], 2.0,
                 f"Class Superiority: มูลค่าทีมต่อ {f['value_ratio']:.1f}x ของคู่แข่ง เรตเปิด {f['fav_line_o']:g} -> ห้ามสวนรอง")]
    return []


def rule16(f, P):
    if f["derby"] and f["has_ou"]:
        out = [("R16", "OU_OVER", 0.6, "ดาร์บี้: เพิ่มตัวคูณความเสี่ยงสกอร์รวม เลี่ยงตลาด Under")]
        if f["ou_c"] <= 2.5 and f["late_goal"]:
            out.append(("R16", "OU_OVER", 0.6, "เรตสกอร์ต่ำ + แนวโน้มยิงท้ายเกมสูง -> เลี่ยง Under"))
        return out
    return []


RULES = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule11, rule12, rule14, rule16]
ROLE_TO_MARKET = lambda role, f: {
    "HDP_FAV": f["fav_hdp"], "HDP_DOG": f["dog_hdp"], "OU_OVER": "OU_OVER",
    "OU_UNDER": "OU_UNDER", "X12_FAV": f["fav_x12"]}[role]


# ----------------------------------------------------------------------------
# 4) State (น้ำหนัก + Rule ที่เรียนรู้) และ History
# ----------------------------------------------------------------------------
class Store:
    def __init__(self, d):
        self.dir = d
        os.makedirs(d, exist_ok=True)
        self.state_p = os.path.join(d, "state.json")
        self.hist_p = os.path.join(d, "history.json")
        self.state = self._load(self.state_p, {
            "weights": dict(DEFAULT_WEIGHTS), "rule_stats": {}, "learned_rules": [],
            "params": {}, "meta": {"next_learned": 1}})
        for k, v in DEFAULT_WEIGHTS.items():
            self.state["weights"].setdefault(k, v)
        self.history = self._load(self.hist_p, [])

    @staticmethod
    def _load(p, default):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return default

    def save(self):
        for p, obj in ((self.state_p, self.state), (self.hist_p, self.history)):
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)

    @property
    def params(self):
        p = dict(DEFAULT_PARAMS)
        p.update(self.state.get("params", {}))
        return p


# ----------------------------------------------------------------------------
# 5) Engine: รวมคะแนน + Single Best Pick (Rule 13)
# ----------------------------------------------------------------------------
def analyze_match(m, store):
    P, S = store.params, store.state
    f = build_features(m, P)
    raw = []                                         # (rule, market, value, note)
    for fn in RULES:
        raw += fn(f, P)
    for lr in S["learned_rules"]:                    # Rule ที่ระบบสร้างเอง
        if lr.get("enabled", True) and set(lr["tags"]) <= set(f["tags"]):
            mk = ROLE_TO_MARKET(lr["role"], f)
            raw.append((lr["id"], mk, lr["strength"],
                        f"Learned {lr['id']}: [{' + '.join(lr['tags'])}] -> {ROLE_TH[lr['role']]} (ชนะ {lr['wr']:.0%} จาก {lr['n']:.0f} นัด)"))
    if f["derby"]:                                   # Rule 10: อารมณ์ร่วมในสนาม
        raw.append(("R10", f["dog_hdp"], 0.3, "ดาร์บี้: ให้น้ำหนักอารมณ์สนามมากกว่าสถิติ (+ทีมรอง)"))
    raw = [r for r in raw if r[1] != "OU_OVER" and r[1] != "OU_UNDER" or f["has_ou"]]

    scores = {k: 0.0 for k in ALL_MARKETS}
    contribs = []
    for rid, mk, val, note in raw:
        w = S["weights"].get(rid, 1.0)
        mod = 1.0
        if f["derby"] and rid in STAT_RULES:
            mod *= P["derby_stat_factor"]            # Rule 10
        if rid in NOISE_RULES and f["conflict"] <= P["decouple_threshold"]:
            mod *= P["noise_factor"]                 # Rule 11: ตัดกระแส Public noise
        eff = val * w * mod
        scores[mk] += eff
        contribs.append({"rule": rid, "market": mk, "raw": round(val, 4), "eff": round(eff, 4), "note": note})

    # --- Veto (Rule 14 / Rule 16) ---
    veto = set()
    if f["class_sup"]:
        veto.add(f["dog_hdp"])
    if f["derby"] and f["has_ou"] and f["ou_c"] <= 2.5 and f["late_goal"]:
        veto.add("OU_UNDER")

    cands = []
    net_h = scores["HDP_HOME"] - scores["HDP_AWAY"]
    for side, v in (("HOME", net_h), ("AWAY", -net_h)):
        if v > 0 and f"HDP_{side}" not in veto:
            cands.append((f"HDP_{side}", v))
        if v > 0 and f["fav_line_c"] <= 0.75 and f"X12_{side}" not in veto:
            fac = 0.7 if side.lower() == f["fav"] else 0.45
            cands.append((f"X12_{side}", v * fac - 0.2))
    if f["has_ou"]:
        net_o = scores["OU_OVER"] - scores["OU_UNDER"]
        if net_o > 0 and "OU_OVER" not in veto:
            cands.append(("OU_OVER", net_o))
        if net_o < 0 and "OU_UNDER" not in veto:
            cands.append(("OU_UNDER", -net_o))
    cands = [c for c in cands if c[1] > 0]
    if not cands:                                    # Rule 13 บังคับฟันธง: fallback = ทีมต่อ
        cands = [(f["fav_hdp"], 0.01)]
    cands.sort(key=lambda x: -x[1])
    mk, strength = cands[0]
    conf = 50 + 35 * (1 - math.exp(-strength / 3.0))
    tier = "สูง" if strength >= 2.5 else "กลาง" if strength >= 1.2 else "ต่ำ"

    price, label = pick_label(m, f, mk)
    pick = {"market": mk, "strength": round(strength, 3), "confidence": round(conf, 1), "tier": tier,
            "label": label, "price_win": price, "veto": sorted(veto),
            "runner_up": [(c[0], round(c[1], 3)) for c in cands[1:3]]}
    return f, contribs, pick


def pick_label(m, f, mk):
    home, away = f["home"], f["away"]
    hc, lc = m["hdp"]["current"], f["line_c"]
    if mk == "HDP_HOME":
        return hc["home_water"], f"แฮนดิแคป {home} {fmt_line(lc)} @{hc['home_water']:.2f}"
    if mk == "HDP_AWAY":
        return hc["away_water"], f"แฮนดิแคป {away} {fmt_line(-lc)} @{hc['away_water']:.2f}"
    if mk == "OU_OVER":
        w = m["ou"]["current"]["over"]
        return w, f"สูง (Over) {f['ou_c']:g} @{w:.2f}"
    if mk == "OU_UNDER":
        w = m["ou"]["current"]["under"]
        return w, f"ต่ำ (Under) {f['ou_c']:g} @{w:.2f}"
    idx = 0 if mk == "X12_HOME" else 2
    o = m["x12"]["current"][idx]
    return o - 1.0, f"1X2 {home if idx == 0 else away} ชนะ @{o:.2f}"


# ----------------------------------------------------------------------------
# 6) รายงานภาษาไทย (Output Format ตาม SKILL)
# ----------------------------------------------------------------------------
def render_report(m, f, contribs, pick, store):
    L = []
    P = store.params
    L.append("=" * 64)
    L.append(f"⚽ {f['home']} vs {f['away']}  |  {f['league']}")
    L.append("=" * 64)
    L.append("\n📊 วิเคราะห์เจาะลึก V5.8 Reality Check")
    L.append(f"  • ทีมต่อ: {f['fav_name']} ({'เหย้า' if f['fav'] == 'home' else 'เยือน'})  เรตเปิด {fmt_line(f['line_o'])} -> ปัจจุบัน {fmt_line(f['line_c'])}"
             f"  (ทีมต่อ{'แรงขึ้น' if f['hdp_shift_fav'] > 0 else 'อ่อนลง' if f['hdp_shift_fav'] < 0 else 'คงที่'} {f['hdp_shift_fav']:+g})")
    L.append(f"  • ค่าน้ำทีมต่อ {f['fav_water_c']:.2f} (เปลี่ยน {-f['fav_drop']:+.2f}) | ทีมรอง {f['dog_water_c']:.2f} (เปลี่ยน {-f['dog_drop']:+.2f})")
    L.append(f"  • พูล 1X2 ทีมต่อ {f['x12_pp']:+.1f}pp | ทีมรอง {f['dog_pp']:+.1f}pp | ความขัดแย้งพูล↔HDP = {f['conflict']:.0%}"
             f" {'(เกินเกณฑ์ 20%)' if f['conflict'] > P['decouple_threshold'] else '(ต่ำกว่าเกณฑ์ -> ถือเป็น noise)'}")
    if f["has_ou"]:
        L.append(f"  • OU เรต {f['ou_o']:g} -> {f['ou_c']:g}  น้ำสูง {f['over_water_c']:.2f} / ต่ำ {f['under_water_c']:.2f}"
                 + (f"  | ประตูรวมคาดการณ์ {f['exp_total']:.2f}" if f["exp_total"] else ""))
    if f["h2h_n"]:
        L.append(f"  • H2H {f['h2h_n']} นัด: ทีมต่อชนะ {f['h2h_fav_w']} เสมอ {f['h2h_draw']} แพ้ {f['h2h_dog_w']}"
                 + (f" | ประตูรวมเฉลี่ย {f['h2h_avg_total']:.1f}" if f["h2h_avg_total"] else ""))
    if f["value_ratio"]:
        L.append(f"  • มูลค่าทีมต่อ/ทีมรอง = {f['value_ratio']:.1f}x")
    fm = f.get("form")
    if fm and fm.get("home") and fm.get("away"):
        for t, nm in (("home", f["home"]), ("away", f["away"])):
            x = fm[t]
            L.append(f"  • ฟอร์ม {nm}: {x.get('seq', '-')}  ได้ {x.get('gf', '-')} เสีย {x.get('ga', '-')}  ชนะ {x.get('win_rate', '-')}%")
    if f.get("n_books"):
        L.append(f"  • ราคารวมจาก {f['n_books']} โบรกเกอร์ (เรต=ฐานนิยม, ค่าน้ำ/ราคา=มัธยฐาน)")
    L.append(f"  • Context tags: {', '.join(f['tags'])}")
    L.append("\n  Rule ที่ทำงาน (คะแนนหลังคูณน้ำหนักที่เรียนรู้แล้ว):")
    if contribs:
        for c in sorted(contribs, key=lambda x: -x["eff"]):
            nm = RULE_NAMES.get(c["rule"], "Learned Rule")
            w = store.state["weights"].get(c["rule"], 1.0)
            L.append(f"    [{c['rule']:<4}] {c['market']:<9} {c['eff']:+.2f} (w={w:.2f})  {nm}")
    else:
        L.append("    (ไม่มี Rule ใดทำงาน)")

    L.append("\n🔍 ถอดรหัสเจตนาโต๊ะ")
    keyr = [c for c in contribs if c["rule"] in ("R1", "R2", "R5", "R9", "R11") or c["rule"].startswith("L")]
    if keyr:
        for c in keyr:
            L.append(f"  - {c['note']}")
    else:
        L.append("  - ไม่พบความผิดปกติเด่นชัดของ Trap / Fake Steam ราคาเคลื่อนไหวอยู่ในกรอบปกติ")

    L.append("\n🎯 สัญญาณฟันธงเดี่ยว (Single Best Pick)")
    L.append(f"  >>> {pick['label']} <<<")
    L.append(f"  ความมั่นใจ: {pick['confidence']:.0f}%  (ระดับ{pick['tier']}, คะแนน {pick['strength']:.2f})")
    if pick["veto"]:
        L.append(f"  ตัวเลือกที่ถูกแบน (Veto): {', '.join(pick['veto'])}")
    if pick["tier"] == "ต่ำ":
        L.append("  ⚠ สัญญาณอ่อน: โปรแกรมบังคับฟันธงตาม Rule 13 แต่ควรลดสัดส่วนเงินเดิมพัน")
    return "\n".join(L)


# ----------------------------------------------------------------------------
# 7) Settlement (Asian Handicap / OU / 1X2)
# ----------------------------------------------------------------------------
def halves_hdp(side, line_home, hg, ag):
    res = []
    for L in split_line(line_home):
        s = sign(hg - ag + L)
        res.append(s if side == "home" else -s)
    return res


def halves_ou(side, line, hg, ag):
    res = []
    for L in split_line(line):
        s = sign(hg + ag - L)
        res.append(s if side == "over" else -s)
    return res


def settle_all(rec, hg, ag):
    """คืน {market: (r, halves)} โดย r ใน [-1,1]"""
    f = rec["features"]
    out = {}
    out["HDP_HOME"] = halves_hdp("home", f["line_c"], hg, ag)
    out["HDP_AWAY"] = halves_hdp("away", f["line_c"], hg, ag)
    if f.get("has_ou"):
        out["OU_OVER"] = halves_ou("over", f["ou_c"], hg, ag)
        out["OU_UNDER"] = halves_ou("under", f["ou_c"], hg, ag)
    out["X12_HOME"] = [1 if hg > ag else -1]
    out["X12_AWAY"] = [1 if ag > hg else -1]
    return {k: (sum(v) / len(v), v) for k, v in out.items()}


def profit(halves, price_win):
    return sum(price_win if h == 1 else -1.0 if h == -1 else 0.0 for h in halves) / len(halves)


def result_word(r):
    return {1: "ชนะเต็ม", 0.5: "ชนะครึ่ง", 0: "เจ๊า(คืนทุน)", -0.5: "เสียครึ่ง", -1: "แพ้เต็ม"}.get(round(r * 2) / 2, f"{r:+.2f}")


# ----------------------------------------------------------------------------
# 8) การเรียนรู้: ปรับน้ำหนัก Rule + สร้าง Rule ใหม่
# ----------------------------------------------------------------------------
def update_weights(store, rec, outcomes):
    P, S = store.params, store.state
    agg, changes = {}, {}
    for c in rec["contribs"]:
        if c["market"] not in outcomes:
            continue
        r = outcomes[c["market"]][0]
        a = agg.setdefault(c["rule"], [0.0, 0.0])
        a[0] += c["raw"] * r
        a[1] += c["raw"]
    for rid, (num, den) in agg.items():
        if den <= 0:
            continue
        rr = num / den
        st = S["rule_stats"].setdefault(rid, {"n": 0, "sum_r": 0.0})
        st["n"] += 1
        st["sum_r"] += rr
        old = S["weights"].get(rid, 1.0)
        lr = max(P["lr_min"], P["lr"] / math.sqrt(st["n"]))
        w = old * (1 + lr * rr)
        w += P["decay"] * (1.0 - w)
        w = min(P["w_max"], max(P["w_min"], w))
        S["weights"][rid] = round(w, 4)
        changes[rid] = (old, w, rr)
    return changes


def role_outcomes(rec, outcomes):
    f = rec["features"]
    d = {"HDP_FAV": outcomes[f["fav_hdp"]][0], "HDP_DOG": outcomes[f["dog_hdp"]][0],
         "X12_FAV": outcomes[f["fav_x12"]][0]}
    if "OU_OVER" in outcomes:
        d["OU_OVER"], d["OU_UNDER"] = outcomes["OU_OVER"][0], outcomes["OU_UNDER"][0]
    return d


def discover_rules(store, verbose=True):
    """ค้นหารูปแบบ (ชุดเงื่อนไข tags) ที่ชนะ/แพ้ซ้ำอย่างมีนัยสำคัญ แล้วแปลงเป็น Rule ใหม่"""
    P, S = store.params, store.state
    stats = {}
    for rec in store.history:
        if rec.get("status") != "settled":
            continue
        tags, roles = rec["features"]["tags"], rec["role_r"]
        for k in range(1, P["disc_max_combo"] + 1):
            for combo in itertools.combinations(tags, k):
                for role, r in roles.items():
                    s = stats.setdefault((combo, role), [0, 0.0])
                    s[0] += 1
                    s[1] += (1 + r) / 2

    learned = S["learned_rules"]
    for lr in learned:                               # รีเฟรชสถิติ Rule เดิม
        s = stats.get((tuple(lr["tags"]), lr["role"]))
        if s and s[0] >= P["disc_min_n"]:
            lr["n"], lr["wr"] = s[0], s[1] / s[0]
            lr["strength"] = round(min(2.5, max(0.3, P["learned_base"] * (lr["wr"] - 0.5) * 4)), 3)
            lr["enabled"] = lr["wr"] >= 0.5
    existing = {(tuple(r["tags"]), r["role"]): r for r in learned}

    cands = []
    for (combo, role), (n, w) in stats.items():
        if n < P["disc_min_n"] or (combo, role) in existing:
            continue
        p = w / n
        lo, _ = wilson(p, n, P["disc_z"])
        if lo <= 0.5:
            continue
        if any(set(r["tags"]) <= set(combo) and r["role"] == role and r.get("enabled", True) for r in learned):
            continue
        cands.append((lo, len(combo), combo, role, n, p, w))
    cands.sort(key=lambda x: (-x[0], x[1]))

    new, seen_sig = [], set()
    for lo, _, combo, role, n, p, w in cands:
        if len(new) >= P["disc_max_new"] or len(learned) + len(new) >= P["disc_max_total"]:
            break
        sig = (role, n, round(w, 2))                 # ชุดแมตช์เดียวกัน -> เก็บอันที่เงื่อนไขน้อยสุด
        if sig in seen_sig:
            continue
        if any(set(r["tags"]) <= set(combo) and r["role"] == role for r in new):
            continue
        seen_sig.add(sig)
        rid = f"L{S['meta']['next_learned']:03d}"
        S["meta"]["next_learned"] += 1
        S["weights"][rid] = 1.0
        rule = {"id": rid, "tags": list(combo), "role": role, "n": n, "wr": round(p, 4),
                "strength": round(min(2.5, max(0.3, P["learned_base"] * (p - 0.5) * 4)), 3),
                "enabled": True, "created": time.strftime("%Y-%m-%d %H:%M")}
        new.append(rule)
    learned.extend(new)
    if verbose and new:
        print("\n🧠 ระบบสร้าง Rule ใหม่จากผลจริง:")
        for r in new:
            print(f"   + {r['id']}: ถ้า [{' + '.join(r['tags'])}] -> เล่น {ROLE_TH[r['role']]}"
                  f"  (ชนะ {r['wr']:.0%} จาก {r['n']} นัด, strength {r['strength']})")
    return new


# ----------------------------------------------------------------------------
# 9) คำสั่ง CLI
# ----------------------------------------------------------------------------
TEMPLATE = {
    "id": "arsenal-vs-spurs-2026-11-02",
    "league": "Premier League",
    "home": "Arsenal", "away": "Tottenham",
    "context": {
        "type": "league",                 # league | cup | playoff
        "derby": True, "high_volatility": False, "high_scoring_league": True,
        "cup_group_stage": False, "knockout": False,
        "desperation": None,              # "home" | "away" | null
        "late_goal_tendency": True
    },
    "x12": {"open": [1.80, 3.80, 4.40], "current": [1.74, 3.90, 4.70]},
    "hdp": {  # line = แต้มต่อมองจากฝั่งเจ้าบ้าน (ลบ = เจ้าบ้านต่อ)
        "open": {"line": -0.75, "home_water": 0.95, "away_water": 0.93},
        "current": {"line": -0.75, "home_water": 0.86, "away_water": 1.02}
    },
    "ou": {"open": {"line": 2.75, "over": 0.92, "under": 0.96},
           "current": {"line": 2.75, "over": 0.88, "under": 1.00}},
    "stats": {"home_gf": 2.1, "home_ga": 0.9, "away_gf": 1.6, "away_ga": 1.4},
    "h2h": [{"hg": 2, "ag": 2}, {"hg": 3, "ag": 1}, {"hg": 1, "ag": 0}, {"hg": 2, "ag": 1}, {"hg": 0, "ag": 1}],
    "team_value": {"home": 1100, "away": 800},
    "public_pct": {"home": 68, "away": 32}
}


def record_prediction(store, m, f, contribs, pick):
    """บันทึกสัญญาณลงประวัติ (สถานะ pending) คืน (id, บันทึกสำเร็จหรือไม่)"""
    mid = m.get("id") or slug(f"{f['home']}-vs-{f['away']}-{time.strftime('%Y%m%d-%H%M')}")
    store.history = [r for r in store.history if not (r["id"] == mid and r["status"] == "pending")]
    if any(r["id"] == mid for r in store.history):
        return mid, False
    store.history.append({"id": mid, "created": time.strftime("%Y-%m-%d %H:%M"), "status": "pending",
                          "features": f, "contribs": contribs, "pick": pick})
    store.save()
    return mid, True


def run_analysis(store, m, no_save=False):
    f, contribs, pick = analyze_match(m, store)
    print(render_report(m, f, contribs, pick, store))
    if not no_save:
        mid, ok = record_prediction(store, m, f, contribs, pick)
        if ok:
            print(f"\n💾 บันทึกสัญญาณแล้ว  id = {mid}\n   หลังจบเกมใช้: python {os.path.basename(sys.argv[0])} settle {mid} <เหย้า>-<เยือน>")
        else:
            print(f"\n(ไม่บันทึก: id '{mid}' ถูก settle ไปแล้ว ให้เปลี่ยน id)")


def cmd_analyze(a):
    store = Store(a.data_dir)
    with open(a.input, "r", encoding="utf-8") as fh:
        m = json.load(fh)
    try:
        m, warns = validate_match(m)
    except ValueError as e:
        sys.exit(f"❌ ข้อมูลไม่ถูกต้อง: {e}")
    for w_ in warns:
        print(f"⚠ {w_}")
    run_analysis(store, m, a.no_save)


# ----------------------------------------------------------------------------
# 9.1) นำเข้ารูปภาพ (5 รูป) -> สกัดข้อมูลด้วย Claude Vision -> ตรวจสอบ -> วิเคราะห์
# ----------------------------------------------------------------------------
API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "gemini-3.7-flash"
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".webp": "image/webp", ".gif": "image/gif"}

EXTRACT_PROMPT = """คุณคือระบบสกัดข้อมูลสำหรับวิเคราะห์ฟุตบอล ภาพที่แนบมาทั้งหมดเป็นของ "แมตช์เดียวกัน"
(ภาพสรุปแมตช์/ฟอร์ม, ตารางราคา 1X2, Asian Handicap, Total Goals (OU) จากหลายโบรกเกอร์, และสถิติเจอกัน H2H)
ลำดับรูปไม่แน่นอน ให้ดูเนื้อหาในรูปเอง

กติกาสำคัญ:
1. อ่านตัวเลขให้ตรงตามภาพ ห้ามเดาหรือแต่งตัวเลข ถ้าไม่มีข้อมูลให้ใส่ null
2. ตารางราคาแต่ละโบรกเกอร์มี 2 แถว: แถบสีน้ำเงินด้านซ้าย = ราคาเปิด (open), แถบสีส้ม = ราคาปัจจุบัน (current)
   ใส่ทุกโบรกเกอร์ใน "books" แยกเป็นรายการ (ถ้าชื่อซ้ำให้ต่อท้าย #1 #2 ตามลำดับในภาพ) ห้ามเฉลี่ยเอง ระบบจะรวมให้
3. hdp.line มองจากฝั่งเจ้าบ้าน (ทีมซ้าย/ทีมแรกในหัวภาพ) เสมอ: ติดลบ = เจ้าบ้านต่อ, บวก = เจ้าบ้านรอง
   แปลงเรตเอเชียนเป็นทศนิยม: 0/0.5 -> 0.25, 0.5/1 -> 0.75, 1/1.5 -> 1.25 (ใส่เครื่องหมายตามฝั่งเจ้าบ้าน)
   เช่น "-0.5/1" ของเจ้าบ้าน = -0.75 ; OU "3/3.5" = 3.25
4. home_water/away_water/over/under คือตัวเลขข้างเรตตามภาพ (รูปแบบ Hong Kong เช่น 0.91) ถ้าเห็นเป็น decimal เกิน 1.5 ให้ลบ 1
5. x12 เป็น decimal odds ลำดับ [เหย้า, เสมอ, เยือน]
6. h2h เรียงล่าสุดก่อน สูงสุด 5 นัด: hg/ag คือสกอร์เต็มเวลา (FT) ของทีมเหย้า/ทีมเยือนในนัดนั้น
   (ทีมที่อยู่แถวบนคือเจ้าบ้านของนัดนั้น) home_is_current_home = true ถ้าเจ้าบ้านนัดนั้นคือเจ้าบ้านของแมตช์ปัจจุบัน
7. form = ฟอร์ม 5 นัดหลังสุดของแต่ละทีมจากภาพสรุป: seq (เช่น "DLDWW"), gf (ประตูได้รวม), ga (ประตูเสียรวม), games (จำนวนนัด), win_rate (%)
8. team_value = มูลค่าทีมที่แสดงใต้ชื่อทีม (ตัวเลขล้วน หน่วยเดียวกัน)
9. context: ใส่ true เฉพาะเมื่อมีหลักฐานชัด (เช่น ดาร์บี้) นอกนั้น false; type เป็น league | cup | playoff
10. warnings = รายการข้อความภาษาไทยของค่าที่อ่านไม่ชัด/ขัดแย้งกันระหว่างรูป (เช่น ลำดับฟอร์มในสองรูปไม่ตรงกัน)

ตอบเป็น JSON ล้วน ไม่มีข้อความอื่น ไม่มี markdown ตามโครงสร้างนี้:
"""

EXTRACT_SCHEMA = {
    "league": "...", "home": "...", "away": "...",
    "context": {"type": "league", "derby": False, "high_volatility": False, "high_scoring_league": False,
                "cup_group_stage": False, "knockout": False, "desperation": None, "late_goal_tendency": False},
    "books": [{
        "name": "bookmaker",
        "x12": {"open": [0.0, 0.0, 0.0], "current": [0.0, 0.0, 0.0]},
        "hdp": {"open": {"line": 0.0, "home_water": 0.0, "away_water": 0.0},
                "current": {"line": 0.0, "home_water": 0.0, "away_water": 0.0}},
        "ou": {"open": {"line": 0.0, "over": 0.0, "under": 0.0},
               "current": {"line": 0.0, "over": 0.0, "under": 0.0}}}],
    "form": {"home": {"seq": "DLDWW", "gf": 0, "ga": 0, "games": 5, "win_rate": 0},
             "away": {"seq": "DLDWW", "gf": 0, "ga": 0, "games": 5, "win_rate": 0}},
    "h2h": [{"hg": 0, "ag": 0, "home_is_current_home": True}],
    "team_value": {"home": 0, "away": 0},
    "warnings": ["..."],
}


def _modal_line(lines):
    c = Counter(lines)
    top = max(c.values())
    cand = sorted(l for l, v in c.items() if v == top)
    if len(cand) == 1:
        return cand[0]
    med = statistics.median(lines)
    return min(cand, key=lambda l: abs(l - med))


def _med(xs):
    return round(statistics.median(xs), 3)


def consolidate_books(m):
    """รวมราคาหลายโบรกเกอร์เป็นราคาเดียว: เรต = ค่าฐานนิยม, ค่าน้ำ/ราคา = มัธยฐานของโบรกเกอร์ที่ใช้เรตเดียวกัน"""
    books = [b for b in (m.get("books") or []) if isinstance(b, dict)]
    w = []
    xs = [b["x12"] for b in books if isinstance(b.get("x12"), dict)
          and all(isinstance(b["x12"].get(t), list) and len(b["x12"][t]) == 3 and all(_num(v) for v in b["x12"][t])
                  for t in ("open", "current"))]
    if xs:
        m["x12"] = {t: [_med([x[t][i] for x in xs]) for i in range(3)] for t in ("open", "current")}
    for key, f1, f2 in (("hdp", "home_water", "away_water"), ("ou", "over", "under")):
        out = {}
        for t in ("open", "current"):
            rows = [(b.get("name", "?"), b[key][t]) for b in books if isinstance(b.get(key), dict)
                    and isinstance(b[key].get(t), dict) and all(_num(b[key][t].get(k)) for k in ("line", f1, f2))]
            if not rows:
                break
            ml = _modal_line([r["line"] for _, r in rows])
            same = [r for _, r in rows if abs(r["line"] - ml) < 1e-9]
            out[t] = {"line": ml, f1: _med([r[f1] for r in same]), f2: _med([r[f2] for r in same])}
            odd = [f"{n} ({r['line']:+g})" for n, r in rows if abs(r["line"] - ml) > 1e-9]
            if odd:
                w.append(f"{key.upper()} {'เปิด' if t == 'open' else 'ปัจจุบัน'}: เรตหลัก {ml:+g} ({len(same)}/{len(rows)} โบรกเกอร์) "
                         f"ที่ต่างออกไป: {', '.join(odd)} -> ไม่นำมาเฉลี่ย")
        else:
            m[key] = out
    m["n_books"] = len(books)
    return w


def extract_from_images(paths, model, api_key):
    content = []
    for i, p in enumerate(paths, 1):
        ext = os.path.splitext(p)[1].lower()
        if ext not in MEDIA_TYPES:
            sys.exit(f"ไม่รองรับไฟล์ {p} (รองรับ: {', '.join(MEDIA_TYPES)})")
        if not os.path.exists(p):
            sys.exit(f"ไม่พบไฟล์ {p}")
        raw = open(p, "rb").read()
        if len(raw) > 5 * 1024 * 1024:
            sys.exit(f"{p} ใหญ่เกิน 5MB กรุณาย่อรูปก่อน")
        content.append({"type": "text", "text": f"รูปที่ {i}: {os.path.basename(p)}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": MEDIA_TYPES[ext],
                                                    "data": base64.b64encode(raw).decode()}})
    schema = EXTRACT_SCHEMA
    content.append({"type": "text", "text": EXTRACT_PROMPT + json.dumps(schema, ensure_ascii=False, indent=1)})
    body = json.dumps({"model": model, "max_tokens": 3000,
                       "messages": [{"role": "user", "content": content}]}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
    except urllib.error.URLError as e:
        sys.exit(f"เชื่อมต่อ API ไม่ได้: {e.reason}")
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return parse_json_reply(text)


def parse_json_reply(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        sys.exit("โมเดลไม่ได้ตอบเป็น JSON:\n" + text[:500])
    try:
        return json.loads(text[i:j + 1])
    except json.JSONDecodeError as e:
        sys.exit(f"แปลง JSON ไม่สำเร็จ: {e}\n{text[:500]}")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_match(m):
    """ตรวจ/แก้ข้อมูลที่สกัดได้ คืน (m, warnings) หรือ raise ValueError ถ้าขาดข้อมูลหลัก"""
    w = list(m.get("warnings") or [])
    if m.get("books"):
        w += consolidate_books(m)
    for k in ("x12", "hdp"):
        if not isinstance(m.get(k), dict) or not m[k].get("open") or not m[k].get("current"):
            raise ValueError(f"ขาดข้อมูล {k} (ต้องมีทั้งราคาเปิดและราคาปัจจุบัน)")
    for t in ("open", "current"):
        o = m["x12"][t]
        if not (isinstance(o, list) and len(o) == 3 and all(_num(x) and x > 1 for x in o)):
            raise ValueError(f"x12.{t} ต้องเป็น [เหย้า, เสมอ, เยือน] และมากกว่า 1: {o}")
        h = m["hdp"][t]
        for k in ("line", "home_water", "away_water"):
            if not _num(h.get(k)):
                raise ValueError(f"hdp.{t}.{k} ไม่ใช่ตัวเลข: {h.get(k)}")
        if abs(h["line"] * 4 - round(h["line"] * 4)) > 1e-6:
            w.append(f"hdp.{t}.line={h['line']} ไม่ตรงขั้น 0.25 โปรดตรวจรูป")
        for k in ("home_water", "away_water"):
            if h[k] > 1.5:
                h[k] = round(h[k] - 1, 3)
                w.append(f"hdp.{t}.{k} ดูเหมือน decimal จึงลบ 1 ให้อัตโนมัติ")
            if not 0.5 <= h[k] <= 1.3:
                w.append(f"hdp.{t}.{k}={h[k]} อยู่นอกช่วงปกติ โปรดตรวจรูป")
    ou = m.get("ou")
    if ou:
        ok = all(isinstance(ou.get(t), dict) and all(_num(ou[t].get(k)) for k in ("line", "over", "under"))
                 for t in ("open", "current"))
        if not ok:
            w.append("ข้อมูล OU ไม่ครบ จึงตัดตลาดสูง/ต่ำออกจากการวิเคราะห์")
            m["ou"] = None
        else:
            for t in ("open", "current"):
                for k in ("over", "under"):
                    if ou[t][k] > 1.5:
                        ou[t][k] = round(ou[t][k] - 1, 3)
                        w.append(f"ou.{t}.{k} ดูเหมือน decimal จึงลบ 1 ให้อัตโนมัติ")
    st = {k: v for k, v in (m.get("stats") or {}).items() if _num(v)}
    fm = m.get("form") or {}
    if not st and all(isinstance(fm.get(t), dict) and _num(fm[t].get("gf")) and _num(fm[t].get("ga")) for t in ("home", "away")):
        n_ = lambda t: fm[t].get("games") or len(fm[t].get("seq") or "") or 5
        st = {"home_gf": fm["home"]["gf"] / n_("home"), "home_ga": fm["home"]["ga"] / n_("home"),
              "away_gf": fm["away"]["gf"] / n_("away"), "away_ga": fm["away"]["ga"] / n_("away")}
        w.append("สถิติประตูได้/เสียคำนวณจากฟอร์ม 5 นัดหลัง (ไม่แยกเหย้า/เยือน)")
    m["stats"] = {k: round(v, 3) for k, v in st.items()}
    m["h2h"] = [e for e in (m.get("h2h") or []) if _num(e.get("hg")) and _num(e.get("ag"))][:5]
    if not m["h2h"]:
        w.append("ไม่พบข้อมูล H2H ใน 5 รูป (Rule 5 จะไม่ทำงาน)")
    if not m["stats"]:
        w.append("ไม่พบสถิติประตูได้/เสีย (Rule 3, 8 จะไม่ทำงาน)")
    m["context"] = {**{"type": "league"}, **{k: v for k, v in (m.get("context") or {}).items() if v is not None}}
    m["home"], m["away"] = m.get("home") or "Home", m.get("away") or "Away"
    m["warnings"] = w
    return m, w


def cmd_images(a):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ต้องตั้งค่า environment variable ANTHROPIC_API_KEY ก่อน\n"
                 "  macOS/Linux: export ANTHROPIC_API_KEY=sk-ant-...\n"
                 "  Windows PS : $env:ANTHROPIC_API_KEY='sk-ant-...'")
    if len(a.images) != 5:
        print(f"⚠ ได้รับ {len(a.images)} รูป (ปกติใช้ 5 รูป) จะดำเนินการต่อ")
    print(f"🖼  กำลังอ่าน {len(a.images)} รูปด้วย {a.model} ...")
    m = extract_from_images(a.images, a.model, key)
    try:
        m, warns = validate_match(m)
    except ValueError as e:
        raw = os.path.join(a.data_dir, "extracted_failed.json")
        os.makedirs(a.data_dir, exist_ok=True)
        json.dump(m, open(raw, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        sys.exit(f"❌ ข้อมูลที่อ่านได้ไม่ครบ: {e}\n   บันทึกผลดิบไว้ที่ {raw} แก้ไขแล้วใช้คำสั่ง analyze ต่อได้")
    # ตัวเลือกบริบทจากผู้ใช้ มีสิทธิ์เหนือสิ่งที่โมเดลอ่านได้
    c = m["context"]
    for flag, key_ in (("derby", "derby"), ("high_vol", "high_volatility"), ("high_scoring", "high_scoring_league"),
                       ("cup_group", "cup_group_stage"), ("knockout", "knockout"), ("late_goal", "late_goal_tendency")):
        if getattr(a, flag):
            c[key_] = True
    if a.league_type:
        c["type"] = a.league_type
    if a.desperation:
        c["desperation"] = a.desperation
    m["id"] = a.match_id or slug(f"{m['home']}-vs-{m['away']}-{time.strftime('%Y%m%d-%H%M')}")

    out = a.save_json or os.path.join(a.data_dir, f"extracted_{m['id']}.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(m, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n📋 ข้อมูลที่สกัดได้:")
    print(json.dumps({k: v for k, v in m.items() if k != "warnings"}, ensure_ascii=False, indent=1))
    if warns:
        print("\n⚠ คำเตือนจากการอ่านภาพ:")
        for w_ in warns:
            print(f"   - {w_}")
    print(f"\n💾 บันทึก JSON ไว้ที่ {out} (แก้ไขแล้วรันซ้ำด้วย: analyze {out})")
    if a.extract_only:
        return
    if not a.yes:
        ans = input("\nข้อมูลถูกต้องและต้องการวิเคราะห์เลยหรือไม่? [Y/n] ").strip().lower()
        if ans in ("n", "no"):
            print("หยุดไว้ก่อน แก้ไขไฟล์ JSON แล้วใช้คำสั่ง analyze ได้เลย")
            return
    print()
    run_analysis(Store(a.data_dir), m, a.no_save)


def do_settle(store, rec, hg, ag):
    """ใส่สกอร์จริง -> Post-Mortem -> ปรับน้ำหนัก -> ค้นหา Rule ใหม่ (ไม่ print) คืน (outcomes, r, profit, changes, new_rules)"""
    outcomes = settle_all(rec, hg, ag)
    pk = rec["pick"]
    r, halves = outcomes[pk["market"]]
    pf = profit(halves, pk["price_win"])
    rec.update(status="settled", score=[hg, ag], pick_r=r, pick_profit=round(pf, 4),
               role_r=role_outcomes(rec, outcomes))
    changes = update_weights(store, rec, outcomes)
    new = discover_rules(store, verbose=False)
    store.state["meta"]["settled"] = store.state["meta"].get("settled", 0) + 1
    store.save()
    return outcomes, r, pf, changes, new


def cmd_settle(a):
    store = Store(a.data_dir)
    rec = next((r for r in store.history if r["id"] == a.id), None)
    if not rec:
        sys.exit(f"ไม่พบ id: {a.id}  (ดูรายการด้วยคำสั่ง stats)")
    if rec["status"] == "settled":
        sys.exit("รายการนี้ settle ไปแล้ว")
    mm = re.match(r"^\s*(\d+)\s*[-:]\s*(\d+)\s*$", a.score)
    if not mm:
        sys.exit("รูปแบบสกอร์ไม่ถูกต้อง ใช้เช่น 2-1 (เหย้า-เยือน)")
    hg, ag = int(mm.group(1)), int(mm.group(2))
    outcomes, r, pf, changes, new = do_settle(store, rec, hg, ag)
    print(f"🏁 {rec['features']['home']} {hg}-{ag} {rec['features']['away']}")
    print(f"🎯 สัญญาณที่ฟันธง: {rec['pick']['label']}  ->  {result_word(r)}  (กำไร/ขาดทุน {pf:+.2f} หน่วย)")
    print("\n🔬 Post-Match Post-Mortem (ผลของแต่ละตลาด):")
    for mk, (rr, _) in outcomes.items():
        print(f"   {mk:<9} {result_word(rr)}")
    if changes:
        print("\n⚙ ปรับน้ำหนัก Rule:")
        for rid, (o, n, rr) in sorted(changes.items()):
            arrow = "▲" if n > o else "▼" if n < o else "="
            print(f"   {rid:<5} {o:.3f} -> {n:.3f} {arrow}  (ความถูกต้องรอบนี้ {rr:+.2f})  {RULE_NAMES.get(rid, 'Learned Rule')}")
    if new:
        print("\n🧠 ระบบสร้าง Rule ใหม่จากผลจริง:")
        for r_ in new:
            print(f"   + {r_['id']}: ถ้า [{' + '.join(r_['tags'])}] -> เล่น {ROLE_TH[r_['role']]}"
                  f"  (ชนะ {r_['wr']:.0%} จาก {r_['n']} นัด, strength {r_['strength']})")


def cmd_learn(a):
    store = Store(a.data_dir)
    new = discover_rules(store)
    if not new:
        print("ยังไม่พบรูปแบบใหม่ที่มีนัยสำคัญ (ต้องสะสมผลจริงเพิ่ม)")
    store.save()


def cmd_stats(a):
    store = Store(a.data_dir)
    S = store.state
    done = [r for r in store.history if r["status"] == "settled"]
    pend = [r for r in store.history if r["status"] == "pending"]
    print(f"📈 สรุปผลงาน: settle แล้ว {len(done)} นัด | รอผล {len(pend)} นัด")
    if done:
        w = sum(1 for r in done if r["pick_r"] > 0)
        l = sum(1 for r in done if r["pick_r"] < 0)
        p = len(done) - w - l
        pr = sum(r["pick_profit"] for r in done)
        print(f"   ชนะ {w} | เจ๊า {p} | แพ้ {l} | กำไรสุทธิ {pr:+.2f} หน่วย | ROI {pr / len(done):+.1%} ต่อไม้")
        by = {}
        for r in done:
            k = r["pick"]["market"].split("_")[0]
            b = by.setdefault(k, [0, 0.0])
            b[0] += 1
            b[1] += r["pick_profit"]
        for k, (n, pf) in by.items():
            print(f"   ตลาด {k:<4}: {n} ไม้ กำไร {pf:+.2f}")
    print("\n⚙ น้ำหนัก Rule ปัจจุบัน:")
    for rid, w in sorted(S["weights"].items()):
        st = S["rule_stats"].get(rid, {"n": 0, "sum_r": 0})
        avg = st["sum_r"] / st["n"] if st["n"] else 0
        print(f"   {rid:<5} w={w:.3f}  ใช้ {st['n']:>3} ครั้ง  avg r={avg:+.2f}  {RULE_NAMES.get(rid, 'Learned Rule')}")
    if S["learned_rules"]:
        print("\n🧠 Rule ที่ระบบสร้างเอง:")
        for r in S["learned_rules"]:
            print(f"   {r['id']} [{'ON' if r.get('enabled', True) else 'OFF'}] ถ้า [{' + '.join(r['tags'])}] -> {ROLE_TH[r['role']]}"
                  f"  ชนะ {r['wr']:.0%}/{r['n']} นัด strength {r['strength']}")
    if pend:
        print("\n⏳ รอผล:", ", ".join(r["id"] for r in pend))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Football Quant V5.8 + Self-Learning Rule Engine")
    ap.add_argument("--data-dir", default="quant_data", help="โฟลเดอร์เก็บ state/history")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("analyze", help="วิเคราะห์แมตช์จากไฟล์ JSON")
    p.add_argument("input")
    p.add_argument("--no-save", action="store_true")
    p.set_defaults(fn=cmd_analyze)
    p = sp.add_parser("images", help="อ่านรูป 5 รูปด้วย Claude Vision แล้ววิเคราะห์ (ต้องมี ANTHROPIC_API_KEY)")
    p.add_argument("images", nargs="+", help="ไฟล์รูป png/jpg/webp (ปกติ 5 รูป)")
    p.add_argument("--model", default=os.environ.get("QUANT_MODEL", DEFAULT_MODEL))
    p.add_argument("--match-id")
    p.add_argument("--save-json", help="ที่เก็บ JSON ที่สกัดได้")
    p.add_argument("--extract-only", action="store_true", help="สกัดข้อมูลอย่างเดียว ไม่วิเคราะห์")
    p.add_argument("--yes", action="store_true", help="ข้ามการถามยืนยัน")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--league-type", choices=["league", "cup", "playoff"])
    p.add_argument("--desperation", choices=["home", "away"])
    for fl in ("derby", "high-vol", "high-scoring", "cup-group", "knockout", "late-goal"):
        p.add_argument("--" + fl, action="store_true", help="ระบุบริบทเอง (override ค่าที่อ่านจากรูป)")
    p.set_defaults(fn=cmd_images)
    p = sp.add_parser("settle", help="ใส่สกอร์จริงเพื่อเรียนรู้")
    p.add_argument("id")
    p.add_argument("score", help="เหย้า-เยือน เช่น 2-1")
    p.set_defaults(fn=cmd_settle)
    sp.add_parser("learn", help="ค้นหา Rule ใหม่จากประวัติ").set_defaults(fn=cmd_learn)
    sp.add_parser("stats", help="ดูผลงานและน้ำหนัก Rule").set_defaults(fn=cmd_stats)
    sp.add_parser("template", help="พิมพ์ JSON ตัวอย่าง").set_defaults(
        fn=lambda a: print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2)))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
