#! python3
# amParser.py - Parse album info from apple music

import requests, bs4

class Am:
    def __init__(self, url):
        res = requests.get(url, headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 6.0) Gecko/20100101 Firefox/14.0.1',
        })

        self.soup = bs4.BeautifulSoup(res.text, 'html.parser')

    def get_album_info(self):
        info = {}

        container = self.soup.select('.album-header-metadata')[0]
        info['title'] = container.h1
        info['artist'] = container.h2.a
        info['meta'] = container.h3

        for k, v in info.items():
            info[k] = v.get_text(strip=True)

        info['meta'] = info['meta'].split("\u2004·\u2004")
        info['tracklist'] = []
        song_list = self.soup.select('.songs-list .row.track .col.col-song .song-name')

        for i in song_list:
            info['tracklist'].append(i.get_text(strip=True))

        info['art'] = self.soup.select('.media-artwork-v2 picture source[type="image/jpeg"]')[0].attrs['srcset'].split(",")[0].split()[0]

        return info

    def get_dummy_info(self):
        return {'title': 'After Hours', 'artist': 'The Weeknd', 'meta': ['R&B/Soul', '2020'], 'tracklist': ['Alone Again', 'Too Late', 'Hardest To Love', 'Scared To Live', 'Snowchild', 'Escape From LA', 'Heartless', 'Faith', 'Blinding Lights', 'In Your Eyes', 'Save Your Tears', 'Repeat After Me (Interlude)', 'After Hours', 'Until I Bleed Out'], 'art': 'https://is2-ssl.mzstatic.com/image/thumb/Music124/v4/06/e5/8c/06e58ce4-a813-8d5b-ef64-03a69064773c/20UMGIM12176.rgb.jpg/500x500bb-60.jpg'}



#a = Am("https://music.apple.com/us/album/after-hours/1499378108")
#print(a.get_album_info())

