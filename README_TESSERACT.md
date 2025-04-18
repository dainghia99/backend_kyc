# Hướng dẫn cài đặt Tesseract OCR

Dự án này sử dụng Tesseract OCR để trích xuất thông tin từ ảnh CCCD. Dưới đây là hướng dẫn cài đặt Tesseract OCR cho các hệ điều hành khác nhau.

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

## Kiểm tra cài đặt

Sau khi cài đặt, bạn có thể kiểm tra xem Tesseract OCR đã được cài đặt đúng chưa bằng cách chạy:

```bash
tesseract --version
```

Nếu lệnh trên hiển thị phiên bản Tesseract, điều đó có nghĩa là Tesseract đã được cài đặt thành công.

Để kiểm tra xem ngôn ngữ tiếng Việt đã được cài đặt chưa, bạn có thể chạy:

```bash
tesseract --list-langs
```

Nếu `vie` xuất hiện trong danh sách, điều đó có nghĩa là ngôn ngữ tiếng Việt đã được cài đặt.

## Kiểm tra với Python

Chạy script kiểm tra để xác nhận Tesseract OCR đã được cài đặt đúng và hoạt động với Python:

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

### Thiếu ngôn ngữ tiếng Việt

Nếu bạn gặp lỗi liên quan đến ngôn ngữ tiếng Việt, hãy sử dụng script tự động tải và cài đặt:

```bash
python download_vie_language.py
```

Hoặc cài đặt thủ công:

-   **Windows**:

    1. Tải file `vie.traineddata` từ [GitHub Tesseract](https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata)
    2. Lưu vào thư mục `C:\Program Files\Tesseract-OCR\tessdata\`
    3. Thiết lập biến môi trường `TESSDATA_PREFIX` trỏ đến thư mục `tessdata`:
        ```
        setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata" /M
        ```
    4. Khởi động lại máy tính

-   **Linux**:

    ```bash
    sudo apt install tesseract-ocr-vie   # Ubuntu/Debian
    sudo dnf install tesseract-langpack-vie   # Fedora/RHEL/CentOS
    ```

-   **macOS**:
    ```bash
    brew install tesseract-lang
    ```

### Lỗi "Failed loading language 'vie'" hoặc "TESSDATA_PREFIX"

Nếu bạn gặp lỗi liên quan đến TESSDATA_PREFIX hoặc không tải được ngôn ngữ, hãy thử các bước sau:

1. Thiết lập biến môi trường TESSDATA_PREFIX trỏ đến thư mục chứa file `vie.traineddata`:

    ```
    # Windows (Command Prompt với quyền Administrator)
    setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata" /M

    # Linux/macOS
    export TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata  # hoặc đường dẫn phù hợp
    ```

2. Khởi động lại máy tính hoặc terminal

3. Chạy script `download_vie_language.py` để tải và cài đặt file ngôn ngữ tiếng Việt

## Tài liệu tham khảo

-   [Trang chủ Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
-   [Tài liệu pytesseract](https://pypi.org/project/pytesseract/)
-   [Hướng dẫn cài đặt Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)
