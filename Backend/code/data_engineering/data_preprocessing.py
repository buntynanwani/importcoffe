from urllib import request
from urllib.parse import urlparse
import os
import polars as pl
import os
import pandas as pd
import chardet
import pandas as pd
import numpy as np
from geopy.distance import distance

# Function to convert file to UTF-8
def convert_to_utf8(input_file, output_file=None):
    if output_file is None:
        output_file = input_file.replace('.csv', '_utf8.csv')
    
    # Detect encoding
    with open(input_file, 'rb') as f:
        raw_data = f.read()
        encoding = chardet.detect(raw_data)['encoding']
        print(f"Detected encoding: {encoding}")
    
    # Read with detected encoding and save as UTF-8
    with open(input_file, 'r', encoding=encoding, errors='replace') as f:
        content = f.read()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"File converted to UTF-8: {output_file}")
    return output_file

def download_file_urllib(url: str, local_filename: str = None) -> str:
    """
    Downloads a file from a URL using the built-in urllib.request library.

    Args:
        url (str): The URL of the file to download.
        local_filename (str, optional): The name to save the file as. 
            If None, the filename is extracted from the URL's path.

    Returns:
        str: The path to the downloaded file.
    """
    if local_filename is None:
        # Extract filename from the URL path
        path = urlparse(url).path
        local_filename = os.path.basename(path)
    
    print(f"Attempting to download {url} to {local_filename}...")

    try:
        # Use urlretrieve for a simple, one-shot download
        request.urlretrieve(url, local_filename)
        
        print(f"Successfully downloaded to {os.path.abspath(local_filename)}")
        return os.path.abspath(local_filename)
        
    except Exception as e:
        print(f"An error occurred during download: {e}")
        return None
    

health_centers_url = f"https://datos.madrid.es/egob/catalogo/212769-0-atencion-medica.csv"
population_madrid_url = f"https://datos.madrid.es/egob/catalogo/300557-0-poblacion-distrito-barrio.csv"



download_file_urllib(health_centers_url, "health_center.csv")
download_file_urllib(population_madrid_url, "population.csv")

utf8_file_health_centers = convert_to_utf8("health_center.csv")
utf8_file_population_madrid = convert_to_utf8("population.csv")

df = pl.read_csv(utf8_file_health_centers, separator=";")
df_population = pl.read_csv(utf8_file_population_madrid, separator=";", infer_schema_length=None)

df_with_type = df.with_columns(
    pl.when(pl.col("NOMBRE").str.starts_with("Centro de Salud"))
    .then(pl.lit("health_center"))
    .when(pl.col("NOMBRE").str.starts_with("Hospital"))
    .then(pl.lit("hospital"))
    .otherwise(pl.col("NOMBRE"))
    .alias("center_type")
)

df_with_type = df_with_type.with_columns(pl.col("DISTRITO").str.to_lowercase().alias("distrito"))
df_population = df_population.with_columns(
    pl.col("distrito").str.to_lowercase().str.strip_chars().alias("distrito")).filter(
        pl.col("fecha") == "1 de enero de 2024"
    ).group_by('distrito').agg(
    pl.col('num_personas').cast(pl.Float32, strict=False).sum().alias('num_personas')
)

df_with_population = df_with_type.join(
    df_population.select(["distrito", "num_personas"]), how="left", left_on="distrito", right_on="distrito"
).with_columns(
    pl.col("num_personas").cast(pl.Float64).alias("population"))

df_algorithm = df_with_population.select(
    ["NOMBRE", "distrito", "LATITUD", "LONGITUD", "population"]
)
df_algorithm_renamed = df_algorithm.rename({
    "NOMBRE": "hospital_name",
    "LATITUD": "lat",
    "LONGITUD": "lon",
    "population": "population"
})

# Step 1: Compute district centroids weighted by population
district_centroids = df_algorithm_renamed.to_pandas().groupby('distrito').apply(
    lambda x: pd.Series({
        'centroid_lat': np.average(x['lat'], weights=x['population']),
        'centroid_lon': np.average(x['lon'], weights=x['population']),
        'total_population': x['population'].sum(),
        'current_hospitals': len(x)
    })
).reset_index()

# Step 2: Compute a simple score to suggest new hospitals
# e.g., more population per existing hospital => higher need
district_centroids['population_per_hospital'] = district_centroids['total_population'] / (district_centroids['current_hospitals'] + 1)

# Step 3: Propose new hospital location (here just the centroid for simplicity)
district_centroids['proposed_lat'] = district_centroids['centroid_lat']
district_centroids['proposed_lon'] = district_centroids['centroid_lon']

# Sort districts by need
proposals = district_centroids.sort_values(by='population_per_hospital', ascending=False)

print(proposals[['distrito', 'proposed_lat', 'proposed_lon', 'population_per_hospital']])
