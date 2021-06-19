
from rest_framework.throttling import AnonRateThrottle
from rest_framework.generics import CreateAPIView

from dsca.models import LinkClickedEntry
from .serializers import LinkClickedEntrySerializer


class LinkClickedEntryCreateAPIView(CreateAPIView):
    queryset = LinkClickedEntry.objects.all()
    serializer_class = LinkClickedEntrySerializer
    throttle_classes = [AnonRateThrottle]
