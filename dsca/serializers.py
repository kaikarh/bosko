from .models import Daybook
from rest_framework import serializers

class DaybookSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Daybook
        fields = ['time', 'referer', 'origin', 'destination']
