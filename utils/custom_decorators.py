import functools
from utils.custom_errors import TokenError


def token_auto_refresh(on_token_error=None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                if result:
                    return result
            except TokenError:
                on_token_error()
                result = f(*args, **kwargs)
                return result
        return wrapper
    return decorator
