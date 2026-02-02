import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import os
from branca.colormap import LinearColormap
from streamlit_folium import st_folium

# ============================================================
# CONFIG STREAMLIT PAGE
# ============================================================
st.set_page_config(
    page_title="Air Quality Dashboard - Fahmi Fadillah",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# LOAD DATA
# ============================================================
def load_data():
    # Logika untuk mencari file di folder yang sama dengan script ini
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "all_data.csv")
    
    # Cek apakah file ada, jika tidak ada coba cari di folder utama (root)
    if not os.path.exists(file_path):
        file_path = "all_data.csv"

    try:
        df = pd.read_csv(file_path)
        # Konversi kolom tanggal
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        return df
    except FileNotFoundError:
        st.error(f"❌ File 'all_data.csv' tidak ditemukan di {file_path}. Pastikan file sudah di-upload ke GitHub!")
        st.stop()

df = load_data()

# ============================================================
# SIDEBAR FILTER
# ============================================================
with st.sidebar:
    st.title("🔎 Filter Data")

    # Filter Station
    stations = sorted(df["station"].unique())
    selected_station = st.multiselect(
        "Pilih Station",
        stations,
        default=stations
    )

    # Filter Rentang Tanggal
    date_range = st.date_input(
        "Rentang Tanggal",
        value=[
            df["date"].min().date(),
            df["date"].max().date()
        ]
    )

    if len(date_range) != 2:
        st.error("Mohon pilih rentang tanggal yang valid.")
        st.stop()

    start_date, end_date = date_range

    # Filter Data
    filtered_df = df[
        (df["station"].isin(selected_station)) &
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

# ============================================================
# TITLE DASHBOARD
# ============================================================
st.title("🌏 Air Quality Analysis Dashboard - Fahmi Fadillah")

st.markdown(
    f"""
    Dashboard ini dibuat untuk menjawab pertanyaan bisnis berikut:

    1. **Tren polusi PM2.5 dari tahun ke tahun di berbagai stasiun**
    2. **Pola musiman PM2.5 dan PM10 berdasarkan bulan**

    📅 Periode Data: **{start_date} s.d. {end_date}**  
    📌 Total Observasi: **{len(filtered_df):,} baris**
    """
)

# ============================================================
# SUMMARY METRICS
# ============================================================
st.subheader("📊 Ringkasan Global Polusi Udara")

col1, col2, col3 = st.columns(3)

avg_pm25 = filtered_df["PM2.5"].mean()
avg_pm10 = filtered_df["PM10"].mean()
worst_station = filtered_df.groupby("station")["PM2.5"].mean().idxmax()

with col1:
    st.metric("Rata-rata PM2.5", f"{avg_pm25:.2f} µg/m³")

with col2:
    st.metric("Rata-rata PM10", f"{avg_pm10:.2f} µg/m³")

with col3:
    st.metric("Station Terburuk (PM2.5)", worst_station)

# ============================================================
# PERTANYAAN BISNIS 1
# ============================================================
st.subheader("📈 Pertanyaan 1: Tren PM2.5 dari Tahun ke Tahun")

yearly_trend = (
    filtered_df.groupby(["year", "station"])["PM2.5"]
    .mean()
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(18, 7))

sns.lineplot(
    data=yearly_trend,
    x="year",
    y="PM2.5",
    hue="station",
    marker="o",
    ax=ax1
)

ax1.set_title("Tren Rata-rata PM2.5 dari Tahun ke Tahun per Station", fontsize=16)
ax1.set_xlabel("Tahun")
ax1.set_ylabel("Rata-rata PM2.5 (µg/m³)")
ax1.grid(True, linestyle="--", alpha=0.5)

st.pyplot(fig1)

st.markdown(
    """
    **Insight:**  
    Grafik ini menunjukkan bahwa tingkat PM2.5 mengalami fluktuasi dari tahun ke tahun,
    dengan beberapa station seperti **Wanshouxigong dan Dongsi** cenderung memiliki
    rata-rata polusi lebih tinggi dibanding station lainnya.
    """
)

# ============================================================
# PERTANYAAN BISNIS 2
# ============================================================
st.subheader("📅 Pertanyaan 2: Pola Musiman PM2.5 dan PM10 Berdasarkan Bulan")

monthly_avg = (
    filtered_df.groupby("month")[["PM2.5", "PM10"]]
    .mean()
    .reset_index()
)

fig2, ax2 = plt.subplots(figsize=(18, 6))

ax2.plot(
    monthly_avg["month"],
    monthly_avg["PM2.5"],
    marker="o",
    linewidth=2,
    label="PM2.5"
)

ax2.plot(
    monthly_avg["month"],
    monthly_avg["PM10"],
    marker="o",
    linewidth=2,
    label="PM10"
)

ax2.set_title("Seasonality Polusi Udara Berdasarkan Bulan", fontsize=16)
ax2.set_xlabel("Bulan")
ax2.set_ylabel("Rata-rata Konsentrasi Polutan (µg/m³)")
ax2.set_xticks(range(1, 13))
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.legend()

st.pyplot(fig2)

st.markdown(
    """
    **Insight:**  
    Terlihat adanya pola musiman yang jelas, di mana konsentrasi PM2.5 dan PM10
    cenderung lebih tinggi pada bulan-bulan musim dingin (akhir tahun),
    dan menurun pada musim panas. Hal ini menunjukkan efek seasonality
    pada kualitas udara Beijing.
    """
)

# ============================================================
# ANALISIS LANJUTAN: PETA PERSEBARAN PM2.5
# ============================================================
st.subheader("🗺️ Analisis Lanjutan: Persebaran PM2.5 Antar Station")

station_pm25 = filtered_df.groupby("station", as_index=False)["PM2.5"].mean()

station_coords = {
    "Aotizhongxin": (40.00, 116.41),
    "Changping": (40.20, 116.23),
    "Dingling": (40.30, 116.22),
    "Dongsi": (39.93, 116.42),
    "Guanyuan": (39.94, 116.36),
    "Gucheng": (39.93, 116.23),
    "Huairou": (40.36, 116.64),
    "Nongzhanguan": (39.97, 116.47),
    "Shunyi": (40.14, 116.72),
    "Tiantan": (39.87, 116.43),
    "Wanliu": (39.99, 116.32),
    "Wanshouxigong": (39.87, 116.37)
}

station_pm25["lat"] = station_pm25["station"].map(lambda x: station_coords[x][0])
station_pm25["lon"] = station_pm25["station"].map(lambda x: station_coords[x][1])

m = folium.Map(location=[39.9, 116.4], zoom_start=9)

colormap = LinearColormap(
    colors=["#ffffff", "#ff0000", "#000000"],
    vmin=station_pm25["PM2.5"].min(),
    vmax=station_pm25["PM2.5"].max()
)

colormap.caption = "Rata-rata PM2.5 (µg/m³)"

for _, row in station_pm25.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=8,
        popup=f"{row['station']}<br>PM2.5: {row['PM2.5']:.2f}",
        color=colormap(row["PM2.5"]),
        fill=True,
        fill_opacity=0.8
    ).add_to(m)

colormap.add_to(m)

st_folium(m, width=1200, height=500)

st.markdown(
    """
    **Insight:**  
    Peta ini menunjukkan hotspot polusi udara berdasarkan rata-rata PM2.5.
    Station dengan warna paling gelap menandakan tingkat polusi tertinggi.
    """
)

# ============================================================
# FOOTER
# ============================================================
