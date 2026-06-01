# KAKM API

Kerzz POS şirketine stajyer başvurum kapsamında geliştirdiğim KAKM (Kerzz Akıllı
Karlılık Motoru) projesinin backend katmanı. POS verisinden restoranın finansal
sağlığını okuyan bir analitik motor; bu repo onun REST API tarafını içeriyor.

Proje üç parçadan oluşuyor — backend (burası), HTML dashboard ve Python analitik
çekirdek motoru. Üçü bir araya gelince Kerzz POS üzerine kurulu bir karar destek
sistemi çıkıyor.


## Neden yaptım?

Restoranların büyük çoğunluğu ilk üç yılda kapanıyor ve sebep çoğu zaman
"kötü yemek" değil, finansal körlük. Kasada her gün ne sattığını gören
işletmeci, "bu ay kâr ediyor muyum" sorusunun cevabını ay sonu muhasebeciden
öğreniyor — bu da çoğu zaman geç oluyor. Kerzz POS'un elinde bu sorunu
çözecek tüm veri zaten var. Eksik olan onu karar diline çeviren katman.
KAKM bu katmanı kurmaya çalışıyor.


## Hızlı başlangıç

```bash
git clone https://github.com/[kullanıcı-adın]/kakm-api.git
cd kakm-api
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload
```

Bu kadar. Harici servise (PostgreSQL, Redis, vs.) ihtiyaç yok, ortam değişkeni
ayarlamak gerekmiyor. Yaklaşık yarım dakikada `http://localhost:8000/docs`
adresinde Swagger UI açılıyor olacak.


## Endpoint'ler

| Method | Path | Ne yapar |
|---|---|---|
| GET | `/` | API meta bilgisi |
| GET | `/subeler` | Tüm şubelerin özet skor listesi |
| GET | `/menu-analizi/{sube_id}` | Menü mühendisliği matrisi (Şampiyon / Lokomotif / Gizli Cevher / Zayıf Halka) |
| GET | `/finansal-skor/{sube_id}` | 5 bileşenli ağırlıklı sağlık skoru |
| GET | `/cogs-anomali/{sube_id}?esik_yuzde=5` | Stok sapma + anomali tespiti |
| GET | `/nakit-akisi/{sube_id}?gun=14` | P10/P50/P90 nakit akışı tahmini |


## Örnek çıktı

`GET /finansal-skor/1`:

```json
{
  "sube": { "isim": "Kadıköy Merkez", ... },
  "skor": 63,
  "etiket": "İzlenmeli",
  "bilesenler": {
    "brut_kar_marji":      100.0,
    "stok_devir_hizi":     38.6,
    "personel_verimi":     27.5,
    "cogs_sapma_sagligi":  76.2,
    ...
  },
  "ham_metrikler": {
    "gunluk_ortalama_ciro": 36506.5,
    "brut_kar_marji":       63.51,
    "cogs_sapma_yuzde":     4.97
  }
}
```

Skor 0–100 arası. 80+ sağlıklı, 60–79 izlenmeli, 40–59 riskli, 40 altı kriz.


## Veritabanı

Beş tablo, klasik bir POS verisinin sadeleştirilmiş hali: