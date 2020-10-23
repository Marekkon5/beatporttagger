# Beatport Tagger

Simple PyQt5 app to update your audio tags & cover with data from Beatport using scrapping (no paid API).

## How to compile:

Install dependencies:
```
pip install --user -r requirements.txt
```
On Linux you might wanna install your system's PyQt5, for example: `sudo apt install python3-pyqt5`  
Compile GUI:
```
pyuic5 mainwindow.ui -o mainwindow.py
```
Start:
```
python3 beatporttagger.py
```
Compiling Windows EXE:
```
pip install pyinstaller
build.bat
```
It should produce a folder in `dist/beatporttagger`.

## Credits

Idea, icon and request by Bas Curtiz.