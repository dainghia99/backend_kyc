"""
Script để so sánh hiệu suất giữa phương pháp phát hiện khuôn mặt cũ và phương pháp mới sử dụng YOLOv11
"""
import os
import sys
import cv2
import time
import logging
import argparse
import numpy as np
from utils.face_verification import extract_face_from_id_card, extract_face_from_selfie
from utils.face_verification_yolo import extract_face_from_id_card_yolo, extract_face_from_selfie_yolo

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_face_detection(image_path, output_dir=None, num_runs=5):
    """
    So sánh hiệu suất giữa phương pháp phát hiện khuôn mặt cũ và phương pháp mới
    
    Args:
        image_path: Đường dẫn đến ảnh cần phát hiện khuôn mặt
        output_dir: Thư mục để lưu ảnh kết quả
        num_runs: Số lần chạy để tính thời gian trung bình
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(image_path):
            logger.error(f"Không tìm thấy file: {image_path}")
            return
        
        # Tạo thư mục output nếu cần
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Đọc ảnh gốc
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Không thể đọc ảnh: {image_path}")
            return
        
        # Lưu ảnh gốc
        if output_dir:
            original_path = os.path.join(output_dir, f"original_{os.path.basename(image_path)}")
            cv2.imwrite(original_path, image)
        
        # So sánh thời gian xử lý
        logger.info("=== So sánh thời gian xử lý ===")
        
        # Phương pháp cũ
        old_times = []
        old_success = False
        old_face_location = None
        
        for i in range(num_runs):
            start_time = time.time()
            old_encoding, old_face_location, old_success, old_message = extract_face_from_id_card(image_path)
            end_time = time.time()
            old_times.append(end_time - start_time)
        
        old_avg_time = sum(old_times) / len(old_times)
        logger.info(f"Phương pháp cũ: {old_avg_time:.4f} giây (trung bình {num_runs} lần chạy)")
        logger.info(f"Phương pháp cũ: {'Thành công' if old_success else 'Thất bại'}")
        
        # Phương pháp mới
        new_times = []
        new_success = False
        new_face_location = None
        
        for i in range(num_runs):
            start_time = time.time()
            new_encoding, new_face_location, new_success, new_message = extract_face_from_id_card_yolo(image_path)
            end_time = time.time()
            new_times.append(end_time - start_time)
        
        new_avg_time = sum(new_times) / len(new_times)
        logger.info(f"Phương pháp mới (YOLOv11): {new_avg_time:.4f} giây (trung bình {num_runs} lần chạy)")
        logger.info(f"Phương pháp mới (YOLOv11): {'Thành công' if new_success else 'Thất bại'}")
        
        # So sánh kết quả
        logger.info("=== So sánh kết quả ===")
        
        # Vẽ kết quả lên ảnh
        if output_dir and image is not None:
            # Tạo bản sao của ảnh gốc
            old_result_image = image.copy()
            new_result_image = image.copy()
            
            # Vẽ kết quả của phương pháp cũ
            if old_success and old_face_location:
                top, right, bottom, left = old_face_location
                cv2.rectangle(old_result_image, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(old_result_image, "Old Method", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Lưu ảnh kết quả
                old_result_path = os.path.join(output_dir, f"old_method_{os.path.basename(image_path)}")
                cv2.imwrite(old_result_path, old_result_image)
                logger.info(f"Đã lưu kết quả phương pháp cũ tại: {old_result_path}")
            
            # Vẽ kết quả của phương pháp mới
            if new_success and new_face_location:
                top, right, bottom, left = new_face_location
                cv2.rectangle(new_result_image, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(new_result_image, "YOLOv11", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # Lưu ảnh kết quả
                new_result_path = os.path.join(output_dir, f"yolo_method_{os.path.basename(image_path)}")
                cv2.imwrite(new_result_path, new_result_image)
                logger.info(f"Đã lưu kết quả phương pháp mới tại: {new_result_path}")
            
            # Tạo ảnh so sánh
            if old_success and new_success and old_face_location and new_face_location:
                # Tạo ảnh so sánh
                comparison_image = np.hstack((old_result_image, new_result_image))
                
                # Lưu ảnh so sánh
                comparison_path = os.path.join(output_dir, f"comparison_{os.path.basename(image_path)}")
                cv2.imwrite(comparison_path, comparison_image)
                logger.info(f"Đã lưu ảnh so sánh tại: {comparison_path}")
        
        # Hiển thị kết luận
        logger.info("=== Kết luận ===")
        
        # So sánh thời gian
        if new_avg_time < old_avg_time:
            speedup = old_avg_time / new_avg_time
            logger.info(f"Phương pháp mới (YOLOv11) nhanh hơn {speedup:.2f} lần so với phương pháp cũ")
        else:
            slowdown = new_avg_time / old_avg_time
            logger.info(f"Phương pháp mới (YOLOv11) chậm hơn {slowdown:.2f} lần so với phương pháp cũ")
        
        # So sánh kết quả
        if new_success and not old_success:
            logger.info("Phương pháp mới (YOLOv11) phát hiện được khuôn mặt trong khi phương pháp cũ không phát hiện được")
        elif not new_success and old_success:
            logger.info("Phương pháp cũ phát hiện được khuôn mặt trong khi phương pháp mới (YOLOv11) không phát hiện được")
        elif new_success and old_success:
            logger.info("Cả hai phương pháp đều phát hiện được khuôn mặt")
        else:
            logger.info("Cả hai phương pháp đều không phát hiện được khuôn mặt")
    
    except Exception as e:
        logger.error(f"Lỗi khi so sánh phương pháp phát hiện khuôn mặt: {str(e)}")

def main():
    # Tạo parser cho command line arguments
    parser = argparse.ArgumentParser(description="So sánh hiệu suất giữa phương pháp phát hiện khuôn mặt cũ và phương pháp mới")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh cần phát hiện khuôn mặt")
    parser.add_argument("--output", type=str, default="comparison", help="Thư mục để lưu ảnh kết quả")
    parser.add_argument("--runs", type=int, default=5, help="Số lần chạy để tính thời gian trung bình")
    
    # Parse arguments
    args = parser.parse_args()
    
    # So sánh phương pháp phát hiện khuôn mặt
    compare_face_detection(args.image, args.output, args.runs)

if __name__ == "__main__":
    main()
