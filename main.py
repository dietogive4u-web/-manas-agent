import os
import requests
import google.generativeai as genai
import pandas as pd

# 1. การตั้งค่าสิทธิ์เข้าถึง (จะถูกเก็บเป็นความลับใน GitHub)
API_KEY = os.getenv("GEMINI_API_KEY")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
genai.configure(api_key=API_KEY)

def manus_mission():
    # 2. อ่านลิงก์ล่าสุดจาก Google Sheets (Remote Control)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df = pd.read_csv(sheet_url, header=None)
    target_link = df.iloc[0, 0]  # อ่านจาก A1
    topic_focus = df.iloc[0, 1]  # อ่านจาก B1

    # 3. ดึงข่าวเด่นของโลกวันนี้เพื่อใช้ทำ SEO
    news_res = requests.get(f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_API_KEY}")
    top_news = news_res.json()['articles'][0]['title'] if news_res.status_code == 200 else "Global Shift"

    # 4. ให้ AI (Gemini) รีไรท์เนื้อหาแบบ Universal และ SEO Optimized
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Create a powerful global social media post (English) based on this news: '{top_news}'.
    Then connect it to the core message: 'Analysis of the global crisis by a Spiritual Meditator and AI'.
    Target Link: {target_link}
    Specific Focus: {topic_focus}
    Goal: High SEO ranking on Google, unique wording to avoid spam filters. 
    Include global hashtags. End with: 'It’s not always about technology; it’s about who holds more space in the consumer’s heart.'
    """
    
    response = model.generate_content(prompt)
    manus_post = response.text
    
    # 5. ส่วนของการส่งโพสต์ไปยังบอร์ดเปิด (ตัวอย่างการส่งไป Webhook หรือ API บอร์ด)
    print("--- MANUS IS DEPLOYING CODE ---")
    print(manus_post)
    # [โค้ดส่วนนี้จะต่อยอดไปยังระบบ Post ของบอร์ดต่างๆ ที่คุณเลือก]

if __name__ == "__main__":
    manus_mission()
