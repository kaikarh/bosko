from django.db.models.query import QuerySet
import pytz

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.throttling import AnonRateThrottle
from rest_framework.generics import CreateAPIView

from .serializers import DaybookSerializer
from .models import Daybook
from postmaker.models import Release

# Create your views here.

def index(request):
    data = {}

    total = len(Daybook.objects.all())
    data['total'] = total

    daily_count = Daybook.objects.values('time__date').annotate(dcount=Count('time__date')).order_by('-time__date')
    country_count = Daybook.objects.values('country').annotate(ccount=Count('country')).order_by('-ccount')
    file_count = Daybook.objects.values('destination').annotate(fcount=Count('destination')).order_by('-fcount')

    data['daily_count'] = daily_count[:30]
    data['country_count'] = country_count
    data['file_count'] = file_count[:5]
    
    return render(request, 'dsca/dash.html', {'stats': data})

class ListAllView(LoginRequiredMixin, generic.ListView):
    model = Daybook
    queryset = Daybook.objects.all().order_by('-time')[:300]
    template_name = 'dsca/list-all.html'
    extra_context = {'timezones': pytz.common_timezones}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for record in context['object_list']:
            try:
                release = Release.objects.filter(share_link=record.destination)[0]
                record.release_name = release.release_name
            except Exception:
                continue
        return context

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

