# app.py
# Streamlit App: Hospital and Missing Points Map
# Author: Generated Example
# English comments, SOLID principles applied

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# -----------------------------
# DATA GENERATION FUNCTIONS
# -----------------------------
@st.cache_data
def generate_hospitals(num_hospitals=20, lat_range=(19.0, 20.0), lon_range=(-99.0, -98.0)) -> pd.DataFrame:
    data = {
        "name": [f"Hospital {i+1}" for i in range(num_hospitals)],
        "lat": np.random.uniform(lat_range[0], lat_range[1], num_hospitals),
        "lon": np.random.uniform(lon_range[0], lon_range[1], num_hospitals)
    }
    return pd.DataFrame(data)
@st.cache_data
def generate_missing_points(num_points=10, lat_range=(19.0, 20.0), lon_range=(-99.0, -98.0)) -> pd.DataFrame:
    data = {
        "lat": np.random.uniform(lat_range[0], lat_range[1], num_points),
        "lon": np.random.uniform(lon_range[0], lon_range[1], num_points)
    }
    return pd.DataFrame(data)

# -----------------------------
# METRICS FUNCTIONS
# -----------------------------

def count_hospitals(df_hospitals: pd.DataFrame) -> int:
    return len(df_hospitals)

def count_missing(df_missing: pd.DataFrame) -> int:
    return len(df_missing)

# -----------------------------
# MAP VISUALIZATION FUNCTION
# -----------------------------
@st.cache_data
def create_map(df_hospitals: pd.DataFrame, df_missing: pd.DataFrame) -> folium.Map:
    """
    Create a Folium map showing hospitals and missing points.
    """
    # Center the map around the average coordinates
    center_lat = (df_hospitals['lat'].mean() + df_missing['lat'].mean()) / 2
    center_lon = (df_hospitals['lon'].mean() + df_missing['lon'].mean()) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="CartoDB positron")

    # Hospitals layer (green)
    for _, row in df_hospitals.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=8,
            color='green',
            fill=True,
            fill_opacity=0.8,
            popup=row['name']
        ).add_to(m)

    # Missing points layer (red)
    for _, row in df_missing.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=8,
            color='red',
            fill=True,
            fill_opacity=0.8,
            popup="Missing Point"
        ).add_to(m)

    return m

# -----------------------------
# STREAMLIT APP
# -----------------------------

def main():
    st.set_page_config(page_title="Hospitals Map", layout="wide")
    st.title("Hospitals and Missing Points Map")

    # Sidebar filters
    num_hosp = st.sidebar.slider("Number of hospitals", 5, 50, 20)
    num_missing = st.sidebar.slider("Number of missing points", 5, 30, 10)

    # Generate random data
    df_hospitals = generate_hospitals(num_hosp)
    df_missing = generate_missing_points(num_missing)

    # Display metrics
    st.subheader("Summary Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Hospitals", count_hospitals(df_hospitals))
    col2.metric("Missing Points", count_missing(df_missing))

    # Display map
    st.subheader("Interactive Map")
    folium_map = create_map(df_hospitals, df_missing)
    st_folium(folium_map, width=700, height=500)

# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":
    main()
