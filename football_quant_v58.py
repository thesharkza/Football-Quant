#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant V5.9 (Advanced Volatility, Trap Shield & Class Superiority Edition)
+ Self-Learning Rule Engine

ทำอะไรได้บ้าง
  1) analyze : วิเคราะห์ตารางราคา (1X2 / HDP / OU) ตาม Rule 1-26 (+R27 Coupled Steam, R28 Current Odds Anchor) แล้ว "ฟันธงเดี่ยว" 1 ตัวเลือก
  2) settle  : ใส่สกอร์จริง -> Post-Match Post-Mortem -> ปรับน้ำหนักแต่ละ Rule อัตโนมัติ
               และ "สร้าง Rule ใหม่" (Learned Rules) จากรูปแบบที่ชนะ/แพ้ซ้ำ ๆ
  3) learn   : รันการค้นหา Rule ใหม่จากประวัติทั้งหมดอีกครั้ง
  4) stats   : ดูผลงาน, ROI, น้ำหนักของแต่ละ Rule, Rule ที่ระบบสร้างเอง
  5) template: พิมพ์ไฟล์ JSON ตัวอย่างสำหรับกรอกข้อมูลแมตช์
  6) images  : นำเข้ารูปภาพ 5 รูป -> Gemini (gemini-3.7-flash) สกัดค่าราคา/H2H/สถิติ -> ตรวจสอบ -> วิเคราะห์
               (ต้องตั้ง GEMINI_API_KEY)

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
import datetime as _dt_mod
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
    "move_only_discount": 0.60,  # Current Odds Priority: สัญญาณที่มาจากการไหลของราคาล้วน (ไม่มีราคาปัจจุบัน/บริบทหนุน) ลดเหลือ 60%
    "skew_min": 0.08,            # ส่วนต่างค่าน้ำปัจจุบันของสองฝั่ง ที่ถือว่าโต๊ะกดราคาฝั่งใดฝั่งหนึ่ง
    "rank_gap_dog": 4,           # Rule 18: ทีมต่ออยู่อันดับต่ำกว่าทีมรอง >= 4 อันดับ
    "rank_gap_fav": 6,           # Rule 18: ทีมต่ออยู่อันดับสูงกว่าทีมรอง >= 6 อันดับ
    "bottom_zone": 0.75,         # Rule 19: โซนท้ายตาราง = อันดับ > 75% ของจำนวนทีมในลีก
    "counter_pct": 40.0,         # Rule 24: ประสิทธิภาพสวนกลับ > 40%
    "water_per_quarter": 0.10,   # ค่าประมาณ: เรตเปลี่ยน 0.25 ลูก ค่าน้ำเปลี่ยนตามธรรมชาติ ~0.10 (ใช้ปรับค่าน้ำข้ามเรต)
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
    "score_mode": "sum",         # sum = รวมคะแนนทุก Rule | grouped = นับกลุ่มข้อมูลละครั้ง (ไม่บวก Rule ที่ชี้ทางเดียวกันซ้ำ)
    "false_giant_max_ratio": 3.5,  # Rule 27: มูลค่าทีมต่อ >= 3.5 เท่า ไม่ใช้ Rule 26 สวนรอง
    "exclude_universal": True,   # ไม่ใช้เงื่อนไขที่จริงเกือบทุกนัด (เช่น ctx:league) สร้าง Rule
    "universal_cov": 0.85,
    # --- วงจรชีวิตของ Rule ที่ระบบสร้างเอง/Rule ทดลอง: เงา -> ปลดล็อค -> ถอด ---
    "unlock_wr": 0.65,           # อัตราชนะนอกกลุ่มตัวอย่าง (out-of-sample) ขั้นต่ำเพื่อปลดล็อคทางลัด
    "unlock_min_n": 40,          # จำนวนครั้งขั้นต่ำของทางลัด (เดิม 30: Rule ที่ไม่มีประโยชน์หลุดผ่านได้ ~9% ต่อข้อ)
    "judge_n": 70,               # ครบกี่ครั้งถึงตัดสินสุดท้าย (ผ่านเกณฑ์นัยสำคัญ -> ปลดล็อค, ไม่ผ่าน -> ถอด)
    "breakeven_wr": 0.525,       # จุดคุ้มทุนอัตราชนะ (ค่าน้ำเฉลี่ย ~0.90)
    "gate_enabled": True,        # ตัวกรองช่วงคะแนน: งดลงทุนเมื่อประเภทไม้ × ช่วงคะแนนนั้นมีผลที่ผ่านมาต่ำกว่าจุดคุ้มทุนหรือขาดทุน
    "gate_min_n": 20,            # ต้องมีผลในช่วงนั้นอย่างน้อยกี่ไม้ จึงเริ่มตัดสิน (น้อยกว่านี้ = ลงทุนตามปกติ)
    "gate_edges": [1.0, 1.5, 2.0, 2.5, 3.0],
    "lock_unlocks": True,        # ล็อก: Rule ที่ผ่านเกณฑ์ยังไม่ถูกเปิดใช้อัตโนมัติ (คงเป็นเงา ติดป้าย "พร้อมใช้") จนกว่าจะปลดล็อกเอง
    "lb_z_fast": 1.96, "lb_z_judge": 1.645,          # ทางลัดใช้ความเชื่อมั่น 95% (เดิม 1.28 = 80%)
    "retire_min_n": 20,          # ใช้ครบเท่านี้แล้วอัตราชนะต่ำกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ -> ถอด
    "decline_window": 10,        # ขนาดช่วงที่ใช้ตรวจว่าอัตราชนะลดลงต่อเนื่อง 3 ช่วง
    # --- สถานะ "ข้าม": ไม้ที่สัญญาณอ่อนหรือขัดกัน ยังคำนวณไม้เงาไว้ติดตามผล แต่ไม่นับเป็นไม้ที่เล่น ---
    "skip_enabled": True,
    "skip_min_strength": 1.2,    # คะแนนต่ำกว่านี้ = สัญญาณอ่อน
    "skip_conflict": 0.6,        # คะแนนฝั่งตรงข้าม >= 60% ของฝั่งที่เลือก = สัญญาณขัดกัน
    "skip_move_only": True,      # สัญญาณมาจากการไหลของราคาล้วน = ข้าม
    "skip_verify_fail": True,    # ตรวจเหย้า/เยือนไม่ผ่าน = ข้าม
    # --- แช่แข็งน้ำหนัก Rule: น้ำหนักที่ใช้ฟันธงไม่เปลี่ยน ระบบปรับ "น้ำหนักเงา" ไว้เบื้องหลังแทน ---
    "freeze_weights": True,
}

DEFAULT_WEIGHTS = {
    "R1": 1.0, "R2": 1.5, "R3": 1.0, "R4": 1.0, "R5": 1.0, "R6": 1.0, "R7": 1.0,
    "R8": 1.0, "R9": 1.0, "R10": 1.0, "R11": 1.0, "R12": 1.0, "R14": 1.5, "R16": 1.0, "R17": 1.0, "R18": 1.0, "R19": 1.0,
    "R20": 1.0, "R21": 1.0, "R22": 1.0, "R23": 1.0, "R24": 1.0, "R25": 1.5, "R26": 1.5, "X1": 1.0, "X2": 1.0,
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
    "R17": "Table Control: ลีกอัตราเสมอสูง",
    "R18": "Table Control: อันดับสวนทางราคา",
    "R19": "Table Control: ทีมเยือนโซนท้ายตาราง",
    "R20": "Draw-Prone League: เอนต่ำ",
    "R21": "Home Pride & Underdog Defensive Resurgence",
    "R22": "High-Scoring League Volatility Filter",
    "R23": "Away Favorite Security Buffer (Balanced Table)",
    "R24": "Continental Cup Underdog Shield",
    "R25": "Home Momentum Over Market Value",
    "R26": "False Giant Slump Shield",
    "R27": "Extreme Market Value Override to Slump Shield (ปรับ Rule 26)",
    "X1": "Coupled Steam Confirmation",
    "X2": "Current Odds Anchor (ราคาปัจจุบัน)",
    "R28": "Top-Table Away Shallow Handicap Draw Guard",
    "R29": "Women & Regional League Market Flow Supremacy",
    "R30": "Bottom-Table Home Desperation Guard",
    "R31": "Heavy Handicap Deep Defense Filter",
    "R32": "High Win-Rate Away Momentum Override",
    "R33": "Bottom-Team Home Defensive Collapse Filter",
    "R34": "Continental Heavyweight Home Rebound Guard",
    "R35": "Continental Heavy Handicap Resilience Filter",
    "R36": "Championship & High-Volatility Defensive Leakage Filter",
    "R37": "Cup & Lower-Tier Upset Defense Protocol",
    "R38": "Shallow Handicap Draw Vulnerability Filter",
    "R39": "Home Defensive Meltdown & Collapse Shield (รวม Rule 41)",
    "R40": "Elite Away Giant Slump & Pressured Trap Filter",
    "R42": "xG Total vs OU Line (ข้อมูลทีม)",
    "R43": "Favorite xG Over/Under-performance Regression",
    "R44": "Key Starters Missing (ตัวจริงหาย)",
    "R45": "Rest Days Gap (พักน้อย/มาก)",
    "R46": "Cup Rotation Risk (หมุนเวียนตัวหลัก)",
}
STAT_RULES = {"R3", "R5", "R8"}          # กฎที่อิงสถิติ -> ถูกลดน้ำหนักในดาร์บี้ (Rule 10)
MOVEMENT_RULES = {"R1", "R2", "R9", "R11", "X1"}   # กฎที่อิงการไหลของราคา (เทียบราคาเปิด) -> ต้องมีราคาปัจจุบัน/บริบทหนุนด้วย
NOISE_RULES = {"R1", "R9"}               # กฎที่ถูกลดน้ำหนักเมื่อความขัดแย้ง <= 20% (Rule 11)

ROLE_TH = {
    "HDP_FAV": "แฮนดิแคป ทีมต่อ", "HDP_DOG": "แฮนดิแคป ทีมรอง",
    "OU_OVER": "สูง (Over)", "OU_UNDER": "ต่ำ (Under)", "X12_FAV": "1X2 ทีมต่อชนะ",
}
ALL_MARKETS = ["HDP_HOME", "HDP_AWAY", "OU_OVER", "OU_UNDER", "X12_HOME", "X12_AWAY"]


# ----------------------------------------------------------------------------
# 1) เครื่องมือช่วย
# ----------------------------------------------------------------------------
TZ_TH = _dt_mod.timezone(_dt_mod.timedelta(hours=7))


def now_th(fmt="%Y-%m-%d %H:%M"):
    """เวลาปัจจุบันตามเวลาไทย (เซิร์ฟเวอร์คลาวด์ใช้ UTC ทำให้เวลาที่บันทึก/วันที่ที่ส่งให้ AI ช้าไป 7 ชั่วโมง)"""
    return _dt_mod.datetime.now(TZ_TH).strftime(fmt)


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
        "line_o": lo, "line_c": lc, "fav_line_c": abs(lc), "fav_line_o": -lo if (lc < 0 or (lc == 0 and fav == "home")) else lo,
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
    pb = (m.get("water_chg") or {}).get("hdp")
    if pb and abs(lc - lo) < 1e-9:                     # เรตหลักนิ่ง: ใช้มัธยฐานการเปลี่ยนแปลงรายโบรกเกอร์ (ไม่ปนผลจากชุดเจ้าที่ต่างกัน)
        f["fav_drop"] = pb["home_water"] if fav == "home" else pb["away_water"]
        f["dog_drop"] = pb["away_water"] if fav == "home" else pb["home_water"]
    f["fav_water_c"], f["dog_water_c"] = fc, dc
    # ค่าน้ำที่ปรับตามการเปลี่ยนเรตแล้ว: เรตลึกขึ้น -> ค่าน้ำทีมต่อสูงขึ้น/ทีมรองต่ำลงตามธรรมชาติ ไม่ใช่สัญญาณ
    sq = f["hdp_shift_fav"] / 0.25
    f["fav_drop_adj"] = f["fav_drop"] + sq * P["water_per_quarter"]
    f["dog_drop_adj"] = f["dog_drop"] - sq * P["water_per_quarter"]
    f["hdp_agree"] = m.get("hdp_agree")

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
        pbo = (m.get("water_chg") or {}).get("ou")
        if pbo and abs(f["ou_shift"]) < 1e-9:
            f["over_drop"], f["under_drop"] = pbo["over"], pbo["under"]
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

    # --- V5.9: ตารางคะแนน / ฟอร์ม / บริบทเพิ่มเติม ---
    f["continental"] = bool(ctx.get("continental_cup"))
    f["women_regional"] = bool(ctx.get("women_or_regional"))                                    # Rule 29
    f["asian_cup"] = bool(ctx.get("asian_cup")) or "AFC" in str(m.get("league", "")).upper()   # Rule 35
    f["high_draw"] = bool(ctx.get("high_draw_league"))
    rk = m.get("rank") or {}
    f["rank_home"] = rk.get("home") if _num(rk.get("home")) else None
    f["rank_away"] = rk.get("away") if _num(rk.get("away")) else None
    f["rank_fav"], f["rank_dog"] = (f["rank_home"], f["rank_away"]) if fav == "home" else (f["rank_away"], f["rank_home"])
    f["rank_gap"] = (f["rank_fav"] - f["rank_dog"]) if (f["rank_fav"] is not None and f["rank_dog"] is not None) else None
    ls = m.get("league_size")
    f["league_size"] = ls if _num(ls) and ls > 0 else None
    f["home_gf"], f["home_ga"] = g("home_gf"), g("home_ga")

    def _wr(side):
        x = (m.get("form") or {}).get(side) or {}
        if _num(x.get("win_rate")):
            return float(x["win_rate"])
        seq = str(x.get("seq") or "").upper()
        return 100.0 * seq.count("W") / len(seq) if seq else None
    f["fav_win_rate"], f["dog_win_rate"] = _wr(fav), _wr(dog)
    f["false_giant"] = bool(f["value_ratio"] is not None and f["value_ratio"] > 1
                            and f["fav_win_rate"] is not None and f["fav_win_rate"] <= 20
                            and f["value_ratio"] < P["false_giant_max_ratio"])                    # Rule 26 (ยกเว้น Rule 27: มูลค่า >= 3.5 เท่า)
    cp = st.get("away_counter_pct")
    f["shield24"] = bool(f["continental"] and cp is not None and cp > P["counter_pct"])           # Rule 24
    if f["false_giant"] or f["shield24"]:
        f["class_sup"] = False                                                                   # ปิด Rule 14
    hfh = m.get("home_form_home") or {}
    gm = sum(hfh.get(k, 0) for k in ("w", "d", "l") if _num(hfh.get(k)))
    hw_ = hfh.get("w") if _num(hfh.get("w")) else 0
    f["home_momentum"] = bool(abs(lc) < 1e-9 and gm >= 5 and hfh.get("l", 0) == 0 and hw_ / gm > 0.5)  # Rule 25
    veto = set()
    if f["class_sup"]:
        veto.add(f["dog_hdp"])
    if f["false_giant"]:
        veto.add(f["fav_hdp"])
    if f["home_momentum"]:
        veto.add("HDP_AWAY")
    f["veto"] = sorted(veto)

    f["form"] = m.get("form")
    f["away_form_away"] = m.get("away_form_away")
    f["venue_stats"] = bool(st.get("venue"))
    f["n_books"] = m.get("n_books")
    f["best_price"] = m.get("best_price") or {}
    f["verify"] = verify_home_away(m, f)
    f["verify_fail"] = any(not ok for ok, _ in f["verify"])
    f["tags"] = make_tags(f, P)
    f.update(team_news_features(m, f))                # ข้อมูลทีม (ไม่เข้า tags: ใช้กับ Rule เงา R42-R46 เท่านั้น)
    try:
        f["score_model"] = score_model(f)              # สกอร์ที่น่าจะเป็น (แสดงผลเท่านั้น ไม่มีผลต่อการฟันธง)
    except Exception:  # noqa
        f["score_model"] = None
    return f


def _same_team(a, b):
    a, b = re.sub(r"\s+", " ", str(a or "")).strip().lower(), re.sub(r"\s+", " ", str(b or "")).strip().lower()
    return bool(a and b and (a == b or a in b or b in a))


def verify_home_away(m, f):
    """Home/Away Verification Protocol: ตรวจสิทธิ์เหย้า(ซ้าย)/เยือน(ขวา) และความสอดคล้องของราคา คืน [(ผ่านไหม, ข้อความ)]"""
    v = []
    home, away = f["home"], f["away"]
    v.append((not _same_team(home, away) or home == "Home", f"เหย้า (ซ้าย) = {home}  |  เยือน (ขวา) = {away}"))
    xh, xa = f["x12_cur"][0], f["x12_cur"][2]
    lc = f["line_c"]
    if abs(lc) >= 0.5:
        ok = ("home" if xh < xa else "away") == ("home" if lc < 0 else "away")
        v.append((ok, f"เรต HDP ปัจจุบัน {fmt_line(lc)} ({'เจ้าบ้านต่อ' if lc < 0 else 'เจ้าบ้านรอง'}) "
                      f"{'สอดคล้อง' if ok else 'ขัดแย้ง'}กับ 1X2 ปัจจุบัน ({xh:.2f} / {xa:.2f})"
                      + ("" if ok else " -> ตรวจว่าสลับเหย้า/เยือนหรือไม่"))
                 )
    else:
        v.append((True, f"เรต HDP ปัจจุบัน {fmt_line(lc)} (ปริ่มน้ำ/เสมอ) ใช้ 1X2 ปัจจุบัน {xh:.2f} / {xa:.2f} ประกอบ"))
    al = m.get("ah_left_team")
    if al:
        if _same_team(al, home):
            v.append((True, f"คอลัมน์ซ้ายของตาราง Asian Handicap = {al} (ตรงกับเจ้าบ้าน)"))
        elif _same_team(al, away):
            v.append((False, f"คอลัมน์ซ้ายของตาราง Asian Handicap = {al} ซึ่งเป็นทีมเยือน -> เรต HDP อาจถูกอ่านกลับด้าน"))
    n = m.get("h2h_names_checked") or 0
    if n:
        bad = m.get("h2h_names_bad") or 0
        v.append((bad == 0, f"H2H ตรวจชื่อทีมเหย้า/เยือนของแต่ละนัดแล้ว {n} นัด" + (f" (ไม่ตรง {bad} นัด)" if bad else " ครบถ้วน")))
    return v


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
    if f["fav"] == "away":
        t.append("home_dog")
    for flag, name in (("high_draw", "draw_league"), ("continental", "continental"), ("women_regional", "women_regional"), ("asian_cup", "asian_cup"), ("false_giant", "false_giant"),
                       ("shield24", "shield24"), ("home_momentum", "home_momentum")):
        if f[flag]:
            t.append(name)
    if f["rank_gap"] is not None:
        if f["rank_gap"] >= P["rank_gap_dog"]:
            t.append("table:fav_below")
        elif f["rank_gap"] <= -P["rank_gap_fav"]:
            t.append("table:fav_above")
    if f["league_size"] and f["rank_away"] and f["rank_away"] > P["bottom_zone"] * f["league_size"]:
        t.append("away_bottom")
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
        lure = f["hdp_shift_fav"] > 0 or f["fav_drop_adj"] < -0.04
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
    """Anti-Fake Steam Matrix: แยก Silent Money ออกจาก Public Steam
    - เทียบค่าน้ำแบบปรับตามเรตแล้ว (fav_drop_adj/dog_drop_adj)
    - ถ้า HDP ยืนยันการไหลของพูล 1X2 (เรตขยับไปทางเดียวกัน) ไม่นับเป็น Fake Steam เว้นแต่มหาชนแห่แทงหนัก (ดู Rule 17)"""
    silent = abs(f["hdp_shift_fav"]) < 0.01 and max(f["fav_drop"], f["dog_drop"]) >= P["water_drop_min"]
    if silent:
        return []
    s = f["hdp_shift_fav"]
    out = []
    for side, pp, pct, adj, mk_fade, confirmed in (
        ("fav", f["x12_pp"], f["public_fav"], f["fav_drop_adj"], f["dog_hdp"], s >= P["crash_min"]),
        ("dog", f["dog_pp"], f["public_dog"], f["dog_drop_adj"], f["fav_hdp"], s <= -P["crash_min"]),
    ):
        if pp < P["x12_steam_pp"] or adj >= P["water_drop_min"]:
            continue
        heavy = pct is not None and pct >= 65
        if confirmed and not heavy:
            continue                                   # การไหลยืนยันกัน -> ไม่ใช่ Fake Steam
        v = 0.5 if confirmed else 0.6 + (0.4 if heavy else 0.0)
        nm = f["fav_name"] if side == "fav" else f["dog_name"]
        why = "HDP ยืนยัน แต่มหาชนแห่แทงหนัก" if confirmed else "ไม่มีลายเซ็น Silent Money และ HDP ไม่ยืนยัน"
        out.append(("R9", mk_fade, v, f"Public Steam: พูล 1X2 ของ {nm} ไหล +{pp:.1f}pp ({why}) -> Fade"))
    return out


def rule_x1(f, P):
    """Coupled Steam Confirmation: เรต HDP + พูล 1X2 + โบรกเกอร์ส่วนใหญ่ ไหลไปทางเดียวกัน
    โดยราคา (ปรับตามเรตแล้ว) ไม่แย่ลง และไม่มีหลักฐานมหาชนแห่หนัก -> ถือเป็นการไหลจริง หนุนฝั่งนั้น"""
    s = f["hdp_shift_fav"]
    if abs(s) < P["crash_min"]:
        return []
    if s > 0:
        nm, pp, adj, pct, mk = f["fav_name"], f["x12_pp"], f["fav_drop_adj"], f["public_fav"], f["fav_hdp"]
    else:
        nm, pp, adj, pct, mk = f["dog_name"], f["dog_pp"], f["dog_drop_adj"], f["public_dog"], f["dog_hdp"]
    if pp < P["x12_steam_pp"] or adj < -0.03 or (pct is not None and pct >= 65):
        return []
    ag = f.get("hdp_agree")
    agf = 0.8 if ag is None else 0.6 + 0.4 * ag
    val = min(abs(s) / 0.25, 2.0) * agf
    ag_txt = "" if ag is None else f", โบรกเกอร์ขยับทางเดียวกัน {ag:.0%}"
    return [("X1", mk, val, f"Coupled Steam: เรต HDP {s:+g} + พูล 1X2 {nm} +{pp:.1f}pp{ag_txt} ยืนยันกัน (ค่าน้ำปรับตามเรตแล้วไม่แย่ลง)")]


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


def rule17(f, P):
    """Table Control: ลีกอัตราเสมอสูง -> คุมความเสี่ยงการถือหางทีมต่อ"""
    if not f["high_draw"]:
        return []
    return [("R17", f["dog_hdp"], 0.5 if f["fav_line_c"] >= 0.75 else 0.3,
             "ลีกอัตราเสมอสูง: คุมความเสี่ยงการถือหางทีมต่อ -> เอนไปทางทีมรอง")]


