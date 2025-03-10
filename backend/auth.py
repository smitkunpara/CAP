from fastapi import APIRouter, HTTPException, Depends
from config import settings
from jose import jwt
import requests
from typing import Dict
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

router = APIRouter()

@router.get("/validate")
async def validate_token(token: str = Depends(get_current_user)) -> Dict:
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
        
        # Get refresh token from Chrome identity API
        refresh_token = request.get('refresh_token')
        
        # Store tokens in your database (for now we'll just return them)
        # In production, you should store these securely in your database
        tokens = {
            "access_token": token,
            "refresh_token": refresh_token,
            "expires_in": 3600  # Google OAuth tokens typically expire in 1 hour
        }
        
        app_token = jwt.encode(
            {
                "email": user_info['email'],
                "name": user_info.get('name', ''),
                "sub": user_info['sub'],
                "tokens": tokens  # Include tokens in JWT
            },
            settings.JWT_SECRET,
            algorithm="HS256"
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

@router.post("/refresh")
async def refresh_token(request: dict) -> Dict:
    try:
        refresh_token = request.get('refresh_token')
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
            
        # Request new access token from Google
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code != 200:
            raise ValueError("Failed to refresh token")
            
        token_data = response.json()
        
        return {
            "status": "success",
            "access_token": token_data['access_token'],
            "expires_in": token_data['expires_in']
        }
        
    except Exception as e:
        print(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
