# Generated by Django 3.2.5 on 2021-08-27 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moons', '0008_auto_20210827_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='miningtax',
            name='flat_tax_rate',
            field=models.DecimalField(
                decimal_places=2, default=0.0, max_digits=5),
        ),
    ]
