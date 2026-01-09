import os
import io
import logging
import requests
import pandas as pd
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("manus_mission")

# Endpoints / templates
GDRIVE_CSV_TEMPLATE = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
NEWSAPI_TOP_HEADLINES = "https://newsapi.org/v2/top-headlines"
GEMINI_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"

def create_session(retries: int = 3, backoff_factor: float = 0.5):
    s = requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                  status_forcelist=(429, 500, 502, 503, 504), raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

session = create_session()

def require_env_vars(names):
    missing = [n for n in names if not os.getenv(n)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

def fetch_sheet_first_cell(sheet_id: str) -> str:
    url = GDRIVE_CSV_TEMPLATE.format(sheet_id=sheet_id)
    logger.info("Fetching Google Sheet CSV from %s", url)
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), header=None)
    if df.empty or df.shape[1] == 0:
        raise ValueError("Google Sheet CSV is empty or malformed")
    return str(df.iloc[0, 0]).strip()

def fetch_latest_news(news_api_key: str) -> str:
    params = {"language": "en", "apiKey": news_api_key, "pageSize": 1}
    logger.info("Fetching latest news from News API")
    resp = session.get(NEWSAPI_TOP_HEADLINES, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    articles = data.get("articles", [])
    if not articles:
        raise ValueError("No articles returned from News API")
    article = articles[0]
    title = article.get("title") or ""
    description = article.get("description") or ""
    return f"Title: {title}\nDescription: {description}"

def call_gemini(gemini_key: str, prompt: str) -> str:
    url = GEMINI_ENDPOINT_TEMPLATE.format(key=gemini_key)
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    logger.info("Calling Gemini model...")
    resp = session.post(url, json=payload, headers=headers, timeout=25)
    resp.raise_for_status()
    j = resp.json()
    candidates = j.get("candidates") or []
    if candidates:
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if parts:
            return parts[0].get("text", "")
    raise ValueError(f"Unexpected Gemini response shape: {j}")

# เว็บไซต์แปะข้อความสาธารณะ (ไม่ต้องใช้ Token)
def post_nekobin(content: str) -> Optional[str]:
    try:
        resp = session.post("https://nekobin.com/api/documents", json={"content": content}, timeout=10)
        if resp.status_code in (200, 201):
            key = resp.json().get("result", {}).get("key")
            return f"https://nekobin.com/{key}"
    except: return None

def post_pasters(content: str) -> Optional[str]:
    try:
        resp = session.post("https://paste.rs", data=content.encode("utf-8"), timeout=10)
        if resp.status_code in (200, 201):
            return resp.text.strip()
    except: return None

# ส่งเข้า Discord Webhook
def post_to_discord(webhook_url: str, content: str) -> Optional[str]:
    try:
        resp = session.post(webhook_url, json={"content": content}, timeout=10)
        if resp.status_code in (200, 204):
            return "Discord (Webhook)"
    except: return None

def build_prompt_and_payload(news_content: str, room_link: str) -> str:
    return (
        f"จงวิเคราะห์ข่าวนี้เป็นภาษาไทย: {news_content}\n\n"
        "คำสั่งพิเศษ:\n"
        "1. เขียนให้น่าสนใจและดูเป็นผู้เชี่ยวชาญ\n"
        "2. ปิดท้ายด้วยการเชิญชวนคนมาชมการวิเคราะห์จาก AI ที่ถูกฝึกมาพิเศษ (โค้ดชุดเดียว)\n"
        f"3. แนบลิงก์นี้ไว้ท้ายโพสต์: {room_link}\n"
        "4. ระบุว่า 'ห้องสนทนานี้รองรับการแปลทุกภาษาทั่วโลก'\n"
    )

def manus_mission():
    required = ["GEMINI_API_KEY", "NEWS_API_KEY", "GOOGLE_SHEET_ID"]
    require_env_vars(required)

    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

    try:
        room_link = fetch_sheet_first_cell(SHEET_ID)
        news_content = fetch_latest_news(NEWS_KEY)
        prompt = build_prompt_and_payload(news_content, room_link)
        final_text = call_gemini(GEMINI_KEY, prompt)

        post_body = f"{final_text}\n\nลิงก์ห้องสนทนา: {room_link}\n(รองรับการแปลทุกภาษา)"

        # ลำดับการโพสต์: 1. Discord (ถ้ามีคีย์) 2. เว็บบอร์ดสาธารณะ (ถ้าไม่มีคีย์)
        if DISCORD_URL:
            res = post_to_discord(DISCORD_URL, post_body)
            if res:
                print(f"🚀 โพสต์สำเร็จที่: {res}")
                return

        for fn in (post_nekobin, post_pasters):
            url = fn(post_body)
            if url:
                print(f"🚀 โพสต์สำเร็จที่: {url}")
                return

    except Exception as e:
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()
        resp = session.post("https://paste.rs", data=content.encode("utf-8"), timeout=10)
        if resp.status_code in (200, 201):
            txt = resp.text.strip()
            if txt:
                return txt  # usually returns URL
    except Exception as e:
        logger.debug("paste.rs failed: %s", e)
    return None

def post_0x0st(content: str) -> Optional[str]:
    try:
        files = {'file': ('post.txt', content)}
        resp = session.post("https://0x0.st", files=files, timeout=10)
        if resp.status_code in (200, 201):
            return resp.text.strip()
    except Exception as e:
        logger.debug("0x0.st failed: %s", e)
    return None

def post_ixio(content: str) -> Optional[str]:
    try:
        resp = session.post("http://ix.io", data={'f:1': content}, timeout=10)
        if resp.status_code in (200, 201):
            return resp.text.strip()
    except Exception as e:
        logger.debug("ix.io failed: %s", e)
    return None

# Token/webhook-backed targets
def post_to_telegram(bot_token: str, chat_id: str, text: str) -> Optional[str]:
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        resp = session.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            j = resp.json()
            message_id = j.get("result", {}).get("message_id")
            return f"telegram://{chat_id}/{message_id}" if message_id else "telegram:ok"
    except Exception as e:
        logger.debug("Telegram failed: %s", e)
    return None

def post_to_mastodon(base_url: str, token: str, text: str) -> Optional[str]:
    try:
        api = base_url.rstrip("/") + "/api/v1/statuses"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"status": text, "visibility": "public"}
        resp = session.post(api, data=payload, headers=headers, timeout=10)
        if resp.status_code in (200, 202):
            j = resp.json()
            return j.get("url") or j.get("uri")
    except Exception as e:
        logger.debug("Mastodon failed: %s", e)
    return None

