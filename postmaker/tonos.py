#! python3

# Tonos
# - itunes api wrapper

import sys, re, requests, json, logging, unicodedata
from pprint import pformat

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Tonos:
    def __init__(self, rls_name=None):
        self.data = {}
        if rls_name:
            self.data['release_name'] = rls_name
            self.data['parsed_rls'] = self.parse_rls_name(rls_name)
            self.data['a_id'] = self.get_adam_id(rls_name)
            if self.data['a_id']:
                id_result = self._query_apple(a_id=self.data['a_id'])
                self.data['album_info'] = self._extract_id_query_result(id_result)

    def get_data(self):
        return self.data

    def parse_rls_name(self, rls_name):
        # group1 -> Artist Name
        # group2 -> Album Title
        # group3 -> Lang for FLAC
        # group4 -> WEB
        # group5 -> FLAC

        match = re.search('([\w\.\-]*?)\-{1,2}([\w\(\)]*?)(?:\-\(.*\))?(?:\-([A-Z]{2}))?(?:\-(?:(WEB)|(?:\d?CD)|(?:CDEP)))?(?:\-\d{2}BIT)?(?:\-(?:WEB)?(FLAC))?(?:\-([A-Z]{2}))?\-(?:\d{4})\-(?:[\w\_]+)', rls_name)

        if match:
            logger.debug('Regex match result {}'.format(match.groups()))
            return {
                'flac': True if match.group(5) else False,
                'web': True if match.group(4) else False,
                'artist': match.group(1).replace('_', ' '),
                'title': match.group(2).replace('_', ' '),
                'lang': match.group(6)
            }
        logger.info('Cannot parse release name (Regex did not match anything)')
        return False

    def _query_apple(self, query=None, a_id=None, country='US'):
        if query:
            payload = {'term': query, 'media': 'music', 'entity': 'album', 'limit': 1, 'country': country}
            r = requests.get('https://itunes.apple.com/search', params=payload).json()
            logger.debug(json.dumps(r, indent=2))
            return r

        if a_id:
            payload = {'id': a_id, 'entity': 'song'}
            r = requests.get('https://itunes.apple.com/lookup', params=payload).json()
            logger.debug(json.dumps(r, indent=2))
            return r

        return False

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

            data['type'] = album['collectionType']
            data['artist'] = album['artistName']
            data['title'] = album['collectionName']
            data['artwork'] = album['artworkUrl100']
            data['genre'] = album['primaryGenreName']
            data['copyright'] = album['copyright']
            data['releaseDate'] = album['releaseDate']
            data['amUrl'] = album['collectionViewUrl']
            data['tracks'] = []

            for record in query_result['results'][1:]:
                # Filter only songs
                if record['kind'] == 'song':
                    song = {}
                    song['artist'] = record['artistName']
                    song['name'] = record['trackName']
                    song['previewUrl'] = record['previewUrl']
                    song['trackNumber'] = record['trackNumber']
                    song['duration'] = record['trackTimeMillis']

                    data['tracks'].append(song)

            return data
        return False

    def check_validity(self):
        parsed_rls = self.data.get('parsed_rls')
        album_info = self.data.get('album_info')
        if parsed_rls and album_info:
            if self._strip_stylization(parsed_rls['artist']) in \
                    self._strip_stylization(self._normalize_accented(album_info['artist'])):
                # Probably got a accurate result
                # Continue to query album info
                logger.debug('Matched Artist Name, continuing')
                if self._strip_stylization(parsed_rls['title']) in \
                        self._strip_stylization(
                            self._normalize_accented(album_info['title'])):
                    logger.debug('Matched album Name, continuing')
                    return True
        return False

    def get_adam_id(self, rls_name):
        parsed_rls = self.parse_rls_name(rls_name)
        if parsed_rls:
            # if parsed a valid release name
            query_term = '{} {}'.format(parsed_rls['artist'], parsed_rls['title'])
        else:
            # cant even parse the release name
            return False

        result = self._query_apple(query=query_term, country=parsed_rls['lang'])
        if result.get('resultCount'):
            # There's a search result
            logger.info('iTunes API Search result: [{}] {} - {}'.
                        format(result['results'][0]['collectionId'],
                               result['results'][0]['artistName'],
                               result['results'][0]['collectionName']))

            # Basic match accuracy test
            #if self._strip_stylization(parsed_rls['artist']) in \
            #        self._strip_stylization(self._normalize_accented(result['results'][0]['artistName'])):
            #    # Probably got a accurate result
            #    # Continue to query album info
            #    logger.debug('Found album, continuing')

            return result['results'][0]['collectionId']
        return None

    def lookup_album_id(self, a_id):
        id_result = self._query_apple(a_id=a_id)
        return self._extract_id_query_result(id_result)

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

