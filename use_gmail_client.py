# Use Python 2.7

import os
import time
import shutil
import base64
import argparse
import datetime
import httplib2
import requests
import threading
import subprocess
import pandas as pd
import oauth2client
from BeautifulSoup import BeautifulSoup
from apiclient import discovery, errors
from oauth2client import client, file


def get_credentials():

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    return credentials


def GetMessage(service, user_id, msg_id):

    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        return message
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def ListMessagesMatchingQuery(service, user_id, query=''):
    response = service.users().messages().list(userId=user_id, q=query).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query,
                                            pageToken=page_token).execute()
        messages.extend(response['messages'])

    return messages


# ------------------- #
#     main program    #
# ------------------- #
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--date', help='date to parse, ex: 2016-02-06')
args = parser.parse_args()

if args.date is not None:
    date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
else:
    date = datetime.datetime.today().date() - datetime.timedelta(days=1)

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)

date_str = datetime.datetime.today().date().strftime('%Y/%m/%d')

query = 'Amazon Your order has been shipped after:{0:}'.format(date_str)
m_ids = ListMessagesMatchingQuery(service, 'me', query=query)
msg = GetMessage(service, 'me', m_ids[0]['id'])
http_content = base64.urlsafe_b64decode(msg['payload']['parts'][0]['parts'][1]['body']['data'].encode('UTF-8'))

download_url = None
soup = BeautifulSoup(http_content)
for link in soup.findAll('a'):
    if link.get('href').startswith('http://tracking/packages/'):
        download_url = link.get('href')

file_name = 'download_file_{0:}.txt'.format(date)

s = requests.Session()
r = s.get(download_url, stream=True)
r.raw.decode_content = True
f = open(file_name, 'wb')
shutil.copyfileobj(r.raw, f) 
f.close()
r.close()
s.close()

