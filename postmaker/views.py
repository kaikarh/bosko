import json, re, logging, threading

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
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Release
from .forms import AplForm, PostForm, ReleaseForm
from utils.amParser import Am
from utils.np import Np
from utils.baal import Baal
from utils.tonos import Tonos
from minos.views import add_to_db, update_flac_post

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
    #model = Release
    context_object_name = 'release_list'
    template_name = 'postmaker/releases.html'
    queryset = Release.objects.order_by('-time')

class ReleaseDetailView(LoginRequiredMixin, DetailView):
    model = Release
    template_name = 'postmaker/release-detail.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        form = ReleaseForm(instance=context['release'])
        context['form'] = form
        return context

class ReleaseDetailMakeView(LoginRequiredMixin, DetailView):
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

def process_new_release(data):
    # Check validity
    if data.get('release_name') and \
            data.get('archive_name'):
        r = Release(release_name=data['release_name'],
                    archive_name=data['archive_name'],
                    archive_size=data.get('archive_size', 0),
                    stream_song_name=data.get('strm_name', ''),
                    stream_song_url=data.get('strm_url', ''),
                    share_link=data.get('link', ''),
                    share_link_passcode=data.get('link_pwd', ''))

        # Save to database
        try:
            r.full_clean()
            r.save()
        except (ValidationError, IntegrityError) as error:
            logger.info('Invalid record: {}'.format(error))
        except:
            logger.info('Write to database failed')

        try:
            auto_post(r)
        except Exception as err:
            logger.warning('Auto post error: {}'.format(err))

@csrf_exempt
def new_release_ping(request):
    # JSON api for getting ping of new release
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            t = threading.Thread(target=process_new_release,
                                 args=[data])
            t.setDaemon(True)
            t.start()
        except Exception as err:
            logger.warning('Spawning release process failed: {}'.format(err))
            return JsonResponse({'error': 1, 'message': 'Spawning process: {}'.format(err)},
                                status=400)
        return JsonResponse({'error': 0})

    return JsonResponse({'error': 1, 'message': 'Unsupported method'}, status=400)

def auto_post(release, a_id=None, forced=False):
    tonos = Tonos(release.release_name, a_id)
    release.adam_id = tonos.data.get('a_id', '')

    try:
        if tonos.data['parsed_rls'].get('flac'):
            try:
                add_to_db(tonos, link=release.share_link, link_pwd=release.share_link_passcode)
                update_flac_post(np=Np(cdb_auth=environ.get('AUTOPOSTER')), thread_url=environ.get('FLACTHREADURL'))
            except Exception as err:
                logger.warning('Failed to post FLAC {}:\n - {}'.format(release.release_name, err))
            finally:
                return None
    except AttributeError:
        logger.warning('Failed to parse release name')

    # Check if got a hit on album api
    if not release.adam_id:
        raise Exception('Not found on Apple music')
    # Check duplicate
    dupe = chk_rls_dup(release)
    if not forced:
        if dupe:
            logger.warning(f'Dupe: {dupe}')
            raise Exception('Duplication')
        if not chk_validity(tonos):
            raise Exception('Search Result Validation Failed')

    # All Clear!
    print('Release {} clear for autopost!'.format({release.release_name}))

    post_meta = compose_post(release, tonos)
    # subject word limit
    if len(post_meta['thread_subject']) > Np.POST_TITLE_MAX:
        post_meta['thread_subject'] = post_meta['thread_subject'][:Np.POST_TITLE_MAX-3] + '.' * 3

    np = Np(cdb_auth=environ.get('AUTOPOSTER'))
    post_url = post_to_forum(post_meta['thread_subject'], post_meta['rendered_post'],
                post_meta['forum_id'], post_meta['typeid'], np)

    if post_url:
        release.post_url = post_url
        release.posted = True
        release.full_clean()
        release.save()

def post_to_forum(subject, body, forum_id, typeid, np):
    # Try to post thread
    # retry if failed
    for attempt in range(3):
        try:
            post = np.post_thread(subject.encode('gbk', 'ignore'),
                        body.encode('gbk', 'ignore'),
                        forum_id=forum_id,
                        typeid=typeid)
            return post.get('url', '')
        except Exception as err:
            logger.info(err)
            logger.warning('Post Failed attempt {}/3'.format(attempt+1))
    else:
        logger.warning('All post attempt failed')
        raise Exception('All post attempt failed')

def compose_post(release, tonos):
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
        'Alternative Indie Songwriter Psychedelic': 86,
        'R&B Soul': 90,
        'Hip-Hop Rap': 91,
        'Pop': 83,
        'Rock Metal Punk Ska': 84,
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

    if data['parsed_rls'].get('lang') == 'CN':
        forum_id = 56

    if 'Soundtrack' in data['album_info']['genre'] or \
            'Original Score' in data['album_info']['genre']:
        forum_id = 86

    if 'Classical' in data['album_info']['genre']:
        forum_id = 34

    return {
        'rendered_post': rendered_post,
        'thread_subject': thread_subject,
        'typeid': typeid,
        'forum_id': forum_id
    }

def chk_validity(tonos):
    return tonos.check_validity()

def chk_rls_dup(release):
    dup = Release.objects.filter(adam_id=release.adam_id)
    for d in dup:
        if d.posted:
            return d
    return False

