import pytz

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic
from django.utils import timezone
from django.db.models import Count

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.throttling import AnonRateThrottle
from rest_framework.generics import CreateAPIView

from .serializers import DaybookSerializer
from .models import Daybook

# Create your views here.

def index(request):
    data = {}

    total = len(Daybook.objects.all())
    data['total'] = total

    daily_count = Daybook.objects.values('time__date').annotate(dcount=Count('time__date')).order_by('-dcount')
    country_count = Daybook.objects.values('country').annotate(ccount=Count('country')).order_by('-ccount')

    data['top_daily_count'] = daily_count[:5]
    data['country_count'] = country_count
    return render(request, 'dsca/dash.html', {'stats': data})

class ListAllView(generic.ListView):
    model = Daybook
    template_name = 'dsca/list-all.html'
    extra_context = {'timezones': pytz.common_timezones}

    def get(self, request, *args, **kwargs):
        tzname = request.session.get('django_timezone')
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('.')

class GeneralCreateView(CreateAPIView):
    queryset = Daybook.objects.all()
    serializer_class = DaybookSerializer
    renderer_classes = [renderers.JSONRenderer]
    throttle_classes = [AnonRateThrottle]

class DaybookViewSet(viewsets.ModelViewSet):
    queryset = Daybook.objects.all()
    serializer_class = DaybookSerializer
    permission_classes = [permissions.IsAdminUser]

