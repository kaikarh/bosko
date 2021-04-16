from os import path, environ
import json, logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from utils.np import Np
from utils.tonos import Tonos

from .models import *
from .serializers import AlbumSerializer

logger = logging.getLogger(__name__)

def serialize_all_data():
    data = []
    records = Album.objects.filter().order_by('-date')
    for r in records:
        data.append(AlbumSerializer(r).data)

    return data

def generate_album_from_pre(tonos):
    album = Album(artist=tonos.data['parsed_rls']['artist'],
                title=tonos.data['parsed_rls']['title'],
                date='{}-01-01'.format(tonos.data['parsed_rls']['year']))
    return album

def generate_album_from_a_id(tonos):
    album = Album(artist=tonos.data['album_info']['artist'],
            title=tonos.data['album_info']['title'],
            genre=tonos.data['album_info']['genre'],
            adam_id=tonos.data['a_id'],
            cover_art=tonos.data['album_info']['artwork'].replace('100x100bb.jpg', '600x600bb.jpg'),
            date=tonos.data['album_info']['releaseDate'].split('T')[0])
    return album

@csrf_exempt
def api_accept_release(request):
    if request.method == 'POST':
        try:
            content = json.loads(request.body)
            release_name = content['name']
            link = content['link']
            link_pwd = content['link_pwd']
        except KeyError:
            return JsonResponse({'error': '1', 'message': 'Wrong data'}, status=400)
        except json.decoder.JSONDecodeError:
            return JsonResponse({'error': '1', 'message': 'Wrong format'}, status=400)

        # try to scrape for album info
        t = Tonos(release_name)
        album = ''
        if t.data.get('a_id'):
            # if there is a hit
            # check if theres already a record in the database
            try:
                album = Album.objects.get(adam_id=t.data['a_id'])
            except Album.DoesNotExist:
                # album not in database
                # loosly check validity
                if t.check_validity(threshold=0.65):
                    # kind of similar
                    # use the scraped info to fill database
                    try:
                        album = generate_album_from_a_id(t)
                        album.full_clean()
                        album.save()
                    except:
                        return JsonResponse({'error': '1', 'message': 'Error saving to database'}, status=400)
                else:
                    # A completely different album
                    # generate album record from pre name
                    try:
                        album = generate_album_from_pre(t)
                        album.full_clean()
                        album.save()
                    except Exception:
                        return JsonResponse({'error': '1', 'message': 'Error saving to database'}, status=400)
        else:
            try:
                album = generate_album_from_pre(t)
                album.full_clean()
                album.save()
            except Exception:
                return JsonResponse({'error': '1', 'message': 'Error saving to database'}, status=400)

        # Check for duplicate release
        try:
            release = Release.objects.get(release_name=release_name)
        except Release.DoesNotExist:
            # no record in the database
            # create a new release
            release = Release(release_name=release_name, album=album)
            try:
                release.full_clean()
                release.save()
            except Exception:
                return JsonResponse({'error': '1', 'message': 'Error saving to database'}, status=400)

        # Finally add link
        l = Link(url=link, passcode=link_pwd, release=release)
        try:
            l.full_clean()
            l.save()
        except Exception:
            return JsonResponse({'error': '1', 'message': 'Possibly duplicate link, or wrong url format'}, status=400)
        finally:
            if not release.link_set.all():
                release.delete()
            if not album.release_set.all():
                album.delete()

        #return JsonResponse({'error': 0, 'message': 'ok', 'info': t.data['parsed_rls']})

        # Try to make changes to designated thread
        np = Np(cdb_auth=environ.get('AUTOPOSTER'))
        thread_url = environ.get('FLACTHREADURL')
        subject = 'FLAC 無損音樂索引 - (Updated {})'.format(timezone.now().date())
        css = ''
        style_file_path = path.join(path.dirname(path.realpath(__file__)),
                        'static/{}/minos-thread-style.css'.
                        format(__name__.split('.')[0]))
        with open(style_file_path) as f:
            for line in f:
                line = line.strip()
                css += line
        message = render_to_string('minos/rendered_thread.html',
                                {'data': json.dumps(serialize_all_data()), 'css': css})

        try:
            post = np.edit_thread(thread_url,
                        subject.encode('gbk', 'ignore'),
                        message.encode('gbk', 'ignore'))
        except Exception as err:
            logger.warning(err)
            return JsonResponse({'error': '1', 'message': 'Error Posting'}, status=400)

        return JsonResponse({'error': 0, 'message': 'ok', 'url': post})

    return HttpResponse('Bad Request', status=400)

def render_thread(request):
    # Read style file for the post thread
    css = ''
    style_file_path = path.join(path.dirname(path.realpath(__file__)),
                    'static/{}/minos-thread-style.css'.
                    format(__name__.split('.')[0]))
    with open(style_file_path) as f:
        for line in f:
            line = line.strip()
            css += line

    data = serialize_all_data()
    return render(request, 'minos/rendered_thread.html', {'data': json.dumps(data), 'css': css})
