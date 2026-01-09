import os
import requests
import pandas as pd
from datetime import datetime
# ใช้ library ตัวใหม่ที่ระบบแนะนำ
from google import genai 

def manus_mission():
    # 1. ดึงข้อมูลจาก GitHub Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    NEWS_KEY = os.getenv("NEWS_API_KEY")

    # 2. อ่านข้อมูลจาก Google Sheets
    try:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        target_link = df.iloc[0, 0]  # ช่อง A1
        topic_focus = df.iloc[0, 1]  # ช่อง B1
        print(f"✅ Read Sheet Success: {topic_focus}")
    except Exception as e:
        print(f"❌ Sheet Error: {e}")
        return

    # 3. ดึงข่าวเด่น (ถ้าไม่มี News Key จะใช้หัวข้อสำรอง)
    top_news = "Global Digital Trends 2026"
    if NEWS_KEY:
        try:
            res = requests.get(f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}").json()
            if res.get('articles'):
                top_news = res['articles'][0]['title']
        except:
            print("⚠️ NewsAPI error, using default topic.")

    # 4. ใช้ AI สร้างเนื้อหา (ใช้โครงสร้าง Client แบบใหม่ลดปัญหา 404)
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Context: {top_news}. Topic: {topic_focus}. Link: {target_link}. Create a social media post (English) with a Spiritual & AI perspective."
        )
        
        # 5. แสดงผลลัพธ์ลงในหน้า Log
        print("\n" + "="*30)
        print("🤖 MANUS MISSION OUTPUT")
        print("="*30)
        print(f"DATE: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"NEWS: {top_news}")
        print("-"*30)
        print(response.text)
        print("="*30)
        
    except Exception as e:
        print(f"❌ AI Generation Error: {e}")
        print("Tip: ตรวจสอบว่า GEMINI_API_KEY ใน Secrets ถูกต้องหรือไม่")

if __name__ == "__main__":
    manus_mission()
    # 4. ใช้ Gemini สร้างเนื้อหา (ปรับปรุงการเรียก Model)
    try:
        # ใช้ชื่อโมเดลมาตรฐานที่เสถียรที่สุด
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Context News: '{top_news}'
        Core Message: 'Analysis of the global crisis by a Spiritual Meditator and AI'
        Target Link: {target_link}
        Specific Focus: {topic_focus}

        Task: Create a powerful, professional social media post in English.
        Style: Insightful, futuristic, yet grounded in spiritual wisdom.
        Requirement: High SEO potential, unique wording.
        Hashtags: Include 3-5 global trending hashtags.
        
        Ending Phrase: 'It’s not always about technology; it’s about who holds more space in the consumer’s heart.'
        """
        
        response = model.generate_content(prompt)
        
        print("--- MANUS MISSION DEPLOYED ---")
        print(response.text)
        
    except Exception as e:
        print(f"Error during AI Generation: {e}")
        # หากยังขึ้น 404 ให้ลองดูรุ่นโมเดลที่มีในระบบ
        print("Tip: Check if gemini-1.5-flash is available in your region.")

if __name__ == "__main__":
    manus_mission()
