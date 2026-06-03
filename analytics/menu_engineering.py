"""
menu_engineering.py — Menü Mühendisliği  

Kasavana-Smith menü mühendisliği matrisini POS verisinden üretir
Ürünleri popülerlik × katkı marjı eksenlerinde 4 kadrana ayırır:


"""

import pandas as pd
import matplotlib.pyplot as plt
import data_loader as dl


SINIFLAR = {
    "Şampiyon":     {"renk": "#10B981", "aksiyon": "Menünün yıldızı. Görünürlüğü artır, fiyata dokunma."},
    "Lokomotif":    {"renk": "#14B8A6", "aksiyon": "Sürümden kazandırıyor. Maliyet pazarlığı ile kâr katlanır."},
    "Gizli Cevher": {"renk": "#F59E0B", "aksiyon": "Marjı yüksek ama bilinmiyor. Garsona 'günün önerisi' olarak ver."},
    "Zayıf Halka":  {"renk": "#EF4444", "aksiyon": "Maliyetli ve satmıyor. Menüden çıkarmayı veya reçeteyi sadeleştirmeyi düşün."},
}


def analiz_et(sube_id: int, gun: int = 90) -> pd.DataFrame:
    """
    Şube için menü mühendisliği analizini DataFrame olarak döner.

    Returns:
        DataFrame kolonları: urun, kategori, toplam_satis, birim_kar,
                             toplam_kar, siniflandirma, aksiyon
    """
    df = dl.satislar(sube_id=sube_id, gun=gun)

    # Ürün bazında grupla
    ozet = df.groupby(["urun_id", "urun", "kategori", "satis_fiyati", "birim_kar"]).agg(
        toplam_satis=("satilan_miktar", "sum"),
        toplam_kar=("kar", "sum"),
    ).reset_index()

    # Medyan eşik uç değerlersden etkilenmesin
    esik_satis = ozet["toplam_satis"].median()
    esik_kar = ozet["birim_kar"].median()

    def sinifla(r):
        yuksek_satis = r["toplam_satis"] >= esik_satis
        yuksek_kar = r["birim_kar"] >= esik_kar
        if yuksek_satis and yuksek_kar:    return "Şampiyon"
        if yuksek_satis and not yuksek_kar: return "Lokomotif"
        if not yuksek_satis and yuksek_kar: return "Gizli Cevher"
        return "Zayıf Halka"

    ozet["siniflandirma"] = ozet.apply(sinifla, axis=1)
    ozet["aksiyon"] = ozet["siniflandirma"].map(lambda s: SINIFLAR[s]["aksiyon"])
    ozet["kar_marji_yuzde"] = (ozet["birim_kar"] / ozet["satis_fiyati"] * 100).round(1)

    # Eşik bilgisi ek metadata
    ozet.attrs["esik_satis"] = esik_satis
    ozet.attrs["esik_kar"] = esik_kar
    ozet.attrs["sube_id"] = sube_id

    return ozet.sort_values("toplam_kar", ascending=False).reset_index(drop=True)


