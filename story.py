# -*- coding: utf-8 -*-
"""ระบบแสดงผลแบบ "เล่าเรื่องทีละขั้น" (visual story) สำหรับทุกหน้าของแอป

- ทุกหน้าสร้างเป็น HTML ล้วนจาก Python (ข้อความจากภายนอก/AI ผ่าน html.escape เสมอ)
- พฤติกรรม (เผยทีละบทเมื่อเลื่อนถึง, ตัวเลขนับขึ้น, กราฟแตะดูค่า, เปิด/ปิด, แท็บ, เมนูบท) อยู่ใน RUNTIME_JS ชุดเดียว
- ในแอป: mount() แสดงผ่าน st.components.v2 (อยู่ในหน้าเดียวกัน ไม่ใช้ iframe สูงอัตโนมัติ)
- ไฟล์ดาวน์โหลด: document() รวม CSS + JS เป็นไฟล์ HTML เดียวที่เปิดได้ทุกเครื่อง
- ถ้า JavaScript ไม่ทำงาน เนื้อหาทั้งหมดยังแสดงครบ (แค่ไม่มีแอนิเมชัน)
"""
import html as _html
import json
import math

# ============================================================================ CSS
RUNTIME_CSS = r"""
:host { display:block; }
.s-root { --bg:#0b1220; --panel:rgba(255,255,255,.045); --panel2:rgba(255,255,255,.075); --line:rgba(255,255,255,.09);
  --txt:#e6edf7; --mut:#8fa3c0; --acc:#14b8a6; --acc2:#6366f1; --up:#34d399; --down:#f87171; --warn:#fbbf24;
  font-family:-apple-system,BlinkMacSystemFont,'Sukhumvit Set','Thonburi','Noto Sans Thai','Segoe UI',Tahoma,sans-serif;
  color:var(--txt); font-variant-numeric:tabular-nums; line-height:1.55; font-size:15px; position:relative; }
.s-root * { box-sizing:border-box; }
.s-root a { color:#5eead4; text-decoration:none; } .s-root a:hover { text-decoration:underline; }
.s-mut { color:var(--mut); } .s-up { color:var(--up); } .s-down { color:var(--down); } .s-warn { color:var(--warn); }
.s-sm { font-size:.8rem; } .s-xs { font-size:.72rem; } .s-b { font-weight:700; }

/* ---------- เผยทีละส่วน ---------- */
.s-js .s-rv { opacity:0; transform:translateY(22px); transition:opacity .7s ease var(--dl,0s), transform .8s cubic-bezier(.2,.7,.2,1) var(--dl,0s); }
.s-js .s-rv.in { opacity:1; transform:none; }
.s-fill { display:block; height:100%; width:var(--w); border-radius:inherit; transition:width 1.1s cubic-bezier(.2,.7,.2,1) calc(var(--dl,0s) + .15s); }
.s-js .s-rv:not(.in) .s-fill { width:0 !important; }
.s-vfill { position:absolute; left:15%; right:15%; border-radius:3px; height:var(--h); transition:height .9s cubic-bezier(.2,.7,.2,1) calc(var(--dl,0s) + .1s); }
.s-js .s-rv:not(.in) .s-vfill { height:0 !important; }
.s-draw { stroke-dasharray:var(--len); stroke-dashoffset:0; transition:stroke-dashoffset 1.8s cubic-bezier(.3,.6,.2,1) .2s; }
.s-js .s-rv:not(.in) .s-draw { stroke-dashoffset:var(--len); }
.s-ring { transition:stroke-dashoffset 1.3s cubic-bezier(.2,.7,.2,1) .2s; stroke-dashoffset:var(--o); }
.s-js .s-rv:not(.in) .s-ring { stroke-dashoffset:100; }
.s-pop { transition:transform .45s cubic-bezier(.3,1.6,.5,1) var(--dl,0s), opacity .3s ease var(--dl,0s); }
.s-js .s-rv:not(.in) .s-pop { transform:scale(.3); opacity:0; }
@media (prefers-reduced-motion: reduce) { .s-root * { transition:none !important; animation:none !important; } }

/* ---------- เมนูบท ---------- */
.s-nav { position:sticky; top:0; z-index:6; display:flex; gap:6px; overflow-x:auto; padding:10px 2px 12px; margin:0 0 6px;
  background:linear-gradient(180deg, #0b1220 82%, rgba(11,18,32,0)); scrollbar-width:none; }
.s-nav::-webkit-scrollbar { display:none; }
.s-nav a { flex:none; display:flex; align-items:center; gap:6px; font-size:.75rem; padding:5px 12px 5px 6px; border-radius:99px;
  border:1px solid var(--line); color:var(--mut); cursor:pointer; white-space:nowrap; background:rgba(255,255,255,.03); text-decoration:none !important; }
.s-nav a i { font-style:normal; width:19px; height:19px; border-radius:50%; display:grid; place-items:center; font-size:.66rem; font-weight:700;
  background:rgba(255,255,255,.08); color:var(--mut); }
.s-nav a.on { background:rgba(20,184,166,.16); color:#99f6e4; border-color:rgba(94,234,212,.45); }
.s-nav a.on i { background:var(--acc); color:#04201d; }
.s-nav a.seen i { background:rgba(20,184,166,.35); color:#e6fffb; }

/* ---------- บท ---------- */
.s-ch { position:relative; padding:6px 0 30px 48px; scroll-margin-top:64px; }
.s-ch::before { content:""; position:absolute; left:16px; top:42px; bottom:4px; width:2px; border-radius:2px;
  background:linear-gradient(180deg, rgba(94,234,212,.45), rgba(99,102,241,.2) 60%, transparent); }
.s-ch:last-child::before { display:none; }
.s-node { position:absolute; left:0; top:4px; width:34px; height:34px; border-radius:50%; display:grid; place-items:center;
  font-weight:800; font-size:.84rem; background:#0f1a2e; border:2px solid rgba(94,234,212,.55); color:#5eead4;
  box-shadow:0 0 0 5px rgba(20,184,166,.08); }
.s-kick { font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:#5eead4; font-weight:700; }
.s-ch h2 { margin:1px 0 6px; font-size:1.32rem; font-weight:800; letter-spacing:-.01em; line-height:1.25; }
.s-lead { color:#c6d3e7; font-size:.97rem; margin:0 0 16px; max-width:68ch; }
.s-lead b { color:#fff; font-weight:700; }

/* ---------- การ์ด/กริด ---------- */
.s-grid { display:grid; gap:12px; grid-template-columns:repeat(auto-fit, minmax(min(270px,100%), 1fr)); }
.s-grid2 { display:grid; gap:12px; grid-template-columns:1fr 1fr; }
.s-card { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:15px 17px; min-width:0; }
.s-card + .s-card { margin-top:12px; } .s-grid > .s-card + .s-card, .s-grid2 > .s-card + .s-card { margin-top:0; }
.s-h { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:6px 8px; font-size:.7rem; letter-spacing:.09em;
  text-transform:uppercase; color:var(--mut); font-weight:700; margin-bottom:10px; }
.s-big { font-size:2rem; font-weight:800; line-height:1.1; letter-spacing:-.02em; }
.s-mid { font-size:1.3rem; font-weight:800; line-height:1.15; }
.s-chip { display:inline-flex; align-items:center; gap:4px; font-size:.74rem; padding:2px 10px; border-radius:99px; white-space:nowrap;
  background:rgba(99,102,241,.16); color:#c7d2fe; border:1px solid rgba(165,180,252,.25); }
.s-chip.ok { background:rgba(52,211,153,.14); color:#6ee7b7; border-color:rgba(110,231,183,.3); }
.s-chip.bad { background:rgba(248,113,113,.14); color:#fca5a5; border-color:rgba(252,165,165,.3); }
.s-chip.warn { background:rgba(251,191,36,.12); color:#fde68a; border-color:rgba(253,224,71,.3); }
.s-chip.off { background:rgba(255,255,255,.05); color:var(--mut); border-color:var(--line); }
.s-chip.acc { background:rgba(20,184,166,.16); color:#5eead4; border-color:rgba(94,234,212,.3); }
.s-chips { display:flex; flex-wrap:wrap; gap:6px; }
.s-list { margin:6px 0 0; padding-left:18px; color:#c0cde2; font-size:.88rem; }
.s-list li { margin:3px 0; }
.s-empty { padding:26px; text-align:center; color:var(--mut); border:1px dashed var(--line); border-radius:16px; }
.s-note { font-size:.78rem; color:var(--mut); margin-top:10px; }
.s-kv { display:flex; justify-content:space-between; gap:10px; padding:7px 0; border-bottom:1px solid var(--line); font-size:.88rem; }
.s-kv:last-child { border-bottom:none; } .s-kv > span:first-child { color:#a9b8cf; } .s-kv > b { text-align:right; }

/* ---------- แถบ ---------- */
.s-bar { height:10px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; position:relative; }
.s-bar.thin { height:6px; } .s-bar.fat { height:16px; }
.s-fill.t { background:linear-gradient(90deg,#14b8a6,#22d3ee); } .s-fill.i { background:linear-gradient(90deg,#6366f1,#a78bfa); }
.s-fill.g { background:#34d399; } .s-fill.r { background:#f87171; } .s-fill.y { background:#fbbf24; } .s-fill.n { background:#64748b; }
.s-fill.o { background:rgba(255,255,255,.28); }
.s-bar .s-mark { position:absolute; top:-3px; bottom:-3px; width:2px; background:rgba(255,255,255,.75); border-radius:2px; }
.s-brow { display:grid; grid-template-columns:minmax(0,1.3fr) 2fr auto; gap:10px; align-items:center; margin:9px 0; font-size:.86rem; }
.s-brow .n { font-weight:700; text-align:right; white-space:nowrap; }
.s-brow .l { overflow-wrap:anywhere; line-height:1.3; }

/* ---------- ฉากเปิด ---------- */
.s-hero { position:relative; overflow:hidden; border-radius:26px; padding:22px 22px 20px; margin-bottom:26px;
  background:radial-gradient(600px 260px at 0% 0%, rgba(20,184,166,.22), transparent 60%),
             radial-gradient(520px 260px at 100% 0%, rgba(99,102,241,.22), transparent 60%), #0e1829;
  border:1px solid rgba(255,255,255,.1); box-shadow:0 30px 70px rgba(0,0,0,.35); }
.s-hero .comp { text-align:center; font-size:.76rem; color:var(--mut); letter-spacing:.06em; margin-bottom:12px; }
.s-vs { display:grid; grid-template-columns:1fr auto 1fr; gap:10px; align-items:start; text-align:center; }
.s-team .nm { font-size:1.35rem; font-weight:800; line-height:1.2; margin:6px 0 4px; overflow-wrap:anywhere; }
.s-team .sub { font-size:.74rem; color:var(--mut); }
.s-vsx { align-self:center; font-weight:900; font-size:.95rem; color:#64748b; padding-top:18px; letter-spacing:.1em; }
.s-pick { position:relative; overflow:hidden; margin-top:18px; border-radius:20px; padding:18px 20px;
  background:linear-gradient(135deg,#0f766e 0%,#14b8a6 58%,#22d3ee 135%); color:#04201d; box-shadow:0 20px 50px rgba(20,184,166,.28); }
.s-pick.low { background:linear-gradient(135deg,#334155,#4b5873 60%,#64739a 140%); color:#eef2fb; box-shadow:0 20px 50px rgba(51,65,85,.35); }
.s-pick.skip { background:repeating-linear-gradient(135deg,#2a3346 0 14px,#2f3a50 14px 28px); color:#eef2fb; border:1px dashed rgba(255,255,255,.25); box-shadow:none; }
.s-pick::after { content:""; position:absolute; inset:-40% -10% auto auto; width:220px; height:220px; border-radius:50%;
  background:radial-gradient(circle, rgba(255,255,255,.35), transparent 65%); pointer-events:none; }
.s-pick .k { font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; opacity:.8; }
.s-pick .lb { font-size:1.85rem; font-weight:900; line-height:1.15; margin:6px 0 10px; letter-spacing:-.01em; }
.s-pick .row { display:flex; flex-wrap:wrap; align-items:flex-end; gap:22px; }
.s-pick .s-chip { background:rgba(4,32,29,.16); color:inherit; border-color:rgba(4,32,29,.2); }
.s-pick.low .s-chip, .s-pick.skip .s-chip { background:rgba(255,255,255,.12); border-color:rgba(255,255,255,.18); }
.s-pick .best { margin-top:12px; padding:9px 12px; border-radius:12px; background:rgba(255,255,255,.22); font-size:.85rem; }
.s-pick.low .best, .s-pick.skip .best { background:rgba(255,255,255,.1); }
.s-lvl { display:flex; align-items:flex-end; gap:5px; height:40px; }
.s-lvl i { display:block; width:13px; border-radius:4px; background:rgba(4,32,29,.22); transform-origin:bottom; }
.s-lvl i.on { background:#04201d; }
.s-pick.low .s-lvl i, .s-pick.skip .s-lvl i { background:rgba(255,255,255,.18); } .s-pick.low .s-lvl i.on, .s-pick.skip .s-lvl i.on { background:#fff; }
.s-js .s-rv:not(.in) .s-lvl i { transform:scaleY(.05); }
.s-lvl i { transition:transform .6s cubic-bezier(.3,1.5,.5,1) var(--dl,0s); }
.s-statline { display:flex; flex-direction:column; } .s-statline .v { font-size:1.6rem; font-weight:900; line-height:1; }
.s-statline .t { font-size:.7rem; font-weight:700; letter-spacing:.08em; opacity:.75; text-transform:uppercase; margin-top:4px; }

/* ---------- ฟอร์ม ---------- */
.s-dots { display:flex; gap:4px; justify-content:center; flex-wrap:wrap; margin:6px 0; }
.s-dot { width:24px; height:24px; border-radius:50%; display:grid; place-items:center; font-size:.68rem; font-weight:800; color:#0b1220; }
.s-dot.w { background:#34d399; } .s-dot.d { background:#fbbf24; } .s-dot.l { background:#f87171; }
.s-score { display:inline-flex; align-items:center; justify-content:center; min-width:52px; padding:5px 10px; border-radius:10px;
  font-weight:800; font-size:.86rem; border:1px solid var(--line); }
.s-score.w { color:#6ee7b7; background:rgba(52,211,153,.1); } .s-score.d { color:#fde68a; background:rgba(251,191,36,.1); }
.s-score.l { color:#fca5a5; background:rgba(248,113,113,.1); }

/* ---------- ราคา ---------- */
.s-line { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.s-line .b { padding:6px 12px; border-radius:12px; background:rgba(255,255,255,.06); border:1px solid var(--line); text-align:center; min-width:72px; }
.s-line .b.cur { background:rgba(20,184,166,.16); border-color:rgba(94,234,212,.45); }
.s-line .b .t { font-size:.66rem; color:var(--mut); letter-spacing:.06em; } .s-line .b .v { font-size:1.25rem; font-weight:800; }
.s-flow { position:relative; width:46px; height:2px; background:rgba(255,255,255,.18); border-radius:2px; overflow:hidden; }
.s-flow::after { content:""; position:absolute; top:0; left:-40%; width:40%; height:100%; background:var(--fc,#5eead4); animation:sflow 1.6s linear infinite; }
@keyframes sflow { to { left:100%; } }
.s-prob { display:grid; grid-template-columns:76px 1fr 64px; gap:10px; align-items:center; margin:10px 0; font-size:.86rem; }
.s-prob .stk { display:flex; flex-direction:column; gap:4px; }
.s-prob .v { text-align:right; font-weight:800; }

/* ---------- ดึงเชือก ---------- */
.s-tug { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.3fr) minmax(0,1.3fr) minmax(0,1fr); gap:8px; align-items:center; margin:12px 0; }
.s-tug .sd { min-width:0; line-height:1.25; } .s-tug .sd.r { text-align:right; }
.s-tug .sd .nm { display:block; font-size:.74rem; color:var(--mut); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.s-tug .sd b { font-size:1.15rem; font-weight:800; } .s-tug .sd.win b { color:#5eead4; }
.s-tug .half { height:18px; background:rgba(255,255,255,.06); display:flex; overflow:hidden; }
.s-tug .half.l { justify-content:flex-end; border-radius:9px 0 0 9px; } .s-tug .half.r { border-radius:0 9px 9px 0; }
.s-tug .half .s-fill { background:#475569; }
.s-tug .half.win .s-fill { background:linear-gradient(90deg,#14b8a6,#22d3ee); } .s-tug .half.l.win .s-fill { background:linear-gradient(270deg,#14b8a6,#22d3ee); }
.s-tug .half.ban .s-fill { background:repeating-linear-gradient(45deg,#475569 0 4px,#334155 4px 8px); opacity:.6; }
.s-tug .tg { font-size:.66rem; color:var(--down); font-weight:700; margin-left:4px; }

/* ---------- Rule ---------- */
.s-rule { display:grid; grid-template-columns:4px minmax(0,1fr) 92px; gap:12px; align-items:center; padding:10px 0; border-bottom:1px solid var(--line); }
.s-rule:last-child { border-bottom:none; }
.s-rule .edge { align-self:stretch; border-radius:4px; background:#475569; }
.s-rule.sup .edge { background:linear-gradient(#14b8a6,#22d3ee); } .s-rule.opp .edge { background:#f87171; }
.s-rule .nm { font-weight:700; font-size:.88rem; line-height:1.3; } .s-rule .nm small { color:var(--mut); font-weight:500; margin-left:4px; }
.s-rule .nt { color:#a9b8cf; font-size:.8rem; line-height:1.4; margin-top:2px; }
.s-rule .sc { text-align:right; } .s-rule .sc b { font-size:1rem; } .s-rule .sc .s-bar { margin-top:5px; }
.s-more { display:none; } .s-more.open { display:block; }
.s-btn { display:inline-flex; align-items:center; gap:6px; margin-top:10px; padding:6px 14px; border-radius:99px; font-size:.78rem; cursor:pointer;
  border:1px solid rgba(94,234,212,.35); color:#99f6e4; background:rgba(20,184,166,.08); font-family:inherit; }
.s-btn:hover { background:rgba(20,184,166,.16); }

/* ---------- แท็บ ---------- */
.s-tabs .s-tabbar { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; }
.s-tabs .s-tabbar button { font-family:inherit; font-size:.78rem; padding:6px 13px; border-radius:99px; cursor:pointer;
  border:1px solid var(--line); background:rgba(255,255,255,.03); color:var(--mut); }
.s-tabs .s-tabbar button.on { background:rgba(99,102,241,.2); color:#e0e7ff; border-color:rgba(165,180,252,.45); }
.s-js .s-tabs [data-tabpane]:not(.on) { display:none; }

/* ---------- กราฟ ---------- */
.s-chart { position:relative; } .s-chart svg { display:block; width:100%; height:auto; touch-action:pan-y; }
.s-chart .s-guide { stroke:rgba(255,255,255,.4); stroke-width:1; opacity:0; }
.s-chart .s-hdot { opacity:0; }
.s-legend { display:flex; flex-wrap:wrap; gap:14px; font-size:.78rem; color:var(--mut); margin-bottom:8px; }
.s-legend i { display:inline-block; width:18px; height:3px; border-radius:3px; margin-right:6px; vertical-align:middle; }
.s-vbars { display:flex; align-items:stretch; gap:3px; height:130px; }
.s-vbars > div { flex:1; position:relative; min-width:2px; max-width:30px; cursor:default; }
.s-vbars .mid { position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(255,255,255,.18); }
.s-vbars .s-vfill.p { bottom:50%; background:#34d399; } .s-vbars .s-vfill.n { top:50%; background:#f87171; }
.s-vbars .s-vfill.z { top:calc(50% - 1px); height:2px !important; background:#64748b; }
.s-ringw { display:flex; align-items:center; gap:16px; }
.s-ringw svg { width:96px; height:96px; flex:none; transform:rotate(-90deg); }
.s-ringw .bg { stroke:rgba(255,255,255,.1); } .s-ringw .s-ring { stroke-linecap:round; }

/* ---------- KPI ---------- */
.s-kpis { display:grid; gap:12px; grid-template-columns:repeat(auto-fit, minmax(min(170px,46%),1fr)); }
.s-kpi { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:14px 16px; }
.s-kpi .t { font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; color:var(--mut); font-weight:700; }
.s-kpi .v { font-size:1.75rem; font-weight:900; line-height:1.15; margin:4px 0 2px; }
.s-kpi .d { font-size:.78rem; color:var(--mut); }
.s-kpi.wide { grid-column:span 2; }
.s-ringw svg { width:84px; height:84px; }

/* ---------- การ์ดเลือกได้ / ไทม์ไลน์ ---------- */
.s-pickgrid { display:grid; gap:10px; grid-template-columns:repeat(auto-fill, minmax(min(250px,100%),1fr)); }
.s-sel { text-align:left; font-family:inherit; color:inherit; cursor:pointer; border-radius:16px; padding:13px 15px;
  background:var(--panel); border:1px solid var(--line); transition:transform .15s ease, border-color .15s ease, background .15s; }
.s-sel:hover { transform:translateY(-2px); border-color:rgba(94,234,212,.4); }
.s-sel.on { border-color:#14b8a6; background:rgba(20,184,166,.12); box-shadow:0 0 0 3px rgba(20,184,166,.18); }
.s-sel .tm { font-weight:800; font-size:.95rem; line-height:1.3; } .s-sel .pk { font-size:.82rem; color:#a9b8cf; margin:4px 0 8px; }
.s-tl { position:relative; padding-left:18px; }
.s-tl::before { content:""; position:absolute; left:5px; top:6px; bottom:6px; width:2px; background:var(--line); }
.s-tl .it { position:relative; padding:7px 0 7px 8px; display:flex; justify-content:space-between; gap:10px; font-size:.86rem; }
.s-tl .it::before { content:""; position:absolute; left:-17px; top:13px; width:10px; height:10px; border-radius:50%; background:#475569; border:2px solid #0b1220; }
.s-tl .it.w::before { background:#34d399; } .s-tl .it.l::before { background:#f87171; } .s-tl .it.p::before { background:#fbbf24; }
.s-tl .it small { display:block; color:var(--mut); font-size:.76rem; }

/* ---------- ผลออก ---------- */
.s-result { border-radius:24px; padding:22px; text-align:center; position:relative; overflow:hidden; margin-bottom:22px; }
.s-result.w { background:radial-gradient(500px 200px at 50% 0%, rgba(52,211,153,.3), transparent 70%), #0f1f1a; border:1px solid rgba(110,231,183,.4); }
.s-result.l { background:radial-gradient(500px 200px at 50% 0%, rgba(248,113,113,.28), transparent 70%), #1f1216; border:1px solid rgba(252,165,165,.35); }
.s-result.p { background:radial-gradient(500px 200px at 50% 0%, rgba(251,191,36,.22), transparent 70%), #1f1b10; border:1px solid rgba(253,224,71,.3); }
.s-result .sc { font-size:2.6rem; font-weight:900; letter-spacing:.04em; margin:6px 0; }
.s-result .vd { font-size:1.4rem; font-weight:900; }

/* ---------- tooltip ---------- */
.s-tipbox { position:fixed; z-index:50; display:none; max-width:280px; padding:8px 11px; border-radius:10px; pointer-events:none;
  background:#0f172a; border:1px solid rgba(148,163,184,.35); color:#e2e8f0; font-size:.78rem; line-height:1.45;
  white-space:pre-line; box-shadow:0 12px 30px rgba(0,0,0,.45); }
[data-tip] { cursor:help; }

@media (max-width: 640px) {
  .s-root { font-size:14px; }
  .s-brow { grid-template-columns:minmax(0,1fr) 1.2fr auto; gap:8px; }
  .s-ch { padding-left:38px; } .s-node { width:28px; height:28px; font-size:.74rem; } .s-ch::before { left:13px; top:36px; }
  .s-ch h2 { font-size:1.16rem; } .s-hero { padding:18px 14px; border-radius:20px; }
  .s-team .nm { font-size:1.08rem; } .s-pick .lb { font-size:1.45rem; } .s-big { font-size:1.6rem; }
  .s-grid2 { grid-template-columns:1fr; }
  .s-tug { grid-template-columns:70px 1fr 1fr 70px; gap:5px; } .s-tug .sd b { font-size:.98rem; }
  .s-rule { grid-template-columns:4px minmax(0,1fr) 74px; gap:9px; }
  .s-prob { grid-template-columns:60px 1fr 52px; }
}
"""

