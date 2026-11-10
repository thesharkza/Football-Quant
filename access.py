# -*- coding: utf-8 -*-
"""สิทธิ์ผู้ใช้ 3 ระดับ (Admin / User / Local) + โควตาการใช้งานรายวัน

- Admin   : อีเมลใน Secrets ADMIN_EMAILS ทำได้ทุกอย่าง
- User    : Admin เชิญ ใช้วิเคราะห์ได้วันละ N ครั้ง (ค่าเริ่มต้น 5) ไม่บันทึกผล
- Local   : Admin เชิญ ใช้วิเคราะห์ได้วันละ N ครั้ง (ค่าเริ่มต้น 1) ไม่บันทึกผล
- ไม่ได้รับเชิญ = เข้าไม่ได้

ข้อมูลเก็บแยกจากข้อมูลการเรียนรู้ (access.json) เพื่อให้การนับโควตาของผู้ใช้ทั่วไป
ไม่เขียนทับน้ำหนัก Rule/ประวัติของ Admin และซิงก์ขึ้นที่เก็บถาวรเดียวกัน (Google Sheets / Gist)
"""
import datetime as _dt
import json
import os
import threading
import time
import urllib.request

import football_quant_v58 as q

ROLES = ("admin", "user", "local")
ROLE_TH = {"admin": "Admin", "user": "User", "local": "Local"}
DEFAULT_LIMITS = {"user": 5, "local": 1}
TZ = _dt.timezone(_dt.timedelta(hours=7))           # เวลาไทย: โควตารีเซ็ตเที่ยงคืน
_LOCK = threading.Lock()
_PULLED = set()
ACCESS_REMOTE = {"ok": None, "error": None}


def today():
    return _dt.datetime.now(TZ).strftime("%Y-%m-%d")


