import os
import requests
import pandas as pd
from google import genai
from datetime import datetime

def manus_mission():
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    try:
        # อ่านคำสั่งจาก Google Sheets
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        room_link = df.iloc[0, 0] # ลิงก์ห้องแปลใน A1
        topic_focus = df.iloc[0, 1] # หัวข้อใน B1
        print(f"✅ รับภารกิจ: {topic_focus}")
    except Exception as e:
        print(f"❌ อ่านชีตไม่ได้: {e}"); return

    try:
        # ใช้สมอง Gemini ตัวใหม่ล่าสุด
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Analyze '{topic_focus}' and invite people to: {room_link}"
        )
        article = response.text

        # 🚀 ส่งไปโพสต์ที่บอร์ดสาธารณะ (ได้ลิงก์ใหม่ทันที)
        res = requests.post(
            "https://api.paste.ee/v1/pastes",
            json={"sections": [{"name": "Manus Mission", "contents": article}]},
            headers={"X-Auth-Token": "public"}
        )
        
        if res.status_code == 201:
            print(f"🚀 โพสต์สำเร็จ! ดูใบปลิวที่นี่: {res.json().get('link')}")
        else:
            print("⚠️ สร้างเนื้อหาได้แต่โพสต์ไม่สำเร็จ")

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
