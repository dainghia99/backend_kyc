import logging
from deepface import DeepFace
import os

# Cấu hình logging
logger = logging.getLogger(__name__)

class DeepFaceVerification:
    def __init__(self, model_name='VGG-Face', distance_metric='cosine'):
        """
        Khởi tạo hệ thống xác thực khuôn mặt sử dụng DeepFace.

        Args:
            model_name: Tên model DeepFace sử dụng để trích xuất đặc trưng (ví dụ: 'VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'DeepID', 'ArcFace', 'Dlib', 'SFace').
            distance_metric: Metric sử dụng để so sánh vector đặc trưng (ví dụ: 'cosine', 'euclidean', 'euclidean_l2').
        """
        self.model_name = model_name
        self.distance_metric = distance_metric
        logger.info(f"Khởi tạo DeepFaceVerification với model: {self.model_name}, metric: {self.distance_metric}")

    def verify_face_match(self, img1_path, img2_path):
        """
        Xác thực xem hai ảnh có phải cùng một người không sử dụng DeepFace.

        Args:
            img1_path: Đường dẫn đến ảnh thứ nhất.
            img2_path: Đường dẫn đến ảnh thứ hai.

        Returns:
            Một dictionary chứa kết quả xác thực (verified: True/False, distance, v.v.) hoặc None nếu có lỗi.
        """
        try:
            # Kiểm tra xem file có tồn tại không
            if not os.path.exists(img1_path):
                logger.error(f"Không tìm thấy file: {img1_path}")
                return {"verified": False, "distance": None, "message": f"File không tồn tại: {img1_path}"}
            if not os.path.exists(img2_path):
                logger.error(f"Không tìm thấy file: {img2_path}")
                return {"verified": False, "distance": None, "message": f"File không tồn tại: {img2_path}"}

            # Thực hiện xác thực bằng DeepFace
            # DeepFace.verify tự động phát hiện khuôn mặt, trích xuất embedding và so sánh
            result = DeepFace.verify(img1_path, img2_path, 
                                   model_name=self.model_name, 
                                   distance_metric=self.distance_metric,
                                   enforce_detection=False, # Đảm bảo phát hiện khuôn mặt trước khi xử lý
                                   detector_backend='opencv' # Chỉ định sử dụng trình phát hiện OpenCV
                                  )

            # Log kết quả chi tiết từ deepface để debug
            logger.info(f"Kết quả DeepFace.verify: {result}")

            # Tạo cấu trúc trả về giống với lớp cũ để dễ thay thế
            verified = result['verified']
            distance = result['distance']
            # Bạn có thể thêm các thông tin khác từ result nếu cần
            message = f"Xác thực {'thành công' if verified else 'thất bại'}. Khoảng cách: {distance:.4f}"

            return {"verified": verified, "distance": distance, "message": message}

        except Exception as e:
            logger.error(f"Lỗi khi xác thực khuôn mặt bằng DeepFace: {type(e).__name__} - {str(e)}", exc_info=True)
            # Trả về kết quả thất bại khi có lỗi
            return {"verified": False, "distance": None, "message": f"Lỗi khi xử lý ảnh: {str(e)}"}

# Helper function to get an instance of DeepFaceVerification (optional, but good practice)
def get_deepface_verification():
    """
    Hàm trợ giúp để lấy một instance của DeepFaceVerification.
    Có thể cấu hình model và metric ở đây.
    """
    # Có thể đọc cấu hình từ config file nếu có
    # Hiện tại dùng giá trị mặc định
    return DeepFaceVerification(model_name='VGG-Face', distance_metric='cosine') 