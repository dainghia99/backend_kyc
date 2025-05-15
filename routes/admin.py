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
        search = request.args.get('search', '')

        # Quyết định cách truy vấn dựa trên trạng thái
        if status == 'all' or not status:
            # Nếu lọc "all" hoặc không có trạng thái, truy vấn từ bảng User để lấy tất cả người dùng
            query = User.query.filter(User.role != 'superadmin')  # Loại trừ tài khoản superadmin
        elif status == 'pending' or status == 'verified':
            # Nếu lọc theo trạng thái cụ thể, truy vấn từ bảng User
            query = User.query.filter_by(kyc_status=status)
        else:
            # Không có trường hợp khác, tất cả đã được xử lý ở trên
            return jsonify({
                'error': 'Trạng thái không hợp lệ'
            }), 400

        # Tìm kiếm theo email hoặc tên
        if search:
            # Tìm kiếm theo email
            email_users = query.filter(User.email.ilike(f'%{search}%')).all()
            email_user_ids = [user.id for user in email_users]

            # Tìm kiếm theo tên trong bảng IdentityInfo
            identity_info_users = IdentityInfo.query.filter(IdentityInfo.full_name.ilike(f'%{search}%')).all()
            name_user_ids = [info.user_id for info in identity_info_users]

            # Kết hợp các ID
            all_user_ids = list(set(email_user_ids + name_user_ids))

            if all_user_ids:
                query = User.query.filter(User.id.in_(all_user_ids))
                if status == 'rejected' or status == 'pending' or status == 'verified':
                    query = query.filter(User.kyc_status == status)
                elif status == 'all' or not status:
                    query = query.filter(User.role != 'superadmin')
            else:
                # Nếu không tìm thấy kết quả, trả về danh sách trống
                return jsonify({
                    'requests': [],
                    'total': 0,
                    'pages': 0,
                    'current_page': page
                }), 200

        # Phân trang
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items

        # Chuẩn bị dữ liệu phản hồi
        request_list = []
        for user in users:
            identity_info = IdentityInfo.query.filter_by(user_id=user.id).first()
            kyc = KYCVerification.query.filter_by(user_id=user.id).first()

            full_name = identity_info.full_name if identity_info else "Chưa có thông tin"

            # Lấy thông tin từ bảng KYCVerification nếu có
            id_card_front_url = None
            id_card_back_url = None
            selfie_url = None
            rejection_reason = None
            created_at = user.created_at
            verified_at = user.kyc_verified_at
            liveness_score = None
            blink_count = None
            face_match = None
            face_distance = None
            attempt_count = 0
            last_attempt_at = None

            if kyc:
                # Đảm bảo đường dẫn ảnh được tạo đúng cách
                id_card_front_url = f"/uploads/{kyc.identity_card_front}" if kyc.identity_card_front else None
                id_card_back_url = f"/uploads/{kyc.identity_card_back}" if kyc.identity_card_back else None

                # Xử lý đường dẫn ảnh selfie
                if kyc.selfie_path:
                    # Kiểm tra xem đường dẫn đã có tiền tố /uploads/ chưa
                    if kyc.selfie_path.startswith('/uploads/'):
                        selfie_url = kyc.selfie_path
                    else:
                        selfie_url = f"/uploads/{kyc.selfie_path}"
                else:
                    selfie_url = None
                rejection_reason = kyc.rejection_reason
                created_at = kyc.created_at or user.created_at
                verified_at = kyc.verified_at or user.kyc_verified_at
                liveness_score = kyc.liveness_score
                blink_count = kyc.blink_count
                face_match = kyc.face_match
                face_distance = kyc.face_distance
                attempt_count = kyc.attempt_count or 0
                last_attempt_at = kyc.last_attempt_at

            request_data = {
                'id': kyc.id if kyc else f"user_{user.id}",
                'user_id': user.id,
                'email': user.email,
                'full_name': full_name,
                'status': user.kyc_status,
                'submitted_at': created_at.isoformat() if created_at else None,
                'created_at': created_at.isoformat() if created_at else None,
                'verified_at': verified_at.isoformat() if verified_at else None,
                'liveness_score': liveness_score,
                'blink_count': blink_count,
                'face_match': face_match,
                'face_distance': face_distance,
                'attempt_count': attempt_count,
                'last_attempt_at': last_attempt_at.isoformat() if last_attempt_at else None,
                'rejection_reason': rejection_reason,
                'id_card_front': id_card_front_url,
                'id_card_back': id_card_back_url,
                'selfie_path': selfie_url
            }
            request_list.append(request_data)

        return jsonify({
            'requests': request_list,
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
            # Đảm bảo thông tin từ chối được lưu vào cả bảng User và KYCVerification
            current_app.logger.info(f"Từ chối KYC cho user {user.email} với lý do: {reason}")

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

@admin_bp.route('/kyc-requests/<int:kyc_id>/manual-verify', methods=['POST'])
@admin_required
def manual_verify_kyc(current_user, kyc_id):
    """
    Xác minh thủ công yêu cầu KYC (bỏ qua kiểm tra tự động)
    """
    try:
        kyc = KYCVerification.query.get(kyc_id)

        if not kyc:
            return jsonify({'error': 'Không tìm thấy yêu cầu KYC'}), 404

        # Cập nhật trạng thái KYC
        kyc.status = 'verified'
        kyc.verified_at = datetime.utcnow()
        kyc.liveness_score = 1.0  # Đặt điểm số liveness cao nhất
        kyc.blink_count = 3  # Đặt số lần nháy mắt đạt yêu cầu
        kyc.face_match = True  # Đánh dấu khuôn mặt khớp
        kyc.id_card_verified = True  # Đánh dấu CCCD đã xác minh

        # Cập nhật trạng thái người dùng
        user = User.query.get(kyc.user_id)
        if user:
            user.kyc_status = 'verified'
            user.kyc_verified_at = datetime.utcnow()
            user.identity_verified = True

        db.session.commit()

        return jsonify({
            'message': 'Xác minh thủ công KYC thành công',
            'kyc_id': kyc.id,
            'user_id': kyc.user_id,
            'status': kyc.status,
            'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error manually verifying KYC: {str(e)}")
        return jsonify({'error': 'Không thể xác minh thủ công yêu cầu KYC'}), 500

@admin_bp.route('/kyc-requests/<int:kyc_id>', methods=['GET'])
@admin_required
def get_kyc_request_details(current_user, kyc_id):
    """
    Lấy thông tin chi tiết của một yêu cầu KYC
    """
    try:
        kyc = KYCVerification.query.get(kyc_id)

        if not kyc:
            return jsonify({'error': 'Không tìm thấy yêu cầu KYC'}), 404

        user = User.query.get(kyc.user_id)
        identity_info = IdentityInfo.query.filter_by(user_id=kyc.user_id).first()

        # Chuẩn bị thông tin danh tính
        identity_data = None
        if identity_info:
            identity_data = {
                'id_number': identity_info.id_number,
                'full_name': identity_info.full_name,
                'date_of_birth': identity_info.date_of_birth.strftime('%d/%m/%Y') if identity_info.date_of_birth else None,
                'gender': identity_info.gender,
                'nationality': identity_info.nationality,
                'issue_date': identity_info.issue_date.strftime('%d/%m/%Y') if identity_info.issue_date else None,
                'expiry_date': identity_info.expiry_date.strftime('%d/%m/%Y') if identity_info.expiry_date else None
            }

        # Chuẩn bị đường dẫn ảnh
        id_card_front_url = f"/uploads/{kyc.identity_card_front}" if kyc.identity_card_front else None
        id_card_back_url = f"/uploads/{kyc.identity_card_back}" if kyc.identity_card_back else None

        # Xử lý đường dẫn ảnh selfie
        if kyc.selfie_path:
            # Kiểm tra xem đường dẫn đã có tiền tố /uploads/ chưa
            if kyc.selfie_path.startswith('/uploads/'):
                selfie_url = kyc.selfie_path
            else:
                selfie_url = f"/uploads/{kyc.selfie_path}"
        else:
            selfie_url = None

        kyc_data = {
            'id': kyc.id,
            'user_id': kyc.user_id,
            'email': user.email if user else None,
            'full_name': identity_data.get('full_name') if identity_data else "Chưa có thông tin",
            'status': kyc.status,
            'submitted_at': kyc.created_at.isoformat() if kyc.created_at else None,
            'created_at': kyc.created_at.isoformat() if kyc.created_at else None,
            'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None,
            'liveness_score': kyc.liveness_score,
            'blink_count': kyc.blink_count,
            'face_match': kyc.face_match,
            'face_distance': kyc.face_distance,
            'attempt_count': kyc.attempt_count,
            'last_attempt_at': kyc.last_attempt_at.isoformat() if kyc.last_attempt_at else None,
            'rejection_reason': kyc.rejection_reason,
            'id_card_front': id_card_front_url,
            'id_card_back': id_card_back_url,
            'selfie_path': selfie_url,
            'selfie': selfie_url,  # Thêm trường này để tương thích với cả hai cách gọi
            'identity_info': identity_data
        }

        return jsonify(kyc_data), 200

    except Exception as e:
        current_app.logger.error(f"Error getting KYC request details: {str(e)}")
        return jsonify({'error': 'Không thể lấy thông tin chi tiết yêu cầu KYC'}), 500



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
            'totalUsers': total_users,
            'verifiedUsers': verified_users,
            'pendingUsers': pending_users,
            'rejectedUsers': rejected_users,
            'verificationRate': f"{verification_rate}%",  # Thêm dấu % để phù hợp với frontend
            'monthly_stats': monthly_stats
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'error': 'Không thể lấy thống kê'}), 500
