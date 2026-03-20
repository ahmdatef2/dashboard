#!/usr/bin/env python3
"""
notify.py
يقرأ feeds.json ويرسل إشعارات تيليجرام للفيديوهات الجديدة مع تلخيص Gemini
"""

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

# ── المفاتيح من GitHub Secrets ──
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

FEEDS_FILE = "data/feeds.json"
SENT_FILE  = "data/sent.json"

# ── قراءة الملفات ──
def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── تلخيص Gemini مع رابط يوتيوب مباشرة ──
def summarize_with_gemini(title, video_url):
    prompt = f"""أنت مساعد متخصص في تلخيص محتوى الفيديوهات.
شاهد هذا الفيديو ولخّصه بالعربية في 5-7 نقاط واضحة ومفيدة.
اكتب الملخص بالعربية فقط بصيغة نقاط."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps({
        "contents": [{
            "parts": [
                {
                    "file_data": {
                        "mime_type": "video/mp4",
                        "file_uri": video_url
                    }
                },
                {
                    "text": prompt
                }
            ]
        }]
    }).encode("utf-8")

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"  ⚠️ خطأ في Gemini (محاولة {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(10)

    # fallback: تلخيص بالعنوان فقط
    return summarize_by_title(title)

def summarize_by_title(title):
    prompt = f"""أنت مساعد متخصص في تلخيص محتوى الفيديوهات.
بناءً على عنوان الفيديو فقط، اكتب وصفاً مختصراً بالعربية لما يُرجَّح أن يتناوله هذا الفيديو.
عنوان الفيديو: {title}
اكتب الوصف بالعربية في 3-4 جمل."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  ⚠️ خطأ في Gemini fallback: {e}")
        return "⚠️ تعذّر إنشاء الملخص."

# ── إرسال رسالة تيليجرام ──
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result.get("ok", False)
    except Exception as e:
        print(f"  ✗ خطأ في تيليجرام: {e}")
        return False

# ── البرنامج الرئيسي ──
def main():
    print(f"\n{'='*50}")
    print(f"بدء الإشعارات — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")

    feeds = load_json(FEEDS_FILE, {})
    sent  = load_json(SENT_FILE, {"videos": []})
    sent_ids = set(sent["videos"])

    channels = feeds.get("channels", {})
    new_count = 0

    for ch_id, ch_data in channels.items():
        items = ch_data.get("items", [])
        ch_name = ch_data.get("name", "")

        for item in items:
            video_id = item.get("videoId", "")
            if not video_id or video_id in sent_ids:
                continue

            title     = item.get("title", "")
            link      = item.get("link", "")
            print(f"\n📹 فيديو جديد: {title}")
            print(f"   القناة: {ch_name}")

            # تلخيص Gemini برابط الفيديو مباشرة
            print("  🤖 جاري التلخيص...")
            summary = summarize_with_gemini(title, link)

            # بناء الرسالة
            message = (
                f"📺 <b>{ch_name}</b>\n"
                f"🎬 <b>{title}</b>\n\n"
                f"✅ ملخص الفيديو:\n"
                f"{summary}\n\n"
                f"🔗 <a href='{link}'>مشاهدة الفيديو</a>"
            )

            # إرسال تيليجرام
            if send_telegram(message):
                sent_ids.add(video_id)
                new_count += 1
                print(f"  ✓ تم الإرسال")
            else:
                print(f"  ✗ فشل الإرسال")

            # انتظار بين الفيديوهات
            time.sleep(5)

    # حفظ الملف المحدّث
    sent["videos"] = list(sent_ids)
    sent["updated"] = datetime.now(timezone.utc).isoformat()
    save_json(SENT_FILE, sent)

    print(f"\n{'='*50}")
    print(f"✓ فيديوهات جديدة أُرسلت: {new_count}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
