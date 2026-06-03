import sqlite3
import random
from datetime import datetime, timedelta
import os

DB_PATH = "kakm_restoran.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE Subeler (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isim            TEXT NOT NULL,
    bolge           TEXT NOT NULL,
    acilis_tarihi   TEXT NOT NULL
);

CREATE TABLE Urunler (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isim            TEXT NOT NULL,
    kategori        TEXT NOT NULL,
    satis_fiyati    REAL NOT NULL,
    maliyet         REAL NOT NULL
);

CREATE TABLE Satislar (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sube_id         INTEGER NOT NULL,
    urun_id         INTEGER NOT NULL,
    tarih           TEXT NOT NULL,
    satilan_miktar  INTEGER NOT NULL,
    FOREIGN KEY (sube_id) REFERENCES Subeler(id),
    FOREIGN KEY (urun_id) REFERENCES Urunler(id)
);

CREATE TABLE Stok_Hareketleri (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sube_id             INTEGER NOT NULL,
    urun_id             INTEGER NOT NULL,
    tarih               TEXT NOT NULL,
    teorik_tuketim      REAL NOT NULL,
    gercek_tuketim      REAL NOT NULL,
    FOREIGN KEY (sube_id) REFERENCES Subeler(id),
    FOREIGN KEY (urun_id) REFERENCES Urunler(id)
);

CREATE TABLE Giderler (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sube_id         INTEGER NOT NULL,
    tarih           TEXT NOT NULL,
    kategori        TEXT NOT NULL,
    tutar           REAL NOT NULL,
    aciklama        TEXT,
    FOREIGN KEY (sube_id) REFERENCES Subeler(id)
);

