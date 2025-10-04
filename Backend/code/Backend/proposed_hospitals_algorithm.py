import polars as pl
import pandas as pd
import numpy as np
from .models import MedicalCenter

def load_data_from_django():
    # Query Django ORM
    qs = MedicalCenter.objects.all().values(
        "id",
        "type_of_center",
        "accesibility",
        "name",
        "city",
        "city_district",
        "latitude",
        "longitude",
        "population_in_district",
        "street",
        "is_suggested",
    )

    # Convert queryset (list of dicts) into Polars DataFrame
    df = pl.DataFrame(list(qs))

    return df

def insert_into_django(df):
    # Convert Polars to list of dicts
    records = df.to_dicts()

    # Map to Django model fields if column names match
    objects = [
        MedicalCenter(
            latitude=rec["latitude"],
            longitude=rec["longitude"],
            type_of_center="TODO",
            accesibility="test",
            name="PROPOSED HOSPITAL",
            city="Madrid",
            city_district=rec["city_district"],
            population_in_district=0,
            street="MOCK STREET",
            is_suggested=bool(rec.get("is_suggested", False))  # default if not in df
        )
        for rec in records
    ]

    # Bulk insert for efficiency
    MedicalCenter.objects.bulk_create(objects, batch_size=500)

def insert_proposed_hospitals_into_object():
    
    df = load_data_from_django()

    # Step 1: Compute district centroids weighted by population
    district_centroids = df.to_pandas().groupby('city_district').apply(
        lambda x: pd.Series({
            'centroid_lat': np.ma.average(x['latitude'], weights=x['population_in_district'], ),
            'centroid_lon': np.ma.average(x['longitude'], weights=x['population_in_district']),
            'total_population': x['population_in_district'].sum(),
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
    proposals = district_centroids.sort_values(
        by='population_per_hospital', ascending=False)

    proposals_polars = pl.from_pandas(proposals)

    proposals_polars_final =  proposals_polars.with_columns(
            pl.lit(None).alias("accesibility"),
            pl.lit(None).alias("name"),
            pl.lit("Madrid").alias("city"),
            pl.lit(None).alias("street"),
            pl.lit(True).alias("is_suggested")
        ).rename({
        "proposed_lat": "latitude",
        "proposed_lon": "longitude",
    }).drop_nulls()



    insert_into_django(proposals_polars_final)
    