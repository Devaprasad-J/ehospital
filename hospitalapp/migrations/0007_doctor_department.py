# Generated by Django 5.1.1 on 2024-12-04 12:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0006_alter_department_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='department',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='hospitalapp.department'),
        ),
    ]