import os
import requests
import pandas as pd
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
    if not GEMINI_KEY:
        print("❌ ไม่มี GEMINI_API_KEY")
        return
    if not NEWS_KEY:
        print("❌ ไม่มี NEWS_API_KEY")
        return
    if not SHEET_ID:
        print("❌ ไม่มี GOOGLE_SHEET_ID")
        return
    
    print("✅ API Keys พร้อมใช้งาน\n")
    
    try:
        # ========================================
        # ขั้นที่ 1: อ่านลิงก์ห้องสนทนาจาก Google Sheets ช่อง A1
        # ========================================
        print("📊 กำลังอ่านลิงก์จาก Google Sheets...")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        
        try:
            df = pd.read_csv(sheet_url, header=None)
        except Exception as e:
            print(f"❌ ไม่สามารถอ่าน Google Sheet: {e}")
            print("💡 ตรวจสอบว่า Sheet เปิดเป็น 'Anyone with the link can view'")
            return
        
        if df.empty or pd.isna(df.iloc[0, 0]) or str(df.iloc[0, 0]).strip() == "":
            print("❌ ไม่พบลิงก์ในช่อง A1!")
            return
        
        room_link = str(df.iloc[0, 0]).strip()
        print(f"✅ ลิงก์ห้องสนทนา: {room_link}\n")
        
        # ========================================
        # ขั้นที่ 2: ดึงข่าวล่าสุดจาก News API
        # ========================================
        print("📰 กำลังดึงข่าวโลกล่าสุด...")
        news_url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=1&apiKey={NEWS_KEY}"
        
        try:
            news_response = requests.get(news_url, timeout=10)
        except Exception as e:
            print(f"⚠️ ไม่สามารถเชื่อมต่อ News API: {e}")
            news_title = "Global Events Today"
            news_desc = "Current world developments and trends."
        else:
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
        
        # ใช้ REST API ตรงแทน SDK
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        prompt_text = f"""คุณคือ AI นักวิเคราะห์ข่าวชั้นนำที่ทำงานในโปรเจกต์ "Manus Mission"

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
เขียนเป็นข้อความต่อเนื่องเลย"""
        
        gemini_payload = {
            "contents": [{
                "parts": [{
                    "text": prompt_text
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }
        
        try:
            gemini_response = requests.post(
                f"{gemini_url}?key={GEMINI_KEY}",
                json=gemini_payload,
                timeout=30
            )
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อ Gemini API: {e}")
            return
        
        if gemini_response.status_code != 200:
            print(f"❌ Gemini API Error: {gemini_response.status_code}")
            print(f"Response: {gemini_response.text}")
            print("\n💡 ตรวจสอบ GEMINI_API_KEY ที่ https://aistudio.google.com/app/apikey")
            return
        
        gemini_data = gemini_response.json()
        
        if 'candidates' in gemini_data and len(gemini_data['candidates']) > 0:
            final_content = gemini_data['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"✅ สร้างเนื้อหาเสร็จแล้ว ({len(final_content)} ตัวอักษร)\n")
        else:
            print("❌ ไม่ได้รับเนื้อหาจาก AI")
            print(f"Response: {gemini_data}")
            return
        
        # ========================================
        # ขั้นที่ 4: โพสต์อัตโนมัติไปยังบอร์ดสาธารณะ
        # ========================================
        print("📤 กำลังโพสต์ไปยังบอร์ดสาธารณะ...")
        
        # เพิ่ม timestamp และ signature
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        footer = f"\n\n━━━━━━━━━━━━━━━━━\n⏰ {timestamp}\n🤖 Posted by Manus Mission\n📰 Source: NewsAPI.org"
        full_post = final_content + footer
        
        # โพสต์ไปที่ Paste.ee
        try:
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
                },
                timeout=10
            )
        except Exception as e:
            print(f"❌ ไม่สามารถโพสต์: {e}")
            return
        
        if post_response.status_code == 201:
            post_url = post_response.json().get('link')
            print(f"\n{'='*60}")
            print("✅ โพสต์สำเร็จ!")
            print(f"🔗 ดูโพสต์ได้ที่: {post_url}")
            print(f"🔗 ลิงก์ห้องสนทนา: {room_link}")
            print("="*60 + "\n")
            
            # แสดงตัวอย่างเนื้อหา
            print("📝 ตัวอย่างเนื้อหาที่โพสต์:")
            print("-" * 60)
            preview = final_content[:300] + "..." if len(final_content) > 300 else final_content
            print(preview)
            print("-" * 60)
        else:
            print(f"❌ โพสต์ล้มเหลว! Status: {post_response.status_code}")
            print(f"Response: {post_response.text}")
    
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    manus_mission()        full_post = final_content + footer
        
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
