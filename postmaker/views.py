import json, re, logging

from os import path

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse

from .amParser import Am
from .forms import AplForm, PostForm
from .np import Np

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

