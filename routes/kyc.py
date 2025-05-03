from flask import Blueprint, request, jsonify, current_app
from models import db, KYCVerification, User, IdentityInfo
from utils.auth import token_required
from utils.liveness import process_video_for_liveness
# Thay thế Tesseract OCR bằng EasyOCR
from utils.easyocr_utils import process_id_card
from middleware.rate_limit import kyc_rate_limit
from middleware.security import is_valid_file_extension, is_valid_file_size, sanitize_file_name
from datetime import datetime
import os

kyc_bp = Blueprint('kyc', __name__)

@kyc_bp.route('/verify/liveness', methods=['POST'])
@token_required
@kyc_rate_limit()
def verify_liveness(current_user):
    if 'video' not in request.files:
        return jsonify({'error': 'Không tìm thấy file video'}), 400

    video_file = request.files['video']
    if not video_file.filename:
        return jsonify({'error': 'Không có file nào được chọn'}), 400

    # Validate file
    if not video_file.filename.lower().endswith(('.mp4', '.mov')):
        return jsonify({'error': 'Chỉ chấp nhận file MP4 hoặc MOV'}), 400

    # Check file size (16MB limit)
    max_file_size = current_app.config['MAX_VIDEO_FILE_SIZE']
    if len(video_file.read()) > max_file_size:
        return jsonify({'error': f'File không được vượt quá {max_file_size / (1024 * 1024)}MB'}), 400
    video_file.seek(0)

    try:
        # Get or create verification record
        verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
        if not verification:
            verification = KYCVerification(user_id=current_user.id)

        # Check attempt limits
        if verification.attempt_count >= 5:
            return jsonify({
                'error': 'Quá số lần thử cho phép',
                'message': 'Vui lòng thử lại sau 24 giờ'
            }), 429

        # Process video for liveness detection
        verification.increment_attempt()
        results = process_video_for_liveness(video_file)

        # Update verification record
        verification.liveness_score = results['liveness_score']
        verification.blink_count = results['blink_count']
        verification.last_attempt_at = datetime.utcnow()

        if results['liveness_score'] > current_app.config['MIN_LIVENESS_SCORE']:
            if results['blink_count'] >= current_app.config['MIN_BLINK_COUNT']:
                verification.status = 'verified'
                verification.verified_at = datetime.utcnow()
                current_user.kyc_status = 'verified'
                current_user.kyc_verified_at = datetime.utcnow()
                message = 'Xác thực thành công'
            else:
                verification.status = 'failed'
                verification.rejection_reason = f'Không phát hiện đủ số lần nháy mắt (phát hiện {results["blink_count"]} lần, yêu cầu {current_app.config["MIN_BLINK_COUNT"]} lần)'
                message = f'Không phát hiện đủ số lần nháy mắt (phát hiện {results["blink_count"]} lần, yêu cầu {current_app.config["MIN_BLINK_COUNT"]} lần)'
        else:
            verification.status = 'failed'
            verification.rejection_reason = f'Điểm số liveness không đạt yêu cầu (điểm số: {results["liveness_score"]:.2f}, yêu cầu: {current_app.config["MIN_LIVENESS_SCORE"]:.2f})'
            message = f'Xác thực không thành công: Điểm số liveness {results["liveness_score"]:.2f} thấp hơn ngưỡng yêu cầu {current_app.config["MIN_LIVENESS_SCORE"]:.2f}'

        db.session.add(verification)
        db.session.commit()

        # Đảm bảo tất cả các giá trị số và boolean được chuyển đổi sang kiểu Python gốc
        return jsonify({
            'message': message,
            'liveness_score': float(results['liveness_score']),
            'blink_count': int(results['blink_count']),
            'attempt_count': int(verification.attempt_count),
            'status': verification.status
        }), 200

    except Exception as e:
        current_app.logger.error(f"Liveness verification error: {str(e)}")

        # Thêm thông tin chi tiết về lỗi để giúp người dùng hiểu vấn đề
        error_message = 'Không thể xác thực. Vui lòng thử lại.'

        # Phân loại lỗi để cung cấp hướng dẫn cụ thể
        if "face" in str(e).lower():
            error_message = "Không thể phát hiện khuôn mặt rõ ràng. Vui lòng đảm bảo ánh sáng đầy đủ và giữ khuôn mặt ở giữa khung hình."
        elif "blink" in str(e).lower():
            error_message = "Không thể phát hiện nháy mắt. Vui lòng nháy mắt rõ ràng và tự nhiên."
        elif "video" in str(e).lower():
            error_message = "Lỗi khi xử lý video. Vui lòng thử lại với ánh sáng tốt hơn."

        return jsonify({
            'error': error_message,
            'details': str(e) if current_app.config.get('DEBUG', False) else None
        }), 500

