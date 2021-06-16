#! python3

# Tonos
# - itunes api wrapper

import sys, re, requests, json, logging, unicodedata
from difflib import SequenceMatcher
from pprint import pformat
from .releaseparser import ReleaseParser

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Tonos:
    def __init__(self, rls_name=None, a_id=None):
        self.data = {}
        if rls_name:
            self.data['release_name'] = rls_name
            self.data['parsed_rls'] = self.parse_rls_name(rls_name)
            self.data['a_id'] = a_id if a_id else self.get_adam_id(rls_name)
            if self.data['a_id']:
                self.data['album_info'] = self.lookup_album_id()

    def get_data(self):
        return self.data

    def get_album_data(self):
        return self.data['album_info'].copy()
    
    def get_parsed_data(self):
        return self.data['parsed_rls']

    def parse_rls_name(self, rls_name):
        try:
            return ReleaseParser.parse_name(rls_name)
        except:
            return None

    def _query_apple(self, query=None, a_id=None, country='US'):
        for attempt in range(3):
            try:
                if query:
                    payload = {'term': query, 'media': 'music', 'entity': 'album', 'limit': 1, 'country': country}
                    r = requests.get('https://itunes.apple.com/search', params=payload).json()
                    logger.debug(json.dumps(r, indent=2))
                    return r

                if a_id:
                    payload = {'id': a_id, 'entity': 'song', 'country': country}
                    r = requests.get('https://itunes.apple.com/lookup', params=payload).json()
                    logger.debug(json.dumps(r, indent=2))
                    return r
            except Exception as err:
                logger.info(err)
                logger.warning('Query apple failed attempt {}/3'.format(attempt+1))
            else:
                break
        return {}

    def _normalize_accented(self, s):
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode()

    def _strip_stylization(self, styzd_str):
        return re.sub('[\W_]+', '', styzd_str.lower())

    def _extract_id_query_result(self, query_result):
        data = {}

        if query_result.get('resultCount'):
            # Loop through all results
            # First record is always the album info
            album = query_result['results'][0]

            data['collection_type'] = album['collectionType']
            data['artist_name'] = album['artistName']
            data['collection_name'] = album['collectionName']
            data['artwork_url'] = album['artworkUrl100']
            data['genre_name'] = album['primaryGenreName']
            data['copyright'] = album['copyright']
            data['release_date'] = album['releaseDate']
            data['apple_music_url'] = album['collectionViewUrl']
            data['tracks'] = []

            for record in query_result['results'][1:]:
                # Filter only songs
                if record['kind'] == 'song':
                    song = {}
                    song['artist'] = record['artistName']
                    song['name'] = record['trackName']
                    song['trackNumber'] = record['trackNumber']
                    song['duration'] = record['trackTimeMillis']
                    # iTunes api may or may not provide streamable preview
                    try:
                        song['previewUrl'] = record['previewUrl']
                    except KeyError:
                        # No preview url available
                        pass

                    data['tracks'].append(song)

        return data

    def check_validity(self, threshold=0.85):
        parsed_rls = self.data.get('parsed_rls')
        album_info = self.data.get('album_info')

        try:
            release = '{} {}'.format(parsed_rls.artist, parsed_rls.title).upper()
            fetched = '{} {}'.format(album_info['artist_name'], album_info['collection_name']).upper()
        except:
            return False

        logger.debug('Checking: {} vs {}'.format(release, fetched))
        m = SequenceMatcher(None, release, fetched)
        if m.ratio() >= threshold:
            return True

        #if parsed_rls and album_info:
        #    if self._strip_stylization(parsed_rls['artist']) in \
        #            self._strip_stylization(self._normalize_accented(album_info['artist'])):
        #        # Probably got a accurate result
        #        # Continue to query album info
        #        logger.debug('Matched Artist Name, continuing')
        #        if self._strip_stylization(parsed_rls['title']) in \
        #                self._strip_stylization(
        #                    self._normalize_accented(album_info['title'])):
        #            logger.debug('Matched album Name, continuing')
        #            return True
        return False

    def get_adam_id(self, rls_name):
        parsed_rls = self.parse_rls_name(rls_name)
        if parsed_rls:
            # if parsed a valid release name
            query_term = '{} {}'.format(parsed_rls.artist, parsed_rls.title)
        else:
            # cant even parse the release name
            return False

        result = self._query_apple(query=query_term, country=parsed_rls.lang)
        if result.get('resultCount'):
            # There's a search result
            logger.info('iTunes API Search result: [{}] {} - {}'.
                        format(result['results'][0]['collectionId'],
                               result['results'][0]['artistName'],
                               result['results'][0]['collectionName']))

            return result['results'][0]['collectionId']
        return None

    def lookup_album_id(self, a_id=None, country='US', fallback=True):
        a_id = a_id if a_id else self.data.get('a_id')
        id_result = self._query_apple(a_id=a_id, country=country)
        result_dict = self._extract_id_query_result(id_result)

        if fallback:
            if isinstance(fallback, tuple):
                # Max 3 fallback queries
                fallback = fallback[:3]
            else:
                # no fallback country specified. Use default
                fallback = ('GB', 'DE', 'HK', 'JP')

            for _ in fallback:
                fallback_result_dict = ''
                if not result_dict:
                    fallback_result_dict = self._extract_id_query_result(
                        self._query_apple(a_id=a_id, country=_))
                    if fallback_result_dict:
                        result_dict = fallback_result_dict
                    else:
                        continue

                # Query fallback country iTunes stores if tracklist result is empty
                if len(result_dict['tracks']) == 0:
                    if not fallback_result_dict:
                        fallback_result_dict = self._extract_id_query_result(
                            self._query_apple(a_id=a_id, country=_))
                    if len(fallback_result_dict['tracks']) > 0:
                        result_dict['tracks'] = fallback_result_dict['tracks'][:]
                        break

        return result_dict

    def go(self, rls_name):
        a_id = self.get_adam_id(rls_name)
        if a_id:
            id_result = self._query_apple(a_id=a_id)
            album_info = self._extract_id_query_result(id_result)
            logger.info('Retrived data: ===>\n{}'.format(pformat(album_info)))
        else:
            return False

if __name__ == '__main__':
    t = Tonos()
    t.go(sys.argv[1])

