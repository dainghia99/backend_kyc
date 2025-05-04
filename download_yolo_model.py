"""
Script để tải model YOLOv11 face từ GitHub
"""
import os
import sys
import logging
import requests
import torch
from tqdm import tqdm

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_file(url, destination):
    """
    Tải file từ URL và lưu vào destination
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Lấy kích thước file
        total_size = int(response.headers.get('content-length', 0))
        
        # Tạo thư mục chứa file nếu chưa tồn tại
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Tải file với thanh tiến trình
        with open(destination, 'wb') as f:
            logger.info(f"Đang tải file từ {url} vào {destination}")
            
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(destination)) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"Đã tải file thành công: {destination}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi tải file: {str(e)}")
        return False

def download_yolo_model(model_name="yolov8n-face.pt"):
    """
    Tải model YOLO face từ GitHub
    
    Args:
        model_name: Tên model (yolov8n-face.pt, yolov11n-face.pt, etc.)
    """
    try:
        # Tạo thư mục cho model
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_models", "weights")
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, model_name)
        
        # Kiểm tra xem model đã tồn tại chưa
        if os.path.exists(model_path):
            logger.info(f"Model {model_name} đã tồn tại tại {model_path}")
            return model_path
        
        # URL của model
        if model_name == "yolov8n-face.pt":
            # YOLOv8n-face từ akanametov/yolo-face
            url = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt"
        elif model_name == "yolov11n-face.pt":
            # YOLOv11n-face từ akanametov/yolo-face
            url = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt"
        else:
            logger.error(f"Model {model_name} không được hỗ trợ")
            return None
        
        # Tải model
        success = download_file(url, model_path)
        
        if success:
            logger.info(f"Đã tải model {model_name} thành công")
            return model_path
        else:
            logger.error(f"Không thể tải model {model_name}")
            return None
    
    except Exception as e:
        logger.error(f"Lỗi khi tải model {model_name}: {str(e)}")
        return None

def main():
    # Kiểm tra xem CUDA có khả dụng không
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA available: {cuda_available}")
    
    # Tải model YOLOv8n-face
    yolov8_path = download_yolo_model("yolov8n-face.pt")
    
    # Tải model YOLOv11n-face
    yolov11_path = download_yolo_model("yolov11n-face.pt")
    
    if yolov8_path:
        logger.info(f"Model YOLOv8n-face đã được tải tại: {yolov8_path}")
    else:
        logger.error("Không thể tải model YOLOv8n-face")
    
    if yolov11_path:
        logger.info(f"Model YOLOv11n-face đã được tải tại: {yolov11_path}")
    else:
        logger.error("Không thể tải model YOLOv11n-face")

if __name__ == "__main__":
    main()
