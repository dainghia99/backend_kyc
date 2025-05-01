# Hướng dẫn cài đặt EasyOCR

Dự án này sử dụng EasyOCR để trích xuất thông tin từ ảnh CCCD. Dưới đây là hướng dẫn cài đặt EasyOCR cho các hệ điều hành khác nhau.

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
    python setup_easyocr.py
    ```

3. Làm theo hướng dẫn trên màn hình.

4. Sau khi cài đặt, kiểm tra cài đặt:
    ```
    python test_easyocr.py
    ```

## Cài đặt thủ công

### Cài đặt các gói Python cần thiết

```bash
pip install easyocr torch torchvision opencv-python
```

### Kiểm tra cài đặt

Sau khi cài đặt, bạn có thể kiểm tra xem EasyOCR đã được cài đặt đúng chưa bằng cách chạy:

```bash
python test_easyocr.py
```

## Ưu điểm của EasyOCR so với Tesseract OCR

1. **Độ chính xác cao hơn**: EasyOCR sử dụng mô hình học sâu (deep learning) để nhận dạng văn bản, mang lại độ chính xác cao hơn đặc biệt với tiếng Việt.

2. **Khả năng nhận dạng tốt hơn trong điều kiện khó**: EasyOCR hoạt động tốt hơn với ảnh có chất lượng thấp, góc nghiêng, hoặc ánh sáng không đều.

3. **Hỗ trợ nhiều ngôn ngữ**: EasyOCR hỗ trợ hơn 80 ngôn ngữ, bao gồm tiếng Việt với chất lượng tốt.

4. **Dễ sử dụng**: API của EasyOCR đơn giản và dễ sử dụng hơn Tesseract OCR.

5. **Không cần cài đặt phức tạp**: Không cần cài đặt phần mềm bên ngoài như Tesseract, tất cả được cài đặt thông qua pip.

## Khắc phục sự cố

### Lỗi khi cài đặt PyTorch

Nếu bạn gặp lỗi khi cài đặt PyTorch, bạn có thể cài đặt phiên bản phù hợp với hệ thống của bạn từ trang web chính thức: https://pytorch.org/get-started/locally/

### Lỗi khi tải mô hình ngôn ngữ

Nếu bạn gặp lỗi khi tải mô hình ngôn ngữ, hãy đảm bảo bạn có kết nối internet ổn định. Các mô hình ngôn ngữ sẽ được tải tự động khi bạn khởi tạo EasyOCR Reader lần đầu tiên.

### Lỗi CUDA

Nếu bạn gặp lỗi liên quan đến CUDA, bạn có thể tắt GPU bằng cách sử dụng tham số `gpu=False` khi khởi tạo Reader:

```python
reader = easyocr.Reader(['vi', 'en'], gpu=False)
```

### Lỗi bộ nhớ

EasyOCR có thể sử dụng nhiều bộ nhớ, đặc biệt là khi xử lý ảnh lớn. Nếu bạn gặp lỗi bộ nhớ, hãy thử:

1. Giảm kích thước ảnh trước khi xử lý
2. Sử dụng `gpu=False` để tránh sử dụng bộ nhớ GPU
3. Đóng và khởi động lại ứng dụng để giải phóng bộ nhớ

## Tài liệu tham khảo

- [Trang chủ EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [Tài liệu EasyOCR](https://www.jaided.ai/easyocr/documentation/)
- [PyTorch](https://pytorch.org/)