# ============================================================================ JS
RUNTIME_JS = r"""
function fqStory(wrap, api) {
  const root = wrap.querySelector('.s-root');
  if (!root) return function () {};
  root.classList.add('s-js');
  const reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const offs = [];

  // ---- tooltip
  let tip = root.querySelector(':scope > .s-tipbox');
  if (!tip) { tip = document.createElement('div'); tip.className = 's-tipbox'; root.appendChild(tip); }
  const showTip = (text, x, y) => {
    tip.textContent = text; tip.style.display = 'block';
    const w = tip.offsetWidth, h = tip.offsetHeight;
    const L = Math.min(Math.max(8, x - w / 2), window.innerWidth - w - 8);
    let T = y - h - 12; if (T < 8) T = y + 22;
    tip.style.left = L + 'px'; tip.style.top = T + 'px';
  };
  const hideTip = () => { tip.style.display = 'none'; };
  root.addEventListener('pointerover', (ev) => {
    const t = ev.target.closest && ev.target.closest('[data-tip]');
    if (t && root.contains(t)) { const r = t.getBoundingClientRect(); showTip(t.getAttribute('data-tip'), r.left + r.width / 2, r.top); }
  });
  root.addEventListener('pointerout', (ev) => { if (ev.target.closest && ev.target.closest('[data-tip]')) hideTip(); });
  const onScroll = () => hideTip();
  window.addEventListener('scroll', onScroll, true); offs.push(() => window.removeEventListener('scroll', onScroll, true));

  // ---- ตัวเลขนับขึ้น
  const count = (el) => {
    if (el.__done) return; el.__done = 1;
    const to = parseFloat(el.getAttribute('data-n')); if (!isFinite(to)) return;
    const d = parseInt(el.getAttribute('data-d') || '0', 10), pre = el.getAttribute('data-pre') || '',
          suf = el.getAttribute('data-suf') || '', sg = el.getAttribute('data-sg') === '1';
    const fmt = (v) => pre + (sg && v > 0 ? '+' : '') + v.toFixed(d) + suf;
    if (reduce) { el.textContent = fmt(to); return; }
    const t0 = performance.now(), dur = 1000;
    const step = (t) => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(to * e); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  };
  const show = (el) => { el.classList.add('in'); el.querySelectorAll('[data-n]').forEach(count); };

  // ---- เผยเมื่อเลื่อนถึง
  const rvs = Array.prototype.slice.call(root.querySelectorAll('.s-rv'));
  if (reduce || !('IntersectionObserver' in window)) { rvs.forEach(show); }
  else {
    const io = new IntersectionObserver((es) => es.forEach((en) => { if (en.isIntersecting) { show(en.target); io.unobserve(en.target); } }),
                                        { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
    rvs.forEach((el) => io.observe(el)); offs.push(() => io.disconnect());
    const all = () => rvs.forEach(show);
    window.addEventListener('beforeprint', all); offs.push(() => window.removeEventListener('beforeprint', all));
  }

  // ---- เมนูบท
  const nav = root.querySelector('.s-nav');
  if (nav) {
    const links = Array.prototype.slice.call(nav.querySelectorAll('a[data-go]'));
    nav.addEventListener('click', (ev) => {
      const a = ev.target.closest('a[data-go]'); if (!a) return; ev.preventDefault();
      const ch = root.querySelector('#' + a.getAttribute('data-go'));
      if (ch) ch.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
    if ('IntersectionObserver' in window) {
      const chs = links.map((a) => root.querySelector('#' + a.getAttribute('data-go'))).filter(Boolean);
      const io2 = new IntersectionObserver((es) => es.forEach((en) => {
        if (!en.isIntersecting) return;
        const id = en.target.id; let hit = false;
        links.forEach((a) => { const on = a.getAttribute('data-go') === id; a.classList.toggle('on', on); if (on) hit = true; });
        let past = true; links.forEach((a) => { if (a.classList.contains('on')) past = false; a.classList.toggle('seen', past); });
        const cur = links.find((a) => a.classList.contains('on'));
        if (hit && cur && nav.scrollTo) nav.scrollTo({ left: cur.offsetLeft - 20, behavior: reduce ? 'auto' : 'smooth' });
      }), { rootMargin: '-35% 0px -60% 0px' });
      chs.forEach((c) => io2.observe(c)); offs.push(() => io2.disconnect());
    }
  }

  // ---- เปิด/ปิด, แท็บ, การกระทำ
  root.addEventListener('click', (ev) => {
    const tg = ev.target.closest('[data-tg]');
    if (tg && root.contains(tg)) {
      const p = root.querySelector('[data-pane="' + tg.getAttribute('data-tg') + '"]');
      if (p) { const o = p.classList.toggle('open'); tg.setAttribute('aria-expanded', o ? 'true' : 'false');
               const a = tg.getAttribute('data-alt'); if (a) { tg.setAttribute('data-alt', tg.textContent); tg.textContent = a; }
               if (o) p.querySelectorAll('.s-rv').forEach(show); }
      return;
    }
    const tb = ev.target.closest('[data-tab]');
    if (tb && root.contains(tb)) {
      const box = tb.closest('.s-tabs'), k = tb.getAttribute('data-tab');
      box.querySelectorAll('[data-tab]').forEach((b) => b.classList.toggle('on', b === tb));
      box.querySelectorAll('[data-tabpane]').forEach((p) => { const on = p.getAttribute('data-tabpane') === k; p.classList.toggle('on', on); if (on) p.querySelectorAll('.s-rv').forEach(show); });
      return;
    }
    const ac = ev.target.closest('[data-act]');
    if (ac && root.contains(ac) && wrap.__api && wrap.__api.setTriggerValue) {
      root.querySelectorAll('[data-act]').forEach((b) => b.classList.toggle('on', b === ac));
      wrap.__api.setTriggerValue('act', ac.getAttribute('data-act'));
    }
  });

  // ---- กราฟเส้นแตะดูค่า
  root.querySelectorAll('.s-chart[data-chart]').forEach((ch) => {
    let D; try { D = JSON.parse(ch.getAttribute('data-chart')); } catch (e) { return; }
    const svg = ch.querySelector('svg'), guide = svg.querySelector('.s-guide');
    const dots = Array.prototype.slice.call(svg.querySelectorAll('.s-hdot'));
    const move = (ev) => {
      const r = svg.getBoundingClientRect(); if (!r.width) return;
      const vx = (ev.clientX - r.left) / r.width * D.W;
      let i = 0, best = 1e9; D.x.forEach((x, k) => { const dd = Math.abs(x - vx); if (dd < best) { best = dd; i = k; } });
      guide.setAttribute('x1', D.x[i]); guide.setAttribute('x2', D.x[i]); guide.style.opacity = 1;
      dots.forEach((dt, s) => { dt.setAttribute('cx', D.x[i]); dt.setAttribute('cy', D.y[s][i]); dt.style.opacity = 1; });
      const lines = [D.lab[i]].concat(D.s.map((nm, k) => nm + ': ' + D.v[k][i]));
      const ymin = Math.min.apply(null, D.y.map((a) => a[i]));
      showTip(lines.join('\n'), r.left + D.x[i] / D.W * r.width, r.top + ymin / D.H * r.height);
    };
    const leave = () => { guide.style.opacity = 0; dots.forEach((dt) => { dt.style.opacity = 0; }); hideTip(); };
    svg.addEventListener('pointermove', move); svg.addEventListener('pointerdown', move); svg.addEventListener('pointerleave', leave);
  });

  return function () { offs.forEach((f) => { try { f(); } catch (e) {} }); };
}
"""

