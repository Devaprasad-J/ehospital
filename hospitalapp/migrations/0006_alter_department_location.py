# Generated by Django 5.1.1 on 2024-12-04 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0005_alter_department_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='location',
            field=models.CharField(max_length=100),
        ),
    ]
