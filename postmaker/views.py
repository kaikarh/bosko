import json, re, logging

from os import path, environ
from datetime import datetime

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from .models import Release
from .amParser import Am
from .forms import AplForm, PostForm, ReleaseForm
from .np import Np
from .baal import Baal
from .tonos import Tonos

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
        post = np.post_thread(content.get('subject').encode('gbk', 'ignore'),
                    content.get('message').encode('gbk', 'ignore'),
                    forum_id=content.get('forum_id'),
                    typeid=content.get('typeid'))

        if post:
            return JsonResponse(post)
        else:
            return JsonResponse({"error": "error posting"}, status=400)

    return HttpResponse('Bad Request', status=400)

class ReleaseList(ListView):
    #model = Release
    context_object_name = 'release_list'
    template_name = 'postmaker/releases.html'
    queryset = Release.objects.order_by('-time')

class ReleaseDetailView(DetailView):
    model = Release
    template_name = 'postmaker/release-detail.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        form = ReleaseForm(instance=context['release'])
        context['form'] = form
        return context

class ReleaseDetailMakeView(DetailView):
    model = Release
    template_name = 'postmaker/release-detail-make.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        aplform = AplForm()
        form = PostForm({'arc_info': 'zip / Password Protected',
                         'stream_url': context['release'].stream_song_url,
                         'hidden_info': '密码：needpop.com',
                         'download_link': context['release'].share_link,
                         'download_passcode': context['release'].share_link_passcode})
        # Add in the publisher
        context['aplfrm'] = aplform
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        release = Release.objects.get(pk=kwargs['pk'])
        form = PostForm(request.POST)

        rendered = render_post(form)
        rendered_post = rendered.get('post')
        data = rendered.get('album')
        if rendered_post:
            accounts = request.session.get('np_accounts')
            print(request.session.items())
            return render(request,
                          'postmaker/result.html',
                          context={'code': rendered_post,
                                   'album': data,
                                   'accounts': accounts,
                                   'release': release})
        return render(request, 'postmaker/make-post.html', {'form': form, 'aplfrm': aplform})

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


def render_post(form):
    rendered_post = ''
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

        # Read style file for the post thread
        css = ''
        style_file_path = path.join(path.dirname(path.realpath(__file__)),
                        'static/{}/threadstyle.css'.
                        format(__name__.split('.')[0]))
        with open(style_file_path) as f:
            for line in f:
                line = line.strip()
                css += line

        #template = loader.get_template('postmaker/rendered-post.html')
        #rendered = template.render({'album': data})
        rendered_post = loader.render_to_string('postmaker/rendered-post.html', {'album': data, 'css': css})
    return { 'post': rendered_post, 'album': data }

def make(request):
    aplform = AplForm()
    form = PostForm()
    css = ''

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

            # Read style file for the post thread
            style_file_path = path.join(path.dirname(path.realpath(__file__)),
                            'static/{}/threadstyle.css'.
                            format(__name__.split('.')[0]))
            with open(style_file_path) as f:
                for line in f:
                    line = line.strip()
                    css += line

            #template = loader.get_template('postmaker/rendered-post.html')
            #rendered = template.render({'album': data})
            rendered_post = loader.render_to_string('postmaker/rendered-post.html', {'album': data, 'css': css})

            accounts = request.session.get('np_accounts')
            print(request.session.items())
            return render(request,
                          'postmaker/result.html',
                          context={'code': rendered_post,
                                   'album': data,
                                   'accounts': accounts})
        else:
            # send back the form with error message
            return render(request, 'postmaker/make-post.html', {'form': form, 'aplfrm': aplform})

    # normal get request - render an empty form
    return render(request, 'postmaker/make-post.html', {'form': form, 'aplfrm': aplform})

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

