# Beatport Tagger

Simple Python app to update your audio tags & cover with data from Beatport using scrapping (no paid API).

## How to compile:

Install dependencies:
```
pip install --user -r requirements.txt
```
Run:
```
python beatporttagger.py
```
Compile Binary:
```
pip install pyinstaller
pyinstaller --onefile beatporttagger.spec
```
Should be saved in `dist` folder.  

## Credits:
UI, icon, idea, request by Bas Curtiz