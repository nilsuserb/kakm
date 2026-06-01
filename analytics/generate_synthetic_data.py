"""
generate_synthetic_data.py — Sentetik POS verisi üretici.

API katmanındaki init_db.py'nin bir kopyası — analytics paketi tek başına da
kullanılabilsin diye buraya alındı. Aynı veriyi üretir.

Çalıştırmak için:
    python generate_synthetic_data.py

Varsayılan: ../api/kakm_restoran.db konumunda oluşturur.
Bu sayede hem API hem analytics aynı veriyi paylaşır.
"""

import sys
from pathlib import Path

# api klasöründeki init_db.py'yi çalıştır
api_dir = Path(__file__).parent.parent / "api"
init_script = api_dir / "init_db.py"

if not init_script.exists():
    print(f"Hata: {init_script} bulunamadı.")
    print("api klasörünün yanında olduğundan emin ol.")
    sys.exit(1)

# api klasörüne geç, scripti çalıştır
import os
os.chdir(api_dir)
exec(open(init_script).read())

print()
print(f"✓ Veri ../api/kakm_restoran.db konumunda hazır.")
print("  analytics modüllerini şimdi çalıştırabilirsin.")
