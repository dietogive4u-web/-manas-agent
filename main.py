import os
import requests
import pandas as pd
from google import genai

def manus_mission():
    # ดึงค่า Keys จาก GitHub Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    try:
        # 1. อ่านลิงก์ห้องสนทนาจาก Google Sheets ช่อง A1
        # ต้องตั้งค่า Sheet เป็น "Anyone with the link can view"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        room_link = df.iloc[0, 0] 
        print(f"🔗 ลิงก์จากชีต: {room_link}")
        
        # 2. ดึงข่าวล่าสุดจาก News API (เลือกข่าวเด่น 1 ข่าว)
        news_url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}"
        news_data = requests.get(news_url).json()
        
        if news_data.get('articles'):
            article = news_data['articles'][0]
            news_title = article['title']
            news_desc = article['description']
        else:
            news_title = "Global Trends Today"
            news_desc = "Analysis of current events."

        # 3. ใช้ Gemini AI วิเคราะห์และรีไรท์
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""
        วิเคราะห์ข่าวนี้: {news_title}
        รายละเอียด: {news_desc}
        
        คำสั่ง:
        1. เขียนสรุปวิเคราะห์ให้ดูมีความรู้และน่าสนใจ (ภาษาไทย)
        2. เน้นย้ำว่านี่คือการวิเคราะห์โดย AI รุ่นพิเศษที่มีโค้ดชุดเดียว
        3. ปิดท้ายด้วยประโยคเชิญชวนให้คนเข้ามาคุยต่อที่นี่: {room_link}
        4. บอกว่า "ห้องสนทนานี้รองรับการแปลทุกภาษาทั่วโลก"
        """
        
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        final_content = response.text

        # 4. ส่งไปโพสต์ที่บอร์ดสาธารณะ (Paste.ee)
        # นี่คือบอร์ดที่โพสต์ได้เลยโดยไม่ต้องสมัครสมาชิก (ใช้เป็นที่กระจายข่าว)
        post_res = requests.post(
            "https://api.paste.ee/v1/pastes",
            json={
                "description": "Manus Mission Post",
                "sections": [{"name": "AI Analysis", "contents": final_content}]
            },
            headers={"X-Auth-Token": "u6IOfYIDJ34C48R2p6y3S9H9x8r5fX5z9mX1"} # Public Key
        )
        
        if post_res.status_code == 201:
            print(f"🚀 สำเร็จ! ดูโพสต์ได้ที่: {post_res.json().get('link')}")
        else:
            print(f"❌ โพสต์ไม่สำเร็จ: {post_res.status_code}")

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
