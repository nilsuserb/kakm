# KAKM API

KAKM'nin backend tarafıdır. FastAPI ile yazılmış REST API, SQLite üzerinde çalışıyor.

## Kurulum

```bash
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload
```

http://localhost:8000/docs adresinde Swagger UI ile endpoint'leri deneyebilirsiniz 

## Endpoint'ler

GET / API bilgisi

GET /subeler Tüm şubelerin skor listesi

GET /menu-analizi/{sube_id} Menü mühendisliği matrisi

GET /finansal-skor/{sube_id} Sağlık skoru ve bileşenleri

GET /cogs-anomali/{sube_id} Stok sapma analizi

GET /nakit-akisi/{sube_id} 14 günlük nakit akışı tahmini

## Veri

5 tablo oluşturdum: Subeler, Urunler, Satislar, Stok_Hareketleri, Giderler.

init_db.py çalıştırıldığında 7 şube, 23 ürün ve yaklaşık 19.000 satış kaydı oluşuyor. Hepsi sentetik verilerden oluşmaktadır 
