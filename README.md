# KAKM

Kerzz Akıllı Karlılık Motoru. POS verisinden restoranın finansal durumunu okuyan bir analitik motor tasarımıdır

Kerzz POS staj başvurum için hazırladığım proje. Üç klasör içermektedir

## Modüller

Menü mühendisliği. Hangi ürün kazandırıyor, hangisi yer kaplıyor?

COGS anomali tespiti. Stoktan beklenenden fazla düşen ne var?

Nakit akışı tahmini. 14 gün sonra kasa ne durumda olur?

Şube karşılaştırma. Şubeler arasında nereye odaklanmalı?

Dördünün üstünde tek bir özet var. 0-100 arası finansal sağlık skoru.

## Çalıştırmak için

API:

```bash
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload
```

Analytics:

```bash
cd analytics
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
jupyter notebook demo.ipynb
```

Dashboard:

```bash
open dashboard/index.html
```

Detaylar her klasörün kendi readme'sinde yer almaktadır.



Hazırlayan: Nilsu Serbest  - nilsu3serbest@gmail.com
