"""
Script để chạy kiểm thử so sánh khuôn mặt giữa ảnh CCCD và các ảnh selfie
"""
import os
import sys
import logging
import subprocess

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Đường dẫn đến ảnh CCCD và các ảnh selfie
    # Xác định thư mục hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__))

    id_card_path = os.path.join(current_dir, "uploads", "id_card_35_front_20250504_183313.jpg")
    selfie_paths = [
        os.path.join(current_dir, "uploads", "selfie_35_20250504_184022.jpg"), # Ảnh sai
        os.path.join(current_dir, "uploads", "selfie_35_20250504_175324.jpg"), # Ảnh đúng
    ]

    # Kiểm tra xem các file có tồn tại không
    if not os.path.exists(id_card_path):
        logger.error(f"Không tìm thấy file CCCD: {id_card_path}")
        sys.exit(1)

    for selfie_path in selfie_paths:
        if not os.path.exists(selfie_path):
            logger.error(f"Không tìm thấy file selfie: {selfie_path}")
            sys.exit(1)

    # Tạo thư mục kết quả
    output_dir = os.path.join(current_dir, "test_results", "face_comparison")
    os.makedirs(output_dir, exist_ok=True)

    # Chạy kiểm thử so sánh khuôn mặt
    logger.info("Bắt đầu kiểm thử so sánh khuôn mặt...")

    # Tạo lệnh để chạy kiểm thử
    command = [
        sys.executable,
        "test_pure_yolo.py",
        "--mode", "multi-verification",
        "--id-card", id_card_path,
        "--selfies"
    ] + selfie_paths + [
        "--output", output_dir,
        "--tolerance", "0.45"
    ]

    # Chạy lệnh
    try:
        logger.info(f"Chạy lệnh: {' '.join(command)}")
        subprocess.run(command, check=True)
        logger.info("Kiểm thử so sánh khuôn mặt đã hoàn thành!")
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi chạy kiểm thử: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
