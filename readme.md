# Hướng dẫn cài đặt

## Cài đặt môi trường ảo (venv)

1. Tạo môi trường ảo:

    ```bash
    python -m venv venv
    ```

2. Kích hoạt môi trường ảo:

    ```bash
    # Windows
    venv\Scripts\activate

    # Linux/macOS
    source venv/bin/activate
    ```

## Cài đặt các gói Python cần thiết

1. Cài đặt các gói Python từ requirements.txt:
    ```bash
    pip install -r requirements.txt
    ```

## Cài đặt Tesseract OCR

1. Cài đặt Tesseract OCR:

    ```bash
    python setup_tesseract.py
    ```

2. Cài đặt ngôn ngữ tiếng Việt:
    ```bash
    python download_vie_language.py
    ```
3. Kiểm tra cài đặt:
    ```bash
    python test_tesseract.py
    ```

### Lưu ý quan trọng:

Tạo thêm thư mục `uploads` trong thư mục gốc của dự án

## Chạy ứng dụng

1. Chạy ứng dụng:
    ```bash
    python run.py
    ```
2. Truy cập ứng dụng tại:
    ```
    http://localhost:5000
    ```
