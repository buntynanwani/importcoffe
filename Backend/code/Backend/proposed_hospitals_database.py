import polars as pl
import os
import pandas as pd
import chardet

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

#Primer data frame

    # Convert the CSV file to UTF-8
csv_file = "/content/212769-0-atencion-medica.csv"
utf8_file = convert_to_utf8(csv_file)
os.chdir(".")

df = pl.read_csv(utf8_file, separator=";")

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
csv_file2 = "/content/poblacion_1_enero.csv"
utf8_file2 = convert_to_utf8(csv_file2)
df2 = pl.read_csv(utf8_file2, separator=";", infer_schema_length=None)

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
