from rest_framework import serializers
from .models import *

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ['url', 'passcode']

class ReleaseSerializer(serializers.ModelSerializer):
    link_set = LinkSerializer(many=True, read_only=True)
    class Meta:
        model = Release
        fields = ['release_name', 'added_time', 'size', 'encode', 'link_set']

class AlbumSerializer(serializers.ModelSerializer):
    release_set = ReleaseSerializer(many=True, read_only=True)
    class Meta:
        model = Album
        fields = ['id', 'artist', 'title', 'genre', 'cover_art', 'date', 'release_set']
