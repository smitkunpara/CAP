from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from auth import router as auth_router, get_current_user
from fetch_email import get_email_from_gmail
from models import EmailRequest
from analyze_email import analyze_email
from database import db
import os

app = FastAPI(title="Email Analyzer API")

# Enable CORS for the Chrome extension and Gmail
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "https://mail.google.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")

@app.get("/")
async def root():
    return {"message": "Email Analyzer API is running"}

@app.post("/email")
async def email(request: EmailRequest, userdata = Depends(get_current_user)):
    try:
        email = get_email_from_gmail(user_email=userdata["email"], message_id=request.email_id)
        
        # Use CPU instead of CUDA to avoid the device-side assertion errors
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        
        report = analyze_email(email)
        db.add_email_analysis(userdata["user_id"], report)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@app.get("/email/{email_id}")
async def get_email(email_id: str, userdata = Depends(get_current_user)):
    return db.get_email_analysis(email_id)

@app.get("/emails")
async def get_all_user_emails(user_id: str, userdata = Depends(get_current_user)):
    email_ids = db.get_all_user_emails(userdata["user_id"])
    return email_ids

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    print("Server is running")

