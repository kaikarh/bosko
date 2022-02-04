#! python3
# np.py - handles connection to needpop 
# need an account

from os import environ
import bs4, requests, logging, html

from urllib import parse

logger = logging.getLogger(__name__)

class Np:

    POST_TITLE_MAX = 80
    AUTOPOSTER = environ.get('AUTOPOSTER')

    def __init__(self, cdb_auth=None):
        # setup the session connection
        self.host_url = 'http://needpop.com'
        self.login_url = parse.urljoin(self.host_url, '/logging.php?action=login')
        self.newthread_url_base = parse.urljoin(self.host_url,
                                '/post.php?action=newthread&fid={}')
        self.reply_url_base = parse.urljoin(self.host_url,
                                '/post.php?action=reply&tid={}')
        self.edit_url_base = parse.urljoin(self.host_url,
                                '/post.php?action=edit&tid={}&pid={}')
        self.s = requests.Session()
        self.s.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.0) Gecko/20100101 Firefox/14.0.1'}

        if cdb_auth:
            self.set_user(cdb_auth=cdb_auth)

    def __del__(self):
        self.s.close()

    def __get_page(self, url):
        # try to make the request
        try:
            res = self.s.get(url)
            res.encoding = 'GBK'
        except:
            # something went wrong returning an empty string
            res = ''
        return res

    def __get_page_and_parse(self, url):
        html = self.__get_page(url)
        if html:
            return bs4.BeautifulSoup(html.text, 'html.parser')
        return ''

    def __post_page(self, url, *args, **kwargs):
        res = self.s.post(url, *args, **kwargs)
        res.encoding = 'GBK'
        return res

    def __post_page_and_parse(self, url, *args, **kwargs):
        html = self.__post_page(url, *args, **kwargs)
        if html:
            return bs4.BeautifulSoup(html.text, 'html.parser')
        return ''

    def __get_all_fields_in_form(self, form):
        result = {}
        fields = form.find_all('input')
        for field in fields:
            # get all fields that are to be posted in request
            if field.attrs.get('name'):
                # ignore unchecked
                if field.attrs.get('type') == 'radio' or \
                    field.attrs.get('type') == 'checkbox':
                    if not field.has_attr('checked'):
                        continue
                # ignore buttons
                if field.attrs.get('type') == 'button':
                    continue
                result[field.attrs['name']] = field.attrs['value']
                logger.debug('{:<12} {:<20}'.format(field.attrs['name'], field.attrs['value']))
        
        typeid_select = form.find('select', {'name': 'typeid'})
        if typeid_select:
            selected = form.find('option', selected=True)
            result['typeid'] = selected.attrs['value'] if selected else 0
        return result

    def _trim_subject(self, s):
        # subject line has a character word count limit
        # html characters are counted as escaped html entity i.e. & -> &amps;
        s_len = len(html.escape(s))
        diff = s_len - len(s)
        return s if s_len < self.POST_TITLE_MAX else s[:self.POST_TITLE_MAX - diff - 3] + '.' * 3

    def __trim_str_to_len(self, s, max_len, oversized=False):
        if len(html.escape(s)
        .encode('gbk', 'xmlcharrefreplace')) <= max_len:
            return s[:-2] + '…' if oversized else s
        return self.__trim_str_to_len(s[:-1], max_len, True)

    def login(self, account):
        # Login to forum
        # Takes in an account dict containing username and password
        # return a cookiejar

        if account['username'] and account['password']:
            # request login form
            soup = self.__get_page_and_parse(self.login_url)

            # Get form
            try:
                login_form = soup.form
                fields = login_form.find_all('input')
            except AttributeError:
                return False

            payload = dict.fromkeys(list(set([ f.attrs['name'] for f in fields ])))

            # construct login form
            payload['form_hash'] = login_form.find('input', {'name':'formhash'}).attrs['value']
            payload['referer'] = login_form.find('input', {'name': 'referer'}).attrs['value']
            payload['loginfield'] = 'username'
            payload['username'] = account['username']
            payload['password'] = account['password']
            payload['questionid'] = 0
            payload['cookietime'] = 315360000
            payload['loginsubmit'] = login_form.find('input', {'name': 'loginsubmit'}).attrs['value']

            # login
            res = self.__post_page(parse.urljoin(self.login_url, login_form.attrs['action']), data=payload)
            #res = self.s.post(parse.urljoin(self.login_url, login_form.attrs['action']), data=payload)

            if res.cookies.get('cdb_auth'):
                return res.cookies
            else:
                raise Exception('Login Failed')
        else:
            raise Exception('Login Failed')

    def set_user(self, cookies=None, cdb_auth=None):
        # set user credential to cookie
        if cookies:
            self.s.cookies = cookies
        else:
            if cdb_auth:
                jar = requests.cookies.RequestsCookieJar()
                jar.set('cdb_auth', cdb_auth, domain='needpop.com')

                self.s.cookies = jar

    def get_current_user(self):
        # get the name of the authenticated user

        soup = self.__get_page_and_parse(self.host_url)

        # try to find the user id on page
        try:
            username = soup.find('span', {'class': 'bold'}).a.get_text(strip=True)
        except AttributeError:
            # Auth failed
            return False

        return username

    def logout(self):
        soup = self.__get_page_and_parse(self.host_url)

        try:
            logout_button = soup.find('a', text='退出')
        except AttributeError:
            # Auth failed
            return False

        # logout
        return (self.__get_page(parse.urljoin(self.host_url, logout_button.attrs['href']))).cookies

    def __post(self, action, subject, message, thread_id=None, post_id=None, forum_id=None, **kwargs):
        if action == 'edit':
            compose_url = self.edit_url_base.format(thread_id, post_id)
        elif action == 'reply':
            compose_url = self.reply_url_base.format(thread_id)
        elif action == 'create':
            compose_url = self.newthread_url_base.format(forum_id)
        else:
            raise Exception('Post Action Unknown: %s', action)

        soup = self.__get_page_and_parse(compose_url)
        form = soup.find('form')
        fields = self.__get_all_fields_in_form(form)
        fields.update(kwargs)
        fields.update({
            'subject': self.__trim_str_to_len(
                subject, self.POST_TITLE_MAX).encode('gbk', 'xmlcharrefreplace'),
            'message': message.encode('ascii', 'xmlcharrefreplace'),
        })
        submit_url = parse.urljoin(self.host_url, form.attrs['action'])
        return self.__post_page(submit_url, data=fields)

    def edit_thread(self, thread_id, post_id, subject, message):
        res = self.__post('edit', subject, message, thread_id=thread_id, post_id=post_id)

        return {'url': res.url}


    def new_thread(self, subject, message, forum_id=45, typeid=None, price=0, readperm=0):
        post_pref = {
            'parseurloff': 1,
            'htmlon': 1,
            'usesig': 1,
            'price': price,
            'readperm': readperm,
            'typeid': typeid,
        }

        res = self.__post('create', subject, message, forum_id=forum_id, **post_pref)

        view_page = bs4.BeautifulSoup(res.text, 'html.parser')

        wrapper = view_page.find('tr', {'class': 'header'}).td
        # get title
        if len(wrapper.contents) <= 1:
            # server returned a login form
            raise Exception('Post Failed: User not logged in or wrong credential')
        elif len(wrapper.contents) > 3:
            # forums that have typeid
            title = wrapper.contents[-2].get_text() + wrapper.contents[-1]
        else:
            # forums that dont have typeid
            title = wrapper.contents[-1].strip().split('\n')[-1]

        return {'url': res.url, 'title': title}