COMPONENT_JS = RUNTIME_JS + r"""
export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let wrap = parentElement.querySelector('.s-mount');
  if (!wrap) { wrap = document.createElement('div'); wrap.className = 's-mount'; parentElement.appendChild(wrap); }
  wrap.__api = { setTriggerValue: setTriggerValue };
  const html = (data && data.html) || '';
  if (wrap.__html === html) return;
  wrap.__html = html;
  if (wrap.__off) { try { wrap.__off(); } catch (e) {} }
  wrap.innerHTML = html;
  wrap.__off = fqStory(wrap, wrap.__api);
}
"""

_COMP = None


def mount(html_str, key, on_act=False):
    """แสดงหน้าเรื่องเล่าในแอป Streamlit คืนค่าที่ผู้ใช้กดจากการ์ด data-act (หรือ None)"""
    import streamlit as st
    global _COMP
    if _COMP is None:
        _COMP = st.components.v2.component("fq_story", css=RUNTIME_CSS, js=COMPONENT_JS)
    kw = {"on_act_change": (lambda: None)} if on_act else {}
    res = _COMP(data={"html": html_str}, key=key, **kw)
    if on_act:
        try:
            return getattr(res, "act", None)
        except Exception:  # noqa
            return None
    return None


def document(title, body_html, subtitle=""):
    """ไฟล์ HTML เดี่ยวสำหรับดาวน์โหลด (มีแอนิเมชันและกราฟโต้ตอบครบ)"""
    return ('<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><style>html,body{{margin:0;background:#0b1220}}'
            '.wrap{max-width:980px;margin:0 auto;padding:18px 16px 40px}'
            '.doc-h{color:#e6edf7;font-family:-apple-system,BlinkMacSystemFont,"Sukhumvit Set","Thonburi","Noto Sans Thai","Segoe UI",Tahoma,sans-serif;margin:4px 0 14px}'
            '.doc-h b{font-size:1.15rem}.doc-h div{color:#8fa3c0;font-size:.8rem;margin-top:2px}'
            f'{RUNTIME_CSS}</style></head><body><div class="wrap" id="fqw"><div class="doc-h"><b>⚽ {e(title)}</b>'
            f'<div>{e(subtitle)}</div></div>{body_html}</div>'
            f'<script>{RUNTIME_JS}\nfqStory(document.getElementById("fqw"), null);</script></body></html>')


