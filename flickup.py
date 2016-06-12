#!/usr/bin/python3

import flickrapi
import pprint
import os
import fnmatch
import re
import datetime
import sys
import configparser

import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

config_file = "/etc/flickrup.conf"
config = configparser.ConfigParser()
try:
    config.read(config_file)
    api_key = config.get("main","api_key")
    api_secret = config.get("main","api_secret")
    api_token = config.get("main","api_token")
    email_from = config.get("main","email_from")
    email_to = config.get("main","email_to")
except:
  print("Missing "+config_file)
  sys.exit(0)


done = ".done"

sdcard = sys.argv[1] + "/"

logfile = sdcard + "upload-log.txt"

includes = ['*.jpg'] # for files only / case insensitive
excludes = ["*"+done,logfile] # for dirs and files / case insensitive

flickr = flickrapi.FlickrAPI(api_key, api_secret, api_token)

def send_mail( send_from, send_to, subject, text, files=[], server="localhost", port=25, username='', password='', isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if isTls: smtp.starttls()
    if len(username)>0 : smtp.login(username,password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

def logit( text ):
    log.write(str(datetime.datetime.utcnow())+ " "+text+"\n")

def cleanexit():

    log.close()

    send_mail( email_from, [email_to], "Photo Upload", "Photo upload log", [logfile])

    sys.exit()

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='write'):
    print("Authentication required")
    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='write')
    print("Open the following URL on your web browser and copy the code to " + config_file)
    print(authorize_url)

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = input('Verifier code: ')

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

    sys.exit()

includes = r'|'.join([fnmatch.translate(x) for x in includes])
excludes = r'|'.join([fnmatch.translate(x) for x in excludes]) or r'$.'

if len(sys.argv) < 2:
    print("Usage: "+sys.argv[0]+" path")
    sys.exit(0)

try:
    log = open(logfile, 'a')
except:
    print("Can't open log file for writing ("+logfile+")")
    sys.exit()

logit("New run")
for root, dirs, files in os.walk(sdcard):

    # exclude dirs
    dirs[:] = [os.path.join(root, d) for d in dirs]
    dirs[:] = [d for d in dirs if not re.match(excludes, d.lower())]

    # exclude/include files
    files = [os.path.join(root, f) for f in files]

    files = [f for f in files if not re.match(excludes, f.lower())]
    files = [f for f in files if re.match(includes, f.lower())]

    for fname in files:
        try:
            resp = flickr.upload(filename=fname, tags='rpiup', is_public=0)
            pre, ext = os.path.splitext(fname)
            os.rename(fname, pre + done)
            logit(fname + " : " + resp.find('photoid').text)
        except:
            logit("Error on " + fname)

logit("End run")
cleanexit()
