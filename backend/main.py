from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from auth import router as auth_router , get_current_user
from models import EmailRequest

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
    try:
        return {
            "status": "success",
            "message": "Email analyzed successfully",
            "user": userdata["email"],
            "analysis": {
                "url": request.email_link,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    print("Server is running")
    