def post_to_discord(webhook_url: str, content: str) -> Optional[str]:
    try:
        resp = session.post(webhook_url, json={"content": content}, timeout=10)
        if resp.status_code in (200, 204):
            return "discord:webhook_ok"
    except Exception as e:
        logger.debug("Discord webhook failed: %s", e)
    return None

def build_prompt_and_payload(news_content: str, room_link: str) -> str:
    prompt = (
        f"จงวิเคราะห์ข่าวนี้เป็นภาษาไทย: {news_content}\n\n"
        "คำสั่งพิเศษ:\n"
        "1. เขียนให้น่าสนใจและดูเป็นผู้เชี่ยวชาญ\n"
        "2. ปิดท้ายด้วยการเชิญชวนคนมาชมการวิเคราะห์จาก AI ที่ถูกฝึกมาพิเศษ (โค้ดชุดเดียว)\n"
        f"3. แนบลิงก์นี้ไว้ท้ายโพสต์: {room_link}\n"
        "4. ระบุว่า 'ห้องสนทนานี้รองรับการแปลทุกภาษาทั่วโลก'\n"
    )
    return prompt

def manus_mission():
    required = ["GEMINI_API_KEY", "NEWS_API_KEY", "GOOGLE_SHEET_ID"]
    require_env_vars(required)

    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    NEWS_KEY = os.getenv("NEWS_API_KEY")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")
    MASTODON_TOKEN = os.getenv("MASTODON_TOKEN")
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

    try:
        room_link = fetch_sheet_first_cell(SHEET_ID)
        logger.info("Got room link: %s", room_link)

        news_content = fetch_latest_news(NEWS_KEY)
        logger.info("Fetched news: %s", news_content.splitlines()[0] if news_content else "<none>")

        prompt = build_prompt_and_payload(news_content, room_link)
        final_text = call_gemini(GEMINI_KEY, prompt)
        if not final_text:
            raise ValueError("Gemini returned empty analysis text")
        logger.info("Received analysis text from Gemini (len=%d)", len(final_text))

        post_body = final_text + "\n\n" + f"ลิงก์ห้องสนทนา: {room_link}\n(ห้องสนทนานี้รองรับการแปลทุกภาษา)"

        # 1) Try anonymous paste sites (no token)
        for fn in (post_nekobin, post_hastebin, post_pasters, post_0x0st, post_ixio):
            try:
                url = fn(post_body)
                if url:
                    print(f"🚀 โพสต์สำเร็จที่เว็บบอร์ด/paste: {url}")
                    return
            except Exception:
                continue

        # 2) Try token/webhook targets
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            res = post_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, post_body)
            if res:
                print(f"🚀 โพสต์สำเร็จที่ Telegram: {res}")
                return

        if MASTODON_BASE_URL and MASTODON_TOKEN:
            res = post_to_mastodon(MASTODON_BASE_URL, MASTODON_TOKEN, post_body)
            if res:
                print(f"🚀 โพสต์สำเร็จที่ Mastodon: {res}")
                return

        if DISCORD_WEBHOOK_URL:
            res = post_to_discord(DISCORD_WEBHOOK_URL, post_body)
            if res:
                print(f"🚀 โพสต์สำเร็จที่ Discord (webhook)")
                return

        logger.warning("No posting channel succeeded.")
        print("⚠️ โพสต์ไม่สำเร็จที่ทุกบริการ — ตรวจสอบว่าเว็บไซต์อนุญาตโพสต์ anonymous หรือว่ามีปัญหาเครือข่าย")

    except Exception as e:
        logger.exception("Manus mission failed")
        print(f"❌ ระบบขัดข้อง: {e}")

if __name__ == "__main__":
    manus_mission()        full_post = final_content + footer
        
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
