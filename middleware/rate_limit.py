import os
from flask import request, jsonify
from functools import wraps
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, max_requests=60, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_rate_limited(self, key: str) -> bool:
        with self.lock:
            current_time = time.time()
            # Remove old requests
            self.requests[key] = [req_time for req_time in self.requests[key]
                                if current_time - req_time < self.window_seconds]
            
            # Check if rate limit is exceeded
            if len(self.requests[key]) >= self.max_requests:
                return True
            
            # Add new request
            self.requests[key].append(current_time)
            return False

    def get_remaining_requests(self, key: str) -> int:
        with self.lock:
            current_time = time.time()
            valid_requests = [req_time for req_time in self.requests[key]
                            if current_time - req_time < self.window_seconds]
            return max(0, self.max_requests - len(valid_requests))

# Create global rate limiter instances
api_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 requests per minute
auth_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes for auth
kyc_limiter = RateLimiter(
    max_requests=int(os.environ.get('KYC_RATE_LIMIT_REQUESTS', 3)),
    window_seconds=int(os.environ.get('KYC_RATE_LIMIT_WINDOW', 300))
)   # 3 requests per 5 minutes for KYC

def rate_limit(limiter):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Use IP address as rate limit key
            key = request.remote_addr
            
            # Check rate limit
            if limiter.is_rate_limited(key):
                remaining_time = limiter.window_seconds
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Vui lòng thử lại sau {remaining_time} giây',
                    'remaining_requests': 0,
                    'retry_after': remaining_time
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response
            else:
                response_obj, status_code = response, 200
                
            if isinstance(response_obj, dict):
                response_obj = jsonify(response_obj)
                
            response_obj.headers['X-RateLimit-Limit'] = str(limiter.max_requests)
            response_obj.headers['X-RateLimit-Remaining'] = str(limiter.get_remaining_requests(key))
            response_obj.headers['X-RateLimit-Reset'] = str(int(time.time() + limiter.window_seconds))
            
            return response_obj, status_code
            
        return wrapped
    return decorator

# Decorator aliases for different rate limits
def auth_rate_limit():
    return rate_limit(auth_limiter)

def kyc_rate_limit():
    return rate_limit(kyc_limiter)

def api_rate_limit():
    return rate_limit(api_limiter)