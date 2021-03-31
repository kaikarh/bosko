from django.db import models

class Release(models.Model):
    release_name = models.CharField(max_length=128, unique=True)
    archive_name = models.CharField(max_length=200)
    archive_size = models.IntegerField(blank=True, default=0)
    stream_song_name = models.CharField(max_length=200, blank=True)
    stream_song_url = models.URLField(blank=True)
    share_link = models.URLField(blank=True)
    share_link_passcode = models.CharField(max_length=4, blank=True)
    adam_id = models.CharField(max_length=64, blank=True)
    posted = models.BooleanField(default=False)
    post_url = models.URLField(blank=True)
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{}'.format(self.release_name.replace('_', ' '))
