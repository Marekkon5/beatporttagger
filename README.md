# Beatport Tagger

![Logo](https://github.com/Marekkon5/beatporttagger/raw/main/assets/icon64.png "Logo")

Simple Python app to update your audio tags & cover with data from Beatport using scrapping (no paid API).

# WARNING: Deprecated
This app has been deprecated for OneTagger, because we wanted to unify all the taggers. [Github Repository](https://github.com/Marekkon5/onetagger), [Website](https://onetagger.github.io/).

![Screenshot](https://raw.githubusercontent.com/Marekkon5/beatporttagger/main/assets/screenshot.jpg)

# Compatibility
<table>
    <thead>
        <tr>
            <th>Tested on platform</th>
            <th>Works correctly</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Windows 7</td>
            <td>✅</td>
        </tr>
        <tr>
            <td>Windows 10</td>
            <td>✅</td>
        </tr>
        <tr>
            <td>macOS El Capitan</td>
            <td>✅</td>
        </tr>
        <tr>
            <td>macOS Catalina</td>
            <td>✅</td>
        </tr>
        <tr>
            <td>macOS Big Sur</td>
            <td>✅</td>
        </tr>
        <tr>
            <td>Linux</td>
            <td>✅</td>
        </tr>
    </tbody>
</table>

# Troubleshooting

## MacOS:

If you get a warning on macOS, this app can't be opened for whatever reason:  
- Click Apple icon on top left
- Click System Preferences
- Click Security & Privacy
- Click Open Anyway

## Windows:

If you get an error opening the app like: "(Exception from HRESULT: 0x80010007 (RPC_E_SERVER_DIED))"  
- Try to run it without Admin rights.
- In order to do so, make sure <a href="https://articulate.com/support/article/how-to-turn-user-account-control-on-or-off-in-windows-10">UAC</a> is enabled.
- If you get `Python.Runtime not found` during compiling, run the following commands:
```
pip uninstall pythonnet
pip install pythonnet
```
And try again, if doesn't work, try different Python version

# How to compile:

Install dependencies:
```
pip install --user -r requirements.txt
# If Windows, do also:
pip install cefpython3 --user
```
If you get errors installing dependencies, use Python 3.7 (or 3.6).  

Run:
```
python beatporttagger.py
```
Compile Binary:
```
pip install pyinstaller
pyinstaller --onefile beatporttagger.spec
```
MacOS Binary:
```
pyinstaller --onefile beatporttagger-mac.spec
```
Should be saved in `dist` folder.  

## Showcase

Comparison of strictness settings and simillar projects: https://docs.google.com/spreadsheets/d/1k-grRDQszg2B99CpoK81_cHODy0DwvdhsIAhob0ezJU/edit?usp=sharing  

Trailer: https://youtu.be/D_-ZAX5MIig

## Credits:
UI, icon, idea, trailer, comparisons and request by Bas Curtiz

