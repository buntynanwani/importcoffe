import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
from typing import List, Tuple
# from model import MedicalCenter # Asumo que MedicalCenter existe y está definida correctamente

# --- Definición de MedicalCenter (Placeholder si no tienes el archivo model.py) ---
class MedicalCenter:
    """Clase placeholder para simular el objeto del backend."""
    def __init__(self, lat: float, lon: float):
        self.latitude = lat
        self.longitude = lon

    @staticmethod
    def from_json_list(json_data: str) -> List['MedicalCenter']:
        """Simula la deserialización. Aquí solo devuelve una lista vacía para evitar errores de importación/ejecución si no existe el backend."""
        # Nota: En una app real, usarías 'json.loads(json_data)' y construirías los objetos.
        # Aquí se devuelve una lista vacía si la data no es parseable o si el backend no está disponible.
        # Para propósitos de demostración, se devolverá data simulada si el backend falla.
        # return []
        # Simulación de datos si el backend no está levantado

        # Generar 5 puntos aleatorios si la llamada al API fallara
        num_simulated = 5
        simulated_centers = []
        lat_range=(19.0, 20.0)
        lon_range=(-99.0, -98.0)
        lats = np.random.uniform(lat_range[0], lat_range[1], num_simulated)
        lons = np.random.uniform(lon_range[0], lon_range[1], num_simulated)
        for lat, lon in zip(lats, lons):
            simulated_centers.append(MedicalCenter(lat, lon))
        return simulated_centers
# ---------------------------------------------------------------------------------

# --- CONSTANTS & UTILITY FUNCTIONS ---

# Asegúrate de que este URL sea accesible desde el entorno de Streamlit
API_ENDPOINT = "http://Backend:8080/api/get_proposed_medical_centers"

@st.cache_data
def geocode_location(location_name: str) -> Tuple[float, float] | None:
    """
    Converts a location name (city, address) into (latitude, longitude) coordinates.
    Uses Nominatim geocoding service.
    """
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
def generate_hospitals(num_hospitals=20, lat_range=(19.0, 20.0), lon_range=(-99.0, -98.0), street_address="Av. Central, #123") -> pd.DataFrame:
    """Generates simulated hospital data points (Points in Green)."""
    data = {
        "name": [f"Hospital {i+1}" for i in range(num_hospitals)],
        "lat": np.random.uniform(lat_range[0], lat_range[1], num_hospitals),
        "lon": np.random.uniform(lon_range[0], lon_range[1], num_hospitals),
        "street": [street_address] * num_hospitals
    }
    return pd.DataFrame(data)

# 🚨 CAMBIO CLAVE: Se eliminó @st.cache_data para usar st.session_state 🚨
def fetch_and_process_missing_points(url: str) -> pd.DataFrame:
    """
    Fethches proposed medical centers from the API.
    Returns a DataFrame for mapping.
    """
    st.info("Intentando obtener datos del backend...")

    try:
        # 1. Fetch data from the API endpoint
        # NOTA: Si 'http://Backend:8080' es un nombre de servicio de Docker,
        # puede que necesites el IP directo o un proxy si no estás en la misma red.
        response = requests.get(url, timeout=40)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        json_data = response.text
        st.code(response.text, language='json')
        st.success("✅ Datos obtenidos exitosamente del backend.")
        # Opcional: mostrar la respuesta JSON (comentar en producción)
        # st.code(response.text, language='json')

        # 2. Convert JSON string to list of MedicalCenter objects
        centers: List[MedicalCenter] = MedicalCenter.from_json_list(json_data)

        # 3. Convert list of objects to a DataFrame for map rendering
        if not centers:
            st.warning("El backend devolvió una lista vacía de centros.")
            return pd.DataFrame({"lat": [], "lon": []})

        data = {
            "lat": [center.latitude for center in centers],
            "lon": [center.longitude for center in centers]
        }
        return pd.DataFrame(data)

    except requests.exceptions.RequestException as e:
        # st.error(f"❌ Error al obtener datos del API ({url}): {e}")
        st.warning(f"❌ Fallo de conexión o respuesta del API. Usando datos simulados: {e}")
        # Retorna data simulada si la conexión falla para no romper la app
        return MedicalCenter.from_json_list("").pipe(
            lambda centers: pd.DataFrame({
                "lat": [c.latitude for c in centers],
                "lon": [c.longitude for c in centers]
            })
        )
    except Exception as e:
        st.error(f"❌ Error al procesar los datos recibidos: {e}")
        return pd.DataFrame({"lat": [], "lon": []})

# --- METRICS FUNCTIONS ---

def count_hospitals(df_hospitals: pd.DataFrame) -> int:
    """Counts the total number of hospitals."""
    return len(df_hospitals)

def count_missing(df_missing: pd.DataFrame) -> int:
    """Counts the total number of missing points."""
    return len(df_missing)

# --- MAP VISUALIZATION FUNCTION ---

