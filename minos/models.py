from django.db import models

class Album(models.Model):
    artist = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=32, default='Unknown')
    adam_id = models.IntegerField(default=0)
    cover_art = models.URLField(default='https://a.radikal.ru/a41/2104/ec/b998218537aa.png')
    date = models.DateField()

class Release(models.Model):
    release_name = models.CharField(max_length=256)
    archive_name = models.CharField(max_length=256, default='N/A')
    added_time = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(blank=True, default=0)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    encode = models.CharField(
        max_length=4,
        choices=[('mp3', 'MP3'), ('flac', 'FLAC'), ('aac', 'AAC')],
        default='flac',
    )

class Link(models.Model):
    url = models.URLField()
    passcode = models.CharField(max_length=4, blank=True)
    original_poster = models.CharField(max_length=128, blank=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
