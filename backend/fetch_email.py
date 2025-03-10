import google.oauth2.credentials
from googleapiclient.discovery import build
import base64
import email

def get_email_from_gmail(message_id):
    try:
        oauth_token = "ya29.A0AeXRPp7ZKSC7_2s25OUXnVdoenf_rsh-2KiF2_OYC6ON6FE3bWTaW1L5XXZwSR-qFlI04J3CQazxmx9PvP1COmsB4jrsh1pY4bPb6ivHuVIO0Y2zLnqVes247HGQH41zOcQNZJaINNpEOeh7obBImbzI7uMmEUyMQw4BV5k2J7o62JefphhtDee-bK3HXMJ-kPsatu6vez9X_aM1WkVRnpEhLUqYQelwwWikvnYt1d9Uy3Cv_12BwZlZHbm6-zxqUXmlQh2oiDHjG9iuohdsF9FzhWURslCLkmp1ae53SpxPOXaCrlZOvdSsXwy1aGRwGbm1rwaCgYKAcsSARASFQHGX2MivLgaHLmZlVTbOn0nmLZkrw0333"
        credentials = google.oauth2.credentials.Credentials(oauth_token)
        service = build('gmail', 'v1', credentials=credentials)
        message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
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
