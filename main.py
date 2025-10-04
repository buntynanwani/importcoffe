# app.py
# Streamlit App: Hospital and Missing Points Map
# Author: Generated Example
# English comments, SOLID principles applied

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# -----------------------------
# DATA GENERATION FUNCTIONS
# -----------------------------

def generate_hospitals(num_hospitals=20, lat_range=(19.0, 20.0), lon_range=(-99.0, -98.0)) -> pd.DataFrame:
    """
    Generate a DataFrame with random hospitals.
    Single Responsibility: only generates hospital data.
    """
    data = {
        "name": [f"Hospital {i+1}" for i in range(num_hospitals)],
        "lat": np.random.uniform(lat_range[0], lat_range[1], num_hospitals),
        "lon": np.random.uniform(lon_range[0], lon_range[1], num_hospitals)
    }
    return pd.DataFrame(data)

def generate_missing_points(num_points=10, lat_range=(19.0, 20.0), lon_range=(-99.0, -98.0)) -> pd.DataFrame:
    """
    Generate a DataFrame with random points where hospitals are missing.
    Single Responsibility: only generates missing points.
    """
    data = {
        "lat": np.random.uniform(lat_range[0], lat_range[1], num_points),
        "lon": np.random.uniform(lon_range[0], lon_range[1], num_points)
    }
    return pd.DataFrame(data)

# -----------------------------
# METRICS FUNCTIONS
# -----------------------------

def count_hospitals(df_hospitals: pd.DataFrame) -> int:
    """Return the number of hospitals."""
    return len(df_hospitals)

def count_missing(df_missing: pd.DataFrame) -> int:
    """Return the number of missing points."""
    return len(df_missing)

# -----------------------------
# MAP VISUALIZATION FUNCTION
# -----------------------------
def create_map(df_hospitals: pd.DataFrame, df_missing: pd.DataFrame) -> pdk.Deck:
    """
    Create a PyDeck map showing hospitals and missing points.
    Single Responsibility: only builds map.
    Changes applied:
        - Increased point size for better visibility
        - Adjusted colors for more contrast
        - Added HTML tooltips
        - Set map style for better visual contrast
    """
    layers = []

    # -----------------------------
    # Hospitals layer (green)
    # Changes:
    #   - get_radius increased from 200 -> 400
    #   - get_color updated to brighter green with higher opacity
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=df_hospitals,
            get_position='[lon, lat]',
            get_color='[0, 200, 0, 230]',  # brighter green
            get_radius=400,                 # larger points
            pickable=True
        )
    )

    # -----------------------------
    # Missing points layer (red)
    # Changes:
    #   - get_radius increased from 200 -> 400
    #   - get_color updated to brighter red with higher opacity
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=df_missing,
            get_position='[lon, lat]',
            get_color='[255, 50, 50, 230]',  # brighter red
            get_radius=400,                   # larger points
            pickable=True
        )
    )

    # Initial view centered on the planet
    initial_view = pdk.ViewState(
        latitude=0,       # Center at the equator
        longitude=0,      # Center at the prime meridian
        zoom=1,           # Zoom out to see the whole planet
        pitch=0
    )


    # Create Deck with tooltip
    # Map style removed or set to default to ensure visibility
    return pdk.Deck(
        layers=layers,
        initial_view_state=initial_view,
        map_style=None
    )

# -----------------------------
# STREAMLIT APP
# -----------------------------

def main():
    """Main function for the Streamlit app."""
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
    deck_map = create_map(df_hospitals, df_missing)
    st.pydeck_chart(deck_map)

# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":
    main()
