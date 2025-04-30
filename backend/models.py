from pydantic import BaseModel
from typing import Optional

class GoogleAuthRequest(BaseModel):
    token: str

class EmailRequest(BaseModel):
    email_id: str

class EmailData(BaseModel):
    sender: str
    subject: str
    body: Optional[str] = None
    attachments: Optional[list[str]] = []

class EmailReport(BaseModel):
    sender: str
    subject: str
    body: Optional[str] = None
    attachments: Optional[list[dict[str, str]]] = []
    links: Optional[list[str]] = []
    risk_level: str
    phishing: bool
    error: Optional[str] = None