def reset_in():
    """เวลาที่เหลือก่อนโควตารีเซ็ต (ข้อความ)"""
    now = _dt.datetime.now(TZ)
    nxt = (now + _dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    s = int((nxt - now).total_seconds())
    return f"{s // 3600} ชม. {s % 3600 // 60} นาที"


def norm(email):
    return str(email or "").strip().lower()


def admin_emails(getter):
    raw = getter("ADMIN_EMAILS") or ""
    return {norm(x) for x in str(raw).replace(";", ",").split(",") if norm(x)}


# ------------------------------------------------------------------ ที่เก็บถาวร
def _remote_pull():
    be = q.remote_backend()
    try:
        if be == "sheets":
            out = q._sheets_call({"action": "pull_access"})
            ACCESS_REMOTE.update(ok=True, error=None)
            return out.get("access")
        if be == "gist":
            tok, gid = q._gist_cfg()
            g = q._gh("GET", f"https://api.github.com/gists/{gid}", tok)
            fo = (g.get("files") or {}).get("access.json")
            ACCESS_REMOTE.update(ok=True, error=None)
            if not fo:
                return None
            text = fo.get("content")
            if fo.get("truncated") or text is None:
                with urllib.request.urlopen(urllib.request.Request(fo["raw_url"], headers=q._gh_headers(tok)), timeout=30) as r:
                    text = r.read().decode("utf-8")
            return json.loads(text) if text and text.strip() else None
    except Exception as e:  # noqa
        ACCESS_REMOTE.update(ok=False, error=q._remote_err(e) + _hint(e))
    return None


def _remote_push(acc):
    be = q.remote_backend()
    try:
        if be == "sheets":
            q._sheets_call({"action": "push_access", "access": acc})
        elif be == "gist":
            tok, gid = q._gist_cfg()
            q._gh("PATCH", f"https://api.github.com/gists/{gid}", tok,
                  {"files": {"access.json": {"content": json.dumps(acc, ensure_ascii=False)}}})
        else:
            return
        ACCESS_REMOTE.update(ok=True, error=None)
    except Exception as e:  # noqa
        ACCESS_REMOTE.update(ok=False, error=q._remote_err(e) + _hint(e))


def _hint(e):
    return (" — อัปเดตสคริปต์ใน Google Sheets เป็นรุ่นล่าสุด (apps_script/Code.gs) แล้ว Deploy เวอร์ชันใหม่"
            if "unknown action" in str(e) else "")


def _path(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "access.json")


def _blank():
    return {"users": {}, "usage": {}, "limits": dict(DEFAULT_LIMITS), "log": []}


def load(data_dir):
    p = _path(data_dir)
    key = os.path.abspath(p)
    if not os.path.exists(p) and key not in _PULLED and q.remote_backend():
        _PULLED.add(key)
        acc = _remote_pull()
        if isinstance(acc, dict):
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(acc, fh, ensure_ascii=False)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            acc = json.load(fh)
    else:
        acc = _blank()
    for k, v in _blank().items():
        acc.setdefault(k, v)
    for k, v in DEFAULT_LIMITS.items():
        acc["limits"].setdefault(k, v)
    return acc


def _save(data_dir, acc):
    days = sorted(acc["usage"])                       # เก็บประวัติการใช้งาน 14 วันล่าสุด
    for d in days[:-14]:
        acc["usage"].pop(d, None)
    acc["log"] = acc["log"][-300:]
    with open(_path(data_dir), "w", encoding="utf-8") as fh:
        json.dump(acc, fh, ensure_ascii=False)
    _remote_push(acc)


# ------------------------------------------------------------------ สิทธิ์และโควตา
def role_of(email, admins, acc):
    e = norm(email)
    if not e:
        return None
    if e in admins:
        return "admin"
    u = acc["users"].get(e)
    return u["role"] if u and u.get("role") in ("user", "local") else None


def limit_of(role, acc):
    return None if role == "admin" else int(acc["limits"].get(role, DEFAULT_LIMITS.get(role, 0)))


def used_today(email, acc):
    return int((acc["usage"].get(today()) or {}).get(norm(email), 0))


def remaining(email, role, acc):
    lim = limit_of(role, acc)
    return None if lim is None else max(0, lim - used_today(email, acc))


def reserve(data_dir, email, role):
    """จองสิทธิ์ 1 ครั้งแบบอะตอมมิก (กันกดพร้อมกันหลายแท็บ) คืน True ถ้าใช้ได้ · Admin ไม่จำกัด"""
    if role == "admin":
        return True
    with _LOCK:
        acc = load(data_dir)
        if remaining(email, role, acc) <= 0:
            return False
        day = acc["usage"].setdefault(today(), {})
        day[norm(email)] = day.get(norm(email), 0) + 1
        _save(data_dir, acc)
        return True


def refund(data_dir, email, role):
    """คืนสิทธิ์เมื่อการวิเคราะห์ล้มเหลว (ไม่นับครั้งที่ error)"""
    if role == "admin":
        return
    with _LOCK:
        acc = load(data_dir)
        day = acc["usage"].setdefault(today(), {})
        if day.get(norm(email), 0) > 0:
            day[norm(email)] -= 1
            _save(data_dir, acc)


def invite(data_dir, email, role, by):
    e = norm(email)
    if "@" not in e or role not in ("user", "local"):
        raise ValueError("อีเมลหรือระดับไม่ถูกต้อง")
    with _LOCK:
        acc = load(data_dir)
        old = acc["users"].get(e)
        acc["users"][e] = {"role": role, "added": (old or {}).get("added") or time.strftime("%Y-%m-%d %H:%M"), "by": norm(by)}
        acc["log"].append([time.strftime("%Y-%m-%d %H:%M"), norm(by), "invite" if not old else "role", e, role])
        _save(data_dir, acc)


def remove(data_dir, email, by):
    e = norm(email)
    with _LOCK:
        acc = load(data_dir)
        if acc["users"].pop(e, None) is not None:
            acc["log"].append([time.strftime("%Y-%m-%d %H:%M"), norm(by), "remove", e, ""])
            _save(data_dir, acc)


def set_limits(data_dir, user_n, local_n, by):
    with _LOCK:
        acc = load(data_dir)
        acc["limits"] = {"user": max(0, int(user_n)), "local": max(0, int(local_n))}
        acc["log"].append([time.strftime("%Y-%m-%d %H:%M"), norm(by), "limits", "", f"user={user_n} local={local_n}"])
        _save(data_dir, acc)


def reset_usage(data_dir, email, by):
    with _LOCK:
        acc = load(data_dir)
        (acc["usage"].get(today()) or {}).pop(norm(email), None)
        acc["log"].append([time.strftime("%Y-%m-%d %H:%M"), norm(by), "reset", norm(email), ""])
        _save(data_dir, acc)
