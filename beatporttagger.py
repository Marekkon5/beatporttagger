import webview
import os
import tagger
import math
import sys
import json
import threading
import logging

from flask import Flask, send_from_directory, request

#Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARN)

progress = {}
_tagger = None

#Get path to assets dir, for pyinstaller
def assets_path():
    path = os.getcwd()
    try:
        path = getattr(sys, '_MEIPASS')
    except Exception:
        pass
    return os.path.join(path, 'assets')

#Flask setup
app = Flask(__name__, static_url_path='', static_folder=assets_path())

@app.route('/')
def index():
    return send_from_directory(assets_path(), 'index.html')

#Browse for file
@app.route('/browse')
def browse():
    p = window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG, allow_multiple=False)
    if p == None:
        return ''
    return p[0]

#Return text = error
@app.route('/start', methods = ['POST'])
def start():
    data = request.get_json(force=True)
    #Check path
    path = data['path']
    if not os.path.isdir(path):
        return 'Invalid path!'

    #Generate config
    config = tagger.TagUpdaterConfig(
        update_tags = [tagger.UpdatableTags[t] for t in data['tags']],
        replace_art=data['replaceArt'],
        art_resolution=data['artResolution'],
        artist_separator=data['artistSeparator'],
        fuzziness=data['fuzziness'],
        overwrite=data['overwrite']
    )

    #Start
    thread = threading.Thread(target=start_tagger, args=(config,path))
    thread.start()

    return ''

@app.route('/progress')
def progress_request():
    return json.dumps(progress)

#Generate JSON with progress for UI
def _update_progress(file):
    global progress
    if _tagger != None and _tagger.total > 0:
        #Percentage
        p = (len(_tagger.success) + len(_tagger.fail)) / _tagger.total
        percent = math.floor(p*100)
        progress = {
            'percent': percent,
            'success': len(_tagger.success),
            'failed': len(_tagger.fail)
        }

def start_tagger(config, path):
    global progress
    global _tagger
    #Reset progress
    progress = {}
    _tagger = tagger.TagUpdater(config, success_callback=_update_progress, fail_callback=_update_progress)
    _tagger.tag_dir(path)

def start_flask():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    app.run(host='127.0.0.1', port=36958)

if __name__ == '__main__':
    #Flask
    thread = threading.Thread(target=start_flask)
    thread.daemon = True
    thread.start()
    #Pywebview
    window = webview.create_window(
        'Beatport Tagger', 
        'http://localhost:36958/',
        resizable=False,
        width=400,
        height=845,
        min_size=(400, 845),
    )
    webview.start(debug=False)
    sys.exit()