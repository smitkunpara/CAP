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
        code = request.get("code")
        redirect_uri = request.get("redirect_uri")  # Get redirect URI from request
        if not code or not redirect_uri:
            raise HTTPException(status_code=400, detail="Code and redirect_uri are required")
            
        print("Received code:", code)
        print("Received redirect_uri:", redirect_uri)
        
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }
        )
        
        if token_response.status_code != 200:
            print("Token exchange failed. Response:", token_response.text)
            raise HTTPException(status_code=400, detail=f"Failed to exchange authorization code: {token_response.text}")
            
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        # Get user info using the access token
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve user info")

        user_info = userinfo_response.json()
        if db.get_user(user_info["email"]):
            user_id=db.update_user_token(user_info["email"],access_token,refresh_token)
        else:
            user_id= db.add_user({
                "name": user_info.get("name", ""),
                "email": user_info["email"],    
                "sub": user_info["sub"],
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": datetime.datetime.now(),
            })

        # Convert ObjectId to string for JSON serialization
        user_id = str(user_id)

        # Generate app-specific JWT token for the user
        app_token = jwt.encode(
            {
                "email": user_info["email"],
                "name": user_info.get("name", ""),
                "user_id": user_id,
                "exp": datetime.datetime.now() + datetime.timedelta(minutes=60),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        return {
            "jwt_token": app_token
        }

    except Exception as e:
        print(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/web/google")
async def website_google_auth(request: dict) -> Dict:
    """
    Handle Google authentication specifically for the website.
    This API is separate from the extension authentication flow.
    """
    try:
        code = request.get("code")
        redirect_uri = request.get("redirect_uri")
        
        if not code or not redirect_uri:
            raise HTTPException(status_code=400, detail="Code and redirect_uri are required")
            
        print("Website Auth - Received code:", code)
        print("Website Auth - Received redirect_uri:", redirect_uri)
        
        # Exchange authorization code for tokens
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.WEBSITE_GOOGLE_CLIENT_ID,
                'client_secret': settings.WEBSITE_GOOGLE_CLIENT_SECRET,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }
        )
        
        if token_response.status_code != 200:
            print("Website Auth - Token exchange failed. Response:", token_response.text)
            raise HTTPException(status_code=400, detail=f"Failed to exchange authorization code: {token_response.text}")
            
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        # Get user info using the access token
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve user info")

        user_info = userinfo_response.json()
        
        # Check if user exists and update tokens or create new user
        if db.get_user(user_info["email"]):
            user_id = db.update_user_token(user_info["email"], access_token, refresh_token)
        else:
            user_id = db.add_user({
                "name": user_info.get("name", ""),
                "email": user_info["email"],    
                "sub": user_info["sub"],
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": datetime.datetime.now(),
                "auth_source": "website"  # Mark this user as authenticated via website
            })

        # Convert ObjectId to string for JSON serialization
        user_id = str(user_id)

        # Generate website-specific JWT token for the user
        app_token = jwt.encode(
            {
                "email": user_info["email"],
                "name": user_info.get("name", ""),
                "user_id": user_id,
                "auth_source": "website",
                "exp": datetime.datetime.now() + datetime.timedelta(days=7),  # Longer expiration for website users
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        return {
            "jwt_token": app_token,
            "user": {
                "email": user_info["email"],
                "name": user_info.get("name", ""),
            }
        }

    except Exception as e:
        print(f"Unexpected error during website authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))