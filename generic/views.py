from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

def index(request):
    context = {
        "now": timezone.now(),
        "remote_ip": request.headers.get('x_forwarded_for',
                                         request.META['REMOTE_ADDR']),
    }
    return render(request, 'generic/index.html', context)
