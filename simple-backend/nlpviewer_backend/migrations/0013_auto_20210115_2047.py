# Generated by Django 3.0.4 on 2021-01-16 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nlpviewer_backend', '0012_auto_20210115_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='packID',
            field=models.IntegerField(null=True),
        ),
    ]
