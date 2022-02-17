# Generated by Django 3.2.4 on 2022-02-17 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('postmaker', '0013_auto_20210618_0921'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('artist', models.CharField(max_length=256)),
                ('title', models.CharField(max_length=256)),
                ('genre', models.CharField(default='Unknown', max_length=32)),
                ('adam_id', models.CharField(blank=True, max_length=64)),
                ('cover_art', models.URLField(default='https://a.radikal.ru/a41/2104/ec/b998218537aa.png')),
                ('date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='release',
            name='album',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='postmaker.album'),
        ),
    ]
