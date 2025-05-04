"""
Script để tải trực tiếp model YOLO face từ GitHub
"""
import os
import sys
import logging
import requests
import shutil
from tqdm import tqdm

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_file(url, destination):
    """
    Tải file từ URL và lưu vào destination
    """
    try:
        # Tạo thư mục chứa file nếu chưa tồn tại
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Tải file với thanh tiến trình
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            logger.info(f"Đang tải file từ {url}")
            logger.info(f"Kích thước file: {total_size / (1024 * 1024):.2f} MB")
            logger.info(f"Đích đến: {destination}")
            
            with open(destination, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(destination)) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            logger.info(f"Đã tải file thành công: {destination}")
            return True
    
    except Exception as e:
        logger.error(f"Lỗi khi tải file: {str(e)}")
        return False

def main():
    # Đường dẫn đến thư mục weights
    weights_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_models", "weights")
    os.makedirs(weights_dir, exist_ok=True)
    
    # URL của model YOLOv8n-face
    yolov8_url = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt"
    yolov8_path = os.path.join(weights_dir, "yolov8n-face.pt")
    
    # URL của model YOLOv11n-face
    yolov11_url = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt"
    yolov11_path = os.path.join(weights_dir, "yolov11n-face.pt")
    
    # Tải model YOLOv8n-face
    logger.info("=== Tải model YOLOv8n-face ===")
    if os.path.exists(yolov8_path):
        logger.info(f"Model YOLOv8n-face đã tồn tại tại {yolov8_path}")
    else:
        success = download_file(yolov8_url, yolov8_path)
        if success:
            logger.info(f"Đã tải model YOLOv8n-face thành công")
        else:
            logger.error(f"Không thể tải model YOLOv8n-face")
    
    # Tải model YOLOv11n-face
    logger.info("=== Tải model YOLOv11n-face ===")
    if os.path.exists(yolov11_path):
        logger.info(f"Model YOLOv11n-face đã tồn tại tại {yolov11_path}")
    else:
        success = download_file(yolov11_url, yolov11_path)
        if success:
            logger.info(f"Đã tải model YOLOv11n-face thành công")
        else:
            logger.error(f"Không thể tải model YOLOv11n-face")
    
    # Kiểm tra kết quả
    if os.path.exists(yolov8_path):
        logger.info(f"Model YOLOv8n-face có sẵn tại: {yolov8_path}")
        logger.info(f"Kích thước: {os.path.getsize(yolov8_path) / (1024 * 1024):.2f} MB")
    else:
        logger.error(f"Model YOLOv8n-face không có sẵn")
    
    if os.path.exists(yolov11_path):
        logger.info(f"Model YOLOv11n-face có sẵn tại: {yolov11_path}")
        logger.info(f"Kích thước: {os.path.getsize(yolov11_path) / (1024 * 1024):.2f} MB")
    else:
        logger.error(f"Model YOLOv11n-face không có sẵn")
    
    logger.info("=== Hoàn tất ===")

if __name__ == "__main__":
    main()
