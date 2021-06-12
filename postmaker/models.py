import re

from django.db import models
from django.urls import reverse

from utils.releaseparser import ReleaseParser

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
    
    def get_absolute_url(self):
        return reverse('postmaker:release_detail', kwargs={'pk': self.pk})

    def get_fields(self):
        return [ (field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields ]
    
    def albumpost_values(self):
        r = ReleaseParser.parse_name(self.release_name)
        return {
            'artist_name': r.artist,
            'collection_name': r.title,
            'release_date': r.year,
            'lq_stream_url': self.stream_song_url,
            'archive_size': self.archive_size,
            'rip_source': r.source,
            'download_links': list(self.link_set.values('url', 'passcode'))
        }

class Link(models.Model):
    url = models.URLField(unique=True)
    passcode = models.CharField(max_length=4, blank=True)
    original_poster = models.CharField(max_length=128, blank=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE)


class AlbumPost(models.Model):
    artist_name = models.CharField(max_length=200)
    collection_name = models.CharField(max_length=200)
    artwork_url = models.URLField(default='https://a.radikal.ru/a41/2104/ec/b998218537aa.png', max_length=300)
    genre_name = models.CharField(max_length=32, default='Unknown', blank=True)
    release_date = models.CharField(max_length=12, blank=True)
    notes = models.TextField(blank=True)
    lq_stream_url = models.URLField(blank=True)
    archive_size = models.IntegerField(blank=True, default=0)
    rip_source = models.CharField(
        max_length=7,
        choices=[('cd', 'CD'), ('web', 'Web'), ('vinyl', 'Vinyl'), ('unknown', 'Unknown')],
        default='unknown'
    )
    hidden_content = models.CharField(max_length=200, blank=True)
    miscellaneous = models.JSONField(default=list, blank=True)
    tracks = models.JSONField(default=list, blank=True)
    download_links = models.JSONField(default=list, blank=True)

    def __init__(self, track_str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if track_str:
            self.extract_track_data(track_str)

    def extract_track_data(self, tracks_string):
        def write_formatted_tracks(tracks_list):
            for t in tracks_list:
                if t:
                    self.tracks.append({'name': t})
            return self.tracks

        if not tracks_string.count('\n'):
            # Single line, comma seperated track string
            tracks = tracks_string.split(',')
            return write_formatted_tracks(tracks)
        else:
            # bootcamp filter
            exp = re.compile(r"([\w\(\)\ \.\&\’\/\[\]]+)(?:\W\d+:\d+)")
            # simple filter
            #exp = re.compile(r"\ ([a-zA-Z\ ]+)")
            tracks = exp.findall(tracks_string)
            return write_formatted_tracks(tracks)

    class Meta:
        managed = False
