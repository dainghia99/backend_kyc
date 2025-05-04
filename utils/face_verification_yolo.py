"""
Module xác thực khuôn mặt sử dụng YOLOv11 cho việc phát hiện khuôn mặt
"""
import os
import cv2
import numpy as np
import logging
from verification_models.yolo_face_detection import YOLOFaceDetector
from sklearn.metrics.pairwise import cosine_similarity

# Cấu hình logging
logger = logging.getLogger(__name__)

# Khởi tạo detector khuôn mặt YOLOv11
yolo_detector = None

def initialize_yolo_detector():
    """
    Khởi tạo detector khuôn mặt YOLOv11
    """
    global yolo_detector
    try:
        # Đường dẫn đến model YOLOv11 face
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "verification_models", "weights")
        model_path = os.path.join(model_dir, "yolov11n-face.pt")

        # Kiểm tra xem model đã tồn tại chưa
        if not os.path.exists(model_path):
            logger.warning(f"Không tìm thấy model YOLOv11 face tại {model_path}. Sẽ tải model từ internet.")
            model_path = None

        # Khởi tạo detector
        yolo_detector = YOLOFaceDetector(model_path)
        logger.info("Đã khởi tạo detector khuôn mặt YOLOv11 thành công")

    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo detector khuôn mặt YOLOv11: {str(e)}")
        yolo_detector = None

def extract_face_from_id_card_yolo(id_card_path):
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
    global yolo_detector

    # Khởi tạo detector nếu chưa được khởi tạo
    if yolo_detector is None:
        initialize_yolo_detector()

    # Nếu vẫn không khởi tạo được, sử dụng phương pháp cũ
    if yolo_detector is None:
        logger.warning("Không thể khởi tạo detector YOLOv11. Sử dụng phương pháp cũ.")
        from utils.face_verification import extract_face_from_id_card
        return extract_face_from_id_card(id_card_path)

    try:
        # Sử dụng YOLOv11 để trích xuất đặc trưng khuôn mặt
        face_encoding, face_location, success, message = yolo_detector.extract_face_encoding(id_card_path)

        if success:
            logger.info(f"Trích xuất khuôn mặt từ CCCD thành công sử dụng YOLOv11: {id_card_path}")
        else:
            logger.warning(f"Không thể trích xuất khuôn mặt từ CCCD sử dụng YOLOv11: {message}")

        return face_encoding, face_location, success, message

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất khuôn mặt từ CCCD sử dụng YOLOv11: {str(e)}")

        # Nếu có lỗi, thử sử dụng phương pháp cũ
        logger.info("Thử sử dụng phương pháp cũ để trích xuất khuôn mặt từ CCCD")
        from utils.face_verification import extract_face_from_id_card
        return extract_face_from_id_card(id_card_path)

