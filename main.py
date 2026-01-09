import os
import requests
import pandas as pd
from google import genai
from datetime import datetime

def manus_mission():
    """ภารกิจหลักของมนัส: อ่าน -> วิเคราะห์ -> โพสต์อัตโนมัติ"""
    
    print("\n" + "="*60)
    print("🤖 MANUS MISSION - เริ่มทำงาน")
    print("="*60 + "\n")
    
    # ดึง API Keys จาก GitHub Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    # ตรวจสอบว่ามี Keys ครบหรือไม่
    if not all([GEMINI_KEY, NEWS_KEY, SHEET_ID]):
        print("❌ ขาด API Keys! ตรวจสอบ GitHub Secrets")
        return
    
    try:
        # ========================================
        # ขั้นที่ 1: อ่านลิงก์ห้องสนทนาจาก Google Sheets ช่อง A1
        # ========================================
        print("📊 กำลังอ่านลิงก์จาก Google Sheets...")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        
        if df.empty or df.iloc[0, 0] == "":
            print("❌ ไม่พบลิงก์ในช่อง A1!")
            return
        
        room_link = str(df.iloc[0, 0]).strip()
        print(f"✅ ลิงก์ห้องสนทนา: {room_link}\n")
        
        # ========================================
        # ขั้นที่ 2: ดึงข่าวล่าสุดจาก News API
        # ========================================
        print("📰 กำลังดึงข่าวโลกล่าสุด...")
        news_url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=1&apiKey={NEWS_KEY}"
        news_response = requests.get(news_url, timeout=10)
        
        if news_response.status_code != 200:
            print(f"⚠️ News API ตอบกลับ: {news_response.status_code}")
            news_title = "Global Events Today"
            news_desc = "Current world developments and trends."
        else:
            news_data = news_response.json()
            if news_data.get('articles') and len(news_data['articles']) > 0:
                article = news_data['articles'][0]
                news_title = article.get('title', 'Breaking News')
                news_desc = article.get('description', 'Latest global news.')
            else:
                news_title = "Global Trends"
                news_desc = "Analysis of current events."
        
        print(f"✅ ข่าว: {news_title}\n")
        
        # ========================================
        # ขั้นที่ 3: ให้ Gemini AI วิเคราะห์และรีไรท์
        # ========================================
        print("🧠 กำลังให้ AI วิเคราะห์และสร้างเนื้อหา...")
        
        client = genai.Client(api_key=GEMINI_KEY)
        
        prompt = f"""
คุณคือ AI นักวิเคราะห์ข่าวชั้นนำที่ทำงานในโปรเจกต์ "Manus Mission"

ข่าวที่ต้องวิเคราะห์:
หัวข้อ: {news_title}
รายละเอียด: {news_desc}

คำสั่ง:
1. เขียนวิเคราะห์ข่าวนี้เป็นภาษาไทย ความยาว 150-200 คำ
2. ใช้ภาษาที่เข้าใจง่าย น่าสนใจ และมีมุมมองที่ลึกซึ้ง
3. เน้นย้ำว่านี่คือ "การวิเคราะห์โดย AI ที่ได้รับการฝึกฝนมาเป็นพิเศษ"
4. ท้ายสุดให้เชิญชวนด้วยประโยคนี้:

"💬 สนใจคุยต่อหรืออ่านการวิเคราะห์เชิงลึกเพิ่มเติม?
👉 เข้าร่วมห้องสนทนาได้ที่: {room_link}

🌍 ห้องสนทนารองรับการแปลภาษาอัตโนมัติทุกภาษาทั่วโลก"

ห้ามใส่หัวข้อหรือ markdown formatting
เขียนเป็นข้อความต่อเนื่องเลย
"""
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        final_content = response.text.strip()
        print(f"✅ สร้างเนื้อหาเสร็จแล้ว ({len(final_content)} ตัวอักษร)\n")
        
        # ========================================
        # ขั้นที่ 4: โพสต์อัตโนมัติไปยังบอร์ดสาธารณะ
        # ========================================
        print("📤 กำลังโพสต์ไปยังบอร์ดสาธารณะ...")
        
        # เพิ่ม timestamp และ signature
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        footer = f"\n\n━━━━━━━━━━━━━━━━━\n⏰ {timestamp}\n🤖 Posted by Manus Mission\n🔗 Source: NewsAPI.org"
        full_post = final_content + footer
        
        # โพสต์ไปที่ Paste.ee (บอร์ดสาธารณะที่ไม่ต้องล็อกอิน)
        post_response = requests.post(
            "https://api.paste.ee/v1/pastes",
            json={
                "description": f"Manus Mission - {datetime.now().strftime('%Y-%m-%d')}",
                "sections": [{
                    "name": "AI News Analysis",
                    "contents": full_post
                }]
            },
            headers={
                "X-Auth-Token": "u6IOfYIDJ34C48R2p6y3S9H9x8r5fX5z9mX1"
            }
        )
        
        if post_response.status_code == 201:
            post_url = post_response.json().get('link')
            print(f"\n{'='*60}")
            print("✅ โพสต์สำเร็จ!")
            print(f"🔗 ดูโพสต์ได้ที่: {post_url}")
            print(f"🔗 ลิงก์ห้องสนทนา: {room_link}")
            print("="*60 + "\n")
            
            # แสดงตัวอย่างเนื้อหา
            print("📝 เนื้อหาที่โพสต์:")
            print("-" * 60)
            print(final_content[:300] + "..." if len(final_content) > 300 else final_content)
            print("-" * 60)
        else:
            print(f"❌ โพสต์ล้มเหลว! Status: {post_response.status_code}")
            print(f"Response: {post_response.text}")
    
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    manus_mission()
