# Generated by Django 4.2.8 on 2023-12-13 09:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moons', '0017_moonrental'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='moonfrack',
            options={'permissions': (('view_available', 'Can View Configured Public Moons'), ('view_corp', 'Can View Own Corps Moons'), ('view_alliance',
                                     'Can View Own Alliances Moons'), ('view_all', 'Can View All Moons'), ('view_limited_future', 'Can View a configured limited subset of future moons'))},
        ),
    ]
