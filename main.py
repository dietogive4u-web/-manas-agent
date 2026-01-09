import os
import requests
import pandas as pd
from google import genai
from datetime import datetime

def manus_mission():
    # 1. ดึงข้อมูลจาก GitHub Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    # 2. อ่านคำสั่งจาก Google Sheets
    try:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        room_link = df.iloc[0, 0]  # ลิงก์ห้องแปลในช่อง A1
        topic_focus = df.iloc[0, 1] # หัวข้อภารกิจในช่อง B1
        print(f"✅ รับภารกิจ: {topic_focus}")
    except Exception as e:
        print(f"❌ อ่านชีตไม่สำเร็จ: {e}"); return

    # 3. ให้ AI สร้างบทความวิเคราะห์
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""
        Write a high-impact spiritual and philosophical analysis about '{topic_focus}'. 
        The goal is to save the world and religion through wisdom.
        
        Mandatory Ending:
        "Watch our deep analysis (translated in all languages) here: {room_link}"
        """
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        article = response.text

        # 4. นำไปโพสต์บนกระดานสาธารณะ (Paste.ee)
        payload = {
            "sections": [{"name": f"Mission {datetime.now().date()}", "contents": article}],
            "description": "Global Spiritual Broadcast"
        }
        res = requests.post("https://api.paste.ee/v1/pastes", json=payload, headers={"X-Auth-Token": "public"})
        
        if res.status_code == 201:
            print(f"🚀 ประกาศสำเร็จ! ลิงก์ใบปลิวโลก: {res.json().get('link')}")
        else:
            print(f"⚠️ โพสต์ไม่สำเร็จแต่สร้างบทความได้: {article[:100]}...")

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