def rule18(f, P):
    """Table Control: อันดับบนตารางสวนทางกับราคา"""
    g = f["rank_gap"]
    if g is None:
        return []
    if g >= P["rank_gap_dog"] and not f["class_sup"]:
        return [("R18", f["dog_hdp"], 0.6,
                 f"Table Control: ทีมต่ออันดับ {f['rank_fav']} ต่ำกว่าทีมรองอันดับ {f['rank_dog']} -> ราคาสวนทางตาราง ระวังทีมต่อ")]
    if g <= -P["rank_gap_fav"]:
        return [("R18", f["fav_hdp"], 0.4,
                 f"Table Control: ทีมต่ออันดับ {f['rank_fav']} เหนือทีมรองอันดับ {f['rank_dog']} มาก -> ราคาสอดคล้องตาราง")]
    return []


def rule19(f, P):
    """Table Control: ทีมเยือนโซนท้ายตาราง"""
    ls, ra = f["league_size"], f["rank_away"]
    if not ls or ra is None or ra <= P["bottom_zone"] * ls:
        return []
    if f["fav"] == "away":
        return [("R19", f["dog_hdp"], 0.8, f"ทีมเยือนอยู่โซนท้ายตาราง (อันดับ {ra:g}/{ls:g}) แต่เป็นทีมต่อ -> ไม่ถือหางทีมเยือน")]
    return [("R19", f["fav_hdp"], 0.5, f"ทีมเยือนอยู่โซนท้ายตาราง (อันดับ {ra:g}/{ls:g}) พลังสวนกลับต่ำ")]


def rule20(f, P):
    """Draw-Prone League: ลีกเสมอสูง เอนไปทางสกอร์ต่ำ"""
    if f["high_draw"] and f["has_ou"]:
        return [("R20", "OU_UNDER", 0.4, "ลีกอัตราเสมอสูง -> เอนไปทางสกอร์ต่ำ")]
    return []


def rule21(f, P):
    """Home Pride & Underdog Defensive Resurgence: ทีมรองเฝ้ารังในบ้าน"""
    if f["fav"] != "away" or f["home_ga"] is None or f["home_ga"] > 1.2:
        return []
    out = [("R21", "HDP_HOME", 0.8, f"Home Pride: เจ้าบ้านเป็นทีมรองแต่เสียประตูเฉลี่ยเพียง {f['home_ga']:.2f} -> ให้เกียรติเกมรับเฝ้ารัง")]
    if f["has_ou"]:
        out.append(("R21", "OU_UNDER", 0.3, "เจ้าบ้านเกมรับเหนียว หนุนสกอร์ต่ำ"))
    return out


def rule22(f, P):
    """High-Scoring League Volatility & Defensive Exposure Filter"""
    if not f["high_scoring"]:
        return []
    out = []
    if f["has_ou"]:
        out.append(("R22", "OU_OVER", 0.6, "ลีกเปิดแลก/ประตูเยอะ -> มองสกอร์สูงควบคู่"))
    if f["fav_line_c"] >= 1.0:
        out.append(("R22", f["dog_hdp"], 0.8, f"ลีกประตูเยอะ + ต่อแพง {f['fav_line_c']:g} -> เลี่ยงเรตต่อแพง"))
    if f["fav_ga"] is not None and f["fav_ga"] >= P["leak_ga"]:
        out.append(("R22", f["dog_hdp"], 0.4, f"ทีมต่อเสียประตูเฉลี่ย {f['fav_ga']:.2f} (Defensive Exposure)"))
    return out


def rule23(f, P):
    """Away Favorite Security Buffer in Balanced Tables"""
    if f["fav"] == "away" and f["fav_line_c"] <= 0.5 and f["rank_gap"] is not None and abs(f["rank_gap"]) <= 4:
        return [("R23", f["dog_hdp"], 0.8, f"ทีมเยือนต่อปริ่มน้ำ {f['fav_line_c']:g} ในตารางสูสี (ห่างกัน {abs(f['rank_gap']):g} อันดับ) -> ยกระดับตรวจสอบ")]
    return []


def rule24(f, P):
    """Continental Cup Underdog Shield: ปิด Rule 14 เมื่อทีมเยือนมีสถิติสวนกลับสูง"""
    if f["shield24"] and f["fav"] == "home":
        return [("R24", f["dog_hdp"], 0.5, "Continental Cup Shield: ปิด Class Superiority Override ทีมเยือนมีสถิติสวนกลับ > 40%")]
    return []


def rule25(f, P):
    """Home Momentum Over Market Value: เรต 0 + เจ้าบ้านไม่แพ้ในบ้าน 5 นัดและชนะ > 50%"""
    if f["home_momentum"]:
        return [("R25", "HDP_HOME", 2.0, "Home Momentum: เรตเสมอ เจ้าบ้านไม่แพ้ใน 5 นัดในบ้านและชนะ > 50% -> ห้ามสวนรอง (แบนฝั่งเยือน)")]
    return []


def rule26(f, P):
    """The False Giant Slump Shield: ทีมต่อมูลค่าสูงแต่ฟอร์ม 5 นัดชนะ <= 20% -> ตัดสิทธิ์การต่อ"""
    if f["false_giant"]:
        return [("R26", f["dog_hdp"], 1.5,
                 f"False Giant: ทีมต่อมูลค่าสูงกว่า {f['value_ratio']:.1f}x แต่ชนะเพียง {f['fav_win_rate']:.0f}% ใน 5 นัด -> ตัดสิทธิ์การต่อ (แบนถือหางทีมต่อ)")]
    return []


def rule_x2(f, P):
    """Current Odds Anchor: อ่านเจตนาโต๊ะจาก 'ราคาปัจจุบัน' ล้วน ๆ (ค่าน้ำถูกกดต่ำกว่าอีกฝั่ง)"""
    out, k = [], P["skew_min"]
    d = f["dog_water_c"] - f["fav_water_c"]            # + = ค่าน้ำทีมต่อต่ำกว่า
    if abs(d) >= k:
        mk, nm = (f["fav_hdp"], f["fav_name"]) if d > 0 else (f["dog_hdp"], f["dog_name"])
        out.append(("X2", mk, min(abs(d) / k, 2.0) * 0.5, f"Current Odds: ค่าน้ำ HDP ปัจจุบันของ {nm} ต่ำกว่าอีกฝั่ง {abs(d):.2f} (โต๊ะกดราคาฝั่งนี้)"))
    if f["has_ou"]:
        d = f["over_water_c"] - f["under_water_c"]       # + = ค่าน้ำ Under ต่ำกว่า
        if abs(d) >= k:
            mk = "OU_UNDER" if d > 0 else "OU_OVER"
            out.append(("X2", mk, min(abs(d) / k, 2.0) * 0.5, f"Current Odds: ค่าน้ำ OU ปัจจุบันฝั่ง {mk[3:]} ต่ำกว่าอีกฝั่ง {abs(d):.2f}"))
    return out


RULES = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule11, rule12, rule14, rule16,
         rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule_x1, rule_x2]
ROLE_TO_MARKET = lambda role, f: {
    "HDP_FAV": f["fav_hdp"], "HDP_DOG": f["dog_hdp"], "OU_OVER": "OU_OVER",
    "OU_UNDER": "OU_UNDER", "X12_FAV": f["fav_x12"]}[role]


# ----------------------------------------------------------------------------
# กลุ่มข้อมูลของ Rule: ใช้ในโหมดคะแนน "นับกลุ่มละครั้ง" เพื่อไม่บวก Rule ที่อิงข้อมูลเดียวกัน/ชี้ทางเดียวกันซ้ำ
# ----------------------------------------------------------------------------
RULE_GROUPS = {
    "R1": "flow", "R2": "flow", "R9": "flow", "R11": "flow", "X1": "flow",     # การไหลของราคา (เทียบราคาเปิด)
    "X2": "price",                                                              # ค่าน้ำปัจจุบัน
    "R3": "stats", "R5": "stats", "R8": "stats", "R22": "stats",               # สถิติประตู/H2H
    "R4": "context", "R6": "context", "R7": "context", "R10": "context", "R12": "context", "R16": "context",
    "R17": "context", "R20": "context", "R21": "context", "R24": "context",     # บริบทการแข่งขัน/แรงจูงใจ
    "R18": "table", "R19": "table", "R23": "table",                            # ตารางคะแนน
    "R14": "override", "R25": "override", "R26": "override",                   # กฎ override มูลค่าทีม/ฟอร์ม
}
GROUP_TH = {"flow": "การไหลของราคา", "price": "ราคาปัจจุบัน", "stats": "สถิติประตู/H2H", "context": "บริบท/แรงจูงใจ",
            "table": "ตารางคะแนน", "override": "กฎ override", "learned": "Rule ที่เรียนรู้", "experimental": "Rule ทดลอง"}


def rule_group(rid):
    return RULE_GROUPS.get(rid) or ("learned" if str(rid).startswith("L") else "experimental")


def _form_stats(f, side):
    x = ((f.get("form") or {}).get(side)) or {}
    seq = str(x.get("seq") or "").upper()
    n = len(seq)
    wr = x.get("win_rate")
    if not isinstance(wr, (int, float)):
        wr = 100.0 * seq.count("W") / n if n else None
    return wr, (seq.count("D") / n if n else None)


def _xv(f):
    """ตัวแปรช่วยสำหรับ Rule ทดลอง (ทนต่อ features รุ่นเก่าที่ขาดบางคีย์)"""
    fav = f["fav"]
    hwr, hdr = _form_stats(f, "home")
    awr, adr = _form_stats(f, "away")
    afa = f.get("away_form_away") or {}
    if all(isinstance(afa.get(k), int) for k in ("w", "d", "l")) and sum(afa[k] for k in ("w", "d", "l")) > 0:
        awr = 100.0 * afa["w"] / sum(afa[k] for k in ("w", "d", "l"))          # ใช้ฟอร์มเกมเยือนถ้ามี (R32/R34)
    vr = f.get("value_ratio")
    return {"home_ga": f.get("home_ga"), "away_ga": f.get("fav_ga") if fav == "away" else f.get("dog_ga"),
            "hwr": hwr, "awr": awr, "hdr": hdr, "adr": adr,
            "hv": None if vr is None else (vr if fav == "home" else 1.0 / vr),
            "rh": f.get("rank_home"), "ra": f.get("rank_away"), "size": f.get("league_size"),
            "line": f["fav_line_c"], "fav_away": fav == "away"}


def _bottom(f, side, P):
    x = _xv(f)
    r = x["rh"] if side == "home" else x["ra"]
    return bool(x["size"] and r is not None and r > P["bottom_zone"] * x["size"])


def _exp(rec, veto, note, flow_only=False):
    return {"rec": rec, "veto": veto, "note": note, "flow_only": flow_only}


def exp28(f, P, c):
    x = _xv(f)
    if x["fav_away"] and x["ra"] is not None and x["rh"] is not None and x["ra"] <= 3 and x["rh"] <= 6 and x["line"] <= 0.25:
        return _exp([("HDP_HOME", 1.2), ("OU_UNDER", 1.0)], ["HDP_AWAY"], "R28: ทีมเยือนท็อป 3 ไปเยือนทีมหัวตาราง เรตบางเฉียบ -> เสี่ยงเสมอ เลี่ยงทีมต่อ")


def exp29(f, P, c):
    if f.get("women_regional") and f.get("rank_gap") is not None and abs(f["rank_gap"]) <= 4:
        net = sum(x["eff"] * (1 if x["market"] == "HDP_HOME" else -1) for x in c if x.get("group") in ("flow", "price") and x["market"] in ("HDP_HOME", "HDP_AWAY"))
        if abs(net) > 1e-9:
            return _exp([("HDP_HOME" if net > 0 else "HDP_AWAY", abs(net))], [], "R29: ฟุตบอลหญิง/ลีกรองภูมิภาค อันดับใกล้กัน -> ยึดกระแสราคา 100%", flow_only=True)


def exp30(f, P, c):
    x = _xv(f)
    if _bottom(f, "home", P) and x["ra"] is not None and abs(x["ra"] - x["rh"]) <= 6 and x["line"] <= 0.25:
        return _exp([("HDP_HOME", 1.2)], ["HDP_AWAY"], "R30: เจ้าบ้านบ๊วยหนีตายเปิดบ้านเรตปริ่มน้ำ -> ห้ามเลือกทีมเยือน")


def exp31(f, P, c):
    x = _xv(f)
    if x["line"] >= 1.5 and f.get("dog_ga") is not None and f["dog_ga"] <= 1.0:
        return _exp([(f["dog_hdp"], 1.0), ("OU_UNDER", 1.0)], [f["fav_hdp"]], "R31: เรตต่อ >= 1.5 ทีมรองตั้งรับเหนียว (ประมาณจากประตูเสีย <= 1.0) -> เลี่ยงทีมต่อ")


def exp32(f, P, c):
    x = _xv(f)
    if x["awr"] is not None and x["awr"] >= 80 and x["line"] <= 0.5:
        return _exp([("HDP_AWAY", 1.5)], ["HDP_HOME"], "R32: ทีมเยือนชนะ >= 80% เรตตื้น -> ตามฟอร์มเยือน")


def exp33(f, P, c):
    x = _xv(f)
    if _bottom(f, "home", P) and x["home_ga"] is not None and x["home_ga"] > 2.0 and x["ra"] is not None and x["size"] and x["ra"] <= 0.5 * x["size"]:
        return _exp([("HDP_AWAY", 1.5)], ["HDP_HOME"], "R33: เจ้าบ้านบ๊วยเสียเฉลี่ย > 2 " + ("ในบ้าน" if f.get("venue_stats") else "(5 นัดหลัง รวมเหย้า-เยือน)") + " พบทีมกลุ่มบน -> ห้ามเลือกเจ้าบ้าน")


def exp34(f, P, c):
    x = _xv(f)
    if f.get("continental") and x["hv"] is not None and x["hv"] >= 1.5 and x["awr"] is not None and x["awr"] >= 60 and x["line"] <= 0.5:
        return _exp([("HDP_HOME", 1.2)], ["HDP_AWAY"], "R34: บอลถ้วยทวีป เจ้าบ้านยักษ์ใหญ่ ทีมเยือนฟอร์มร้อน เรตตื้น -> ห้ามสวนเจ้าบ้าน")


def exp35(f, P, c):
    if f.get("asian_cup") and f["fav"] == "home" and f["fav_line_c"] >= 1.5 and f.get("rank_dog") is not None and f["rank_dog"] <= 5:
        return _exp([(f["dog_hdp"], 1.0)], [], "R35: บอลถ้วยเอเชีย ต่อเรตสูงลิ่ว คู่แข่งกลุ่มหัวตาราง -> เลี่ยงทีมต่อ")


def exp36(f, P, c):
    x = _xv(f)
    if f.get("high_vol") and x["home_ga"] is not None and x["away_ga"] is not None and x["home_ga"] > 1.5 and x["away_ga"] > 1.5:
        return _exp([("OU_OVER", 1.5)], [f["fav_hdp"]] if x["line"] >= 1.0 else [], "R36: ลีกผันผวนสูง เกมรับรั่วทั้งคู่ -> เลี่ยงเรตต่อแพง มองสูง")


def exp37(f, P, c):
    x = _xv(f)
    if (f.get("ctx_type") == "cup" or f.get("cup_group")) and x["fav_away"] and x["line"] <= 0.5 and x["home_ga"] is not None and x["home_ga"] <= 1.2:
        return _exp([("HDP_HOME", 1.0)], ["HDP_AWAY"], "R37: บอลถ้วย เจ้าบ้านเหนียว เรตต่อตื้น -> ตัดสิทธิ์ทีมเยือนเป็นต่อ")


def exp38(f, P, c):
    x = _xv(f)
    if x["line"] <= 0.25 and x["hdr"] is not None and x["adr"] is not None and x["hdr"] >= 0.4 and x["adr"] >= 0.4:
        return _exp([("OU_UNDER", 1.5)], [f["fav_hdp"], f["fav_x12"]], "R38: เรตปริ่มน้ำ ทั้งสองทีมเสมอ >= 40% ใน 5 นัด -> เลี่ยงผลชนะ/แพ้ มองต่ำ")


def exp39(f, P, c):
    x = _xv(f)
    if f["fav"] == "home" and x["home_ga"] is not None and x["home_ga"] > 1.5:
        return _exp([("HDP_AWAY", 1.0)], ["HDP_HOME"], "R39/R41: เจ้าบ้านเป็นต่อแต่เสียเฉลี่ย > 1.5 " + ("ในบ้าน" if f.get("venue_stats") else "(5 นัดหลัง รวมเหย้า-เยือน)") + " -> ตัดสิทธิ์ถือหางเจ้าบ้าน")


def exp40(f, P, c):
    x = _xv(f)
    vr = f.get("value_ratio")
    if x["fav_away"] and vr is not None and vr >= 2 and f.get("fav_win_rate") is not None and f["fav_win_rate"] <= 40:
        return _exp([("HDP_HOME", 1.0)], ["HDP_AWAY"], "R40: ยักษ์เยือนฟอร์มสะดุด -> ห้ามถือหางทีมเยือน")


def exp42(f, P, c):
    t = f.get("tn_xg_total")
    if t is not None and f.get("has_ou"):
        d = t - f["ou_c"]
        if abs(d) >= 0.5:
            mk = "OU_OVER" if d > 0 else "OU_UNDER"
            return _exp([(mk, 1.0)], [], f"R42: xG รวมคาดการณ์ {t:.2f} {'สูง' if d > 0 else 'ต่ำ'}กว่าเรต {f['ou_c']:g} ({d:+.2f}) -> {'สูง' if d > 0 else 'ต่ำ'}")


def exp43(f, P, c):
    o = f.get("tn_fav_overperf")
    if o is not None and abs(o) >= 0.6:
        if o > 0:
            return _exp([(f["dog_hdp"], 1.0)], [], f"R43: ทีมต่อได้ผลดีกว่าเนื้อเกม (xG) {o:+.2f}/นัด -> เสี่ยงกลับสู่ค่าเฉลี่ย ถือรอง")
        return _exp([(f["fav_hdp"], 1.0)], [], f"R43: ทีมต่อเล่นดีกว่าผลที่ได้ (xG) {o:+.2f}/นัด -> ผลน่าจะดีขึ้น ถือต่อ")


def exp44(f, P, c):
    a, b = f.get("tn_fav_starters_out"), f.get("tn_dog_starters_out")
    if a is None or b is None:
        return None
    if a - b >= 2 or (f.get("tn_fav_gk_out") and a > b):
        return _exp([(f["dog_hdp"], 1.0)], [], f"R44: ทีมต่อขาดตัวจริง {a} คน (ทีมรอง {b}){' รวมผู้รักษาประตู' if f.get('tn_fav_gk_out') else ''} -> ถือรอง")
    if b - a >= 2:
        return _exp([(f["fav_hdp"], 1.0)], [], f"R44: ทีมรองขาดตัวจริง {b} คน (ทีมต่อ {a}) -> ถือต่อ")


def exp45(f, P, c):
    a, b = f.get("tn_fav_rest"), f.get("tn_dog_rest")
    if a is None or b is None:
        return None
    if a <= 3 and b >= 5:
        return _exp([(f["dog_hdp"], 1.0)], [], f"R45: ทีมต่อพัก {a} วัน ทีมรองพัก {b} วัน -> ระวังทีมต่อล้า ถือรอง")
    if b <= 3 and a >= 5:
        return _exp([(f["fav_hdp"], 1.0)], [], f"R45: ทีมรองพัก {b} วัน ทีมต่อพัก {a} วัน -> ทีมต่อสดกว่า")


def exp46(f, P, c):
    if f.get("tn_fav_rotation") and not f.get("tn_dog_rotation"):
        return _exp([(f["dog_hdp"], 1.0)], [], "R46: บอลถ้วย มีข่าวยืนยันว่าทีมต่อจะหมุนเวียน/พักตัวหลัก -> ถือรอง")


# Rule ทดลองจากเอกสารของผู้ใช้ (R28-R41): เริ่มเป็น "เงา" (ประเมินเบื้องหลังเท่านั้น) จนกว่าจะผ่านเกณฑ์นอกกลุ่มตัวอย่าง
EXPERIMENTAL = {"R28": exp28, "R29": exp29, "R30": exp30, "R31": exp31, "R32": exp32, "R33": exp33, "R34": exp34,
                "R35": exp35, "R36": exp36, "R37": exp37, "R38": exp38, "R39": exp39, "R40": exp40,
                "R42": exp42, "R43": exp43, "R44": exp44, "R45": exp45, "R46": exp46}   # R42-R46: ข้อมูลทีม (xG/ตัวเจ็บ/วันพัก/หมุนเวียน)


for _rid in ("R28", "R31"):                       # Rule ทดลองที่มี 2 ตลาด
    RULE_NAMES.setdefault(_rid + "b", RULE_NAMES.get(_rid, _rid) + " (ส่วนที่ 2: สูง/ต่ำ)")


def _wilson_lo(w, n, z):
    return wilson(w / n, n, z)[0] if n else 0.0


def _wilson_hi(w, n, z):
    return wilson(w / n, n, z)[1] if n else 1.0


def _declining(results, W, be):
    """อัตราชนะลดลงต่อเนื่อง 3 ช่วงล่าสุด (ช่วงละ W ครั้ง ไม่นับเจ๊า) และช่วงล่าสุดต่ำกว่าจุดคุ้มทุน"""
    dec = [x for x in results if x != 0]
    if len(dec) < 3 * W:
        return False
    wins = [sum(1 for x in dec[-3 * W + i * W: len(dec) - (2 - i) * W] if x > 0) / W for i in range(3)]
    return wins[0] > wins[1] > wins[2] and wins[2] < be


