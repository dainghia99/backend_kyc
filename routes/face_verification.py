from flask import Blueprint, request, jsonify, current_app
from models import db, KYCVerification, User
from utils.auth import token_required
from utils.face_verification_deepface import verify_face_match
from middleware.rate_limit import kyc_rate_limit
from middleware.security import is_valid_file_extension, is_valid_file_size, sanitize_file_name
from datetime import datetime
import os

face_verification_bp = Blueprint('face_verification', __name__)

@face_verification_bp.route('/verify', methods=['POST'])
@token_required
@kyc_rate_limit()
def verify_face(current_user):
    """
    Endpoint để xác minh xem khuôn mặt trong ảnh selfie có khớp với khuôn mặt trong CCCD không
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Không tìm thấy file ảnh'}), 400

    selfie_file = request.files['image']
    if not selfie_file.filename:
        return jsonify({'error': 'Không có file nào được chọn'}), 400

    # Kiểm tra định dạng file
    if not is_valid_file_extension(selfie_file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
        return jsonify({'error': 'Định dạng file không được hỗ trợ. Vui lòng sử dụng định dạng JPG, JPEG hoặc PNG'}), 400

    if not is_valid_file_size(selfie_file, current_app.config['MAX_CONTENT_LENGTH']):
        max_size_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        return jsonify({'error': f'Kích thước file quá lớn. Kích thước tối đa cho phép là {max_size_mb}MB'}), 400

    try:
        # Lấy bản ghi xác minh KYC
        verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
        if not verification:
            return jsonify({'error': 'Vui lòng tải lên CCCD trước khi xác minh khuôn mặt'}), 400

        # Kiểm tra xem đã tải lên mặt trước CCCD chưa
        if not verification.identity_card_front:
            return jsonify({'error': 'Vui lòng tải lên mặt trước CCCD trước khi xác minh khuôn mặt'}), 400

        # Lưu ảnh selfie
        filename = f'selfie_{current_user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        filename = sanitize_file_name(filename)
        selfie_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Đảm bảo thư mục tải lên tồn tại
        os.makedirs(os.path.dirname(selfie_path), exist_ok=True)

        selfie_file.save(selfie_path)
        current_app.logger.info(f"Đã lưu ảnh selfie tại: {selfie_path}")

        # Lấy đường dẫn đến ảnh mặt trước CCCD
        id_card_path = os.path.join(current_app.config['UPLOAD_FOLDER'], verification.identity_card_front)
        current_app.logger.info(f"Đường dẫn ảnh CCCD: {id_card_path}")

        # Sử dụng DeepFace để xác minh khuôn mặt
        current_app.logger.info("Sử dụng DeepFace để xác minh khuôn mặt")
        result = verify_face_match(id_card_path, selfie_path)

        # Cập nhật bản ghi xác minh - Chỉ lưu tên file thay vì đường dẫn đầy đủ
        verification.selfie_path = filename
        
        is_verified = result.get('verified', False) # Get verified status
        verification.face_match = is_verified # Assign boolean result
        verification.face_distance = result.get('distance', None)
        verification.face_verified_at = datetime.now()

        current_app.logger.debug(f"Updating verification record: selfie_path={verification.selfie_path}, face_match={verification.face_match}, face_distance={verification.face_distance}, face_verified_at={verification.face_verified_at}")

        if not is_verified:
            verification.status = 'failed'
            verification.rejection_reason = 'Xác minh không thành công: khuôn mặt không khớp với CCCD'
        # else: # No need for an else block if no specific action is needed for success beyond assignment and response
            # Removed problematic log here

        db.session.commit()

        # Chuẩn bị phản hồi - đảm bảo tất cả các giá trị boolean được chuyển đổi sang kiểu boolean Python gốc
        response = {
            'success': bool(is_verified),
            'match': bool(is_verified),
            'message': result.get('message', 'Xác minh hoàn tất'), # Use message from deepface or default
            'selfie_path': os.path.basename(selfie_path)
        }

        # Thêm thông tin debug nếu có
        # if 'debug_info' in result: # Keep if needed, but simplified for now
        #     response['debug_info'] = result['debug_info']

        # Mã trạng thái dựa trên kết quả
        status_code = 200 # Always return 200 OK, result is in JSON body

        # Thêm thông báo rõ ràng cho người dùng trong trường hợp thất bại
        if not is_verified:
            response['error'] = result.get('message', 'Xác minh không thành công: khuôn mặt trong ảnh selfie không khớp với khuôn mặt trong CCCD. Vui lòng thử lại với ảnh rõ nét hơn hoặc đảm bảo bạn đang sử dụng CCCD của chính mình.') # Use deepface message or default

        return jsonify(response), status_code

    except Exception as e:
        current_app.logger.error(f"Lỗi xác minh khuôn mặt: {str(e)}")

        # Nếu xảy ra lỗi, xóa ảnh selfie nếu tồn tại
        if 'selfie_path' in locals() and os.path.exists(selfie_path):
            os.remove(selfie_path)

        return jsonify({'error': 'Có lỗi xảy ra khi xác minh khuôn mặt. Vui lòng thử lại với ảnh rõ nét hơn và đảm bảo ánh sáng tốt.'}), 500

@face_verification_bp.route('/status', methods=['GET'])
@token_required
def get_face_verification_status(current_user):
    """
    Endpoint para obtener el estado de la verificación facial
    """
    verification = KYCVerification.query.filter_by(user_id=current_user.id).first()

    if not verification:
        return jsonify({
            'face_verified': False,
            'face_match': False,
            'selfie_uploaded': False
        }), 200

    
    return jsonify({
        'face_verified': bool(verification.face_verified_at is not None),
        'face_match': bool(verification.face_match) if verification.face_match is not None else False,
        'selfie_uploaded': bool(verification.selfie_path is not None),
        'verified_at': verification.face_verified_at.isoformat() if verification.face_verified_at else None
    }), 200
