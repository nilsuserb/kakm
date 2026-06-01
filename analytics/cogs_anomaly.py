"""
cogs_anomaly.py — COGS Anomali Tespiti (Modül 2)

Restoran finansının en sessiz sızıntısı: teorik tüketim ile gerçek tüketim
arasındaki açık. İki yaklaşımla çözüyoruz:

  1. Eşik bazlı  : %5'in üstünde sapma → bayrak
  2. Isolation Forest : Olağandışı sapma desenlerini ML ile yakala
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import data_loader as dl


def esik_bazli_anomaliler(sube_id: int, gun: int = 7, esik_yuzde: float = 5.0) -> pd.DataFrame:
    """
    Basit eşik bazlı anomali tespiti — son N gün içinde ürün bazında toplam sapma.

    Returns:
        DataFrame: urun, teorik, gercek, sapma_tl, sapma_yuzde, seviye
    """
    df = dl.stok_hareketleri(sube_id=sube_id, gun=gun)

    ozet = df.groupby(["urun_id", "urun", "kategori"]).agg(
        teorik=("teorik_tuketim", "sum"),
        gercek=("gercek_tuketim", "sum"),
    ).reset_index()

    ozet["sapma_tl"] = ozet["gercek"] - ozet["teorik"]
    ozet["sapma_yuzde"] = (ozet["sapma_tl"] / ozet["teorik"] * 100).round(2)

    # Sadece eşik üstü
    anomaliler = ozet[ozet["sapma_yuzde"].abs() >= esik_yuzde].copy()
    anomaliler["seviye"] = anomaliler["sapma_yuzde"].abs().apply(
        lambda x: "yüksek" if x >= 7 else "orta"
    )
    return anomaliler.sort_values("sapma_tl", key=abs, ascending=False).reset_index(drop=True)


def isolation_forest_anomaliler(sube_id: int, gun: int = 30, contamination: float = 0.05) -> pd.DataFrame:
    """
    Isolation Forest ile gün-ürün bazında olağandışı sapmaları yakalar.

    Eşik bazlı yöntemden farkı: deseni anlar.
    "Cuma akşamları her ürün %3 sapma yapar, ama bu Cuma Beef Noodle %9 sapma yaptı"
    gibi *bağlamsal* anomalileri tespit eder.

    Returns:
        Sadece anomali olarak işaretlenen satırlar (sapma yüzdesine göre sıralı)
    """
    df = dl.stok_hareketleri(sube_id=sube_id, gun=gun)
    df = df[df["teorik_tuketim"] > 0].copy()
    df["sapma_orani"] = df["sapma"] / df["teorik_tuketim"]
    df["gun_adi"] = df["tarih"].dt.dayofweek
    df["hafta_sonu"] = (df["gun_adi"] >= 5).astype(int)

    # ML için özellikler: sapma oranı + gün + ürün id (kategorik proxy)
    X = df[["sapma_orani", "gun_adi", "hafta_sonu", "urun_id"]].values

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )
    df["anomali"] = model.fit_predict(X)
    df["anomali_skoru"] = -model.score_samples(X)  # Pozitif değer = daha anomali

    # -1 = anomali, 1 = normal
    anomaliler = df[df["anomali"] == -1].copy()
    anomaliler["sapma_yuzde"] = (anomaliler["sapma_orani"] * 100).round(2)
    anomaliler = anomaliler.sort_values("anomali_skoru", ascending=False)
    return anomaliler[
        ["tarih", "urun", "kategori", "teorik_tuketim", "gercek_tuketim",
         "sapma", "sapma_yuzde", "gun_adi", "anomali_skoru"]
    ].reset_index(drop=True)


def gunluk_sapma_serisi(sube_id: int, gun: int = 30) -> pd.DataFrame:
    """Tarih bazında günlük toplam sapma — trend analizi için."""
    df = dl.stok_hareketleri(sube_id=sube_id, gun=gun)
    gunluk = df.groupby("tarih").agg(
        teorik=("teorik_tuketim", "sum"),
        gercek=("gercek_tuketim", "sum"),
    ).reset_index()
    gunluk["sapma_tl"] = gunluk["gercek"] - gunluk["teorik"]
    gunluk["sapma_yuzde"] = (gunluk["sapma_tl"] / gunluk["teorik"] * 100).round(2)
    gunluk["gun_adi"] = gunluk["tarih"].dt.dayofweek
    return gunluk


def ciz(sube_id: int, gun: int = 30, kaydet: str = None):
    """COGS anomali tespit görselleştirmesi — 2 panel."""
    gunluk = gunluk_sapma_serisi(sube_id, gun)
    ml_anomaliler = isolation_forest_anomaliler(sube_id, gun)
    sube = dl.sube_adi(sube_id)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={"height_ratios": [1, 1.2]})

    # PANEL 1: Günlük sapma trendi
    renkler = ["#EF4444" if abs(x) >= 5 else "#94A3B8" for x in gunluk["sapma_yuzde"]]
    ax1.bar(gunluk["tarih"], gunluk["sapma_yuzde"], color=renkler, alpha=0.85, width=0.7)
    ax1.axhline(0, color="black", linewidth=0.5)
    ax1.axhline(5, color="#EF4444", linestyle="--", linewidth=0.8, alpha=0.5, label="%5 eşik")
    ax1.axhline(-5, color="#EF4444", linestyle="--", linewidth=0.8, alpha=0.5)
    ax1.set_ylabel("Sapma (%)", fontsize=11)
    ax1.set_title(f"Günlük COGS Sapma Trendi — {sube} (son {gun} gün)",
                  fontsize=12, fontweight="bold", pad=10)
    ax1.grid(True, linestyle=":", alpha=0.3)
    ax1.legend(loc="upper right", fontsize=9, frameon=False)
    ax1.tick_params(axis="x", rotation=30, labelsize=8)

    # PANEL 2: Isolation Forest sonuçları — scatter
    df_tum = dl.stok_hareketleri(sube_id=sube_id, gun=gun)
    df_tum = df_tum[df_tum["teorik_tuketim"] > 0].copy()
    df_tum["sapma_yuzde"] = (df_tum["sapma"] / df_tum["teorik_tuketim"] * 100)

    # Normal noktalar
    if not df_tum.empty:
        ax2.scatter(df_tum["tarih"], df_tum["sapma_yuzde"],
                    c="#CBD5E1", s=15, alpha=0.5, label="Normal", zorder=2)

    # Anomali noktalar
    if not ml_anomaliler.empty:
        ax2.scatter(ml_anomaliler["tarih"], ml_anomaliler["sapma_yuzde"],
                    c="#EF4444", s=60, alpha=0.9, edgecolors="white", linewidths=1,
                    label=f"Anomali ({len(ml_anomaliler)})", zorder=3)

        # En kötü 3 anomaliyi etiketle
        for _, r in ml_anomaliler.head(3).iterrows():
            ax2.annotate(
                f"{r['urun']}\n%{r['sapma_yuzde']:+.1f}",
                (r["tarih"], r["sapma_yuzde"]),
                xytext=(8, 8), textcoords="offset points",
                fontsize=8, alpha=0.8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#EF4444", alpha=0.9, linewidth=0.5),
            )

    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_xlabel("Tarih", fontsize=11)
    ax2.set_ylabel("Ürün Bazında Sapma (%)", fontsize=11)
    ax2.set_title(f"Isolation Forest ile Anomali Tespiti — Bağlamsal sapmalar",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.grid(True, linestyle=":", alpha=0.3)
    ax2.legend(loc="upper right", fontsize=9, frameon=False)
    ax2.tick_params(axis="x", rotation=30, labelsize=8)

    plt.tight_layout()
    if kaydet:
        plt.savefig(kaydet, dpi=150, bbox_inches="tight")
        print(f"Kaydedildi: {kaydet}")
    return fig


if __name__ == "__main__":
    print("COGS Anomali Tespiti — Kadıköy Merkez")
    print("=" * 60)

    print("\n[1] Eşik bazlı (son 7 gün):")
    esik = esik_bazli_anomaliler(sube_id=1)
    print(esik[["urun", "teorik", "gercek", "sapma_tl", "sapma_yuzde", "seviye"]].to_string(index=False))

    print("\n[2] Isolation Forest (son 30 gün, top 10):")
    ml = isolation_forest_anomaliler(sube_id=1)
    print(ml[["tarih", "urun", "sapma_yuzde", "anomali_skoru"]].head(10).to_string(index=False))
