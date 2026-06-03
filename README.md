# KAKM

Kerzz Akıllı Karlılık Motoru. POS verisinden restoranın finansal sağlığını okuyan bir analitik motor önerisidir.

Bu repo, Kerzz POS şirketine stajyer başvurum kapsamında geliştirdiğim projenin tamamını içermekte. Üç ayrı klasör, üç farklı katmandan oluşmaktadır.

## Neden?

Restoranların büyük çoğunluğu ilk üç yılda kapanıyor ve sebep çoğu zaman "kötü yemek" değil, finansal körlük. Kasada her gün ne sattığını gören işletmeci, "bu ay kâr ediyor muyum?" sorusunun cevabını ay sonu muhasebeciden öğreniyor. Genelde geç oluyor.

Kerzz POS'un elinde bu sorunu çözecek tüm veri var. Eksik olan, onu karar diline çeviren katman. KAKM bu katmanı kurmaya çalışıyor.


## Ne yapıyor?

Dört modülün her biri restoran finansının bir tarafını okur.

Menü Mühendisliği. Hangi ürün gerçekten kazandırıyor?

COGS Anomali Tespiti. Sessiz finansal sızıntı nerede?

Nakit Akışı Tahmini. Kasanın yarın boş olmayacağından emin miyim?

Şube Karşılaştırma. Hangi şubeye odaklanmalıyım?

Dört modülün üzerinde tek bir özet. 0 ile 100 arası finansal sağlık skoru. Bankaların kredi skoru mantığı, restoran finansına uyarlanmış.


## Hızlı başlangıç

İki klasör için ayrı kurulum gerekiyor. API ve analytics paylaşımlı bir veritabanı kullanıyor. api/init_db.py çalıştırılınca ikisi de hazır oluyor.

### 1. API'yi ayağa kaldırmanız için;

```bash
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload
```

Sonra http://localhost:8000/docs adresinde Swagger UI açılır.

### 2. Analitik motoru çalıştırmanız için;

```bash
cd ../analytics
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
jupyter notebook demo.ipynb
```

### 3. Dashboard'u açmak için;

```bash
open dashboard/index.html
```

Dashboard çift tıklayarak da açılır. İnternet bağlantısı veya sunucu gerektirmiyor. Tüm veri ve grafikler dosyanın içinde.


## Teknoloji;

Backend. Python 3.10 ve üstü, FastAPI, SQLite.

Analitik. pandas, NumPy, scikit-learn (Isolation Forest), matplotlib.

Görsel. HTML ve Chart.js. Tek dosya, bağımlılıksız.


## Repo yapısı detay

Her klasörün kendi README'si var, oradan daha derine inebilirsiniz.

api klasörü. REST endpoint'leri, veri modeli, mimari notlar.

analytics klasörü. Modül algoritmaları, Jupyter notebook.

dashboard klasörü. HTML demo.

---

Geliştiren. [Nilsu Serbest]. Mayıs 2026.

İletişim. [nilsu3serbest@gmail.com]. 
