import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
import json
from typing import List, Tuple

# --- MADRID CONSTANTS ---
MADRID_LAT = 40.4168  # Central latitude of Madrid
MADRID_LON = -3.7038 # Central longitude of Madrid
# Ranges to generate simulated points near Madrid
MADRID_LAT_RANGE = (40.35, 40.50)
MADRID_LON_RANGE = (-3.80, -3.60)
# -------------------------------------

# --- MedicalCenter Definition ---

class MedicalCenter:
    def __init__(self, type_of_center: str = "Hospital", accesibility: str = "Total", name: str = "Center", city: str = "Madrid",
                 city_district: str = "Centro", latitude: float = MADRID_LAT, longitude: float = MADRID_LON,
                 population_in_district: int = 100000, street: str = "Default St", is_suggested: bool = False,
                 lat: float = None, lon: float = None): # Added lat/lon as aliases for compatibility

        # Prioritize 'latitude'/'longitude' if provided, fall back to 'lat'/'lon'
        self.latitude = latitude if latitude is not None else lat
        self.longitude = longitude if longitude is not None else lon

        # Ensure name and street are present for Green points in the map popup
        self.name = name
        self.street = street

        self.type_of_center = type_of_center
        self.accesibility = accesibility
        self.city = city
        self.city_district = city_district
        self.population_in_district = population_in_district
        self.is_suggested = is_suggested

    def __str__(self):
        return self.name

    @staticmethod
    def from_json_list(json_data: str, is_missing: bool = False) -> List['MedicalCenter']:
        """
        Processes the JSON string into a list of MedicalCenter objects.
        If parsing fails, it returns simulated data (fallback).
        """
        centers: List['MedicalCenter'] = []
        try:
            data = json.loads(json_data)

            if not isinstance(data, list):
                raise ValueError("JSON data is not a list.")

            for item in data:
                # Use a dictionary comprehension to filter out None or missing values
                # and use default values defined in __init__

                # Use 'lat'/'lon' or 'latitude'/'longitude'
                lat = float(item.get('latitude') or item.get('lat', MADRID_LAT))
                lon = float(item.get('longitude') or item.get('lon', MADRID_LON))

                # Extract necessary string data, using defaults for non-critical fields
                name = item.get('name', f"Suggested Center {len(centers) + 1}" if is_missing else f"Hospital {len(centers) + 1}")
                street = item.get('street', "Unknown Street")

                centers.append(MedicalCenter(
                    latitude=lat,
                    longitude=lon,
                    name=name,
                    street=street,
                    is_suggested=is_missing,
                    # Pass other expected fields if available
                    type_of_center=item.get('type_of_center', 'Hospital'),
                    accesibility=item.get('accesibility', 'Total'),
                    city=item.get('city', 'Madrid'),
                    city_district=item.get('city_district', 'Centro'),
                    population_in_district=item.get('population_in_district', 100000)
                ))

            if centers:
                return centers

            # If JSON was valid but empty
            if is_missing:
                st.warning("Backend returned a valid but empty list for Missing Hospitals. Using simulated data.")
            else:
                st.warning("Backend returned a valid but empty list for Existing Hospitals. Using simulated data.")

        except (json.JSONDecodeError, ValueError) as e:
            if json_data: # Only show error if data was received but couldn't be decoded/processed
                st.error(f"JSON Decode/Process Error, backend response is invalid: {e}")
        except Exception as e:
            st.error(f"Error processing JSON structure: {e}")


        # Fallback: Generate simulated data
        num_simulated = 5 if is_missing else 30
        simulated_centers = []
        lats = np.random.uniform(MADRID_LAT_RANGE[0], MADRID_LAT_RANGE[1], num_simulated)
        lons = np.random.uniform(MADRID_LON_RANGE[0], MADRID_LON_RANGE[1], num_simulated)
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            center_name = f"Simulated {'Missing' if is_missing else 'Hospital'} {i+1}"
            street_name = f"Simulated St {i+1}, Madrid"
            simulated_centers.append(MedicalCenter(
                latitude=lat,
                longitude=lon,
                name=center_name,
                street=street_name,
                is_suggested=is_missing
            ))

        return simulated_centers
# ---------------------------------------------------------------------------------

# --- CONSTANTS & UTILITY FUNCTIONS ---

API_ENDPOINT_MISSING = "http://Backend:8080/api/get_proposed_medical_centers"
API_ENDPOINT_HOSPITALS = "http://Backend:8080/api/get_medical_centers"

@st.cache_data
def geocode_location(location_name: str) -> Tuple[float, float] | None:
    """Converts a location name (city, address) into (latitude, longitude) coordinates."""
    if not location_name:
        return None
    try:
        geolocator = Nominatim(user_agent="vitalscan_app")
        location = geolocator.geocode(location_name, timeout=30)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except (GeocoderTimedOut, GeocoderServiceError, AttributeError):
        return None

