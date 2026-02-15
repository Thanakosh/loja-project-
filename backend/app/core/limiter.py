from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

def get_real_remote_address(request: Request):
    """
    Custom key function that returns the remote address.
    If behind a proxy, you might need to check X-Forwarded-For headers.
    """
    return get_remote_address(request)

limiter = Limiter(key_func=get_real_remote_address)
