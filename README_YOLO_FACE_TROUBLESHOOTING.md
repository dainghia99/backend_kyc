# Xử lý lỗi khi tải model YOLO face

## Lỗi thường gặp

### 1. Lỗi "No such file or directory: 'yolov8n-face.pt'" hoặc "No such file or directory: 'yolov11n-face.pt'"

Lỗi này xảy ra khi hệ thống không thể tìm thấy file model YOLO face. Có hai nguyên nhân chính:

1. **Model chưa được tải về**: Hệ thống đang cố gắng tải model từ internet nhưng không thành công.
2. **Đường dẫn không chính xác**: Hệ thống đang tìm model ở sai vị trí.

## Giải pháp

### Cách 1: Tải model trực tiếp bằng script download_yolo_model_direct.py

Script này sẽ tải model trực tiếp từ GitHub mà không thông qua thư viện ultralytics:

```bash
python download_yolo_model_direct.py
```

### Cách 2: Tạo thư mục weights và tải model thủ công

1. Tạo thư mục `verification_models/weights` nếu chưa tồn tại:

```bash
mkdir -p verification_models/weights
```

2. Tải model YOLOv8n-face và YOLOv11n-face từ GitHub:

- YOLOv8n-face: [https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt](https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt)
- YOLOv11n-face: [https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt](https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt)

3. Lưu các file model vào thư mục `verification_models/weights`.

### Cách 3: Sửa đổi code để tải model từ đường dẫn cụ thể

Nếu bạn đã tải model nhưng hệ thống vẫn không tìm thấy, bạn có thể sửa đổi code để chỉ định đường dẫn cụ thể:

1. Mở file `verification_models/yolo_face_recognition.py`
2. Tìm dòng `self.model = YOLO("yolov8n-face.pt")`
3. Thay thế bằng đường dẫn đầy đủ đến file model:

```python
self.model = YOLO("/đường/dẫn/đầy/đủ/đến/yolov8n-face.pt")
```

### Cách 4: Kiểm tra cấu trúc thư mục

Đảm bảo rằng cấu trúc thư mục của bạn như sau:

```
backend/
├── verification_models/
│   ├── weights/
│   │   ├── yolov8n-face.pt
│   │   └── yolov11n-face.pt
│   └── yolo_face_recognition.py
└── ...
```

## Kiểm tra sau khi khắc phục

Sau khi tải model thành công, bạn có thể kiểm tra bằng cách chạy:

```bash
python test_pure_yolo.py --mode detection --image uploads/id_card_29_front_20250503_165630.jpg
```

## Lưu ý

- Hệ thống đã được cập nhật để sử dụng YOLOv8n-face thay vì YOLOv11n-face, vì YOLOv8n-face ổn định hơn và dễ tải hơn.
- Nếu bạn vẫn muốn sử dụng YOLOv11n-face, hãy đảm bảo rằng file model đã được tải và lưu đúng vị trí.
- Nếu bạn gặp lỗi "CUDA out of memory", hãy thử giảm kích thước ảnh hoặc sử dụng CPU thay vì GPU.
