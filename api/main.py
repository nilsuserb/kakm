from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime, timedelta
import statistics

app = FastAPI(
    title="KAKM API",
    description="Kerzz Akıllı Karlılık Motoru — POS verisinden finansal sağlık analizi",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "kakm_restoran.db"
BUGUN = datetime(2026, 5, 27)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_sube_or_404(sube_id: int):
    conn = get_db()
    sube = conn.execute("SELECT * FROM Subeler WHERE id = ?", (sube_id,)).fetchone()
    conn.close()
    if not sube:
        raise HTTPException(status_code=404, detail=f"Şube #{sube_id} bulunamadı")
    return dict(sube)


@app.get("/")
def root():
    return {
        "isim": "KAKM API",
        "surum": "0.1.0",
        "tanim": "Kerzz Akıllı Karlılık Motoru — REST API",
        "dokuman": "/docs",
        "endpoints": [
            "/subeler",
            "/menu-analizi/{sube_id}",
            "/finansal-skor/{sube_id}",
            "/cogs-anomali/{sube_id}",
            "/nakit-akisi/{sube_id}?gun=14",
        ],
    }


@app.get("/subeler")
def tum_subeler():
    conn = get_db()
    subeler = [dict(r) for r in conn.execute("SELECT * FROM Subeler").fetchall()]

    son_30 = (BUGUN - timedelta(days=30)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    sonuc = []
    for s in subeler:
        row = conn.execute("""
            SELECT COALESCE(SUM(s.satilan_miktar * u.satis_fiyati), 0) AS toplam_ciro,
                   COUNT(DISTINCT s.tarih) AS gun_sayisi
            FROM Satislar s JOIN Urunler u ON s.urun_id = u.id
            WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
        """, (s["id"], son_30, bugun_str)).fetchone()

        toplam_ciro = row["toplam_ciro"]
        gun_sayisi = row["gun_sayisi"] or 1
        gunluk_ortalama = toplam_ciro / gun_sayisi if gun_sayisi else 0

        skor_detay = _finansal_skor_hesapla(s["id"], conn)
        sonuc.append({
            "id": s["id"],
            "isim": s["isim"],
            "bolge": s["bolge"],
            "skor": skor_detay["skor"],
            "skor_etiketi": skor_detay["etiket"],
            "son_30_gun_ciro": round(toplam_ciro, 2),
            "gunluk_ortalama_ciro": round(gunluk_ortalama, 2),
        })

    conn.close()
    sonuc.sort(key=lambda x: x["skor"], reverse=True)
    return {"sube_sayisi": len(sonuc), "subeler": sonuc}


@app.get("/menu-analizi/{sube_id}")
def menu_analizi(sube_id: int):
    sube = get_sube_or_404(sube_id)
    conn = get_db()

    son_90 = (BUGUN - timedelta(days=90)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    rows = conn.execute("""
        SELECT
            u.id,
            u.isim,
            u.kategori,
            u.satis_fiyati,
            u.maliyet,
            (u.satis_fiyati - u.maliyet) AS birim_kar,
            SUM(s.satilan_miktar) AS toplam_satis,
            SUM(s.satilan_miktar * (u.satis_fiyati - u.maliyet)) AS toplam_kar
        FROM Urunler u
        JOIN Satislar s ON u.id = s.urun_id
        WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
        GROUP BY u.id
    """, (sube_id, son_90, bugun_str)).fetchall()
    conn.close()

    if not rows:
        return {"mesaj": "Bu şube için satış verisi bulunamadı.", "sube": sube}

    urunler = [dict(r) for r in rows]

    satislar = [u["toplam_satis"] for u in urunler]
    karlar = [u["birim_kar"] for u in urunler]
    esik_satis = statistics.median(satislar)
    esik_kar = statistics.median(karlar)

    SINIF_BILGI = {
        "Şampiyon": {
            "aksiyon": "Menünün yıldızı. Görünürlüğünü artır, fotoğraflı menüye al, fiyata dokunma.",
            "renk": "yesil",
        },
        "Lokomotif": {
            "aksiyon": "Sürümden kazandırıyor. Tedarikçi pazarlığıyla maliyeti %5 düşürmek karı katlar.",
            "renk": "teal",
        },
        "Gizli Cevher": {
            "aksiyon": "Marj harika ama bilinmiyor. Garsona 'günün önerisi' olarak verilebilir.",
            "renk": "amber",
        },
        "Zayıf Halka": {
            "aksiyon": "Maliyetli ve satmıyor. Menüden çıkarmayı veya reçeteyi sadeleştirmeyi düşün.",
            "renk": "kirmizi",
        },
    }

    sayim = {"Şampiyon": 0, "Lokomotif": 0, "Gizli Cevher": 0, "Zayıf Halka": 0}

    for u in urunler:
        yuksek_satis = u["toplam_satis"] >= esik_satis
        yuksek_kar = u["birim_kar"] >= esik_kar
        if yuksek_satis and yuksek_kar:
            sinif = "Şampiyon"
        elif yuksek_satis and not yuksek_kar:
            sinif = "Lokomotif"
        elif not yuksek_satis and yuksek_kar:
            sinif = "Gizli Cevher"
        else:
            sinif = "Zayıf Halka"

        u["siniflandirma"] = sinif
        u["aksiyon_onerisi"] = SINIF_BILGI[sinif]["aksiyon"]
        u["renk"] = SINIF_BILGI[sinif]["renk"]
        u["toplam_kar"] = round(u["toplam_kar"], 2)
        sayim[sinif] += 1

    zayif_halkalar = sorted(
        [u for u in urunler if u["siniflandirma"] == "Zayıf Halka"],
        key=lambda x: x["toplam_satis"],
    )
    one_cikan_aksiyon = None
    if zayif_halkalar:
        z = zayif_halkalar[0]
        one_cikan_aksiyon = (
            f"'{z['isim']}' son 90 günde sadece {z['toplam_satis']} kez satıldı, "
            f"marj %{round(z['birim_kar'] / z['satis_fiyati'] * 100)}. Menüden çıkarmayı değerlendir."
        )

    return {
        "sube": sube,
        "tarih_araligi": f"{son_90} – {bugun_str}",
        "esikler": {
            "medyan_satis": esik_satis,
            "medyan_kar": round(esik_kar, 2),
        },
        "ozet": sayim,
        "one_cikan_aksiyon": one_cikan_aksiyon,
        "urunler": urunler,
    }


SKOR_AGIRLIKLARI = {
    "brut_kar_marji":      0.25,
    "stok_devir_hizi":     0.15,
    "personel_verimi":     0.15,
    "cogs_sapma_sagligi":  0.15,
    "ortalama_sepet":      0.10,
    "yogun_saat":          0.10,
    "atik_fire":           0.10,
}


def _finansal_skor_hesapla(sube_id: int, conn) -> dict:
    son_30 = (BUGUN - timedelta(days=30)).strftime("%Y-%m-%d")
    onceki_30 = (BUGUN - timedelta(days=60)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    row = conn.execute("""
        SELECT
            COALESCE(SUM(s.satilan_miktar * u.satis_fiyati), 0) AS ciro,
            COALESCE(SUM(s.satilan_miktar * u.maliyet), 0) AS maliyet,
            COUNT(DISTINCT s.tarih) AS gun_sayisi,
            COALESCE(SUM(s.satilan_miktar), 0) AS toplam_adet
        FROM Satislar s JOIN Urunler u ON s.urun_id = u.id
        WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
    """, (sube_id, son_30, bugun_str)).fetchone()
    ciro = row["ciro"] or 0
    maliyet = row["maliyet"] or 0
    gun_sayisi = row["gun_sayisi"] or 1
    toplam_adet = row["toplam_adet"] or 1

    brut_marj = (ciro - maliyet) / ciro if ciro else 0
    brut_marj_skor = max(0, min(100, (brut_marj - 0.10) / 0.35 * 100))

    stok_row = conn.execute("""
        SELECT COALESCE(AVG(teorik_tuketim), 0) AS ort_gunluk_tuketim
        FROM Stok_Hareketleri WHERE sube_id = ? AND tarih BETWEEN ? AND ?
    """, (sube_id, son_30, bugun_str)).fetchone()
    devir_skor = min(100, (stok_row["ort_gunluk_tuketim"] / 1500) * 100) if stok_row["ort_gunluk_tuketim"] else 0

    gunluk_ort_ciro = ciro / gun_sayisi
    personel_skor = max(0, min(100, (gunluk_ort_ciro - 20000) / 60000 * 100))

    cogs_row = conn.execute("""
        SELECT
            COALESCE(SUM(teorik_tuketim), 0) AS teorik,
            COALESCE(SUM(gercek_tuketim), 0) AS gercek
        FROM Stok_Hareketleri WHERE sube_id = ? AND tarih BETWEEN ? AND ?
    """, (sube_id, son_30, bugun_str)).fetchone()
    teorik = cogs_row["teorik"] or 1
    gercek = cogs_row["gercek"] or teorik
    sapma_orani = (gercek - teorik) / teorik
    cogs_skor = max(0, min(100, 100 - (sapma_orani - 0.02) * 800))

    ort_sepet = ciro / (toplam_adet / 2.5) if toplam_adet else 0
    sepet_skor = max(0, min(100, (ort_sepet - 100) / 280 * 100))

    onceki_ciro_row = conn.execute("""
        SELECT COALESCE(SUM(s.satilan_miktar * u.satis_fiyati), 0) AS ciro
        FROM Satislar s JOIN Urunler u ON s.urun_id = u.id
        WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
    """, (sube_id, onceki_30, son_30)).fetchone()
    onceki_ciro = onceki_ciro_row["ciro"] or 1
    buyume = (ciro - onceki_ciro) / onceki_ciro if onceki_ciro else 0
    yogun_skor = max(0, min(100, 60 + buyume * 200))

    atik_skor = max(0, min(100, 100 - sapma_orani * 600))

    bilesenler = {
        "brut_kar_marji":      round(brut_marj_skor, 1),
        "stok_devir_hizi":     round(devir_skor, 1),
        "personel_verimi":     round(personel_skor, 1),
        "cogs_sapma_sagligi":  round(cogs_skor, 1),
        "ortalama_sepet":      round(sepet_skor, 1),
        "yogun_saat":          round(yogun_skor, 1),
        "atik_fire":           round(atik_skor, 1),
    }

    skor = sum(bilesenler[k] * SKOR_AGIRLIKLARI[k] for k in SKOR_AGIRLIKLARI)
    skor = int(round(skor))

    if skor >= 80:
        etiket = "Sağlıklı"
    elif skor >= 60:
        etiket = "İzlenmeli"
    elif skor >= 40:
        etiket = "Riskli"
    else:
        etiket = "Kriz"

    return {
        "skor": skor,
        "etiket": etiket,
        "bilesenler": bilesenler,
        "ham_metrikler": {
            "gunluk_ortalama_ciro": round(gunluk_ort_ciro, 2),
            "brut_kar_marji": round(brut_marj * 100, 2),
            "cogs_sapma_yuzde": round(sapma_orani * 100, 2),
            "ortalama_sepet": round(ort_sepet, 2),
            "30_gun_buyume_yuzde": round(buyume * 100, 2),
        },
    }


@app.get("/finansal-skor/{sube_id}")
def finansal_skor(sube_id: int):
    sube = get_sube_or_404(sube_id)
    conn = get_db()
    detay = _finansal_skor_hesapla(sube_id, conn)
    conn.close()
    return {
        "sube": sube,
        "tarih": BUGUN.strftime("%Y-%m-%d"),
        "agirliklar": SKOR_AGIRLIKLARI,
        **detay,
    }


@app.get("/cogs-anomali/{sube_id}")
def cogs_anomali(sube_id: int, esik_yuzde: float = Query(5.0)):
    sube = get_sube_or_404(sube_id)
    conn = get_db()

    son_7 = (BUGUN - timedelta(days=7)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    rows = conn.execute("""
        SELECT
            u.id AS urun_id,
            u.isim,
            u.kategori,
            SUM(sh.teorik_tuketim) AS teorik,
            SUM(sh.gercek_tuketim) AS gercek,
            COUNT(*) AS gun_sayisi
        FROM Stok_Hareketleri sh
        JOIN Urunler u ON sh.urun_id = u.id
        WHERE sh.sube_id = ? AND sh.tarih BETWEEN ? AND ?
        GROUP BY u.id
        HAVING SUM(sh.teorik_tuketim) > 0
    """, (sube_id, son_7, bugun_str)).fetchall()
    conn.close()

    anomaliler = []
    toplam_kayip = 0

    for r in rows:
        teorik = r["teorik"]
        gercek = r["gercek"]
        sapma = gercek - teorik
        sapma_yuzde = (sapma / teorik) * 100 if teorik else 0
        if abs(sapma_yuzde) >= esik_yuzde:
            seviye = "yuksek" if abs(sapma_yuzde) >= 7 else "orta"
            anomaliler.append({
                "urun_id": r["urun_id"],
                "isim": r["isim"],
                "kategori": r["kategori"],
                "teorik_tuketim_tl": round(teorik, 2),
                "gercek_tuketim_tl": round(gercek, 2),
                "sapma_tl": round(sapma, 2),
                "sapma_yuzde": round(sapma_yuzde, 2),
                "seviye": seviye,
                "aciklama": (
                    f"Beklenen ₺{round(teorik, 0):.0f} · Gerçek ₺{round(gercek, 0):.0f} · "
                    f"Sapma %{round(sapma_yuzde, 1)}"
                ),
            })
            toplam_kayip += sapma

    anomaliler.sort(key=lambda x: abs(x["sapma_tl"]), reverse=True)

    return {
        "sube": sube,
        "tarih_araligi": f"{son_7} – {bugun_str}",
        "esik_yuzde": esik_yuzde,
        "anomali_sayisi": len(anomaliler),
        "toplam_haftalik_kayip_tl": round(toplam_kayip, 2),
        "anomaliler": anomaliler[:10],
    }


@app.get("/nakit-akisi/{sube_id}")
def nakit_akisi(sube_id: int, gun: int = Query(14, ge=1, le=30)):
    sube = get_sube_or_404(sube_id)
    conn = get_db()

    son_60 = (BUGUN - timedelta(days=60)).strftime("%Y-%m-%d")
    dun = (BUGUN - timedelta(days=1)).strftime("%Y-%m-%d")

    ciro_rows = conn.execute("""
        SELECT s.tarih, SUM(s.satilan_miktar * u.satis_fiyati) AS gunluk_ciro
        FROM Satislar s JOIN Urunler u ON s.urun_id = u.id
        WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
        GROUP BY s.tarih
        ORDER BY s.tarih
    """, (sube_id, son_60, dun)).fetchall()

    if not ciro_rows:
        conn.close()
        raise HTTPException(status_code=404, detail="Geçmiş satış verisi yetersiz")

    ciro_serisi = [r["gunluk_ciro"] for r in ciro_rows]
    ortalama_ciro = statistics.mean(ciro_serisi)
    std_ciro = statistics.stdev(ciro_serisi) if len(ciro_serisi) > 1 else ortalama_ciro * 0.15

    son_7 = (BUGUN - timedelta(days=7)).strftime("%Y-%m-%d")
    kasa_row = conn.execute("""
        SELECT COALESCE(SUM(s.satilan_miktar * (u.satis_fiyati - u.maliyet)), 0) AS kar
        FROM Satislar s JOIN Urunler u ON s.urun_id = u.id
        WHERE s.sube_id = ? AND s.tarih BETWEEN ? AND ?
    """, (sube_id, son_7, dun)).fetchone()
    mevcut_kasa = kasa_row["kar"]

    bitis = (BUGUN + timedelta(days=gun)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")
    giderler = conn.execute("""
        SELECT tarih, kategori, tutar, aciklama
        FROM Giderler
        WHERE sube_id = ? AND tarih BETWEEN ? AND ?
        ORDER BY tarih
    """, (sube_id, bugun_str, bitis)).fetchall()
    gider_listesi = [dict(g) for g in giderler]
    conn.close()

    gun_gider = {}
    for g in gider_listesi:
        gun_gider.setdefault(g["tarih"], 0)
        gun_gider[g["tarih"]] += g["tutar"]

    tahmin = []
    kasa_p10 = mevcut_kasa
    kasa_p50 = mevcut_kasa
    kasa_p90 = mevcut_kasa

    for i in range(gun + 1):
        tarih = BUGUN + timedelta(days=i)
        tarih_str = tarih.strftime("%Y-%m-%d")
        gun_adi = tarih.weekday()
        hafta_carpani = 1.35 if gun_adi >= 5 else (0.75 if gun_adi == 0 else 1.0)

        beklenen_ciro = ortalama_ciro * hafta_carpani
        beklenen_kar = beklenen_ciro * 0.50
        std_kar = beklenen_kar * 0.20

        if i > 0:
            kasa_p50 += beklenen_kar
            kasa_p10 += beklenen_kar - 1.28 * std_kar
            kasa_p90 += beklenen_kar + 1.28 * std_kar

        gun_gider_tutari = gun_gider.get(tarih_str, 0)
        kasa_p50 -= gun_gider_tutari
        kasa_p10 -= gun_gider_tutari
        kasa_p90 -= gun_gider_tutari

        tahmin.append({
            "tarih": tarih_str,
            "gun_no": i,
            "p10": round(kasa_p10, 2),
            "p50": round(kasa_p50, 2),
            "p90": round(kasa_p90, 2),
            "gider": round(gun_gider_tutari, 2),
        })

    neg_gun = next((t for t in tahmin if t["p10"] < 0), None)
    uyari = None
    if neg_gun:
        uyari = (
            f"{neg_gun['tarih']} tarihinde kötü senaryoda kasa negatife düşebilir "
            f"(P10: ₺{neg_gun['p10']:,.0f}). Yaklaşan büyük gider: "
            f"₺{neg_gun['gider']:,.0f}."
        )

    return {
        "sube": sube,
        "tahmin_gun_sayisi": gun,
        "mevcut_kasa_tahmini": round(mevcut_kasa, 2),
        "ortalama_gunluk_ciro": round(ortalama_ciro, 2),
        "uyari": uyari,
        "yaklasan_giderler": gider_listesi[:10],
        "tahmin": tahmin,
    }