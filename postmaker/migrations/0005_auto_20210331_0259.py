# Generated by Django 3.1.5 on 2021-03-31 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postmaker', '0004_release_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='archive_name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='release',
            name='stream_song_name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