def lifecycle_update(store, f, outcomes):
    """ติดตามผลนอกกลุ่มตัวอย่างของ Rule ผู้สมัครทุกข้อที่เงื่อนไขตรงกับนัดนี้ (ทั้งเงาและที่ใช้งานอยู่)
    แล้วตัดสินสถานะ: เงา -> ปลดล็อค (ผ่านเกณฑ์) / ถอด (ไม่มีประโยชน์ สวนทาง หรือแย่ลงต่อเนื่อง)
    เรียกก่อน discover_rules ของนัดเดียวกัน เพื่อให้ผลที่นับเป็นผลที่ Rule ยังไม่เคยเห็น คืนรายการที่เปลี่ยนสถานะ"""
    if getattr(store, "legacy_learned", False) and not getattr(store, "include_manual", True):
        return []
    P, S = store.params, store.state
    life = S.setdefault("lifecycle", {})
    seq = S.setdefault("meta", {}).get("settled", 0) + 1
    base = _build_contribs(_base_raw(f, P), f, P, S)
    changes = []
    be = P["breakeven_wr"]
    for rid, c in candidates_for(f, P, store, base).items():
        if c["market"] not in outcomes:
            continue
        e = life.setdefault(rid, {"kind": c["kind"], "status": "shadow", "n": 0, "w": 0, "l": 0, "res": [],
                                  "since": seq, "reason": "เริ่มติดตามผลเบื้องหลัง"})
        if e["status"] == "retired":
            continue
        r = outcomes[c["market"]][0]
        e["n"] += 1
        e["w"] += r > 0
        e["l"] += r < 0
        e["res"] = (e["res"] + [round(r, 2)])[-120:]
        dec = e["w"] + e["l"]
        wr = e["w"] / dec if dec else 0.0
        old = e["status"]
        new, why = old, None
        if dec >= P["retire_min_n"] and _wilson_hi(e["w"], dec, P["lb_z_judge"]) < be:
            new, why = "retired", f"สวนทาง: อัตราชนะ {wr:.0%} ต่ำกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ ({e['w']}/{dec})"
        elif old == "active" and _declining(e["res"], P["decline_window"], be):
            new, why = "retired", f"อัตราชนะลดลงต่อเนื่อง 3 ช่วงล่าสุดจนต่ำกว่าจุดคุ้มทุน (รวม {wr:.0%})"
        elif old == "shadow":
            if dec >= P["unlock_min_n"] and wr >= P["unlock_wr"] and _wilson_lo(e["w"], dec, P["lb_z_fast"]) > be:
                new, why = "active", f"ผ่านเกณฑ์ทางลัด: ชนะ {wr:.0%} จาก {dec} ครั้ง (≥ {P['unlock_wr']:.0%}) นอกกลุ่มตัวอย่าง"
            elif e["n"] >= P["judge_n"]:
                if _wilson_lo(e["w"], dec, P["lb_z_judge"]) > be:
                    new, why = "active", f"ครบ {e['n']} ครั้ง: ชนะ {wr:.0%} สูงกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ"
                else:
                    new, why = "retired", f"ครบ {e['n']} ครั้ง: ชนะ {wr:.0%} ไม่ดีกว่าจุดคุ้มทุนอย่างมีนัยสำคัญ -> ไม่มีประโยชน์"
        if new == "active" and old == "shadow" and P.get("lock_unlocks"):
            if not e.get("ready"):                     # ผ่านเกณฑ์แล้วแต่ล็อกอยู่ -> คงเป็นเงา รอผู้ใช้ปลดล็อก
                e["ready"], e["ready_at"] = True, seq
                e["reason"] = why + " — รอเปิดใช้ (ล็อกสถานะ Rule อยู่)"
            new = old
        elif old == "shadow" and e.get("ready") and new == "shadow" and not P.get("lock_unlocks"):
            new, why = "active", "ผ่านเกณฑ์ไว้แล้วระหว่างล็อก เปิดใช้เมื่อปลดล็อก"
        if new == "retired":
            e.pop("ready", None)
        if new != old:
            e["status"], e["reason"], e["since"] = new, why, seq
            changes.append((rid, old, new, why))
    return changes


def market_role(mk, f):
    if mk == f.get("fav_hdp"):
        return "HDP_FAV"
    if mk == f.get("dog_hdp"):
        return "HDP_DOG"
    if mk in ("OU_OVER", "OU_UNDER"):
        return mk
    if mk == f.get("fav_x12"):
        return "X12_FAV"
    return None


def rule_status(store, rid, kind):
    """สถานะของ Rule ผู้สมัคร: shadow (เงา/ระงับ) | active (ใช้งาน) | retired (ถอด)"""
    if kind == "learned" and getattr(store, "legacy_learned", False):
        return "active"                                  # นโยบายเดิม (ใช้ทุก Rule ทันที) สำหรับเทียบใน backtest
    e = (store.state.get("lifecycle") or {}).get(rid)
    return e["status"] if e else "shadow"


X12_ROLE_REASON = ("ไม่ใช้: Rule แบบ 1X2 ไม่ถูกนำไปคิดคะแนนฟันธง และเกณฑ์ 'ชนะเกิน 50%' ใช้กับราคา 1X2 ไม่ได้ "
                   "(ทีมต่อชนะเกินครึ่งอยู่แล้วโดยไม่มีกำไร)")


def retire_x12_learned(state):
    """ถอด Rule ที่ระบบสร้างเองซึ่งชี้ตลาด 1X2 (ไม่มีผลต่อการฟันธง + เกณฑ์ค้นพบไม่ถูกต้องสำหรับราคาไม่ใช่ 1:1) คืนจำนวนที่ถอด"""
    life = state.setdefault("lifecycle", {})
    n = 0
    for lr in state.get("learned_rules", []):
        if str(lr.get("role", "")).startswith("X12"):
            e = life.setdefault(lr["id"], {"kind": "learned", "n": 0, "w": 0, "l": 0, "res": [], "since": 0})
            if e.get("status") != "retired" or lr.get("enabled", True):
                n += 1
            e["status"], e["reason"] = "retired", X12_ROLE_REASON
            lr["enabled"] = False
    return n


def candidates_for(f, P, store, contribs=None):
    """Rule ผู้สมัคร (ที่ระบบสร้างเอง + Rule ทดลอง) ที่เงื่อนไขตรงกับแมตช์นี้ -> {id: {kind, market, role, rec, veto, note, flow_only}}"""
    out = {}
    for lr in store.state.get("learned_rules", []):
        if lr.get("enabled", True) and not str(lr["role"]).startswith("X12") and set(lr["tags"]) <= set(f.get("tags", [])):
            mk = ROLE_TO_MARKET(lr["role"], f)
            out[lr["id"]] = {"kind": "learned", "market": mk, "role": lr["role"], "rec": [(mk, lr["strength"])], "veto": [],
                             "flow_only": False,
                             "note": f"Learned {lr['id']}: [{' + '.join(lr['tags'])}] -> {ROLE_TH[lr['role']]} (ชนะ {lr['wr']:.0%} จาก {lr['n']:.0f} นัด)"}
    if getattr(store, "include_manual", True):
        for rid, fn in EXPERIMENTAL.items():
            try:
                r = fn(f, P, contribs or [])
            except Exception:  # noqa  (features รุ่นเก่าไม่ครบ)
                r = None
            if r and r.get("rec"):
                mk = r["rec"][0][0]
                out[rid] = {"kind": "manual", "market": mk, "role": market_role(mk, f), "rec": r["rec"][:1], "veto": r.get("veto", []),
                            "flow_only": r.get("flow_only", False), "note": r["note"]}
                # Rule ที่แนะนำมากกว่า 1 ตลาด: ตลาดถัดไปถูกติดตามผล/ปลดล็อคแยกกัน (เดิมถูกตัดสินจากตลาดแรกอย่างเดียว)
                for i, (mk2, val2) in enumerate(r["rec"][1:]):
                    sid = rid + "bcd"[i]
                    RULE_NAMES.setdefault(sid, RULE_NAMES.get(rid, rid) + " (ส่วนที่ 2: " + ("สูง/ต่ำ" if mk2.startswith("OU") else "แฮนดิแคป") + ")")
                    out[sid] = {"kind": "manual", "market": mk2, "role": market_role(mk2, f), "rec": [(mk2, val2)], "veto": [],
                                "flow_only": False, "note": r["note"] + " [ส่วนที่ 2]"}
    return out


# ----------------------------------------------------------------------------
# 4) State (น้ำหนัก + Rule ที่เรียนรู้) และ History
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# ซิงก์ข้อมูลเรียนรู้ไปเก็บที่ GitHub Gist (กันข้อมูลหายเมื่อ Streamlit Cloud รีสตาร์ท)
# ตั้งค่าด้วยตัวแปร GITHUB_TOKEN (สิทธิ์ Gists: read/write) และ GIST_ID — ถ้าไม่ตั้ง ระบบทำงานเฉพาะในเครื่องเหมือนเดิม
# ----------------------------------------------------------------------------
REMOTE_STATE = {"enabled": False, "ok": None, "error": None, "last": None, "blocked": False, "backend": None}
GIST_FILES = ("state.json", "history.json")
_PULL_TRIED = set()


def _gist_cfg():
    tok, gid = (os.environ.get("GITHUB_TOKEN") or "").strip(), (os.environ.get("GIST_ID") or "").strip()
    return (tok, gid) if tok and gid else None


def _gh_headers(tok):
    return {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "football-quant", "Content-Type": "application/json"}


def _gh(method, url, tok, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=_gh_headers(tok))
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def _remote_err(e):
    if isinstance(e, RuntimeError):
        return str(e)
    if isinstance(e, urllib.error.HTTPError):
        hint = {401: "token ไม่ถูกต้อง/หมดอายุ", 403: "token ไม่มีสิทธิ์ Gists หรือโดนจำกัดการเรียก",
                404: "ไม่พบ Gist (ตรวจ GIST_ID และสิทธิ์ของ token)"}.get(e.code, "")
        return f"GitHub {e.code} {hint}".strip()
    if isinstance(e, urllib.error.URLError):
        return f"เชื่อมต่อ GitHub ไม่ได้: {e.reason}"
    return f"{type(e).__name__}: {str(e)[:120]}"


def _gist_pull():
    """ดึง state/history จาก Gist คืน dict {ชื่อไฟล์: ข้อมูล} หรือ None ถ้าไม่ได้ตั้งค่า/ล้มเหลว"""
    cfg = _gist_cfg()
    if not cfg:
        return None
    tok, gid = cfg
    REMOTE_STATE["enabled"] = True
    try:
        g = _gh("GET", f"https://api.github.com/gists/{gid}", tok)
        out = {}
        for name in GIST_FILES:
            fo = (g.get("files") or {}).get(name)
            if not fo:
                continue
            text = fo.get("content")
            if fo.get("truncated") or text is None:       # ไฟล์ใหญ่ API ตัดเนื้อหา -> ดึงจาก raw_url
                req = urllib.request.Request(fo["raw_url"], headers=_gh_headers(tok))
                with urllib.request.urlopen(req, timeout=30) as r:
                    text = r.read().decode("utf-8")
            out[name] = json.loads(text) if text and text.strip() else None
        REMOTE_STATE.update(ok=True, error=None, last=now_th("%H:%M:%S"))
        return out
    except Exception as e:  # noqa
        REMOTE_STATE.update(ok=False, error=_remote_err(e))
        return None


def _gist_push(state, history):
    cfg = _gist_cfg()
    if not cfg:
        return False
    tok, gid = cfg
    REMOTE_STATE["enabled"] = True
    if REMOTE_STATE.get("blocked"):
        REMOTE_STATE.update(ok=False, error="ข้ามการซิงก์ขึ้นคลาวด์: ดึงข้อมูลเดิมจากคลาวด์ไม่สำเร็จ (กันการเขียนทับด้วยข้อมูลว่าง) กด “ดึงข้อมูลจากคลาวด์” เพื่อลองใหม่")
        return False
    try:
        _gh("PATCH", f"https://api.github.com/gists/{gid}", tok, {"files": {
            "state.json": {"content": json.dumps(state, ensure_ascii=False)},
            "history.json": {"content": json.dumps(history, ensure_ascii=False)}}})
        REMOTE_STATE.update(ok=True, error=None, last=now_th("%H:%M:%S"))
        return True
    except Exception as e:  # noqa
        REMOTE_STATE.update(ok=False, error=_remote_err(e))
        return False


def _sheets_cfg():
    url, tok = (os.environ.get("SHEETS_URL") or "").strip(), (os.environ.get("SHEETS_TOKEN") or "").strip()
    return (url, tok) if url and tok else None


def remote_backend():
    """เลือกที่เก็บข้อมูลถาวร: Google Sheets (ถ้าตั้งค่า) > GitHub Gist > ไม่มี"""
    return "sheets" if _sheets_cfg() else ("gist" if _gist_cfg() else None)


def _cell(v):
    if isinstance(v, bool) or v is None:
        return "" if v is None else str(v)
    if isinstance(v, (int, float)):
        return v
    v = str(v)
    return " " + v if v[:1] in ("=", "+", "-", "@") else v        # กัน Google Sheets ตีความเป็นสูตร


