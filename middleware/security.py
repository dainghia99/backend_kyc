from functools import wraps
from flask import request, abort
import os

def validate_file_extension(allowed_extensions):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'file' not in request.files:
                abort(400, description="No file provided")
                
            file = request.files['file']
            if not file.filename:
                abort(400, description="No file selected")
                
            if not ('.' in file.filename and \
                   file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                abort(400, description=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
                
            return f(*args, **kwargs)
        return wrapped
    return decorator

def validate_file_size(max_size_mb):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'file' not in request.files:
                abort(400, description="No file provided")
                
            file = request.files['file']
            # Check if the file size exceeds the maximum size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > max_size_mb * 1024 * 1024:
                abort(400, description=f"File size exceeds maximum limit of {max_size_mb}MB")
                
            return f(*args, **kwargs)
        return wrapped
    return decorator

def sanitize_file_name(filename):
    # Remove potentially dangerous characters
    return ''.join(c for c in filename if c.isalnum() or c in '._-')

def secure_file_response(filepath):
    """Safely serve files by validating path and checking for directory traversal"""
    if not os.path.exists(filepath):
        abort(404, description="File not found")
        
    # Prevent directory traversal
    abs_path = os.path.abspath(filepath)
    if not abs_path.startswith(os.path.abspath(os.getcwd())):
        abort(403, description="Access denied")
        
    return abs_path