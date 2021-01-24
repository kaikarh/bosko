from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

def index(request):
    context = {
        "now": timezone.now()
    }
    return render(request, 'generic/index.html', context)