CREATE INDEX idx_satislar_sube_tarih ON Satislar(sube_id, tarih);
CREATE INDEX idx_stok_sube_tarih ON Stok_Hareketleri(sube_id, tarih);
CREATE INDEX idx_giderler_sube_tarih ON Giderler(sube_id, tarih);
""")

subeler = [
    ("Kadıköy Merkez", "İstanbul Anadolu", "2019-03-15"),
    ("Bağdat Caddesi", "İstanbul Anadolu", "2020-09-01"),
    ("Nişantaşı",      "İstanbul Avrupa",  "2018-06-20"),
    ("Beşiktaş",       "İstanbul Avrupa",  "2021-02-10"),
    ("Ataşehir",       "İstanbul Anadolu", "2022-05-05"),
    ("Bakırköy",       "İstanbul Avrupa",  "2021-11-12"),
    ("Maslak",         "İstanbul Avrupa",  "2023-01-20"),
]
cur.executemany("INSERT INTO Subeler (isim, bolge, acilis_tarihi) VALUES (?, ?, ?)", subeler)

urunler = [
    ("Pad Thai",          "Ana Yemek", 185, 62),
    ("Tavuk Curry",       "Ana Yemek", 195, 71),
    ("Beef Noodle",       "Ana Yemek", 220, 95),
    ("Crispy Duck",       "Ana Yemek", 285, 124),
    ("Karides Wok",       "Ana Yemek", 245, 102),
    ("Mantar Risotto",    "Ana Yemek", 175, 142),
    ("Quinoa Bowl",       "Ana Yemek", 165, 128),
    ("Vegan Curry",       "Ana Yemek", 155, 121),
    ("Black Cod",         "Ana Yemek", 380, 145),
    ("Wagyu Bowl",        "Ana Yemek", 420, 168),
    ("Dim Sum",           "Başlangıç", 95,  38),
    ("Spring Roll",       "Başlangıç", 75,  22),
    ("Mango Salad",       "Başlangıç", 85,  29),
    ("Edamame",           "Başlangıç", 55,  18),
    ("Truffle Ramen",     "Başlangıç", 145, 52),
    ("Çay",               "İçecek",    25,  4),
    ("Türk Kahvesi",      "İçecek",    45,  12),
    ("Su",                "İçecek",    15,  3),
    ("Asya Çayı",         "İçecek",    35,  8),
    ("Maden Suyu",        "İçecek",    25,  6),
    ("Mochi Ice Cream",   "Tatlı",     85,  28),
    ("Cheesecake",        "Tatlı",     95,  32),
    ("Tropikal Meyve",    "Tatlı",     65,  25),
]
cur.executemany("INSERT INTO Urunler (isim, kategori, satis_fiyati, maliyet) VALUES (?, ?, ?, ?)", urunler)

populerlik = {
    "Pad Thai":         18, "Tavuk Curry": 16, "Beef Noodle":  14,
    "Crispy Duck":      10, "Karides Wok": 13, "Mantar Risotto": 2,
    "Quinoa Bowl":       2, "Vegan Curry":  3, "Black Cod":     4,
    "Wagyu Bowl":        3, "Dim Sum":     22, "Spring Roll":  28,
    "Mango Salad":      15, "Edamame":     18, "Truffle Ramen": 3,
    "Çay":              45, "Türk Kahvesi":35, "Su":           60,
    "Asya Çayı":        20, "Maden Suyu":  25, "Mochi Ice Cream":12,
    "Cheesecake":       14, "Tropikal Meyve": 8
}

sube_carpani = {
    1: 1.0, 2: 1.95, 3: 1.85, 4: 1.15, 5: 0.85, 6: 0.65, 7: 0.50,
}

sube_fire_orani = {
    1: 0.048, 2: 0.022, 3: 0.025, 4: 0.060, 5: 0.078, 6: 0.092, 7: 0.105,
}

bugun = datetime(2026, 5, 27)
baslangic = bugun - timedelta(days=120)

cur.execute("SELECT id, isim FROM Urunler")
urun_id_map = {row[1]: row[0] for row in cur.fetchall()}

satis_rows = []
stok_rows = []

for sube_id in range(1, 8):
    carpan = sube_carpani[sube_id]
    fire = sube_fire_orani[sube_id]

    for gun_offset in range(120):
        tarih = (baslangic + timedelta(days=gun_offset)).strftime("%Y-%m-%d")
        gun_adi = (baslangic + timedelta(days=gun_offset)).weekday()

        hafta_carpani = 1.35 if gun_adi >= 5 else 1.0
        if gun_adi == 0:
            hafta_carpani = 0.75

        trend = 1.0 + (gun_offset / 120) * 0.08

        for urun_isim, ort_satis in populerlik.items():
            urun_id = urun_id_map[urun_isim]
            beklenen = ort_satis * carpan * hafta_carpani * trend
            satilan = max(0, int(random.gauss(beklenen, beklenen * 0.18)))

            if satilan > 0:
                satis_rows.append((sube_id, urun_id, tarih, satilan))

                urun_maliyet = next(u[3] for u in urunler if u[0] == urun_isim)
                teorik = satilan * urun_maliyet
                anomali_carpani = 1.0
                if gun_adi == 4 and urun_isim in ("Beef Noodle", "Crispy Duck") and sube_id == 1:
                    anomali_carpani = 2.5
                if sube_id in (6, 7) and urun_isim in ("Pad Thai", "Tavuk Curry", "Karides Wok"):
                    anomali_carpani = 1.6
                gercek = teorik * (1 + fire * anomali_carpani + random.gauss(0, 0.008))
                stok_rows.append((sube_id, urun_id, tarih, round(teorik, 2), round(gercek, 2)))

cur.executemany("INSERT INTO Satislar (sube_id, urun_id, tarih, satilan_miktar) VALUES (?, ?, ?, ?)", satis_rows)
cur.executemany("INSERT INTO Stok_Hareketleri (sube_id, urun_id, tarih, teorik_tuketim, gercek_tuketim) VALUES (?, ?, ?, ?, ?)", stok_rows)

gider_rows = []

for sube_id in range(1, 8):
    carpan = sube_carpani[sube_id]
    for gun_offset in range(0, 30):
        tarih = (bugun + timedelta(days=gun_offset)).strftime("%Y-%m-%d")
        gun = (bugun + timedelta(days=gun_offset)).day

        if gun == 28:
            gider_rows.append((sube_id, tarih, "personel", round(180000 * carpan, 2), "Aylık personel bordrosu"))
        if gun == 5:
            gider_rows.append((sube_id, tarih, "kira", round(85000 * carpan, 2), "Aylık kirs"))
        if gun == 26:
            gider_rows.append((sube_id, tarih, "vergi", round(45000 * carpan, 2), "KDV beyanı"))
        if gun_offset % 7 == 3:
            gider_rows.append((sube_id, tarih, "tedarikci", round(random.uniform(35000, 55000) * carpan, 2), "Haftalık tedarikçi ödemesi"))
        if gun == 15:
            gider_rows.append((sube_id, tarih, "fatura", round(28000 * carpan, 2), "Elektrik, su, doğalgaz"))

cur.executemany("INSERT INTO Giderler (sube_id, tarih, kategori, tutar, aciklama) VALUES (?, ?, ?, ?, ?)", gider_rows)

conn.commit()
conn.close()
print(f"{DB_PATH} hazır.")