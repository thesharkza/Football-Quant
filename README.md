# ⚽ Football Quant V5.9 — Self-Learning (Streamlit)

วิเคราะห์ตารางราคา 1X2 / Asian Handicap / OU ด้วย Rule 1-26 (+ R27 Coupled Steam, R28 Current Odds Anchor), Home/Away Verification Protocol และ Current Odds Priority ฟันธงเดี่ยว 1 ตัวเลือก
และเรียนรู้จากผลจริง (ปรับน้ำหนัก Rule + สร้าง Rule ใหม่อัตโนมัติ)

## รันในเครื่อง
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...                # ใช้เฉพาะตอนอ่านรูป (โมเดลเริ่มต้น gemini-3.7-flash)
streamlit run app.py
```
ใช้ผ่านบรรทัดคำสั่งก็ได้: `python football_quant_v58.py --help`

## Deploy บน Streamlit Community Cloud
1. Push โฟลเดอร์นี้ขึ้น GitHub (**ใช้ Private repo ถ้าไม่อยากเปิดเผยโค้ด**)
2. ไปที่ https://share.streamlit.io → New app → เลือก repo/branch → Main file path: `app.py`
3. Advanced settings → **Secrets** วาง:
   ```toml
   GEMINI_API_KEY = "..."
   APP_PASSWORD = "รหัสผ่านของคุณ"
   ```
4. Deploy

## ข้อควรระวัง
- **ห้าม commit API key** (`.gitignore` กัน `secrets.toml` และ `quant_data/` ไว้แล้ว)
- **ข้อมูลการเรียนรู้หายเมื่อแอปรีสตาร์ท** บน Streamlit Cloud (ดิสก์ชั่วคราว) → กดสำรองที่แท็บ 💾 หลังใส่ผลทุกครั้ง
  และกู้คืนเมื่อเปิดใหม่ (หรือรันในเครื่อง/VPS/Docker ที่มี volume ถาวร โดยตั้ง `QUANT_DATA_DIR`)
- ทุกคนที่เข้าลิงก์ใช้ข้อมูลเรียนรู้ชุดเดียวกัน และการอ่านรูปใช้ API key ของคุณ → ตั้ง `APP_PASSWORD` เสมอ
- รองรับรูป png/jpg/webp/gif ไม่เกิน 5MB ต่อรูป (ไม่รองรับ HEIC)
- เครื่องมือเชิงสถิติ/ฮิวริสติก ไม่รับประกันผลลัพธ์

## V5.9 มีอะไรเพิ่ม
- **Home/Away Verification Protocol:** ตรวจสิทธิ์เหย้า/เยือนก่อนทุกครั้ง (เรต HDP ปัจจุบัน vs 1X2 ปัจจุบัน, คอลัมน์ซ้ายของตาราง Asian Handicap, ชื่อทีมของ H2H) ถ้าไม่ผ่านจะลดระดับสัญญาณเป็น "ต่ำ"
- **Current Odds Priority:** รายงานแสดงราคาปัจจุบันเป็นหลัก ราคาเปิดใช้อ้างอิงการไหลเท่านั้น และสัญญาณที่มาจากการไหลของราคาล้วน (ไม่มีราคาปัจจุบัน/บริบทหนุน) จะถูกลดคะแนนเหลือ 60%
- **Rule 17-26:** Table Control, Home Pride, High-Scoring Filter, Away Favorite Buffer, Continental Cup Shield, Home Momentum, False Giant Slump Shield
- **Rule 27/28 (เพิ่มเอง):** Coupled Steam Confirmation (เดิมคือ R17 ใน V5.8) และ Current Odds Anchor

ข้อมูลเสริมในไฟล์ JSON (ไม่บังคับ): `rank`, `league_size`, `ah_left_team`, `home_form_home` (`{"w":3,"d":2,"l":0}` ในบ้าน 5 นัด),
`stats.away_counter_pct`, และ context `high_draw_league` / `continental_cup` ดูตัวอย่างใน `example_match.json`

## ระบบอัตโนมัติ (อัปเดตล่าสุด)
กดปุ่มเดียว "🚀 วิเคราะห์อัตโนมัติ" ระบบจะทำต่อเนื่อง 3 ขั้น: อ่านรูป → **ให้ Gemini ค้นหาข้อมูลจริงทาง Google Search เพื่อกำหนดบริบทแมตช์**
(ดาร์บี้, ประเภทรายการ, ถ้วยทวีป/น็อคเอาต์, ลีกประตูเยอะ/เสมอสูง, อันดับตาราง, จำนวนทีมในลีก, ทีมที่หนีตาย, ฟอร์มในบ้าน 5 นัด) → วิเคราะห์และฟันธง
- หน้าผลลัพธ์แสดงหลักฐานสั้น ๆ และแหล่งข้อมูลของบริบทที่ค้นได้ ถ้าค้นไม่สำเร็จจะใช้ค่าตั้งต้นและแจ้งเตือน
- ปิดการค้นหาได้ที่สวิตช์ "ค้นหาบริบทแมตช์อัตโนมัติ" (การค้นหาคิดค่าบริการตามจำนวนคำค้นของ Gemini)
- แก้บริบทเองได้ที่ "⚙ ตั้งค่าขั้นสูง" (ติ๊กเพื่อบังคับเป็น "ใช่" ทับผลค้นหา)
- บรรทัดคำสั่ง: `python football_quant_v58.py images 1.jpg ... 5.jpg` (ใส่ `--no-research` ถ้าไม่ต้องการค้นหาบริบท)

## หน้าตาและความเป็นส่วนตัวของหน้าจอ
- ธีมมืด ซ่อนเมนู/แถบเครื่องมือของ Streamlit และไม่แสดงโค้ดหรือ JSON ในหน้าหลัก (อยู่ใน "ตั้งค่าขั้นสูง" เท่านั้น)
- `.streamlit/config.toml` ตั้ง `showErrorDetails = "none"` เพื่อไม่ให้ผู้ใช้เห็น traceback ถ้าต้องดูสาเหตุ error ให้ใช้ Manage app → Logs
