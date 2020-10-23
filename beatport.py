import requests
import json
import re
import datetime

from bs4 import BeautifulSoup

class Beatport:

    def __init__(self):
        pass

    def search_tracks(self, query: str) -> list:
        url = 'https://www.beatport.com/search/tracks' 

        r = requests.get(url, params={'q': query})
        soup = BeautifulSoup(r.text, features='lxml')

        #Get search results from JSON from script tag
        script_data = str(soup.find('script', {'id': 'data-objects'}))
        data_str = script_data[script_data.find('window.Playables = ')+19:script_data.find('\n', script_data.find('window.Playables = '))][:-1]
        data = json.loads(data_str)

        return [Track(t) for t in data['tracks']]

    #Search and match track
    def match_track(self, title: str, artists: list):
        query = ', '.join(artists) + f' {title}'
        tracks = self.search_tracks(query)

        clean_title = self._clean_title(title)
        clean_artists = self._clean_artists(artists)

        for track in tracks:
            #Match title
            if clean_title == self._clean_title(track.title) or clean_title == self._clean_title(track.name):
                #Match single artists
                bp_artists = [self._clean_artist(a.name) for a in track.artists]
                for artist in artists:
                    if self._clean_artist(artist) in bp_artists:
                        return track
                
                #Match all artists
                if clean_artists == self._clean_artists(bp_artists):
                    return track


    def _remove_special(self, input: str) -> str:
        specials = '.,()[] &_"' + "'"
        for c in specials:
            input = input.replace(c, '')
        return input.strip()

    def _clean_title(self, title: str) -> str:
        title = re.sub(r'\(*feat[^\(\\[]*', '', title.lower())
        #Remove mid word the
        title = title.replace('the ', '')
        title = self._remove_special(title)
        #Remove Remix/Mix from end
        title = re.sub(r'(re)*mix$', '', title).strip()
        return title

    def _clean_artist(self, artist: str) -> str:
        return self._remove_special(artist.lower())

    def _clean_artists(self, artists: list) -> str:
        return ''.join(sorted([self._clean_artist(a) for a in artists]))


class Track:

    def __init__(self, data: dict):
        self.artists = [BPSmall(artist) for artist in data['artists']]
        self.bpm = data['bpm']
        self.album = BPSmall(data['release'])
        self.duration = data['duration']['milliseconds']
        self.genres = [BPSmall(g) for g in data['genres']]
        self.id = data['id']
        self._art = data['images']['dynamic']['url']
        self.key = data['key']
        self.label = BPSmall(data['label'])
        self.mix = data['mix']
        #Without remix/version stuff
        self.name = data['name']
        #Full title
        self.title = data['title']
        self.release_date = datetime.datetime.strptime(data['date']['released'], '%Y-%m-%d')

    def art(self, resolution: int):
        return self._art.replace('{x}', str(resolution)).replace('{y}', str(resolution)).replace('{w}', str(resolution)).replace('{h}', str(resolution))

#Datatype for sub-types in track data
class BPSmall:

    def __init__(self, data: dict):
        self.name = data['name']
        self.id = data['id']
        self.slug = data['slug']