@kyc_bp.route('/verify/id-card', methods=['POST'])
@token_required
@kyc_rate_limit()
def verify_id_card(current_user):
    if 'image' not in request.files:
        return jsonify({'error': 'Không tìm thấy file ảnh'}), 400

    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'Không có file nào được chọn'}), 400

    is_front = request.args.get('front', 'true').lower() == 'true'
    filepath = None

    try:
        # Get or create verification record
        verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
        if not verification:
            verification = KYCVerification(user_id=current_user.id)

        # Save and process ID card image
        filename = f'id_card_{current_user.id}_{"front" if is_front else "back"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        filename = sanitize_file_name(filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        image_file.save(filepath)

        # Process ID card image
        id_info = process_id_card(filepath, is_front)

        # Kiểm tra xem có trích xuất được các thông tin cần thiết không
        required_fields = ['id_number', 'full_name'] if is_front else ['issue_date', 'expiry_date']
        missing_fields = [field for field in required_fields if field not in id_info]

        if missing_fields:
            # Nếu thiếu thông tin cần thiết, trả về lỗi và yêu cầu upload lại
            missing_fields_vn = {
                'id_number': 'Số CCCD',
                'full_name': 'Họ và tên',
                'residence': 'Nơi cư trú',
                'issue_date': 'Ngày cấp',
                'expiry_date': 'Ngày hết hạn'
            }
            missing_fields_str = ', '.join([missing_fields_vn[field] for field in missing_fields])

            # Lưu lại thông tin về việc không trích xuất được thông tin
            current_app.logger.warning(f"Không trích xuất được thông tin: {missing_fields_str} từ ảnh CCCD {'mặt trước' if is_front else 'mặt sau'}")

            # Xóa file ảnh đã upload vì không sử dụng được
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'error': f"Không thể trích xuất thông tin: {missing_fields_str}",
                'need_reupload': True,
                'message': "Vui lòng chụp lại ảnh CCCD rõ nét hơn, đảm bảo đủ ánh sáng và không bị lóa."
            }), 400

        # Update verification record
        if is_front:
            verification.identity_card_front = filepath
        else:
            verification.identity_card_back = filepath

        # If we have both sides, create/update identity info
        if verification.identity_card_front and verification.identity_card_back:
            # Lưu thông tin từ mặt trước và mặt sau
            try:
                # Lấy thông tin từ mặt trước
                front_info = process_id_card(verification.identity_card_front, True)

                # Lấy thông tin từ mặt sau (hoặc sử dụng thông tin hiện tại nếu đang xử lý mặt sau)
                back_info = id_info if not is_front else process_id_card(verification.identity_card_back, False)

                # Kết hợp thông tin
                combined_info = {**front_info, **back_info}

                # Kiểm tra xem có đủ thông tin cần thiết không
                required_fields = ['id_number', 'full_name', 'date_of_birth', 'gender', 'nationality']
                missing_fields = [field for field in required_fields if field not in combined_info or combined_info[field] is None]

                if not missing_fields:
                    # Tất cả thông tin cần thiết đều có, tạo/cập nhật IdentityInfo
                    identity = IdentityInfo.query.filter_by(user_id=current_user.id).first()
                    if not identity:
                        identity = IdentityInfo(user_id=current_user.id)

                    # Cập nhật thông tin
                    for key, value in combined_info.items():
                        if hasattr(identity, key) and value is not None:
                            setattr(identity, key, value)

                    db.session.add(identity)
                else:
                    current_app.logger.warning(f"Thiếu thông tin cần thiết để tạo IdentityInfo: {missing_fields}")
            except Exception as e:
                current_app.logger.error(f"Lỗi khi kết hợp thông tin CCCD: {str(e)}")
                # Tiếp tục xử lý, không tạo IdentityInfo

        db.session.add(verification)
        db.session.commit()

        # Đảm bảo tất cả các giá trị boolean trong id_info được chuyển đổi sang kiểu boolean Python gốc
        for key, value in id_info.items():
            if isinstance(value, bool):
                id_info[key] = bool(value)

        return jsonify({
            'message': 'Tải lên thành công',
            'id_info': id_info
        }), 200
    except Exception as e:
        current_app.logger.error(f"ID card verification error: {str(e)}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        error_message = "Có lỗi xảy ra khi xác thực ID card. Vui lòng thử lại."
        error_code = 500

        # Xử lý lỗi EasyOCR
        if "easyocr" in str(e).lower() or "not installed" in str(e).lower() or "reader" in str(e).lower():
            error_message = "Lỗi hệ thống OCR: EasyOCR chưa được cài đặt hoặc cấu hình đúng. Vui lòng liên hệ quản trị viên."
            current_app.logger.error(f"EasyOCR error: {str(e)}")

            # Trả về dữ liệu giả lập trong môi trường phát triển
            if current_app.config.get('ENV') == 'development':
                mock_data = {
                    'front': {
                        'id_number': '079123456789',
                        'full_name': 'NGUYỄN VĂN A',
                        'date_of_birth': '01/01/1990',
                        'gender': 'Nam',
                        'nationality': 'Việt Nam',
                        'place_of_origin': 'TP Hồ Chí Minh'
                    },
                    'back': {
                        'issue_date': '01/01/2020',
                        'expiry_date': '01/01/2030'
                    }
                }

                return jsonify({
                    'message': 'Tải lên thành công (dữ liệu giả lập)',
                    'id_info': mock_data['front'] if is_front else mock_data['back'],
                    'warning': 'EasyOCR chưa được cài đặt. Đang sử dụng dữ liệu giả lập.'
                }), 200

        # Xử lý lỗi OCR khác
        elif "lỗi OCR" in str(e) or "OCR error" in str(e):
            error_message = "Không thể đọc thông tin từ ảnh CCCD. Vui lòng đảm bảo ảnh rõ nét và không bị lóa."

        # Xử lý lỗi cơ sở dữ liệu
        elif "IntegrityError" in str(e) or "cannot be null" in str(e):
            if not is_front:
                error_message = "Vui lòng tải lên mặt trước CCCD trước."
            else:
                error_message = "Thiếu thông tin bắt buộc trong CCCD. Vui lòng chụp lại ảnh rõ hơn."
            error_code = 400

        return jsonify({'error': error_message}), error_code

@kyc_bp.route('/status', methods=['GET'])
@token_required
def get_kyc_status(current_user):
    verification = KYCVerification.query.filter_by(user_id=current_user.id).first()

    if not verification:
        return jsonify({
            'status': 'pending',
            'liveness_verified': False,
            'id_card_verified': False,
            'attempt_count': 0
        }), 200

    id_card_verified = bool(verification.identity_card_front and verification.identity_card_back)

    # Đảm bảo tất cả các giá trị boolean được chuyển đổi sang kiểu boolean Python gốc
    liveness_verified = False
    if verification.liveness_score is not None and verification.blink_count is not None:
        liveness_verified = bool(verification.liveness_score > current_app.config['MIN_LIVENESS_SCORE'] and
                                verification.blink_count >= current_app.config['MIN_BLINK_COUNT'])

    return jsonify({
        'status': verification.status,
        'liveness_verified': liveness_verified,
        'id_card_verified': bool(id_card_verified),
        'verified_at': verification.verified_at.isoformat() if verification.verified_at else None,
        'liveness_score': float(verification.liveness_score) if verification.liveness_score is not None else None,
        'blink_count': int(verification.blink_count) if verification.blink_count is not None else 0,
        'attempt_count': int(verification.attempt_count),
        'last_attempt': verification.last_attempt_at.isoformat() if verification.last_attempt_at else None,
        'rejection_reason': verification.rejection_reason
    }), 200
