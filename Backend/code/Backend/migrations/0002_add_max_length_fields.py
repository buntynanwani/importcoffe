from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Backend", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="medicalcenter",
            name="type_of_center",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="medicalcenter",
            name="accesibility",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="medicalcenter",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="medicalcenter",
            name="city",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="medicalcenter",
            name="city_district",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="medicalcenter",
            name="street",
            field=models.CharField(max_length=255),
        ),
    ]
