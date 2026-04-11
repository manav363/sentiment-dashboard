from slowapi import Limiter
from slowapi.util import get_remote_address

SENTIMENT_LIMIT = "30/minute"
EXTERNAL_LIMIT = "10/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[])
