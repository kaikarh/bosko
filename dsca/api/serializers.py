from dsca.models import LinkClickedEntry
from rest_framework import serializers

class LinkClickedEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = LinkClickedEntry
        fields = '__all__'

    def create(self, validated_data):
        validated_data = validated_data.copy()
        try:
            if x_forwarded_for := self.context['request'].headers.get('X-Forwarded-For'):
                validated_data.update(origin=x_forwarded_for.split(',')[0])
            else:
                validated_data.update(origin=self.context['request'].META['REMOTE_ADDR'])
            validated_data.update(user_agent=self.context['request'].headers.get('User-Agent', ''))
        except KeyError:
            # create is not coming from a http request
            validated_data.update(origin='0.0.0.0')
        return super().create(validated_data)
