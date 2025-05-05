from flask import Blueprint, jsonify, current_app
from models import db, User, KYCVerification, IdentityInfo
from utils.auth import token_required
from datetime import datetime

verified_accounts_bp = Blueprint('verified_accounts', __name__)

@verified_accounts_bp.route('/verified-accounts', methods=['GET'])
@token_required
def get_verified_accounts(current_user):
    """
    Endpoint để lấy danh sách tài khoản đã xác minh KYC
    """
    try:
        # Chỉ admin mới có thể xem danh sách tài khoản đã xác minh
        # Tạm thời cho phép tất cả người dùng xem để demo
        # if current_user.role != 'admin':
        #     return jsonify({'error': 'Không có quyền truy cập'}), 403
        
        # Lấy danh sách người dùng đã xác minh KYC
        verified_users = User.query.filter_by(kyc_status='verified').all()
        
        accounts = []
        for user in verified_users:
            # Lấy thông tin KYC verification
            verification = KYCVerification.query.filter_by(user_id=user.id).first()
            
            # Lấy thông tin danh tính
            identity_info = IdentityInfo.query.filter_by(user_id=user.id).first()
            
            if verification and identity_info:
                accounts.append({
                    'id': user.id,
                    'email': user.email,
                    'full_name': identity_info.full_name,
                    'verified_at': verification.verified_at.isoformat() if verification.verified_at else None,
                    'status': user.kyc_status
                })
        
        return jsonify({
            'accounts': accounts,
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting verified accounts: {str(e)}")
        return jsonify({'error': 'Không thể lấy danh sách tài khoản đã xác minh'}), 500
