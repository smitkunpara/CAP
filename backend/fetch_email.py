import google.oauth2.credentials
from googleapiclient.discovery import build
import base64
import email
import requests
from config import settings
from database import db

def refresh_access_token(refresh_token):
    try:
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as error:
        print(f'Error refreshing token: {error}')
        return None

def get_user_email(access_token,refresh_token,message_id):
    credentials = google.oauth2.credentials.Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
    )
    service = build('gmail', 'v1', credentials=credentials)
    return service.users().messages().get(userId='me', id=message_id, format='raw').execute()

def get_email_from_gmail(user_email,message_id):
    try:
        user_data = db.get_user(user_email)
        access_token = user_data["access_token"]
        refresh_token = user_data["refresh_token"]
        message = None
        try:
            message = get_user_email(access_token,refresh_token,message_id)
        except Exception as e:
            print(f'Initial attempt failed: {e}')
            new_access_token = refresh_access_token(refresh_token)
            if not new_access_token:
                raise Exception("Failed to refresh access token")
            db.update_user_token(user_email,new_access_token)
            message = get_user_email(new_access_token,refresh_token,message_id)
        
        msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8"))
        email_msg = email.message_from_bytes(msg_str)
        print("Subject:", email_msg["Subject"])
        # print("From:", email_msg["From"])
        # print("To:", email_msg["To"])
        # if email_msg.is_multipart():
        #     for part in email_msg.walk():
        #         if part.get_content_type() == "text/plain":
        #             print("Body:", part.get_payload())
        # else:
        #     print("Body:", email_msg.get_payload())
        return "got email"
    except Exception as error:
        print(f'An error occurred: {error}')
        return None