def create_map(df_hospitals: pd.DataFrame, df_missing: pd.DataFrame, point_filter: str, search_center: Tuple[float, float] | None = None) -> folium.Map:
    """
    Create a Folium map showing hospitals and missing points.
    """

    # 1. Priority: User search coordinates
    if search_center:
        center_lat, center_lon = search_center
        zoom_level = 12

        # 2. Second priority: Center on existing data points
    elif not df_hospitals.empty or not df_missing.empty:
        all_lats = list(df_hospitals['lat']) + list(df_missing['lat'])
        all_lons = list(df_hospitals['lon']) + list(df_missing['lon'])
        center_lat = np.mean(all_lats) if all_lats else 19.4326 # Default CDMX
        center_lon = np.mean(all_lons) if all_lons else -99.1332 # Default CDMX
        zoom_level = 10

        # 3. Default center (CDMX area)
    else:
        center_lat, center_lon = 19.4326, -99.1332  # Default center (CDMX)
        zoom_level = 10

        # Initialize the map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles="OpenStreetMap")

    # Draw Hospitals (Green Cross Icon)
    if point_filter in ["All", "Hospitals (Green)"]:
        for _, row in df_hospitals.iterrows():
            popup_text = f"""
            <b>{row['name']}</b><br>
            Street: {row['street']}<br>
            Lat: {row['lat']:.4f}<br>
            Lon: {row['lon']:.4f}
            """
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='green', icon='plus', prefix='fa') # Icono de cruz verde
            ).add_to(m)

    # Draw Missing Points (Red Cross Icon)
    if point_filter in ["All", "Missing Hospitals (Red)"]:
        for _, row in df_missing.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=f"Missing Point: Lat {row['lat']:.4f}, Lon {row['lon']:.4f}",
                icon=folium.Icon(color='red', icon='plus', prefix='fa') # Icono de cruz roja
            ).add_to(m)

    return m

# --- STREAMLIT APP ---

def main():
    st.set_page_config(
        page_title="VitalScan",
        layout="wide",
        page_icon="images/logo.png"
    )


    # Inicialización de la caché y el estado de la aplicación
    if 'search_location' not in st.session_state:
        st.session_state.search_location = ""
    if 'center_coords' not in st.session_state:
        st.session_state.center_coords = None # (lat, lon) or None

    # 🚨 NUEVA LÓGICA DE CACHÉ DE SESIÓN PARA LOS DATOS DEL BACKEND 🚨
    # Inicializar la caché para los datos del backend
    if 'df_missing_cached' not in st.session_state:
        st.session_state.df_missing_cached = None

        # 1. Si los datos NO han sido cargados (es la primera ejecución), se hace la llamada al backend.
    if st.session_state.df_missing_cached is None:
        # Usamos un spinner para indicar que la llamada al API está en progreso
        with st.spinner("⏳ Conectando con el backend y cargando puntos faltantes..."):
            df_missing_data = fetch_and_process_missing_points(API_ENDPOINT)

        # Almacenamos el resultado (el DataFrame) en la sesión.
        # Esto provoca una RECARGA IMPLÍCITA con los datos listos.
        st.session_state.df_missing_cached = df_missing_data

    # 2. Usar los datos cacheados para el resto del script
    df_missing = st.session_state.df_missing_cached

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

    st.title("Hospitals and Missing Points Map")

    # --- SIDEBAR (Navigation/Control Panel) ---
    with st.sidebar:
        col_logo, col_title = st.columns([1, 2])
        with col_logo:
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

    # --- MAIN CONTENT ---

    # Generar data de hospitales (esta sí usa @st.cache_data, lo cual es correcto)
    df_hospitals = generate_hospitals(30)

    # df_missing ya está definida con el valor de st.session_state.df_missing_cached

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
                    <i class="fas fa-map-marker-slash text-lg mr-2 text-red-600"></i> Missing Points
                </div>
                <div class="text-4xl font-extrabold text-gray-900">{count_missing(df_missing)}</div>
                <div class="text-xs font-semibold text-red-600 mt-2">-5 <i class="fas fa-arrow-down ml-1"></i></div>
            </div>
            """, unsafe_allow_html=True
        )

    # Search Controls and Action Buttons
    with col_search_controls:
        search_input = st.text_input(
            "📍 Search Map Location:",
            key="location_input_key",
            placeholder="e.g., London, UK or 10 Downing St",
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
                    st.session_state.center_coords = (19.4326, -99.1332) # Fall back to CDMX
                    if st.session_state.search_location:
                        st.warning(f"Could not find coordinates for: **{st.session_state.search_location}**")

        with cog_col:
            st.markdown(
                """<i class="fas fa-cog text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>""", unsafe_allow_html=True
            )
        with download_col:
            st.markdown(
                """<i class="fas fa-download text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>""", unsafe_allow_html=True
            )
        with filter_col:
            st.markdown(
                """<i class="fas fa-filter text-gray-600 hover:bg-gray-100 p-2 rounded-lg cursor-pointer transition duration-200"></i>""", unsafe_allow_html=True
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

    st.markdown('</div>', unsafe_allow_html=True)

# --- RUN APP ---

if __name__ == "__main__":
    main()