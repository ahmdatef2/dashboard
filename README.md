# لوحة المتابعة — YouTube Dashboard

لوحة متابعة شخصية لقنوات يوتيوب العربية، تتحدث تلقائياً كل ساعة عبر GitHub Actions.

## هيكل المشروع

```
dashboard-repo/
├── index.html              ← الصفحة الرئيسية
├── data/
│   └── feeds.json          ← بيانات الفيديوهات (تُحدَّث تلقائياً)
├── scripts/
│   └── fetch_rss.py        ← سكريبت جلب RSS
└── .github/workflows/
    └── fetch-rss.yml       ← GitHub Actions workflow
```

## خطوات الإعداد

### 1. رفع الملفات على GitHub
- أنشئ مستودعاً جديداً باسم `dashboard` (أو أي اسم تريد)
- ارفع جميع الملفات كما هي مع الحفاظ على هيكل المجلدات

### 2. تفعيل GitHub Pages
- اذهب إلى **Settings → Pages**
- اختر **Source: Deploy from a branch**
- اختر **Branch: main** والمجلد **/ (root)**
- احفظ — ستظهر رابط الصفحة خلال دقيقة

### 3. تشغيل أول تحديث يدوياً
- اذهب إلى **Actions → Fetch YouTube RSS Feeds**
- اضغط **Run workflow**
- انتظر دقيقة حتى ينتهي
- بعدها الصفحة ستعرض الفيديوهات 🎉

### 4. التحديث التلقائي
بعد ذلك الـ workflow يعمل تلقائياً **كل ساعة** ويحدّث `data/feeds.json`.

## إضافة قنوات جديدة
افتح `scripts/fetch_rss.py` وأضف القناة في قائمة `CHANNELS`:
```python
{"id": "UCxxxxxxxxxxxxxxxxx", "h": "handle_name", "n": "اسم القناة"},
```
ثم أضفها أيضاً في `SECTIONS` داخل `index.html`.
