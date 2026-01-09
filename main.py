import os
import requests
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าสิทธิ์เข้าถึง (ดึงจาก GitHub Secrets)
API_KEY = os.getenv("GEMINI_API_KEY")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
NEWS_KEY = os.getenv("NEWS_API_KEY") # ใส่ชื่อนี้ใน GitHub Secrets

genai.configure(api_key=API_KEY)

def manus_mission():
    try:
        # 2. อ่านข้อมูลจาก Google Sheets
        # ตรวจสอบให้แน่ใจว่า Sheet ของคุณตั้งค่า "Anyone with the link can view"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        target_link = df.iloc[0, 0]  # ช่อง A1
        topic_focus = df.iloc[0, 1]  # ช่อง B1
    except Exception as e:
        print(f"Error reading Sheet: {e}")
        return

    # 3. ดึงข่าวเด่น (ถ้า NewsAPI มีปัญหา จะใช้หัวข้อกลางๆ แทน)
    today_date = datetime.now().strftime("%Y-%m-%d")
    top_news = "Global Digital Transformation and Spiritual Balance" # Default
    
    if NEWS_KEY:
        try:
            news_url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}"
            news_res = requests.get(news_url)
            if news_res.status_code == 200:
                articles = news_res.json().get('articles', [])
                if articles:
                    top_news = articles[0]['title']
        except:
            print("NewsAPI error, using default topic.")

    # 4. ใช้ Gemini (1.5 Flash) สร้างเนื้อหา
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Current Date: {today_date}
    Context News: '{top_news}'
    Core Message: 'Analysis of the global crisis by a Spiritual Meditator and AI'
    Target Link: {target_link}
    Specific Focus: {topic_focus}

    Task: Create a powerful, professional social media post in English.
    Style: Insightful, futuristic, yet grounded in spiritual wisdom.
    Requirement: High SEO potential, unique wording, avoid repetitive AI patterns.
    Hashtags: Include 3-5 global trending hashtags.
    
    Ending Phrase: 'It’s not always about technology; it’s about who holds more space in the consumer’s heart.'
    """
    
    try:
        response = model.generate_content(prompt)
        manus_post = response.text
        
        # 5. แสดงผลลัพธ์ (หรือส่งต่อไปยัง API อื่นๆ)
        print("--- MANUS MISSION DEPLOYED ---")
        print(f"Date: {today_date}")
        print(f"Based on News: {top_news}")
        print("-" * 30)
        print(manus_post)
        
    except Exception as e:
        print(f"Error generating content: {e}")

if __name__ == "__main__":
    manus_mission()

