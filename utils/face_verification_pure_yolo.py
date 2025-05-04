"""
Module xác thực khuôn mặt chỉ sử dụng YOLO (YOLOv8 hoặc YOLOv11), không phụ thuộc vào face_recognition
"""
import os
import logging
from verification_models.yolo_face_recognition import get_yolo_face_recognition

# Cấu hình logging
logger = logging.getLogger(__name__)

def extract_face_from_id_card(id_card_path):
    """
    Trích xuất khuôn mặt từ ảnh CCCD sử dụng YOLOv11

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD

    Returns:
        face_encoding: Mã hóa khuôn mặt tìm thấy
        face_location: Vị trí khuôn mặt trong ảnh
        success: True nếu tìm thấy khuôn mặt, False nếu không
        message: Thông báo lỗi hoặc thành công
    """
    try:
        # Lấy instance YOLOFaceRecognition
        yolo_face = get_yolo_face_recognition()

        # Trích xuất đặc trưng khuôn mặt
        face_encoding, face_location, success, message = yolo_face.extract_face_encoding(id_card_path)

        if success:
            logger.info(f"Trích xuất khuôn mặt từ CCCD thành công: {id_card_path}")
        else:
            logger.warning(f"Không thể trích xuất khuôn mặt từ CCCD: {message}")

        return face_encoding, face_location, success, message

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất khuôn mặt từ CCCD: {str(e)}")
        return None, None, False, f"Lỗi khi xử lý ảnh CCCD: {str(e)}"

def extract_face_from_selfie(selfie_path):
    """
    Trích xuất khuôn mặt từ ảnh selfie sử dụng YOLOv11

    Args:
        selfie_path: Đường dẫn đến ảnh selfie

    Returns:
        face_encoding: Mã hóa khuôn mặt tìm thấy
        face_location: Vị trí khuôn mặt trong ảnh
        success: True nếu tìm thấy khuôn mặt, False nếu không
        message: Thông báo lỗi hoặc thành công
    """
    try:
        # Lấy instance YOLOFaceRecognition
        yolo_face = get_yolo_face_recognition()

        # Trích xuất đặc trưng khuôn mặt
        face_encoding, face_location, success, message = yolo_face.extract_face_encoding(selfie_path)

        if success:
            logger.info(f"Trích xuất khuôn mặt từ ảnh selfie thành công: {selfie_path}")
        else:
            logger.warning(f"Không thể trích xuất khuôn mặt từ ảnh selfie: {message}")

        return face_encoding, face_location, success, message

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất khuôn mặt từ ảnh selfie: {str(e)}")
        return None, None, False, f"Lỗi khi xử lý ảnh selfie: {str(e)}"

def compare_faces(id_card_encoding, selfie_encoding, tolerance=0.45):
    """
    So sánh hai mã hóa khuôn mặt để xác định xem có phải cùng một người không

    Args:
        id_card_encoding: Mã hóa khuôn mặt từ CCCD
        selfie_encoding: Mã hóa khuôn mặt từ ảnh selfie
        tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau (thấp hơn = nghiêm ngặt hơn)

    Returns:
        match: True nếu khuôn mặt khớp, False nếu không
        distance: Khoảng cách giữa hai mã hóa khuôn mặt
        message: Thông báo mô tả kết quả
    """
    try:
        # Lấy instance YOLOFaceRecognition
        yolo_face = get_yolo_face_recognition()

        # So sánh khuôn mặt
        match, distance, message = yolo_face.compare_faces(id_card_encoding, selfie_encoding, tolerance)

        return match, distance, message

    except Exception as e:
        logger.error(f"Lỗi khi so sánh khuôn mặt: {str(e)}")
        return False, 1.0, f"Lỗi khi so sánh khuôn mặt: {str(e)}"

def verify_face_match(id_card_path, selfie_path, tolerance=0.45):
    """
    Xác minh xem khuôn mặt trong ảnh CCCD có khớp với khuôn mặt trong ảnh selfie không

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD
        selfie_path: Đường dẫn đến ảnh selfie
        tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau (thấp hơn = nghiêm ngặt hơn)

    Returns:
        result: Dictionary chứa kết quả xác minh
    """
    logger.info(f"Bắt đầu xác minh khuôn mặt giữa CCCD ({id_card_path}) và selfie ({selfie_path})")
    logger.info(f"Sử dụng ngưỡng dung sai: {tolerance}")

    # Lấy instance YOLOFaceRecognition
    yolo_face = get_yolo_face_recognition()

    # Xác minh khuôn mặt
    result = yolo_face.verify_face_match(id_card_path, selfie_path, tolerance)

    return result
