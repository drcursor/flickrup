#!/usr/bin/python3

import flickrapi
import pprint
import os
import fnmatch
import re
import datetime
import sys
import configparser
import argparse
import ntpath


import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from tqdm import tqdm


# Default vars
default_args_config = '/etc/flickrup.conf'
default_log_file = 'flickrup.log'
default_uploaded_prefix = '.'

# Initializing argparser
parser = argparse.ArgumentParser(description='Flickrup: Flicker uploader.')

# Enable debug
parser.add_argument('-d',
                    '--debug',
                    help='Debug output. Default: Disabled',
                    action='store_true'
                    )

# Path to config file
parser.add_argument('-c',
                    '--config',
                    help='Path to config file. Defaul: {}'.format(
                        default_args_config),
                    required=False,
                    default=default_args_config
                    )

# Path to dir with pictures
parser.add_argument('-p',
                    '--pictures',
                    help='Path to dir with pictures to upload',
                    required=False,
                    default='/etc/flickrup.conf'
                    )

# Path to log file
parser.add_argument('-l',
                    '--log-file',
                    help='Path to log file. Default: {}'.format(
                        default_log_file),
                    required=False,
                    default=default_log_file
                    )

# prefix for files created to mark uploaded files
parser.add_argument('-u',
                    '--uploaded-prefix',
                    help='File prefix to prevent upload files twice. Default: {}'
                    .format(default_uploaded_prefix),
                    required=False,
                    default=default_uploaded_prefix
                    )


args = parser.parse_args()

# Print resume
if args.debug:
    print("Running with these config options:")
    for arg in vars(args):
        print("\t- {}: {}".format(arg, getattr(args, arg)))


config = configparser.ConfigParser()
try:
    config.read(args.config)
    api_key = config.get("main", "api_key")
    api_secret = config.get("main", "api_secret")
    api_token = config.get("main", "api_token")
    email_from = config.get("main", "email_from")
    email_to = config.get("main", "email_to")
except:
    print("Missing " + args.config)
    sys.exit(0)


includes = ['*.jpg']  # for files only / case insensitive
# for dirs and files / case insensitive
excludes = [args.log_file]

flickr = flickrapi.FlickrAPI(api_key, api_secret, api_token)


def touch(file_name):
    with open(file_name, 'w+'):
        pass
    return True


def send_mail(send_from, send_to, subject, text, files=[], server="localhost", port=25, username='', password='', isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{0}"'.format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if isTls:
        smtp.starttls()
    if len(username) > 0:
        smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


def logit(text):
    log.write(str(datetime.datetime.utcnow()) + " " + text + "\n")


def cleanexit():

    log.close()

    send_mail(email_from, [email_to], "Photo Upload",
              "Photo upload log", [args.log_file])

    sys.exit()

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='write'):
    print("Authentication required")
    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='write')
    print("Open the following URL on your web browser and copy the code to " + args.config)
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
    print("Usage: " + sys.argv[0] + " path")
    sys.exit(0)

try:
    log = open(args.log_file, 'a')
except:
    print("Can't open log file for writing (" + args.log_file + ")")
    sys.exit()

logit("New run")
for root, dirs, files in os.walk(args.pictures + '/'):

    # exclude dirs
    dirs[:] = [os.path.join(root, d) for d in dirs]
    dirs[:] = [d for d in dirs if not re.match(excludes, d.lower())]

    # exclude/include files
    files = [os.path.join(root, f) for f in files]

    files = [f for f in files if not re.match(excludes, f.lower())]
    files = [f for f in files if re.match(includes, f.lower())]

    for fname in tqdm(files):
        control_file = ntpath.dirname(fname) + \
            '/' + \
            args.uploaded_prefix + \
            ntpath.basename(fname)

        if not os.path.isfile(control_file):
            try:
                resp = flickr.upload(filename=fname, tags='rpiup', is_public=0)
                pre, ext = os.path.splitext(fname)
                touch(control_file)
                logit(fname + " : " + resp.find('photoid').text)
            except:
                logit("Error on " + fname)

logit("End run")
cleanexit()
