
"""Nakit akışı tahmini. P10/P50/P90 güven aralığı ile 14-30 gün öngörü."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
import data_loader as dl

BUGUN = dl.BUGUN
N_SIMULASYON = 1000


def gecmis_ciro_ozeti(sube_id: int, gun: int = 60) -> pd.DataFrame:
    """Son N gün için günlük ciro serisi + hafta günü."""
    df = dl.satislar(sube_id=sube_id, gun=gun)
    gunluk = df.groupby("tarih").agg(
        ciro=("ciro", "sum"),
        kar=("kar", "sum"),
    ).reset_index()
    gunluk["gun_adi"] = gunluk["tarih"].dt.dayofweek
    return gunluk


def haftalik_desen(gecmis: pd.DataFrame) -> dict:
    """Her hafta günü için ortalama + std ciro."""
    desen = {}
    for gun_adi in range(7):
        alt = gecmis[gecmis["gun_adi"] == gun_adi]
        if not alt.empty:
            desen[gun_adi] = {
                "ortalama": alt["ciro"].mean(),
                "std": alt["ciro"].std() if len(alt) > 1 else alt["ciro"].mean() * 0.15,
                "kar_marji": (alt["kar"].sum() / alt["ciro"].sum()) if alt["ciro"].sum() else 0.5,
            }
    return desen


def tahmin_et(sube_id: int, gun_sayisi: int = 14, gecmis_gun: int = 60) -> pd.DataFrame:
    """
    Monte Carlo simülasyonu ile nakit akışı tahmini.

    Returns:
        DataFrame: tarih, p10, p50, p90, gider (her gün için)
    """
    gecmis = gecmis_ciro_ozeti(sube_id, gun=gecmis_gun)
    if gecmis.empty:
        return pd.DataFrame()

    desen = haftalik_desen(gecmis)

    # Mevcut kasa tahmini 
    mevcut_kasa = gecmis.tail(7)["kar"].sum()

    # Yaklaşan giderler
    giderler_df = dl.giderler(sube_id=sube_id)
    bitis_tarihi = BUGUN + timedelta(days=gun_sayisi)
    giderler_df = giderler_df[
        (giderler_df["tarih"] >= pd.Timestamp(BUGUN)) &
        (giderler_df["tarih"] <= pd.Timestamp(bitis_tarihi))
    ]
    gun_gider = giderler_df.groupby("tarih")["tutar"].sum().to_dict()

    # Monte carlo simülasyonları her senaryo için kasa pozisyonu
    np.random.seed(42)
    senaryolar = np.zeros((N_SIMULASYON, gun_sayisi + 1))
    senaryolar[:, 0] = mevcut_kasa

    for i in range(1, gun_sayisi + 1):
        tarih = BUGUN + timedelta(days=i)
        gun_adi = tarih.weekday()
        d = desen.get(gun_adi, {"ortalama": 30000, "std": 5000, "kar_marji": 0.5})

        # Her senaryo için rastgele ciro çek (normal dağılım)
        ciro_ornekleri = np.random.normal(d["ortalama"], d["std"], N_SIMULASYON)
        ciro_ornekleri = np.maximum(ciro_ornekleri, 0)  # Negatif ciro olmaz
        kar_ornekleri = ciro_ornekleri * d["kar_marji"]

        # Önceki günün kasa pozisyonu + günün karı
        senaryolar[:, i] = senaryolar[:, i-1] + kar_ornekleri

        # Gider düş
        tarih_ts = pd.Timestamp(tarih.strftime("%Y-%m-%d"))
        if tarih_ts in gun_gider:
            senaryolar[:, i] -= gun_gider[tarih_ts]

    # Her gün için yüzdelikler
    tahmin = pd.DataFrame({
        "tarih":   [BUGUN + timedelta(days=i) for i in range(gun_sayisi + 1)],
        "p10":     np.percentile(senaryolar, 10, axis=0),
        "p50":     np.percentile(senaryolar, 50, axis=0),
        "p90":     np.percentile(senaryolar, 90, axis=0),
    })

    # Gün başına gider sütunu
    tahmin["gider"] = tahmin["tarih"].apply(
        lambda t: gun_gider.get(pd.Timestamp(t.strftime("%Y-%m-%d")), 0)
    )
    tahmin["tarih"] = pd.to_datetime(tahmin["tarih"])

    return tahmin


def risk_uyarisi(tahmin: pd.DataFrame) -> str | None:
    """P10 negatife düşüyorsa uyarı."""
    neg = tahmin[tahmin["p10"] < 0]
    if neg.empty:
        return None
    ilk_neg = neg.iloc[0]
    return (
        f"⚠ {ilk_neg['tarih'].strftime('%Y-%m-%d')} tarihinde kötü senaryoda "
        f"kasa negatife düşebilir (P10: ₺{ilk_neg['p10']:,.0f}). "
        f"O gün gider: ₺{ilk_neg['gider']:,.0f}."
    )


def ciz(sube_id: int, gun_sayisi: int = 14, kaydet: str = None):
    """Fan chart — P10/P50/P90 güven aralıkları."""
    tahmin = tahmin_et(sube_id, gun_sayisi)
    if tahmin.empty:
        print("Veri yetersiz.")
        return None

    sube = dl.sube_adi(sube_id)
    fig, ax = plt.subplots(figsize=(13, 6))

    # P10 P90 fan
    ax.fill_between(
        tahmin["tarih"], tahmin["p10"], tahmin["p90"],
        color="#14B8A6", alpha=0.15, label="P10-P90 (güven aralığı)",
    )

    # P50 medyan çizgisi
    ax.plot(tahmin["tarih"], tahmin["p50"],
            color="#0F766E", linewidth=2.5, label="P50 (medyan tahmin)", zorder=3)

    # P10 kötü senaryo (kesikli)
    ax.plot(tahmin["tarih"], tahmin["p10"],
            color="#EF4444", linewidth=1.2, linestyle="--", alpha=0.7,
            label="P10 (kötü senaryo)", zorder=2)

    # P90 iyi senaryo
    ax.plot(tahmin["tarih"], tahmin["p90"],
            color="#10B981", linewidth=1.2, linestyle="--", alpha=0.7,
            label="P90 (iyi senaryo)", zorder=2)

    # Sıfır çizgisi
    ax.axhline(0, color="black", linewidth=0.6, alpha=0.5)

    # Gider günlerini işaretlemek için
    gider_gunler = tahmin[tahmin["gider"] > 0]
    for _, r in gider_gunler.iterrows():
        ax.axvline(r["tarih"], color="#F59E0B", linewidth=0.5, alpha=0.4, linestyle=":")
        if r["gider"] >= 50000:  # Büyük giderleri etiketle
            ax.annotate(
                f"₺{r['gider']/1000:.0f}K",
                (r["tarih"], r["p50"]),
                xytext=(0, -25), textcoords="offset points",
                fontsize=8, ha="center", color="#92400E",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF3C7",
                          edgecolor="#F59E0B", linewidth=0.5),
            )

    ax.set_xlabel("Tarih", fontsize=11)
    ax.set_ylabel("Kasa Pozisyonu (₺)", fontsize=11)
    ax.set_title(f"Nakit Akışı Tahmini — {sube} (önümüzdeki {gun_sayisi} gün)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.legend(loc="upper left", fontsize=9, frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=":", alpha=0.3)

    # X ekseni formatı
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    fig.autofmt_xdate(rotation=30)

    # Y eksenini binliğe formatla
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₺{x/1000:.0f}K"))

    # Risk uyarısı annotation
    uyari = risk_uyarisi(tahmin)
    if uyari:
        ax.text(
            0.5, -0.20, uyari,
            transform=ax.transAxes, ha="center", fontsize=10,
            color="#991B1B",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEE2E2",
                      edgecolor="#EF4444", linewidth=1),
        )

    plt.tight_layout()
    if kaydet:
        plt.savefig(kaydet, dpi=150, bbox_inches="tight")
        print(f"Kaydedildi: {kaydet}")
    return fig


if __name__ == "__main__":
    print("Nakit Akışı Tahmini — Kadıköy Merkez (14 gün)")
    print("=" * 60)
    tahmin = tahmin_et(sube_id=1, gun_sayisi=14)
    print(tahmin.to_string(index=False))
    print()
    uyari = risk_uyarisi(tahmin)
    if uyari:
        print(uyari)
    else:
        print("✓ 14 gün içinde negatif kasa riski yok.")
