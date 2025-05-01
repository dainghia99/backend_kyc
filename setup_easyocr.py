import os
import sys
import platform
import subprocess
import shutil

def check_python_version():
    """Kiểm tra phiên bản Python"""
    if sys.version_info.major != 3 or sys.version_info.minor != 10:
        print(f"Cảnh báo: Script này được thiết kế cho Python 3.10, bạn đang sử dụng Python {sys.version_info.major}.{sys.version_info.minor}")
        input("Nhấn Enter để tiếp tục hoặc Ctrl+C để hủy...")

def check_venv():
    """Kiểm tra xem script có đang chạy trong môi trường ảo không"""
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("Cảnh báo: Bạn không đang chạy trong môi trường ảo (venv).")
        print("Khuyến nghị sử dụng môi trường ảo để tránh xung đột với các gói Python khác.")
        choice = input("Bạn có muốn tiếp tục không? (y/n): ")
        if choice.lower() != 'y':
            sys.exit(0)

def install_python_packages():
    """Cài đặt các gói Python từ requirements.txt"""
    print("\n=== Cài đặt các gói Python ===")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Đã cài đặt các gói Python thành công!")
    except subprocess.CalledProcessError:
        print("Lỗi khi cài đặt các gói Python. Vui lòng kiểm tra lỗi và thử lại.")
        sys.exit(1)

def check_easyocr_installed():
    """Kiểm tra xem EasyOCR đã được cài đặt chưa"""
    try:
        import easyocr
        print(f"EasyOCR đã được cài đặt: {easyocr.__version__}")
        return True
    except ImportError:
        print("EasyOCR chưa được cài đặt.")
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra EasyOCR: {e}")
        return False

def download_language_models():
    """Tải các mô hình ngôn ngữ cho EasyOCR"""
    print("\n=== Tải các mô hình ngôn ngữ cho EasyOCR ===")
    try:
        import easyocr
        # Khởi tạo reader sẽ tự động tải các mô hình ngôn ngữ
        print("Đang tải mô hình ngôn ngữ tiếng Việt và tiếng Anh...")
        reader = easyocr.Reader(['vi', 'en'], gpu=False)
        print("Đã tải các mô hình ngôn ngữ thành công!")
        return True
    except Exception as e:
        print(f"Lỗi khi tải mô hình ngôn ngữ: {e}")
        return False

def test_easyocr():
    """Kiểm tra cài đặt EasyOCR"""
    print("\n=== Kiểm tra cài đặt EasyOCR ===")
    try:
        from utils.easyocr_utils import test_easyocr
        if test_easyocr():
            print("EasyOCR hoạt động bình thường!")
            return True
        else:
            print(" EasyOCR không hoạt động đúng.")
            return False
    except Exception as e:
        print(f" Lỗi khi kiểm tra EasyOCR: {e}")
        return False

def main():
    print("=== Cài đặt và cấu hình EasyOCR ===")
    
    # Kiểm tra phiên bản Python
    check_python_version()
    
    # Kiểm tra môi trường ảo
    check_venv()
    
    # Cài đặt các gói Python
    install_python_packages()
    
    # Kiểm tra EasyOCR
    if check_easyocr_installed():
        print("EasyOCR đã được cài đặt.")
    else:
        print("\n EasyOCR chưa được cài đặt.")
        print("Đang cài đặt EasyOCR...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "easyocr"], check=True)
            print("Đã cài đặt EasyOCR thành công!")
        except subprocess.CalledProcessError:
            print("Lỗi khi cài đặt EasyOCR. Vui lòng cài đặt thủ công:")
            print("pip install easyocr")
            sys.exit(1)
    
    # Tải các mô hình ngôn ngữ
    download_language_models()
    
    # Kiểm tra cài đặt
    test_easyocr()
    
    print("\n=== Hoàn tất ===")
    print("Sau khi cài đặt EasyOCR, hãy khởi động lại máy chủ của bạn.")
    print("Chạy lệnh sau để khởi động máy chủ: python run.py")

if __name__ == "__main__":
    main()
