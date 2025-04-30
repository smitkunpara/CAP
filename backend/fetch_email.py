import google.oauth2.credentials
from googleapiclient.discovery import build
import base64
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

def get_user_email(access_token, refresh_token, message_id):
    credentials = google.oauth2.credentials.Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
    )
    service = build('gmail', 'v1', credentials=credentials)
    # Using format='full' to get structured data
    return service.users().messages().get(userId='me', id=message_id, format='full').execute()

def get_email_from_gmail(user_email, message_id):
    try:
        user_data = db.get_user(user_email)
        access_token = user_data["access_token"]
        refresh_token = user_data["refresh_token"]
        message = None
        try:
            message = get_user_email(access_token, refresh_token, message_id)
        except Exception as e:
            print(f'Initial attempt failed: {e}')
            new_access_token = refresh_access_token(refresh_token)
            if not new_access_token:
                raise Exception("Failed to refresh access token")
            db.update_user_token(user_email, new_access_token)
            message = get_user_email(new_access_token, refresh_token, message_id)
        
        # Extract only needed data from structured message
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        
        # Get sender and subject
        sender = headers.get("From", "Unknown sender")
        subject = headers.get("Subject", "No subject")
        
        # Extract attachment filenames
        attachment_names = []
        
        # Function to extract email body content
        def get_email_body(message_part):
            body = ""
            
            if 'body' in message_part and message_part['body'].get('data'):
                body = base64.urlsafe_b64decode(message_part['body']['data']).decode('utf-8')
                return body
            
            # If no body found but there are parts, recursively check the parts
            if 'parts' in message_part:
                for part in message_part['parts']:
                    # For multipart/alternative, prefer HTML over plain text
                    if part.get('mimeType') == 'text/html':
                        part_body = get_email_body(part)
                        if part_body:
                            return part_body
                
                # If no HTML found, try plain text
                for part in message_part['parts']:
                    if part.get('mimeType') == 'text/plain':
                        part_body = get_email_body(part)
                        if part_body:
                            return part_body
                
                # If still nothing, check all parts
                for part in message_part['parts']:
                    part_body = get_email_body(part)
                    if part_body:
                        return part_body
                        
            return body
        
        # Function to recursively find attachments in parts
        def extract_attachments(parts):
            for part in parts:
                if 'filename' in part and part['filename']:
                    attachment_names.append(part['filename'])
                
                # Check for nested parts
                if 'parts' in part:
                    extract_attachments(part['parts'])
        
        # Get email body
        body = get_email_body(message['payload'])
        
        # Check if message has parts for attachments
        if 'parts' in message['payload']:
            extract_attachments(message['payload']['parts'])
        
        email_data = {
            "sender": sender,
            "subject": subject,
            "body": body,
            "attachments": attachment_names
        }
        
        return email_data
    except Exception as error:
        print(f'An error occurred: {error}')
        return None
