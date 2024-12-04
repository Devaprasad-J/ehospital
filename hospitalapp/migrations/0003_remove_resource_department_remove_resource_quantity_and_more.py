# Generated by Django 5.1.1 on 2024-12-03 13:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0002_facility_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='department',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='quantity',
        ),
        migrations.AddField(
            model_name='resource',
            name='content',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='resource',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hospitalapp.doctor'),
        ),
    ]