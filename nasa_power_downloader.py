import requests
import pandas as pd
import json
from datetime import datetime

# Coordenadas del centro de Madrid (representa toda la ciudad)
MADRID_LAT = 40.4168
MADRID_LON = -3.7038

def download_nasa_power_data(lat, lon, start_year=2020, end_year=2024, location_name="Madrid"):
    """
    Descarga datos de NASA POWER para Madrid completo
    
    Parámetros clave para energía solar y renovable:
    - ALLSKY_SFC_SW_DWN: Irradiación solar global horizontal (kWh/m²/día)
    - CLRSKY_SFC_SW_DWN: Irradiación con cielo despejado
    - T2M: Temperatura a 2 metros (°C)
    - WS10M: Velocidad del viento a 10 metros (m/s)
    - PRECTOTCORR: Precipitación (mm/día)
    """
    
    print(f"🔍 Descargando datos para {location_name}...")
    print(f"📍 Coordenadas: Lat {lat}, Lon {lon}")
    print(f"📅 Período: {start_year}-{end_year}")
    
    # Parámetros solares, eólicos y meteorológicos
    parameters = [
        'ALLSKY_SFC_SW_DWN',  # Radiación solar total
        'CLRSKY_SFC_SW_DWN',  # Radiación cielo despejado
        'ALLSKY_SFC_SW_DNI',  # Radiación directa normal
        'ALLSKY_SFC_SW_DIFF', # Radiación difusa
        'T2M',                # Temperatura
        'T2M_MAX',            # Temperatura máxima
        'T2M_MIN',            # Temperatura mínima
        'WS10M',              # Velocidad del viento (crucial para energía eólica)
        'WS50M',              # Velocidad del viento a 50m (altura turbinas)
        'WD10M',              # Dirección del viento
        'PRECTOTCORR',        # Precipitación
        'RH2M',               # Humedad relativa
        'CLOUD_AMT'           # Nubosidad
    ]
    
    # Construir URL de la API
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params_str = ','.join(parameters)
    
    url = f"{base_url}?parameters={params_str}&community=RE&longitude={lon}&latitude={lat}&start={start_year}0101&end={end_year}1231&format=JSON"
    
    try:
        print("⏳ Conectando con NASA POWER API...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraer datos de parámetros
        if 'properties' in data and 'parameter' in data['properties']:
            params_data = data['properties']['parameter']
            
            # Convertir a DataFrame
            df = pd.DataFrame(params_data)
            
            # Resetear índice para tener las fechas como columna
            df = df.reset_index()
            df.columns = ['Fecha'] + list(df.columns[1:])
            
            # Convertir fecha a formato datetime
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y%m%d')
            
            # Renombrar columnas para mejor comprensión
            column_names = {
                'ALLSKY_SFC_SW_DWN': 'Radiacion_Solar_Global_kWh_m2',
                'CLRSKY_SFC_SW_DWN': 'Radiacion_Cielo_Despejado_kWh_m2',
                'ALLSKY_SFC_SW_DNI': 'Radiacion_Directa_Normal_kWh_m2',
                'ALLSKY_SFC_SW_DIFF': 'Radiacion_Difusa_kWh_m2',
                'T2M': 'Temperatura_Media_C',
                'T2M_MAX': 'Temperatura_Maxima_C',
                'T2M_MIN': 'Temperatura_Minima_C',
                'WS10M': 'Velocidad_Viento_10m_m_s',
                'WS50M': 'Velocidad_Viento_50m_m_s',
                'WD10M': 'Direccion_Viento_grados',
                'PRECTOTCORR': 'Precipitacion_mm',
                'RH2M': 'Humedad_Relativa_pct',
                'CLOUD_AMT': 'Nubosidad_pct'
            }
            
            df = df.rename(columns=column_names)
            
            # Agregar columnas calculadas útiles
            df['Año'] = df['Fecha'].dt.year
            df['Mes'] = df['Fecha'].dt.month
            df['Dia'] = df['Fecha'].dt.day
            df['Estacion'] = df['Mes'].apply(lambda x: 
                'Invierno' if x in [12, 1, 2] else
                'Primavera' if x in [3, 4, 5] else
                'Verano' if x in [6, 7, 8] else 'Otoño'
            )
            
            # Guardar en CSV
            filename = f"nasa_power_madrid_completo_{start_year}_{end_year}.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Datos guardados en: {filename}")
            print(f"📊 Total de registros: {len(df)}")
            
            # Mostrar estadísticas detalladas
            print_statistics(df, start_year, end_year)
            
            return df
            
        else:
            print("❌ Error: No se pudieron extraer los datos")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la API: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def print_statistics(df, start_year, end_year):
    """Imprime estadísticas detalladas de los datos"""
    
    print("\n" + "=" * 70)
    print("📈 ESTADÍSTICAS DE POTENCIAL DE ENERGÍAS RENOVABLES - MADRID")
    print("=" * 70)
    
    # ENERGÍA SOLAR
    if 'Radiacion_Solar_Global_kWh_m2' in df.columns:
        print("\n☀️  POTENCIAL SOLAR:")
        print(f"   📊 Media diaria: {df['Radiacion_Solar_Global_kWh_m2'].mean():.2f} kWh/m²/día")
        print(f"   🔼 Máxima: {df['Radiacion_Solar_Global_kWh_m2'].max():.2f} kWh/m²/día")
        print(f"   🔽 Mínima: {df['Radiacion_Solar_Global_kWh_m2'].min():.2f} kWh/m²/día")
        
        # Calcular potencial anual promedio
        años = end_year - start_year + 1
        anual_promedio = df['Radiacion_Solar_Global_kWh_m2'].sum() / años
        print(f"   📅 Total anual promedio: {anual_promedio:.2f} kWh/m²/año")
        
        # Días óptimos para solar (>5 kWh/m²/día)
        dias_optimos = len(df[df['Radiacion_Solar_Global_kWh_m2'] > 5])
        print(f"   ✨ Días con alta radiación (>5 kWh/m²): {dias_optimos} ({dias_optimos/len(df)*100:.1f}%)")
        
        # Potencial de generación para un panel de 100m²
        eficiencia = 0.18  # 18% eficiencia moderna
        generacion_anual = anual_promedio * 100 * eficiencia
        print(f"   🔋 Generación potencial (panel 100m², 18% efic.): {generacion_anual:.0f} kWh/año")
        print(f"   💰 Hogares que puede abastecer (~3,500 kWh/año): {generacion_anual/3500:.1f}")
    
    # ENERGÍA EÓLICA
    if 'Velocidad_Viento_50m_m_s' in df.columns:
        print("\n💨 POTENCIAL EÓLICO:")
        print(f"   📊 Velocidad media (50m altura): {df['Velocidad_Viento_50m_m_s'].mean():.2f} m/s")
        print(f"   🔼 Velocidad máxima: {df['Velocidad_Viento_50m_m_s'].max():.2f} m/s")
        
        # Días con viento aprovechable (>3 m/s para turbinas pequeñas)
        dias_viento = len(df[df['Velocidad_Viento_50m_m_s'] > 3])
        print(f"   ✨ Días con viento aprovechable (>3 m/s): {dias_viento} ({dias_viento/len(df)*100:.1f}%)")
        
        # Días con viento óptimo (>6 m/s)
        dias_optimo = len(df[df['Velocidad_Viento_50m_m_s'] > 6])
        print(f"   🎯 Días con viento óptimo (>6 m/s): {dias_optimo} ({dias_optimo/len(df)*100:.1f}%)")
    
    # CONDICIONES CLIMÁTICAS
    if 'Temperatura_Media_C' in df.columns:
        print("\n🌡️  CONDICIONES CLIMÁTICAS:")
        print(f"   📊 Temperatura media: {df['Temperatura_Media_C'].mean():.1f}°C")
        print(f"   🔥 Temperatura máxima: {df['Temperatura_Maxima_C'].max():.1f}°C")
        print(f"   ❄️  Temperatura mínima: {df['Temperatura_Minima_C'].min():.1f}°C")
    
    # ANÁLISIS POR ESTACIÓN
    print("\n📅 ANÁLISIS POR ESTACIÓN:")
    estaciones = df.groupby('Estacion').agg({
        'Radiacion_Solar_Global_kWh_m2': 'mean',
        'Velocidad_Viento_50m_m_s': 'mean' if 'Velocidad_Viento_50m_m_s' in df.columns else 'count'
    }).round(2)
    
    for estacion, row in estaciones.iterrows():
        print(f"   {estacion}:")
        print(f"      ☀️  Solar: {row['Radiacion_Solar_Global_kWh_m2']:.2f} kWh/m²/día")
        if 'Velocidad_Viento_50m_m_s' in df.columns:
            print(f"      💨 Viento: {row['Velocidad_Viento_50m_m_s']:.2f} m/s")

