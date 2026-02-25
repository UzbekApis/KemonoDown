# Kemono WebApp

Kemono WebApp - bu Termux muhitida ishlaydigan Python asosidagi web ilova bo'lib, Kemono.cr platformasidan media kontentlarni yuklab olish, qidirish va boshqarish imkonini beradi.

## Xususiyatlar

- 🔗 URL orqali to'g'ridan-to'g'ri yuklab olish
- 📋 **Multi-URL yuklab olish** - bir vaqtning o'zida bir nechta URL'larni yuklab olish
- 🔍 Artist va post qidirish (Levenshtein distance algoritmi)
- 📚 Kutubxona tizimi (yuklab olingan fayllarni boshqarish)
- ⏸️ Yuklab olishni to'xtatish/davom ettirish/bekor qilish
- 📊 **Active Downloads panel** - barcha yuklanayotgan fayllarni real-time ko'rish va boshqarish
- 🎨 Fayl turi filtrlash (rasmlar, videolar, arxivlar, audio)
- 📱 Responsive web interfeys (mobil qurilmalar uchun)
- 🌙 Dark/Light mode
- 🌐 Ko'p tillilik (O'zbek, Ingliz)

## Texnologiyalar

- **Backend**: Flask 2.3+ (Python web framework)
- **API Client**: requests + cloudscraper
- **Database**: SQLite3
- **Frontend**: HTML5 + CSS3 + JavaScript
- **UI Framework**: Bootstrap 5
- **Image Processing**: Pillow

## O'rnatish (Termux)

### Talablar

