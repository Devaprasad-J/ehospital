# Generated by Django 5.1.1 on 2024-12-04 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitalapp', '0003_remove_resource_department_remove_resource_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='overview',
            field=models.TextField(default='Overview not available'),
        ),
        migrations.DeleteModel(
            name='Resource',
        ),
    ]
