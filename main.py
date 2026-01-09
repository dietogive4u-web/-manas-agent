import os
import requests
import pandas as pd
from google import genai
from datetime import datetime

def manus_mission():
    # 1. ดึงกุญแจสำคัญ
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    # 2. อ่านคำสั่งจาก Google Sheets
    try:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        room_link = df.iloc[0, 0]  # ลิงก์ห้องแปลใน A1
        topic_focus = df.iloc[0, 1] # หัวข้อใน B1
        print(f"✅ รับภารกิจ: {topic_focus}")
    except Exception as e:
        print(f"❌ อ่านชีตไม่สำเร็จ: {e}"); return

    # 3. ใช้ AI สร้างเนื้อหา (ปรับการเรียกใช้ Model ใหม่)
    try:
        # ใช้โครงสร้าง Client ที่เสถียรที่สุด
        client = genai.Client(api_key=GEMINI_KEY)
        
        prompt = f"""
        Analyze and write about '{topic_focus}' to save the world and religion.
        End with: "Watch our deep analysis (translated in all languages) here: {room_link}"
        """

        # เรียกใช้โมเดลโดยไม่ระบุ v1beta เพื่อเลี่ยง Error 404
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        article = response.text

        # 4. การโพสต์กระจายข่าว (สร้าง Link ใหม่ทุกวัน)
        # โพสต์ไปที่กระดานสาธารณะ Paste.ee
        payload = {
            "sections": [{"name": f"Manus Mission {datetime.now().date()}", "contents": article}],
            "description": "Global Spiritual Broadcast"
        }
        res = requests.post("https://api.paste.ee/v1/pastes", json=payload, headers={"X-Auth-Token": "public"})
        
        if res.status_code == 201:
            print(f"🚀 โพสต์สำเร็จ! ลิงก์ใบปลิวใหม่ของโลก: {res.json().get('link')}")
        else:
            print(f"⚠️ สร้างบทความสำเร็จแต่โพสต์ล้มเหลว")

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
