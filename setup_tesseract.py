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
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Cảnh báo: Bạn không đang chạy trong môi trường ảo (venv).")
        print("Khuyến nghị: Kích hoạt môi trường ảo trước khi chạy script này.")
        input("Nhấn Enter để tiếp tục hoặc Ctrl+C để hủy...")

def install_python_packages():
    """Cài đặt các gói Python từ requirements.txt"""
    print("\n=== Cài đặt các gói Python ===")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Đã cài đặt các gói Python thành công!")
    except subprocess.CalledProcessError:
        print("❌ Lỗi khi cài đặt các gói Python. Vui lòng kiểm tra lỗi và thử lại.")
        sys.exit(1)

def check_tesseract_installed():
    """Kiểm tra xem Tesseract đã được cài đặt chưa"""
    try:
        result = subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "tesseract" in result.stdout.lower():
            print(f"✅ Tesseract OCR đã được cài đặt: {result.stdout.splitlines()[0]}")
            return True
    except FileNotFoundError:
        pass
    return False

def install_tesseract_windows():
    """Hướng dẫn cài đặt Tesseract trên Windows"""
    print("\n=== Cài đặt Tesseract OCR trên Windows ===")
    print("1. Tải Tesseract OCR từ: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Chọn phiên bản phù hợp (tesseract-ocr-w64-setup-v5.x.x.exe cho 64-bit)")
    print("3. Trong quá trình cài đặt, chọn thêm ngôn ngữ tiếng Việt")
    print("4. Đảm bảo thêm Tesseract vào PATH hệ thống")
    print("5. Đường dẫn mặc định: C:\\Program Files\\Tesseract-OCR")
    
    # Kiểm tra xem Tesseract đã được thêm vào PATH chưa
    path_var = os.environ.get('PATH', '')
    if 'tesseract' in path_var.lower() or 'tesseract-ocr' in path_var.lower():
        print("✅ Tesseract có vẻ đã được thêm vào PATH.")
    else:
        print("⚠️ Không tìm thấy Tesseract trong PATH. Hãy đảm bảo thêm nó vào PATH.")
        print("   Ví dụ: C:\\Program Files\\Tesseract-OCR")

def install_tesseract_linux():
    """Cài đặt Tesseract trên Linux"""
    print("\n=== Cài đặt Tesseract OCR trên Linux ===")
    
    # Kiểm tra distro
    if os.path.exists('/etc/debian_version'):  # Debian, Ubuntu, etc.
        print("Phát hiện hệ điều hành dựa trên Debian/Ubuntu")
        try:
            print("Cài đặt Tesseract OCR và ngôn ngữ tiếng Việt...")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "tesseract-ocr"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "tesseract-ocr-vie"], check=True)
            print("✅ Đã cài đặt Tesseract OCR thành công!")
        except subprocess.CalledProcessError:
            print("❌ Lỗi khi cài đặt Tesseract. Vui lòng cài đặt thủ công:")
            print("   sudo apt update")
            print("   sudo apt install -y tesseract-ocr")
            print("   sudo apt install -y tesseract-ocr-vie")
    elif os.path.exists('/etc/fedora-release') or os.path.exists('/etc/redhat-release'):  # Fedora, RHEL, CentOS
        print("Phát hiện hệ điều hành dựa trên Fedora/RHEL/CentOS")
        try:
            print("Cài đặt Tesseract OCR và ngôn ngữ tiếng Việt...")
            subprocess.run(["sudo", "dnf", "install", "-y", "tesseract"], check=True)
            subprocess.run(["sudo", "dnf", "install", "-y", "tesseract-langpack-vie"], check=True)
            print("✅ Đã cài đặt Tesseract OCR thành công!")
        except subprocess.CalledProcessError:
            print("❌ Lỗi khi cài đặt Tesseract. Vui lòng cài đặt thủ công:")
            print("   sudo dnf install -y tesseract")
            print("   sudo dnf install -y tesseract-langpack-vie")
    else:
        print("⚠️ Không thể xác định bản phân phối Linux. Vui lòng cài đặt Tesseract thủ công.")
        print("   Tham khảo: https://tesseract-ocr.github.io/tessdoc/Installation.html")