# ============================================================================ ชิ้นส่วนพื้นฐาน
def e(x):
    return _html.escape("" if x is None else str(x), quote=True)


def chip(text, kind=""):
    return f'<span class="s-chip {kind}">{e(text)}</span>'


def chips(items):
    return '<div class="s-chips">' + "".join(chip(t, k) for t, k in items) + "</div>"


def tipattr(text):
    return f' data-tip="{e(text)}"' if text else ""


def num(v, d=2, sign=False, pre="", suf="", cls=""):
    """ตัวเลขที่นับขึ้นเมื่อเผย (แสดงค่าจริงไว้แล้วเผื่อไม่มี JS)"""
    txt = pre + (f"{v:+.{d}f}" if sign else f"{v:.{d}f}") + suf
    return (f'<span class="{cls}" data-n="{v}" data-d="{d}" data-sg="{1 if sign else 0}" '
            f'data-pre="{e(pre)}" data-suf="{e(suf)}">{e(txt)}</span>')


def bar(frac, color="t", size="", mark=None, tip="", dl=0.0):
    w = max(0.0, min(1.0, frac or 0.0)) * 100
    mk = f'<i class="s-mark" style="left:{max(0, min(100, mark * 100)):.1f}%"></i>' if mark is not None else ""
    return (f'<div class="s-bar {size}"{tipattr(tip)}><i class="s-fill {color}" style="--w:{w:.1f}%;--dl:{dl:.2f}s"></i>{mk}</div>')