def extract_face_from_selfie_yolo(selfie_path):
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
    global yolo_detector

    # Khởi tạo detector nếu chưa được khởi tạo
    if yolo_detector is None:
        initialize_yolo_detector()

    # Nếu vẫn không khởi tạo được, sử dụng phương pháp cũ
    if yolo_detector is None:
        logger.warning("Không thể khởi tạo detector YOLOv11. Sử dụng phương pháp cũ.")
        from utils.face_verification import extract_face_from_selfie
        return extract_face_from_selfie(selfie_path)

    try:
        # Sử dụng YOLOv11 để trích xuất đặc trưng khuôn mặt
        face_encoding, face_location, success, message = yolo_detector.extract_face_encoding(selfie_path)

        if success:
            logger.info(f"Trích xuất khuôn mặt từ ảnh selfie thành công sử dụng YOLOv11: {selfie_path}")
        else:
            logger.warning(f"Không thể trích xuất khuôn mặt từ ảnh selfie sử dụng YOLOv11: {message}")

        return face_encoding, face_location, success, message

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất khuôn mặt từ ảnh selfie sử dụng YOLOv11: {str(e)}")

        # Nếu có lỗi, thử sử dụng phương pháp cũ
        logger.info("Thử sử dụng phương pháp cũ để trích xuất khuôn mặt từ ảnh selfie")
        from utils.face_verification import extract_face_from_selfie
        return extract_face_from_selfie(selfie_path)

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
        # Kiểm tra xem các vector đặc trưng có hợp lệ không
        if id_card_encoding is None or selfie_encoding is None:
            logger.warning("Vector đặc trưng khuôn mặt không hợp lệ")
            return False, 1.0, "Không thể so sánh khuôn mặt: vector đặc trưng không hợp lệ"

        # Đảm bảo các vector đặc trưng có định dạng đúng cho cosine_similarity
        id_card_encoding_reshaped = np.array(id_card_encoding).reshape(1, -1)
        selfie_encoding_reshaped = np.array(selfie_encoding).reshape(1, -1)

        # Tính cosine similarity giữa hai vector đặc trưng
        similarity = cosine_similarity(id_card_encoding_reshaped, selfie_encoding_reshaped)[0][0]

        # Chuyển đổi similarity thành distance (1 - similarity)
        # Cosine similarity nằm trong khoảng [-1, 1], với 1 là hoàn toàn giống nhau
        # Chúng ta chuyển đổi thành distance trong khoảng [0, 2], với 0 là hoàn toàn giống nhau
        distance = 1.0 - similarity

        # Ghi log khoảng cách để debug
        logger.info(f"Cosine similarity giữa khuôn mặt CCCD và selfie: {similarity}")
        logger.info(f"Khoảng cách giữa khuôn mặt CCCD và selfie: {distance}")
        logger.info(f"Ngưỡng dung sai hiện tại: {tolerance}")

        # Xác định xem khuôn mặt có khớp theo ngưỡng dung sai không
        match = distance <= tolerance

        # Tạo thông báo mô tả
        if match:
            confidence = (1.0 - distance) * 100
            message = f"Khuôn mặt khớp với độ tin cậy {confidence:.2f}%"
            logger.info(f"Khuôn mặt khớp với độ tin cậy {confidence:.2f}%")
        else:
            confidence = (1.0 - distance) * 100
            if confidence < 0:
                confidence = 0
            message = f"Khuôn mặt không khớp (độ tin cậy chỉ đạt {confidence:.2f}%)"
            logger.warning(f"Khuôn mặt không khớp (độ tin cậy chỉ đạt {confidence:.2f}%)")

        return match, distance, message

    except Exception as e:
        logger.error(f"Lỗi khi so sánh khuôn mặt: {str(e)}")
        return False, 1.0, f"Lỗi khi so sánh khuôn mặt: {str(e)}"

def verify_face_match_yolo(id_card_path, selfie_path, tolerance=0.45):
    """
    Xác minh xem khuôn mặt trong ảnh CCCD có khớp với khuôn mặt trong ảnh selfie không sử dụng YOLOv11

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD
        selfie_path: Đường dẫn đến ảnh selfie
        tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau (thấp hơn = nghiêm ngặt hơn)

    Returns:
        result: Dictionary chứa kết quả xác minh
    """
    logger.info(f"Bắt đầu xác minh khuôn mặt giữa CCCD ({id_card_path}) và selfie ({selfie_path}) sử dụng YOLOv11")
    logger.info(f"Sử dụng ngưỡng dung sai: {tolerance}")

    result = {
        'success': False,
        'match': False,
        'distance': 1.0,
        'message': "",
        'id_card_face_found': False,
        'selfie_face_found': False
    }

    # Trích xuất khuôn mặt từ CCCD sử dụng YOLOv11
    id_card_encoding, id_card_location, id_card_success, id_card_message = extract_face_from_id_card_yolo(id_card_path)
    result['id_card_face_found'] = bool(id_card_success)  # Chuyển đổi sang bool gốc của Python

    if not id_card_success:
        logger.warning(f"Không thể trích xuất khuôn mặt từ CCCD: {id_card_message}")
        result['message'] = id_card_message
        return result

    # Trích xuất khuôn mặt từ ảnh selfie sử dụng YOLOv11
    selfie_encoding, selfie_location, selfie_success, selfie_message = extract_face_from_selfie_yolo(selfie_path)
    result['selfie_face_found'] = bool(selfie_success)  # Chuyển đổi sang bool gốc của Python

    if not selfie_success:
        logger.warning(f"Không thể trích xuất khuôn mặt từ ảnh selfie: {selfie_message}")
        result['message'] = selfie_message
        return result

    # So sánh khuôn mặt
    match, distance, message = compare_faces(id_card_encoding, selfie_encoding, tolerance)

    # Ghi log kết quả so sánh
    if match:
        logger.info(f"Khuôn mặt khớp với khoảng cách {distance} (ngưỡng: {tolerance})")
    else:
        logger.warning(f"Khuôn mặt không khớp với khoảng cách {distance} (ngưỡng: {tolerance})")

    # Cập nhật kết quả
    result['success'] = True
    result['match'] = match
    result['distance'] = distance
    result['message'] = message

    return result
