"""Dashboard data prodi (Streamlit). Jalankan:  streamlit run prodi_dashboard.py"""
from pathlib import Path

import pandas as pd
import streamlit as st

KET = "Keketatan 2025 (%)"
MAPEL = ["Mapel Pendukung 1", "Mapel Pendukung 2", "Mapel Pendukung 3"]


@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).parent / "data_prodi.csv")


def main():
    st.set_page_config(page_title="Dashboard Data Prodi", layout="wide")
    st.title("Dashboard Data Prodi")
    st.caption("Keketatan 2025 = daya tampung ÷ peminat. Angka kecil berarti lebih ketat.")
    df = load()

    with st.sidebar:
        st.header("Filter")
        q = st.text_input("Cari prodi")
        ptn = st.multiselect("PTN", sorted(df["PTN"].unique()))
        jen = st.multiselect("Jenjang", sorted(df["Jenjang"].unique()))
        mapel_opsi = sorted(set(df[MAPEL].stack()))
        pm = st.multiselect("Mapel pendukung", mapel_opsi, help="Tampilkan prodi yang memakai salah satu mapel ini.")
        baru = st.selectbox("Prodi baru 2026", ["Semua", "Ya", "Tidak"])
        porto = st.selectbox("Portofolio", ["Semua"] + sorted(df["Portofolio"].unique()))
        kelas = st.selectbox("Keketatan 2025", ["Semua", "Sangat ketat (< 10%)", "Ketat (10-20%)",
                                                "Sedang (20-40%)", "Longgar (> 40%)", "Tanpa data"])

    f = df
    if q:
        f = f[f["Program Studi"].str.contains(q, case=False, na=False)]
    if ptn:
        f = f[f["PTN"].isin(ptn)]
    if jen:
        f = f[f["Jenjang"].isin(jen)]
    if pm:
        f = f[f[MAPEL].isin(pm).any(axis=1)]
    if baru != "Semua":
        f = f[f["Prodi Baru 2026"] == baru]
    if porto != "Semua":
        f = f[f["Portofolio"] == porto]
    k = f[KET]
    f = {"Semua": f, "Sangat ketat (< 10%)": f[k < 10], "Ketat (10-20%)": f[(k >= 10) & (k < 20)],
         "Sedang (20-40%)": f[(k >= 20) & (k < 40)], "Longgar (> 40%)": f[k >= 40],
         "Tanpa data": f[k.isna()]}[kelas]

    sel = f.dropna(subset=["Daya Tampung 2025"])
    selisih = int((sel["Daya Tampung 2026"] - sel["Daya Tampung 2025"]).sum()) if len(sel) else None
    med = f[KET].median()
    c = st.columns(4)
    c[0].metric("Prodi sesuai filter", f"{len(f):,}".replace(",", "."))
    c[1].metric("Total daya tampung 2026", f"{int(f['Daya Tampung 2026'].sum()):,}".replace(",", "."))
    c[2].metric("Median keketatan 2025", "-" if pd.isna(med) else f"{med:.1f}%")
    c[3].metric("Selisih daya tampung 2026 vs 2025", "-" if selisih is None else f"{selisih:+,}".replace(",", "."))

    g1, g2, g3 = st.columns(3)
    with g1:
        st.subheader("Sebaran keketatan 2025")
        bins = pd.cut(f[KET].dropna().clip(upper=99.99), bins=list(range(0, 101, 10)), right=False, include_lowest=True)
        hist = bins.value_counts().sort_index()
        hist.index = [f"{int(i.left)}-{int(i.right)}%" for i in hist.index]
        st.bar_chart(hist, y_label="Jumlah prodi", x_label="Keketatan")
    with g2:
        st.subheader("10 prodi paling ketat")
        top = f.dropna(subset=[KET]).nsmallest(10, KET)
        top = top.assign(Label=top["Program Studi"] + " | " + top["PTN"])
        st.bar_chart(top.set_index("Label")[KET], horizontal=True, x_label="Keketatan (%)", y_label="")
    with g3:
        st.subheader("Mapel pendukung terbanyak")
        cnt = f[MAPEL].stack().value_counts().head(10)
        st.bar_chart(cnt, horizontal=True, x_label="Jumlah prodi", y_label="")

    st.subheader("Daftar prodi")
    st.dataframe(f.sort_values(KET, na_position="last"), hide_index=True, use_container_width=True, height=420,
                 column_config={KET: st.column_config.NumberColumn(format="%.2f")})
    st.download_button("Unduh hasil filter (CSV)", f.to_csv(index=False).encode("utf-8"),
                       "prodi_terfilter.csv", "text/csv")


if __name__ == "__main__":
    main()