def rv(html_str, dl=0.0, tag="div", cls=""):
    return f'<{tag} class="s-rv {cls}" style="--dl:{dl:.2f}s">{html_str}</{tag}>'


def card(title, body, tag="", cls="", dl=0.0):
    head = f'<div class="s-h"><span>{e(title)}</span>{tag}</div>' if title or tag else ""
    return f'<div class="s-card s-rv {cls}" style="--dl:{dl:.2f}s">{head}{body}</div>'


def chapter(cid, n, kicker, title, lead, body):
    return (f'<section class="s-ch" id="{e(cid)}"><div class="s-node">{e(n)}</div>'
            f'<div class="s-rv"><div class="s-kick">{e(kicker)}</div><h2>{e(title)}</h2>'
            f'<p class="s-lead">{lead}</p></div>{body}</section>')


def story(chs, hero="", nav=True):
    """chs = [(id, ชื่อสั้นในเมนู, html ของบท)]"""
    nv = ""
    if nav and len(chs) > 1:
        nv = '<nav class="s-nav">' + "".join(
            f'<a data-go="{e(cid)}" href="#{e(cid)}"><i>{i}</i>{e(short)}</a>' for i, (cid, short, _) in enumerate(chs, 1)) + "</nav>"
    return f'<div class="s-root">{nv}{hero}{"".join(h for _, _, h in chs)}</div>'


