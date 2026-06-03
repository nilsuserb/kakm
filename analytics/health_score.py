
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import data_loader as dl

BUGUN = dl.BUGUN

AGIRLIKLAR = {
    "brut_kar_marji":     0.25,
    "stok_devir_hizi":    0.15,
    "personel_verimi":    0.15,
    "cogs_sapma_sagligi": 0.15,
    "ortalama_sepet":     0.10,
    "yogun_saat":         0.10,
    "atik_fire":          0.10,
}


def hesapla(sube_id: int) -> dict:
    
   
    satis_son30 = dl.satislar(sube_id=sube_id, gun=30)
    satis_oncesi = dl.satislar(sube_id=sube_id, gun=60)
    
    son_30_baslangic = pd.Timestamp(BUGUN - pd.Timedelta(days=30))
    satis_oncesi_30 = satis_oncesi[satis_oncesi["tarih"] < son_30_baslangic]

    if satis_son30.empty:
        return {"hata": "Veri yok"}

   
    toplam_ciro = satis_son30["ciro"].sum()
    toplam_maliyet = (satis_son30["satilan_miktar"] * satis_son30["maliyet"]).sum()
    brut_marj = (toplam_ciro - toplam_maliyet) / toplam_ciro if toplam_ciro else 0
   
    brut_marj_skor = max(0, min(100, (brut_marj - 0.10) / 0.35 * 100))

   
    gun_sayisi = satis_son30["tarih"].dt.date.nunique()
    gunluk_ort_ciro = toplam_ciro / max(gun_sayisi, 1)
    
    personel_skor = max(0, min(100, (gunluk_ort_ciro - 20000) / 60000 * 100))

   
    stok = dl.stok_hareketleri(sube_id=sube_id, gun=30)
    if not stok.empty:
        teorik = stok["teorik_tuketim"].sum()
        gercek = stok["gercek_tuketim"].sum()
        sapma_orani = (gercek - teorik) / teorik if teorik else 0
        ort_gunluk_tuketim = stok.groupby("tarih")["teorik_tuketim"].sum().mean()
    else:
        sapma_orani = 0
        ort_gunluk_tuketim = 0

   
    devir_skor = min(100, (ort_gunluk_tuketim / 1500) * 100)
   
    cogs_skor = max(0, min(100, 100 - (sapma_orani - 0.02) * 800))
  
    atik_skor = max(0, min(100, 100 - sapma_orani * 600))

   
    
    toplam_adet = satis_son30["satilan_miktar"].sum()
    ort_sepet = toplam_ciro / max(toplam_adet / 2.5, 1)
  
    sepet_skor = max(0, min(100, (ort_sepet - 100) / 280 * 100))

   
    onceki_ciro = satis_oncesi_30["ciro"].sum() if not satis_oncesi_30.empty else toplam_ciro
    buyume = (toplam_ciro - onceki_ciro) / onceki_ciro if onceki_ciro else 0
   
    yogun_skor = max(0, min(100, 60 + buyume * 200))

    bilesenler = {
        "brut_kar_marji":     round(brut_marj_skor, 1),
        "stok_devir_hizi":    round(devir_skor, 1),
        "personel_verimi":    round(personel_skor, 1),
        "cogs_sapma_sagligi": round(cogs_skor, 1),
        "ortalama_sepet":     round(sepet_skor, 1),
        "yogun_saat":         round(yogun_skor, 1),
        "atik_fire":          round(atik_skor, 1),
    }

    skor = int(round(sum(bilesenler[k] * AGIRLIKLAR[k] for k in AGIRLIKLAR)))

    if skor >= 80:   etiket = "Sağlıklı"
    elif skor >= 60: etiket = "İzlenmeli"
    elif skor >= 40: etiket = "Riskli"
    else:            etiket = "Kriz"

    return {
        "sube_id":     sube_id,
        "sube_adi":    dl.sube_adi(sube_id),
        "skor":        skor,
        "etiket":      etiket,
        "bilesenler":  bilesenler,
        "ham_metrikler": {
            "gunluk_ort_ciro":    round(gunluk_ort_ciro, 2),
            "brut_marji_yuzde":   round(brut_marj * 100, 2),
            "cogs_sapma_yuzde":   round(sapma_orani * 100, 2),
            "ortalama_sepet":     round(ort_sepet, 2),
            "buyume_yuzde":       round(buyume * 100, 2),
        },
    }


def tum_subeler_skor() -> pd.DataFrame:
    """7 şube için karşılaştırmalı skor tablosu."""
    subeler_df = dl.subeler()
    sonuclar = []
    for _, s in subeler_df.iterrows():
        r = hesapla(s["id"])
        if "hata" in r:
            continue
        sonuclar.append({
            "sube":    r["sube_adi"],
            "skor":    r["skor"],
            "etiket":  r["etiket"],
            "gunluk_ciro": r["ham_metrikler"]["gunluk_ort_ciro"],
            "buyume_yuzde": r["ham_metrikler"]["buyume_yuzde"],
        })
    df = pd.DataFrame(sonuclar).sort_values("skor", ascending=False).reset_index(drop=True)
    return df


