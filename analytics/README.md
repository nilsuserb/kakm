# KAKM Analytics

KAKM'nin analitik tarafıdır.  pandas ve scikit-learn kullanıyor.

API ile aynı veritabanını paylaşıyor

## Kurulum

```bash
pip install -r requirements.txt
python generate_synthetic_data.py
jupyter notebook demo.ipynb
```

## Dosyalar

data_loader.py Veritabanından DataFrame'e veri yükler

menu_engineering.py Menü mühendisliği matrisi

cogs_anomaly.py Eşik bazlı ve Isolation Forest anomali tespiti

cash_flow_forecast.py Monte Carlo nakit akışı tahmini

health_score.py 7 bileşenli sağlık skoru

demo.ipynb Hepsini birleştiren notebook

## Komut satırından da çalışıyor

```bash
python menu_engineering.py
python cogs_anomaly.py
python cash_flow_forecast.py
python health_score.py
```