# --- DATA ACQUISITION & PROCESSING FUNCTIONS ---

@st.cache_data
def fetch_and_process_hospitals(url: str) -> pd.DataFrame:
    """
    Fetches existing medical centers (Hospitals - Green) from the API.
    Returns a DataFrame for mapping.
    """
    st.info("Attempting to get Existing Hospitals (Green) from the backend...")
    raw_json_data = ""

    try:
        # 1. Fetch data from the API endpoint
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        raw_json_data = response.text

        st.success("✅ Existing Hospitals successfully retrieved from the backend.")

        # 2. Convert JSON string to list of MedicalCenter objects
        centers: List[MedicalCenter] = MedicalCenter.from_json_list(raw_json_data, is_missing=False)

        # 3. Convert list of objects to a DataFrame for map rendering
        if not centers:
            # This case is handled by the fallback inside MedicalCenter.from_json_list
            return pd.DataFrame({"lat": [], "lon": [], "name": [], "street": []})

        data = {
            "lat": [center.latitude for center in centers],
            "lon": [center.longitude for center in centers],
            "name": [center.name for center in centers],
            "street": [center.street for center in centers]
        }
        return pd.DataFrame(data)

    except requests.exceptions.RequestException as e:
        st.warning(f"❌ Connection or API response failed for Existing Hospitals. Using simulated data: {e}")

        # Fallback to simulated data via MedicalCenter.from_json_list(empty string)
        centers = MedicalCenter.from_json_list("", is_missing=False)

        data = {
            "lat": [center.latitude for center in centers],
            "lon": [center.longitude for center in centers],
            "name": [center.name for center in centers],
            "street": [center.street for center in centers]
        }
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"❌ Error processing received Hospital data: {e}")
        return pd.DataFrame({"lat": [], "lon": [], "name": [], "street": []})


@st.cache_data
def fetch_and_process_missing_points(url: str) -> Tuple[pd.DataFrame, str]:
    """
    Fetches proposed medical centers (Missing Hospitals - Red) from the API.
    Returns a DataFrame for mapping and the raw JSON data string.
    """
    st.info("Attempting to get Missing Hospitals (Red) from the backend...")
    raw_json_data = ""

    try:
        # 1. Fetch data from the API endpoint
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        raw_json_data = response.text

        st.success("✅ Missing Hospitals successfully retrieved from the backend.")

        # 2. Convert JSON string to list of MedicalCenter objects
        centers: List[MedicalCenter] = MedicalCenter.from_json_list(raw_json_data, is_missing=True)

        # 3. Convert list of objects to a DataFrame for map rendering
        if not centers:
            return pd.DataFrame({"lat": [], "lon": []}), raw_json_data

        data = {
            "lat": [center.latitude for center in centers],
            "lon": [center.longitude for center in centers]
        }
        return pd.DataFrame(data), raw_json_data

    except requests.exceptions.RequestException as e:
        st.warning(f"❌ Connection or API response failed for Missing Hospitals. Using simulated data: {e}")

        # Fallback to simulated data via MedicalCenter.from_json_list(empty string)
        centers = MedicalCenter.from_json_list("", is_missing=True)

        data = {
            "lat": [c.latitude for c in centers],
            "lon": [c.longitude for c in centers]
        }
        return pd.DataFrame(data), f"Connection Failed: {e}"

    except Exception as e:
        st.error(f"❌ Error processing received Missing Hospital data: {e}")
        return pd.DataFrame({"lat": [], "lon": []}), f"Processing Error: {e}"

# --- METRICS FUNCTIONS ---

def count_hospitals(df_hospitals: pd.DataFrame) -> int:
    """Counts the total number of hospitals."""
    return len(df_hospitals)

def count_missing(df_missing: pd.DataFrame) -> int:
    """Counts the total number of missing points."""
    return len(df_missing)

# --- MAP VISUALIZATION FUNCTION ---

