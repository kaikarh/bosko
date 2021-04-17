# Generated by Django 3.1.5 on 2021-04-11 07:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('artist', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('genre', models.CharField(max_length=32)),
                ('cover_art', models.URLField()),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('release_name', models.CharField(max_length=256)),
                ('archive_name', models.CharField(max_length=256)),
                ('added_time', models.DateTimeField(auto_now_add=True)),
                ('size', models.IntegerField(blank=True, default=0)),
                ('encode', models.CharField(choices=[('mp3', 'MP3'), ('flac', 'FLAC'), ('aac', 'AAC')], default='flac', max_length=4)),
                ('album', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='minos.album')),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('passcode', models.CharField(blank=True, max_length=4)),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='minos.release')),
            ],
        ),
    ]