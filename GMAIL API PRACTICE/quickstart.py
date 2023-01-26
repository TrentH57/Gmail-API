from __future__ import print_function

import os.path
import pickle
import base64
import email
import os


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def initiate():
    creds = None
    if os.path.exists('token.json'): # The file token.json stores the user's access and refresh tokens, and iscreated automatically when the authorization flow completes for the first time.
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if creds and creds.valid:
            return creds

    if not creds or not creds.valid: # If there are no (valid) credentials available, let the user log in.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            return creds
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token: # Save the credentials for the next run
            token.write(creds.to_json())
            return creds

def check_for_mail(service):
    try:
        messageresults = service.users().messages().list(userId='me').execute()
        messages = messageresults.get('messages', [])
        return messages

    except HttpError as error:
        print(f'An error occurred: {error}') #still working on error handling

def screen_mail(messages): #set a condition to only bother handling emails that meet specific criteria
    print('messages:')
    for message in messages:
        content = service.users().messages().get(userId='me', id=message['id']).execute() #gets the parts of the specific email by Id
        try:
            payload = content['payload']
            headers = payload['headers']
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                if header['name'] == 'From':
                    sender = header['value']
            if sender == "***INSERT_SENDER_TO_SCREEN_FOR: SHOULD_BE_THE_EXACT_TEXT_GRABBED_FROM_THE_'FROM'_HEADER_OF_AN_EMAIL***": #this condition can be one of many, it can check for specific labels, senders, subjects, whatever you want
                handle_mail(content, subject, sender)

        except:
            print("houston we have a problem", "\n") # Working on propert error handling
            pass

def handle_mail(message, subject, sender): #download all files attached to email and gets the body of the email using BeautifulSoup
    attachments=[]
    payload = message['payload']
    print(f"This is from {sender}")
    for part in message['payload']['parts']:
        if part['filename']:
            attachments.append(download_files(message, part))
            

        parts = payload.get('parts')[0] # the structure of the payload is different if there are attachments. There are two different "parts" within the payload if there are attachments so the call for 'parts' doesn't work and you have to be specific
        if 'parts' in parts:
            items = parts['parts'] #items has all parts of the payload including the files, but only the text body of the email had the 'body' and 'data' keys
            for item in items:
                data = item['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                soup = BeautifulSoup(decoded_data , "lxml")
                mainBody = soup.body

        else:
            data = parts['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            soup = BeautifulSoup(decoded_data , "lxml")
            mainBody = soup.body()

    print("Sender: ", sender)
    print("Subject: ", subject)
    print("Message: ", mainBody)
    if attachments:
        print("Attachments: ")
        for attachment in attachments:
            print(attachment)
    print('\n')

def download_files(message, email_part):
    attachment_Id = email_part['body']['attachmentId']
    attachment = service.users().messages().attachments().get(userId = 'me', messageId=message['id'], id=attachment_Id).execute()
    attachment_b64_data = attachment['data']
    attachment_data = base64.urlsafe_b64decode(attachment_b64_data.encode('UTF-8'))
    filename = email_part['filename']
    save_location = os.getcwd()
    with open(os.path.join(save_location, filename), 'wb') as file:
        file.write(attachment_data)
    return filename




if __name__ == '__main__':
    creds = initiate()
    service = build('gmail', 'v1', credentials=creds)
    messages = check_for_mail(service)
    screen_mail(messages)
