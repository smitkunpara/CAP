from fastapi import APIRouter, HTTPException, Depends
from config import settings
from jose import jwt
import requests
from typing import Dict
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import db
import datetime

    
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        if db.is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="User is logged out")
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM)
        return payload
    except Exception as e:
        print(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

router = APIRouter()

@router.get("/logout")
async def logout(token:HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = token.credentials
        jwt.decode(token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM)
        if db.is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="User is already logged out")
        db.add_blacklisted_token(token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        print(f"Error logging out: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate")
async def validate_token(user: str = Depends(get_current_user)) -> Dict:
    return {
        "status": "success",
        "valid": True,
        "message": "Token is valid"
    }

@router.post("/google")
async def google_auth(request: dict) -> Dict:
    try:
        token = request.get('token')
        print("token:", token)
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
            
        # Get user info and refresh token
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code != 200:
            raise ValueError("Invalid token")
            
        user_info = response.json()
        
        db.add_user({
            "name":user_info.get('name', ''),
            "email":user_info['email'],
            "sub":user_info['sub'],
            "access_token":token,
            "created_at":datetime.datetime.now()
        })
        
        app_token = jwt.encode(
            {
                "email": user_info['email'],
                "name": user_info.get('name', ''),
                "exp": datetime.datetime.now() + datetime.timedelta(minutes=settings.JWT_EXP_MINUTES)
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return {
            "status": "success",
            "token": app_token,
            "user": {
                "email": user_info['email'],
                "name": user_info.get('name', '')
            }
        }
        
    except ValueError as e:
        print(f"Google token validation error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
