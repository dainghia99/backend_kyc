from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from utils.auth import create_session, invalidate_session, token_required
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email và mật khẩu là bắt buộc'}), 400
        
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Email không hợp lệ'}), 400
        
    # Validate password strength
    if len(password) < 8:
        return jsonify({'error': 'Mật khẩu phải có ít nhất 8 ký tự'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email đã được sử dụng'}), 400
        
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Tạo session mới cho user
        token = create_session(new_user)
        
        return jsonify({
            'message': 'Đăng ký thành công',
            'token': token,
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'kyc_status': new_user.kyc_status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email và mật khẩu là bắt buộc'}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401
        
    # Tạo session mới cho user
    token = create_session(user)
    
    return jsonify({
        'message': 'Đăng nhập thành công',
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'kyc_status': user.kyc_status
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    token = request.headers['Authorization'].split(' ')[1]
    invalidate_session(token)
    return jsonify({'message': 'Đăng xuất thành công'}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'kyc_status': current_user.kyc_status,
        'identity_verified': current_user.identity_verified
    }), 200
