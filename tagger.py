import os
import requests

from enum import Enum
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPUB, TBPM, TCON, TDAT, TYER, APIC, TKEY
from mutagen.flac import FLAC, Picture

import beatport

UpdatableTags = Enum('UpdatableTags', 'title artist album label bpm genre date key')

class TagUpdaterConfig:

    def __init__(self, update_tags = [UpdatableTags.genre], replace_art = False, artist_separator = ';', art_resolution = 1200, fuzziness = 80):
        self.update_tags = update_tags
        self.replace_art = replace_art
        self.artist_separator = artist_separator
        self.art_resolution = art_resolution
        self.fuzziness = fuzziness

class TagUpdater:

    def __init__(self, config: TagUpdaterConfig, success_callback=None, fail_callback=None):
        self.config = config
        self.beatport = beatport.Beatport()
        self._success_callback = success_callback
        self._fail_callback = fail_callback
        self.success = []
        self.fail = []
        self.total = 0

    #Mark file as succesfull
    def _ok(self, path: str):
        self.success.append(path)
        if self._success_callback != None:
            self._success_callback(path)

    def _fail(self, path: str):
        self.fail.append(path)
        if self._fail_callback != None:
            self._fail_callback(path)

    def tag_dir(self, path: str):
        #Reset
        self.success = []
        self.fail = []
        self.total = 0

        #Get files
        files = []
        for root, _, f in os.walk(path):
            for file in f:
                if file.lower().endswith('.mp3') or file.lower().endswith('.flac'):
                    files.append(os.path.join(root, file))
        self.total = len(files)

        for file in files:
            title, artists = None, None
            file_type = None
            #MP3 Files
            if file.lower().endswith('.mp3'):
                try:
                    title, artists = self.info_mp3(file)
                except Exception:
                    print('Invalid file: ' + file)
                    self._fail(file)
                    continue
                file_type = 'mp3'
            #FLAC
            if file.lower().endswith('.flac'):
                try:
                    title, artists = self.info_flac(file)
                except Exception:
                    print('Invalid file: ' + file)
                    self._fail(file)
                    continue
                file_type = 'flac'

            if title != None and artists != None:
                print('Processing file: ' + file)
                #Search
                track = None
                try:
                    track = self.beatport.match_track(title, artists, fuzzywuzzy_ratio=self.config.fuzziness)
                except Exception as e:
                    print(f'Matching failed: {file}, {str(e)}')
                    self._fail(file)
                    continue

                if track == None:
                    print('Track not found on Beatport! ' + file)
                    self._fail(file)
                    continue
                
                #Update files
                if file_type == 'mp3':
                    self.update_mp3(file, track)
                if file_type == 'flac':
                    self.update_flac(file, track)
                
                self._ok(file)
            
            else:
                self._fail(file)
                print('No metadata in file: ' + file)


    def update_mp3(self, path: str, track: beatport.Track):
        f = ID3(path)
        
        #Update tags
        if UpdatableTags.title in self.config.update_tags:
            f['TIT2'] = TIT2(text=track.title)
        if UpdatableTags.artist in self.config.update_tags:
            f['TPE1'] = TPE1(text=self.config.artist_separator.join([a.name for a in track.artists]))
        if UpdatableTags.album in self.config.update_tags:
            f['TALB'] = TALB(text=track.album.name)
        if UpdatableTags.label in self.config.update_tags:
            f['TPUB'] = TPUB(text=track.label.name)
        if UpdatableTags.bpm in self.config.update_tags:
            f['TBPM'] = TBPM(text=str(track.bpm))
        if UpdatableTags.genre in self.config.update_tags:
            f['TCON'] = TCON(text=', '.join([g.name for g in track.genres]))
        if UpdatableTags.date in self.config.update_tags:
            date = track.release_date.strftime('%d%m')
            f['TDAT'] = TDAT(text=date)
            f['TYER'] = TYER(text=str(track.release_date.year))
        if UpdatableTags.key in self.config.update_tags:
            f['TKEY'] = TKEY(text=track.id3key())
        

        #Redownlaod cover
        if self.config.replace_art:
            try:
                url = track.art(self.config.art_resolution)
                r = requests.get(url)
                data = APIC(
                    encoding = 3,
                    mime = 'image/jpeg',
                    type = 3,
                    desc = u'Cover',
                    data = r.content
                )
                f.delall('APIC')
                f['APIC:cover.jpg'] = data

            except Exception:
                print('Error downloading cover for file: ' + path)

        f.save(v2_version=3)
        #Remove V1 tags
        f.delete(path, delete_v1=True, delete_v2=False)

    def update_flac(self, path: str, track: beatport.Track):
        f = FLAC(path)

        if UpdatableTags.title in self.config.update_tags:
            f['TITLE'] = track.title
        if UpdatableTags.artist in self.config.update_tags:
            f['ARTIST'] = self.config.artist_separator.join([a.name for a in track.artists])
        if UpdatableTags.album in self.config.update_tags:
            f['ALBUM'] = track.album.name
        if UpdatableTags.label in self.config.update_tags:
            f['LABEL'] = track.label.name
        if UpdatableTags.bpm in self.config.update_tags:
            f['BPM'] = str(track.bpm)
        if UpdatableTags.genre in self.config.update_tags:
            f['GENRE'] = ', '.join([g.name for g in track.genres])
        if UpdatableTags.date in self.config.update_tags:
            f['DATE'] = track.release_date.strftime('%Y-%m-%d')
            #Year - part of date
        if UpdatableTags.key in self.config.update_tags:
            f['INITIALKEY'] = track.id3key()

        #Redownlaod cover
        if self.config.replace_art:
            try:
                url = track.art(self.config.art_resolution)
                r = requests.get(url)
                image = Picture()
                image.type = 3
                image.mime = 'image/jpeg'
                image.desc = 'Cover'
                image.data = r.content
                f.clear_pictures()
                f.add_picture(image)
            except Exception:
                print('Error downloading cover for file: ' + path)

        f.save()

    #Info returns title and artists aray
    def info_mp3(self, path: str) -> (str, list):
        f = ID3(path)
        title = str(f['TIT2'])
        artists = self._parse_artists(str(f['TPE1']))
        return title, artists

    #Info returns title and artists aray
    def info_flac(self, path: str) -> (str, list):
        f = FLAC(path)
        title = str(f['title'][0])
        if len(f['artist']) > 1:
            artists = f['artist']
        else:
            artists = self._parse_artists(f['artist'][0])
        return title, artists


    #Artist separators
    def _parse_artists(self, input: str) -> list:
        if ';' in input:
            return input.split(';')
        if ',' in input:
            return input.split(',')
        if '/' in input:
            return input.split('/')
        return [input]