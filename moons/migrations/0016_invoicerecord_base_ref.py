# Generated by Django 3.2.5 on 2021-09-06 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moons', '0015_auto_20210906_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicerecord',
            name='base_ref',
            field=models.CharField(default='', max_length=72),
        ),
    ]