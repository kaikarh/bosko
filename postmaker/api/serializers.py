from rest_framework import serializers

from postmaker.models import Release, Link
from utils.np import Np

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

class NpAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=32)

    def login(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        try:
            return Np().login(validated_data).get_dict()
        except:
            return None

class NpCreateThreadSerializer(serializers.Serializer):
    cdb_auth = serializers.CharField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    forum_id = serializers.CharField(max_length=4, default='45')
    typeid = serializers.CharField(max_length=4, required=False)

    def post_thread(self, **kwargs):
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

    def post_thread(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        np = Np(cdb_auth=validated_data['cdb_auth'])

        post = np.edit_thread(
            thread_id=validated_data.get('thread_id'),
            post_id=validated_data.get('post_id'),
            subject=validated_data.get('subject').encode('gbk', 'ignore'),
            message=validated_data.get('message').encode('gbk', 'ignore'),
        )

        return post