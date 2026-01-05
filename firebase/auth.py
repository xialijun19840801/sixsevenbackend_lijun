from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import Optional

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify Firebase ID token and return user_id
    """
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )

async def get_current_user_id(user_id: str = Depends(verify_token)) -> str:
    """
    Dependency to get current authenticated user ID
    """
    return user_id

async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional authentication dependency - returns user_id if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
        return user_id if user_id else None
    except Exception:
        # If token is invalid, just return None (optional auth)
        return None

