import requests
import json
import re
import datetime

from fuzzywuzzy import fuzz
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

        #Some tracks on beatport are invalid, filter them
        out = []
        for t in data['tracks']:
            track = Track(t)
            if (track.name and track.artists and track.duration):
                out.append(track)
        return out

    #Search and match track
    def match_track(self, title: str, artists: list, fuzzywuzzy_ratio = 80):
        query = ', '.join(artists) + f' {title}'
        tracks = self.search_tracks(query)

        clean_title = self._clean_title(title)
        clean_artists = self._clean_artists(artists)

        fuzzy_matches = []
        for track in tracks:
            #Match title
            if clean_title == self._clean_title(track.title):
                #Match single artists
                bp_artists = [self._clean_artist(a.name) for a in track.artists]
                for artist in artists:
                    if self._clean_artist(artist) in bp_artists:
                        return track
                
                #Match all artists
                if clean_artists == self._clean_artists(bp_artists):
                    return track

            #No match - use fuzzywuzzy
            fuzzy = fuzz.token_sort_ratio(self._clean_attributes(track.title), self._clean_attributes(title))
            if fuzzy >= fuzzywuzzy_ratio:
                #Fuzzy match all artists
                bp_artists = ','.join([a.name for a in track.artists])
                if fuzz.token_sort_ratio(','.join(artists), bp_artists) >= fuzzywuzzy_ratio:
                    fuzzy_matches.append((fuzzy, track))
                    continue
                #Match single exact artist
                bp_artists = [self._clean_artist(a.name) for a in track.artists]
                for artist in artists:
                    if self._clean_artist(artist) in bp_artists:
                        fuzzy_matches.append((fuzzy, track))
                        continue
        
        #Get best fuzzy match
        fuzzy_matches.sort(key=lambda i: i[0], reverse=True)
        if len(fuzzy_matches) > 0:
            return fuzzy_matches[0][1]
                

    def _remove_special(self, input: str) -> str:
        specials = '.,()[] &_"' + "'"
        for c in specials:
            input = input.replace(c, '')
        return input.strip()

    #Remove track attributes like Original mix, intro clean
    def _clean_attributes(self, title: str) -> str:
        title = re.sub(r'\(original( (mix|remix))*\)', '', title.lower())
        title = title.replace('(intro)', '')
        title = title.replace('(clean)', '')
        return title.replace('  ', '').strip()

    def _clean_title(self, title: str) -> str:
        title = re.sub(r'\(*feat[^\(\\[]*', '', title.lower())
        title = self._clean_attributes(title)
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
        self.exclusive = data['exclusive']
        self.slug = data['slug']
        #Without remix/version stuff
        self.name = data['name']
        #Full title
        self.title = data['title']
        if self.title == None or self.title == "" or self.title == " ":
            self.title = f"{data['name']} ({data['mix']})"

        self.release_date = datetime.datetime.strptime(data['date']['released'], '%Y-%m-%d')
        self.publish_date = datetime.datetime.strptime(data['date']['published'], '%Y-%m-%d')

    def art(self, resolution: int):
        if '{x}' in self._art or '{w}' in self._art:
            return self._art.replace('{x}', str(resolution)).replace('{y}', str(resolution)).replace('{w}', str(resolution)).replace('{h}', str(resolution))
        if '/image_size/' not in self._art:
            return self._art

        #Parse non-dynamic dynamic image
        return re.sub(r'\/image_size\/\d+x\d+\/', f'/image_size/{resolution}x{resolution}/', self._art)

    #Convert Beatport key to ID3
    def id3key(self):
        return self.key.replace('\u266d', 'b').replace('\u266f', '#').replace('min', 'm').replace('maj', '').replace(' ', '')

    def url(self):
        return f'https://beatport.com/track/{self.slug}/{self.id}'

#Datatype for sub-types in track data
class BPSmall:

    def __init__(self, data: dict):
        self.name = data['name']
        self.id = data['id']
        self.slug = data['slug']

    def url(self, type):
        return f'https://beatport.com/{type}/{self.slug}/{self.id}'
