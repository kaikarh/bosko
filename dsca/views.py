import pytz

from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import LinkClickedEntry
from postmaker.models import Link

# Create your views here.

def index(request):
    data = {}

    total = len(LinkClickedEntry.objects.all())
    data['total'] = total

    daily_count = LinkClickedEntry.objects.values('time__date').annotate(dcount=Count('time__date')).order_by('-time__date')
    country_count = LinkClickedEntry.objects.values('country').annotate(ccount=Count('country')).order_by('-ccount')
    file_count = LinkClickedEntry.objects.values('destination').annotate(fcount=Count('destination')).order_by('-fcount')

    data['daily_count'] = daily_count[:30]
    data['country_count'] = country_count
    data['file_count'] = file_count[:5]
    
    return render(request, 'dsca/dash.html', {'stats': data})

class LinkClickedEntryListView(LoginRequiredMixin, ListView):
    model = LinkClickedEntry
    paginate_by = 300
    extra_context = {'timezones': pytz.common_timezones}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for obj in context['object_list']:
            if link := Link.objects.filter(url=obj.destination).first():
                obj.release_name = link.release.release_name
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