def create_map(df_hospitals: pd.DataFrame, df_missing: pd.DataFrame, point_filter: str, search_center: Tuple[float, float] | None = None) -> folium.Map:
    """Create a Folium map showing hospitals and missing points."""

    # 1. Determine Map Center and Zoom
    # Using Madrid as default center
    center_lat, center_lon, zoom_level = MADRID_LAT, MADRID_LON, 10

    if search_center:
        center_lat, center_lon = search_center
        zoom_level = 12
    elif not df_hospitals.empty or not df_missing.empty:
        all_lats = list(df_hospitals['lat']) + list(df_missing['lat'])
        all_lons = list(df_hospitals['lon']) + list(df_missing['lon'])
        center_lat = np.mean(all_lats) if all_lats else center_lat
        center_lon = np.mean(all_lons) if all_lons else center_lon
        zoom_level = 11

    # Initialize the map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles="OpenStreetMap")

    # Draw Hospitals (Green Cross Icon)
    if point_filter in ["All", "Hospitals (Green)"]:
        for _, row in df_hospitals.iterrows():
            # Ensure name and street columns exist in df_hospitals
            name = row.get('name', 'Hospital')
            street = row.get('street', 'Address Unknown')

            popup_text = f"""
            <b>{name}</b><br>
            Street: {street}<br>
            Lat: {row['lat']:.4f}<br>
            Lon: {row['lon']:.4f}
            """
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='green', icon='plus', prefix='fa')
            ).add_to(m)

    # Draw Missing Hospitals (Red Cross Icon)
    if point_filter in ["All", "Missing Hospitals (Red)"]:
        for _, row in df_missing.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=f"Missing Hospital: Lat {row['lat']:.4f}, Lon {row['lon']:.4f}",
                icon=folium.Icon(color='red', icon='plus', prefix='fa')
            ).add_to(m)

    return m

# --- STREAMLIT APP ---

