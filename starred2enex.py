#!/usr/bin/python
# this script imports a google reader starred.json file and spits out evernote enex files
#
import json
import sys
import argparse
import codecs
import datetime
import time
from xml.sax.saxutils import escape
from BeautifulSoup import BeautifulSoup as bs 	# html parsing
import urllib2 as ul 	# image downloading
import base64		# image encoding
import hashlib		# for the image hashes
import urlparse		# to complete the image urls 
import StringIO		# for the image stuff below
import Image 		# for the image size and type
import imghdr		# to get the mime type

# some defaults
charEncoding=	"UTF-8"
fileName	=	"starred.json"
bookName	=	"Starred"
limit 		= 	100
verbose		=	True
timeStamp=datetime.datetime.today()


# get the options from the command line, and parse them
argParser=argparse.ArgumentParser(prog="starred2enex.py")
argParser.add_argument("-f","--file",nargs="?",help="specifies the file you want to import. Defaults to 'starred.json'")
argParser.add_argument("-n","--notebook",nargs="?",help="specifies the Evernote notebook name you want to use. Defaults to 'Starred'")
argParser.add_argument("-c","--count",nargs="?",help="specifies the number of notes per book. Defaults to 100.")
argParser.add_argument("-v","--verbose",help="Has the script output the titles of the items it's parsing.")
args=argParser.parse_args()


if args.file:
	fileName=args.file
if args.notebook:
	bookName=args.notebook
if args.count:
	limit=int(args.count)
if args.verbose:
	verbose=True

# open the file, and try to read
try:
	jFile = codecs.open(fileName,encoding=charEncoding)
except:
	print "\nERROR: Can't open %s\n" % fileName
	argParser.print_help()
	sys.exit(2)

# let's try to load the json data
try:
	jDict=json.loads(jFile.read())
except:
	print "\nERROR: %s is not a valid json file\n" % (fileName)
	argParser.print_help()
	sys.exit(3)

# get an item array
items=jDict["items"]


# do we have a new file?

# print the header