def create_monthly_summary(df):
    """Crea un resumen mensual de los datos"""
    
    monthly = df.groupby(['Año', 'Mes']).agg({
        'Radiacion_Solar_Global_kWh_m2': 'mean',
        'Velocidad_Viento_50m_m_s': 'mean' if 'Velocidad_Viento_50m_m_s' in df.columns else 'count',
        'Temperatura_Media_C': 'mean'
    }).round(2)
    
    monthly.columns = ['Radiacion_Solar_Media', 'Velocidad_Viento_Media', 'Temperatura_Media']
    monthly = monthly.reset_index()
    
    # Guardar resumen mensual
    filename_monthly = 'madrid_resumen_mensual.csv'
    monthly.to_csv(filename_monthly, index=False, encoding='utf-8')
    print(f"\n📊 Resumen mensual guardado en: {filename_monthly}")
    
    return monthly

def create_annual_summary(df):
    """Crea un resumen anual de los datos"""
    
    annual = df.groupby('Año').agg({
        'Radiacion_Solar_Global_kWh_m2': ['mean', 'sum'],
        'Velocidad_Viento_50m_m_s': 'mean' if 'Velocidad_Viento_50m_m_s' in df.columns else 'count',
        'Temperatura_Media_C': 'mean',
        'Precipitacion_mm': 'sum'
    }).round(2)
    
    annual.columns = ['_'.join(col).strip() for col in annual.columns.values]
    annual = annual.reset_index()
    
    # Calcular potencial de generación
    annual['Potencial_Solar_100m2_kWh'] = annual['Radiacion_Solar_Global_kWh_m2_sum'] * 100 * 0.18
    
    # Guardar resumen anual
    filename_annual = 'madrid_resumen_anual.csv'
    annual.to_csv(filename_annual, index=False, encoding='utf-8')
    print(f"📊 Resumen anual guardado en: {filename_annual}")
    
    return annual

