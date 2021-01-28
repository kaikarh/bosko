from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from .serializers import DaybookSerializer
from .models import Daybook

# Create your views here.

def index(request):
    return HttpResponse("It works")

class GeneralCreateView(CreateAPIView):
    queryset = Daybook.objects.all()
    serializer_class = DaybookSerializer

class DaybookViewSet(viewsets.ModelViewSet):
    queryset = Daybook.objects.all()
    serializer_class = DaybookSerializer
    permission_classes = [permissions.IsAdminUser]
