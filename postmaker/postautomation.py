import logging, threading

#from concurrent.futures import ThreadPoolExecutor

from .models import Release, AlbumPost
from utils.tonos import Tonos
from utils.np import Np

logger = logging.getLogger(__name__)

def new_release_entry(release):
    # Entry point of a newly added release
    try:
        t = threading.Thread(
            target=process_new_release,
            args=[release]
        )
        t.start()
    except Exception as err:
        logger.warning('Spawning release process failed: {}'.format(err))

def process_new_release(release):
    try:
        autopost(release)
    except Exception as err:
        logger.warning(err)

def autopost(release, a_id=None, forced=False, cdb_auth=None):
    try:
        t = validity_check(release, a_id=a_id, forced=forced)
        albumpost = generate_albumpost(release, tonos=t)
        post_params = generate_forum_post_field_value(albumpost)
        posted = post_to_forum(**post_params, cdb_auth=cdb_auth)
    except Exception as err:
        release.autopost_alert = err
        raise Exception('Auto post error: {}'.format(err))
    finally:
        if 'posted' in locals():
            release.post_url = posted
            release.posted = True
            release.autopost_alert = ''
        release.full_clean()
        release.save()

def validity_check(release, a_id=None, forced=False):
    tonos = Tonos(release.release_name, a_id)
    # Check if got a hit on album api
    a_id = a_id if a_id else tonos.data.get('a_id', '')
    if not a_id:
        raise Exception('Not found on Apple Music')

    # Ignore flac
    if tonos.get_parsed_data().coding == 'flac':
        pass

    # basic check
    if not forced:
        if dupe := chk_rls_dup(a_id):
            raise Exception(f'Duplication: {dupe}')
        if not chk_validity(tonos):
            raise Exception('Search Result Validation Failed - search return: {}'.format(a_id))

    # All Clear!
    release.adam_id = a_id
    logger.info(
        'Release ->{}<- matched {}\nclear to {}autopost!'.format(
            release.release_name,
            a_id,
            'Forced ' if forced else ''
        )
    )
    return tonos

def generate_albumpost(release, a_id=None, tonos=None):
    # get data from tonos instance or fetch using a_id
    tonos = tonos if tonos else Tonos(release.release_name, a_id)
    # try:
    #     if tonos.get_parsed_data().encode == 'flac':
    #         try:
    #             pass
    #             # do something
    #             #add_to_db(tonos, link=release.share_link, link_pwd=release.share_link_passcode)
    #             #update_flac_post(np=Np(cdb_auth=environ.get('AUTOPOSTER')), thread_url=environ.get('FLACTHREADURL'))
    #         except Exception as err:
    #             logger.warning('Failed to post FLAC {}:\n - {}'.format(release.release_name, err))
    #         finally:
    #             return None
    # except AttributeError:
    #     raise Exception('Failed to parse release name')

    # generate albumpost
    album_data = tonos.get_album_data()

    # generate albumpost from release
    albumpost = AlbumPost(**release.generate_albumpost_values())
    # Update field value for fields in albumpost if field name in AlbumPost fields
    # Same evaluation as following
    # albumpost_fields = [ f.name for f in AlbumPost._meta.fields ]
    # for attr, value in album_data.items():
    #     if attr in albumpost_fields:
    #         setattr(albumpost, attr, value)
    [ setattr(albumpost, attr, value) for attr, value in album_data.items() if attr in [ f.name for f in AlbumPost._meta.fields ] ]
    albumpost.clean()

    return albumpost

def post_to_forum(subject, body, forum_id, typeid, cdb_auth=None):
    np = Np(cdb_auth if cdb_auth else Np.AUTOPOSTER)
    # Try to post thread
    # retry if failed
    for attempt in range(3):
        try:
            post = np.post_thread(subject, body, forum_id=forum_id, typeid=typeid)
            return post.get('url', '')
        except Exception as err:
            logger.warning('Post Failed attempt {}/3: \n - {}'.format(attempt+1, err))
    else:
        raise Exception('Failed to post to forum: all post attempt failed')

def generate_forum_post_field_value(albumpost):
    forum_id = get_forum_id(albumpost)
    typeid = get_typeid(albumpost, forum_id)

    # subject word limit
    subject = str(albumpost)
    body = albumpost.render_post()

    return {'subject': subject, 'body': body, 'forum_id': forum_id, 'typeid': typeid}


def get_forum_id(albumpost):
    # fid list
    # 45 => EN Album    59 => JP / KR   56 => CN    86 => OST
    # 12 => EN Sngls    18 => Jazz      34 => Cls   14 => MV

    lang = albumpost.collection_language
    genre = albumpost.genre_name
    num_of_tracks = len(albumpost.tracks)
    # set a default
    forum_id = 45

    if lang == 'KR' or lang == 'JP':
        forum_id = 59
    if lang == 'CN':
        forum_id = 56

    if 'Soundtrack' in genre or 'Original Score' in genre:
        forum_id = 86
    if 'Classical' in genre:
        forum_id = 34
    if 'K-Pop' in genre or 'J-Pop' in genre:
        forum_id = 59

    # if number of track is less than 3 it's a singles release
    if forum_id == 45:
        if 0 < num_of_tracks <= 3:
            forum_id = 12
    
    return forum_id

def get_typeid(albumpost, forum_id):
    # typeid list
    # For EN forum
    # 90 => R&B     91 => Hip-Hop   83 => Pop   84 => Rock
    # 86 => Alt     87 => Dance     88 => Elec  89 => Other
    # For JP/KR forum
    # 66 => Album   67 => Sngls     68 => Ep
    typeid = None
    album_genre = albumpost.genre_name
    num_of_tracks = len(albumpost.tracks)

    if forum_id == 45:
        genre_list = {
            'Alternative Indie Songwriter Psychedelic': 86,
            'R&B Soul': 90,
            'Hip-Hop Rap': 91,
            'Pop': 83,
            'Rock Metal Punk Ska': 84,
            'Dance House Trance': 87,
            'Electronic': 88
        }

        typeid = 89
        for genre_group in genre_list:
            for genre in genre_group.split():
                if genre in album_genre:
                    typeid = genre_list[genre_group]
                    break

    if forum_id == 59:
        typeid = 66
        if 0 < num_of_tracks <= 3:
            typeid = 67
        if 3 < num_of_tracks <= 6:
            typeid = 68
    
    return typeid

def chk_validity(tonos):
    return tonos.check_validity()

def chk_rls_dup(a_id):
    dup = Release.objects.filter(adam_id=a_id)
    for d in dup:
        if d.posted:
            return d
    return False
