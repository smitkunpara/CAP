import google.oauth2.credentials
from googleapiclient.discovery import build
import base64
import email
import requests
from backend.config import settings

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

def get_email_from_gmail(message_id):
    try:
        # Get refresh token from config
        refresh_token = settings.GOOGLE_REFRESH_TOKEN
        
        # First try with the current access token
        try:
            credentials = google.oauth2.credentials.Credentials(
                token=settings.oauth_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            service = build('gmail', 'v1', credentials=credentials)
            message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
        except Exception as e:
            print(f'Initial attempt failed: {e}')
            # If initial attempt fails, try refreshing the token
            new_access_token = refresh_access_token(refresh_token)
            if not new_access_token:
                raise Exception("Failed to refresh access token")
            
            # Create new credentials with refreshed token
            credentials = google.oauth2.credentials.Credentials(
                token=new_access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            service = build('gmail', 'v1', credentials=credentials)
            message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()

        # Process the email message
        msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8"))
        email_msg = email.message_from_bytes(msg_str)
        print("Subject:", email_msg["Subject"])
        print("From:", email_msg["From"])
        print("To:", email_msg["To"])
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    print("Body:", part.get_payload())
        else:
            print("Body:", email_msg.get_payload())
        return "got email"
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

# print(get_email_from_gmail("1957fe88782ffa39"))