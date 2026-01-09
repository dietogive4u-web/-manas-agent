import os
import requests
import pandas as pd

def manus_mission():
    # ดึงค่า Keys จาก GitHub Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    try:
        # 1. อ่านลิงก์ห้องสนทนาจาก Google Sheets ช่อง A1
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(sheet_url, header=None)
        room_link = df.iloc[0, 0] 
        print(f"✅ ดึงลิงก์เป้าหมายสำเร็จ: {room_link}")
        
        # 2. ดึงข่าวล่าสุดจาก News API
        news_url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}"
        news_res = requests.get(news_url).json()
        article = news_res.get('articles', [{}])[0]
        news_content = f"Title: {article.get('title')}\nDescription: {article.get('description')}"
        print(f"✅ ดึงข่าวสำเร็จ: {article.get('title')}")

        # 3. วิเคราะห์ด้วย Gemini (ใช้ URL ตรงเพื่อเลี่ยง Error 404)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        prompt = f"""
        จงวิเคราะห์ข่าวนี้เป็นภาษาไทย: {news_content}
        
        คำสั่งพิเศษ:
        1. เขียนให้น่าสนใจและดูเป็นผู้เชี่ยวชาญ
        2. ปิดท้ายด้วยการเชิญชวนคนมาชมการวิเคราะห์จาก AI ที่ถูกฝึกมาพิเศษ (โค้ดชุดเดียว)
        3. แนบลิงก์นี้ไว้ท้ายโพสต์: {room_link} 
        4. ระบุว่า 'ห้องสนทนานี้รองรับการแปลทุกภาษาทั่วโลก'
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(gemini_url, json=payload)
        
        if response.status_code == 200:
            final_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # 4. โพสต์ลงบอร์ดสาธารณะ (Paste.ee) 
            # คุณสามารถเปลี่ยน URL ตรงนี้เป็น API ของบอร์ดอื่นที่คุณต้องการได้
            requests.post(
                "https://api.paste.ee/v1/pastes",
                json={"sections": [{"name": "Manus Mission Analysis", "contents": final_text}]},
                headers={"X-Auth-Token": "public"}
            )
            print("🚀 โพสต์ข่าวเรียบร้อยแล้ว!")
        else:
            print(f"❌ Gemini Error: {response.text}")

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
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