def sheet_views(state, history):
    """ตารางอ่านง่ายสำหรับแสดงใน Google Sheets"""
    hist = [["id", "บันทึกเมื่อ", "เหย้า", "เยือน", "ลีก", "สัญญาณฟันธง", "ระดับสัญญาณ", "ราคาดีที่สุด", "สถานะ", "สกอร์", "ผล", "กำไร/ขาดทุน (หน่วย)"]]
    for r in reversed(history):
        fe, pk = r.get("features") or {}, r.get("pick") or {}
        done = r.get("status") == "settled"
        hist.append([_cell(x) for x in (
            r.get("id", ""), r.get("created", ""), fe.get("home", ""), fe.get("away", ""), fe.get("league", ""),
            pk.get("label", ""), pk.get("tier", ""),
            (f'{pk["best"]["book"]} @{pk["best"]["price"]:.2f}' if pk.get("best") else ""),
            "บันทึกผลแล้ว" if done else "รอผล", "-".join(map(str, r.get("score") or [])),
            result_word(r["pick_r"]) if done and "pick_r" in r else "", r.get("pick_profit", "") if done else "")])
    wt = [["Rule", "ชื่อ", "น้ำหนัก", "ใช้ (ครั้ง)"]]
    for k, v in sorted((state.get("weights") or {}).items()):
        wt.append([_cell(k), _cell(RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง")), round(v, 4),
                   (state.get("rule_stats") or {}).get(k, {}).get("n", 0)])
    lr = [["id", "สถานะ", "เงื่อนไข", "เล่น", "ชนะ %", "จำนวนนัด", "strength"]]
    for r in state.get("learned_rules") or []:
        lr.append([_cell(r.get("id")), "เปิด" if r.get("enabled", True) else "ปิด", _cell(" + ".join(r.get("tags", []))),
                   _cell(ROLE_TH.get(r.get("role"), r.get("role"))), round(100 * r.get("wr", 0), 1), r.get("n", 0), r.get("strength", "")])
    return {"ประวัติ": hist, "น้ำหนัก Rule": wt, "Rule ที่ระบบสร้างเอง": lr}


def _sheets_call(payload):
    url, tok = _sheets_cfg()
    body = json.dumps(dict(payload, token=tok)).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:         # Apps Script ตอบด้วย 302 -> urllib ตามไปดึงผลให้เอง
        raw = resp.read().decode("utf-8", "replace")
    try:
        out = json.loads(raw)
    except ValueError:
        raise RuntimeError("Google Sheets ตอบกลับไม่ใช่ JSON — ตรวจว่า Deploy เป็น Web app, Execute as = Me และ Who has access = Anyone")
    if not out.get("ok"):
        raise RuntimeError("Google Sheets: " + str(out.get("error"))[:150])
    return out


def remote_pull():
    """ดึง state/history จากที่เก็บถาวร คืน dict {ชื่อไฟล์: ข้อมูล} หรือ None ถ้าไม่ได้ตั้งค่า/ล้มเหลว"""
    be = remote_backend()
    if not be:
        return None
    if be == "gist":
        REMOTE_STATE.update(enabled=True, backend="gist")
        return _gist_pull()
    REMOTE_STATE.update(enabled=True, backend="sheets")
    try:
        out = _sheets_call({"action": "pull"})
        REMOTE_STATE.update(ok=True, error=None, last=now_th("%H:%M:%S"))
        return {"state.json": out.get("state"), "history.json": out.get("history")}
    except Exception as e:  # noqa
        REMOTE_STATE.update(ok=False, error=_remote_err(e))
        return None


def remote_push(state, history):
    be = remote_backend()
    if not be:
        return False
    REMOTE_STATE.update(enabled=True, backend=be)
    if REMOTE_STATE.get("blocked"):
        REMOTE_STATE.update(ok=False, error="ข้ามการซิงก์: ดึงข้อมูลเดิมจากที่เก็บถาวรไม่สำเร็จ (กันการเขียนทับด้วยข้อมูลว่าง) กด “ดึงข้อมูลจากคลาวด์” เพื่อลองใหม่")
        return False
    if be == "gist":
        return _gist_push(state, history)
    try:
        _sheets_call({"action": "push", "state": state, "history": history, "views": sheet_views(state, history)})
        REMOTE_STATE.update(ok=True, error=None, last=now_th("%H:%M:%S"))
        return True
    except Exception as e:  # noqa
        REMOTE_STATE.update(ok=False, error=_remote_err(e))
        return False


def _valid_remote(data):
    st_, hi = (data or {}).get("state.json"), (data or {}).get("history.json")
    return (st_ if isinstance(st_, dict) and st_.get("weights") else None,
            hi if isinstance(hi, list) and hi else None)


class Store:
    def __init__(self, d):
        self.dir = d
        os.makedirs(d, exist_ok=True)
        self.state_p = os.path.join(d, "state.json")
        self.hist_p = os.path.join(d, "history.json")
        key_ = os.path.abspath(d)
        if (not os.path.exists(self.state_p) and not os.path.exists(self.hist_p)
                and remote_backend() and key_ not in _PULL_TRIED):
            _PULL_TRIED.add(key_)
            data_ = remote_pull()
            REMOTE_STATE["blocked"] = data_ is None          # ดึงไม่สำเร็จ -> ห้าม push ทับจนกว่าจะดึงสำเร็จ
            st_, hi = _valid_remote(data_)
            for path, obj in ((self.state_p, st_), (self.hist_p, hi)):
                if obj is not None:
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(obj, fh, ensure_ascii=False, indent=1)
        self.state = self._load(self.state_p, {
            "weights": dict(DEFAULT_WEIGHTS), "rule_stats": {}, "learned_rules": [],
            "params": {}, "meta": {"next_learned": 1, "schema": "6.0"}, "lifecycle": {}})
        self._migrate()
        for k, v in DEFAULT_WEIGHTS.items():
            self.state["weights"].setdefault(k, v)
        retire_x12_learned(self.state)
        self.history = self._load(self.hist_p, [])
        ren = getattr(self, "_pending_migration", None)
        if ren:
            for r in self.history:
                for c in r.get("contribs", []):
                    if c.get("rule") in ren:
                        c["rule"] = ren[c["rule"]]

    def _migrate(self):
        """V5.8 -> V5.9: R17 เดิม (Coupled Steam) -> R27
        V5.9 -> V6.0: R27 (Coupled Steam) -> X1, R28 (Current Odds Anchor) -> X2 เพราะ R27-R41 เป็นกฎชุดใหม่
        และ Rule ที่ระบบสร้างเองทั้งหมดเริ่มสถานะ "เงา" (ระงับ) จนกว่าจะผ่านเกณฑ์นอกกลุ่มตัวอย่าง"""
        meta = self.state.setdefault("meta", {"next_learned": 1})
        w, rs = self.state.setdefault("weights", {}), self.state.setdefault("rule_stats", {})
        sch = meta.get("schema")
        if sch == "6.0":
            return
        ren = {"R27": "X1", "R28": "X2"} if sch == "5.9" else {"R17": "X1"}
        for d in (w, rs):
            for old in list(ren):
                if old in d and ren[old] not in d:
                    d[ren[old]] = d.pop(old)
        self.state.setdefault("lifecycle", {})
        meta["schema"] = "6.0"
        self._pending_migration = ren

    @staticmethod
    def _load(p, default):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        return default

    def save(self, push=True):
        for p, obj in ((self.state_p, self.state), (self.hist_p, self.history)):
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
        if push:
            remote_push(self.state, self.history)       # ล้มเหลวได้ (ข้อมูลในเครื่องยังอยู่) ดูสถานะที่ REMOTE_STATE

    def pull_remote(self):
        """ดึงข้อมูลจากคลาวด์มาเขียนทับในเครื่อง คืน True ถ้าสำเร็จ"""
        data_ = remote_pull()
        if data_ is None:
            return False
        REMOTE_STATE["blocked"] = False
        st_, hi = _valid_remote(data_)
        if st_ is None and hi is None:
            return True                                     # คลาวด์ว่างเปล่า (เริ่มต้นใหม่) ไม่ใช่ความผิดพลาด
        if st_ is not None:
            self.state = st_
        if hi is not None:
            self.history = hi
        for k, v in DEFAULT_WEIGHTS.items():
            self.state["weights"].setdefault(k, v)
        self._migrate()
        retire_x12_learned(self.state)
        self.save(push=False)
        return True

    @property
    def params(self):
        p = dict(DEFAULT_PARAMS)
        p.update(self.state.get("params", {}))
        return p


# ----------------------------------------------------------------------------
# 5) Engine: รวมคะแนน + Single Best Pick (Rule 13)
# ----------------------------------------------------------------------------
def analyze_match(m, store):
    f, contribs, pick = analyze_features(m, build_features(m, store.params), store)
    gate_check(store, f, pick)
    return f, contribs, pick


# ----------------------------------------------------------------------------
# ตัวกรองช่วงคะแนน (ขั้นสุดท้ายก่อนลงทุน): เทียบไม้ที่ฟันธงกับผลจริงในอดีตของ
# "ประเภทไม้ (ต่อ/รอง/สูง/ต่ำ) × ช่วงคะแนน" ถ้าช่วงนั้นชนะต่ำกว่าจุดคุ้มทุนหรือขาดทุน -> งดลงทุน (ไม้เงา)
# สถิตินับจากทุกไม้ที่บันทึกผลแล้ว รวมไม้ที่ถูกงด เพื่อให้ช่วงที่ถูกงดกลับมาผ่านได้ถ้าผลดีขึ้น
# ----------------------------------------------------------------------------
GATE_KIND_TH = {"fav": "แฮนดิแคปทีมต่อ", "dog": "แฮนดิแคปทีมรอง", "over": "สูง (Over)", "under": "ต่ำ (Under)"}


def gate_kind(f, mk):
    if str(mk).startswith("HDP"):
        return "fav" if mk == f.get("fav_hdp") else "dog"
    if str(mk).startswith("OU"):
        return "over" if mk == "OU_OVER" else "under"
    return None


def gate_bucket(strength, edges):
    import bisect
    return bisect.bisect_right(list(edges), float(strength))


def gate_label(i, edges):
    e = list(edges)
    if i == 0:
        return f"< {e[0]:g}"
    if i >= len(e):
        return f"≥ {e[-1]:g}"
    return f"{e[i - 1]:g}–{e[i]:g}"


def gate_table(history, P):
    """สถิติจริงของแต่ละ (ประเภทไม้, ช่วงคะแนน) จากทุกไม้ที่บันทึกผลแล้ว"""
    edges = P.get("gate_edges") or DEFAULT_PARAMS["gate_edges"]
    tab = {}
    for r in history:
        if r.get("status") != "settled" or "pick_r" not in r:
            continue
        k = gate_kind(r["features"], r["pick"]["market"])
        if k is None:
            continue
        key = (k, gate_bucket(r["pick"]["strength"], edges))
        t = tab.setdefault(key, {"n": 0, "w": 0, "l": 0, "profit": 0.0})
        t["n"] += 1
        t["w"] += r["pick_r"] > 0
        t["l"] += r["pick_r"] < 0
        t["profit"] += r["pick_profit"]
    for t in tab.values():
        dec = t["w"] + t["l"]
        t["wr"] = t["w"] / dec if dec else None
    return tab


def gate_status(t, P):
    if not t or t["n"] < P.get("gate_min_n", 20):
        return "data"
    if (t["wr"] is not None and t["wr"] < P["breakeven_wr"]) or t["profit"] < 0:
        return "fail"
    return "pass"


def gate_check(store, f, pick, history=None):
    """ตัดสินขั้นสุดท้าย: แนบผลตัวกรองไว้ที่ pick["gate"] และงดลงทุน (ข้าม) ถ้าช่วงนั้นไม่ผ่าน"""
    P = store.params
    k = gate_kind(f, pick["market"])
    if k is None:
        return None
    edges = P.get("gate_edges") or DEFAULT_PARAMS["gate_edges"]
    b = gate_bucket(pick["strength"], edges)
    t = gate_table(store.history if history is None else history, P).get((k, b))
    stt = gate_status(t, P)
    g = {"kind": k, "kind_th": GATE_KIND_TH[k], "bucket": b, "label": gate_label(b, edges), "status": stt,
         "n": t["n"] if t else 0, "w": t["w"] if t else 0, "l": t["l"] if t else 0,
         "wr": t["wr"] if t else None, "profit": round(t["profit"], 2) if t else 0.0,
         "enabled": bool(P.get("gate_enabled", True)), "min_n": P.get("gate_min_n", 20)}
    pick["gate"] = g
    if stt == "fail" and g["enabled"] and not pick.get("skip"):
        pick["skip"] = True
        pick["gate_suspended"] = True
        pick.setdefault("skip_reasons", []).append(
            f"ตัวกรองช่วงคะแนน: {g['kind_th']} คะแนน {g['label']} ที่ผ่านมาชนะ {g['w']}-{g['l']}"
            + (f" ({g['wr']:.0%})" if g["wr"] is not None else "") + f" กำไร {g['profit']:+.2f} จาก {g['n']} ไม้ → งดลงทุน")
    return g


def _build_contribs(raw, f, P, S):
    out = []
    for rid, mk, val, note in raw:
        w = S["weights"].get(rid, 1.0)
        mod = 1.0
        if f["derby"] and rid in STAT_RULES:
            mod *= P["derby_stat_factor"]            # Rule 10
        if rid in NOISE_RULES and f["conflict"] <= P["decouple_threshold"]:
            mod *= P["noise_factor"]                 # Rule 11: ตัดกระแส Public noise
        eff = val * w * mod
        out.append({"rule": rid, "market": mk, "raw": round(val, 4), "eff": eff, "note": note, "group": rule_group(rid)})
    return out


def _base_raw(f, P):
    """คะแนนดิบจาก Rule หลัก 1-26 (+X1/X2) ก่อนรวม Rule ผู้สมัคร"""
    raw = []                                         # (rule, market, value, note)
    for fn in RULES:
        raw += fn(f, P)
    if f["derby"]:                                   # Rule 10: อารมณ์ร่วมในสนาม
        raw.append(("R10", f["dog_hdp"], 0.3, "ดาร์บี้: ให้น้ำหนักอารมณ์สนามมากกว่าสถิติ (+ทีมรอง)"))
    return [r for r in raw if r[1] not in ("OU_OVER", "OU_UNDER") or f["has_ou"]]


def analyze_features(m, f, store):
    """ให้คะแนน Rule และฟันธงจาก features (m ไม่จำเป็น) ใช้ซ้ำใน backtest กับ features ที่เก็บไว้
    Rule ที่ระบบสร้างเอง/Rule ทดลอง จะมีผลต่อการฟันธงก็ต่อเมื่อสถานะเป็น active เท่านั้น (shadow = ประเมินเบื้องหลัง)"""
    P, S = store.params, store.state
    flt = lambda L: [r for r in L if r[1] not in ("OU_OVER", "OU_UNDER") or f["has_ou"]]
    raw = _base_raw(f, P)
    base_contribs = _build_contribs(raw, f, P, S)

    extra, shadow, extra_veto, flow_only = [], [], set(), False
    for rid, c in candidates_for(f, P, store, base_contribs).items():
        st_ = rule_status(store, rid, c["kind"])
        if st_ == "active":
            extra += [(rid, mk_, val_, c["note"]) for mk_, val_ in c["rec"]]
            extra_veto |= set(c["veto"])
            flow_only = flow_only or c.get("flow_only", False)
        elif st_ == "shadow":
            shadow.append({"id": rid, "kind": c["kind"], "market": c["market"], "role": c["role"], "note": c["note"]})
    contribs = _build_contribs(flt(raw + extra), f, P, S)

    # ---- รวมคะแนนต่อทางเลือก
    scores = {k: 0.0 for k in ALL_MARKETS}
    use = [c for c in contribs if (not flow_only) or c["group"] in ("flow", "price")]
    for c in contribs:
        c["counted"] = False
    mode = P.get("score_mode", "sum")
    if mode == "grouped":                            # นับกลุ่มข้อมูลละครั้ง: เอาค่าสูงสุดของแต่ละกลุ่มต่อทางเลือก
        best = {}
        for c in use:
            key = (c["market"], c["group"])
            if key not in best or c["eff"] > best[key]["eff"]:
                best[key] = c
        for (mk_, _g), c in best.items():
            scores[mk_] += c["eff"]
            c["counted"] = True
    else:
        for c in use:
            scores[c["market"]] += c["eff"]
            c["counted"] = True

    # --- Veto (Rule 14 / 16 / 25 / 26 และ Rule ทดลองที่ปลดล็อคแล้ว) ---
    veto = set(f.get("veto", [])) | extra_veto
    if f["derby"] and f["has_ou"] and f["ou_c"] <= 2.5 and f["late_goal"]:
        veto.add("OU_UNDER")

    sc = dict(scores)
    for vk in veto:                                  # ฝั่งที่ถูกแบนห้ามนำคะแนนไปหักล้างอีกฝั่ง (ห้ามสวนเด็ดขาด)
        if vk in sc:
            sc[vk] = 0.0
    cands = []
    net_h = sc["HDP_HOME"] - sc["HDP_AWAY"]
    for side, v in (("HOME", net_h), ("AWAY", -net_h)):
        if v > 0 and f"HDP_{side}" not in veto:
            cands.append((f"HDP_{side}", v))
        if v > 0 and f["fav_line_c"] <= 0.75 and f"X12_{side}" not in veto and f"HDP_{side}" not in veto:
            fac = 0.7 if side.lower() == f["fav"] else 0.45
            cands.append((f"X12_{side}", v * fac - 0.2))
    if f["has_ou"]:
        net_o = sc["OU_OVER"] - sc["OU_UNDER"]
        if net_o > 0 and "OU_OVER" not in veto:
            cands.append(("OU_OVER", net_o))
        if net_o < 0 and "OU_UNDER" not in veto:
            cands.append(("OU_UNDER", -net_o))
    cands = [c for c in cands if c[1] > 0]

    # --- Current Odds Priority: สัญญาณที่มาจากการไหลของราคา (เทียบราคาเปิด) ล้วน ๆ ถูกลดน้ำหนัก ---
    def cur_support(mk_):
        base = mk_.replace("X12_", "HDP_") if mk_.startswith("X12_") else mk_
        return sum(c["eff"] for c in contribs if c["market"] == base and c["rule"] not in MOVEMENT_RULES)
    moved = set()
    adj = []
    for mk_, st_ in cands:
        if cur_support(mk_) <= 1e-9:
            st_ *= P["move_only_discount"]
            moved.add(mk_)
        adj.append((mk_, st_))
    cands = adj

    if not cands:                                    # Rule 13 บังคับฟันธง: fallback = ทีมต่อ
        cands = [(f["fav_hdp"], 0.01)]
    cands.sort(key=lambda x: -x[1])
    mk, strength = cands[0]
    conf = 50 + 35 * (1 - math.exp(-strength / 3.0))
    tier = "สูง" if strength >= 2.5 else "กลาง" if strength >= 1.2 else "ต่ำ"
    if f.get("verify_fail"):
        tier = "ต่ำ"                                 # Home/Away Verification ไม่ผ่าน -> ไม่ให้ระดับสูง/กลาง

    # --- สถานะ "ข้าม" (ไม้ยังถูกคำนวณเป็นไม้เงา เพื่อติดตามว่าการข้ามช่วยจริงหรือไม่) ---
    pair = {"HDP_HOME": "HDP_AWAY", "HDP_AWAY": "HDP_HOME", "OU_OVER": "OU_UNDER", "OU_UNDER": "OU_OVER",
            "X12_HOME": "HDP_AWAY", "X12_AWAY": "HDP_HOME"}
    base_mk = mk.replace("X12_", "HDP_") if mk.startswith("X12_") else mk
    support, oppose = sc.get(base_mk, 0.0), sc.get(pair.get(mk, ""), 0.0)
    skip = []
    if P.get("skip_enabled"):
        if strength < P["skip_min_strength"]:
            skip.append(f"สัญญาณอ่อน (คะแนน {strength:.2f} < {P['skip_min_strength']:g})")
        if support > 0 and oppose / support >= P["skip_conflict"]:
            skip.append(f"สัญญาณขัดกัน (ฝั่งตรงข้าม {oppose:.2f} = {oppose / support:.0%} ของฝั่งที่เลือก {support:.2f})")
        if P.get("skip_move_only") and mk in moved:
            skip.append("มาจากการไหลของราคาล้วน ไม่มีราคาปัจจุบัน/บริบทหนุน")
        if P.get("skip_verify_fail") and f.get("verify_fail"):
            skip.append("ตรวจเหย้า/เยือนไม่ผ่าน")
    for c in contribs:
        c["eff"] = round(c["eff"], 4)                # ปัดเศษเพื่อเก็บ (หลังรวมคะแนนด้วยค่าเต็มแล้ว)
    price, label = pick_label(m, f, mk)
    bp = (f.get("best_price") or {}).get(mk)
    best = None
    if bp and bp["price"] > price + 1e-9:
        best = {"book": bp["book"], "price": round(bp["price"], 3), "gain": round(bp["price"] - price, 3),
                "breakeven": round(1 / (1 + bp["price"]), 4), "breakeven_median": round(1 / (1 + price), 4)}
    pick = {"market": mk, "strength": round(strength, 3), "confidence": round(conf, 1), "tier": tier,
            "label": label, "price_win": price, "veto": sorted(veto),
            "move_only": mk in moved, "verify_fail": bool(f.get("verify_fail")),
            "runner_up": [(c[0], round(c[1], 3)) for c in cands[1:3]],
            "shadow": shadow, "score_mode": mode,
            "skip": bool(skip), "skip_reasons": skip, "support": round(support, 3), "oppose": round(oppose, 3),
            "signal_level": tier, "best": best}
    return f, contribs, pick


def pick_label(m, f, mk):
    """ป้ายและราคา (ผลตอบแทนเมื่อชนะ) ของทางเลือก คำนวณจาก features ล้วน (m ไม่ถูกใช้)"""
    home, away, lc = f["home"], f["away"], f["line_c"]
    hw = f["fav_water_c"] if f["fav"] == "home" else f["dog_water_c"]
    aw = f["dog_water_c"] if f["fav"] == "home" else f["fav_water_c"]
    if mk == "HDP_HOME":
        return hw, f"แฮนดิแคป {home} {fmt_line(lc)} @{hw:.2f}"
    if mk == "HDP_AWAY":
        return aw, f"แฮนดิแคป {away} {fmt_line(-lc)} @{aw:.2f}"
    if mk == "OU_OVER":
        w = f["over_water_c"]
        return w, f"สูง (Over) {f['ou_c']:g} @{w:.2f}"
    if mk == "OU_UNDER":
        w = f["under_water_c"]
        return w, f"ต่ำ (Under) {f['ou_c']:g} @{w:.2f}"
    idx = 0 if mk == "X12_HOME" else 2
    o = f["x12_cur"][idx]
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
    L.append("\n📊 วิเคราะห์เจาะลึก V5.9 Reality Check")
    L.append("  [1] Home/Away Verification Protocol")
    for ok, txt in f["verify"]:
        L.append(f"    {'✅' if ok else '❌'} {txt}")
    if f["verify_fail"]:
        L.append("    ⚠ การยืนยันเหย้า/เยือนไม่ผ่าน: ตรวจรูป/ไฟล์ JSON ก่อนเชื่อผลวิเคราะห์ (ระบบลดระดับสัญญาณเป็น 'ต่ำ')")
    xc, xo = f["x12_cur"], f["x12_open"]
    pc = implied(xc)
    L.append("  [2] ราคาปัจจุบัน (Current/Live Odds = ราคาหลักที่ใช้ตัดสินใจ)")
    L.append(f"    • 1X2: {xc[0]:.2f} / {xc[1]:.2f} / {xc[2]:.2f}  (โอกาสโดยนัย เหย้า {pc[0]:.0%} เสมอ {pc[1]:.0%} เยือน {pc[2]:.0%})")
    hw = f["fav_water_c"] if f["fav"] == "home" else f["dog_water_c"]
    aw = f["dog_water_c"] if f["fav"] == "home" else f["fav_water_c"]
    L.append(f"    • HDP: {f['home']} {fmt_line(f['line_c'])} น้ำ {hw:.2f} | {f['away']} {fmt_line(-f['line_c'])} น้ำ {aw:.2f}"
             f"  -> ทีมต่อ: {f['fav_name']} ({'เหย้า' if f['fav'] == 'home' else 'เยือน'})")
    if f["has_ou"]:
        L.append(f"    • OU: {f['ou_c']:g} น้ำสูง {f['over_water_c']:.2f} / ต่ำ {f['under_water_c']:.2f}")
    L.append("  [3] การไหลของราคา (อ้างอิงเทียบราคาเปิดเท่านั้น)")
    L.append(f"    • เรต HDP เปิด {fmt_line(f['line_o'])} -> ปัจจุบัน {fmt_line(f['line_c'])}  "
             f"(ทีมต่อ{'แรงขึ้น' if f['hdp_shift_fav'] > 0 else 'อ่อนลง' if f['hdp_shift_fav'] < 0 else 'คงที่'} {f['hdp_shift_fav']:+g})")
    adj_txt = (f"  [ปรับตามเรตแล้ว: ทีมต่อ {-f['fav_drop_adj']:+.2f} / ทีมรอง {-f['dog_drop_adj']:+.2f}]"
               if abs(f["hdp_shift_fav"]) >= 0.01 else "")
    L.append(f"    • ค่าน้ำทีมต่อเปลี่ยน {-f['fav_drop']:+.2f} | ทีมรองเปลี่ยน {-f['dog_drop']:+.2f}{adj_txt}")
    L.append(f"    • พูล 1X2 ทีมต่อ {f['x12_pp']:+.1f}pp | ทีมรอง {f['dog_pp']:+.1f}pp | ความขัดแย้งพูล↔HDP = {f['conflict']:.0%}"
             f" {'(เกินเกณฑ์ 20%)' if f['conflict'] > P['decouple_threshold'] else '(ต่ำกว่าเกณฑ์ -> ถือเป็น noise)'}")
    if f["has_ou"]:
        L.append(f"    • เรต OU เปิด {f['ou_o']:g} -> ปัจจุบัน {f['ou_c']:g}"
                 + (f"  | ประตูรวมคาดการณ์จากสถิติ {f['exp_total']:.2f}" if f["exp_total"] else ""))
    L.append("  [4] สถิติ & บริบท")
    if f["rank_home"] is not None or f["rank_away"] is not None:
        L.append(f"    • อันดับตาราง: {f['home']} {f['rank_home'] if f['rank_home'] is not None else '-'} | {f['away']} {f['rank_away'] if f['rank_away'] is not None else '-'}"
                 + (f" (จาก {f['league_size']:g} ทีม)" if f["league_size"] else ""))
    if f["h2h_n"]:
        L.append(f"    • H2H {f['h2h_n']} นัด: ทีมต่อชนะ {f['h2h_fav_w']} เสมอ {f['h2h_draw']} แพ้ {f['h2h_dog_w']}"
                 + (f" | ประตูรวมเฉลี่ย {f['h2h_avg_total']:.1f}" if f["h2h_avg_total"] else ""))
    if f["value_ratio"]:
        L.append(f"    • มูลค่าทีมต่อ/ทีมรอง = {f['value_ratio']:.1f}x")
    fm = f.get("form")
    if fm and fm.get("home") and fm.get("away"):
        for t, nm in (("home", f["home"]), ("away", f["away"])):
            x = fm[t]
            L.append(f"    • ฟอร์ม {nm}: {x.get('seq', '-')}  ได้ {x.get('gf', '-')} เสีย {x.get('ga', '-')}  ชนะ {x.get('win_rate', '-')}%")
    if f.get("n_books"):
        L.append(f"    • ราคารวมจาก {f['n_books']} โบรกเกอร์ (เรต=ฐานนิยม, ค่าน้ำ/ราคา=มัธยฐาน)")
    L.append(f"    • Context tags: {', '.join(f['tags'])}")
    L.append("\n  Rule ที่ทำงาน (คะแนนหลังคูณน้ำหนักที่เรียนรู้แล้ว):")
    if contribs:
        for c in sorted(contribs, key=lambda x: -x["eff"]):
            nm = RULE_NAMES.get(c["rule"], "Learned Rule")
            w = store.state["weights"].get(c["rule"], 1.0)
            basis = "ไหลราคา" if c["rule"] in MOVEMENT_RULES else "ปัจจุบัน/บริบท"
            L.append(f"    [{c['rule']:<4}] {c['market']:<9} {c['eff']:+.2f} (w={w:.2f}, {basis})  {nm}")
    else:
        L.append("    (ไม่มี Rule ใดทำงาน)")

    L.append("\n🔍 ถอดรหัสเจตนาโต๊ะ (จากราคาปัจจุบัน)")
    keyr = [c for c in contribs if c["rule"] in ("R1", "R2", "R5", "R9", "R11", "X1", "X2") or c["rule"].startswith("L")]
    if keyr:
        for c in keyr:
            L.append(f"  - {c['note']}")
    else:
        L.append("  - ไม่พบความผิดปกติเด่นชัดของ Trap / Fake Steam ราคาเคลื่อนไหวอยู่ในกรอบปกติ")

    L.append("\n🎯 สัญญาณฟันธงเดี่ยว (Single Best Pick)")
    if pick.get("skip"):
        L.append("  ⏭ ข้ามไม้นี้ (ไม่นับเป็นไม้ที่เล่น) — ไม้เงาที่ติดตามผล:")
        for x in pick.get("skip_reasons", []):
            L.append(f"     · {x}")
    L.append(f"  >>> {pick['label']} <<<   (ราคาปัจจุบัน)")
    L.append(f"  ระดับสัญญาณ: {pick['tier']}  (คะแนน {pick['strength']:.2f} · ไม่ใช่โอกาสชนะ)")
    if pick.get("best"):
        b_ = pick["best"]
        L.append(f"  ราคาดีที่สุด: {b_['book']} @{b_['price']:.2f} (ดีกว่าราคามัธยฐาน +{b_['gain']:.2f} · จุดคุ้มทุน {b_['breakeven']:.1%})")
    if pick["veto"]:
        L.append(f"  ตัวเลือกที่ถูกแบน (Veto): {', '.join(pick['veto'])}")
    if pick.get("move_only"):
        L.append("  ⚠ Current Odds Priority: สัญญาณนี้มาจากการไหลของราคา (เทียบราคาเปิด) ล้วน ไม่มีราคาปัจจุบัน/บริบทหนุน ระบบลดคะแนนเหลือ 60% แล้ว")
    if pick["tier"] == "ต่ำ":
        L.append("  ⚠ สัญญาณอ่อน: โปรแกรมบังคับฟันธงตาม Rule 13 แต่ควรลดสัดส่วนเงินเดิมพัน")
    sm = f.get("score_model")
    if sm:
        br = best_by_result(sm)
        L.append(f"\n🔢 สกอร์ที่น่าจะเป็น (จากราคาตลาด · แสดงผลเท่านั้น): ประตูคาดหมาย {f['home']} {sm['lh']:.2f} – {sm['la']:.2f} {f['away']}")
        L.append("  อันดับ: " + " · ".join(f"{h}-{a} ({p:.0%})" for h, a, p in sm["top"][:5]))
        L.append(f"  ถ้า{f['home']}ชนะ: {br['home'][0]}-{br['home'][1]} · ถ้าเสมอ: {br['draw'][0]}-{br['draw'][1]} · ถ้า{f['away']}ชนะ: {br['away'][0]}-{br['away'][1]}")
        L.append(f"  สกอร์อันดับ 1 มีโอกาสถูกเพียง ~{sm['top'][0][2]:.0%} — ใช้ดูภาพรวมของเกม ไม่ใช่สกอร์ที่จะออกจริง")
    g = pick.get("gate")
    if g:
        st_th = {"pass": "ผ่าน · ลงทุนได้", "fail": "ไม่ผ่าน · งดลงทุน" if g["enabled"] else "ไม่ผ่าน (ตัวกรองปิดอยู่)", "data": "ข้อมูลยังไม่พอ · ลงทุนตามปกติ"}[g["status"]]
        L.append(f"\n🚦 ตัวกรองช่วงคะแนน: {g['kind_th']} คะแนน {g['label']} — {st_th}"
                 + (f" (ที่ผ่านมา {g['w']}-{g['l']}, กำไร {g['profit']:+.2f} จาก {g['n']} ไม้)" if g["n"] else ""))
    L += team_news_lines(m)
    return "\n".join(L)


_ST_TH = {"ok": "", "reported": "AI รายงาน รอยืนยัน", "unverified": "ไม่ยืนยันแหล่ง", "stale": "ข้อมูลเก่า", "invalid": "ค่าผิดปกติ"}
INJ_TH = {"out": "ไม่ได้ลง", "doubtful": "ไม่แน่", "suspended": "โดนแบน"}
ROLE_TH_TN = {"starter": "ตัวจริง", "rotation": "สำรอง", "unknown": "ไม่ทราบบทบาท"}


def team_news_lines(m):
    """ข้อความรายงานข้อมูลทีม: แสดงตรงตามที่ยืนยันได้ ไม่มี = เขียนว่าไม่มีข้อมูล"""
    tn = m.get("team_news")
    if not tn:
        return []
    L = ["\n🩺 ข้อมูลทีม (ประกอบการตัดสินใจ · ยังไม่มีผลต่อการฟันธง)"]
    if tn.get("error"):
        return L + [f"  ค้นข้อมูลทีมไม่สำเร็จ: {tn['error']}"]
    names = {"home": m.get("home", "เจ้าบ้าน"), "away": m.get("away", "ทีมเยือน")}
    for side in ("home", "away"):
        x = (tn.get("xg") or {}).get(side) or {}
        if x.get("status", "none") == "none":
            L.append(f"  • xG {names[side]}: ไม่มีข้อมูล")
        elif "xg" not in x:
            L.append(f"  • xG {names[side]}: ไม่มีข้อมูลที่ยืนยันได้")
        else:
            flag = f"  ⚠ {x.get('why')} — ไม่นำไปใช้" if x["status"] != "ok" else ""
            gfga = f" · ได้/เสียจริง {x['gf']:.2f}/{x['ga']:.2f}" if x.get("gf") is not None and x.get("ga") is not None else ""
            L.append(f"  • xG {names[side]} ({x.get('games') or '?'} นัด): xG {x['xg']:.2f} / xGA {x['xga']:.2f}{gfga}"
                     f"  [{x.get('source') or '-'} {x.get('as_of') or ''}]{flag}")
    for side in ("home", "away"):
        lst = (tn.get("injuries") or {}).get(side) or []
        if not (tn.get("injuries_checked") or {}).get(side) and not lst:
            L.append(f"  • ตัวเจ็บ/แบน {names[side]}: ไม่มีข้อมูล")
        elif not lst:
            L.append(f"  • ตัวเจ็บ/แบน {names[side]}: ไม่พบรายงาน")
        else:
            L.append(f"  • ตัวเจ็บ/แบน {names[side]}:")
            for p in lst:
                flag = f"  ⚠ {p.get('why')}" if p.get("st") != "ok" else ""
                L.append(f"      - {p['player']} ({p.get('position')}, {ROLE_TH_TN.get(p.get('role'), '')}) "
                         f"{INJ_TH.get(p.get('status'), '?')}  [{p.get('source') or '-'} {p.get('as_of') or ''}]{flag}")
    for side in ("home", "away"):
        r = (tn.get("rest") or {}).get(side) or {}
        if r.get("status", "none") == "none" or r.get("days") is None:
            L.append(f"  • วันพัก {names[side]}: ไม่มีข้อมูล")
        else:
            flag = "  ⚠ AI รายงาน รอยืนยัน" if r["status"] != "ok" else ""
            L.append(f"  • วันพัก {names[side]}: {r['days']} วัน (นัดก่อน {r['last_date']} {r.get('competition') or ''}){flag}")
    c = tn.get("cup") or {}
    if c.get("is_cup"):
        leg = f" เลก {c['leg']}" if c.get("leg") else ""
        fl = f" (เลกแรก {c['first_leg_score']})" if c.get("first_leg_score") else ""
        L.append(f"  • บอลถ้วย{leg}{fl}")
        for side in ("home", "away"):
            if c.get("rotation", {}).get(side):
                L.append(f"      - ⚠ {names[side]} มีข่าวหมุนเวียน/พักตัวหลัก [{c.get('source')}]")
    lu = tn.get("lineups") or {}
    L.append("  • ตัวจริง: " + ("ประกาศแล้ว" + (f" — {lu['notes']}" if lu.get("notes") else "") if lu.get("confirmed") else "ยังไม่ประกาศ / ไม่มีข้อมูล"))
    for n in tn.get("other_news") or []:
        flag = f"  ⚠ {n.get('why')}" if n.get("st") != "ok" else ""
        L.append(f"  • ข่าว: {n['text']}  [{n.get('source') or '-'}]{flag}")
    for p in tn.get("problems") or []:
        L.append(f"  ⚠ {p}")
    return L


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


# ----------------------------------------------------------------------------
# สกอร์ที่น่าจะเป็น (ไม่มีผลต่อการฟันธง): หา "ประตูคาดหมาย" ของสองทีมที่ทำให้แบบจำลอง
# Dixon-Coles (Poisson + ปรับสกอร์ต่ำ) ให้ราคายุติธรรมตรงกับตลาด 1X2 + แฮนดิแคป + สูง/ต่ำ ปัจจุบันมากที่สุด
# ----------------------------------------------------------------------------
SCORE_MAXG = 10
SCORE_RHO = -0.08                                       # ค่ามาตรฐานของ Dixon-Coles (เพิ่มโอกาส 0-0/1-1 เล็กน้อย)


def _fair_dec(w_a, w_b):
    """ค่าน้ำแบบฮ่องกงสองฝั่ง -> ราคาทศนิยมยุติธรรม (ตัดค่าต๋งแล้ว) ของฝั่ง a"""
    ia, ib = 1.0 / (1.0 + w_a), 1.0 / (1.0 + w_b)
    return (ia + ib) / ia


def _score_grid(lh, la, rho=SCORE_RHO, G=SCORE_MAXG):
    """lh, la = array ของประตูคาดหมาย -> เมทริกซ์ความน่าจะเป็น [..., สกอร์เจ้าบ้าน, สกอร์ทีมเยือน]"""
    import numpy as np
    g = np.arange(G + 1)
    lg = np.array([math.lgamma(k + 1) for k in g])
    lh, la = np.asarray(lh, float), np.asarray(la, float)
    ph = np.exp(g * np.log(lh[..., None]) - lh[..., None] - lg)
    pa = np.exp(g * np.log(la[..., None]) - la[..., None] - lg)
    M = ph[..., :, None] * pa[..., None, :]
    M[..., 0, 0] *= np.clip(1 - lh * la * rho, 0, None)
    M[..., 0, 1] *= np.clip(1 + lh * rho, 0, None)
    M[..., 1, 0] *= np.clip(1 + la * rho, 0, None)
    M[..., 1, 1] *= (1 - rho)
    return M / M.sum(axis=(-1, -2), keepdims=True)


def score_model(f):
    """คืน dict สกอร์ที่น่าจะเป็นจากราคาปัจจุบัน หรือ None ถ้าข้อมูลราคาไม่พอ"""
    try:
        import numpy as np
    except ImportError:
        return None
    try:
        x = [float(v) for v in f["x12_cur"]]
        if min(x) <= 1.0:
            return None
    except Exception:  # noqa
        return None
    inv = [1 / v for v in x]
    t1x2 = [v / sum(inv) for v in inv]
    G = SCORE_MAXG
    hs, as_ = np.meshgrid(np.arange(G + 1), np.arange(G + 1), indexing="ij")
    terms = []                                           # (เมทริกซ์ผลตอบแทนต่อเดิมพัน 1 หน่วยที่ราคายุติธรรม)
    try:
        hw = f["fav_water_c"] if f["fav"] == "home" else f["dog_water_c"]
        aw = f["dog_water_c"] if f["fav"] == "home" else f["fav_water_c"]
        dec = _fair_dec(hw, aw)
        pay = np.array([[profit(halves_hdp("home", f["line_c"], h, a), dec - 1) for a in range(G + 1)] for h in range(G + 1)])
        terms.append(pay)
    except Exception:  # noqa
        pass
    if f.get("has_ou"):
        try:
            dec = _fair_dec(f["over_water_c"], f["under_water_c"])
            pay = np.array([[profit(halves_ou("over", f["ou_c"], h, a), dec - 1) for a in range(G + 1)] for h in range(G + 1)])
            terms.append(pay)
        except Exception:  # noqa
            pass
    hwin, draw, awin = (hs > as_).astype(float), (hs == as_).astype(float), (hs < as_).astype(float)

    def loss(M):
        ps = [(M * k).sum(axis=(-1, -2)) for k in (hwin, draw, awin)]
        L = sum((p - t) ** 2 for p, t in zip(ps, t1x2))
        for pay in terms:                                 # ราคายุติธรรม = ผลตอบแทนคาดหมายเป็นศูนย์
            L = L + 0.5 * (M * pay).sum(axis=(-1, -2)) ** 2
        return L

    best = None
    for lo, hi, step in ((0.1, 4.5, 0.05), (None, None, 0.01)):
        if lo is None:
            c_h, c_a = best
            gh = np.arange(max(0.05, c_h - 0.06), c_h + 0.061, step)
            ga = np.arange(max(0.05, c_a - 0.06), c_a + 0.061, step)
        else:
            gh = ga = np.arange(lo, hi + 1e-9, step)
        LH, LA = np.meshgrid(gh, ga, indexing="ij")
        Ls = loss(_score_grid(LH, LA))
        i, j = np.unravel_index(int(np.argmin(Ls)), Ls.shape)
        best = (float(gh[i]), float(gh[0] * 0 + ga[j]))
        err = float(Ls[i, j])
    lh, la = best
    M = _score_grid(lh, la)
    flat = sorted(((float(M[h, a]), h, a) for h in range(G + 1) for a in range(G + 1)), reverse=True)
    top = [[h, a, round(p, 4)] for p, h, a in flat[:6]]
    grid = [[round(float(M[h, a]), 4) for a in range(6)] for h in range(6)]
    pH, pD, pA = (float((M * k).sum()) for k in (hwin, draw, awin))
    return {"lh": round(lh, 2), "la": round(la, 2), "top": top, "grid": grid,
            "p": [round(pH, 4), round(pD, 4), round(pA, 4)], "market_p": [round(v, 4) for v in t1x2],
            "exp_total": round(lh + la, 2), "rmse": round((err / max(3 + len(terms), 1)) ** 0.5, 4),
            "inputs": 1 + len(terms), "outside_5": round(1 - sum(sum(r) for r in grid), 4)}


_SCORE_MEMO = {}


def best_by_result(sm):
    """สกอร์ที่น่าจะเป็นที่สุดแยกตามผล (เจ้าบ้านชนะ / เสมอ / ทีมเยือนชนะ) จากตาราง 0-5"""
    out = {}
    for key, cond in (("home", lambda h, a: h > a), ("draw", lambda h, a: h == a), ("away", lambda h, a: h < a)):
        cells = [(sm["grid"][h][a], h, a) for h in range(6) for a in range(6) if cond(h, a)]
        p, h, a = max(cells)
        out[key] = (h, a, p)
    return out


def score_accuracy(history):
    """วัดผลการทายสกอร์ย้อนหลังกับผลจริง (ทุกไม้ที่บันทึกผลแล้ว รวมไม้ที่ข้าม)"""
    import math as _m
    rows, freq = [], {}
    for r in history:
        if r.get("status") != "settled" or not r.get("score"):
            continue
        sm = r["features"].get("score_model")
        if not sm:
            key = (r.get("id"), str(r["features"].get("x12_cur")), r["features"].get("line_c"), r["features"].get("ou_c"))
            if key not in _SCORE_MEMO:
                _SCORE_MEMO[key] = score_model(r["features"])
            sm = _SCORE_MEMO[key]
        if not sm:
            continue
        hg, ag = int(r["score"][0]), int(r["score"][1])
        freq[(hg, ag)] = freq.get((hg, ag), 0) + 1
        tops = [(t[0], t[1]) for t in sm["top"]]
        g = sm["grid"]
        p_act = g[hg][ag] if hg < 6 and ag < 6 else None
        res = (hg > ag) - (hg < ag)
        mr = (tops[0][0] > tops[0][1]) - (tops[0][0] < tops[0][1])
        rows.append({"top1": tops[0] == (hg, ag), "top3": (hg, ag) in tops[:3], "p_act": p_act, "p_top1": sm["top"][0][2],
                     "res_hit": mr == res, "tot_err": abs(sm["exp_total"] - (hg + ag)), "score": (hg, ag), "pred": tops[0]})
    n = len(rows)
    if not n:
        return {"n": 0}
    common = max(freq.items(), key=lambda kv: kv[1])
    ll = [-_m.log(max(x["p_act"], 1e-4)) for x in rows if x["p_act"] is not None]
    pred_freq = {}
    for x in rows:
        pred_freq[x["pred"]] = pred_freq.get(x["pred"], 0) + 1
    return {"n": n, "top1": sum(x["top1"] for x in rows), "top3": sum(x["top3"] for x in rows),
            "exp_top1": sum(x["p_top1"] for x in rows) / n,
            "res_hit": sum(x["res_hit"] for x in rows), "mae_total": sum(x["tot_err"] for x in rows) / n,
            "common_score": common[0], "common_n": common[1], "logloss": (sum(ll) / len(ll)) if ll else None,
            "pred_freq": sorted(pred_freq.items(), key=lambda kv: -kv[1])[:5]}


def profit(halves, price_win):
    return sum(price_win if h == 1 else -1.0 if h == -1 else 0.0 for h in halves) / len(halves)


def result_word(r):
    return {1: "ชนะเต็ม", 0.5: "ชนะครึ่ง", 0: "เจ๊า(คืนทุน)", -0.5: "เสียครึ่ง", -1: "แพ้เต็ม"}.get(round(r * 2) / 2, f"{r:+.2f}")


# ----------------------------------------------------------------------------
# 8) การเรียนรู้: ปรับน้ำหนัก Rule + สร้าง Rule ใหม่
# ----------------------------------------------------------------------------
def weight_key(store):
    """ชุดน้ำหนักที่การเรียนรู้ปรับ: แช่แข็ง -> shadow_weights (เบื้องหลัง) / ไม่แช่แข็ง -> weights (ใช้ฟันธงจริง)"""
    S = store.state
    if store.params.get("freeze_weights"):
        if "shadow_weights" not in S:
            S["shadow_weights"] = dict(S["weights"])
        for k, v in DEFAULT_WEIGHTS.items():
            S["shadow_weights"].setdefault(k, v)
        return "shadow_weights"
    return "weights"


def update_weights(store, rec, outcomes):
    P, S = store.params, store.state
    wk = weight_key(store)
    W = S[wk]
    agg, changes = {}, {}
    valid_learned = {r_["id"] for r_ in S.get("learned_rules", [])}
    for c in rec["contribs"]:
        if c["market"] not in outcomes:
            continue
        if c["rule"].startswith("L") and c["rule"] not in valid_learned:
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
        old = W.get(rid, 1.0)
        lr = max(P["lr_min"], P["lr"] / math.sqrt(st["n"]))
        w = old * (1 + lr * rr)
        w += P["decay"] * (DEFAULT_WEIGHTS.get(rid, 1.0) - w)
        w = min(P["w_max"], max(P["w_min"], w))
        W[rid] = round(w, 4)
        changes[rid] = (old, w, rr)
    return changes


def role_outcomes(rec, outcomes):
    f = rec["features"]
    d = {"HDP_FAV": outcomes[f["fav_hdp"]][0], "HDP_DOG": outcomes[f["dog_hdp"]][0],
         "X12_FAV": outcomes[f["fav_x12"]][0]}
    if "OU_OVER" in outcomes:
        d["OU_OVER"], d["OU_UNDER"] = outcomes["OU_OVER"][0], outcomes["OU_UNDER"][0]
    return d


def accumulate_stats(stats, tags, roles, P):
    """เพิ่มผลของ 1 นัดเข้าสถิติของทุกชุดเงื่อนไข (tags) x ทางเลือก"""
    for k in range(1, P["disc_max_combo"] + 1):
        for combo in itertools.combinations(tags, k):
            for role, r in roles.items():
                s_ = stats.setdefault((combo, role), [0, 0.0])
                s_[0] += 1
                s_[1] += (1 + r) / 2
    a_ = stats.setdefault(("__all__", ""), [0, 0.0])
    a_[0] += 1


def discover_rules(store, verbose=True):
    """ค้นหารูปแบบ (ชุดเงื่อนไข tags) ที่ชนะ/แพ้ซ้ำอย่างมีนัยสำคัญ แล้วแปลงเป็น Rule ใหม่"""
    P, S = store.params, store.state
    stats = getattr(store, "inc_stats", None)          # MemStore (backtest) สะสมสถิติเองทีละนัด
    if stats is None:
        stats = {}
        for rec in store.history:
            if rec.get("status") != "settled":
                continue
            accumulate_stats(stats, rec["features"]["tags"], rec["role_r"], P)

    learned = S["learned_rules"]
    total = (stats.get(("__all__", "")) or [0])[0]
    universal = set()
    if P.get("exclude_universal") and total >= 20:    # เงื่อนไขที่จริงเกือบทุกนัด = เดิมพันตามสัดส่วนเดิม ไม่ใช่รูปแบบ
        for (combo, role), v in stats.items():
            if role == "HDP_FAV" and isinstance(combo, tuple) and len(combo) == 1 and v[0] / total >= P["universal_cov"]:
                universal.add(combo[0])
    life = S.get("lifecycle") or {}
    live_count = sum(1 for r in learned if (life.get(r["id"]) or {}).get("status") != "retired")
    for lr in learned:                               # รีเฟรชสถิติ Rule เดิม
        s = stats.get((tuple(lr["tags"]), lr["role"]))
        if s and s[0] >= P["disc_min_n"] and not str(lr["role"]).startswith("X12"):
            lr["n"], lr["wr"] = s[0], s[1] / s[0]
            lr["strength"] = round(min(2.5, max(0.3, P["learned_base"] * (lr["wr"] - 0.5) * 4)), 3)
            lr["enabled"] = lr["wr"] >= 0.5
    existing = {(tuple(r["tags"]), r["role"]): r for r in learned}

    cands = []
    for (combo, role), (n, w) in stats.items():
        if combo == "__all__" or n < P["disc_min_n"] or (combo, role) in existing or universal & set(combo):
            continue
        if str(role).startswith("X12"):               # ราคา 1X2 ไม่ใช่ 1:1 เกณฑ์ชนะ > 50% จึงไม่ได้แปลว่าได้เปรียบ และตลาดนี้ไม่ถูกนำไปคิดคะแนน
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
        if len(new) >= P["disc_max_new"] or live_count + len(new) >= P["disc_max_total"]:
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
        if "shadow_weights" in S:
            S["shadow_weights"][rid] = 1.0
        rule = {"id": rid, "tags": list(combo), "role": role, "n": n, "wr": round(p, 4),
                "strength": round(min(2.5, max(0.3, P["learned_base"] * (p - 0.5) * 4)), 3),
                "enabled": True, "created": now_th("%Y-%m-%d %H:%M")}
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


import secrets as _secrets
import threading as _threading

SESSIONS = {}                                  # token -> เวลาใช้งานล่าสุด (เก็บในหน่วยความจำของเซิร์ฟเวอร์)
_SESS_LOCK = _threading.Lock()


def session_new():
    tok = _secrets.token_urlsafe(24)
    now = time.time()
    with _SESS_LOCK:
        for k in [k for k, t in SESSIONS.items() if now - t > 3600]:      # ล้างโทเค็นเก่า
            SESSIONS.pop(k, None)
        SESSIONS[tok] = now
    return tok


def session_touch(tok, idle_sec):
    """ต่ออายุถ้ายังไม่เกินเวลา idle คืน True; ถ้าเกิน/ไม่มี ลบโทเค็นแล้วคืน False"""
    if not tok:
        return False
    with _SESS_LOCK:
        t, now = SESSIONS.get(tok), time.time()
        if t is None or now - t > idle_sec:
            SESSIONS.pop(tok, None)
            return False
        SESSIONS[tok] = now
        return True


def session_alive(tok, idle_sec):
    """ตรวจอย่างเดียว ไม่ต่ออายุ (ใช้ตัวจับเวลาเบื้องหลัง)"""
    with _SESS_LOCK:
        t = SESSIONS.get(tok) if tok else None
        return t is not None and time.time() - t <= idle_sec


def session_revoke(tok):
    with _SESS_LOCK:
        SESSIONS.pop(tok, None)


# ----------------------------------------------------------------------------
# งานวิเคราะห์เบื้องหลัง: ทำงานบนเซิร์ฟเวอร์ต่อแม้หน้าเว็บหลุด/สลับแอป (เก็บในหน่วยความจำ 1 ชั่วโมง)
# ----------------------------------------------------------------------------
JOBS = {}
_JOBS_LOCK = _threading.Lock()
JOB_TTL = 3600


def job_new(owner):
    jid = _secrets.token_urlsafe(9)
    now = time.time()
    with _JOBS_LOCK:
        for k in [k for k, j in JOBS.items() if now - j["started"] > JOB_TTL]:
            JOBS.pop(k, None)
        JOBS[jid] = {"id": jid, "owner": owner, "status": "running", "steps": [], "result": None, "error": None,
                     "started": now, "finished": None}
    return JOBS[jid]


def job_get(jid):
    j = JOBS.get(jid) if jid else None
    return j if j and time.time() - j["started"] <= JOB_TTL else None


def job_latest(owner, max_age=1800):
    """งานล่าสุดของผู้ใช้คนนี้ (ใช้กู้คืนเมื่อเปิดหน้าใหม่แล้วลิงก์ไม่มีรหัสงาน)"""
    if not owner:
        return None
    now = time.time()
    c = [j for j in JOBS.values() if j["owner"] == owner and now - j["started"] <= max_age and not j.get("dismissed")]
    return max(c, key=lambda j: j["started"]) if c else None


def job_start(job, fn, *args):
    """รัน fn(job, *args) ในเธรดเบื้องหลัง: fn ต้องไม่เรียกคำสั่งแสดงผลของ Streamlit และต้องคืนผลลัพธ์ (dict) หรือ raise"""
    def run():
        try:
            res = fn(job, *args)
            job["result"] = res
            job["status"] = "gate" if isinstance(res, dict) and res.get("_gate") else "done"
        except SystemExit as e:
            job["error"], job["status"] = str(e.code), "error"
        except ValueError as e:
            job["error"], job["status"] = f"อ่านข้อมูลจากรูปได้ไม่ครบ: {e}", "error"
        except Exception as e:  # noqa
            job["error"], job["status"] = f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {type(e).__name__}: {str(e)[:200]}", "error"
        finally:
            job["finished"] = time.time()
            cb = job.pop("on_finish", None)
            if cb:
                try:
                    cb(job)
                except Exception:  # noqa
                    pass
    th = _threading.Thread(target=run, name="fq-job-" + job["id"], daemon=True)
    th.start()
    return th


def record_prediction(store, m, f, contribs, pick, warns=None):
    """บันทึกสัญญาณลงประวัติ (สถานะ pending) คืน (id, บันทึกสำเร็จหรือไม่)"""
    mid = m.get("id") or slug(f"{f['home']}-vs-{f['away']}-{now_th('%Y%m%d-%H%M')}")
    store.history = [r for r in store.history if not (r["id"] == mid and r["status"] == "pending")]
    if any(r["id"] == mid for r in store.history):
        return mid, False
    store.history.append({"id": mid, "created": now_th("%Y-%m-%d %H:%M"), "status": "pending",
                          "features": f, "contribs": contribs, "pick": pick,
                          "match": {k: v for k, v in m.items() if k not in ("books", "warnings")},   # ไว้แสดงการ์ดเดิมในหน้าบันทึกผล
                          "warns": list(warns or [])})
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
# 9.1) นำเข้ารูปภาพ (5 รูป) -> สกัดข้อมูลด้วย Gemini -> ตรวจสอบ -> วิเคราะห์
# ----------------------------------------------------------------------------
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
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
10. rank = อันดับบนตารางของแต่ละทีม (ตัวเลขในวงเล็บเหลี่ยม [ ] ข้างโลโก้ทีม) ; league_size = จำนวนทีมในลีก (null ถ้าไม่เห็น)
    ah_left_team = ชื่อทีมที่อยู่คอลัมน์ซ้ายของตาราง Asian Handicap (ใช้ยืนยันว่าเรตมองจากเจ้าบ้านจริง)
    h2h แต่ละนัดต้องใส่ home_team / away_team = ชื่อทีมเจ้าบ้าน (แถวบน) / ทีมเยือน (แถวล่าง) ของนัดนั้น
11. warnings = รายการข้อความภาษาไทยของค่าที่อ่านไม่ชัด/ขัดแย้งกันระหว่างรูป (เช่น ลำดับฟอร์มในสองรูปไม่ตรงกัน)

ตอบเป็น JSON ล้วน ไม่มีข้อความอื่น ไม่มี markdown ตามโครงสร้างนี้:
"""

EXTRACT_SCHEMA = {
    "league": "...", "home": "...", "away": "...",
    "rank": {"home": 0, "away": 0}, "league_size": None, "ah_left_team": "...",
    "context": {"type": "league", "derby": False, "high_volatility": False, "high_scoring_league": False,
                "cup_group_stage": False, "knockout": False, "desperation": None, "late_goal_tendency": False,
                "high_draw_league": False, "continental_cup": False},
    "books": [{
        "name": "bookmaker",
        "x12": {"open": [0.0, 0.0, 0.0], "current": [0.0, 0.0, 0.0]},
        "hdp": {"open": {"line": 0.0, "home_water": 0.0, "away_water": 0.0},
                "current": {"line": 0.0, "home_water": 0.0, "away_water": 0.0}},
        "ou": {"open": {"line": 0.0, "over": 0.0, "under": 0.0},
               "current": {"line": 0.0, "over": 0.0, "under": 0.0}}}],
    "form": {"home": {"seq": "DLDWW", "gf": 0, "ga": 0, "games": 5, "win_rate": 0},
             "away": {"seq": "DLDWW", "gf": 0, "ga": 0, "games": 5, "win_rate": 0}},
    "h2h": [{"home_team": "...", "away_team": "...", "hg": 0, "ag": 0, "home_is_current_home": True}],
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
    conv = set()
    for b in books:                                   # ค่าน้ำที่เห็นเป็น decimal (> 1.5) -> แปลงเป็นแบบฮ่องกงก่อนรวม (กันค่ากลาง/ราคาดีที่สุดเพี้ยน)
        for key, ks in (("hdp", ("home_water", "away_water")), ("ou", ("over", "under"))):
            for t in ("open", "current"):
                row = (b.get(key) or {}).get(t) if isinstance(b.get(key), dict) else None
                if isinstance(row, dict):
                    for k in ks:
                        if _num(row.get(k)) and row[k] > 1.5:
                            row[k] = round(row[k] - 1, 3)
                            conv.add(str(b.get("name", "?")))
    if conv:
        w.append("ค่าน้ำของ " + ", ".join(sorted(conv)) + " ดูเหมือน decimal จึงลบ 1 ให้อัตโนมัติก่อนรวมราคา")
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
    # การเปลี่ยนค่าน้ำรายโบรกเกอร์: เฉพาะเจ้าที่เรตเปิด = เรตปัจจุบัน = เรตหลักปัจจุบัน (เปิด - ปัจจุบัน, + = น้ำลด)
    chg = {}
    for key, f1, f2 in (("hdp", "home_water", "away_water"), ("ou", "over", "under")):
        cur = (m.get(key) or {}).get("current") if isinstance(m.get(key), dict) else None
        if not cur:
            continue
        d1, d2 = [], []
        for b in books:
            bo, bc = ((b.get(key) or {}).get("open") or {}), ((b.get(key) or {}).get("current") or {})
            if all(_num(x.get(k)) for x in (bo, bc) for k in ("line", f1, f2)) and abs(bo["line"] - bc["line"]) < 1e-9 \
                    and abs(bc["line"] - cur["line"]) < 1e-9:
                d1.append(bo[f1] - bc[f1])
                d2.append(bo[f2] - bc[f2])
        if d1:
            chg[key] = {f1: _med(d1), f2: _med(d2), "n": len(d1)}
    m["water_chg"] = chg
    # ราคาดีที่สุดของแต่ละทางเลือก (ราคาปัจจุบัน เฉพาะเจ้าที่อยู่เรตเดียวกับเรตรวม) สำหรับ line shopping
    best = {}
    cur_h, cur_o = (m.get("hdp") or {}).get("current"), (m.get("ou") or {}).get("current")
    for b in books:
        nm = b.get("name", "?")
        h = (b.get("hdp") or {}).get("current") or {}
        if cur_h and all(_num(h.get(k)) for k in ("line", "home_water", "away_water")) and abs(h["line"] - cur_h["line"]) < 1e-9:
            for mk_, k in (("HDP_HOME", "home_water"), ("HDP_AWAY", "away_water")):
                if mk_ not in best or h[k] > best[mk_]["price"]:
                    best[mk_] = {"book": nm, "price": h[k]}
        o = (b.get("ou") or {}).get("current") or {}
        if cur_o and all(_num(o.get(k)) for k in ("line", "over", "under")) and abs(o["line"] - cur_o["line"]) < 1e-9:
            for mk_, k in (("OU_OVER", "over"), ("OU_UNDER", "under")):
                if mk_ not in best or o[k] > best[mk_]["price"]:
                    best[mk_] = {"book": nm, "price": o[k]}
        x = (b.get("x12") or {}).get("current")
        if isinstance(x, list) and len(x) == 3 and all(_num(v) for v in x):
            for mk_, i in (("X12_HOME", 0), ("X12_AWAY", 2)):
                if mk_ not in best or x[i] - 1 > best[mk_]["price"]:
                    best[mk_] = {"book": nm, "price": round(x[i] - 1, 3)}
    m["best_price"] = best
    # สัดส่วนโบรกเกอร์ที่ขยับเรต HDP ไปทางเดียวกับเรตรวม (ใช้ใน Rule 17)
    m["hdp_agree"] = None
    h = m.get("hdp")
    if isinstance(h, dict) and h.get("open") and h.get("current"):
        main = sign(h["open"]["line"] - h["current"]["line"])      # + = เจ้าบ้านแรงขึ้น
        if main != 0:
            moves = [sign(b["hdp"]["open"]["line"] - b["hdp"]["current"]["line"]) for b in books
                     if isinstance(b.get("hdp"), dict) and all(isinstance(b["hdp"].get(t), dict) and _num(b["hdp"][t].get("line"))
                                                               for t in ("open", "current"))]
            if moves:
                m["hdp_agree"] = round(sum(1 for x in moves if x == main) / len(moves), 3)
    return w


def sanity_checks(m):
    """ตรวจความสมเหตุสมผลของราคาที่อ่านจากรูป คืน (คำเตือน, ข้อผิดพลาดร้ายแรง)
    ร้ายแรง = มีแนวโน้มอ่านรูปผิด (เช่น เครื่องหมายเรตกลับด้าน, ค่าน้ำ/ราคาผิดรูป) -> ควรตรวจก่อนวิเคราะห์"""
    warn, crit = [], []
    books = [b for b in (m.get("books") or []) if isinstance(b, dict)] or [{"name": "ราคารวม", "x12": m.get("x12"), "hdp": m.get("hdp"), "ou": m.get("ou")}]
    flips = []
    for b in books:
        nm = b.get("name", "?")
        for t, tn in (("open", "เปิด"), ("current", "ปัจจุบัน")):
            x = (b.get("x12") or {}).get(t)
            if isinstance(x, list) and len(x) == 3 and all(_num(v) and v > 1 for v in x):
                ovr = sum(1 / v for v in x)
                if ovr < 0.98 or ovr > 1.20:
                    crit.append(f"{nm} 1X2 {tn}: ผลรวมโอกาส {ovr:.0%} ผิดปกติ (ปกติ 100-115%) อาจอ่านราคาผิด/สลับคอลัมน์")
                elif ovr > 1.12:
                    warn.append(f"{nm} 1X2 {tn}: ค่าคอมมิชชันสูง ({ovr - 1:.0%})")
            h = (b.get("hdp") or {}).get(t)
            if isinstance(h, dict) and all(_num(h.get(k)) for k in ("line", "home_water", "away_water")):
                hw, aw = h["home_water"], h["away_water"]
                hw, aw = (hw - 1 if hw > 1.5 else hw), (aw - 1 if aw > 1.5 else aw)
                sm = hw + aw
                if sm < 1.6 or sm > 2.2:
                    crit.append(f"{nm} แฮนดิแคป {tn}: ค่าน้ำรวม {sm:.2f} ผิดปกติ (ปกติ ~1.80-2.05)")
                elif sm < 1.72 or sm > 2.08:
                    warn.append(f"{nm} แฮนดิแคป {tn}: ค่าน้ำรวม {sm:.2f} ค่อนข้างผิดปกติ")
                if isinstance(x, list) and len(x) == 3 and all(_num(v) for v in x) and abs(h["line"]) >= 0.5:
                    fav_x = "home" if x[0] < x[2] else "away"
                    fav_h = "home" if h["line"] < 0 else "away"
                    if fav_x != fav_h and abs(x[0] - x[2]) > 0.3:
                        flips.append(f"{nm} ({tn})")
            o = (b.get("ou") or {}).get(t)
            if isinstance(o, dict) and all(_num(o.get(k)) for k in ("line", "over", "under")):
                ov, un = o["over"], o["under"]
                ov, un = (ov - 1 if ov > 1.5 else ov), (un - 1 if un > 1.5 else un)
                if not 1.6 <= ov + un <= 2.2:
                    crit.append(f"{nm} สูง/ต่ำ {tn}: ค่าน้ำรวม {ov + un:.2f} ผิดปกติ")
                if not 0.5 <= o["line"] <= 7.5 or abs(o["line"] * 4 - round(o["line"] * 4)) > 1e-6:
                    crit.append(f"{nm} สูง/ต่ำ {tn}: เรต {o['line']} ไม่ใช่เรตที่เป็นไปได้")
        ho, hc = ((b.get("hdp") or {}).get("open") or {}), ((b.get("hdp") or {}).get("current") or {})
        if _num(ho.get("line")) and _num(hc.get("line")) and abs(ho["line"] - hc["line"]) > 1.0:
            warn.append(f"{nm}: เรตแฮนดิแคปขยับมากผิดปกติ ({ho['line']:+g} → {hc['line']:+g}) โปรดตรวจรูป")
        if _num(ho.get("line")) and _num(hc.get("line")) and ho["line"] * hc["line"] < 0 and min(abs(ho["line"]), abs(hc["line"])) >= 0.25:
            crit.append(f"{nm}: เรตแฮนดิแคปเปลี่ยนฝั่ง ({ho['line']:+g} → {hc['line']:+g}) มักเกิดจากอ่านเครื่องหมายผิด")
    if flips:
        crit.append("เรตแฮนดิแคปขัดกับราคา 1X2 (ทีมต่อคนละฝั่ง) ที่: " + ", ".join(flips) + " -> เครื่องหมาย +/- อาจกลับด้าน หรือสลับเหย้า/เยือน")
    return warn, crit


def get_api_key(getter):
    """getter(name) -> ค่า secret/env ; ใช้คีย์ Gemini เท่านั้น"""
    return getter("GEMINI_API_KEY") or getter("GOOGLE_API_KEY")


def _load_images(paths):
    out = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext not in MEDIA_TYPES:
            sys.exit(f"ไม่รองรับไฟล์ {p} (รองรับ: {', '.join(MEDIA_TYPES)})")
        if not os.path.exists(p):
            sys.exit(f"ไม่พบไฟล์ {p}")
        with open(p, "rb") as fh:
            raw = fh.read()
        if len(raw) > 5 * 1024 * 1024:
            sys.exit(f"{p} ใหญ่เกิน 5MB กรุณาย่อรูปก่อน")
        out.append((os.path.basename(p), MEDIA_TYPES[ext], base64.b64encode(raw).decode()))
    return out


RETRY_CODES = {429, 500, 502, 503, 504}
API_ERR_TH = {429: "Gemini ถูกเรียกใช้ถี่เกินโควตาชั่วคราว", 500: "เซิร์ฟเวอร์ Gemini ขัดข้องชั่วคราว",
              502: "เซิร์ฟเวอร์ Gemini ขัดข้องชั่วคราว", 503: "Gemini มีผู้ใช้หนาแน่น ให้บริการไม่ได้ชั่วคราว",
              504: "Gemini ตอบช้าเกินกำหนด", 400: "คำขอไม่ถูกต้อง (ตรวจชื่อโมเดล/รูปภาพ)",
              401: "API key ไม่ถูกต้อง",
              402: "เครดิต Gemini แบบเติมเงินล่วงหน้าหมดแล้ว — เติมเครดิตที่ aistudio.google.com/billing (ปุ่ม Buy credits) "
                   "แล้วรอสักครู่ให้ยอดอัปเดต (ตั้ง Auto-reload ไว้ได้เพื่อไม่ให้หมดอีก)", 403: "API key ไม่มีสิทธิ์ใช้โมเดลนี้", 404: "ไม่พบโมเดลนี้"}


def _post_json(url, headers, payload, tries=4):
    """เรียก API พร้อมลองใหม่อัตโนมัติเมื่อเซิร์ฟเวอร์ไม่ว่างชั่วคราว (429/5xx): รอ 2, 5, 10 วินาที"""
    body = json.dumps(payload).encode("utf-8")
    waits = [2, 5, 10]
    for k in range(tries):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:300]
            if e.code in RETRY_CODES and k < tries - 1:
                time.sleep(waits[min(k, len(waits) - 1)])
                continue
            msg = API_ERR_TH.get(e.code, "API ตอบกลับผิดพลาด")
            extra = f" (ลองแล้ว {tries} ครั้ง) — รอสักครู่แล้วกดวิเคราะห์ใหม่" if e.code in RETRY_CODES else ""
            sys.exit(f"{msg}{extra} [รหัส {e.code}]" + ("" if e.code in RETRY_CODES or e.code == 402 else f": {detail}"))
        except urllib.error.URLError as e:
            if k < tries - 1:
                time.sleep(waits[min(k, len(waits) - 1)])
                continue
            sys.exit(f"เชื่อมต่อ API ไม่ได้: {e.reason}")
        except TimeoutError:
            if k < tries - 1:
                continue
            sys.exit("Gemini ตอบช้าเกินกำหนด — รอสักครู่แล้วลองใหม่")


def extract_from_images(paths, model, api_key):
    """อ่านรูปด้วย Gemini แล้วคืน dict ข้อมูลแมตช์"""
    if not str(model).lower().startswith("gemini"):
        sys.exit(f"รองรับเฉพาะโมเดล Gemini (ได้รับ '{model}')")
    imgs = _load_images(paths)
    task = EXTRACT_PROMPT + json.dumps(EXTRACT_SCHEMA, ensure_ascii=False, indent=1)
    parts = []
    for i, (name, mt, b64) in enumerate(imgs, 1):
        parts.append({"text": f"รูปที่ {i}: {name}"})
        parts.append({"inline_data": {"mime_type": mt, "data": b64}})
    parts.append({"text": task})
    data = _post_json(GEMINI_URL.format(model=model),
                      {"content-type": "application/json", "x-goog-api-key": api_key},
                      {"contents": [{"role": "user", "parts": parts}],
                       "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 8192}})
    cands = data.get("candidates") or []
    if not cands:
        fb = data.get("promptFeedback", {})
        sys.exit(f"Gemini ไม่ส่งผลลัพธ์กลับมา: {json.dumps(fb, ensure_ascii=False)[:300] or 'ไม่ทราบสาเหตุ'}")
    text = "".join(pt.get("text", "") for pt in cands[0].get("content", {}).get("parts", [])
                   if not pt.get("thought"))
    return parse_json_reply(text)


RESEARCH_PROMPT = """คุณคือนักวิเคราะห์ข้อมูลฟุตบอล ใช้ Google Search ค้นหาข้อมูลล่าสุด เพื่อกำหนด "บริบทแมตช์" ของคู่นี้:
เจ้าบ้าน: @HOME@
ทีมเยือน: @AWAY@
รายการแข่งขัน: @LEAGUE@
วันนี้: @TODAY@ (แมตช์คือนัดที่จะแข่งในอีกไม่กี่ชั่วโมง/วันข้างหน้า)

กติกา:
1. ใช้เฉพาะข้อมูลที่ค้นเจอจริง ห้ามเดา ถ้าไม่พบหรือไม่แน่ใจให้ใส่ null (สำหรับตัวเลข/ข้อความ) หรือ false (สำหรับ flag ที่ไม่มีหลักฐาน)
2. derby = true เมื่อเป็นคู่ปรับ/ดาร์บี้ที่มีชื่อเรียกหรือแหล่งข้อมูลยืนยัน
3. competition.type: league | cup | playoff ; cup_group_stage = ถ้วยรอบแบ่งกลุ่ม ; knockout = รอบน็อคเอาต์/เพลย์ออฟ ; continental_cup = ถ้วยระดับทวีป (เช่น Champions League, Libertadores, AFC)
4. league.avg_goals_per_match = ค่าเฉลี่ยประตูรวมต่อนัดของลีกในซีซันนี้ ; high_scoring = true ถ้า >= 2.9
   league.draw_rate_pct = สัดส่วนเสมอ (%) ของลีกซีซันนี้ ; high_draw = true ถ้า >= 28
   league.size = จำนวนทีมในลีก ; high_volatility = true เฉพาะเมื่อมีหลักฐานว่าลีกผลไม่แน่นอนมาก (ปกติ false)
5. standings = อันดับล่าสุดของแต่ละทีมในตาราง (ตัวเลข)
6. motivation.desperation = "home" หรือ "away" เฉพาะทีมที่กำลังหนีตก/ลุ้นแชมป์/ลุ้นโควตาในช่วงท้ายฤดูกาลอย่างชัดเจน ไม่เช่นนั้น null
7. home_form_home = ผลเกมเหย้า 5 นัดหลังสุดของเจ้าบ้าน (ลีกเดียวกัน) เป็น {"w":..,"d":..,"l":..} รวมต้องเท่ากับ 5 ไม่ครบ/ไม่ชัวร์ให้ null
8. late_goal_tendency = true เฉพาะเมื่อมีสถิติว่า 2 ทีมยิงประตูช่วงท้ายเกมบ่อยชัดเจน ไม่เช่นนั้น false
11. women_or_regional = true ถ้าเป็นฟุตบอลหญิง หรือลีกระดับรอง/ลีกภูมิภาค (ต่ำกว่าลีกสูงสุดของประเทศ) ; asian_cup = true ถ้าเป็นถ้วยระดับเอเชีย (AFC)
12. venue_stats = สถิติแยกสนามจาก 5 นัดหลังสุด (ลีก/รายการเดียวกันถ้ามี): เจ้าบ้าน "เฉพาะเกมเหย้า" และทีมเยือน "เฉพาะเกมเยือน"
    เป็นค่าเฉลี่ยต่อนัด: home_gf, home_ga (ประตูได้/เสียของเจ้าบ้านในบ้าน), away_gf, away_ga (ของทีมเยือนนอกบ้าน), games_home, games_away (จำนวนนัดที่ใช้)
    ไม่พบ/ไม่ชัวร์ให้ null ทั้งก้อน
13. away_form_away = ผลเกมเยือน 5 นัดหลังสุดของทีมเยือน เป็น {"w":..,"d":..,"l":..} รวม = 5 ไม่ชัวร์ให้ null
9. evidence = ข้อความสั้นภาษาไทยไม่เกิน 6 ข้อ บอกหลักฐานสำคัญของแต่ละ flag ที่เป็น true
10. confidence = high | medium | low

ตอบเป็น JSON ล้วน ไม่มีข้อความอื่น ไม่มี markdown ตามโครงสร้างนี้:
{"competition":{"type":"league","name":"...","cup_group_stage":false,"knockout":false,"continental_cup":false},
 "derby":false,"derby_reason":null,
 "league":{"size":null,"avg_goals_per_match":null,"draw_rate_pct":null,"high_scoring":false,"high_draw":false,"high_volatility":false},
 "standings":{"home_rank":null,"away_rank":null},
 "motivation":{"desperation":null,"reason":null},
 "home_form_home":null,"away_form_away":null,"late_goal_tendency":false,
 "women_or_regional":false,"asian_cup":false,
 "venue_stats":{"home_gf":null,"home_ga":null,"away_gf":null,"away_ga":null,"games_home":null,"games_away":null},
 "evidence":["..."],"confidence":"medium"}"""


INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


def _collect_links(node, out, depth=0):
    """เก็บทุก dict ที่มีลิงก์ http (url/uri) พร้อมชื่อ จากผลค้นหา/การอ้างอิง (ไม่สนรูปแบบการซ้อน)"""
    if depth > 10:
        return
    if isinstance(node, list):
        for x in node:
            _collect_links(x, out, depth + 1)
        return
    if not isinstance(node, dict):
        return
    link = node.get("url") or node.get("uri")
    if isinstance(link, str) and link.startswith("http"):
        out.append({"title": str(node.get("title") or node.get("domain") or node.get("source") or ""), "uri": link})
    for k, v in node.items():
        if isinstance(v, (list, dict)):
            _collect_links(v, out, depth + 1)


def _walk_interaction(node, acc, depth=0):
    """ไล่อ่านคำตอบของ Interactions API แบบทนต่อโครงสร้างที่ต่างกัน: เก็บข้อความคำตอบ, คำค้น, และแหล่งอ้างอิง"""
    if depth > 12:
        return
    if isinstance(node, list):
        for x in node:
            _walk_interaction(x, acc, depth + 1)
        return
    if not isinstance(node, dict):
        return
    t = node.get("type")
    if t == "thought":                                    # ไม่เอาความคิดภายใน
        return
    if t == "google_search_result":                       # รายการผลค้นหา: เก็บเฉพาะลิงก์+ชื่อ (ข้าม HTML คำแนะนำการค้น)
        acc["searched"] = True
        _collect_links({k: v for k, v in node.items() if k not in ("search_suggestions", "rendered_content")}, acc["sources"])
        return
    if t == "google_search_call":
        acc["searched"] = True
        qs = (node.get("arguments") or {}).get("queries") if isinstance(node.get("arguments"), dict) else None
        acc["queries"] += [str(x) for x in (qs or []) if x]
        return
    if t == "text" and isinstance(node.get("text"), str):
        acc["text"].append(node["text"])
    if node.get("annotations"):
        _collect_links(node["annotations"], acc["sources"])
    for k, v in node.items():
        if k not in ("annotations", "arguments") and isinstance(v, (list, dict)):
            _walk_interaction(v, acc, depth + 1)


def _uniq_sources(src):
    out, seen = [], set()
    for x in src:
        key = x.get("title") or x.get("uri")
        if key and key not in seen:
            seen.add(key)
            out.append(x)
    return out


def gemini_search(prompt, model, api_key, max_tokens=4096, temperature=None):
    """ถาม Gemini พร้อม Google Search คืน {"text", "sources", "queries", "searched", "api"}
    searched = True เมื่อ API ยืนยันว่ามีการค้นเว็บจริง (เห็นขั้นตอนค้นหา/คำค้น/แหล่งอ้างอิง) · False = ไม่มีหลักฐานการค้นกลับมา
    ใช้ Interactions API ก่อน (ส่งหลักฐานการค้นกลับมาครบกว่า) ถ้าใช้ไม่ได้จึงถอยไปใช้ generateContent แบบเดิม"""
    if not str(model).lower().startswith("gemini"):
        sys.exit(f"รองรับเฉพาะโมเดล Gemini (ได้รับ '{model}')")
    hdr = {"content-type": "application/json", "x-goog-api-key": api_key}
    try:
        data = _post_json(INTERACTIONS_URL, hdr, {"model": model, "input": prompt, "tools": [{"type": "google_search"}]}, tries=2)
        acc = {"text": [], "sources": [], "queries": [], "searched": False}
        steps = data.get("steps") if isinstance(data, dict) and data.get("steps") is not None else data
        _walk_interaction(steps, acc)
        text = "".join(acc["text"]).strip()
        if text:
            src = _uniq_sources(acc["sources"])
            shape = []                                    # โครงสร้างคำตอบแบบย่อ (ไว้วินิจฉัยเมื่อไม่ได้ลิงก์แหล่ง)
            for st_ in (steps if isinstance(steps, list) else [])[:12]:
                if isinstance(st_, dict):
                    shape.append(str(st_.get("type")) + ":" + ",".join(sorted(k for k in st_ if k != "type"))[:80])
            return {"text": text, "sources": src, "queries": acc["queries"], "api": "interactions",
                    "searched": bool(acc["searched"] or src), "shape": shape if not src else None}
    except (SystemExit, Exception):  # noqa  (รุ่น/บัญชีที่ยังใช้ช่องทางใหม่ไม่ได้ -> ใช้ช่องทางเดิม)
        pass
    gen = {"maxOutputTokens": max_tokens}
    if temperature is not None:
        gen["temperature"] = temperature
    data = _post_json(GEMINI_URL.format(model=model), hdr,
                      {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                       "tools": [{"google_search": {}}], "generationConfig": gen})
    cands = data.get("candidates") or []
    if not cands:
        sys.exit("Gemini ไม่ส่งผลการค้นหากลับมา")
    cand = cands[0]
    text = "".join(pt.get("text", "") for pt in cand.get("content", {}).get("parts", []) if not pt.get("thought"))
    gm = cand.get("groundingMetadata") or {}
    src = _uniq_sources([{"title": (ch.get("web") or {}).get("title") or "", "uri": (ch.get("web") or {}).get("uri") or ""}
                         for ch in gm.get("groundingChunks") or []])
    qs = list(gm.get("webSearchQueries") or [])
    return {"text": text, "sources": src, "queries": qs, "api": "generateContent", "searched": bool(src or qs), "shape": None}


def research_context(home, away, league, model, api_key, today=None):
    """ให้ Gemini ค้นหาข้อมูลจริงผ่าน Google Search เพื่อกำหนดบริบทแมตช์ คืน (dict ผลวิจัย, แหล่งข้อมูล, คำค้น)"""
    prompt = (RESEARCH_PROMPT.replace("@HOME@", str(home)).replace("@AWAY@", str(away))
              .replace("@LEAGUE@", str(league or "ไม่ระบุ")).replace("@TODAY@", today or now_th("%Y-%m-%d")))
    r = gemini_search(prompt, model, api_key, 4096)
    out = parse_json_reply(r["text"])
    if isinstance(out, dict):
        out["_search"] = {"api": r["api"], "searched": r["searched"], "shape": r.get("shape")}
    return out, r["sources"], r["queries"]


def _bool(v):
    return v if isinstance(v, bool) else None


def apply_research(m, r, sources=None, queries=None):
    """นำผลวิจัยบริบทมาใส่ในข้อมูลแมตช์ (ตรวจชนิดข้อมูลทุกช่อง เติมเฉพาะค่าที่ยังไม่มี)"""
    if not isinstance(r, dict):
        return m
    ctx = m.get("context") if isinstance(m.get("context"), dict) else {}
    m["context"] = ctx
    comp = r.get("competition") if isinstance(r.get("competition"), dict) else {}
    if comp.get("type") in ("league", "cup", "playoff"):
        ctx["type"] = comp["type"]
    for k in ("cup_group_stage", "knockout", "continental_cup"):
        if _bool(comp.get(k)) is not None:
            ctx[k] = comp[k]
    if _bool(r.get("derby")) is not None:
        ctx["derby"] = r["derby"]
    lg = r.get("league") if isinstance(r.get("league"), dict) else {}
    for src, dst in (("high_scoring", "high_scoring_league"), ("high_draw", "high_draw_league"),
                     ("high_volatility", "high_volatility")):
        if _bool(lg.get(src)) is not None:
            ctx[dst] = lg[src]
    if _num(lg.get("size")) and 8 <= lg["size"] <= 40 and not _num(m.get("league_size")):
        m["league_size"] = int(lg["size"])
    stn = r.get("standings") if isinstance(r.get("standings"), dict) else {}
    rk = m.get("rank") if isinstance(m.get("rank"), dict) else {}
    for side in ("home", "away"):
        if not _num(rk.get(side)) and _num(stn.get(side + "_rank")):
            rk[side] = stn[side + "_rank"]
    m["rank"] = rk
    mo = r.get("motivation") if isinstance(r.get("motivation"), dict) else {}
    if mo.get("desperation") in ("home", "away"):
        ctx["desperation"] = mo["desperation"]
    if _bool(r.get("late_goal_tendency")) is not None:
        ctx["late_goal_tendency"] = r["late_goal_tendency"]
    hf = r.get("home_form_home")
    if isinstance(hf, dict) and all(isinstance(hf.get(k), int) and not isinstance(hf.get(k), bool) for k in ("w", "d", "l")) \
            and hf["w"] + hf["d"] + hf["l"] == 5 and not m.get("home_form_home"):
        m["home_form_home"] = {k: hf[k] for k in ("w", "d", "l")}
    for k in ("women_or_regional", "asian_cup"):
        if _bool(r.get(k)) is not None:
            ctx[k] = r[k]
    af = r.get("away_form_away")
    if isinstance(af, dict) and all(isinstance(af.get(k), int) and not isinstance(af.get(k), bool) for k in ("w", "d", "l")) \
            and af["w"] + af["d"] + af["l"] == 5 and not m.get("away_form_away"):
        m["away_form_away"] = {k: af[k] for k in ("w", "d", "l")}
    vs = r.get("venue_stats") if isinstance(r.get("venue_stats"), dict) else {}
    keys = ("home_gf", "home_ga", "away_gf", "away_ga")
    if all(_num(vs.get(k)) and 0 <= vs[k] <= 6 for k in keys) and not (m.get("stats") or {}).get("venue"):
        m["stats"] = {**{k: float(vs[k]) for k in keys}, "venue": True,
                      "games_home": vs.get("games_home") if _num(vs.get("games_home")) else None,
                      "games_away": vs.get("games_away") if _num(vs.get("games_away")) else None}
    ev = [str(x) for x in (r.get("evidence") or []) if x][:6] if isinstance(r.get("evidence"), list) else []
    m["research"] = {"evidence": ev, "sources": (sources or [])[:8], "queries": (queries or [])[:6],
                     "confidence": r.get("confidence") if r.get("confidence") in ("high", "medium", "low") else None,
                     "derby_reason": r.get("derby_reason"), "desperation_reason": mo.get("reason"),
                     "avg_goals": lg.get("avg_goals_per_match") if _num(lg.get("avg_goals_per_match")) else None,
                     "draw_rate": lg.get("draw_rate_pct") if _num(lg.get("draw_rate_pct")) else None,
                     "competition": comp.get("name"), "search": r.get("_search")}
    return m


# ----------------------------------------------------------------------------
# ข้อมูลทีม (xG/xGA, ตัวเจ็บ/โดนแบน, บอลถ้วย, วันพัก, ตัวจริง) — นโยบาย "ไม่มีให้บอกว่าไม่มี ห้ามมโน"
#   ชั้นที่ 1 (คำสั่ง Gemini): ทุกค่าต้องมีแหล่ง + วันที่ ไม่พบให้ null และระบุในรายการ missing
#   ชั้นที่ 2 (โค้ดตรวจซ้ำ): แหล่งต้องตรงกับผลค้นหาจริงของ Google (grounding) ช่วงค่าต้องสมเหตุสมผล ข้อมูลต้องไม่เก่า
#   ค่าที่ไม่ผ่าน = แสดงว่า "ไม่มีข้อมูล"/"ไม่ยืนยัน" และไม่ถูกนำไปคำนวณ
#   Rule ที่ใช้ข้อมูลนี้ (R42-R46) เริ่มเป็นเงาเสมอ ไม่เปลี่ยนการฟันธงจนกว่าจะผ่านเกณฑ์นอกกลุ่มตัวอย่าง
# ----------------------------------------------------------------------------
TEAM_NEWS_PROMPT = """คุณคือผู้ช่วยค้นข้อมูลฟุตบอล ใช้ Google Search ค้นข้อมูลก่อนแข่งของคู่นี้:
เจ้าบ้าน: @HOME@
ทีมเยือน: @AWAY@
รายการแข่งขัน: @LEAGUE@
วันนี้: @TODAY@

กฎเหล็ก (สำคัญที่สุด ห้ามฝ่าฝืน):
- ห้ามเดา ห้ามประมาณ ห้ามคำนวณเอง ห้ามแต่งตัวเลขหรือชื่อนักเตะขึ้นมาเด็ดขาด
- ทุกค่าต้องมาจากหน้าเว็บที่คุณค้นเจอจริงในการค้นครั้งนี้ และต้องใส่ "source" เป็นชื่อโดเมนของเว็บนั้น (เช่น fbref.com) และ "as_of" เป็นวันที่ของข้อมูล/ข่าว (YYYY-MM-DD)
- ถ้าค้นไม่เจอ ไม่ชัวร์ หรือข้อมูลขัดกันเอง ให้ใส่ null แล้วเขียนเหตุผลสั้นๆ ในรายการ "missing" เช่น "ไม่พบ xG ของ @AWAY@"
- การตอบว่า "ไม่มีข้อมูล" ถือว่าถูกต้องและดีกว่าการให้ข้อมูลที่ไม่แน่ใจเสมอ

สิ่งที่ต้องค้น:
1. match_date = วันแข่งของนัดนี้ (YYYY-MM-DD) ถ้าไม่พบ null
2. xg (แยก home/away) = ค่าเฉลี่ยต่อนัดจาก "5 นัดล่าสุด" (ระบุจำนวนนัดที่ใช้จริงใน games)
   xg = expected goals ที่ทีมสร้างได้ต่อนัด, xga = expected goals ที่เสียต่อนัด, gf/ga = ประตูจริงได้/เสียต่อนัด ในนัดชุดเดียวกัน
   ใช้เฉพาะเว็บที่เผยแพร่ค่า xG จริง (เช่น fbref, understat, fotmob, sofascore, footystats, americansocceranalysis)
   ห้ามแปลงจากจำนวนการยิงเอง ถ้าลีกนี้ไม่มี xG ให้ null ทั้งก้อน
3. injuries (แยก home/away) = นักเตะที่ "เจ็บ/ไม่แน่ว่าจะได้ลง/โดนแบน" สำหรับนัดนี้ จากข่าวไม่เกิน 7 วัน
   status: out | doubtful | suspended
   role: starter ถ้าแหล่งข้อมูลระบุหรือแสดงว่าเป็นตัวจริงประจำ (เช่น ลงตัวจริงส่วนใหญ่ของฤดูกาล) ; rotation ถ้าเป็นตัวสำรอง/หมุนเวียน ; unknown ถ้าไม่มีหลักฐาน (ห้ามเดา)
   position: GK | DF | MF | FW | unknown
   injuries_checked.home/away = true เฉพาะเมื่อพบรายงานข่าวทีมก่อนเกมของนัดนี้จริง (แม้จะไม่มีตัวเจ็บเลย) ไม่เช่นนั้น false
4. cup = ข้อมูลถ้าเป็นบอลถ้วย: is_cup, leg (1/2/null), first_leg_score (เช่น "2-1" มุมมองเจ้าบ้านนัดนี้ หรือ null)
   rotation_risk.home/away = true เฉพาะเมื่อมีข่าว/คำให้สัมภาษณ์โค้ชว่าจะหมุนเวียนหรือพักตัวหลัก ไม่เช่นนั้น false ; rotation_evidence = ข้อความสั้นพร้อมแหล่ง
5. last_match (แยก home/away) = วันที่ของนัดล่าสุดที่ทีมลงแข่งก่อนนัดนี้ (ทุกรายการ) {"date","competition","source"}
6. lineups = confirmed true เฉพาะเมื่อมีการประกาศรายชื่อตัวจริงอย่างเป็นทางการแล้วเท่านั้น ; notes = ตัวหลักที่ไม่อยู่ในตัวจริง (ถ้ามี)
7. other_news = ข่าวสำคัญอื่นที่อาจมีผลต่อเกม (เปลี่ยนโค้ช, ปัญหาในทีม, สภาพอากาศรุนแรง) ไม่เกิน 4 ข้อ ทุกข้อต้องมี source และ as_of

ตอบเป็น JSON ล้วน ไม่มีข้อความอื่น ไม่มี markdown ตามโครงสร้างนี้:
{"match_date":null,
 "xg":{"home":{"games":5,"xg":null,"xga":null,"gf":null,"ga":null,"source":null,"as_of":null},
       "away":{"games":5,"xg":null,"xga":null,"gf":null,"ga":null,"source":null,"as_of":null}},
 "injuries":{"home":[{"player":"...","status":"out","role":"unknown","position":"unknown","source":"...","as_of":"..."}],"away":[]},
 "injuries_checked":{"home":false,"away":false},
 "cup":{"is_cup":false,"leg":null,"first_leg_score":null,"rotation_risk":{"home":false,"away":false},"rotation_evidence":null,"source":null},
 "last_match":{"home":null,"away":null},
 "lineups":{"confirmed":false,"source":null,"notes":null},
 "other_news":[],
 "missing":["..."]}"""

TN_MAX_AGE = {"xg": 30, "injury": 10, "news": 14}       # อายุข้อมูลสูงสุด (วัน) ที่ยังนำไปใช้


def research_team_news(home, away, league, model, api_key, today=None):
    """ค้นข้อมูลทีมด้วย Gemini + Google Search คืน (ผลดิบ, แหล่งข้อมูลจริง, คำค้น)
    หลักฐานว่ามีการค้นจริงหรือไม่แนบไปในผลดิบที่คีย์ "_search" (validate_team_news นำไปใช้ตรวจ)"""
    prompt = (TEAM_NEWS_PROMPT.replace("@HOME@", str(home)).replace("@AWAY@", str(away))
              .replace("@LEAGUE@", str(league or "ไม่ระบุ")).replace("@TODAY@", today or now_th("%Y-%m-%d")))
    r = gemini_search(prompt, model, api_key, 6144, temperature=0)
    out = parse_json_reply(r["text"])
    if isinstance(out, dict):
        out["_search"] = {"api": r["api"], "searched": r["searched"], "shape": r.get("shape")}
    return out, r["sources"], r["queries"]


def _domain(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"^[a-z]+://", "", s).split("/")[0].split("?")[0]
    s = re.sub(r"^(www|m|en|th)\.", "", s)
    return s if "." in s else ""


def _src_check(src, grounded):
    """แหล่งที่ AI อ้าง ต้องอยู่ในผลค้นหาจริงของ Google ครั้งนี้ -> (โดเมน, ยืนยันได้หรือไม่)"""
    d = _domain(src)
    if not d:
        return None, False
    return d, any(d == g or d.endswith("." + g) or g.endswith("." + d) for g in grounded)


def _date(s):
    try:
        return _dt_mod.date.fromisoformat(str(s)[:10])
    except Exception:  # noqa
        return None


def _age_days(as_of, ref):
    d = _date(as_of)
    return None if d is None or ref is None else (ref - d).days


def validate_team_news(raw, sources, queries=None, today=None, home=None, away=None):
    """ตรวจผลค้นข้อมูลทีมทุกค่า: มีแหล่ง + แหล่งตรงกับผลค้นหาจริง + ช่วงค่าสมเหตุสมผล + ไม่เก่าเกิน
    ระดับหลักฐาน:  ok = แหล่งที่อ้างตรงกับแหล่งที่ Google ส่งกลับมา (ใช้คำนวณได้)
                   reported = API ยืนยันว่ามีการค้นเว็บจริง แต่จับคู่แหล่งรายรายการไม่ได้ (แสดงพร้อมป้าย ไม่ใช้คำนวณ)
                   unverified = ไม่มีหลักฐานการค้น/ไม่ระบุแหล่ง-วันที่ (ไม่แสดงค่า) · stale | invalid | none"""
    ref = _date(today) or _dt_mod.datetime.now(TZ_TH).date()
    grounded = set()
    for s_ in sources or []:
        for txt in (s_.get("title"), s_.get("uri")):
            for mt in re.findall(r"[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)+", str(txt or "").lower()):
                d_ = _domain(mt)
                if d_ and "vertexaisearch" not in d_ and "googleapis" not in d_:
                    grounded.add(d_)
    r = raw if isinstance(raw, dict) else {}
    se = r.get("_search") if isinstance(r.get("_search"), dict) else {}
    searched = bool(se.get("searched") or grounded or queries)       # มีหลักฐานจาก API ว่าค้นเว็บจริง
    out = {"searched_at": ref.isoformat(), "grounded": sorted(grounded), "sources": (sources or [])[:12],
           "queries": (queries or [])[:8], "missing": [], "problems": [], "searched": searched, "api": se.get("api"),
           "shape": se.get("shape")}
    if not searched:
        out["problems"].append("Gemini ไม่ส่งหลักฐานการค้นเว็บกลับมาในครั้งนี้ จึงยืนยันไม่ได้ว่าข้อมูลมาจากการค้นจริง — ไม่แสดงและไม่นำข้อมูลทีมไปใช้")
    elif not grounded:
        out["problems"].append("Gemini ค้นเว็บจริง แต่ไม่ส่งรายชื่อแหล่งรายรายการกลับมา — แสดงข้อมูลพร้อมป้าย “AI รายงาน” และยังไม่นำไปคำนวณ")
    names = {"home": home or "เจ้าบ้าน", "away": away or "ทีมเยือน"}

    def stamp(item, kind):
        d, ok = _src_check(item.get("source"), grounded)
        age = _age_days(item.get("as_of"), ref)
        if not d:
            return "unverified", "ไม่ระบุแหล่งข้อมูล", d, age
        if not ok and not searched:
            return "unverified", "ไม่มีหลักฐานว่าค้นเว็บจริง", d, age
        if age is None:
            return "unverified", "ไม่ระบุวันที่ของข้อมูล", d, age
        if age < -2:
            return "invalid", "วันที่ของข้อมูลอยู่ในอนาคต", d, age
        if age > TN_MAX_AGE[kind]:
            return "stale", f"ข้อมูลเก่า {age} วัน (เกิน {TN_MAX_AGE[kind]} วัน)", d, age
        if not ok:
            return "reported", f"AI รายงานจาก {d} (ระบบยืนยันแหล่งรายรายการไม่ได้)", d, age
        return "ok", None, d, age

    # วันแข่ง
    md = _date(r.get("match_date") if not isinstance(r.get("match_date"), dict) else r["match_date"].get("value"))
    out["match_date"] = md.isoformat() if md and -3 <= (md - ref).days <= 14 else None

    # xG / xGA
    out["xg"] = {}
    xg = r.get("xg") if isinstance(r.get("xg"), dict) else {}
    for side in ("home", "away"):
        it = xg.get(side) if isinstance(xg.get(side), dict) else None
        vals = {k: it.get(k) for k in ("xg", "xga", "gf", "ga")} if it else {}
        if not it or not _num(vals.get("xg")) or not _num(vals.get("xga")):
            out["xg"][side] = {"status": "none"}
            out["missing"].append(f"ไม่มีข้อมูล xG/xGA ของ {names[side]}")
            continue
        st_, why, d, age = stamp(it, "xg")
        games = it.get("games") if _num(it.get("games")) else None
        if not all(0.05 <= vals[k] <= 4.5 for k in ("xg", "xga")) or (games is not None and not 1 <= games <= 10):
            st_, why = "invalid", "ค่าไม่สมเหตุสมผล (ไม่ใช่ค่าเฉลี่ยต่อนัด)"
        for k in ("gf", "ga"):
            if not (_num(vals.get(k)) and 0 <= vals[k] <= 6):
                vals[k] = None
        out["xg"][side] = {**{k: (round(float(v), 2) if v is not None else None) for k, v in vals.items()},
                           "games": int(games) if games else None, "source": d, "as_of": it.get("as_of"),
                           "status": st_, "why": why}

    # ตัวเจ็บ/โดนแบน
    out["injuries"], out["injuries_checked"] = {}, {}
    inj = r.get("injuries") if isinstance(r.get("injuries"), dict) else {}
    chk = r.get("injuries_checked") if isinstance(r.get("injuries_checked"), dict) else {}
    for side in ("home", "away"):
        lst = []
        for it in (inj.get(side) or [])[:15] if isinstance(inj.get(side), list) else []:
            if not isinstance(it, dict) or not str(it.get("player") or "").strip():
                continue
            st_, why, d, age = stamp(it, "injury")
            status = it.get("status") if it.get("status") in ("out", "doubtful", "suspended") else None
            if status is None:
                st_, why = "invalid", "ไม่ระบุสถานะ"
            lst.append({"player": str(it["player"]).strip()[:40], "status": status,
                        "role": it.get("role") if it.get("role") in ("starter", "rotation") else "unknown",
                        "position": it.get("position") if it.get("position") in ("GK", "DF", "MF", "FW") else "unknown",
                        "source": d, "as_of": it.get("as_of"), "st": st_, "why": why})
        out["injuries"][side] = lst
        checked = chk.get(side) is True and searched
        out["injuries_checked"][side] = checked or any(x["st"] in ("ok", "reported") for x in lst)
        if not out["injuries_checked"][side]:
            out["missing"].append(f"ไม่มีรายงานข่าวทีม/ตัวเจ็บของ {names[side]}")

    # บอลถ้วย
    cup = r.get("cup") if isinstance(r.get("cup"), dict) else {}
    rr = cup.get("rotation_risk") if isinstance(cup.get("rotation_risk"), dict) else {}
    d, ok = _src_check(cup.get("source"), grounded)
    fls = cup.get("first_leg_score")
    out["cup"] = {"is_cup": cup.get("is_cup") is True, "leg": cup.get("leg") if cup.get("leg") in (1, 2) else None,
                  "first_leg_score": fls if isinstance(fls, str) and re.match(r"^\d{1,2}-\d{1,2}$", fls.strip()) else None,
                  "rotation": {s: rr.get(s) is True and ok for s in ("home", "away")},
                  "rotation_claimed": {s: rr.get(s) is True for s in ("home", "away")},
                  "evidence": str(cup.get("rotation_evidence"))[:200] if cup.get("rotation_evidence") else None,
                  "source": d, "verified": ok}
    if any(out["cup"]["rotation_claimed"].values()) and not ok:
        out["problems"].append("ข่าวหมุนเวียนผู้เล่นไม่มีแหล่งยืนยัน — ไม่นำไปใช้")

    # วันพัก (โค้ดคำนวณเองจากวันที่ ไม่ให้ AI คำนวณ)
    out["rest"] = {}
    lm = r.get("last_match") if isinstance(r.get("last_match"), dict) else {}
    kick = _date(out["match_date"]) or ref
    for side in ("home", "away"):
        it = lm.get(side) if isinstance(lm.get(side), dict) else None
        ld = _date(it.get("date")) if it else None
        if not ld:
            out["rest"][side] = {"status": "none"}
            out["missing"].append(f"ไม่มีข้อมูลนัดล่าสุดของ {names[side]}")
            continue
        d, ok = _src_check(it.get("source"), grounded)
        days = (kick - ld).days
        st_ = "invalid" if not 1 <= days <= 60 else ("ok" if ok else "reported" if (searched and d) else "unverified")
        out["rest"][side] = {"days": days if 1 <= days <= 60 else None, "last_date": ld.isoformat(),
                             "competition": str(it.get("competition") or "")[:40] or None, "source": d, "status": st_}

    # ตัวจริง
    lu = r.get("lineups") if isinstance(r.get("lineups"), dict) else {}
    d, ok = _src_check(lu.get("source"), grounded)
    out["lineups"] = {"confirmed": lu.get("confirmed") is True and ok, "claimed": lu.get("confirmed") is True,
                      "source": d, "notes": str(lu.get("notes"))[:200] if lu.get("notes") else None}

    # ข่าวอื่น
    out["other_news"] = []
    for it in (r.get("other_news") or [])[:4] if isinstance(r.get("other_news"), list) else []:
        if isinstance(it, dict) and it.get("text"):
            st_, why, d, age = stamp(it, "news")
            out["other_news"].append({"text": str(it["text"])[:200], "source": d, "as_of": it.get("as_of"), "st": st_, "why": why})

    for x in (r.get("missing") or [])[:10] if isinstance(r.get("missing"), list) else []:
        if x and str(x) not in out["missing"]:
            out["missing"].append(str(x)[:120])
    return _strip_unverified(out, names)


def _strip_unverified(out, names):
    """ห้ามแสดงค่าที่ยืนยันแหล่งไม่ได้: ลบตัวเลข/ชื่อทิ้ง เหลือเพียงข้อความว่า 'ไม่มีข้อมูลที่ยืนยันได้' พร้อมเหตุผล"""
    bad = ("unverified", "invalid")
    for side in ("home", "away"):
        x = out["xg"].get(side) or {}
        if x.get("status") in bad:
            out["xg"][side] = {"status": x["status"], "why": x.get("why")}
            out["problems"].append(f"xG ของ {names[side]}: ไม่มีข้อมูลที่ยืนยันได้ ({x.get('why')}) — ไม่แสดงค่า")
        lst = out["injuries"].get(side) or []
        keep = [p for p in lst if p["st"] not in bad]
        if len(keep) < len(lst):
            out["problems"].append(f"ตัดรายชื่อตัวเจ็บของ {names[side]} ที่ยืนยันแหล่งไม่ได้ออก {len(lst) - len(keep)} รายการ")
        out["injuries"][side] = keep
        rs = out["rest"].get(side) or {}
        if rs.get("status") in bad:
            out["rest"][side] = {"status": rs["status"]}
            out["problems"].append(f"วันพักของ {names[side]}: ไม่มีข้อมูลที่ยืนยันได้ — ไม่แสดงค่า")
    n0 = len(out["other_news"])
    out["other_news"] = [n for n in out["other_news"] if n["st"] not in bad]
    if len(out["other_news"]) < n0:
        out["problems"].append(f"ตัดข่าวที่ยืนยันแหล่งไม่ได้ออก {n0 - len(out['other_news'])} ข่าว")
    lu = out["lineups"]
    if lu.get("claimed") and not lu.get("confirmed"):
        out["problems"].append("AI ระบุว่าประกาศตัวจริงแล้ว แต่ยืนยันแหล่งไม่ได้ — ถือว่ายังไม่มีข้อมูล")
        lu["notes"] = None
    if any(out["cup"]["rotation_claimed"].values()) and not out["cup"]["verified"]:
        out["cup"]["evidence"] = None
    return out


def apply_team_news(m, raw, sources=None, queries=None, today=None):
    m["team_news"] = validate_team_news(raw, sources, queries, today, m.get("home"), m.get("away"))
    return m


def team_news_features(m, f):
    """แปลงข้อมูลทีม (เฉพาะค่าที่ยืนยันแล้ว status = ok) เป็น features สำหรับ Rule เงา R42-R46"""
    tn = m.get("team_news") or {}
    fav, dog = f["fav"], f["dog"]
    out = {"tn_has": bool(tn), "tn_xg_total": None, "tn_fav_overperf": None, "tn_fav_starters_out": None,
           "tn_dog_starters_out": None, "tn_fav_gk_out": False, "tn_fav_rest": None, "tn_dog_rest": None,
           "tn_fav_rotation": False, "tn_dog_rotation": False, "tn_lineups": bool((tn.get("lineups") or {}).get("confirmed"))}
    if not tn:
        return out
    xg = tn.get("xg") or {}
    h, a = xg.get("home") or {}, xg.get("away") or {}
    if h.get("status") == "ok" and a.get("status") == "ok":
        out["tn_xg_total"] = round((h["xg"] + a["xga"]) / 2 + (a["xg"] + h["xga"]) / 2, 2)
    fx = xg.get(fav) or {}
    if fx.get("status") == "ok" and fx.get("gf") is not None and fx.get("ga") is not None:
        out["tn_fav_overperf"] = round((fx["gf"] - fx["xg"]) + (fx["xga"] - fx["ga"]), 2)   # + = ผลจริงดีกว่าเนื้อเกม (เสี่ยงกลับสู่ค่าเฉลี่ย)
    chk = tn.get("injuries_checked") or {}
    for side, key in ((fav, "tn_fav_starters_out"), (dog, "tn_dog_starters_out")):
        if chk.get(side):
            lst = [x for x in (tn.get("injuries") or {}).get(side, []) if x.get("st") == "ok" and x.get("status") in ("out", "suspended")]
            out[key] = sum(1 for x in lst if x.get("role") == "starter")
            if side == fav:
                out["tn_fav_gk_out"] = any(x.get("role") == "starter" and x.get("position") == "GK" for x in lst)
    rs = tn.get("rest") or {}
    for side, key in ((fav, "tn_fav_rest"), (dog, "tn_dog_rest")):
        if (rs.get(side) or {}).get("status") == "ok":
            out[key] = rs[side]["days"]
    rot = (tn.get("cup") or {}).get("rotation") or {}
    out["tn_fav_rotation"], out["tn_dog_rotation"] = bool(rot.get(fav)), bool(rot.get(dog))
    return out


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
    sw, sc_ = sanity_checks(m)
    w += sw
    m["critical"] = sc_
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
    venue = bool((m.get("stats") or {}).get("venue"))
    m["stats"] = {k: round(v, 3) for k, v in st.items()}
    if venue:
        m["stats"]["venue"] = True                   # สถิติแยกเหย้า/เยือนจากการค้นหา
    m["h2h"] = [e for e in (m.get("h2h") or []) if _num(e.get("hg")) and _num(e.get("ag"))][:5]
    if not m["h2h"]:
        w.append("ไม่พบข้อมูล H2H ใน 5 รูป (Rule 5 จะไม่ทำงาน)")
    if not m["stats"]:
        w.append("ไม่พบสถิติประตูได้/เสีย (Rule 3, 8 จะไม่ทำงาน)")
    m["context"] = {**{"type": "league"}, **{k: v for k, v in (m.get("context") or {}).items() if v is not None}}
    m["home"], m["away"] = m.get("home") or "Home", m.get("away") or "Away"
    # Home/Away Verification: ยืนยันสิทธิ์เจ้าบ้านของแต่ละนัด H2H จากชื่อทีม (ถ้ามีชื่อ)
    chk = bad = 0
    for e in m["h2h"]:
        ht, at = e.get("home_team"), e.get("away_team")
        if not (ht and at):
            continue
        chk += 1
        if _same_team(ht, m["home"]) or _same_team(at, m["away"]):
            val = True
        elif _same_team(ht, m["away"]) or _same_team(at, m["home"]):
            val = False
        else:
            bad += 1
            w.append(f"H2H {ht} vs {at}: ชื่อทีมไม่ตรงกับ {m['home']}/{m['away']} โปรดตรวจรูป")
            continue
        if e.get("home_is_current_home") is not None and e["home_is_current_home"] != val:
            w.append(f"H2H {ht} vs {at}: แก้ home_is_current_home เป็น {val} ตามชื่อทีม")
        e["home_is_current_home"] = val
    m["h2h_names_checked"], m["h2h_names_bad"] = chk, bad
    m["rank"] = {k: v for k, v in (m.get("rank") or {}).items() if _num(v)}
    if not m["rank"]:
        w.append("ไม่พบอันดับตาราง (Rule 18, 19, 23 จะไม่ทำงาน)")
    m["warnings"] = w
    return m, w


def cmd_images(a):
    key = get_api_key(os.environ.get)
    if not key:
        sys.exit("ต้องตั้งค่า environment variable GEMINI_API_KEY ก่อน (สร้างที่ https://aistudio.google.com/apikey)\n"
                 "  macOS/Linux: export GEMINI_API_KEY=...\n"
                 "  Windows PS : $env:GEMINI_API_KEY='...'")
    if len(a.images) != 5:
        print(f"⚠ ได้รับ {len(a.images)} รูป (ปกติใช้ 5 รูป) จะดำเนินการต่อ")
    print(f"🖼  กำลังอ่าน {len(a.images)} รูปด้วย {a.model} ...")
    m = extract_from_images(a.images, a.model, key)
    if not a.no_research:
        print("🔎 ค้นหาข้อมูลบริบทแมตช์ด้วย Gemini + Google Search ...")
        try:
            r, srcs, qs = research_context(m.get("home"), m.get("away"), m.get("league"), a.model, key)
            apply_research(m, r, srcs, qs)
            for e_ in (m.get("research") or {}).get("evidence", []):
                print(f"   - {e_}")
        except SystemExit as e_:
            print(f"   (ข้ามการค้นหาบริบท: {e_})")
        print("🩺 ค้นข้อมูลทีม (xG/xGA, ตัวเจ็บ, บอลถ้วย, วันพัก) ...")
        try:
            r2, srcs2, qs2 = research_team_news(m.get("home"), m.get("away"), m.get("league"), a.model, key)
            apply_team_news(m, r2, srcs2, qs2)
        except SystemExit as e_:
            print(f"   (ข้ามการค้นข้อมูลทีม: {e_})")
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
    m["id"] = a.match_id or slug(f"{m['home']}-vs-{m['away']}-{now_th('%Y%m%d-%H%M')}")

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
    bst = pk.get("best")
    rec["pick_profit_best"] = round(profit(halves, bst["price"]), 4) if bst else round(pf, 4)
    rec.update(status="settled", score=[hg, ag], pick_r=r, pick_profit=round(pf, 4),
               role_r=role_outcomes(rec, outcomes))
    changes = update_weights(store, rec, outcomes)
    rec["life_changes"] = lifecycle_update(store, rec["features"], outcomes)
    new = discover_rules(store, verbose=False)
    store.state["meta"]["settled"] = store.state["meta"].get("settled", 0) + 1
    rec["settle_seq"] = store.state["meta"]["settled"]
    rec["settled_at"] = now_th("%Y-%m-%d %H:%M")
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


def rebuild_learning(store):
    """คำนวณการเรียนรู้ใหม่ทั้งหมดจากประวัติที่บันทึกผลแล้ว ตามลำดับที่ใส่ผลเดิม
    (รีเซ็ตน้ำหนัก/Rule ที่เรียนรู้ แล้ว replay ทีละนัด โดยให้การค้นหา Rule ใหม่เห็นเฉพาะนัดก่อนหน้า)
    ใช้หลังแก้สกอร์หรือยกเลิกผล เพื่อไม่ให้ข้อมูลการเรียนรู้ผิดตามสกอร์ที่ใส่ผิด คืนจำนวนนัดที่ replay"""
    S = store.state
    frozen = bool(store.params.get("freeze_weights"))
    live = {k: v for k, v in S["weights"].items() if k in DEFAULT_WEIGHTS} if frozen else None
    S["weights"] = dict(live) if frozen else dict(DEFAULT_WEIGHTS)
    if frozen:
        S["shadow_weights"] = dict(DEFAULT_WEIGHTS)
    S["rule_stats"] = {}
    S["learned_rules"] = []
    S["lifecycle"] = {}
    meta = S.setdefault("meta", {})
    meta["next_learned"], meta["settled"] = 1, 0
    order = sorted(((r.get("settle_seq", -1), i, r) for i, r in enumerate(store.history) if r.get("status") == "settled"),
                   key=lambda x: (x[0], x[1]))
    recs = [r for _, _, r in order]
    for r in recs:
        r["status"] = "_replay"                       # ซ่อนไว้ก่อน เพื่อไม่ให้ discover_rules เห็นข้อมูลจากอนาคต
    try:
        for rec in recs:
            rec["status"] = "settled"
            hg, ag = rec["score"]
            outcomes = settle_all(rec, hg, ag)
            pk = rec["pick"]
            r_, halves = outcomes[pk["market"]]
            rec.update(pick_r=r_, pick_profit=round(profit(halves, pk["price_win"]), 4), role_r=role_outcomes(rec, outcomes))
            if pk.get("best"):
                rec["pick_profit_best"] = round(profit(halves, pk["best"]["price"]), 4)
            elif "pick_profit_best" in rec:
                rec["pick_profit_best"] = rec["pick_profit"]
            update_weights(store, rec, outcomes)
            rec["life_changes"] = lifecycle_update(store, rec["features"], outcomes)
            discover_rules(store, verbose=False)
            meta["settled"] += 1
            rec["settle_seq"] = meta["settled"]
    finally:
        for r in recs:
            if r["status"] == "_replay":
                r["status"] = "settled"
    return len(recs)


def _find(store, rid):
    return next((r for r in store.history if r["id"] == rid), None)


def edit_result(store, rid, hg, ag):
    """แก้สกอร์ของรายการที่บันทึกผลแล้ว แล้วคำนวณการเรียนรู้ใหม่ คืนสรุปก่อน/หลัง (ValueError ถ้าไม่พบ/ยังไม่ได้บันทึกผล)"""
    rec = _find(store, rid)
    if rec is None or rec.get("status") != "settled":
        raise ValueError("ไม่พบรายการที่บันทึกผลแล้ว")
    old = {"score": list(rec["score"]), "r": rec["pick_r"], "profit": rec["pick_profit"]}
    old_w, old_rules = dict(store.state[weight_key(store)]), len(store.state["learned_rules"])
    rec["score"] = [int(hg), int(ag)]
    rec["edits"] = rec.get("edits", 0) + 1
    rec["edited_at"] = now_th("%Y-%m-%d %H:%M")
    n = rebuild_learning(store)
    store.save()
    return {"old": old, "new": {"score": rec["score"], "r": rec["pick_r"], "profit": rec["pick_profit"]},
            "replayed": n, "weight_changes": _weight_diff(old_w, store.state[weight_key(store)]),
            "rules_before": old_rules, "rules_after": len(store.state["learned_rules"])}


def revert_result(store, rid):
    """ยกเลิกผลที่บันทึกไว้ (กลับเป็นรอผล) แล้วคำนวณการเรียนรู้ใหม่"""
    rec = _find(store, rid)
    if rec is None or rec.get("status") != "settled":
        raise ValueError("ไม่พบรายการที่บันทึกผลแล้ว")
    old_w, old_rules = dict(store.state[weight_key(store)]), len(store.state["learned_rules"])
    rec["status"] = "pending"
    for k in ("score", "pick_r", "pick_profit", "pick_profit_best", "role_r", "settle_seq", "settled_at", "life_changes"):
        rec.pop(k, None)
    n = rebuild_learning(store)
    store.save()
    return {"replayed": n, "weight_changes": _weight_diff(old_w, store.state[weight_key(store)]),
            "rules_before": old_rules, "rules_after": len(store.state["learned_rules"])}


def _weight_diff(old, new):
    out = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a is None or b is None or abs(a - b) >= 0.005:
            out.append((k, a, b))
    return out


def cmd_edit(a):
    store = Store(a.data_dir)
    mm = re.match(r"^\s*(\d+)\s*[-:]\s*(\d+)\s*$", a.score)
    if not mm:
        sys.exit("รูปแบบสกอร์ไม่ถูกต้อง ใช้เช่น 2-1 (เหย้า-เยือน)")
    try:
        res = edit_result(store, a.id, int(mm.group(1)), int(mm.group(2)))
    except ValueError as e:
        sys.exit(str(e))
    print(f"แก้สกอร์ {a.id}: {res['old']['score'][0]}-{res['old']['score'][1]} -> {res['new']['score'][0]}-{res['new']['score'][1]}")
    print(f"ผลสัญญาณ: {result_word(res['old']['r'])} ({res['old']['profit']:+.2f}) -> {result_word(res['new']['r'])} ({res['new']['profit']:+.2f})")
    print(f"คำนวณการเรียนรู้ใหม่จาก {res['replayed']} นัด | Rule ที่ระบบสร้างเอง {res['rules_before']} -> {res['rules_after']}")


def cmd_revert(a):
    store = Store(a.data_dir)
    try:
        res = revert_result(store, a.id)
    except ValueError as e:
        sys.exit(str(e))
    print(f"ยกเลิกผลของ {a.id} แล้ว (กลับเป็นรอผล) | คำนวณการเรียนรู้ใหม่จาก {res['replayed']} นัด")


def delete_records(store, ids):
    """ลบรายการออกจากประวัติ (pending หรือ settled) คืนจำนวนที่ลบ
    หมายเหตุ: น้ำหนัก Rule ที่เคยปรับจากรายการที่ settle แล้วจะไม่ถูกย้อนกลับ"""
    ids = set(ids)
    before = len(store.history)
    had_settled = any(r["id"] in ids and r["status"] == "settled" for r in store.history)
    store.history = [r for r in store.history if r["id"] not in ids]
    n = before - len(store.history)
    if had_settled:
        discover_rules(store, verbose=False)         # รีเฟรชสถิติ Rule ที่เรียนรู้จากประวัติที่เหลือ
    if n:
        store.save()
    return n


def cmd_delete(a):
    n = delete_records(Store(a.data_dir), a.ids)
    print(f"ลบแล้ว {n} รายการ" if n else "ไม่พบ id ที่ระบุ")


def cmd_backtest(a):
    import backtest as bt
    store = Store(a.data_dir)
    res = bt.run_backtest(store.history, {"disc_min_n": a.min_n} if a.min_n else None, permute=a.perm)
    print(bt.text_summary(res))
    if res.get("perm"):
        pm = res["perm"]
        print(f"permutation ({pm['B']} รอบ): กำไรจากการเรียนรู้ {pm['obs']:+.3f} เทียบค่ากลางเมื่อสุ่ม {pm['null_mean']:+.3f} (±{pm['null_sd']:.3f}) p = {pm['p']:.3f}")
    if a.html:
        with open(a.html, "w", encoding="utf-8") as fh:
            fh.write(bt.report_document(res))
        print("บันทึกรายงาน HTML ที่", a.html)


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
    ap = argparse.ArgumentParser(description="Football Quant V5.9 + Self-Learning Rule Engine")
    ap.add_argument("--data-dir", default="quant_data", help="โฟลเดอร์เก็บ state/history")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("analyze", help="วิเคราะห์แมตช์จากไฟล์ JSON")
    p.add_argument("input")
    p.add_argument("--no-save", action="store_true")
    p.set_defaults(fn=cmd_analyze)
    p = sp.add_parser("images", help="อ่านรูป 5 รูปด้วย Gemini แล้ววิเคราะห์ (ต้องมี GEMINI_API_KEY)")
    p.add_argument("images", nargs="+", help="ไฟล์รูป png/jpg/webp (ปกติ 5 รูป)")
    p.add_argument("--model", default=os.environ.get("QUANT_MODEL", DEFAULT_MODEL))
    p.add_argument("--match-id")
    p.add_argument("--save-json", help="ที่เก็บ JSON ที่สกัดได้")
    p.add_argument("--extract-only", action="store_true", help="สกัดข้อมูลอย่างเดียว ไม่วิเคราะห์")
    p.add_argument("--yes", action="store_true", help="ข้ามการถามยืนยัน")
    p.add_argument("--no-research", action="store_true", help="ไม่ค้นหาบริบทแมตช์อัตโนมัติ")
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
    p = sp.add_parser("backtest", help="ทดสอบย้อนหลัง: ไม่เรียนรู้ vs เรียนรู้ต่อเนื่อง")
    p.add_argument("--perm", type=int, default=60, help="จำนวนรอบสุ่มสลับสกอร์ (0 = ไม่รัน)")
    p.add_argument("--min-n", type=int, default=0, help="จำนวนนัดขั้นต่ำก่อนสร้าง Rule ใหม่ (0 = ค่าตั้งต้น)")
    p.add_argument("--html", help="บันทึกรายงาน HTML ลงไฟล์นี้")
    p.set_defaults(fn=cmd_backtest)
    p = sp.add_parser("edit", help="แก้สกอร์ที่ใส่ผิด แล้วคำนวณการเรียนรู้ใหม่")
    p.add_argument("id")
    p.add_argument("score", help="เหย้า-เยือน เช่น 2-1")
    p.set_defaults(fn=cmd_edit)
    p = sp.add_parser("revert", help="ยกเลิกผลที่บันทึกไว้ (กลับเป็นรอผล)")
    p.add_argument("id")
    p.set_defaults(fn=cmd_revert)
    p = sp.add_parser("delete", help="ลบรายการออกจากประวัติ")
    p.add_argument("ids", nargs="+")
    p.set_defaults(fn=cmd_delete)
    sp.add_parser("learn", help="ค้นหา Rule ใหม่จากประวัติ").set_defaults(fn=cmd_learn)
    sp.add_parser("stats", help="ดูผลงานและน้ำหนัก Rule").set_defaults(fn=cmd_stats)
    sp.add_parser("template", help="พิมพ์ JSON ตัวอย่าง").set_defaults(
        fn=lambda a: print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2)))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
