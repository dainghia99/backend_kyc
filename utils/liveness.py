import cv2
import numpy as np
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
import os
import tempfile

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
    
    blink_counter = 0
    counter = 0
    total_ear = 0
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.resize(frame, (450, 450))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện khuôn mặt
        faces = face_detector(gray, 0)
        
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
    
    blink_score = min(1.0, blink_counter / 3) if 2 <= blink_counter <= 5 else 0.0
    ear_score = 1.0 if 0.2 <= avg_ear <= 0.35 else max(0, 1 - abs(avg_ear - 0.275) / 0.275)
    rate_score = 1.0 if 0.2 <= blink_rate <= 0.4 else max(0, 1 - abs(blink_rate - 0.3) / 0.3)
    
    liveness_score = (blink_score * 0.4 + ear_score * 0.3 + rate_score * 0.3)
    
    return {
        'liveness_score': liveness_score,
        'blink_count': blink_counter,
        'avg_ear': avg_ear,
        'blink_rate': blink_rate
    }

def process_video_for_liveness(video_file):
    # Lưu video tạm thời
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_video.mp4')
    
    with open(temp_path, 'wb') as f:
        f.write(video_file.read())
    
    try:
        # Phân tích video
        results = detect_blinks(temp_path)
        
        # Xóa file tạm
        os.remove(temp_path)
        
        return results
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