- Android 7.0 yoki yuqori
- Termux ilovasi ([F-Droid](https://f-droid.org/packages/com.termux/) yoki [GitHub](https://github.com/termux/termux-app/releases))
- Kamida 500MB bo'sh xotira

### Avtomatik o'rnatish

1. Termux ni oching va repositoriyani klonlang:

```bash
pkg install git -y
git clone <repository-url>
cd kemono-webapp
```

2. O'rnatish skriptini ishga tushiring:

```bash
bash install.sh
```

Skript quyidagi amallarni bajaradi:
- Termux paketlarini yangilaydi
- Python va kerakli kutubxonalarni o'rnatadi
- Ilova kataloglarini yaratadi
- Ma'lumotlar bazasini initsializatsiya qiladi
- Standart konfiguratsiyani yaratadi

### Qo'lda o'rnatish

Agar avtomatik o'rnatish ishlamasa, quyidagi qadamlarni bajaring:

1. Paketlarni yangilang:

```bash
pkg update && pkg upgrade -y
```

2. Python va kerakli paketlarni o'rnating:

```bash
pkg install python libxml2 libxslt libjpeg-turbo -y
```

3. Python kutubxonalarini o'rnating:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Kataloglarni yarating:

```bash
mkdir -p data data/cache downloads library library/thumbs templates/errors
```

5. Ma'lumotlar bazasini initsializatsiya qiling:

```bash
python -c "from models.database import init_db; init_db()"
```

6. Konfiguratsiyani yarating:

```bash
python -c "from config import create_default_config; create_default_config()"
```

## Ishga tushirish

### Oddiy usul

```bash
bash run.sh
```

### Qo'lda ishga tushirish

```bash
python app.py
```

Server ishga tushgandan keyin, brauzeringizda quyidagi manzilni oching:

```
http://localhost:5000
```

Agar boshqa qurilmadan kirmoqchi bo'lsangiz, Termux qurilmasining IP manzilini aniqlang:

```bash
ifconfig
```

Keyin boshqa qurilmadan:

```
http://<termux-device-ip>:5000
```

## Foydalanish

### 1. URL orqali yuklab olish

1. "Download" sahifasiga o'ting
2. Kemono URL manzilini kiriting:
   - Artist profili: `https://kemono.cr/patreon/user/12345`
   - Individual post: `https://kemono.cr/patreon/user/12345/post/67890`
3. Fayl turini tanlang (ixtiyoriy)
4. "Start Download" tugmasini bosing
5. Progress barni kuzatib boring

### 2. Artist qidirish

1. "Search" sahifasiga o'ting
2. Artist nomini kiriting
3. Qidiruv natijalaridan kerakli artistni tanlang
4. Artist profilidan postlarni ko'ring va yuklab oling

### 3. Kutubxonani ko'rish

1. "Library" sahifasiga o'ting
2. Yuklab olingan fayllarni ko'ring
3. Artist yoki post bo'yicha filtrlang
4. Faylni ochish yoki o'chirish uchun ustiga bosing

### 4. Sozlamalar

1. "Settings" sahifasiga o'ting
2. Quyidagi sozlamalarni o'zgartiring:
   - Yuklab olish katalogi
   - Maksimal parallel yuklab olishlar soni
   - API base URL
   - Tema (Dark/Light)
   - Til (O'zbek/Ingliz)

## API Endpoints

### Download Endpoints

- `GET /download` - Yuklab olish sahifasi
- `POST /download/start` - Yuklab olishni boshlash
- `POST /download/pause/<task_id>` - Yuklab olishni to'xtatish
- `POST /download/resume/<task_id>` - Yuklab olishni davom ettirish
- `POST /download/cancel/<task_id>` - Yuklab olishni bekor qilish

### Search Endpoints

- `GET /search` - Qidiruv sahifasi
- `POST /search/artist` - Artist qidirish
- `POST /search/post` - Post qidirish

### Library Endpoints

- `GET /library` - Kutubxona sahifasi
- `GET /library/filter` - Fayllarni filtrlash
- `DELETE /library/file/<file_id>` - Faylni o'chirish

### API Endpoints (JSON)

- `GET /api/progress/<task_id>` - Yuklab olish progressi
- `GET /api/library/scan` - Kutubxonani skanerlash
- `POST /api/settings` - Sozlamalarni saqlash
- `GET /api/downloads` - Barcha yuklab olishlar ro'yxati

## Konfiguratsiya

Konfiguratsiya fayli: `data/config.json`

```json
{
  "api_base_url": "https://kemono.cr/api/",
  "download_path": "./downloads",
  "library_path": "./library",
  "max_concurrent_downloads": 3,
  "theme": "dark",
  "language": "uz",
  "cache_ttl": 300,
  "thumbnail_size": [200, 200],
  "flask_host": "0.0.0.0",
  "flask_port": 5000,
  "flask_debug": true
}
```

### Konfiguratsiya parametrlari

- `api_base_url` - Kemono API manzili
- `download_path` - Yuklab olingan fayllar katalogi
- `library_path` - Kutubxona katalogi
- `max_concurrent_downloads` - Maksimal parallel yuklab olishlar soni
- `theme` - Interfeys temasi (`dark` yoki `light`)
- `language` - Til (`uz` yoki `en`)
- `cache_ttl` - Cache muddati (soniyalarda)
- `thumbnail_size` - Thumbnail o'lchami (pikselda)
- `flask_host` - Flask server host manzili
- `flask_port` - Flask server porti
- `flask_debug` - Debug rejimi

## Muammolarni hal qilish

### Python topilmadi

```bash
pkg install python -y
```

### Pip paketlari o'rnatilmayapti

```bash
pip install --upgrade pip
pip install --upgrade setuptools wheel
```

### Storage ruxsati yo'q

```bash
termux-setup-storage
```

Keyin Termux ga storage ruxsatini bering.

### Port band

Agar 5000 porti band bo'lsa, `data/config.json` faylida `flask_port` ni o'zgartiring:

```json
{
  "flask_port": 8080
}
```

### Ma'lumotlar bazasi xatoligi

Ma'lumotlar bazasini qayta yarating:

```bash
rm data/webapp.db
python -c "from models.database import init_db; init_db()"
```

### Yuklab olish ishlamayapti

1. Internet ulanishini tekshiring
2. Kemono.cr saytining ishlayotganini tekshiring
3. URL manzilini to'g'ri kiritganingizni tekshiring
4. Loglarni ko'ring: `data/app.log`

**403 Forbidden xatosi:**
- Ilova avtomatik ravishda alternative domenlarni (kemono.su, kemono.party) sinab ko'radi
- Agar muammo davom etsa, VPN ishlatib ko'ring
- Biroz kutib qayta urinib ko'ring (rate limiting bo'lishi mumkin)
- Boshqa post URL'ini sinab ko'ring

### Xotira to'lgan

Eski yuklab olishlarni o'chiring:

```bash
rm -rf downloads/*
rm -rf library/thumbs/*
```

Yoki Library sahifasidan fayllarni o'chiring.

### Server ishga tushmayapti

1. Portni tekshiring:

```bash
netstat -tuln | grep 5000
```

2. Loglarni ko'ring:

```bash
tail -f data/app.log
```

3. Dependencies ni qayta o'rnating:

```bash
pip install -r requirements.txt --force-reinstall
```

## Xavfsizlik

- Ilova faqat localhost da ishlaydi (standart)
- Barcha foydalanuvchi kiritgan ma'lumotlar validatsiya qilinadi
- SQL injection va XSS hujumlaridan himoyalangan
- Fayllar xavfsiz kataloglarda saqlanadi

## Litsenziya

MIT License

## Muallif

Kemono WebApp - Termux uchun optimallashtirilgan

## Qo'llab-quvvatlash

Muammolar yoki savollar bo'lsa, GitHub Issues bo'limida xabar bering.

## Changelog

### v1.0.0 (2024)

- Dastlabki versiya
- URL orqali yuklab olish
- Artist va post qidirish
- Kutubxona tizimi
- Responsive web interfeys
- Dark/Light mode
- Ko'p tillilik

