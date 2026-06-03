# KAKM Analytics

KAKM projesinin analitik çekirdeği. Pandas + scikit-learn ile yazılmış,
restoran POS verisinden finansal kararları çıkaran dört modülü içeriyor.

API katmanı (`../api/`) bu motorların basitleştirilmiş bir REST sürümünü
sunuyor. Burası işin "beyni" — algoritmaların açık, görselleştirmelerin
matplotlib ile yapıldığı, Jupyter üzerinden adım adım gezilebilen sürüm.


## Hızlı başlangıç

```bash
pip install -r requirements.txt

# Veri yoksa üretmek için;
python generate_synthetic_data.py

# Jupyter notebook ile interaktif gezmeniz için;
jupyter notebook demo.ipynb
# Python 
python menu_engineering.py
python cogs_anomaly.py
python cash_flow_forecast.py
python health_score.py
```


## Modüller

 Dosya  Ne yapar 
 
 `data_loader.py`  SQLite DB'den pandas DataFrame'lerine veri yükler 
 `menu_engineering.py` Kasavana-Smith menü mühendisliği matrisi + scatter plot 
 `cogs_anomaly.py`  Eşik bazlı + Isolation Forest ile anomali tespiti |
 `cash_flow_forecast.py` |Monte Carlo simülasyonu ile P10/P50/P90 nakit akışı tahmini 
 `health_score.py` 7 bileşenli ağırlıklı finansal sağlık skoru + radar/bar chart 
 `demo.ipynb` Tüm modülleri birleştiren çalıştırılabilir notebook 


## Modüllerin teknik özeti

**Menü Mühendisliği** — Ürünleri popülerlik × katkı marjı eksenlerinde 4 kadrana
ayırır. Eşik olarak medyan kullanılır (uç değerlere karşı sağlam).
Çıktı: DataFrame + scatter plot.

**COGS Anomali** — İki yöntem birlikte:
*Eşik bazlı:* %5'in üstünde sapma → bayrak
*Isolation Forest:* Bağlamsal anomaliler (örneğin Cuma akşamı Beef Noodle'da
%12 sapma — diğer Cumalarda yok) yakalanır.

**Nakit Akışı** — 60 günlük geçmişten haftalık desen çıkarılır, 1000 Monte
Carlo senaryosu üretilir, her gün için P10/P50/P90 yüzdelikleri hesaplanır.
Yaklaşan giderler (maaş, kira, vergi) takvimi entegredir.

**Sağlık Skoru** — 7 bileşen, ağırlıklı toplam, 0-100 ölçeği. Skor bandları:
80+ Sağlıklı, 60-79 İzlenmeli, 40-59 Riskli, 0-39 Kriz.


## Veri kaynağı

`../api/kakm_restoran.db` — api klasöründeki ortak SQLite veritabanını
kullanıyor. Bu sayede aynı veri hem REST API'de hem analitik modüllerde
tutarlı şekilde işleniyor.

DB yoksa `python generate_synthetic_data.py` üretebilir.

