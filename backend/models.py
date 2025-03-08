from pydantic import BaseModel

class GoogleAuthRequest(BaseModel):
    token: str

class EmailRequest(BaseModel):
    email_link: str