def main():
    st.set_page_config(
        page_title="VitalScan",
        layout="wide",
        page_icon="images/logo.png"
    )

    # Initialization of state
    if 'search_location' not in st.session_state:
        st.session_state.search_location = ""
    if 'center_coords' not in st.session_state:
        st.session_state.center_coords = None
    if 'df_missing_cached' not in st.session_state:
        st.session_state.df_missing_cached = None
    if 'raw_backend_log' not in st.session_state:
        st.session_state.raw_backend_log = ""

    # --- DATA LOADING ---

    # 1. Load Missing Hospitals (Red Points)
    if st.session_state.df_missing_cached is None:
        with st.spinner("⏳ Connecting to backend and loading missing hospitals (Red)..."):
            df_missing_data, log_data = fetch_and_process_missing_points(API_ENDPOINT_MISSING)

        st.session_state.df_missing_cached = df_missing_data
        st.session_state.raw_backend_log = log_data

    # Use cached data
    df_missing = st.session_state.df_missing_cached
    raw_backend_log = st.session_state.raw_backend_log

    # 2. Load Existing Hospitals (Green Points)
    # This function uses st.cache_data, so we don't need manual session state caching here.
    with st.spinner("⏳ Connecting to backend and loading existing hospitals (Green)..."):
        df_hospitals = fetch_and_process_hospitals(API_ENDPOINT_HOSPITALS)
    # -------------------------------------------------------------

    # --- INYECTAR TAILWIND CDN Y OVERRIDES CSS ---
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body, .stApp { background-color: #f8f9fa; }
            .main .block-container { padding: 2rem 2.5rem; }
            .css-1d391kg { background-color: #212529; border-right: 1px solid #dee2e6; padding: 1.5rem; }
            header {display: none !important;}
            .stSidebar{ background-color: #212529; }
            .stSidebar a, .stSidebar h1, .stSidebar h2, .stSidebar h3 { color: #f8f9fa !important; }
            .sidebar-link.active { color: #34d399 !important; font-weight: 700 !important; background-color: transparent !important; }
            .sidebar-link:hover { background-color: #495057 !important; color: #f8f9fa !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- TOP BAR (Main Header) ---
    col_empty, col_top_icons = st.columns([8, 2])
    with col_top_icons:
        st.markdown(
            """
            <div class="flex items-center space-x-3 justify-end">
                <i class="fas fa-user text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>
                <i class="fas fa-bell text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>
                <i class="fas fa-question-circle text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>
                <button class="bg-green-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-green-700 transition duration-200">Deploy</button>
            </div>
            """, unsafe_allow_html=True
        )

    st.title("Hospitals and Missing Hospitals Map")

    # --- SIDEBAR (Navigation/Control Panel) ---
    with st.sidebar:
        col_logo, col_title = st.columns([1, 2])
        with col_logo:
            # Use a placeholder image path if the actual image is not present
            st.image("images/logo.png", use_container_width=True)
        with col_title:
            st.markdown(
                """<h1 class='text-xl font-bold mt-0 '>VitalScan</h1>""", unsafe_allow_html=True
            )


        st.markdown(
            """
            <a href="#" class="flex items-center p-3 mb-2 rounded-lg font-bold transition duration-200 sidebar-link active">
                <i class="fas fa-tachometer-alt mr-3 text-xl"></i> Dashboard
            </a>
            
            <a href="#summary-metrics" class="flex items-center p-3 mb-2 rounded-lg transition duration-200 pl-8 text-sm sidebar-link">
                <i class="fas fa-chart-bar mr-3 text-base"></i> Overview Metrics
            </a>
            
            <a href="#interactive-map" class="flex items-center p-3 mb-2 rounded-lg transition duration-200 pl-8 text-sm sidebar-link">
                <i class="fas fa-map-marked-alt mr-3 text-base"></i> Global Map
            </a>

            <hr class='border-gray-600'>
            """,
            unsafe_allow_html=True
        )

        st.subheader("Point Filter")
        point_filter = st.selectbox(
            "Display Points:",
            options=[
                "All",
                "Hospitals (Green)",
                "Missing Hospitals (Red)"
            ],
            index=0,
            help="Select which types of points to display on the map."
        )

        # --- RAW DATA LOG ---
        st.markdown("<hr class='border-gray-600'>", unsafe_allow_html=True)
        st.subheader("Backend Raw Data Log (Missing)")

        # Log only the raw data from the missing points endpoint
        st.code(raw_backend_log, language='json')


    # --- MAIN CONTENT ---

    # 1. Metrics
    st.markdown("<h2 class='text-2xl font-semibold text-gray-900 mb-4'>Summary Metrics</h2>", unsafe_allow_html=True)

    col_hosp_metric, col_missing_metric, col_search_controls = st.columns([2, 2, 4])

    with col_hosp_metric:
        st.markdown(
            f"""
            <div class="bg-white rounded-xl shadow-lg p-6 flex flex-col justify-between h-full">
                <div class="text-sm text-gray-500 mb-1 flex items-center">
                    <i class="fas fa-hospital-alt text-lg mr-2 text-green-600"></i> Hospitals
                </div>
                <div class="text-4xl font-extrabold text-gray-900">{count_hospitals(df_hospitals)}</div>
                <div class="text-xs font-semibold text-green-600 mt-2">+10 <i class="fas fa-arrow-up ml-1"></i></div>
            </div>
            """, unsafe_allow_html=True
        )

    with col_missing_metric:
        st.markdown(
            f"""
            <div class="bg-white rounded-xl shadow-lg p-6 flex flex-col justify-between h-full">
                <div class="text-sm text-gray-500 mb-1 flex items-center">
                    <i class="fas fa-map-marker-slash text-lg mr-2 text-red-600"></i> Missing Hospitals
                </div>
                <div class="text-4xl font-extrabold text-gray-900">{count_missing(df_missing)}</div>
                <div class="text-xs font-semibold text-red-600 mt-2">-5 <i class="fas fa-arrow-down ml-1"></i></div>
            </div>
            """, unsafe_allow_html=True
        )

    # Search Controls and Action Buttons
    with col_search_controls:
        # Use a hidden label and placeholder for better aesthetics
        search_input = st.text_input(
            "📍 Search Map Location:",
            key="location_input_key",
            placeholder="e.g., Madrid, Spain or Calle Mayor 1",
            label_visibility="collapsed"
        )

        search_button_col, cog_col, download_col, filter_col = st.columns([2, 1, 1, 1])

        with search_button_col:
            if st.button("Focus Map", use_container_width=True, help="Center the map on the searched location."):
                st.session_state.search_location = search_input
                coords = geocode_location(st.session_state.search_location)

                if coords:
                    st.session_state.center_coords = coords
                else:
                    # Fallback to Madrid center
                    st.session_state.center_coords = (MADRID_LAT, MADRID_LON)
                    if st.session_state.search_location:
                        st.warning(f"Could not find coordinates for: **{st.session_state.search_location}**")

        # Placeholder icons for aesthetic
        with cog_col:
            st.markdown(
                """<div class='flex justify-center items-center h-full'><i class="fas fa-cog text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i></div>""", unsafe_allow_html=True
            )
        with download_col:
            st.markdown(
                """<div class='flex justify-center items-center h-full'><i class="fas fa-download text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i></div>""", unsafe_allow_html=True
            )
        with filter_col:
            st.markdown(
                """<div class='flex justify-center items-center h-full'><i class="fas fa-filter text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i></div>""", unsafe_allow_html=True
            )


    # 2. Interactive Map
    st.markdown("<h2 class='text-2xl font-semibold text-gray-900 mb-4 mt-8'>Interactive Map</h2>", unsafe_allow_html=True)


    map_toolbar_cols = st.columns([1, 1, 1, 1, 6])
    with map_toolbar_cols[0]:
        st.button("Layers", help="Change map layers")
    with map_toolbar_cols[1]:
        st.button("Group", help="Group nearby points")
    with map_toolbar_cols[2]:
        st.button("Draw", help="Draw shapes on the map")
    with map_toolbar_cols[3]:
        st.button("Export", help="Export map view")

    folium_map = create_map(df_hospitals, df_missing, point_filter, search_center=st.session_state.center_coords)
    st_folium(folium_map, width='100%', height=500)

# --- RUN APP ---

if __name__ == "__main__":
    main()