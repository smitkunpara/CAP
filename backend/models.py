from pydantic import BaseModel
from typing import Optional

class GoogleAuthRequest(BaseModel):
    token: str

class EmailContent(BaseModel):
    subject: str
    from_: str = ""
    to: str = ""
    plainText: str = ""
    htmlContent: str = ""

class EmailRequest(BaseModel):
    email_id: str

