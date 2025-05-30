"""
Module xác thực khuôn mặt sử dụng DeepFace.
"""
import os
import logging
# from verification_models.yolo_face_recognition import get_yolo_face_recognition
from verification_models.deepface_verification import DeepFaceVerification

# Cấu hình logging
logger = logging.getLogger(__name__)

def extract_face_from_id_card(id_card_path):
    """
    (Chức năng này hiện không được sử dụng trực tiếp trong luồng DeepFace. DeepFace xử lý phát hiện và trích xuất nội bộ)

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD

    Returns:
        None, None, False, Thông báo lỗi hoặc không hỗ trợ
    """
    logger.warning("extract_face_from_id_card not implemented or used in DeepFace flow")
    return None, None, False, "Hàm không được hỗ trợ trong chế độ DeepFaceVerification"

def extract_face_from_selfie(selfie_path):
    """
    (Chức năng này hiện không được sử dụng trực tiếp trong luồng DeepFace. DeepFace xử lý phát hiện và trích xuất nội bộ)

    Args:
        selfie_path: Đường dẫn đến ảnh selfie

    Returns:
        None, None, False, Thông báo lỗi hoặc không hỗ trợ
    """
    logger.warning("extract_face_from_selfie not implemented or used in DeepFace flow")
    return None, None, False, "Hàm không được hỗ trợ trong chế độ DeepFaceVerification"

def compare_faces(id_card_encoding, selfie_encoding, tolerance=0.45):
    """
    (Chức năng này hiện không được sử dụng trực tiếp trong luồng DeepFace. DeepFace xử lý so sánh nội bộ)

    Args:
        id_card_encoding: Mã hóa khuôn mặt từ CCCD (không sử dụng trực tiếp)
        selfie_encoding: Mã hóa khuôn mặt từ ảnh selfie (không sử dụng trực tiếp)
        tolerance: Ngưỡng dung sai (không sử dụng trực tiếp bởi DeepFace.verify)

    Returns:
        False, 1.0, Thông báo lỗi hoặc không hỗ trợ
    """
    logger.warning("compare_faces not implemented or used in DeepFace flow")
    return False, 1.0, "Hàm không được hỗ trợ trong chế độ DeepFaceVerification"

def verify_face_match(id_card_path, selfie_path):
    """
    Xác minh xem khuôn mặt trong ảnh CCCD có khớp với khuôn mặt trong ảnh selfie sử dụng DeepFace.

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD
        selfie_path: Đường dẫn đến ảnh selfie

    Returns:
        result: Dictionary chứa kết quả xác minh từ DeepFace
    """
    logger.info(f"Bắt đầu xác minh khuôn mặt giữa CCCD ({id_card_path}) và selfie ({selfie_path}) sử dụng DeepFace")

    deepface_verifier = DeepFaceVerification(model_name='VGG-Face', distance_metric='cosine') 
    result = deepface_verifier.verify_face_match(id_card_path, selfie_path)

    return result
