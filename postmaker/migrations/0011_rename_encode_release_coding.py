# Generated by Django 3.2.4 on 2021-06-16 05:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('postmaker', '0010_auto_20210616_0029'),
    ]

    operations = [
        migrations.RenameField(
            model_name='release',
            old_name='encode',
            new_name='coding',
        ),
    ]