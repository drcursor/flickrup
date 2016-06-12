# flickrup

## Concept
Simple script that automatically uploads all photo files from a connected removable disk/card to Flickr.
This should be run on a standalone device (eg. Raspberry PI).

## Requirements
- Python 3
- flickrapi package
- working local sendmail
- usbmount

## Install
The following procedure assumes you have a working Debian/Raspbian system with network access.

- Install requirements
~~~~
sudo apt-get install python3 python3-pip postfix usbmount
sudo pip3 install flickrapi
~~~~
- Copy files to correct locations
~~~~
sudo cp flickrup.py /usb/bin
sudo chmod a+x /usb/bin/flickrup.py
sudo cp flickrup.conf /etc
sudo cp 01_process /etc/usbmount/mount.d
sudo chmod a+x /etc/usbmount/mount.d/01_process
~~~~
- Define correct API key and secret in /etc/flickrup.conf (Default should be OK)
- Define from and to email in in /etc/flickrup.conf
- Run /usb/bin/flickrup.py and follow screen instructions

## Configuration
- API keys as well as email options are defined on /etc/flickrup.conf
- File extensions as well as exceptions can be configured in flickrup.py

## Usage
- Whenever a USB mass storage device is connected (eg. SD/CF Card), flickrup will automatically upload the files to flickr (with private permissions). Uploaded files are renamed and a log file is created at the root of the storage device. Additionally the log file is sent to the email defined in the configuration file. After the email is sent, the mass storage device is unmounted, and can be safely removed.
