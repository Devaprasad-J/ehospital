# Generated by Django 5.1.1 on 2024-12-03 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='facility_images/'),
        ),
    ]
