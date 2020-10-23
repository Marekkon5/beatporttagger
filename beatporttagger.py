import sys
import os
import math
import threading

from PyQt5 import QtWidgets, QtGui, uic

import mainwindow
import tagger

class MainWindow(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        #Icon
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.environ.get('_MEIPASS', os.path.abspath(".")), 'icon.png')))
            
        #Browser button
        self.browse_button.clicked.connect(self.browse_folder)

        self.start_button.clicked.connect(self.start_click)

    def browse_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if path != None:
            self.path_entry.setText(path)

    def start_click(self):
        #Check path
        path = self.path_entry.text()
        if not os.path.exists(path) or path == None or path == '':
            #Error dialog
            dialog = QtWidgets.QErrorMessage()
            dialog.showMessage('Invalid path!')
            dialog.setWindowTitle('Error')
            dialog.exec_()
            return

        #Generate settings
        config = tagger.TagUpdaterConfig(update_tags=[
            tagger.UpdatableTags.title if self.update_title.isChecked() else None,
            tagger.UpdatableTags.artist if self.update_artists.isChecked() else None,
            tagger.UpdatableTags.album if self.update_album.isChecked() else None,
            tagger.UpdatableTags.label if self.update_label.isChecked() else None,
            tagger.UpdatableTags.bpm if self.update_bpm.isChecked() else None,
            tagger.UpdatableTags.genre if self.update_genre.isChecked() else None,
            tagger.UpdatableTags.date if self.update_date.isChecked() else None,
        ],
            replace_art=self.replace_art.isChecked(),
            art_resolution=self.art_resolution.value(),
            artist_separator=self.artist_separator.text()
        )

        #Disable button
        self.start_button.setEnabled(False)

        #Start thread
        self.path = path
        self.tagger = tagger.TagUpdater(config, callback=self.progress_callback)
        self.taggerThread = threading.Thread(target=self.tagger_thread)
        self.taggerThread.start()

    def tagger_thread(self):
        print('Starting...')
        self.tagger.tag_dir(self.path)
        self.start_button.setEnabled(True)

        #Show done dialog
        # Causes errors/crashes because of threading
        # QtWidgets.QMessageBox.information(self, 'Done', 'Finished!')

        print('Done!')

    def progress_callback(self):
        if self.tagger != None and self.tagger.total > 0:
            #Percentage
            p = (len(self.tagger.success) + len(self.tagger.fail)) / self.tagger.total
            self.progress_bar.setValue(math.floor(p*100))

            #Success, fail
            self.success_count.setText(str(len(self.tagger.success)))
            self.fail_count.setText(str(len(self.tagger.fail)))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()