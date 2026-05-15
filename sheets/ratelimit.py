import functools
from django.core.cache import cache
from django.shortcuts import render


def login_rate_limit(max_attempts=5, window_seconds=300, block_seconds=900):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method != 'POST':
                return view_func(request, *args, **kwargs)

            ip = _client_ip(request)
            attempt_key = f'login_attempts:{ip}'
            block_key = f'login_blocked:{ip}'

            if cache.get(block_key):
                return render(request, 'sheets/login.html', {
                    'rate_limit_error': '登录尝试次数过多，请15分钟后再试。',
                })

            response = view_func(request, *args, **kwargs)

            if response.status_code == 302:
                cache.delete(attempt_key)
            else:
                attempts = cache.get(attempt_key, 0) + 1
                if attempts >= max_attempts:
                    cache.set(block_key, True, block_seconds)
                    cache.delete(attempt_key)
                    return render(request, 'sheets/login.html', {
                        'rate_limit_error': '登录尝试次数过多，请15分钟后再试。',
                    })
                cache.set(attempt_key, attempts, window_seconds)

            return response

        return wrapper
    return decorator


def _client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')