# EJECUTAR DESCARGA
if __name__ == "__main__":
    print("=" * 70)
    print("🌞💨 DESCARGADOR DE DATOS NASA POWER - MADRID COMPLETO")
    print("=" * 70)
    print("📍 Obteniendo datos unificados para toda la ciudad de Madrid")
    print("=" * 70)
    
    # Descargar datos para Madrid completo
    df = download_nasa_power_data(
        lat=MADRID_LAT,
        lon=MADRID_LON,
        start_year=2020,
        end_year=2024,
        location_name="Madrid"
    )
    
    if df is not None:
        # Crear resúmenes adicionales
        print("\n" + "=" * 70)
        print("📋 GENERANDO RESÚMENES ADICIONALES")
        print("=" * 70)
        
        monthly_summary = create_monthly_summary(df)
        annual_summary = create_annual_summary(df)
        
        print("\n" + "=" * 70)
        print("✨ DESCARGA COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print("\n📁 Archivos generados:")
        print("   ✅ nasa_power_madrid_completo_2020_2024.csv (datos diarios completos)")
        print("   ✅ madrid_resumen_mensual.csv (promedios mensuales)")
        print("   ✅ madrid_resumen_anual.csv (totales y promedios anuales)")
        print("\n🎯 Próximos pasos:")
        print("   1. Importa estos datos en tu aplicación Streamlit")
        print("   2. Visualiza las zonas con mayor potencial solar/eólico")
        print("   3. Integra con el mapa interactivo para ubicaciones específicas")
        print("   4. Combina con datos de hospitales y necesidades energéticas")
        print("\n💡 Casos de uso:")
        print("   • Identificar tejados óptimos para paneles solares")
        print("   • Ubicar zonas para parques eólicos pequeños")
        print("   • Calcular autosuficiencia energética de hospitales")
        print("   • Planificar microredes de energía renovable")
        
    else:
        print("\n❌ No se pudieron descargar los datos. Verifica tu conexión a internet.")
    
    print("\n" + "=" * 70)