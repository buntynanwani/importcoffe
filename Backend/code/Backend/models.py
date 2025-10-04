from django.db import models

# Create your models here.
class   MedicalCenter(models.Model):
    type_of_center = models.CharField(max_length=255)
    accesibility = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    city_district = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    population_in_district = models.IntegerField()
    street = models.CharField(max_length=255)
    is_suggested = models.BooleanField(default=False)

    def __str__(self):
        return (self.name)