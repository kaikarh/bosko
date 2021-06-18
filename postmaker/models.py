from os import path
import re
import datetime

from django.db import models
from django.urls import reverse
from django.template.loader import render_to_string

from utils.releaseparser import ReleaseParser

class Release(models.Model):
    release_name = models.CharField(max_length=200, unique=True)
    archive_name = models.CharField(max_length=200)
    archive_size = models.IntegerField(blank=True, default=0)
    stream_song_name = models.CharField(max_length=200, blank=True)
    stream_song_url = models.URLField(blank=True)
    adam_id = models.CharField(max_length=64, blank=True)
    lang = models.CharField(max_length=2, blank=True)
    coding = models.CharField(max_length=4, blank=True)
    rip_source = models.CharField(max_length=10, blank=True)
    posted = models.BooleanField(default=False)
    post_url = models.URLField(blank=True)
    autopost_alert = models.TextField(blank=True)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return '{}'.format(self.release_name.replace('_', ' '))
    
    def get_absolute_url(self):
        return reverse('postmaker:release-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        try:
            r = ReleaseParser.parse_name(self.release_name)
            self.lang = r.lang
            self.coding = r.coding
            self.rip_source = r.source
        except ValueError:
            # Cant parse release
            pass
        finally:
            super().save(*args, **kwargs)

    def get_fields(self):
        return [ (field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields ]
    
    def generate_albumpost_values(self):
        r = ReleaseParser.parse_name(self.release_name)
        return {
            'artist_name': r.artist,
            'collection_name': r.title,
            'release_date': r.year,
            'lq_stream_url': self.stream_song_url,
            'archive_size': self.archive_size,
            'rip_source': r.source,
            'download_links': list(self.link_set.values('url', 'passcode')),
            'coding': self.coding,
            'collection_language': self.lang
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
    #release_date = models.CharField(max_length=20, blank=True)
    release_date = models.DateField(blank=True)
    notes = models.TextField(blank=True)
    collection_language = models.CharField(max_length=2, blank=True)
    lq_stream_url = models.URLField(blank=True)
    archive_size = models.IntegerField(blank=True, default=0)
    rip_source = models.CharField(
        max_length=7,
        choices=[('cd', 'CD'), ('web', 'Web'), ('vinyl', 'Vinyl'), ('unknown', 'Unknown')],
        default='unknown'
    )
    coding = models.CharField(
        max_length=4,
        choices=[('mp3', 'MP3'), ('flac', 'FLAC'), ('aac', 'AAC')],
        default='mp3'
    )
    hidden_content = models.CharField(max_length=200, blank=True)
    miscellaneous = models.JSONField(default=list, blank=True)
    tracks = models.JSONField(default=list, blank=True)
    download_links = models.JSONField(default=list, blank=True)

    class Meta:
        managed = False

    def __str__(self):
        return '{} - {}{}'.format(
            self.artist_name,
            self.collection_name,
            ' ({})'.format(self.release_date.year) if self.release_date else ''
        )

    def clean(self):
        # Resize thumbnail
        self.artwork_url = self.artwork_url.replace('100x100bb.jpg', '600x600bb.jpg')
        # reformat release_date
        try:
            rdate = datetime.datetime.fromisoformat(str(self.release_date).replace('Z', '+00:00'))
            self.release_date = rdate.date()
        except (AttributeError, ValueError) as err:
            # release date is not a iso format date
            pass

    def render_post(self):
        # Read style file for the post thread
        def load_css(css_filename):
            css = ''
            style_file_path = path.join(path.dirname(path.realpath(__file__)),
                            'static/{}/{}'.
                            format(__name__.split('.')[0], css_filename))
            with open(style_file_path) as f:
                for line in f:
                    line = line.strip()
                    css += line
            return css
        
        #template = loader.get_template('postmaker/rendered-post.html')
        #rendered = template.render({'album': data})

        return render_to_string(
            'postmaker/rendered-post.html',
            {'album': self, 'css': load_css('threadstyle.css')}
        )
