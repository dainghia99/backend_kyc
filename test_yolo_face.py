"""
Script để kiểm thử YOLOv11 cho phát hiện khuôn mặt
"""
import os
import sys
import cv2
import logging
import argparse
from verification_models.yolo_face_detection import YOLOFaceDetector

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yolo_face_detection(image_path, output_dir=None, confidence=0.5):
    """
    Kiểm thử phát hiện khuôn mặt bằng YOLOv11
    
    Args:
        image_path: Đường dẫn đến ảnh cần phát hiện khuôn mặt
        output_dir: Thư mục để lưu ảnh kết quả
        confidence: Ngưỡng tin cậy cho việc phát hiện khuôn mặt
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(image_path):
            logger.error(f"Không tìm thấy file: {image_path}")
            return False
        
        # Khởi tạo detector
        detector = YOLOFaceDetector(confidence=confidence)
        
        # Phát hiện khuôn mặt
        logger.info(f"Đang phát hiện khuôn mặt trong ảnh: {image_path}")
        faces, image = detector.detect_faces(image_path)
        
        if len(faces) == 0:
            logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {image_path}")
            return False
        
        logger.info(f"Đã phát hiện {len(faces)} khuôn mặt trong ảnh")
        
        # Vẽ các khuôn mặt phát hiện được
        if image is not None:
            for i, (x1, y1, x2, y2) in enumerate(faces):
                # Vẽ bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Hiển thị số thứ tự của khuôn mặt
                cv2.putText(image, f"Face #{i+1}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Lưu ảnh kết quả nếu có output_dir
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"detected_{os.path.basename(image_path)}")
                cv2.imwrite(output_path, image)
                logger.info(f"Đã lưu ảnh kết quả tại: {output_path}")
            
            # Hiển thị ảnh
            cv2.imshow("Detected Faces", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # Trích xuất đặc trưng khuôn mặt
        logger.info("Đang trích xuất đặc trưng khuôn mặt...")
        face_encoding, face_location, success, message = detector.extract_face_encoding(image_path)
        
        if not success:
            logger.warning(f"Không thể trích xuất đặc trưng khuôn mặt: {message}")
            return False
        
        logger.info(f"Đã trích xuất đặc trưng khuôn mặt thành công: {message}")
        
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi kiểm thử phát hiện khuôn mặt: {str(e)}")
        return False

def main():
    # Tạo parser cho command line arguments
    parser = argparse.ArgumentParser(description="Kiểm thử phát hiện khuôn mặt bằng YOLOv11")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh cần phát hiện khuôn mặt")
    parser.add_argument("--output", type=str, default="debug", help="Thư mục để lưu ảnh kết quả")
    parser.add_argument("--confidence", type=float, default=0.5, help="Ngưỡng tin cậy cho việc phát hiện khuôn mặt")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Kiểm thử phát hiện khuôn mặt
    success = test_yolo_face_detection(args.image, args.output, args.confidence)
    
    if success:
        logger.info("Kiểm thử phát hiện khuôn mặt thành công!")
    else:
        logger.error("Kiểm thử phát hiện khuôn mặt thất bại!")

if __name__ == "__main__":
    main()
