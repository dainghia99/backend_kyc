import cv2
import numpy as np
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
import os
import time

# Khởi tạo face detector và facial landmark predictor
face_detector = dlib.get_frontal_face_detector()
predictor_path = os.path.join(os.path.dirname(__file__), 'models', 'shape_predictor_68_face_landmarks.dat')
landmark_predictor = dlib.shape_predictor(predictor_path)

def eye_aspect_ratio(eye):
    # Tính tỉ lệ khung mắt dựa trên landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def detect_blinks(video_path):
    EYE_AR_THRESH = 0.25  # Ngưỡng để xác định mắt nhắm
    EYE_AR_CONSEC_FRAMES = 2  # Số frame liên tiếp để xác định nháy mắt

    # Đọc video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Tạo thư mục debug để lưu các frame đã xử lý
    debug_dir = os.path.join(os.path.dirname(video_path), "debug_frames")
    os.makedirs(debug_dir, exist_ok=True)

    blink_counter = 0
    counter = 0
    total_ear = 0
    frame_count = 0
    face_detected_frames = 0

    # Danh sách lưu các frame có khuôn mặt để xử lý
    face_frames = []

    # Đọc tất cả các frame trước
    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Tăng kích thước frame để có độ phân giải tốt hơn
        frame = cv2.resize(frame, (640, 640))

        # Cải thiện độ tương phản và độ sáng
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)

        # Phát hiện khuôn mặt
        faces = face_detector(gray, 0)

        # Lưu frame có khuôn mặt để xử lý
        if len(faces) > 0:
            face_detected_frames += 1
            face_frames.append((frame_index, enhanced_frame, gray, faces))

            # Lưu frame để debug (chỉ lưu một số frame)
            if frame_index % 5 == 0:
                cv2.imwrite(os.path.join(debug_dir, f"frame_{frame_index}.jpg"), enhanced_frame)

        frame_index += 1

    # Đóng video sau khi đọc xong
    cap.release()

    # Nếu không phát hiện đủ frame có khuôn mặt
    if face_detected_frames < 10:
        print(f"Chỉ phát hiện được {face_detected_frames} frame có khuôn mặt, không đủ để phân tích")
        return {
            'liveness_score': 0.0,
            'blink_count': 0,
            'avg_ear': 0.0,
            'blink_rate': 0.0,
            'face_detected_frames': face_detected_frames
        }

    # Xử lý các frame có khuôn mặt để phát hiện nháy mắt
    for frame_index, enhanced_frame, gray, faces in face_frames:
        for face in faces:
            # Phát hiện facial landmarks
            shape = landmark_predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            # Lấy tọa độ của mắt
            (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]

            # Tính EAR cho cả 2 mắt
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            # Lưu debug thông tin EAR
            if frame_index % 5 == 0:
                # Vẽ đường viền mắt để debug
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(enhanced_frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(enhanced_frame, [rightEyeHull], -1, (0, 255, 0), 1)

                # Hiển thị giá trị EAR
                cv2.putText(enhanced_frame, f"EAR: {ear:.2f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Lưu frame đã được chỉnh sửa
                cv2.imwrite(os.path.join(debug_dir, f"eye_frame_{frame_index}.jpg"), enhanced_frame)

            total_ear += ear
            frame_count += 1

            if ear < EYE_AR_THRESH:
                counter += 1
            else:
                if counter >= EYE_AR_CONSEC_FRAMES:
                    blink_counter += 1
                counter = 0

    cap.release()

    # Tính điểm số liveness
    avg_ear = total_ear / frame_count if frame_count > 0 else 0
    duration = total_frames / fps
    blink_rate = blink_counter / duration if duration > 0 else 0

    # Tính điểm số dựa trên các yếu tố:
    # 1. Số lần nháy mắt (2-5 lần trong 5 giây là bình thường)
    # 2. Tỉ lệ khung mắt trung bình (0.2-0.35 là bình thường)
    # 3. Tần suất nháy mắt (0.2-0.4 lần/giây là bình thường)
    # 4. Tỉ lệ frame phát hiện được khuôn mặt (càng cao càng tốt)

    # Điều chỉnh ngưỡng nháy mắt dựa trên độ dài video
    min_blinks = max(1, int(duration / 2.5))  # Ít nhất 1 nháy mắt mỗi 2.5 giây
    max_blinks = min(10, int(duration))       # Tối đa 1 nháy mắt mỗi giây

    # Tính điểm số nháy mắt
    blink_score = 0.0
    if min_blinks <= blink_counter <= max_blinks:
        blink_score = 1.0
    elif blink_counter > 0:
        # Nếu có nháy mắt nhưng không đủ, vẫn cho điểm một phần
        blink_score = max(0.3, min(0.8, blink_counter / min_blinks))

    # Tính điểm số EAR
    ear_score = 1.0 if 0.2 <= avg_ear <= 0.35 else max(0, 1 - abs(avg_ear - 0.275) / 0.275)

    # Tính điểm số tần suất nháy mắt
    rate_score = 1.0 if 0.2 <= blink_rate <= 0.4 else max(0, 1 - abs(blink_rate - 0.3) / 0.3)

    # Tính điểm số phát hiện khuôn mặt
    face_detection_ratio = face_detected_frames / total_frames if total_frames > 0 else 0
    face_score = min(1.0, face_detection_ratio * 1.5)  # Cho điểm cao hơn nếu phát hiện nhiều khuôn mặt

    # Tổng hợp điểm số liveness
    liveness_score = (blink_score * 0.4 + ear_score * 0.2 + rate_score * 0.2 + face_score * 0.2)

    # Ghi log kết quả để debug
    log_file = os.path.join(os.path.dirname(video_path), "debug_frames", "liveness_results.txt")
    with open(log_file, "w") as f:
        f.write(f"Total frames: {total_frames}\n")
        f.write(f"Face detected frames: {face_detected_frames}\n")
        f.write(f"Blink count: {blink_counter}\n")
        f.write(f"Average EAR: {avg_ear:.4f}\n")
        f.write(f"Blink rate: {blink_rate:.4f} blinks/second\n")
        f.write(f"Face detection ratio: {face_detection_ratio:.4f}\n")
        f.write(f"Blink score: {blink_score:.4f}\n")
        f.write(f"EAR score: {ear_score:.4f}\n")
        f.write(f"Rate score: {rate_score:.4f}\n")
        f.write(f"Face score: {face_score:.4f}\n")
        f.write(f"Liveness score: {liveness_score:.4f}\n")

    return {
        'liveness_score': liveness_score,
        'blink_count': blink_counter,
        'avg_ear': avg_ear,
        'blink_rate': blink_rate,
        'face_detected_frames': face_detected_frames,
        'face_detection_ratio': face_detection_ratio
    }

def process_video_for_liveness(video_file):
    # Tạo thư mục uploads nếu chưa có
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'liveness')
    os.makedirs(upload_dir, exist_ok=True)

    # Tạo tên file duy nhất dựa trên timestamp
    timestamp = int(time.time())
    video_path = os.path.join(upload_dir, f'liveness_{timestamp}.mp4')

    # Lưu video để có thể phân tích và debug sau này
    with open(video_path, 'wb') as f:
        f.write(video_file.read())

    try:
        # Phân tích video
        print(f"Bắt đầu phân tích video liveness: {video_path}")
        results = detect_blinks(video_path)
        print(f"Kết quả phân tích: {results}")

        # Không xóa video để có thể debug sau này
        # Chỉ xóa các video cũ hơn 7 ngày
        cleanup_old_videos(upload_dir, days=7)

        return results
    except Exception as e:
        print(f"Lỗi khi phân tích video liveness: {e}")
        # Vẫn giữ lại video để debug
        raise e

def cleanup_old_videos(directory, days=7):
    """Xóa các video cũ hơn số ngày chỉ định"""
    try:
        now = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Kiểm tra xem file có phải là file thường và có cũ hơn số ngày chỉ định không
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < now - days * 86400:
                os.remove(file_path)
                print(f"Đã xóa file cũ: {file_path}")
    except Exception as e:
        print(f"Lỗi khi dọn dẹp các file cũ: {e}")
