import os
import cv2
import numpy as np
import face_recognition
import logging

# Ensure numpy is properly imported for type checking
from numpy import bool_ as np_bool, number as np_number

# Configurar logging
logger = logging.getLogger(__name__)

def extract_face_from_id_card(id_card_path):
    """
    Trích xuất khuôn mặt từ ảnh CCCD

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD

    Returns:
        face_encoding: Mã hóa khuôn mặt tìm thấy
        face_location: Vị trí khuôn mặt trong ảnh
        success: True nếu tìm thấy khuôn mặt, False nếu không
        message: Thông báo lỗi hoặc thành công
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(id_card_path):
            logger.error(f"Không tìm thấy file: {id_card_path}")
            return None, None, False, "Không tìm thấy ảnh CCCD"

        # Đọc ảnh bằng OpenCV để xử lý trước
        img = cv2.imread(id_card_path)
        if img is None:
            logger.error(f"Không thể đọc ảnh: {id_card_path}")
            return None, None, False, "Không thể đọc ảnh CCCD"

        # Ghi lại kích thước ảnh gốc để debug
        original_height, original_width = img.shape[:2]
        logger.info(f"Kích thước ảnh CCCD gốc: {original_width}x{original_height}")

        # Chuyển đổi sang RGB (face_recognition yêu cầu định dạng RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Tăng cường độ tương phản để dễ nhận diện khuôn mặt
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        img_lab[:,:,0] = clahe.apply(img_lab[:,:,0])
        img_enhanced = cv2.cvtColor(img_lab, cv2.COLOR_LAB2RGB)

        # Sử dụng face_recognition để phát hiện khuôn mặt
        face_locations = face_recognition.face_locations(img_enhanced)

        # Kiểm tra xem có tìm thấy khuôn mặt không
        if len(face_locations) == 0:
            logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {id_card_path}")

            # Thử lại với ảnh gốc nếu ảnh tăng cường không phát hiện được
            face_locations = face_recognition.face_locations(img_rgb)
            if len(face_locations) == 0:
                return None, None, False, "Không tìm thấy khuôn mặt trong ảnh CCCD"
            else:
                logger.info("Đã tìm thấy khuôn mặt trong ảnh gốc sau khi thử lại")
                img_enhanced = img_rgb  # Sử dụng ảnh gốc nếu phát hiện được khuôn mặt

        # Nếu tìm thấy nhiều khuôn mặt, chọn khuôn mặt lớn nhất (có khả năng cao nhất là khuôn mặt chính trong CCCD)
        if len(face_locations) > 1:
            logger.warning(f"Tìm thấy nhiều khuôn mặt ({len(face_locations)}) trong ảnh: {id_card_path}")

            # Tìm khuôn mặt có diện tích lớn nhất
            largest_face_idx = 0
            largest_face_area = 0

            for i, (top, right, bottom, left) in enumerate(face_locations):
                face_area = (bottom - top) * (right - left)
                if face_area > largest_face_area:
                    largest_face_area = face_area
                    largest_face_idx = i

            # Chỉ giữ lại khuôn mặt lớn nhất
            face_locations = [face_locations[largest_face_idx]]
            logger.info(f"Đã chọn khuôn mặt lớn nhất với diện tích: {largest_face_area} pixels")

        # Ghi lại thông tin vị trí khuôn mặt để debug
        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top
        logger.info(f"Vị trí khuôn mặt: top={top}, right={right}, bottom={bottom}, left={left}")
        logger.info(f"Kích thước khuôn mặt: {face_width}x{face_height}")

        # Mã hóa khuôn mặt
        face_encodings = face_recognition.face_encodings(img_enhanced, face_locations)

        if len(face_encodings) == 0:
            logger.warning(f"Không thể mã hóa khuôn mặt trong ảnh: {id_card_path}")
            return None, None, False, "Không thể mã hóa khuôn mặt trong ảnh CCCD"

        # Trả về mã hóa của khuôn mặt đầu tiên tìm thấy
        return face_encodings[0], face_locations[0], True, "Trích xuất khuôn mặt thành công"

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất khuôn mặt từ CCCD: {str(e)}")
        return None, None, False, f"Lỗi khi xử lý ảnh: {str(e)}"

def extract_face_from_selfie(selfie_path):
    """
    Trích xuất khuôn mặt từ ảnh selfie

    Args:
        selfie_path: Đường dẫn đến ảnh selfie

    Returns:
        face_encoding: Mã hóa khuôn mặt tìm thấy
        face_location: Vị trí khuôn mặt trong ảnh
        success: True nếu tìm thấy khuôn mặt, False nếu không
        message: Thông báo lỗi hoặc thành công
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(selfie_path):
            logger.error(f"Không tìm thấy file: {selfie_path}")
            return None, None, False, "Không tìm thấy ảnh selfie"

        # Đọc ảnh bằng OpenCV để xử lý trước
        img = cv2.imread(selfie_path)
        if img is None:
            logger.error(f"Không thể đọc ảnh: {selfie_path}")
            return None, None, False, "Không thể đọc ảnh selfie"

        # Ghi lại kích thước ảnh gốc để debug
        original_height, original_width = img.shape[:2]
        logger.info(f"Kích thước ảnh selfie gốc: {original_width}x{original_height}")

        # Chuyển đổi sang RGB (face_recognition yêu cầu định dạng RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Sử dụng face_recognition để phát hiện khuôn mặt
        face_locations = face_recognition.face_locations(img_rgb)

        # Kiểm tra xem có tìm thấy khuôn mặt không
        if len(face_locations) == 0:
            logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {selfie_path}")
            return None, None, False, "Không tìm thấy khuôn mặt trong ảnh selfie"

        # Nếu tìm thấy nhiều khuôn mặt, chọn khuôn mặt lớn nhất (có khả năng cao nhất là khuôn mặt chính)
        if len(face_locations) > 1:
            logger.warning(f"Tìm thấy nhiều khuôn mặt ({len(face_locations)}) trong ảnh selfie: {selfie_path}")

            # Tìm khuôn mặt có diện tích lớn nhất
            largest_face_idx = 0
            largest_face_area = 0

            for i, (top, right, bottom, left) in enumerate(face_locations):
                face_area = (bottom - top) * (right - left)
                if face_area > largest_face_area:
                    largest_face_area = face_area
                    largest_face_idx = i

            # Chỉ giữ lại khuôn mặt lớn nhất
            face_locations = [face_locations[largest_face_idx]]
            logger.info(f"Đã chọn khuôn mặt lớn nhất trong ảnh selfie với diện tích: {largest_face_area} pixels")

        # Ghi lại thông tin vị trí khuôn mặt để debug
        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top
        logger.info(f"Vị trí khuôn mặt trong selfie: top={top}, right={right}, bottom={bottom}, left={left}")
        logger.info(f"Kích thước khuôn mặt trong selfie: {face_width}x{face_height}")

        # Mã hóa khuôn mặt
        face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

        if len(face_encodings) == 0:
            logger.warning(f"Không thể mã hóa khuôn mặt trong ảnh selfie: {selfie_path}")
            return None, None, False, "Không thể mã hóa khuôn mặt trong ảnh selfie"

        # Trả về mã hóa của khuôn mặt đầu tiên tìm thấy
        return face_encodings[0], face_locations[0], True, "Trích xuất khuôn mặt từ ảnh selfie thành công"

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
        distance: Khoảng cách giữa hai khuôn mặt (khoảng cách nhỏ hơn cho biết độ tương đồng cao hơn)
        message: Thông báo mô tả kết quả
    """
    try:
        if id_card_encoding is None or selfie_encoding is None:
            return False, 1.0, "Không thể so sánh mã hóa khuôn mặt"

        # Tính toán khoảng cách giữa hai khuôn mặt
        face_distances = face_recognition.face_distance([id_card_encoding], selfie_encoding)

        if len(face_distances) == 0:
            return False, 1.0, "Lỗi khi tính toán khoảng cách giữa khuôn mặt"

        distance = face_distances[0]

        # Ghi log khoảng cách để debug
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

    result = {
        'success': False,
        'match': False,
        'distance': 1.0,
        'message': "",
        'id_card_face_found': False,
        'selfie_face_found': False
    }

    # Trích xuất khuôn mặt từ CCCD
    id_card_encoding, id_card_location, id_card_success, id_card_message = extract_face_from_id_card(id_card_path)
    result['id_card_face_found'] = bool(id_card_success)  # Chuyển đổi sang bool gốc của Python

    if not id_card_success:
        logger.warning(f"Không thể trích xuất khuôn mặt từ CCCD: {id_card_message}")
        result['message'] = id_card_message
        return result

    # Trích xuất khuôn mặt từ ảnh selfie
    selfie_encoding, selfie_location, selfie_success, selfie_message = extract_face_from_selfie(selfie_path)
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

    result['success'] = True
    result['match'] = bool(match)  # Chuyển đổi sang bool gốc của Python
    result['distance'] = float(distance)  # Chuyển đổi sang float gốc của Python
    result['message'] = message

    # Đảm bảo tất cả các giá trị đều có thể serialize thành JSON
    for key in result:
        if isinstance(result[key], np_bool):
            result[key] = bool(result[key])
        elif isinstance(result[key], np_number):
            result[key] = float(result[key])

    # Thêm thông tin chi tiết về vị trí khuôn mặt để debug
    if id_card_location and selfie_location:
        id_top, id_right, id_bottom, id_left = id_card_location
        selfie_top, selfie_right, selfie_bottom, selfie_left = selfie_location

        id_face_width = id_right - id_left
        id_face_height = id_bottom - id_top
        selfie_face_width = selfie_right - selfie_left
        selfie_face_height = selfie_bottom - selfie_top

        result['debug_info'] = {
            'id_face_size': f"{id_face_width}x{id_face_height}",
            'selfie_face_size': f"{selfie_face_width}x{selfie_face_height}",
            'tolerance': tolerance
        }

    return result
