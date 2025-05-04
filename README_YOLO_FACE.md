# Hướng dẫn sử dụng YOLO Face Recognition

## Giới thiệu

Hệ thống xác thực khuôn mặt sử dụng YOLO (YOLOv8 hoặc YOLOv11) để phát hiện khuôn mặt, trích xuất đặc trưng và so sánh khuôn mặt. Hệ thống này thay thế hoàn toàn thư viện face_recognition và dlib, giúp cải thiện hiệu suất và độ chính xác.

## Cài đặt

### 1. Tải model YOLO face

Có hai cách để tải model YOLO face:

#### Cách 1: Sử dụng script download_yolo_model.py

```bash
python download_yolo_model.py
```

Script này sẽ tải model YOLOv8n-face và YOLOv11n-face từ GitHub và lưu vào thư mục `verification_models/weights`.

#### Cách 2: Tải thủ công

Bạn có thể tải model YOLOv8n-face hoặc YOLOv11n-face từ GitHub và lưu vào thư mục `verification_models/weights`:

- YOLOv8n-face: [https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt](https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt)
- YOLOv11n-face: [https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt](https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt)

### 2. Cài đặt các gói Python cần thiết

```bash
pip install -r requirements.txt
```

## Kiểm thử

### 1. Kiểm thử phát hiện khuôn mặt

```bash
python test_pure_yolo.py --mode detection --image path/to/image.jpg
```

### 2. Kiểm thử xác thực khuôn mặt

```bash
python test_pure_yolo.py --mode verification --id-card path/to/id_card.jpg --selfie path/to/selfie.jpg
```

## Cấu hình

Bạn có thể điều chỉnh ngưỡng dung sai cho việc so sánh khuôn mặt bằng cách cấu hình trong file `.env`:

```
FACE_MATCH_TOLERANCE=0.45  # Giá trị mặc định
```

Giá trị thấp hơn sẽ nghiêm ngặt hơn, giá trị cao hơn sẽ dễ dàng hơn.

## Xử lý lỗi

### Lỗi khi tải model YOLO face

Nếu bạn gặp lỗi khi tải model YOLO face:

```
[Errno 2] No such file or directory: 'yolov11n-face.pt'
```

Hãy thử các cách sau:

1. Chạy script download_yolo_model.py để tải model:

```bash
python download_yolo_model.py
```

2. Tải model thủ công và lưu vào thư mục `verification_models/weights`.

3. Kiểm tra kết nối internet của bạn.

### Lỗi CUDA

Nếu bạn gặp lỗi liên quan đến CUDA, hãy thử các cách sau:

1. Kiểm tra xem CUDA đã được cài đặt chưa:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

2. Nếu CUDA không khả dụng, hệ thống sẽ tự động sử dụng CPU.

## Lưu ý

- Hệ thống sẽ tự động chọn YOLOv8n-face nếu có sẵn, nếu không sẽ thử tải YOLOv11n-face.
- Nếu không tải được cả hai model, hệ thống sẽ thử sử dụng script download_yolo_model.py để tải model.
- Nếu vẫn không tải được, hãy tải model thủ công và lưu vào thư mục `verification_models/weights`.
