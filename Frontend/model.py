import json
from typing import List

class MedicalCenter:
    def __init__(self, type_of_center: str, accesibility: str, name: str, city: str,
                 city_district: str, latitude: float, longitude: float,
                 population_in_district: int, street: str, is_suggested: bool = False):
        self.type_of_center = type_of_center
        self.accesibility = accesibility
        self.name = name
        self.city = city
        self.city_district = city_district
        self.latitude = latitude
        self.longitude = longitude
        self.population_in_district = population_in_district
        self.street = street
        self.is_suggested = is_suggested

    def __str__(self):
        return self.name

    @classmethod
    def from_json_list(cls, json_data: str) -> List['MedicalCenter']:
        try:
            list_of_dicts = json.loads(json_data)
        except json.JSONDecodeError:
            return []

        if not isinstance(list_of_dicts, list):
            return []

        medical_centers = []
        for data_dict in list_of_dicts:
            try:
                center = cls(**data_dict)
                medical_centers.append(center)
            except (TypeError, Exception):
                pass

        return medical_centers