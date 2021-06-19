from rest_framework import serializers

from postmaker.models import Release, Link
from postmaker.postautomation import autopost
from utils.np import Np
from utils.baal import Baal
from utils.amParser import Am

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ['url', 'passcode', 'original_poster']

class ReleaseSerializer(serializers.ModelSerializer):
    link_set = LinkSerializer(many=True, partial=True)

    class Meta:
        model = Release
        fields = [
            'pk',
            'release_name',
            'archive_name',
            'archive_size',
            'stream_song_name',
            'stream_song_url',
            'link_set',
            'adam_id',
            'posted',
            'post_url',
            'time',
        ]

    # We have to rewrite the create method because nested serializers
    def create(self, validated_data):
        links_data = validated_data.pop('link_set')
        release = Release.objects.create(**validated_data)
        for link in links_data:
            Link.objects.create(release=release, **link)
        return release

    def validate_link_set(self, value):
        if len(value) > 0: return value
        raise serializers.ValidationError('Must contain at least a link')

class BaalShareLinkCreateSerializer(serializers.Serializer):
    bduss = serializers.CharField()
    stoken = serializers.CharField()
    filename = serializers.CharField()

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        b = Baal({ key: validated_data[key] for key in ('bduss', 'stoken') })
        return b.generate_link(validated_data['filename'])

class ReleaseWithaIDSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    a_id = serializers.IntegerField()

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        release = Release.objects.get(pk=validated_data['pk'])
        autopost(release, a_id=validated_data['a_id'], forced=True)
        return 'OK'

class ReleaseWithForumPostURLSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    url = serializers.URLField(max_length=300)

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        release = Release.objects.get(pk=validated_data['pk'])
        release.posted = True
        release.post_url = validated_data['url']
        release.full_clean()
        release.save()
        return 'OK'

class NpAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=32)

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        return Np().login(validated_data).get_dict()

class NpCreateThreadSerializer(serializers.Serializer):
    cdb_auth = serializers.CharField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    forum_id = serializers.CharField(max_length=4, default='45')
    typeid = serializers.CharField(max_length=4, required=False)

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        np = Np(cdb_auth=validated_data['cdb_auth'])

        post = np.post_thread(
            validated_data.get('subject').encode('gbk', 'ignore'),
            validated_data.get('message').encode('gbk', 'ignore'),
            forum_id=validated_data.get('forum_id'),
            typeid=validated_data.get('typeid')
        )

        return post

class NpEditThreadSerializer(NpCreateThreadSerializer):
    thread_id = serializers.CharField()
    post_id = serializers.CharField()

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        np = Np(cdb_auth=validated_data['cdb_auth'])

        post = np.edit_thread(
            thread_id=validated_data.get('thread_id'),
            post_id=validated_data.get('post_id'),
            subject=validated_data.get('subject').encode('gbk', 'ignore'),
            message=validated_data.get('message').encode('gbk', 'ignore'),
        )

        return post

class AplMusicSerializer(serializers.Serializer):
    amurl = serializers.URLField(max_length=300)
    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        return_data = Am(validated_data['amurl']).get_album_info()
        return_data.update(tracklist=[ track.replace(',', ' ') for track in return_data['tracklist'] ])
        return return_data