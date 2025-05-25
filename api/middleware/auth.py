from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from ..config import API_SECRET_KEY

security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    # Skip auth for docs
    if request.url.path.startswith(("/docs", "/redoc", "/openapi.json", "/health")):
        return await call_next(request)
        
    try:
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=403, detail="No authentication token provided")
            
        scheme, token = auth.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token or expired token")
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
        
    return await call_next(request)