def plain(body):
    return f'<div class="s-root">{body}</div>'


def dots(seq):
    cls = {"W": "w", "D": "d", "L": "l"}
    th = {"W": "ชนะ", "D": "เสมอ", "L": "แพ้"}
    s = str(seq or "").upper()
    return ('<div class="s-dots">' + "".join(
        f'<span class="s-dot {cls.get(c, "d")} s-pop" style="--dl:{.08 * i:.2f}s"{tipattr(th.get(c, c))}>{e(c)}</span>'
        for i, c in enumerate(s)) + "</div>") if s else ""


def ring(frac, label, sub="", color="#14b8a6"):
    o = 100 - max(0.0, min(1.0, frac)) * 100
    return (f'<div class="s-ringw"><svg viewBox="0 0 36 36"><circle class="bg" cx="18" cy="18" r="15.9" fill="none" stroke-width="3.6"/>'
            f'<circle class="s-ring" cx="18" cy="18" r="15.9" fill="none" stroke="{color}" stroke-width="3.6" pathLength="100" '
            f'stroke-dasharray="100" style="--o:{o:.1f}"/></svg><div>{label}<div class="s-sm s-mut">{sub}</div></div></div>')


def vbars(values, tips, cap=None):
    """แท่งบวก/ลบรายไม้ (เขียวบน แดงล่าง) แตะดูรายละเอียด"""
    mx = cap or max([1e-9] + [abs(v) for v in values])
    out = []
    for i, (v, t) in enumerate(zip(values, tips)):
        dl = min(i * 0.012, 0.9)
        if abs(v) < 1e-9:
            out.append(f'<div{tipattr(t)}><span class="mid"></span><i class="s-vfill z" style="--dl:{dl:.2f}s"></i></div>')
        else:
            out.append(f'<div{tipattr(t)}><span class="mid"></span><i class="s-vfill {"p" if v > 0 else "n"}" '
                       f'style="--h:{max(abs(v) / mx * 50, 2):.1f}%;--dl:{dl:.2f}s"></i></div>')
    return '<div class="s-vbars">' + "".join(out) + "</div>"


