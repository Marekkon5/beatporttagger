import webview
import os
import tagger
import math

class JSAPI:
    def __init__(self):
        self.tagger = None

    def browseFolder(self):
        return window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG, allow_multiple=False)

    def start(self):
        #Validate path
        path = window.get_elements('#path')[0]['value']
        if not os.path.exists(path):
            window.evaluate_js('alert("Invalid path!")')
            return

        #Generate config
        jconfig = window.evaluate_js('getConfig()')
        config = tagger.TagUpdaterConfig(
            update_tags = [tagger.UpdatableTags[t] for t in jconfig['tags']],
            replace_art=jconfig['replaceArt'],
            art_resolution=jconfig['artResolution'],
            artist_separator=jconfig['artistSeparator'],
            fuzziness=jconfig['fuzziness']
        )

        #Prepare tagger
        self.tagger = tagger.TagUpdater(config, success_callback=self.success, fail_callback=self.fail)
        self.tagger.tag_dir(path)
        window.evaluate_js('alert("Done!")')
        return

    def success(self, path):
        self.update()

    def fail(self, path):
        self.update()

    def update(self):
        if self.tagger != None and self.tagger.total > 0:
            #Percentage
            p = (len(self.tagger.success) + len(self.tagger.fail)) / self.tagger.total
            percent = math.floor(p*100)
            window.evaluate_js(f'updateProgress({percent}, {len(self.tagger.success)}, {len(self.tagger.fail)})')

window = webview.create_window(
    'Beatport Tagger', 
    'html/index.html',
    resizable=True,
    width=420,
    height=860,
    min_size=(420, 420),
    js_api=JSAPI()
)

if __name__ == '__main__':
    webview.start(debug=False)