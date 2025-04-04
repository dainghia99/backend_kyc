import cv2
import mediapipe as mp
import numpy as np

def calculate_ear(eye_landmarks):
    # Calculate Eye Aspect Ratio
    A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
    B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
    C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
    ear = (A + B) / (2.0 * C)
    return ear

def detect_blinks(video_path):
    cap = cv2.VideoCapture(video_path)
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh()
    
    blink_counter = 0
    ear_threshold = 0.2
    consecutive_frames = 2
    
    total_frames = 0
    blink_frames = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        total_frames += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0].landmark
            
            # Get eye landmarks
            left_eye = np.array([[face_landmarks[p].x, face_landmarks[p].y] 
                               for p in [33, 160, 158, 133, 153, 144]])
            right_eye = np.array([[face_landmarks[p].x, face_landmarks[p].y] 
                                for p in [362, 385, 387, 263, 373, 380]])
            
            # Calculate EAR for both eyes
            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            if ear < ear_threshold:
                blink_frames += 1
            else:
                if blink_frames >= consecutive_frames:
                    blink_counter += 1
                blink_frames = 0
    
    cap.release()
    
    # Calculate liveness score based on blink rate
    liveness_score = min(blink_counter / (total_frames / 30), 1.0)  # Normalize to 30fps
    
    return blink_counter, liveness_score
