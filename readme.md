# Hướng dẫn cài đặt

## Cài đặt môi trường ảo (venv)

## Khuyến khích sử dụng `Python 3.10`

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

## Cài đặt EasyOCR (Khuyến nghị)

1. Cài đặt EasyOCR và tải mô hình ngôn ngữ:

    ```bash
    python setup_easyocr.py
    ```

2. Kiểm tra cài đặt:

    ```bash
    python test_easyocr.py
    ```

3. Để biết thêm thông tin, xem tài liệu EasyOCR:
    ```bash
    cat README_EASYOCR.md
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
