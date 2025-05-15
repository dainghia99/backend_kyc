from flask import Blueprint, request, jsonify, current_app
from models import db, KYCVerification, User, IdentityInfo
from utils.auth import token_required
from utils.easyocr_utils import process_id_card
from middleware.rate_limit import kyc_rate_limit
from datetime import datetime
import os
import logging

# Cấu hình logger
logger = logging.getLogger(__name__)

ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/process', methods=['POST'])
@token_required
@kyc_rate_limit()
def process_image_direct(current_user):
    """
    API endpoint để xử lý ảnh trực tiếp từ đường dẫn file trong thư mục uploads

    Request JSON:
    {
        "image_path": "đường dẫn tương đối đến file ảnh trong thư mục uploads",
        "is_front": true/false
    }
    """
    data = request.get_json()

    if not data or 'image_path' not in data:
        return jsonify({'error': 'Thiếu đường dẫn ảnh'}), 400

    image_path = data.get('image_path')
    is_front = data.get('is_front', True)

    # Xây dựng đường dẫn đầy đủ
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_path)

    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(full_path):
        return jsonify({'error': f'Không tìm thấy file ảnh tại đường dẫn: {image_path}'}), 404

    try:
        # Xử lý ảnh CCCD
        id_info = process_id_card(full_path, is_front)

        # Kiểm tra xem có trích xuất được các thông tin cần thiết không
        required_fields = ['id_number', 'full_name'] if is_front else ['issue_date', 'expiry_date']
        missing_fields = [field for field in required_fields if field not in id_info]

        if missing_fields:
            # Nếu thiếu thông tin cần thiết, trả về lỗi
            missing_fields_vn = {
                'id_number': 'Số CCCD',
                'full_name': 'Họ và tên',
                'residence': 'Nơi cư trú',
                'issue_date': 'Ngày cấp',
                'expiry_date': 'Ngày hết hạn'
            }
            missing_fields_str = ', '.join([missing_fields_vn[field] for field in missing_fields])

            # Lưu lại thông tin về việc không trích xuất được thông tin
            logger.warning(f"Không trích xuất được thông tin: {missing_fields_str} từ ảnh CCCD {'mặt trước' if is_front else 'mặt sau'}")

            return jsonify({
                'error': f"Không thể trích xuất thông tin: {missing_fields_str}",
                'need_reupload': True,
                'message': "Vui lòng chụp lại ảnh CCCD rõ nét hơn, đảm bảo đủ ánh sáng và không bị lóa."
            }), 400

        # Cập nhật thông tin KYC nếu cần
        if data.get('update_verification', False):
            verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
            if not verification:
                verification = KYCVerification(user_id=current_user.id)

            # Cập nhật đường dẫn ảnh - Chỉ lưu tên file thay vì đường dẫn đầy đủ
            if is_front:
                verification.identity_card_front = image_path
            else:
                verification.identity_card_back = image_path

            db.session.add(verification)
            db.session.commit()

        # Đảm bảo tất cả các giá trị boolean trong id_info được chuyển đổi sang kiểu boolean Python gốc
        for key, value in id_info.items():
            if isinstance(value, bool):
                id_info[key] = bool(value)

        return jsonify({
            'message': 'Xử lý ảnh thành công',
            'id_info': id_info
        }), 200

    except Exception as e:
        logger.error(f"Lỗi khi xử lý ảnh OCR: {str(e)}")

        error_message = "Có lỗi xảy ra khi xử lý ảnh. Vui lòng thử lại."
        error_code = 500

        # Xử lý lỗi EasyOCR
        if "easyocr" in str(e).lower() or "not installed" in str(e).lower() or "reader" in str(e).lower():
            error_message = "Lỗi hệ thống OCR: EasyOCR chưa được cài đặt hoặc cấu hình đúng. Vui lòng liên hệ quản trị viên."

        # Xử lý lỗi OCR khác
        elif "lỗi OCR" in str(e) or "OCR error" in str(e):
            error_message = "Không thể đọc thông tin từ ảnh CCCD. Vui lòng đảm bảo ảnh rõ nét và không bị lóa."

        return jsonify({'error': error_message}), error_code

@ocr_bp.route('/upload-and-process', methods=['POST'])
@token_required
@kyc_rate_limit()
def upload_and_process(current_user):
    """
    API endpoint để upload ảnh và xử lý OCR trong một bước
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Không tìm thấy file ảnh'}), 400

    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'Không có file nào được chọn'}), 400

    is_front = request.args.get('front', 'true').lower() == 'true'
    filepath = None

    try:
        # Lưu ảnh vào thư mục uploads
        filename = f'id_card_{current_user.id}_{"front" if is_front else "back"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Đảm bảo thư mục uploads tồn tại
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Lưu file
        image_file.save(filepath)

        # Xử lý ảnh CCCD
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
            logger.warning(f"Không trích xuất được thông tin: {missing_fields_str} từ ảnh CCCD {'mặt trước' if is_front else 'mặt sau'}")

            # Xóa file ảnh đã upload vì không sử dụng được
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({
                'error': f"Không thể trích xuất thông tin: {missing_fields_str}",
                'need_reupload': True,
                'message': "Vui lòng chụp lại ảnh CCCD rõ nét hơn, đảm bảo đủ ánh sáng và không bị lóa."
            }), 400

        # Cập nhật thông tin KYC
        verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
        if not verification:
            verification = KYCVerification(user_id=current_user.id)

        # Cập nhật đường dẫn ảnh - Chỉ lưu tên file thay vì đường dẫn đầy đủ
        if is_front:
            verification.identity_card_front = filename
        else:
            verification.identity_card_back = filename

        db.session.add(verification)
        db.session.commit()

        # Đảm bảo tất cả các giá trị boolean trong id_info được chuyển đổi sang kiểu boolean Python gốc
        for key, value in id_info.items():
            if isinstance(value, bool):
                id_info[key] = bool(value)

        # Trả về kết quả
        return jsonify({
            'message': 'Tải lên và xử lý ảnh thành công',
            'id_info': id_info,
            'image_path': filename  # Trả về tên file để có thể sử dụng lại sau này
        }), 200

    except Exception as e:
        logger.error(f"Lỗi khi upload và xử lý ảnh OCR: {str(e)}")

        # Xóa file nếu có lỗi
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        error_message = "Có lỗi xảy ra khi xử lý ảnh. Vui lòng thử lại."
        error_code = 500

        # Xử lý lỗi EasyOCR
        if "easyocr" in str(e).lower() or "not installed" in str(e).lower() or "reader" in str(e).lower():
            error_message = "Lỗi hệ thống OCR: EasyOCR chưa được cài đặt hoặc cấu hình đúng. Vui lòng liên hệ quản trị viên."

        # Xử lý lỗi OCR khác
        elif "lỗi OCR" in str(e) or "OCR error" in str(e):
            error_message = "Không thể đọc thông tin từ ảnh CCCD. Vui lòng đảm bảo ảnh rõ nét và không bị lóa."

        return jsonify({'error': error_message}), error_code