def install_tesseract_macos():
    """Cài đặt Tesseract trên macOS"""
    print("\n=== Cài đặt Tesseract OCR trên macOS ===")
    
    # Kiểm tra xem Homebrew đã được cài đặt chưa
    try:
        subprocess.run(["brew", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ Homebrew đã được cài đặt.")
        
        try:
            print("Cài đặt Tesseract OCR và ngôn ngữ tiếng Việt...")
            subprocess.run(["brew", "install", "tesseract"], check=True)
            subprocess.run(["brew", "install", "tesseract-lang"], check=True)
            print("✅ Đã cài đặt Tesseract OCR thành công!")
        except subprocess.CalledProcessError:
            print("❌ Lỗi khi cài đặt Tesseract. Vui lòng cài đặt thủ công:")
            print("   brew install tesseract")
            print("   brew install tesseract-lang")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Homebrew chưa được cài đặt. Vui lòng cài đặt Homebrew trước:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("   Sau đó chạy lại script này.")

def create_test_script():
    """Tạo script kiểm tra Tesseract"""
    test_script = """
import pytesseract
from PIL import Image
import sys

def test_tesseract():
    try:
        # Kiểm tra phiên bản Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR phiên bản: {version}")
        
        # Kiểm tra các ngôn ngữ có sẵn
        langs = pytesseract.get_languages()
        print(f"Các ngôn ngữ có sẵn: {langs}")
        
        # Kiểm tra xem tiếng Việt có sẵn không
        if 'vie' in langs:
            print("✅ Ngôn ngữ tiếng Việt (vie) đã được cài đặt.")
        else:
            print("⚠️ Ngôn ngữ tiếng Việt (vie) chưa được cài đặt.")
            print("   Vui lòng cài đặt thêm gói ngôn ngữ tiếng Việt.")
        
        print("\\nTesseract OCR đã được cài đặt và cấu hình đúng! 🎉")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra Tesseract: {e}")
        
        # Kiểm tra đường dẫn Tesseract
        try:
            tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            print(f"\\nĐường dẫn Tesseract hiện tại: {tesseract_cmd}")
        except:
            print("\\nKhông thể xác định đường dẫn Tesseract.")
        
        print("\\nGợi ý khắc phục:")
        print("1. Đảm bảo Tesseract OCR đã được cài đặt")
        print("2. Đảm bảo Tesseract đã được thêm vào PATH hệ thống")
        print("3. Hoặc thiết lập đường dẫn Tesseract trong code:")
        print("   pytesseract.pytesseract.tesseract_cmd = r'C:\\\\Program Files\\\\Tesseract-OCR\\\\tesseract.exe'  # Windows")
        print("   pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/macOS")
        return False

if __name__ == "__main__":
    test_tesseract()
"""
    
    with open("test_tesseract.py", "w") as f:
        f.write(test_script)
    
    print("\n✅ Đã tạo script kiểm tra Tesseract: test_tesseract.py")
    print("   Chạy script này để kiểm tra cài đặt Tesseract: python test_tesseract.py")

def main():
    print("=== Cài đặt Tesseract OCR và các thư viện Python ===")
    
    # Kiểm tra phiên bản Python
    check_python_version()
    
    # Kiểm tra môi trường ảo
    check_venv()
    
    # Cài đặt các gói Python
    install_python_packages()
    
    # Kiểm tra Tesseract
    if check_tesseract_installed():
        print("Tesseract OCR đã được cài đặt.")
    else:
        print("\n⚠️ Tesseract OCR chưa được cài đặt hoặc không có trong PATH.")
        
        # Cài đặt Tesseract dựa trên hệ điều hành
        system = platform.system()
        if system == "Windows":
            install_tesseract_windows()
        elif system == "Linux":
            install_tesseract_linux()
        elif system == "Darwin":  # macOS
            install_tesseract_macos()
        else:
            print(f"⚠️ Hệ điều hành không được hỗ trợ: {system}")
            print("   Vui lòng cài đặt Tesseract OCR thủ công.")
    
    # Tạo script kiểm tra
    create_test_script()
    
    print("\n=== Hoàn tất ===")
    print("Sau khi cài đặt Tesseract OCR, hãy khởi động lại máy chủ của bạn.")
    print("Chạy script kiểm tra để xác nhận cài đặt: python test_tesseract.py")

if __name__ == "__main__":
    main()
