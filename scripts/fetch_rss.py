#!/usr/bin/env python3
"""
fetch_rss.py
يجلب RSS لكل قنوات اليوتيوب ويحفظها في data/feeds.json
يعمل تلقائياً كل ساعة عبر GitHub Actions
"""

import json
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
from datetime import datetime, timezone
import os

# ── قائمة القنوات (نفس SECTIONS في الصفحة) ──
CHANNELS = [
  # عالم التقنية
  {"id": "UCMvdDpKRU_-ZmSz9F1lKOVA", "h": "dr_hebaahmed",                 "n": "د. هبة أحمد"},
  {"id": "UC2jjW7c63dqOPkfMm3P-u3w", "h": "every_day_a_new_website",      "n": "موقع كل يوم"},
  {"id": "UCKD8vOz3maRPyLAbMXhr-Pw", "h": "infotech4you_Marwasoliman",    "n": "مروة سليمان"},
  {"id": "UCSRy-3lglM2QKJ_xF2zuPlQ", "h": "AbdellatifSaidA",              "n": "عبداللطيف سعيد"},
  {"id": "UC81Ks7DR9JFgZc14nmZ07EA", "h": "AMRSALEM800",                  "n": "عمرو سالم"},
  {"id": "UC9ocsRoOwj9tkAQNfUt8ZJg", "h": "PythonArab",                   "n": "بايثون عربي"},
  {"id": "UCSNkfKl4cU-55Nm-ovsvOHQ", "h": "elzerowebschool",              "n": "Elzero Web School"},
  {"id": "UCGrVvqu8PlVv0wPqA5kgY8A", "h": "ArabicArtificialIntelligence", "n": "الذكاء الاصطناعي العربي"},
  {"id": "UCSXcmF4Gxl6Hc-m6cHYD_Vg", "h": "MohamedAnsary",               "n": "محمد أنصاري"},
  {"id": "UCDqp23rTdCo_tXsuHLYF47Q", "h": "ArabianAiSchool",              "n": "Arabian AI School"},
  {"id": "UCz0N3nKrJiDhNdKQvM6r93w", "h": "ryan.academy",                 "n": "Ryan Academy"},
  {"id": "UCXVSIaWCZBxqZ5eCxwIqRGw", "h": "TechnoFlashAITech",            "n": "TechnoFlash AI"},
  # عالم الكتب
  {"id": "UC16aC4Jti6tYAi0LuXmu-9w", "h": "KhairJaleesBook",              "n": "خير جليس"},
  {"id": "UCu1NJiJlhrhmF5ZgT-0yWdA", "h": "Jeelyaqraa",                   "n": "جيل يقرأ"},
  {"id": "UCtUor2SqesPS3b_SMFtLT_w", "h": "a5drcom",                      "n": "أخضر"},
  {"id": "UCUjRjJ1-h3oUx40gf2tuh3w", "h": "Sha5bata",                     "n": "شخبطة"},
  {"id": "UChbuH4HULlesX_rzlozkT6Q", "h": "AliMuhammadAli",               "n": "علي محمد علي"},
  {"id": "UCJlu6BjPWHZhzuCc0zVME0Q", "h": "Dupamicaffeine",               "n": "دوباميكافيين"},
  # الوثائقية
  {"id": "UC0LSnqrwqtMwl2YwfUpO66g", "h": "aljazeeradocumentary",         "n": "الجزيرة الوثائقية"},
  {"id": "UCArK7aSQ68vRCiJY2m7spkA", "h": "AsharqDoc",                    "n": "الشرق الوثائقية"},
  {"id": "UCLiTe0aOHShx7hXGyqZ9UIw", "h": "natgeoabudhabime",             "n": "ناشيونال جيوغرافيك"},
  {"id": "UCET6sWl4Xcu-U8Ka9PJPrwA", "h": "dwdocarabia",                  "n": "DW عربية وثائقي"},
]

NS = {"atom": "http://www.w3.org/2005/Atom",
      "yt":   "http://www.youtube.com/xml/schemas/2015",
      "media":"http://search.yahoo.com/mrss/"}

def fetch_channel(ch):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
    except Exception as e:
        print(f"  ✗ {ch['n']}: {e}")
        return None

    try:
        root = ET.fromstring(raw)
        title_el = root.find("atom:title", NS)
        feed_title = title_el.text if title_el is not None else ch["n"]

        items = []
        for entry in root.findall("atom:entry", NS)[:3]:
            vid_id_el = entry.find("yt:videoId", NS)
            title_e   = entry.find("atom:title", NS)
            pub_e     = entry.find("atom:published", NS)
            if vid_id_el is None:
                continue
            vid = vid_id_el.text
            items.append({
                "title":   title_e.text if title_e is not None else "",
                "link":    f"https://www.youtube.com/watch?v={vid}",
                "videoId": vid,
                "pubDate": pub_e.text if pub_e is not None else "",
            })

        print(f"  ✓ {feed_title} — {len(items)} فيديوهات")
        return {"title": feed_title, "items": items}

    except Exception as e:
        print(f"  ✗ {ch['n']} (parse error): {e}")
        return None


def main():
    print(f"\n{'='*50}")
    print(f"بدء الجلب — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")

    results = {}
    for ch in CHANNELS:
        result = fetch_channel(ch)
        results[ch["id"]] = {
            "handle":    ch["h"],
            "name":      ch["n"],
            "feedTitle": result["title"] if result else ch["n"],
            "items":     result["items"] if result else [],
            "ok":        result is not None,
        }

    # حفظ النتائج
    os.makedirs("data", exist_ok=True)
    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "channels": results,
    }
    with open("data/feeds.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    ok  = sum(1 for v in results.values() if v["ok"])
    err = len(results) - ok
    print(f"\n{'='*50}")
    print(f"✓ نجح: {ok} | ✗ فشل: {err} | المجموع: {len(results)}")
    print(f"تم الحفظ في data/feeds.json")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
