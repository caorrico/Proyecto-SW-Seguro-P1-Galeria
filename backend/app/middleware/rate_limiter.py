from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()

# Instancia global del limiter — se importa en main.py y en los routers
limiter = Limiter(key_func=get_remote_address)
