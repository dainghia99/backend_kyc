from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timezone
from models import db, User, UserSession

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token không hợp lệ'}), 401
                
        if not token:
            return jsonify({'error': 'Token không tồn tại'}), 401
            
        try:
            # Kiểm tra token trong database
            session = UserSession.query.filter_by(token=token, is_active=True).first()
            if not session:
                return jsonify({'error': 'Session không hợp lệ'}), 401
                
            if session.expires_at < datetime.now(timezone.utc):
                session.is_active = False
                db.session.commit()
                return jsonify({'error': 'Session đã hết hạn'}), 401
                
            # Giải mã token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User không tồn tại'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token đã hết hạn'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token không hợp lệ'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

def create_session(user):
    # Tạo JWT token
    expires_at = datetime.now(timezone.utc) + current_app.config['SESSION_LIFETIME']
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': expires_at
        },
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )
    
    # Tạo session mới trong database
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    
    db.session.add(session)
    db.session.commit()
    
    return token

def invalidate_session(token):
    session = UserSession.query.filter_by(token=token).first()
    if session:
        session.is_active = False
        db.session.commit()
        
def invalidate_all_sessions(user_id):
    UserSession.query.filter_by(user_id=user_id).update({'is_active': False})
    db.session.commit()
