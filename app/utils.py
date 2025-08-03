from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
SECRET_KEY = "🧄jwt_super_secret🧄"
ALGORITHM = "HS256"
ACCESS_EXPIRE_MIN = 60 * 24  # یک روز

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_ctx.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_ctx.verify(password, hashed)

def create_access_token(data: dict, expires_delta: int = ACCESS_EXPIRE_MIN):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None