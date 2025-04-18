import os
import sys
import platform
import subprocess
import requests
import shutil

def download_vie_language():
    """Tải và cài đặt file ngôn ngữ tiếng Việt cho Tesseract OCR"""
    print("=== Tải và cài đặt file ngôn ngữ tiếng Việt cho Tesseract OCR ===")
    
    # URL của file vie.traineddata
    url = "https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata"
    
    # Tìm thư mục tessdata
    tessdata_path = find_tessdata_dir()
    if not tessdata_path:
        print("❌ Không tìm thấy thư mục tessdata. Vui lòng cài đặt Tesseract OCR trước.")
        return False
    
    # Tạo thư mục tessdata nếu chưa tồn tại
    os.makedirs(tessdata_path, exist_ok=True)
    
    # Đường dẫn đến file vie.traineddata
    vie_file = os.path.join(tessdata_path, "vie.traineddata")
    
    # Kiểm tra xem file đã tồn tại chưa
    if os.path.exists(vie_file):
        print(f"✅ File ngôn ngữ tiếng Việt đã tồn tại: {vie_file}")
        overwrite = input("Bạn có muốn tải lại file này không? (y/n): ")
        if overwrite.lower() != 'y':
            return True
    
    print(f"Đang tải file ngôn ngữ tiếng Việt từ {url}...")
    try:
        # Tải file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Lưu file
        with open(vie_file, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        
        print(f"✅ Đã tải và lưu file ngôn ngữ tiếng Việt vào: {vie_file}")
        
        # Thiết lập biến môi trường TESSDATA_PREFIX
        set_tessdata_prefix(tessdata_path)
        
        return True
    except Exception as e:
        print(f"❌ Lỗi khi tải file ngôn ngữ tiếng Việt: {e}")
        return False

def find_tessdata_dir():
    """Tìm thư mục tessdata dựa trên cài đặt Tesseract OCR"""
    system = platform.system()
    
    if system == "Windows":
        # Kiểm tra các đường dẫn phổ biến trên Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tessdata',
            r'C:\Program Files (x86)\Tesseract-OCR\tessdata',
            r'C:\Tesseract-OCR\tessdata'
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.dirname(path)):
                return path
        
        # Tìm trong PATH
        try:
            result = subprocess.run(["where", "tesseract"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            if result.returncode == 0 and result.stdout:
                tesseract_path = result.stdout.strip().split('\n')[0]
                return os.path.join(os.path.dirname(tesseract_path), 'tessdata')
        except:
            pass
    else:
        # Linux/macOS
        try:
            result = subprocess.run(["which", "tesseract"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            if result.returncode == 0 and result.stdout:
                tesseract_path = result.stdout.strip()
                # Thường là /usr/bin/tesseract, nên tessdata có thể ở /usr/share/tesseract-ocr/tessdata
                if os.path.exists('/usr/share/tesseract-ocr/tessdata'):
                    return '/usr/share/tesseract-ocr/tessdata'
                elif os.path.exists('/usr/share/tessdata'):
                    return '/usr/share/tessdata'
        except:
            pass
    
    # Nếu không tìm thấy, hỏi người dùng
    print("Không tìm thấy thư mục tessdata tự động.")
    custom_path = input("Vui lòng nhập đường dẫn đến thư mục tessdata (hoặc nhấn Enter để bỏ qua): ")
    if custom_path and os.path.exists(os.path.dirname(custom_path)):
        return custom_path
    
    return None

def set_tessdata_prefix(tessdata_path):
    """Thiết lập biến môi trường TESSDATA_PREFIX"""
    system = platform.system()
    
    print(f"Thiết lập biến môi trường TESSDATA_PREFIX = {tessdata_path}")
    
    # Thiết lập biến môi trường cho phiên làm việc hiện tại
    os.environ['TESSDATA_PREFIX'] = tessdata_path
    
    if system == "Windows":
        try:
            # Thiết lập biến môi trường vĩnh viễn trên Windows
            subprocess.run(["setx", "TESSDATA_PREFIX", tessdata_path, "/M"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            print("✅ Đã thiết lập biến môi trường TESSDATA_PREFIX vĩnh viễn.")
            print("⚠️ Vui lòng khởi động lại máy tính để áp dụng thay đổi.")
        except:
            print("❌ Không thể thiết lập biến môi trường vĩnh viễn. Vui lòng thiết lập thủ công.")
            print(f"Thêm TESSDATA_PREFIX={tessdata_path} vào biến môi trường hệ thống.")
    else:
        # Linux/macOS
        print("Để thiết lập biến môi trường vĩnh viễn trên Linux/macOS, thêm dòng sau vào ~/.bashrc hoặc ~/.zshrc:")
        print(f"export TESSDATA_PREFIX={tessdata_path}")

def test_tesseract():
    """Kiểm tra cài đặt Tesseract OCR và ngôn ngữ tiếng Việt"""
    print("\n=== Kiểm tra cài đặt Tesseract OCR và ngôn ngữ tiếng Việt ===")
    
    try:
        import pytesseract
        from PIL import Image
        
        # Kiểm tra phiên bản Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR phiên bản: {version}")
        
        # Kiểm tra các ngôn ngữ có sẵn
        langs = pytesseract.get_languages()
        print(f"Các ngôn ngữ có sẵn: {langs}")
        
        # Kiểm tra xem tiếng Việt có sẵn không
        if 'vie' in langs:
            print("✅ Ngôn ngữ tiếng Việt (vie) đã được cài đặt.")
            return True
        else:
            print("❌ Ngôn ngữ tiếng Việt (vie) chưa được cài đặt.")
            return False
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra Tesseract OCR: {e}")
        return False

if __name__ == "__main__":
    if download_vie_language():
        print("\n✅ Đã tải và cài đặt file ngôn ngữ tiếng Việt thành công!")
        test_tesseract()
    else:
        print("\n❌ Không thể tải và cài đặt file ngôn ngữ tiếng Việt.")
        print("Vui lòng tải thủ công từ: https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata")
        print("Và lưu vào thư mục tessdata của Tesseract OCR.")
