from urllib import request
from urllib.parse import urlparse
from .models import MedicalCenter
import polars as pl
import os
import pandas as pd
import chardet
import numpy as np

os.listdir()

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

def insert_into_django(df):
    # Convert Polars to list of dicts
    records = df.to_dicts()

    # Map to Django model fields if column names match
    objects = [
        MedicalCenter(
            type_of_center=rec["type_of_center"],
            accesibility=rec["accesibility"],
            name=rec["name"],
            city=rec["city"],
            city_district=rec["city_district"],
            latitude=rec["latitude"],
            longitude=rec["longitude"],
            population_in_district=int(rec["population_in_district"]),
            street=rec["street"],
            is_suggested=bool(rec.get("is_suggested", False))  # default if not in df
        )
        for rec in records
    ]

    # Bulk insert for efficiency
    MedicalCenter.objects.bulk_create(objects, batch_size=500)

def insert_proposed_hospitals_into_object():
    health_centers_url = f"https://datos.madrid.es/egob/catalogo/212769-0-atencion-medica.csv"
    population_madrid_url = f"https://datos.madrid.es/egob/catalogo/300557-0-poblacion-distrito-barrio.csv"

    download_file_urllib(health_centers_url, "health_center.csv")
    download_file_urllib(population_madrid_url, "population.csv")

    utf8_file_health_centers = convert_to_utf8("health_center.csv")
    utf8_file_population_madrid = convert_to_utf8("population.csv")

    df = pl.read_csv(utf8_file_health_centers, separator=";")
    df2 = pl.read_csv(utf8_file_population_madrid, separator=";", infer_schema_length=None)


#Primer data frame

    # Convert the CSV file to UTF-8
"""csv_file = "/content/212769-0-atencion-medica.csv"
utf8_file = convert_to_utf8(csv_file)
os.chdir(".")

df = pl.read_csv(utf8_file, separator=";")"""

df = df.with_columns(
    (pl.col('CLASE-VIAL') + ' ' + pl.col('NOMBRE-VIA') + ' ' + pl.col('NUM')).alias('CALLE')
)

# Corrected code with the right syntax for Polars
df = df.with_columns(
    pl.when(
        pl.col("NOMBRE").str.starts_with("Centro de Salud") | pl.col("NOMBRE").str.starts_with("CMSc")
    )
    .then(pl.lit("health_center"))
    .when(
        pl.col("NOMBRE").str.starts_with("Hospital")
    )
    .then(pl.lit("hospital"))
    .when(
        pl.col("NOMBRE").str.starts_with("Centro de Especialidades")
    )
    .then(pl.lit("clinic"))
    .otherwise(
        pl.lit(None)
    )
    .alias("center_type")
)

df = df.filter(pl.col("center_type").is_not_null())

# List of columns to drop
columns_to_drop = ["COD-BARRIO","BARRIO","DESCRIPCION","ACCESIBILIDAD","PK","COORDENADA-X","COORDENADA-Y","CONTENT-URL", "FAX", "EMAIL","TELEFONO","NOMBRE-VIA","CLASE-VIAL","TIPO-NUM","NUM","PLANTA","PUERTA","ESCALERAS","ORIENTACION","PROVINCIA","CODIGO-POSTAL","TIPO","HORARIO","EQUIPAMIENTO","DESCRIPCION-ENTIDAD"] # Add other column names you want to drop to this list

# Drop the specified columns from the DataFrame
df = df.drop(columns_to_drop)


#Segundo data frame

# Convert the CSV file to UTF-8
"""csv_file2 = "/content/poblacion_1_enero.csv"
utf8_file2 = convert_to_utf8(csv_file2)
df2 = pl.read_csv(utf8_file2, separator=";", infer_schema_length=None)"""

df2 = df2.filter( pl.col("fecha") == "1 de enero de 2024")
df2 = df2.filter(pl.col("cod_distrito") == pl.col("cod_barrio"))
df2 = df2.filter(pl.col("cod_distrito") != "Todos")

# List of columns to drop
columns_to_drop2 = ["cod_municipio","municipio","num_personas_hombres","num_personas_mujeres","cod_barrio","barrio"] # Add other column names you want to drop to this list

# Drop the specified columns from the DataFrame
df2 = df2.drop(columns_to_drop2)

#Unión de data frames

df = df.with_columns(pl.col("COD-DISTRITO").str.to_lowercase().alias("cod_distrito"))
df2 = df2.with_columns(
   pl.col("cod_distrito").str.to_lowercase().str.strip_chars().alias("cod_distrito")).group_by('cod_distrito').agg(
   pl.col('num_personas').cast(pl.Float32, strict=False).sum().alias('num_personas')
)

df_unido = df.join(
   df2.select(["cod_distrito", "num_personas"]), how="left", left_on="cod_distrito", right_on="cod_distrito"
).with_columns(
   pl.col("num_personas").cast(pl.Float64).alias("population"))

df_unido = df_unido.rename({"TRANSPORTE": "accesibility","NOMBRE": "name","LOCALIDAD": "city","DISTRITO": "city_district","LATITUD": "latitude","LONGITUD": "longitude","CALLE": "street","center_type": "type_of_center"})
df_unido = df_unido.with_columns(pl.lit(False).alias('is_suggested'))

# List of columns to drop
columns_to_drop = ["cod_distrito","COD-DISTRITO"] # Add other column names you want to drop to this list

# Drop the specified columns from the DataFrame
df_unido = df_unido.drop(columns_to_drop)
