from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
class EmailRequest(BaseModel):
    email_link: str
    
app = FastAPI(title="Email Analyzer API")

# Enable CORS for the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Email Analyzer API is running"}

@app.post("/email")
async def analyze_email_old(email_request: EmailRequest):
    print('\n\n\n'+'data is:', email_request.dict())
    print("Fetching email data for:", email_request.email_link)
    return {"message": "Email fetched", "link": email_request.email_link}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    print("Server is running")