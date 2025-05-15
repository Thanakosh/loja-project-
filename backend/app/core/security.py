from datetime import datetime, timedelta
from jose import jwt
SECRET = 'changeme'
def create_token(data: dict, minutes: int = 60):
    to_encode = data.copy()
    to_encode['exp'] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(to_encode, SECRET, algorithm='HS256')
