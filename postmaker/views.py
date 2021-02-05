import json
import re

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .amParser import Am
from .forms import AplForm, PostForm

# Create your views here.

def main(request):
    return HttpResponse("This is the postmaker.")

def fetchapi(request):
    if request.method == 'POST':
        url = json.loads(request.body)['amurl']

        am = Am(url)
        info = am.get_album_info()

        for i, val in enumerate(info['tracklist']):
            info['tracklist'][i] = val.replace(',', ' ')

        return JsonResponse(info)

def make(request):
    aplform = AplForm()
    form = PostForm()

    # post request
    if request.method == 'POST':
        form = PostForm(request.POST)

        if form.is_valid():
            data = dict(form.cleaned_data)
            if data['apple_tracks']:
                data['tracks'] = data['apple_tracks'].split(',')
            else:
                # couldnt get tracklist from apple, try to parse tracklist 
                # Amazon Music filter
                #exp = re.compile(r"([\w\(\)\ \'\!\[\]\?]{2,})(?:\t[0-9\:]+)")
                # Wikipedia music filter
                #exp = re.compile(r'\"(.+)\"')
                # bootcamp filter
                exp = re.compile(r"([\w\(\)\ \.\&\’\/\[\]]+)(?:\W\d+:\d+)")
                # simple filter
                #exp = re.compile(r"\ ([a-zA-Z\ ]+)")
                tracks = exp.findall(data['tracks'])
                data['tracks'] = tracks

            return render(request, 'postmaker/rendered-post.html', context={'album': data})
        else:
            # send back the form with error message
            return render(request, 'postmaker/make-post.html', {'form': form, 'aplfrm': aplform})

    # normal get request - render an empty form
    return render(request, 'postmaker/make-post.html', {'form': form, 'aplfrm': aplform})

