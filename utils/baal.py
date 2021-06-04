#! python3

# A Manage Interface for Baidu Pan

import requests, re, logging, random, string
from urllib.parse import urljoin
from os import path as Path

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Baal:
    def __init__(self, credential=None):
        # set up baidu login cookies
        self.base_url = 'https://pan.baidu.com/'
        self.list_url = '/api/list'
        self.share_url = '/share/set'
        self.default_dir = '/apps/bypy'
        self.s = requests.Session()
        self.s.cookies.set('BDUSS', credential.get('bduss'), domain='.baidu.com')
        self.s.cookies.set('STOKEN', credential.get('stoken'), domain='.pan.baidu.com')
        self.s.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'}

        self.bdstoken = ''

    def get_user(self):
        if not self.s.cookies['BDUSS'] or not self.s.cookies['STOKEN']:
            logger.info('No login credential')
            return False
        else:
            r = self.s.get(self.base_url)
            search = re.search('\"username\"\:\"(.*?)\"\,', r.text)
            if search:
                username = search.group(1)
                logger.info('Current user is: {}'.format(username))
                return username
            else:
                logger.info('Invalid credential')
                return False

    def _get_bdstoken(self):
        r = self.s.get(self.base_url)
        search = re.search('\"bdstoken\"\:\"(.*?)\"\,', r.text)
        if search:
            logger.info('Got the token')
            self.bdstoken = search.group(1)
            return search.group(1)
        else:
            logger.info('Get bdstoken failed. Not logged in?')
            return False

    def get_list_of_files(self, path='/'):
        # get bdstoken
        if self.bdstoken:
            bdstoken = self.bdstoken
        else:
            bdstoken = self._get_bdstoken()

        page = 1
        max_items = 100

        # construct GET params
        payload = {
            'order': 'time',
            'desc': 1,
            'showempty': 0,
            'web': 1,
            'page': page,
            'num': max_items,
            'dir': path,
            't': random.random(),
            'channel': 'chunlei',
            #'app_id': 250528,
            'bdstoken': bdstoken,
            #'logid': 'QzlEOURFMDgyQjkyQTkwRUZBMkQ5MzhBQjIxNzY2NEY6Rkc9MQ==',
            'clienttype': 0
        }
        url = urljoin(self.base_url, self.list_url)
        #headers = self.s.headers
        #headers['referer'] = 'https://pan.baidu.com/disk/home?'
        #r = self.s.get(url, params=payload, headers=headers)
        r = self.s.get(url, params=payload)

        return r.json()

    def get_fs_id(self, path):
        directory = Path.dirname(path) if Path.dirname(path) else self.default_dir
        filename = Path.basename(path)

        # list files in path
        ls = self.get_list_of_files(directory)['list']
        for item in ls:
            if item['server_filename'] == filename:
                # found the file
                logger.info('File {} Found, returning fs_id'.format(filename))
                return item['fs_id']

        logger.info('File not found. Getting fs_id failed')
        return False

    def _generate_share_pwd(self, length=4):
        pool = string.ascii_lowercase + string.digits
        pwd = ''
        for i in range(length):
            pwd += random.choice(pool)

        return pwd

    def generate_link(self, path):
        # get bdstoken
        if self.bdstoken:
            bdstoken = self.bdstoken
        else:
            bdstoken = self._get_bdstoken()

        fs_id = self.get_fs_id(path)
        pwd = self._generate_share_pwd()
        logger.info('Generated passcode for file {}: {}'.format(path, pwd))

        params = {
            'channel': 'chunlei',
            'clienttype': 0,
            'web': 1,
            #'app_id': 250528,
            'bdstoken': bdstoken,
            #'logid': 'QzlEOURFMDgyQjkyQTkwRUZBMkQ5MzhBQjIxNzY2NEY6Rkc9MQ==',
            'clienttype': 0
        }
        form = {
            'channel_list': '[]',
            'period': 0,
            'pwd': pwd,
            'schannel': 4,
            'fid_list': '[{}]'.format(fs_id)
        }

        url = urljoin(self.base_url, self.share_url)
        r = self.s.post(url, params=params, data=form)

        resp_json = r.json()

        if resp_json['errno'] == 0:
            return {
                'link': resp_json['link'],
                'pwd': pwd
            }
        else:
            return False



