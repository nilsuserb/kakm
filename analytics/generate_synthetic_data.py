"""
generate_synthetic_data.py — Sentetik POS verisi üretici.

API katmanındaki init_db.py'nin bir kopyasıdır analytics paketi tek başına da
kullanılabilsin diye buraya aldım. Aynı veriyi üretiyor

Çalıştırmak için:
    python generate_synthetic_data.py

Varsayılan: ../api/kakm_restoran.db konumunda oluşturur.
Bu sayede hem API hem analytics aynı veriyi paylaşırız 
"""

import sys
from pathlib import Path

api_dir = Path(__file__).parent.parent / "api"
init_script = api_dir / "init_db.py"

if not init_script.exists():
    print(f"Hata: {init_script} bulunamadı.")
    print("api klasörünün yanında olduğundan emin ol.")
    sys.exit(1)


import os
os.chdir(api_dir)
exec(open(init_script).read())

print()
print(f"✓ Veri ../api/kakm_restoran.db konumunda hazır.")
print("  analytics modüllerini şimdi çalıştırabilirsin.")
