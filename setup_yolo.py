"""
Script để cài đặt và cấu hình YOLOv11 cho phát hiện khuôn mặt
"""
import os
import sys
import subprocess
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Kiểm tra phiên bản Python"""
    logger.info("Kiểm tra phiên bản Python...")
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 trở lên là bắt buộc")
        sys.exit(1)
    logger.info(f"Phiên bản Python: {sys.version}")

def check_venv():
    """Kiểm tra môi trường ảo"""
    logger.info("Kiểm tra môi trường ảo...")
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        logger.warning("Không chạy trong môi trường ảo. Khuyến nghị sử dụng môi trường ảo.")
    else:
        logger.info(f"Đang chạy trong môi trường ảo: {sys.prefix}")

def install_python_packages():
    """Cài đặt các gói Python từ requirements.txt"""
    logger.info("Cài đặt các gói Python...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logger.info("Đã cài đặt các gói Python thành công!")
    except subprocess.CalledProcessError:
        logger.error("Lỗi khi cài đặt các gói Python. Vui lòng kiểm tra lỗi và thử lại.")
        sys.exit(1)

def check_ultralytics_installed():
    """Kiểm tra xem Ultralytics đã được cài đặt chưa"""
    try:
        import ultralytics
        logger.info(f"Ultralytics đã được cài đặt: {ultralytics.__version__}")
        return True
    except ImportError:
        logger.warning("Ultralytics chưa được cài đặt.")
        return False
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra Ultralytics: {e}")
        return False

def download_yolo_model():
    """Tải model YOLOv11 face từ GitHub"""
    try:
        from ultralytics import YOLO
        
        # Tạo thư mục cho model
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_models", "weights")
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, "yolov11x-face.pt")
        
        # Kiểm tra xem model đã tồn tại chưa
        if os.path.exists(model_path):
            logger.info(f"Model YOLOv11 face đã tồn tại tại {model_path}")
            return True
        
        # Tải model từ GitHub
        logger.info("Đang tải model YOLOv11n-face từ GitHub...")
        model = YOLO("yolov11x-face.pt")
        
        # Lưu model
        model.save(model_path)
        logger.info(f"Đã tải và lưu model YOLOv11 face tại {model_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi tải model YOLOv11 face: {str(e)}")
        return False

def main():
    logger.info("=== Cài đặt và cấu hình YOLOv11 cho phát hiện khuôn mặt ===")
    
    # Kiểm tra phiên bản Python
    check_python_version()
    
    # Kiểm tra môi trường ảo
    check_venv()
    
    # Cài đặt các gói Python
    install_python_packages()
    
    # Kiểm tra Ultralytics
    if check_ultralytics_installed():
        logger.info("Ultralytics đã được cài đặt.")
    else:
        logger.info("Ultralytics chưa được cài đặt.")
        logger.info("Đang cài đặt Ultralytics...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "ultralytics"], check=True)
            logger.info("Đã cài đặt Ultralytics thành công!")
        except subprocess.CalledProcessError:
            logger.error("Lỗi khi cài đặt Ultralytics. Vui lòng cài đặt thủ công:")
            logger.error("pip install ultralytics")
            sys.exit(1)
    
    # Tải model YOLOv11 face
    if download_yolo_model():
        logger.info("Đã tải model YOLOv11 face thành công!")
    else:
        logger.error("Lỗi khi tải model YOLOv11 face. Vui lòng thử lại sau.")
        sys.exit(1)
    
    logger.info("=== Cài đặt và cấu hình YOLOv11 hoàn tất ===")

if __name__ == "__main__":
    main()
