from flask import Blueprint, jsonify, request, current_app
from models import db, User, KYCVerification, IdentityInfo
from utils.auth import token_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """
    Decorator để kiểm tra quyền admin
    """
    @token_required
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Không có quyền truy cập'}), 403
        return f(current_user, *args, **kwargs)
    
    # Giữ tên hàm gốc
    decorated_function.__name__ = f.__name__
    return decorated_function

def superadmin_required(f):
    """
    Decorator để kiểm tra quyền superadmin
    """
    @token_required
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role != 'superadmin':
            return jsonify({'error': 'Không có quyền truy cập'}), 403
        return f(current_user, *args, **kwargs)
    
    # Giữ tên hàm gốc
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/check-admin', methods=['GET'])
@token_required
def check_admin(current_user):
    """
    Kiểm tra xem người dùng hiện tại có quyền admin không
    """
    is_admin = current_user.role in ['admin', 'superadmin']
    is_superadmin = current_user.role == 'superadmin'
    
    return jsonify({
        'is_admin': is_admin,
        'is_superadmin': is_superadmin,
        'role': current_user.role,
        'email': current_user.email
    }), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """
    Lấy danh sách người dùng (chỉ admin mới có quyền)
    """
    try:
        # Lấy tham số query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        # Query với phân trang và tìm kiếm
        query = User.query
        
        if search:
            # Tìm kiếm theo email
            query = query.filter(User.email.like(f'%{search}%'))
        
        # Phân trang
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # Chuẩn bị dữ liệu phản hồi
        user_list = []
        for user in users:
            identity_info = None
            if user.identity_info:
                identity_info = {
                    'full_name': user.identity_info.full_name,
                    'id_number': user.identity_info.id_number,
                    'date_of_birth': user.identity_info.date_of_birth.strftime('%d/%m/%Y') if user.identity_info.date_of_birth else None,
                    'gender': user.identity_info.gender,
                    'nationality': user.identity_info.nationality
                }
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'kyc_status': user.kyc_status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'kyc_verified_at': user.kyc_verified_at.isoformat() if user.kyc_verified_at else None,
                'identity_info': identity_info
            }
            user_list.append(user_data)
        
        return jsonify({
            'users': user_list,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({'error': 'Không thể lấy danh sách người dùng'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(current_user, user_id):
    """
    Lấy thông tin chi tiết của một người dùng
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Không tìm thấy người dùng'}), 404
        
        # Lấy thông tin KYC
        kyc = KYCVerification.query.filter_by(user_id=user.id).first()
        
        # Lấy thông tin danh tính
        identity_info = None
        if user.identity_info:
            identity_info = {
                'full_name': user.identity_info.full_name,
                'id_number': user.identity_info.id_number,
                'date_of_birth': user.identity_info.date_of_birth.strftime('%d/%m/%Y') if user.identity_info.date_of_birth else None,
                'gender': user.identity_info.gender,
                'nationality': user.identity_info.nationality,
                'issue_date': user.identity_info.issue_date.strftime('%d/%m/%Y') if user.identity_info.issue_date else None,
                'expiry_date': user.identity_info.expiry_date.strftime('%d/%m/%Y') if user.identity_info.expiry_date else None
            }
        
        # Chuẩn bị dữ liệu KYC
        kyc_data = None
        if kyc:
            kyc_data = {
                'id': kyc.id,
                'status': kyc.status,
                'created_at': kyc.created_at.isoformat() if kyc.created_at else None,
                'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None,
                'liveness_score': kyc.liveness_score,
                'blink_count': kyc.blink_count,
                'face_match': kyc.face_match,
                'face_distance': kyc.face_distance,
                'attempt_count': kyc.attempt_count,
                'last_attempt_at': kyc.last_attempt_at.isoformat() if kyc.last_attempt_at else None,
                'rejection_reason': kyc.rejection_reason
            }
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'kyc_status': user.kyc_status,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'kyc_verified_at': user.kyc_verified_at.isoformat() if user.kyc_verified_at else None,
            'identity_info': identity_info,
            'kyc_verification': kyc_data
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user details: {str(e)}")
        return jsonify({'error': 'Không thể lấy thông tin người dùng'}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@superadmin_required
def update_user_role(current_user, user_id):
    """
    Cập nhật vai trò của người dùng (chỉ superadmin mới có quyền)
    """
    try:
        data = request.get_json()
        
        if not data or 'role' not in data:
            return jsonify({'error': 'Thiếu thông tin vai trò'}), 400
        
        role = data['role']
        
        # Kiểm tra vai trò hợp lệ
        if role not in ['user', 'admin', 'superadmin']:
            return jsonify({'error': 'Vai trò không hợp lệ'}), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Không tìm thấy người dùng'}), 404
        
        # Không thể thay đổi vai trò của chính mình
        if user.id == current_user.id:
            return jsonify({'error': 'Không thể thay đổi vai trò của chính mình'}), 400
        
        user.role = role
        db.session.commit()
        
        return jsonify({
            'message': 'Cập nhật vai trò thành công',
            'user_id': user.id,
            'email': user.email,
            'role': user.role
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user role: {str(e)}")
        return jsonify({'error': 'Không thể cập nhật vai trò người dùng'}), 500

@admin_bp.route('/kyc-requests', methods=['GET'])
@admin_required
def get_kyc_requests(current_user):
    """
    Lấy danh sách yêu cầu KYC
    """
    try:
        # Lấy tham số query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        
        # Query với phân trang và lọc theo trạng thái
        query = KYCVerification.query.join(User)
        
        if status and status != 'all':
            query = query.filter(KYCVerification.status == status)
        
        # Phân trang
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        kyc_requests = pagination.items
        
        # Chuẩn bị dữ liệu phản hồi
        request_list = []
        for kyc in kyc_requests:
            user = User.query.get(kyc.user_id)
            identity_info = IdentityInfo.query.filter_by(user_id=kyc.user_id).first()
            
            full_name = identity_info.full_name if identity_info else "Chưa có thông tin"
            
            request_data = {
                'id': kyc.id,
                'user_id': kyc.user_id,
                'email': user.email if user else None,
                'full_name': full_name,
                'status': kyc.status,
                'created_at': kyc.created_at.isoformat() if kyc.created_at else None,
                'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None,
                'liveness_score': kyc.liveness_score,
                'blink_count': kyc.blink_count,
                'face_match': kyc.face_match,
                'face_distance': kyc.face_distance,
                'attempt_count': kyc.attempt_count,
                'last_attempt_at': kyc.last_attempt_at.isoformat() if kyc.last_attempt_at else None,
                'rejection_reason': kyc.rejection_reason
            }
            request_list.append(request_data)
        
        return jsonify({
            'kyc_requests': request_list,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting KYC requests: {str(e)}")
        return jsonify({'error': 'Không thể lấy danh sách yêu cầu KYC'}), 500

@admin_bp.route('/kyc-requests/<int:kyc_id>/approve', methods=['POST'])
@admin_required
def approve_kyc(current_user, kyc_id):
    """
    Phê duyệt yêu cầu KYC
    """
    try:
        kyc = KYCVerification.query.get(kyc_id)
        
        if not kyc:
            return jsonify({'error': 'Không tìm thấy yêu cầu KYC'}), 404
        
        # Cập nhật trạng thái KYC
        kyc.status = 'verified'
        kyc.verified_at = datetime.utcnow()
        
        # Cập nhật trạng thái người dùng
        user = User.query.get(kyc.user_id)
        if user:
            user.kyc_status = 'verified'
            user.kyc_verified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Phê duyệt KYC thành công',
            'kyc_id': kyc.id,
            'user_id': kyc.user_id,
            'status': kyc.status,
            'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving KYC: {str(e)}")
        return jsonify({'error': 'Không thể phê duyệt yêu cầu KYC'}), 500

@admin_bp.route('/kyc-requests/<int:kyc_id>/reject', methods=['POST'])
@admin_required
def reject_kyc(current_user, kyc_id):
    """
    Từ chối yêu cầu KYC
    """
    try:
        data = request.get_json()
        
        if not data or 'reason' not in data:
            return jsonify({'error': 'Thiếu lý do từ chối'}), 400
        
        reason = data['reason']
        
        kyc = KYCVerification.query.get(kyc_id)
        
        if not kyc:
            return jsonify({'error': 'Không tìm thấy yêu cầu KYC'}), 404
        
        # Cập nhật trạng thái KYC
        kyc.status = 'rejected'
        kyc.rejection_reason = reason
        
        # Cập nhật trạng thái người dùng
        user = User.query.get(kyc.user_id)
        if user:
            user.kyc_status = 'rejected'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Từ chối KYC thành công',
            'kyc_id': kyc.id,
            'user_id': kyc.user_id,
            'status': kyc.status,
            'rejection_reason': kyc.rejection_reason
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting KYC: {str(e)}")
        return jsonify({'error': 'Không thể từ chối yêu cầu KYC'}), 500

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics(current_user):
    """
    Lấy thống kê về KYC
    """
    try:
        # Tổng số người dùng
        total_users = User.query.count()
        
        # Số người dùng đã xác minh
        verified_users = User.query.filter_by(kyc_status='verified').count()
        
        # Số người dùng đang chờ xác minh
        pending_users = User.query.filter_by(kyc_status='pending').count()
        
        # Số người dùng bị từ chối
        rejected_users = User.query.filter_by(kyc_status='rejected').count()
        
        # Tỷ lệ xác minh
        verification_rate = round((verified_users / total_users) * 100) if total_users > 0 else 0
        
        # Thống kê theo tháng (6 tháng gần nhất)
        monthly_stats = []
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        for i in range(6):
            month = current_month - i
            year = current_year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Đếm số lượng người dùng xác minh trong tháng
            verified_in_month = User.query.filter(
                User.kyc_status == 'verified',
                db.extract('month', User.kyc_verified_at) == month,
                db.extract('year', User.kyc_verified_at) == year
            ).count()
            
            # Đếm số lượng người dùng đăng ký trong tháng
            registered_in_month = User.query.filter(
                db.extract('month', User.created_at) == month,
                db.extract('year', User.created_at) == year
            ).count()
            
            monthly_stats.append({
                'month': f"{month:02d}/{year}",
                'verified': verified_in_month,
                'registered': registered_in_month
            })
        
        # Đảo ngược để hiển thị từ tháng cũ đến tháng mới
        monthly_stats.reverse()
        
        return jsonify({
            'total_users': total_users,
            'verified_users': verified_users,
            'pending_users': pending_users,
            'rejected_users': rejected_users,
            'verification_rate': verification_rate,
            'monthly_stats': monthly_stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'error': 'Không thể lấy thống kê'}), 500
