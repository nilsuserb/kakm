"""
data_loader.py — KAKM verilerini pandas DataFrame'lerine yükler.

API klasöründeki kakm_restoran.db'yi paylaşır. Analitik modüller buradan veri çeker.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime


# DB yolu api klasöründeki ortak veritabanı
DB_PATH = Path(__file__).parent.parent / "api" / "kakm_restoran.db"
BUGUN = datetime(2026, 5, 27)


def _conn():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Veritabanı bulunamadı: {DB_PATH}\n"
            f"Önce api klasörüne gidip 'python init_db.py' çalıştır."
        )
    return sqlite3.connect(DB_PATH)


def subeler() -> pd.DataFrame:
    """Tüm şubeler."""
    with _conn() as c:
        return pd.read_sql("SELECT * FROM Subeler", c)


def urunler() -> pd.DataFrame:
    """Tüm ürünler + birim kar kolonu eklenmiş."""
    with _conn() as c:
        df = pd.read_sql("SELECT * FROM Urunler", c)
    df["birim_kar"] = df["satis_fiyati"] - df["maliyet"]
    df["kar_marji"] = df["birim_kar"] / df["satis_fiyati"]
    return df


def satislar(sube_id: int = None, gun: int = 90) -> pd.DataFrame:
    """
    Satış verisi — ürün adı ve fiyat bilgisi join'lenmiş.

    Args:
        sube_id: Belirli bir şube için filtrele (None = tüm şubeler)
        gun: Son kaç gün (varsayılan 90)
    """
    baslangic = (BUGUN - pd.Timedelta(days=gun)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    sql = """
        SELECT
            s.tarih,
            s.sube_id,
            s.urun_id,
            s.satilan_miktar,
            u.isim AS urun,
            u.kategori,
            u.satis_fiyati,
            u.maliyet,
            (u.satis_fiyati - u.maliyet) AS birim_kar,
            s.satilan_miktar * u.satis_fiyati AS ciro,
            s.satilan_miktar * (u.satis_fiyati - u.maliyet) AS kar
        FROM Satislar s
        JOIN Urunler u ON s.urun_id = u.id
        WHERE s.tarih BETWEEN ? AND ?
    """
    params = [baslangic, bugun_str]

    if sube_id is not None:
        sql += " AND s.sube_id = ?"
        params.append(sube_id)

    with _conn() as c:
        df = pd.read_sql(sql, c, params=params, parse_dates=["tarih"])
    return df


def stok_hareketleri(sube_id: int = None, gun: int = 30) -> pd.DataFrame:
    """Teorik vs gerçek tüketim verisi."""
    baslangic = (BUGUN - pd.Timedelta(days=gun)).strftime("%Y-%m-%d")
    bugun_str = BUGUN.strftime("%Y-%m-%d")

    sql = """
        SELECT
            sh.tarih,
            sh.sube_id,
            sh.urun_id,
            u.isim AS urun,
            u.kategori,
            sh.teorik_tuketim,
            sh.gercek_tuketim,
            (sh.gercek_tuketim - sh.teorik_tuketim) AS sapma
        FROM Stok_Hareketleri sh
        JOIN Urunler u ON sh.urun_id = u.id
        WHERE sh.tarih BETWEEN ? AND ?
    """
    params = [baslangic, bugun_str]

    if sube_id is not None:
        sql += " AND sh.sube_id = ?"
        params.append(sube_id)

    with _conn() as c:
        df = pd.read_sql(sql, c, params=params, parse_dates=["tarih"])
    return df


def giderler(sube_id: int = None) -> pd.DataFrame:
    """Yaklaşan giderler (önümüzdeki 30 gün)."""
    sql = "SELECT * FROM Giderler"
    params = []
    if sube_id is not None:
        sql += " WHERE sube_id = ?"
        params.append(sube_id)
    sql += " ORDER BY tarih"

    with _conn() as c:
        df = pd.read_sql(sql, c, params=params, parse_dates=["tarih"])
    return df


def sube_adi(sube_id: int) -> str:
    """Şube id → isim."""
    df = subeler()
    row = df[df["id"] == sube_id]
    return row.iloc[0]["isim"] if not row.empty else f"Şube #{sube_id}"
