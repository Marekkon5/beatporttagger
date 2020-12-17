import os
import requests
import logging
import threading
import copy
import time

from enum import Enum
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPUB, TBPM, TCON, TDAT, TYER, APIC, TKEY, TORY, TXXX
from mutagen.flac import FLAC, Picture
from mutagen.aiff import AIFF

import beatport

UpdatableTags = Enum('UpdatableTags', 'title artist album label bpm genre date key other publishdate')

class TagUpdaterConfig:

    def __init__(self, update_tags = [UpdatableTags.genre], replace_art = False, artist_separator = ';', art_resolution = 1200, fuzziness = 80, overwrite = False):
        self.update_tags = update_tags
        self.replace_art = replace_art
        self.artist_separator = artist_separator
        self.art_resolution = art_resolution
        self.fuzziness = fuzziness
        self.overwrite = overwrite

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

        extensions = ['.mp3', 'flac', 'aiff', '.aif']

        #Get files
        files = []
        for root, _, f in os.walk(path):
            for file in f:
                if file.lower()[-4:] in extensions:
                    files.append(os.path.join(root, file))
        self.total = len(files)

        #Threads
        threads = []
        available = copy.deepcopy(files)
        while len(available) > 0 or len(threads) > 0:
            #Create new threads
            while len(threads) < 16 and len(available) > 0:
                t = threading.Thread(target=self.tag_file, args=(available[0],))
                t.daemon = True
                t.start()
                threads.append(t)
                available.pop(0)

            #Remove done
            for i in range(0, len(threads)):
                #Out of bounds
                if i >= len(threads):
                    break
                if not threads[i].is_alive():
                    threads.pop(i)
                    
            #Prevent infinite loop
            time.sleep(0.005)
            
            
    def tag_file(self, file):
        title, artists = None, None
        file_type = None
        try:
            #MP3 Files
            if file.lower().endswith('.mp3'):
                title, artists = self.info_id3(file)
                file_type = 'mp3'
            #FLAC
            if file.lower().endswith('.flac'):
                title, artists = self.info_flac(file)
                file_type = 'flac'
            #AIFF
            if file.lower().endswith('.aiff') or file.lower().endswith('.aif'):
                title, artists = self.info_id3(file)
                file_type = 'aiff'
    
        except Exception as e:
            logging.error('Invalid file: ' + file)
            self._fail(file)
            return

        if title == None or artists == None:
            self._fail(file)
            logging.error('No metadata in file: ' + file)
            return

        logging.info('Processing file: ' + file)
        #Search
        track = None
        try:
            track = self.beatport.match_track(title, artists, fuzzywuzzy_ratio=self.config.fuzziness)
        except Exception as e:
            logging.error(f'Matching failed: {file}, {str(e)}')
            self._fail(file)
            return

        if track == None:
            logging.error('Track not found on Beatport! ' + file)
            self._fail(file)
            return

        #Update files
        if file_type == 'mp3' or file_type == 'aiff':
            self.update_id3(file, track)
        if file_type == 'flac':
            self.update_flac(file, track)
        self._ok(file)



    def update_id3(self, path: str, track: beatport.Track):
        #AIFF Check
        aiff = None
        if path.endswith('.aiff') or path.endswith('.aif'):
            aiff = AIFF(path)
            f = aiff.tags
        else:
            f = ID3()
            f.load(path, v2_version=3, translate=True)
        
        #Update tags
        if UpdatableTags.title in self.config.update_tags and self.config.overwrite:
            f.setall('TIT2', [TIT2(text=track.title)])
        if UpdatableTags.artist in self.config.update_tags and self.config.overwrite:
            f.setall('TPE1', [TPE1(text=self.config.artist_separator.join([a.name for a in track.artists]))])
        if UpdatableTags.album in self.config.update_tags and (self.config.overwrite or len(f.getall('TALB')) == 0):
            f.setall('TALB', [TALB(text=track.album.name)])
        if UpdatableTags.label in self.config.update_tags and (self.config.overwrite or len(f.getall('TPUB')) == 0):
            f.setall('TPUB', [TPUB(text=track.label.name)])
        if UpdatableTags.bpm in self.config.update_tags and (self.config.overwrite or len(f.getall('TBPM')) == 0):
            f.setall('TBPM', [TBPM(text=str(track.bpm))])
        if UpdatableTags.genre in self.config.update_tags and (self.config.overwrite or len(f.getall('TCON')) == 0):
            f.setall('TCON', [TCON(text=', '.join([g.name for g in track.genres]))])
        if UpdatableTags.date in self.config.update_tags and (self.config.overwrite or (len(f.getall('TYER')) == 0 and len(f.getall('TDAT')) == 0)):
            date = track.release_date.strftime('%d%m')
            f.setall('TDAT', [TDAT(text=date)])
            f.setall('TYER', [TYER(text=str(track.release_date.year))])
        if UpdatableTags.key in self.config.update_tags and (self.config.overwrite or len(f.getall('TKEY')) == 0):
            f.setall('TKEY', [TKEY(text=track.id3key())])
        if UpdatableTags.publishdate in self.config.update_tags and (self.config.overwrite or len(f.getall('TORY')) == 0):
            f.setall('TORY', [TORY(text=str(track.publish_date.year))])
        #Other keys
        if UpdatableTags.other in self.config.update_tags:
            f.add(TXXX(desc='WWWAUDIOFILE', text=track.url()))
            f.add(TXXX(desc='WWWPUBLISHER', text=track.label.url('label')))

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
                logging.warning('Error downloading cover for file: ' + path)

        if aiff == None:    
            f.save(path, v2_version=3, v1=0)
        else:
            aiff.save()

    def update_flac(self, path: str, track: beatport.Track):
        f = FLAC(path)

        if UpdatableTags.title in self.config.update_tags and self.config.overwrite:
            f['TITLE'] = track.title
        if UpdatableTags.artist in self.config.update_tags and self.config.overwrite:
            f['ARTIST'] = self.config.artist_separator.join([a.name for a in track.artists])
        if UpdatableTags.album in self.config.update_tags and (self.config.overwrite or f.get('ALBUM') == None):
            f['ALBUM'] = track.album.name
        if UpdatableTags.label in self.config.update_tags and (self.config.overwrite or f.get('LABEL') == None):
            f['LABEL'] = track.label.name
        if UpdatableTags.bpm in self.config.update_tags and (self.config.overwrite or f.get('BPM') == None):
            f['BPM'] = str(track.bpm)
        if UpdatableTags.genre in self.config.update_tags and (self.config.overwrite or f.get('GENRE') == None):
            f['GENRE'] = ', '.join([g.name for g in track.genres])
        if UpdatableTags.date in self.config.update_tags and (self.config.overwrite or f.get('DATE') == None):
            f['DATE'] = track.release_date.strftime('%Y-%m-%d')
            #Year - part of date
        if UpdatableTags.key in self.config.update_tags and (self.config.overwrite or f.get('INITIALKEY') == None):
            f['INITIALKEY'] = track.id3key()
        if UpdatableTags.publishdate in self.config.update_tags and (self.config.overwrite or f.get('ORIGINALDATE') == None):
            f['ORIGINALDATE'] = str(track.publish_date.year)
        #Other tags
        if UpdatableTags.other in self.config.update_tags:
            f['WWWAUDIOFILE'] = track.url()
            f['WWWPUBLISHER'] = track.label.url('label')

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
                logging.warning('Error downloading cover for file: ' + path)

        f.save()

    #Info returns title and artists aray
    def info_id3(self, path: str) -> (str, list):
        #AIFF
        if path.endswith('.aiff') or path.endswith('.aif'):
            f = AIFF(path).tags
        else:
            f = ID3(path)

        title = str(f['TIT2'])
        artists = self._parse_artists(str(f['TPE1']))
        return title, artists

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