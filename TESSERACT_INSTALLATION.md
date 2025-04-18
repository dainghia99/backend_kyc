# Hướng dẫn cài đặt Tesseract OCR

Tài liệu này hướng dẫn cách cài đặt Tesseract OCR và cấu hình nó để hoạt động với ứng dụng Python của bạn.

## Cài đặt tự động

Chúng tôi đã cung cấp script tự động hóa quá trình cài đặt. Để sử dụng:

1. Kích hoạt môi trường ảo của bạn:
   ```
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

2. Chạy script cài đặt:
   ```
   python setup_tesseract.py
   ```

3. Làm theo hướng dẫn trên màn hình.

4. Sau khi cài đặt, kiểm tra cài đặt:
   ```
   python test_tesseract.py
   ```

## Cài đặt thủ công

Nếu script tự động không hoạt động, bạn có thể cài đặt thủ công theo các bước sau:

### Windows

1. Tải Tesseract OCR từ trang chính thức: https://github.com/UB-Mannheim/tesseract/wiki
2. Chọn phiên bản phù hợp (thường là tesseract-ocr-w64-setup-v5.x.x.exe cho hệ thống 64-bit)
3. Trong quá trình cài đặt, chọn thêm ngôn ngữ tiếng Việt (vie)
4. Đảm bảo chọn tùy chọn "Add to PATH" trong quá trình cài đặt
5. Đường dẫn mặc định: `C:\Program Files\Tesseract-OCR`
6. Khởi động lại máy tính sau khi cài đặt

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y tesseract-ocr
sudo apt install -y tesseract-ocr-vie
```

### Linux (Fedora/RHEL/CentOS)

```bash
sudo dnf install -y tesseract
sudo dnf install -y tesseract-langpack-vie
```

### macOS

```bash
brew install tesseract
brew install tesseract-lang
```

## Cài đặt các gói Python cần thiết

Sau khi cài đặt Tesseract OCR, cài đặt các gói Python cần thiết:

```bash
pip install -r requirements.txt
```

## Kiểm tra cài đặt

Chạy script kiểm tra để xác nhận Tesseract OCR đã được cài đặt đúng:

```bash
python test_tesseract.py
```

## Khắc phục sự cố

### Tesseract không được tìm thấy trong PATH

Nếu bạn gặp lỗi "tesseract is not installed or it's not in your PATH", bạn cần chỉ định đường dẫn đến Tesseract trong code Python:

```python
import pytesseract

# Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Linux/macOS
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
```

Thêm đoạn code này vào file xử lý OCR của bạn.

### Thiếu ngôn ngữ tiếng Việt

Nếu bạn gặp lỗi liên quan đến ngôn ngữ tiếng Việt, hãy đảm bảo bạn đã cài đặt gói ngôn ngữ tiếng Việt:

- Windows: Chạy lại trình cài đặt và chọn ngôn ngữ tiếng Việt
- Linux: `sudo apt install tesseract-ocr-vie` hoặc `sudo dnf install tesseract-langpack-vie`
- macOS: `brew install tesseract-lang`

## Cấu hình trong ứng dụng

Để đảm bảo ứng dụng của bạn luôn tìm thấy Tesseract, bạn có thể thêm đoạn code sau vào file xử lý OCR:

```python
import os
import platform
import pytesseract

def configure_tesseract():
    """Cấu hình đường dẫn Tesseract dựa trên hệ điều hành"""
    system = platform.system()
    
    if system == "Windows":
        # Kiểm tra các đường dẫn phổ biến trên Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
                
    # Kiểm tra xem Tesseract có trong PATH không
    try:
        import subprocess
        subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Gọi hàm cấu hình
configure_tesseract()
```

Thêm đoạn code này vào file xử lý OCR của bạn để tự động tìm và cấu hình Tesseract.

## Tài liệu tham khảo

- [Trang chủ Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Tài liệu pytesseract](https://pypi.org/project/pytesseract/)
- [Hướng dẫn cài đặt Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)