def line_chart(series, labels, fmt="{:+.2f}", W=760, H=250, zero=True, ends=None):
    """กราฟเส้นหลายชุด แตะ/ชี้ดูค่าแต่ละจุด · series = [(ชื่อ, สี, [ค่า])]"""
    n = len(labels)
    if n < 2 or not series:
        return '<div class="s-empty">ข้อมูลยังไม่พอวาดกราฟ</div>'
    L, R, T, B = 46, 12, 12, 26
    allv = [v for _, _, vs in series for v in vs] + ([0.0] if zero else [])
    lo, hi = min(allv), max(allv)
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.08
    lo2, hi2 = lo - pad, hi + pad
    X = lambda i: L + (W - L - R) * (i / (n - 1))
    Y = lambda v: T + (H - T - B) * (1 - (v - lo2) / (hi2 - lo2))
    p = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    ticks = sorted({round(lo, 2), round(hi, 2)} | ({0.0} if zero and lo < 0 < hi else set()))
    for v in ticks:
        y = Y(v)
        z = abs(v) < 1e-9
        dash = ' stroke-dasharray="4 4"' if z else ""
        p.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="rgba(255,255,255,{.35 if z else .1})" '
                 f'stroke-width="1"{dash}/>'
                 f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#8fa3c0">{e(fmt.format(v) if not z else "0")}</text>')
    a_, b_ = ends or (labels[0][:24], labels[-1][:24])
    p.append(f'<text x="{L}" y="{H - 6}" font-size="11" fill="#8fa3c0">{e(a_)}</text>'
             f'<text x="{W - R}" y="{H - 6}" text-anchor="end" font-size="11" fill="#8fa3c0">{e(b_)}</text>')
    xs = [round(X(i), 1) for i in range(n)]
    ys = []
    for k, (name, col, vs) in enumerate(series):
        yy = [round(Y(v), 1) for v in vs]
        ys.append(yy)
        pts = " ".join(f"{x},{y}" for x, y in zip(xs, yy))
        ln = 2.2 * sum(math.hypot(xs[i + 1] - xs[i], yy[i + 1] - yy[i]) for i in range(n - 1)) + 4   # เผื่อการย่อ/ขยายจอ
        if k == 0 and len(series) == 1:
            area = f"{xs[0]},{Y(max(lo2, min(0.0, hi2))):.1f} " + pts + f" {xs[-1]},{Y(max(lo2, min(0.0, hi2))):.1f}"
            p.append(f'<defs><linearGradient id="sg{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".28"/>'
                     f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
                     f'<polygon points="{area}" fill="url(#sg{k})" opacity=".9"/>')
        p.append(f'<polyline class="s-draw" style="--len:{ln:.0f}" fill="none" stroke="{col}" stroke-width="{2.6 if k == 0 else 2}" '
                 f'stroke-linejoin="round" stroke-linecap="round" points="{pts}" vector-effect="non-scaling-stroke"/>')
    p.append(f'<line class="s-guide" x1="0" x2="0" y1="{T}" y2="{H - B}"/>')
    for name, col, _ in series:
        p.append(f'<circle class="s-hdot" r="4.5" fill="{col}" stroke="#0b1220" stroke-width="2"/>')
    p.append("</svg>")
    data = {"W": W, "H": H, "x": xs, "y": ys, "s": [s[0] for s in series], "lab": [str(x) for x in labels],
            "v": [[fmt.format(v) for v in s[2]] for s in series]}
    legend = ('<div class="s-legend">' + "".join(f'<span><i style="background:{c}"></i>{e(nm)}</span>' for nm, c, _ in series) + "</div>"
              if len(series) > 1 else "")
    return f'{legend}<div class="s-chart" data-chart="{e(json.dumps(data, ensure_ascii=False))}">{"".join(p)}</div>'
