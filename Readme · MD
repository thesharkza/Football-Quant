# ⚽ Football Quant V5.8 — Self-Learning (Streamlit)

วิเคราะห์ตารางราคา 1X2 / Asian Handicap / OU ด้วย Rule 1-16 ฟันธงเดี่ยว 1 ตัวเลือก
และเรียนรู้จากผลจริง (ปรับน้ำหนัก Rule + สร้าง Rule ใหม่อัตโนมัติ)

## รันในเครื่อง
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # ใช้เฉพาะตอนอ่านรูป
streamlit run app.py
```
ใช้ผ่านบรรทัดคำสั่งก็ได้: `python football_quant_v58.py --help`

## Deploy บน Streamlit Community Cloud
1. Push โฟลเดอร์นี้ขึ้น GitHub (**ใช้ Private repo ถ้าไม่อยากเปิดเผยโค้ด**)
2. ไปที่ https://share.streamlit.io → New app → เลือก repo/branch → Main file path: `app.py`
3. Advanced settings → **Secrets** วาง:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
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