def ciz(ozet: pd.DataFrame, baslik: str = None, kaydet: str = None):
    """
    Menü mühendisliği matrisini scatter plot olarak çizer.

    Args:
        ozet: analiz_et() çıktısı
        baslik: grafik başlığı
        kaydet: dosya yolu verilirse PNG olarak kaydet
    """
    fig, ax = plt.subplots(figsize=(11, 7))

    esik_satis = ozet.attrs["esik_satis"]
    esik_kar = ozet.attrs["esik_kar"]

    # 4 kadran arka plan rengi
    xmax = ozet["toplam_satis"].max() * 1.1
    ymax = ozet["birim_kar"].max() * 1.1

    ax.axhspan(esik_kar, ymax, xmin=esik_satis / xmax, color="#10B981", alpha=0.05)  # Şampiyon
    ax.axhspan(0, esik_kar, xmin=esik_satis / xmax, color="#14B8A6", alpha=0.05)     # Lokomotif
    ax.axhspan(esik_kar, ymax, xmax=esik_satis / xmax, color="#F59E0B", alpha=0.05)  # Gizli Cevher
    ax.axhspan(0, esik_kar, xmax=esik_satis / xmax, color="#EF4444", alpha=0.05)     # Zayıf Halka

    # Eşik çizgileri
    ax.axvline(esik_satis, color="#64748B", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(esik_kar, color="#64748B", linestyle="--", linewidth=0.8, alpha=0.5)

    # Her sınıf için scatter
    for sinif, info in SINIFLAR.items():
        alt = ozet[ozet["siniflandirma"] == sinif]
        ax.scatter(
            alt["toplam_satis"], alt["birim_kar"],
            c=info["renk"], s=140, alpha=0.75,
            edgecolors="white", linewidths=1.5,
            label=f"{sinif} ({len(alt)})",
            zorder=3,
        )

    # Ürün isimlerini noktaların üstüne yazmak
    for _, r in ozet.iterrows():
        ax.annotate(
            r["urun"],
            (r["toplam_satis"], r["birim_kar"]),
            fontsize=7.5, alpha=0.7,
            xytext=(5, 5), textcoords="offset points",
        )

    # Kadran etiketleri köşelerde
    ax.text(xmax * 0.97, ymax * 0.95, "ŞAMPİYON", ha="right", va="top",
            fontsize=10, fontweight="bold", color="#10B981", alpha=0.6)
    ax.text(xmax * 0.97, ymax * 0.05, "LOKOMOTİF", ha="right", va="bottom",
            fontsize=10, fontweight="bold", color="#14B8A6", alpha=0.6)
    ax.text(xmax * 0.03, ymax * 0.95, "GİZLİ CEVHER", ha="left", va="top",
            fontsize=10, fontweight="bold", color="#F59E0B", alpha=0.6)
    ax.text(xmax * 0.03, ymax * 0.05, "ZAYIF HALKA", ha="left", va="bottom",
            fontsize=10, fontweight="bold", color="#EF4444", alpha=0.6)

    ax.set_xlabel("Toplam Satış Adedi (Popülerlik) →", fontsize=11)
    ax.set_ylabel("Birim Katkı Marjı (₺) →", fontsize=11)
    sube = dl.sube_adi(ozet.attrs["sube_id"])
    ax.set_title(baslik or f"Menü Mühendisliği Matrisi — {sube} (son 90 gün)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=4, frameon=False, fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.3)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    plt.tight_layout()

    if kaydet:
        plt.savefig(kaydet, dpi=150, bbox_inches="tight")
        print(f"Kaydedildi: {kaydet}")
    return fig


def one_cikan_aksiyon(ozet: pd.DataFrame) -> str:
    """En düşük performanslı zayıf halka için somut aksiyon önerisi."""
    zayif = ozet[ozet["siniflandirma"] == "Zayıf Halka"].sort_values("toplam_satis")
    if zayif.empty:
        return "Şu an menüde zayıf halka yok. Sağlıklı portföy."
    en_kotu = zayif.iloc[0]
    return (
        f"'{en_kotu['urun']}' son 90 günde sadece {int(en_kotu['toplam_satis'])} kez satıldı, "
        f"marj %{en_kotu['kar_marji_yuzde']:.0f}. Menüden çıkarmayı değerlendir."
    )


if __name__ == "__main__":
    # Hızlı test 
    print("Menü Mühendisliği — Kadıköy Merkez")
    print("=" * 60)
    sonuc = analiz_et(sube_id=1)
    print(sonuc[["urun", "toplam_satis", "birim_kar", "siniflandirma"]].to_string(index=False))
    print()
    print("Sınıf dağılımı:")
    print(sonuc["siniflandirma"].value_counts().to_string())
    print()
    print("Öne çıkan aksiyon:")
    print(" →", one_cikan_aksiyon(sonuc))
