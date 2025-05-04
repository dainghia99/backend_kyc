"""
Module phát hiện khuôn mặt sử dụng YOLOv11
"""
import os
import cv2
import numpy as np
import torch
import logging
from ultralytics import YOLO
import face_recognition

# Cấu hình logging
logger = logging.getLogger(__name__)

class YOLOFaceDetector:
    def __init__(self, model_path=None, confidence=0.5):
        """
        Khởi tạo detector khuôn mặt sử dụng YOLOv11
        
        Args:
            model_path: Đường dẫn đến file model YOLOv11 face. Nếu None, sẽ tải model từ internet
            confidence: Ngưỡng tin cậy cho việc phát hiện khuôn mặt
        """
        self.confidence = confidence
        
        # Tải model YOLOv11 face
        try:
            if model_path and os.path.exists(model_path):
                logger.info(f"Tải model YOLOv11 từ {model_path}")
                self.model = YOLO(model_path)
            else:
                # Tải model YOLOv11n-face từ GitHub
                logger.info("Tải model YOLOv11n-face từ GitHub")
                self.model = YOLO("yolov11n-face.pt")
                
            # Kiểm tra xem CUDA có khả dụng không
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Sử dụng thiết bị: {self.device}")
            
        except Exception as e:
            logger.error(f"Lỗi khi tải model YOLOv11: {str(e)}")
            raise
    
    def detect_faces(self, image_path):
        """
        Phát hiện khuôn mặt trong ảnh sử dụng YOLOv11
        
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
            
            # Phát hiện khuôn mặt bằng YOLOv11
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
            # Phát hiện khuôn mặt bằng YOLOv11
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
            
            # Chuyển đổi tọa độ từ (x1, y1, x2, y2) sang (top, right, bottom, left) cho face_recognition
            x1, y1, x2, y2 = face
            top, right, bottom, left = y1, x2, y2, x1
            
            # Chuyển đổi ảnh từ BGR sang RGB (face_recognition yêu cầu định dạng RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Trích xuất đặc trưng khuôn mặt
            face_location = (top, right, bottom, left)
            face_locations = [face_location]  # face_recognition yêu cầu danh sách các vị trí
            
            # Mã hóa khuôn mặt
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) == 0:
                logger.warning(f"Không thể mã hóa khuôn mặt trong ảnh: {image_path}")
                return None, None, False, "Không thể mã hóa khuôn mặt trong ảnh"
            
            # Trả về mã hóa của khuôn mặt đầu tiên tìm thấy
            return face_encodings[0], face_location, True, "Trích xuất khuôn mặt thành công"
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất đặc trưng khuôn mặt: {str(e)}")
            return None, None, False, f"Lỗi khi xử lý ảnh: {str(e)}"

def download_yolo_model():
    """
    Tải model YOLOv11 face từ GitHub
    """
    try:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, "yolov11n-face.pt")
        
        # Kiểm tra xem model đã tồn tại chưa
        if os.path.exists(model_path):
            logger.info(f"Model YOLOv11 face đã tồn tại tại {model_path}")
            return model_path
        
        # Tải model từ GitHub
        logger.info("Đang tải model YOLOv11n-face từ GitHub...")
        model = YOLO("yolov11n-face.pt")
        
        # Lưu model
        model.save(model_path)
        logger.info(f"Đã tải và lưu model YOLOv11 face tại {model_path}")
        
        return model_path
    
    except Exception as e:
        logger.error(f"Lỗi khi tải model YOLOv11 face: {str(e)}")
        return None

if __name__ == "__main__":
    # Cấu hình logging
    logging.basicConfig(level=logging.INFO)
    
    # Tải model
    model_path = download_yolo_model()
    
    # Khởi tạo detector
    detector = YOLOFaceDetector(model_path)
    
    # Test với một ảnh
    test_image = "path/to/test/image.jpg"
    if os.path.exists(test_image):
        faces, image = detector.detect_faces(test_image)
        print(f"Số khuôn mặt phát hiện được: {len(faces)}")
        
        # Vẽ các khuôn mặt phát hiện được
        if image is not None and len(faces) > 0:
            for (x1, y1, x2, y2) in faces:
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Hiển thị ảnh
            cv2.imshow("Detected Faces", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
