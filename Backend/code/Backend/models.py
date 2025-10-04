from django.db import models

# Create your models here.
class   MedicalCenter(models.Model):
    type_of_center = models.CharField()
    accesibility = models.CharField()
    name = models.CharField()
    city = models.CharField()
    city_district = models.CharField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    population_in_district = models.IntegerField()
    street = models.CharField()
    is_suggested = models.BooleanField(default=False)

    def __str__(self):
        return (self.name)