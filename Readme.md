# What is this?
*starred2enex.py* is a python script that takes the starred.json file from the Google Reader takeout, parses it, and creates an Evernote notebook with all your items in it. 
Options can be seen with *starred2enex.py --help*

## How does it work?
It takes every item in the starred.json file, processes the images (it downloads, parses and encodes), and creates Evernote notes. 
The processing time depends on your internet access speed, as it has to fetch all the images in the stories, and has to embed them into the notes themselves - Evernote does not accept image tags. 
Of course, this process can take a while, depending on the number of starred items - and the Evernote import (File->Import…) and sync will also take some time.

## Anything special?
Next to Python (>=2.7), you might have to install BeautifulSoup and PIL. This can be done with easy_install, eg:
sudo easy_install beautifulsoup
sudo easy_install pil


## Thanks to:
Paul Kerchen (https://github.com/kerchen/) for export2enex, the inspiration for this script.

