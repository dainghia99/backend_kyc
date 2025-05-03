from flask import Blueprint, request, jsonify, current_app
from models import db, KYCVerification, User
from utils.auth import token_required
from utils.face_verification import verify_face_match
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
    Endpoint para verificar si el rostro en la selfie coincide con el rostro en la CCCD
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Không tìm thấy file ảnh'}), 400

    selfie_file = request.files['image']
    if not selfie_file.filename:
        return jsonify({'error': 'Không có file nào được chọn'}), 400

    # Validar el archivo
    if not is_valid_file_extension(selfie_file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
        return jsonify({'error': 'Định dạng file không được hỗ trợ'}), 400

    if not is_valid_file_size(selfie_file, current_app.config['MAX_CONTENT_LENGTH']):
        return jsonify({'error': 'Kích thước file quá lớn'}), 400

    try:
        # Obtener el registro de verificación KYC
        verification = KYCVerification.query.filter_by(user_id=current_user.id).first()
        if not verification:
            return jsonify({'error': 'Vui lòng tải lên CCCD trước khi xác minh khuôn mặt'}), 400

        # Verificar que se haya cargado la imagen frontal de la CCCD
        if not verification.identity_card_front:
            return jsonify({'error': 'Vui lòng tải lên mặt trước CCCD trước khi xác minh khuôn mặt'}), 400

        # Guardar la imagen de selfie
        filename = f'selfie_{current_user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        filename = sanitize_file_name(filename)
        selfie_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Asegurar que el directorio de carga existe
        os.makedirs(os.path.dirname(selfie_path), exist_ok=True)

        selfie_file.save(selfie_path)

        # Obtener la ruta de la imagen frontal de la CCCD
        id_card_path = os.path.join(current_app.root_path, verification.identity_card_front)

        # Verificar la coincidencia de rostros
        tolerance = current_app.config.get('FACE_MATCH_TOLERANCE', 0.6)
        result = verify_face_match(id_card_path, selfie_path, tolerance)

        # Actualizar el registro de verificación
        verification.selfie_path = selfie_path
        verification.face_match = result['match']
        verification.face_distance = result['distance']
        verification.face_verified_at = datetime.now()

        if not result['match']:
            verification.status = 'failed'
            verification.rejection_reason = 'Xác minh không thành công: khuôn mặt không khớp'

        db.session.commit()

        # Preparar la respuesta - đảm bảo tất cả các giá trị boolean được chuyển đổi sang kiểu boolean Python gốc
        response = {
            'success': bool(result['success']),
            'match': bool(result['match']),
            'message': result['message'],
            'selfie_path': os.path.basename(selfie_path)
        }

        # Código de estado basado en el resultado
        status_code = 200 if bool(result['match']) else 400

        return jsonify(response), status_code

    except Exception as e:
        current_app.logger.error(f"Face verification error: {str(e)}")

        # Si ocurrió un error, eliminar la imagen de selfie si existe
        if 'selfie_path' in locals() and os.path.exists(selfie_path):
            os.remove(selfie_path)

        return jsonify({'error': 'Có lỗi xảy ra khi xác minh khuôn mặt. Vui lòng thử lại.'}), 500

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

    # Đảm bảo tất cả các giá trị boolean được chuyển đổi sang kiểu boolean Python gốc
    return jsonify({
        'face_verified': bool(verification.face_verified_at is not None),
        'face_match': bool(verification.face_match) if verification.face_match is not None else False,
        'selfie_uploaded': bool(verification.selfie_path is not None),
        'verified_at': verification.face_verified_at.isoformat() if verification.face_verified_at else None
    }), 200
