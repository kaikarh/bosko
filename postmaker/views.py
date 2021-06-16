import json, re, logging, threading

from os import path, environ
from datetime import datetime

from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Release, Link, AlbumPost
from .forms import AplForm, PostForm, ReleaseForm, LinkInlineFormSet, AlbumPostForm
from utils.amParser import Am
from utils.np import Np
from utils.baal import Baal
from utils.tonos import Tonos
from minos.views import add_to_db, update_flac_post

from . import postautomation

# Create your views here.

logger = logging.getLogger(__name__)

def main(request):
    return HttpResponse("This is the postmaker.")

def fetch_am(request):
    if request.method == 'POST':
        url = json.loads(request.body)['amurl']

        am = Am(url)
        info = am.get_album_info()

        for i, val in enumerate(info['tracklist']):
            info['tracklist'][i] = val.replace(',', ' ')

        return JsonResponse(info)
    return HttpResponse('Bad Request', status=400)

def np(request):
    context = {}
    accounts = request.session.get('np_accounts')
    context['accounts'] = accounts
    return render(request, 'postmaker/np.html', context=context)

def np_login(request):
    res = {}
    if request.method == 'POST':
        try:
            credential = json.loads(request.body)
            logger.info('Trying to login to np for user: {}'.format(credential['username']))
            np = Np()
            user = np.login(credential)
            auth = user.get('cdb_auth')
        except json.decoder.JSONDecodeError:
            return JsonResponse({"error": "Cant Parse Json"}, status=400)
        except:
            return JsonResponse({"error": "Cant Parse Username/Password"}, status=400)


        if auth:
            logger.info('login token is: {}'.format(auth))
            if not request.session.get('np_accounts', False):
                request.session['np_accounts'] = {}
            request.session['np_accounts'][credential['username']] = auth
            request.session.save()
            return JsonResponse({"cdb_auth": auth})
        else:
            logger.info('Login to np failed')
            return JsonResponse({"error": "Login Failed"}, status=400)
        # return a cdb_auth string as JSON
        return JsonResponse(res)

    return HttpResponse('Bad Request', status=400)

def np_get_user(request):
    auth = request.GET.get('cdb_auth')

    if auth:
        np = Np(cdb_auth=auth)
        username = np.get_current_user()

        if username:
            return JsonResponse({"username": username})
        else:
            return JsonResponse({"error": "wrong credential"}, status=400)

    return HttpResponse({"error": "bad request"}, status=400)

def np_post_thread(request):
    if request.method == 'POST':
        content = json.loads(request.body)
        auth = content.get('cdb_auth')
        np = Np(cdb_auth=auth)
        try:
            # replace unicode specified character to html encode
            content['message'] = content['message'].replace('•', '&#8226;')
            post = np.post_thread(content.get('subject').encode('gbk', 'ignore'),
                        content.get('message').encode('gbk', 'ignore'),
                        forum_id=content.get('forum_id'),
                        typeid=content.get('typeid'))
        except Exception as err:
            logger.warning(err)
            return JsonResponse({"error": "error posting"}, status=400)

        return JsonResponse(post)

    return HttpResponse('Bad Request', status=400)

@csrf_exempt
def np_edit_thread(request):
    if request.method == 'POST':
        content = json.loads(request.body)
        auth = content.get('cdb_auth')
        np = Np(cdb_auth=auth)
        try:
            post = np.edit_thread(content.get('post_url'),
                        content.get('subject').encode('gbk', 'ignore'),
                        content.get('message').encode('gbk', 'ignore'))
        except Exception as err:
            logger.warning(err)
            return JsonResponse({"error": "error posting"}, status=400)

        return JsonResponse({"error": 0, "url": post})

    return HttpResponse('Bad Request', status=400)

def post_to_forum_with_id(request):
    if request.method == 'POST':
        try:
            content = json.loads(request.body)
            pk = content['pk']
            a_id = content['a_id']
            release = Release.objects.get(pk=pk)
            auto_post(release, a_id=a_id, forced=True)

        except Exception as err:
            logger.warning(err)
            return JsonResponse({"error": "error posting"}, status=400)

        return JsonResponse({"error": 0})

    return HttpResponse('Bad Request', status=400)    

class ReleaseList(ListView):
    model = Release
    paginate_by = 300

    def get_queryset(self):
        if self.kwargs.get('type'):
            if self.kwargs['type'].upper() == 'MP3':
                return Release.objects.exclude(release_name__contains='FLAC-')
            elif self.kwargs['type'].upper() == 'FLAC':
                return Release.objects.filter(release_name__contains='FLAC-')
            else:
                raise Http404
        return Release.objects.all()

class ReleaseDetailView(LoginRequiredMixin, DetailView):
    model = Release

class ReleaseEditView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = ReleaseForm
    template_name_suffix = '_update_form'

class ReleaseLinkEditView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = LinkInlineFormSet
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

class AlbumPostCreateView(FormView):
    form_class = AlbumPostForm
    template_name = 'postmaker/albumpost_create.html'
    success_url = reverse_lazy('postmaker:albumpost-result')

    def form_valid(self, form):
        # Save form to session
        self.request.session['album_post'] = form.cleaned_data
        return super().form_valid(form)

class ReleaseAlbumPostCreateView(SingleObjectMixin, AlbumPostCreateView):
    model = Release
    template_name = 'postmaker/release_albumpost_create.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        try:
            return self.object.generate_albumpost_values()
        except Exception:
            return self.initial.copy()

class AlbumPostResultView(TemplateView):
    template_name = 'postmaker/albumpost_result.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            album_post = AlbumPost(**self.request.session.pop('album_post'))
            album_post.clean()
        except KeyError:
            # No data was supplied to generate a result
            raise Http404
        context['rendered_post'] = album_post.render_post()
        context['meta'] = {
            'accounts': self.request.session.get('np_accounts'),
            'subject': album_post
        }
        return context

def set_posted(request):
    if request.method == 'POST':
        content = json.loads(request.body)
        pk = content.get('pk')
        url = content.get('url', '')
        release = Release.objects.get(pk=pk)
        release.posted = True
        release.post_url = url
        try:
            release.full_clean()
            release.save()
        except (ValidationError, IntegrityError) as error:
            logger.info('Invalid record: {}'.format(error))
        except:
            logger.info('Write to database failed')
        return JsonResponse({"error": 0})

    return HttpResponse('Bad Request', status=400)


@csrf_exempt
def get_share_link(request):
    # JSON api for generating share link on baidu pan
    if request.method == 'POST':
        data = json.loads(request.body)
        credential = {
            'bduss': data.get('bduss'),
            'stoken': data.get('stoken')
        }
        filename = data.get('filename')

        b = Baal(credential)
        link = b.generate_link(filename)

        if link:
            return JsonResponse(link)
        else:
            return JsonResponse({'error': 1, 'message': 'Can\'t generate link'})

    return JsonResponse({'error': 1, 'message': 'Unsupported method'}, status=400)