# parse the items, and print them
itemcount = 0
filecount = 0
f = ''
for item in jDict["items"]:
	# do we need to open a new output file?
	if itemcount == 0:
		# open the file, append mode, and write the notebook header
		f = open(bookName+str(filecount)+'.enex','w')
		print "Outputting to %s%s.enex" % (bookName,str(filecount))
		f.write('<?xml version="1.0" encoding="'+charEncoding+'"?><!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export2.dtd"><en-export export-date="'+timeStamp.strftime('%Y%m%dT%H%M%SZ')+'" application="Evernote" version="Evernote Mac 5.1.4 (401297)">')


	# initialze some variables:
	noteTitle=""
	noteOrigin=""
	noteContent=""
	noteUrl=""
	noteDatePublished=""
	noteDateUpdated=""
	noteFull=""
	noteResource=""

	# get out the title and blog name
	if "title" in item.keys():
		noteTitle=item["title"].encode(charEncoding,"replace")
		print "\t" + noteTitle
	else:
		# if we don't have a title, we can skip this item
		continue

	# origin = blog name
	if "origin" in item.keys():
		noteOrigin=item["origin"]["title"].encode(charEncoding,"replace")
		noteTitle = noteTitle + " - " + noteOrigin

	# print the note header
	noteFull = '<note><title>'+noteTitle+'</title><content><![CDATA[<?xml version="1.0" encoding="'+charEncoding+'" standalone="no"?> <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note>'

	# parse the item url here, we might need it for the images
	if "canonical" in item.keys():
		noteUrl=item["canonical"][0]["href"].encode(charEncoding,"replace")
	else:
		noteUrl=item["alternate"][0]["href"].encode(charEncoding,"replace")

	# get the note content, and add it, and parse the images
	imageDict 	= 	{}
	imageAttrs	=	{}
	content = ''
	if "content" in item.keys():
		content = item["content"]["content"]
	elif "summary" in item.keys():
		content = item["summary"]["content"]

	imageHash=""
	# use beautifulsoup to find the img tags
	soup = bs(content)
	downloader = ul.build_opener()
	
	# image processing
	for img in soup.findAll('img'):
		# check if img paths are relative or not, and construct if necessary
		try:
			if not urlparse.urlsplit(img['src'])[1]:
				# no location in the img src, so we need to create it
				img['src'] = urlparse.urljoin(noteUrl,img['src'])
		except:
			img.extract()
			continue

		# download the images, hash and encode, catch the errors
		try:
			#print "\t\tGetting: %s" % (img['src'])
			image = downloader.open(ul.Request(img['src']))
		except ul.URLError, e:
			# we can't download the img for whatever reason, so we remove the img tag
			img.extract()
		except ul.HTTPError, e:
			img.extract()
			
		else:
			# we've found the image. download/hash/encode/save the attributes
			attributes = {}
			image = image.read()
			imageHash	=	hashlib.md5(image).hexdigest()
			attributes['type'] = imghdr.what(StringIO.StringIO(image))
			if attributes['type']:
				# we have a valid image, so we can add it
				attributes['width'],attributes['height'] = Image.open(StringIO.StringIO(image)).size
				imageDict[imageHash] 	= 	base64.b64encode(image)
				imageAttrs[imageHash]	=	attributes	 

				# replace the src attribute (with beatifulsoup)
				img.name = 'en-media'
				img['type'] = 'image/' + str(imageAttrs[imageHash]['type'])
				img['hash']=imageHash
				try: 
					del img['src']
				except:
					print ""
				try:
					del img['ismap']
				except:
					print ""	
			else:
				# invalid image type, so we can delete
				img.extract()

	# iframe / ... parsing --> kill'em, they're not allowed in an enex
	for bad in soup.findAll(['applet','base','basefont','bgsound','blink','body','button','dir','embed','fieldset','form','frame','frameset','head','html','iframe','ilayer','input','isindex','label','layer,','legend','link','marquee','menu','meta','noframes','noscript','object','optgroup','option','param','plaintext','script','select','style','textarea','xml']):
		bad.extract()
			
	# print the soup as the note body
	noteFull = noteFull + unicode(soup).encode(charEncoding,"replace") + '</en-note>]]></content>'

	# create the <resource> tag in the .enex, loop over the imageDict
	for imageHash in imageDict.keys():
		noteResource = noteResource + '<resource><data encoding="base64">' + imageDict[imageHash] + '</data>'
		noteResource = noteResource + '<mime>image/' + str(imageAttrs[imageHash]['type']) + '</mime>'
		noteResource = noteResource + '<width>' + str(imageAttrs[imageHash]['width']) + '</width><height>' + str(imageAttrs[imageHash]['height']) + '</height><duration>0</duration><recognition>'

		noteResource = noteResource + '<![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="yes"?><!DOCTYPE recoIndex PUBLIC "SYSTEM" "http://xml.evernote.com/pub/recoIndex.dtd"><recoIndex docType="unknown" objType="image" objID="' + str(imageHash)+ '" engineVersion="5.0.40.8" recoType="service" lang="en" objWidth="' + str(imageAttrs[imageHash]['width']) + '" objHeight="' + str(imageAttrs[imageHash]['height']) + '"></recoIndex>]]>'

		noteResource = noteResource + '</recognition><resource-attributes><timestamp>19700101T000000Z</timestamp><reco-type>unknown</reco-type></resource-attributes></resource>'
	
	# get the dates and add them
	if "published" in item.keys():
		noteDatePublished = time.strftime("%Y%m%dT%H%M%SZ", time.localtime(item["published"]))
	if "updated" in item.keys():
		noteDateUpdated = time.strftime("%Y%m%dT%H%M%SZ", time.localtime(item["updated"]))
	noteFull = noteFull+'<created>'+noteDatePublished+'</created><updated>'+noteDateUpdated+'</updated>'

	# and the end of the note, with the correct url
	noteFull = noteFull+'<note-attributes><source>web.clip</source><source-url>' + escape(noteUrl) + '</source-url></note-attributes>'
	noteFull = noteFull + noteResource
	noteFull = noteFull + '</note>\r\n'

	f.write(noteFull)
	itemcount = itemcount+1

	if itemcount == limit:
		f.write('</en-export>')
		f.close()
		itemcount = 0
		filecount = filecount+1

# and the end of the notes
f.write ('</en-export>')
f.close