@csrf_exempt
def new_release_ping(request):
    # JSON api for getting ping of new release
    if request.method == 'POST':
        data = json.loads(request.body)
        # Check validity
        if data.get('release_name') and \
                data.get('archive_name'):
            tonos = Tonos(data['release_name'])
            album = tonos.get_data()
            a_id = album.get('a_id')
            r = Release(release_name=data['release_name'],
                        archive_name=data['archive_name'],
                        archive_size=data.get('archive_size', 0),
                        stream_song_name=data.get('strm_name', ''),
                        stream_song_url=data.get('strm_url', ''),
                        share_link=data.get('link', ''),
                        share_link_passcode=data.get('link_pwd', ''),
                        adam_id=(a_id if a_id else ''))

            autopost = auto_post(r, tonos)
            if autopost.get('error'):
                logger.warning('Failed to auto post {}:\n {}'.
                               format(r.release_name, autopost['error']))

            # Save to database
            try:
                r.full_clean()
                r.save()
            except (ValidationError, IntegrityError) as error:
                logger.info('Invalid record: {}'.format(error))
            except:
                logger.info('Write to database failed')

        return JsonResponse({'error': 0})

    return JsonResponse({'error': 1, 'message': 'Unsupported method'}, status=400)

def auto_post(release, tonos):
    # Check duplicate
    dupe = chk_rls_dup(release)
    if dupe:
        return {'error': 'Duplicate found', 'dupe': dupe}
    if not chk_validity(tonos):
        return {'error': 'Search Result Validation Failed'}

    # All Clear!
    print('Release {} clear for autopost!'.format({release.release_name}))
    # Compose the post
    # Read style file for the post thread
    style_file_path = path.join(path.dirname(path.realpath(__file__)),
                    'static/{}/threadstyle.css'.
                    format(__name__.split('.')[0]))
    css = ''
    with open(style_file_path) as f:
        for line in f:
            line = line.strip()
            css += line

    # Configure the context to pass to template
    data = tonos.get_data()
    data['album_info']['archive_name'] = release.archive_name
    data['album_info']['archive_size'] = release.archive_size
    data['album_info']['download_link'] = release.share_link
    data['album_info']['download_passcode'] = release.share_link_passcode
    data['album_info']['stream_url'] = release.stream_song_url
    data['album_info']['hidden_info'] = '密码：needpop.com'

    # for template to get resource (WEB)
    data['album_info']['parsed_rls'] = data['parsed_rls']
    # Trim date time to date
    release_date = datetime.fromisoformat(data['album_info']['releaseDate'].
                                          replace('Z', '+00:00'))
    data['album_info']['year'] = str(release_date.date())
    # Fix art work resolution
    data['album_info']['artwork'] = data['album_info']['artwork']. \
        replace('100x100bb.jpg', '600x600bb.jpg')

    # render the post
    rendered_post = loader.render_to_string('postmaker/rendered-post.html',
                                            {'album': data['album_info'],
                                             'css': css})

    # construct thread
    thread_subject = '{} - {} ({})'.format(data['album_info']['artist'],
                                           data['album_info']['title'],
                                           release_date.year)
    genre = {
        'Alternative Indie': 86,
        'R&B': 90,
        'Hip-Hop Rap': 91,
        'Pop': 83,
        'Rock Metal Punk': 84,
        'Dance House': 87,
        'Electronic': 88
    }
    typeid = 89
    for key in genre:
        option = key.split()
        for i in option:
            if i in data['album_info']['genre']:
                typeid = genre[key]
                break

    forum_id = 45
    if data['parsed_rls'].get('lang') == 'KR' or \
            data['parsed_rls'].get('lang') == 'JP':
        typeid = 66
        forum_id = 59

    np = Np(cdb_auth=environ.get('AUTOPOSTER'))
    post = np.post_thread(thread_subject.encode('gbk', 'ignore'),
                rendered_post.encode('gbk', 'ignore'),
                forum_id=forum_id,
                typeid=typeid)

    if post:
        release.post_url = post.get('url', '')
    release.posted = True
    return {'error': None}

def compose_post(release):
    pass

def chk_validity(tonos):
    return tonos.check_validity()

def chk_rls_dup(release):
    dup = Release.objects.filter(adam_id=release.adam_id)
    for d in dup:
        if d.posted:
            return d
    return False