def radar_ciz(sube_id: int, kaydet: str = None):
    """Tek şube için radar (örümcek ağı) grafik."""
    r = hesapla(sube_id)
    if "hata" in r:
        print(r["hata"])
        return None

    bilesenler = r["bilesenler"]
    
    etiketler_tr = {
        "brut_kar_marji":     "Brüt Kar Marjı",
        "stok_devir_hizi":    "Stok Devir",
        "personel_verimi":    "Personel Verimi",
        "cogs_sapma_sagligi": "COGS Sağlığı",
        "ortalama_sepet":     "Ort. Sepet",
        "yogun_saat":         "Büyüme",
        "atik_fire":          "Atık/Fire",
    }
    kategoriler = [etiketler_tr[k] for k in bilesenler.keys()]
    degerler = list(bilesenler.values())
   
    aci = np.linspace(0, 2 * np.pi, len(kategoriler), endpoint=False).tolist()
    degerler_r = degerler + [degerler[0]]
    aci_r = aci + [aci[0]]

   
    skor = r["skor"]
    if skor >= 80:   renk = "#10B981"
    elif skor >= 60: renk = "#14B8A6"
    elif skor >= 40: renk = "#F59E0B"
    else:            renk = "#EF4444"

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    ax.plot(aci_r, degerler_r, color=renk, linewidth=2.5)
    ax.fill(aci_r, degerler_r, color=renk, alpha=0.25)

    ax.set_xticks(aci)
    ax.set_xticklabels(kategoriler, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8, color="#94A3B8")
    ax.grid(True, linestyle=":", alpha=0.5)

    
    fig.text(0.5, 0.50, str(skor), ha="center", va="center",
             fontsize=48, fontweight="bold", color=renk)
    fig.text(0.5, 0.42, r["etiket"], ha="center", va="center",
             fontsize=14, color=renk, fontweight="600")

    plt.title(f"Finansal Sağlık Skoru — {r['sube_adi']}",
              fontsize=14, fontweight="bold", pad=30)
    plt.tight_layout()
    if kaydet:
        plt.savefig(kaydet, dpi=150, bbox_inches="tight")
        print(f"Kaydedildi: {kaydet}")
    return fig


def karsilastirma_ciz(kaydet: str = None):
    """7 şube için yatay bar chart."""
    df = tum_subeler_skor()

    fig, ax = plt.subplots(figsize=(11, 6))

    
    def renk_func(skor):
        if skor >= 80:   return "#10B981"
        elif skor >= 60: return "#14B8A6"
        elif skor >= 40: return "#F59E0B"
        else:            return "#EF4444"

    renkler = [renk_func(s) for s in df["skor"]]
    bars = ax.barh(df["sube"], df["skor"], color=renkler, alpha=0.85,
                   edgecolor="white", linewidth=1.5)

   
    for i, (bar, etiket, ciro) in enumerate(zip(bars, df["etiket"], df["gunluk_ciro"])):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"{int(bar.get_width())} · {etiket}",
                va="center", fontsize=10, fontweight="bold")
        ax.text(2, bar.get_y() + bar.get_height()/2,
                f"₺{ciro/1000:.0f}K/gün",
                va="center", fontsize=9, color="white", fontweight="500")

   
    ax.axvspan(0, 40, alpha=0.04, color="#EF4444", zorder=0)
    ax.axvspan(40, 60, alpha=0.04, color="#F59E0B", zorder=0)
    ax.axvspan(60, 80, alpha=0.04, color="#14B8A6", zorder=0)
    ax.axvspan(80, 100, alpha=0.04, color="#10B981", zorder=0)

    ax.set_xlim(0, 110)
    ax.set_xlabel("Finansal Sağlık Skoru", fontsize=11)
    ax.set_title("Şube Karşılaştırması — Tüm Zincir",
                 fontsize=14, fontweight="bold", pad=15)
    ax.invert_yaxis()
    ax.grid(True, axis="x", linestyle=":", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    if kaydet:
        plt.savefig(kaydet, dpi=150, bbox_inches="tight")
        print(f"Kaydedildi: {kaydet}")
    return fig


if __name__ == "__main__":
    print("Finansal Sağlık Skoru — Tüm Şubeler")
    print("=" * 60)
    df = tum_subeler_skor()
    print(df.to_string(index=False))
    print()
    print("Kadıköy Merkez detay:")
    r = hesapla(sube_id=1)
    print(f"  Skor: {r['skor']} → {r['etiket']}")
    print("  Bileşenler:")
    for k, v in r["bilesenler"].items():
        print(f"    {k:25s} {v}")
    print("  Ham metrikler:")
    for k, v in r["ham_metrikler"].items():
        print(f"    {k:25s} {v}")
