from functools import wraps

from django.shortcuts import render


def render_to(tpl):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            out = func(request, *args, **kwargs) or {}
            if isinstance(out, dict):
                out = render(request, tpl, context=out)
            return out
        return wrapper
    return decorator
