from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from auth import router as auth_router , get_current_user
from models import EmailRequest
from fetch_email import get_email_from_gmail

app = FastAPI(title="Email Analyzer API")
app.include_router(auth_router,prefix="/auth")

# Enable CORS for the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Email Analyzer API is running"}

@app.post("/email")
async def analyze_email(request: EmailRequest,userdata = Depends(get_current_user)):
    return get_email_from_gmail(request.email_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    print("Server is running")
    
