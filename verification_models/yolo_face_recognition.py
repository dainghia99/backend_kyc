"""
Module trích xuất đặc trưng khuôn mặt và so sánh khuôn mặt sử dụng YOLO (YOLOv8 hoặc YOLOv11)
Thay thế hoàn toàn thư viện face_recognition
"""
import os
import cv2
import numpy as np
import torch
import logging
from ultralytics import YOLO
from sklearn.metrics.pairwise import cosine_similarity

# Cấu hình logging
logger = logging.getLogger(__name__)

class YOLOFaceRecognition:
    def __init__(self, model_path=None, confidence=0.5):
        """
        Khởi tạo hệ thống nhận diện khuôn mặt sử dụng YOLO (YOLOv8 hoặc YOLOv11)

        Args:
            model_path: Đường dẫn đến file model YOLO face. Nếu None, sẽ tải model từ internet
            confidence: Ngưỡng tin cậy cho việc phát hiện khuôn mặt
        """
        self.confidence = confidence

        # Tải model YOLO face
        try:
            if model_path and os.path.exists(model_path):
                logger.info(f"Tải model YOLO từ {model_path}")
                self.model = YOLO(model_path)
            else:
                # Tải model YOLOv8n-face từ thư mục weights
                model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights", "yolov8n-face.pt")
                logger.info(f"Tải model YOLOv8n-face từ {model_path}")
                self.model = YOLO(model_path)

            # Kiểm tra xem CUDA có khả dụng không
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Sử dụng thiết bị: {self.device}")

        except Exception as e:
            logger.error(f"Lỗi khi tải model YOLO: {str(e)}")
            raise

    def detect_faces(self, image_path):
        """
        Phát hiện khuôn mặt trong ảnh sử dụng YOLO

        Args:
            image_path: Đường dẫn đến ảnh cần phát hiện khuôn mặt

        Returns:
            faces: Danh sách các khuôn mặt phát hiện được (x1, y1, x2, y2)
            image: Ảnh gốc đã được đọc
        """
        try:
            # Kiểm tra xem file có tồn tại không
            if not os.path.exists(image_path):
                logger.error(f"Không tìm thấy file: {image_path}")
                return [], None

            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Không thể đọc ảnh: {image_path}")
                return [], None

            # Ghi lại kích thước ảnh gốc để debug
            original_height, original_width = image.shape[:2]
            logger.info(f"Kích thước ảnh gốc: {original_width}x{original_height}")

            # Phát hiện khuôn mặt bằng YOLO
            results = self.model(image, conf=self.confidence)

            # Lấy thông tin các khuôn mặt phát hiện được
            faces = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Lấy tọa độ bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = float(box.conf[0])

                    # Thêm vào danh sách khuôn mặt
                    faces.append((x1, y1, x2, y2))
                    logger.info(f"Phát hiện khuôn mặt tại ({x1}, {y1}, {x2}, {y2}) với độ tin cậy {confidence:.2f}")

            # Nếu không tìm thấy khuôn mặt
            if len(faces) == 0:
                logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {image_path}")
                return [], image

            return faces, image

        except Exception as e:
            logger.error(f"Lỗi khi phát hiện khuôn mặt: {str(e)}")
            return [], None

    def extract_face_features(self, image, face_box):
        """
        Trích xuất đặc trưng khuôn mặt từ ảnh

        Args:
            image: Ảnh chứa khuôn mặt
            face_box: Tọa độ khuôn mặt (x1, y1, x2, y2)

        Returns:
            features: Vector đặc trưng của khuôn mặt
        """
        try:
            # Cắt khuôn mặt từ ảnh
            x1, y1, x2, y2 = face_box
            face_image = image[y1:y2, x1:x2]

            # Resize khuôn mặt về kích thước chuẩn
            face_image = cv2.resize(face_image, (112, 112))

            # Chuyển đổi sang định dạng RGB
            face_image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Chuẩn hóa ảnh
            face_image_rgb = face_image_rgb.astype(np.float32) / 255.0

            # Sử dụng HOG (Histogram of Oriented Gradients) để trích xuất đặc trưng
            # Chuyển về ảnh grayscale
            face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)

            # Tính toán HOG features
            winSize = (112, 112)
            blockSize = (16, 16)
            blockStride = (8, 8)
            cellSize = (8, 8)
            nbins = 9
            hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)
            hog_features = hog.compute(face_gray)

            # Chuẩn hóa HOG features
            if np.linalg.norm(hog_features) > 0:
                hog_features = hog_features / np.linalg.norm(hog_features)

            # Trích xuất thêm đặc trưng màu sắc
            # Tính histogram màu
            hist_features = []
            for i in range(3):  # 3 kênh màu
                hist = cv2.calcHist([face_image], [i], None, [64], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hist_features.extend(hist)

            # Kết hợp các đặc trưng
            combined_features = np.concatenate((hog_features.flatten(), np.array(hist_features)))

            # Chuẩn hóa vector đặc trưng
            if np.linalg.norm(combined_features) > 0:
                combined_features = combined_features / np.linalg.norm(combined_features)

            return combined_features

        except Exception as e:
            logger.error(f"Lỗi khi trích xuất đặc trưng khuôn mặt: {str(e)}")
            return None

    def extract_face_encoding(self, image_path):
        """
        Trích xuất đặc trưng khuôn mặt từ ảnh

        Args:
            image_path: Đường dẫn đến ảnh cần trích xuất đặc trưng khuôn mặt

        Returns:
            face_encoding: Vector đặc trưng của khuôn mặt
            face_location: Vị trí khuôn mặt trong ảnh (x1, y1, x2, y2)
            success: True nếu trích xuất thành công, False nếu không
            message: Thông báo lỗi hoặc thành công
        """
        try:
            # Phát hiện khuôn mặt bằng YOLO
            faces, image = self.detect_faces(image_path)

            if len(faces) == 0 or image is None:
                return None, None, False, "Không tìm thấy khuôn mặt trong ảnh"

            # Nếu tìm thấy nhiều khuôn mặt, chọn khuôn mặt lớn nhất
            if len(faces) > 1:
                logger.warning(f"Tìm thấy nhiều khuôn mặt ({len(faces)}) trong ảnh: {image_path}")

                # Tìm khuôn mặt có diện tích lớn nhất
                largest_face_idx = 0
                largest_face_area = 0

                for i, (x1, y1, x2, y2) in enumerate(faces):
                    face_area = (x2 - x1) * (y2 - y1)
                    if face_area > largest_face_area:
                        largest_face_area = face_area
                        largest_face_idx = i

                # Chỉ giữ lại khuôn mặt lớn nhất
                face = faces[largest_face_idx]
                logger.info(f"Đã chọn khuôn mặt lớn nhất với diện tích: {largest_face_area} pixels")
            else:
                face = faces[0]

            # Trích xuất đặc trưng khuôn mặt
            face_encoding = self.extract_face_features(image, face)

            if face_encoding is None:
                logger.warning(f"Không thể trích xuất đặc trưng khuôn mặt từ ảnh: {image_path}")
                return None, None, False, "Không thể trích xuất đặc trưng khuôn mặt từ ảnh"

            # Trả về kết quả
            return face_encoding, face, True, "Trích xuất đặc trưng khuôn mặt thành công"

        except Exception as e:
            logger.error(f"Lỗi khi trích xuất đặc trưng khuôn mặt: {str(e)}")
            return None, None, False, f"Lỗi khi xử lý ảnh: {str(e)}"

    def compare_faces(self, face_encoding1, face_encoding2, tolerance=0.45):
        """
        So sánh hai vector đặc trưng khuôn mặt

        Args:
            face_encoding1: Vector đặc trưng khuôn mặt thứ nhất
            face_encoding2: Vector đặc trưng khuôn mặt thứ hai
            tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau (thấp hơn = nghiêm ngặt hơn)

        Returns:
            match: True nếu khuôn mặt khớp, False nếu không
            distance: Khoảng cách giữa hai vector đặc trưng
            message: Thông báo mô tả kết quả
        """
        try:
            # Tính độ tương đồng cosine giữa hai vector đặc trưng
            similarity = cosine_similarity([face_encoding1], [face_encoding2])[0][0]

            # Chuyển đổi từ độ tương đồng sang khoảng cách (1 - similarity)
            distance = 1.0 - similarity

            # Ghi log khoảng cách để debug
            logger.info(f"Khoảng cách giữa hai khuôn mặt: {distance}")
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

    def verify_face_match(self, id_card_path, selfie_path, tolerance=0.45):
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

        # Trích xuất đặc trưng khuôn mặt từ CCCD
        id_card_encoding, id_card_location, id_card_success, id_card_message = self.extract_face_encoding(id_card_path)
        result['id_card_face_found'] = bool(id_card_success)

        if not id_card_success:
            logger.warning(f"Không thể trích xuất khuôn mặt từ CCCD: {id_card_message}")
            result['message'] = id_card_message
            return result

        # Trích xuất đặc trưng khuôn mặt từ ảnh selfie
        selfie_encoding, selfie_location, selfie_success, selfie_message = self.extract_face_encoding(selfie_path)
        result['selfie_face_found'] = bool(selfie_success)

        if not selfie_success:
            logger.warning(f"Không thể trích xuất khuôn mặt từ ảnh selfie: {selfie_message}")
            result['message'] = selfie_message
            return result

        # So sánh khuôn mặt
        match, distance, message = self.compare_faces(id_card_encoding, selfie_encoding, tolerance)

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

def download_yolo_model():
    """
    Tải model YOLO face từ GitHub
    """
    try:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
        os.makedirs(model_dir, exist_ok=True)

        # Thử tải YOLOv8n-face trước
        model_path = os.path.join(model_dir, "yolov8n-face.pt")

        # Kiểm tra xem model đã tồn tại chưa
        if os.path.exists(model_path):
            logger.info(f"Model YOLOv8 face đã tồn tại tại {model_path}")
            return model_path

        # Tải model từ GitHub
        try:
            logger.info("Đang tải model YOLOv8n-face từ GitHub...")
            model = YOLO("yolov8n-face.pt")

            # Lưu model
            model.save(model_path)
            logger.info(f"Đã tải và lưu model YOLOv8 face tại {model_path}")

            return model_path
        except Exception as e:
            logger.warning(f"Không thể tải model YOLOv8n-face: {str(e)}")

            # Nếu không tải được YOLOv8n-face, thử tải YOLOv11n-face
            try:
                model_path = os.path.join(model_dir, "yolov11n-face.pt")

                # Kiểm tra xem model đã tồn tại chưa
                if os.path.exists(model_path):
                    logger.info(f"Model YOLOv11 face đã tồn tại tại {model_path}")
                    return model_path

                logger.info("Đang tải model YOLOv11n-face từ GitHub...")
                model = YOLO("yolov11n-face.pt")

                # Lưu model
                model.save(model_path)
                logger.info(f"Đã tải và lưu model YOLOv11 face tại {model_path}")

                return model_path
            except Exception as e2:
                logger.error(f"Không thể tải model YOLOv11n-face: {str(e2)}")

                # Nếu không tải được cả hai model, thử sử dụng script download_yolo_model.py
                try:
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from download_yolo_model import download_yolo_model as download_model

                    logger.info("Thử tải model bằng script download_yolo_model.py...")
                    model_path = download_model("yolov8n-face.pt")

                    if model_path and os.path.exists(model_path):
                        logger.info(f"Đã tải model YOLOv8 face thành công tại: {model_path}")
                        return model_path
                    else:
                        logger.error("Không thể tải model YOLOv8 face")
                        return None
                except Exception as e3:
                    logger.error(f"Không thể tải model bằng script download_yolo_model.py: {str(e3)}")
                    return None

    except Exception as e:
        logger.error(f"Lỗi khi tải model YOLO face: {str(e)}")
        return None

# Khởi tạo instance toàn cục
yolo_face_recognition = None

def get_yolo_face_recognition():
    """
    Lấy instance YOLOFaceRecognition
    """
    global yolo_face_recognition

    if yolo_face_recognition is None:
        # Tải model
        model_path = download_yolo_model()

        # Khởi tạo instance
        yolo_face_recognition = YOLOFaceRecognition(model_path)

    return yolo_face_recognition
